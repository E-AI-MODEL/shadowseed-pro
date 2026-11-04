"""Research-only matched-pilot preflight contracts, no model or network calls."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "mit_matched_preflight.py"
SPEC = importlib.util.spec_from_file_location("mit_matched_preflight", SCRIPT)
assert SPEC and SPEC.loader
PRE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PRE)


def _plan(regime="RF"):
    shared = {"history_sha256": "a" * 64, "t0_context_sha256": "b" * 64,
              "feedback_sha256": "c" * 64,
              "model_id": "fake-calibration-model", "model_revision": "pinned-test-revision",
              "decoding": {"temperature": 0}, "budget": {
                  "max_model_calls": 3, "max_model_tokens": 4000,
                  "max_tool_calls": 2, "max_retrieval_calls": 2}}
    candidate = {"id": "seed_test", "sha256": "d" * 64, "birth_turn": 0,
                 "exposure_turn": 1, "weight": 0, "authority": False, "token_count": 25}
    arms = []
    for arm in "ABCDE":
        record = {**copy.deepcopy(shared), "arm": arm, "candidate_visibility": "absent",
                  "candidate_sha256": None, "sham_sha256": None, "extra_tokens": 0}
        if regime == "RI":
            record["feedback_sha256"] = None
        if arm == "D":
            record.update(candidate_visibility="frozen_weightless", candidate_sha256="d" * 64, extra_tokens=25)
        if arm == "E":
            record.update(candidate_visibility="sham_ablation", sham_sha256="e" * 64, extra_tokens=25)
        arms.append(record)
    return {"schema": PRE.SCHEMA, "mode": "mechanics_calibration_only",
            "feedback_regime": regime, "g0_authorized": False,
            "cases": [{"case_id": "SYN-01", "provenance": "synthetic_calibration",
                       "shared": shared, "candidate": candidate, "arms": arms}]}


def _arm(p, name):
    return next(a for a in p["cases"][0]["arms"] if a["arm"] == name)


def test_synthetic_rf_plan_is_not_a_g0_pass():
    out = PRE.check_plan(_plan())
    assert out["case_count"] == 1
    assert out["status"] == "MECHANICS_ONLY_NOT_APPROVED"
    assert out["prospective_model_runs"] == 0
    assert out["g0_status"] == "NOT_PASSED"


def test_ri_must_not_fake_identical_future_outcomes():
    p = _plan("RI")
    assert PRE.check_plan(p)["feedback_regime"] == "RI"
    _arm(p, "D")["feedback_sha256"] = "c" * 64
    with pytest.raises(PRE.PreflightError, match="RI cannot pre-fill outcomes"):
        PRE.check_plan(p)


def test_missing_or_duplicate_arm_refused():
    p = _plan()
    p["cases"][0]["arms"][0]["arm"] = "B"
    with pytest.raises(PRE.PreflightError, match="missing/duplicate arm"):
        PRE.check_plan(p)


def test_budget_and_history_must_match():
    p = _plan()
    _arm(p, "B")["budget"]["max_model_calls"] += 1
    with pytest.raises(PRE.PreflightError, match="unequal budget"):
        PRE.check_plan(p)
    p = _plan()
    _arm(p, "C")["history_sha256"] = "f" * 64
    with pytest.raises(PRE.PreflightError, match="different history_sha256"):
        PRE.check_plan(p)


def test_candidate_timing_and_gate_remain_isolated():
    p = _plan()
    p["cases"][0]["candidate"]["authority"] = True
    with pytest.raises(PRE.PreflightError, match="weightless"):
        PRE.check_plan(p)
    p = _plan()
    p["cases"][0]["candidate"]["birth_turn"] = 1
    with pytest.raises(PRE.PreflightError, match="before exposure"):
        PRE.check_plan(p)


def test_baseline_cannot_see_seed_and_sham_differs():
    p = _plan()
    _arm(p, "A")["candidate_sha256"] = "d" * 64
    with pytest.raises(PRE.PreflightError, match="leakage"):
        PRE.check_plan(p)
    p = _plan()
    _arm(p, "E")["sham_sha256"] = "d" * 64
    with pytest.raises(PRE.PreflightError, match="not ablated"):
        PRE.check_plan(p)


def test_ablation_must_match_seed_budget():
    p = _plan()
    _arm(p, "E")["extra_tokens"] -= 1
    with pytest.raises(PRE.PreflightError, match="unmatched sham-token"):
        PRE.check_plan(p)


def test_calibration_never_accepts_outcome_or_private_holdout():
    p = _plan()
    p["cases"][0]["results"] = {"D": "won"}
    with pytest.raises(PRE.PreflightError, match="no outcome labels"):
        PRE.check_plan(p)
    p = _plan()
    p["cases"][0]["provenance"] = "sealed_holdout"
    with pytest.raises(PRE.PreflightError, match="not a synthetic fixture"):
        PRE.check_plan(p)


def test_history_audit_marks_invalid_as_unscorable():
    rows = [{"checkpoint_turn": 26, "ordinary_llm_raw": "NONE",
             "ordinary_llm_parsed": {"valid": False, "reason_code": "invalid_format"},
             "same_prior_notes_in_both_arms": True},
            {"checkpoint_turn": 60, "ordinary_llm_raw": "PICK: t001",
             "ordinary_llm_parsed": {"valid": True},
             "same_prior_notes_in_both_arms": True}]
    res = PRE.audit_historical_replay(rows)
    assert res["unscorable_qwen_results"] == 1
    assert res["parseable_qwen_results"] == 1
    assert res["relative_method_effect_estimated"] is False


def test_invalid_history_disposition_cannot_be_made_up():
    with pytest.raises(PRE.PreflightError, match="missing invalid-reason"):
        PRE.audit_historical_replay([{"checkpoint_turn": 1, "ordinary_llm_raw": "bad",
                                     "ordinary_llm_parsed": {"valid": False}}])


def test_cli_write_protects_source_and_output(tmp_path):
    source, report = tmp_path / "plan.json", tmp_path / "preflight.json"
    source.write_text(json.dumps(_plan()), encoding="utf-8")
    assert PRE.main(["check-plan", "--input", str(source), "--report", str(report)]) == 0
    assert json.loads(report.read_text())["g0_status"] == "NOT_PASSED"
    with pytest.raises(FileExistsError):
        PRE.main(["check-plan", "--input", str(source), "--report", str(report)])
    with pytest.raises(PRE.PreflightError, match="never overwrite"):
        PRE.main(["check-plan", "--input", str(source), "--report", str(source)])
