"""Offline calibration tests: executable prompts, controlled failures and artifacts."""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from mit_matched_runner import (  # noqa: E402
    FakeProvider,
    PreflightError,
    digest_text,
    main,
    make_messages,
    parse_reply,
    run_calibration,
    validate_input,
)

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mit_matched_runner_synthetic_v1.json"


def source():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_real_two_turn_fake_execution_all_five_arms():
    summary, trace = run_calibration(source())
    assert summary["completed_five_arm_cases"] == 1
    assert summary["arm_calls"] == {arm: 2 for arm in "ABCDE"}
    assert summary["model_network_calls"] == 0
    assert summary["g0_status"] == "NOT_PASSED"
    assert trace["visibility"] == "OWNER_ONLY_NOT_BLIND"
    for row in trace["cases"][0]["arms"].values():
        assert [e["stage"] for e in row["events"]] == ["T1", "T3"]
        assert all(e["status"] == "parsed" for e in row["events"])
        assert row["calls_used"] == 2
        assert row["synthetic_token_units"] < row["allocated_model_token_units"]


def test_fake_output_same_in_all_arms_no_seed_success_implied():
    _, trace = run_calibration(source())
    answers = [trace["cases"][0]["arms"][a]["events"][0]["response_text"] for a in "ABCDE"]
    assert len(set(answers)) == 1


def test_actual_payload_hashes_are_checked_not_only_metadata():
    data = source()
    data["payloads"][0]["history"] += " tampering"
    with pytest.raises(PreflightError, match="altered history"):
        validate_input(data)
    data = source()
    data["payloads"][0]["feedback"] += " extra"
    with pytest.raises(PreflightError, match="altered feedback"):
        validate_input(data)


def test_frozen_candidate_bytes_and_sham_bound_to_manifest():
    data = source()
    data["payloads"][0]["candidate_text"] = "Different candidate with matching metadata"
    with pytest.raises(PreflightError, match="candidate does not match"):
        validate_input(data)
    data = source()
    data["payloads"][0]["sham_text"] = "An altered sham"
    with pytest.raises(PreflightError, match="sham does not match"):
        validate_input(data)


def test_ri_requires_a_real_external_executor_not_fake_feedback():
    data = source()
    data["plan"]["feedback_regime"] = "RI"
    for arm in data["plan"]["cases"][0]["arms"]:
        arm["feedback_sha256"] = None
    with pytest.raises(PreflightError, match="RI not supported"):
        validate_input(data)


def test_no_live_or_paid_provider_can_be_injected():
    class NetworkProvider:
        kind = "HTTP_MODEL_PROVIDER"

    with pytest.raises(PreflightError, match="refuses connected or paid providers"):
        run_calibration(source(), provider=NetworkProvider())


def test_explicit_candidate_exposure_only_in_D():
    data = source()
    case = data["plan"]["cases"][0]
    content = data["payloads"][0]
    candidate = content["candidate_text"]
    sham = content["sham_text"]
    prompt_strings = {a: json.dumps(make_messages(case, content, a, "T1")) for a in "ABCDE"}
    assert candidate in prompt_strings["D"] and sham not in prompt_strings["D"]
    assert sham in prompt_strings["E"] and candidate not in prompt_strings["E"]
    assert all(candidate not in prompt_strings[a] and sham not in prompt_strings[a] for a in "ABC")
    assert content["ordinary_notes"] in prompt_strings["C"]
    assert content["ordinary_notes"] not in prompt_strings["D"]


def test_identical_frozen_feedback_delivered_after_own_t1_only():
    data = source()
    _, trace = run_calibration(data)
    feedback = data["payloads"][0]["feedback"]
    for arm in "ABCDE":
        events = trace["cases"][0]["arms"][arm]["events"]
        assert feedback not in json.dumps(events[0]["messages"])
        assert feedback in json.dumps(events[1]["messages"])
        assert events[0]["response_text"] in events[1]["messages"][1]["content"]


def test_invalid_json_is_unscorable_not_a_negative_finding():
    class BadFake(FakeProvider):
        kind = "FAKE_NO_NETWORK"

        @staticmethod
        def complete(messages, **kwargs):
            result = FakeProvider.complete(messages, **kwargs)
            result["text"] = "NONE"
            result["output_tokens"] = 1
            return result

    report, trace = run_calibration(source(), provider=BadFake())
    assert report["completed_five_arm_cases"] == 0
    assert len(report["errors"]) == 10
    assert all(arm["events"][1]["status"] == "skipped_invalid_prior"
               for arm in trace["cases"][0]["arms"].values())


def test_provider_failures_are_logged_not_silently_retried():
    class BrokenFake(FakeProvider):
        kind = "FAKE_NO_NETWORK"

        @staticmethod
        def complete(messages, **kwargs):
            raise OSError("simulated provider failure")

    report, trace = run_calibration(source(), provider=BrokenFake())
    assert report["arm_calls"] == {a: 1 for a in "ABCDE"}
    assert report["completed_five_arm_cases"] == 0
    assert len(report["errors"]) == 10
    assert all(arm["events"][0]["status"] == "provider_or_contract_error"
               for arm in trace["cases"][0]["arms"].values())


def test_fail_closed_on_changed_provider_model_id():
    class WrongModelFake(FakeProvider):
        kind = "FAKE_NO_NETWORK"

        @staticmethod
        def complete(messages, **kwargs):
            output = FakeProvider.complete(messages, **kwargs)
            output["model_revision"] = "other-revision"
            return output

    report, _ = run_calibration(source(), provider=WrongModelFake())
    assert len([e for e in report["errors"] if e["status"] == "provider_or_contract_error"]) == 5


def test_budget_blocks_model_call_instead_of_faking_answer():
    data = source()
    cap = data["plan"]["cases"][0]["shared"]["budget"]
    cap["max_model_tokens"] = 1
    for arm in data["plan"]["cases"][0]["arms"]:
        arm["budget"] = copy.deepcopy(cap)
    report, _ = run_calibration(data)
    assert report["arm_calls"] == {a: 0 for a in "ABCDE"}
    assert all(e["status"] == "budget_blocked" for e in report["errors"] if e["stage"] == "T1")


def test_cli_writes_owner_only_files_without_overwrite(tmp_path):
    inp = tmp_path / "input.json"
    inp.write_text(json.dumps(source()), encoding="utf-8")
    out = tmp_path / "results"
    assert main(["--input", str(inp), "--output-dir", str(out)]) == 0
    summary_path = out / "run_summary.json"
    trace_path = out / "owner_trace.json"
    assert json.loads(summary_path.read_text())["cases"] == 1
    assert json.loads(trace_path.read_text())["summary"]["provider"] == "FAKE_NO_NETWORK"
    assert trace_path.stat().st_mode & 0o077 == 0
    assert summary_path.stat().st_mode & 0o077 == 0
    with pytest.raises(PreflightError, match="already exists"):
        main(["--input", str(inp), "--output-dir", str(out)])


def test_parse_reply_refuses_non_json_schema_and_empty_fields():
    assert parse_reply("NONE")["reason"] == "invalid_json"
    assert parse_reply(json.dumps({"question": "x"}))["reason"] == "invalid_schema"
    assert parse_reply(json.dumps({"question": "x", "experiment": "y", "expected_result": ""}))["reason"] == "invalid_fields"


def test_preflight_never_confers_gate_or_scientific_authority():
    report, _ = run_calibration(source())
    assert not report["scientific_comparative_effect_calculated"]
    assert not report["independent_g0_review_approved"]
    assert not report["real_candidate_birth_verified"]
    assert report["status"] == "SYNTHETIC_EXECUTION_NO_SCIENTIFIC_RESULT"


def test_private_answer_keys_are_rejected_not_accidentally_sent():
    data = source()
    data["hidden_expected_winner"] = "D"
    with pytest.raises(PreflightError, match="unexpected top-level"):
        validate_input(data)
    data = source()
    data["payloads"][0]["arm_truth"] = "D"
    with pytest.raises(PreflightError, match="unexpected payload fields"):
        validate_input(data)


def test_fake_provider_cannot_misreport_completion_cost():
    class LyingFake(FakeProvider):
        kind = "FAKE_NO_NETWORK"

        @staticmethod
        def complete(messages, **kwargs):
            result = FakeProvider.complete(messages, **kwargs)
            result["output_tokens"] = 0
            return result

    summary, _ = run_calibration(source(), provider=LyingFake())
    assert summary["arm_calls"] == {a: 1 for a in "ABCDE"}
    assert sum(e["status"] == "provider_or_contract_error" for e in summary["errors"]) == 5
