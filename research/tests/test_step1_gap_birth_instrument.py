"""Non-network regression for the REAL detector→intake→seed birth route.

All detector strings are investigator-scripted. This suite cannot validate
model detection accuracy, semantic novelty, neurons, or research efficacy.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest

from shadowseed.detection.model_detector import build_detection_prompt
from shadowseed_research.benchmark.step1_gap_birth_instrument import (
    RESULT_SCHEMA, _NoGeneration, _recorded_product_detector, audit,
    validate_fixture,
)

FIXTURE = Path("research/fixtures/step1_gap_birth_recorded_v0.json")


def _load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _runs():
    report = audit(_load(), fixture_sha256="scripted-test-hash")
    return report, {run["variant"]: run for run in report["runs"]}


def test_real_session_uses_original_detector_prompt_parser_and_canonical_intake():
    report, runs = _runs()
    assert report["schema"] == RESULT_SCHEMA
    assert report["status"] == "offline_recorded_product_pipeline_mechanics_only"
    assert report["claimed_efficacy"] is False
    assert report["model_calls"] == report["hosted_embedding_calls"] == 0
    assert report["no_network"] is True
    assert set(runs) == {"current_pair", "generative"}
    first = _load()["cases"][0]["turns"][0]

    current = runs["current_pair"]
    cp0 = current["turns"][0]
    assert cp0["answer_origin"] == "INVESTIGATOR_SCRIPTED_NO_MODEL"
    assert cp0["raw_detector_output"] == first["detector_outputs"]["current_pair"]
    assert cp0["detector_prompt"] == build_detection_prompt(
        first["answer"], variant="current_pair", max_seeds=5,
        question=first["question"], conversation_context="NONE",
    )
    assert cp0["detector_prompt_contract"]["prompt_id"] == "detector_current_pair"
    assert cp0["parse_diagnostics"]["dropped_fewshot_leak"] == 1
    assert cp0["parse_status"] == "parsed_candidates_not_validated"
    assert len(cp0["parsed_candidates"]) == 2
    assert len(cp0["intake"]["normalized_candidates"]) == len(cp0["parsed_candidates"])
    assert len(cp0["observation_ledger_entries"]) == 2
    assert cp0["seed_birth_ids_this_turn"]
    assert all(s["weight"] == 0 for s in cp0["seed_state_after"].values())
    assert all(s["evidence_count"] == 0 for s in cp0["seed_state_after"].values())
    assert all(s["origin"]["context_ref"] == "turn:0:visible_answer"
               for s in cp0["seed_state_after"].values())
    assert cp0["authorized_influence_seed_ids"] == []

    gen = runs["generative"]["turns"][0]
    assert gen["raw_detector_output"] == first["detector_outputs"]["generative"]
    assert gen["detector_prompt"] == build_detection_prompt(
        first["answer"], variant="generative", max_seeds=5
    )
    assert gen["detector_prompt"].endswith("1.")
    assert gen["detector_prompt_contract"] is None
    assert gen["parse_status"] == "parsed_candidates_not_validated"
    assert len(gen["parsed_candidates"]) >= 1


def test_none_parser_failure_and_recurring_seed_are_different_events():
    _, runs = _runs()
    cp = runs["current_pair"]
    cp0, cp1, cp2, cp3 = cp["turns"]
    assert cp1["raw_detector_output"] == "NONE"
    assert cp1["parse_diagnostics"]["explicit_none"] is True
    assert cp1["parse_status"] == "explicit_NONE"
    assert cp1["seed_birth_ids_this_turn"] == []
    assert cp1["parsed_candidates"] == []

    assert cp2["raw_detector_output"] == cp0["raw_detector_lines"][0]
    repeated = cp0["seed_birth_ids_this_turn"][0]
    assert cp2["intake"]["accepted"][0]["seed_id"] == repeated
    assert cp2["seed_state_after"][repeated]["occurrence_count"] >= 2
    # Trace is not monotonic across turns: TTL decay can outweigh recurrence.
    # Test the actual transition after prepare_turn, not a desired end score.
    assert cp2["seed_state_after_prepare"][repeated]["trace"] < cp2["seed_state_before"][repeated]["trace"]
    assert cp2["seed_state_after"][repeated]["trace"] > cp2["seed_state_after_prepare"][repeated]["trace"]
    assert cp2["seed_state_after"][repeated]["trace"] < cp0["seed_state_after"][repeated]["trace"]
    assert cp2["seed_state_after"][repeated]["weight"] == 0
    assert cp2["seed_state_after"][repeated]["evidence_count"] == 0
    assert cp2["authorized_influence_seed_ids"] == []
    assert all(x["weight"] == 0 for x in cp["final_seed_state"].values())

    assert cp3["raw_detector_output"].startswith("Niet-genummerd")
    assert cp3["parse_status"] == "nonempty_output_without_parsed_candidates_not_abstention"
    assert not cp3["parsed_candidates"]
    assert cp3["parse_diagnostics"]["explicit_none"] is False

    # The old generative variant cannot silently treat an empty continuation
    # as the explicit current-pair NONE contract.
    gen1 = runs["generative"]["turns"][1]
    assert gen1["raw_detector_output"] == ""
    assert gen1["parse_status"] == "empty_generation_not_abstention"
    assert gen1["parse_diagnostics"]["explicit_none"] is False
    assert not gen1["seed_birth_ids_this_turn"]


def test_both_arms_are_independent_real_sessions_without_authority():
    _, runs = _runs()
    for run in runs.values():
        assert run["model_calls"] == 0
        assert run["scripted_detector_calls"] == 4
        assert len(run["turns"]) == 4
        assert all(not turn["authorized_influence_seed_ids"]
                   for turn in run["turns"])
        assert all(not turn["suppressed_self_attributed_candidates"]
                   for turn in run["turns"])
        assert all(s["weight"] == 0 and s["evidence_count"] == 0
                   for s in run["final_seed_state"].values())
        assert run["total_influence_records"] == 0
        assert all(len(turn["detector_prompt_sha256"]) == 64
                   for turn in run["turns"])
    # A normal prior turn enters only the later detector context, not the
    # first detector prompt. This audits the original bounded history policy.
    cp = runs["current_pair"]["turns"]
    assert cp[0]["bounded_clean_context"] == "NONE"
    assert "PRIOR TURN 1" in cp[1]["bounded_clean_context"]
    assert "kantine" in cp[2]["bounded_clean_context"]
    assert cp[0]["detector_prompt"] != cp[2]["detector_prompt"]


def test_fixtures_require_explicit_scripted_provenance_and_both_variants():
    original = _load()
    assert len(validate_fixture(original)) == 1
    missing = copy.deepcopy(original)
    missing["provenance"] = "real inference and proof"
    with pytest.raises(ValueError, match="synthetic provenance"):
        validate_fixture(missing)
    unknown = copy.deepcopy(original)
    unknown["cases"][0]["turns"][0]["detector_outputs"].pop("generative")
    with pytest.raises(ValueError, match="both detector variants"):
        validate_fixture(unknown)
    wrong = copy.deepcopy(original)
    wrong["cases"][0]["turns"][0]["answer"] = ""
    with pytest.raises(ValueError, match="invalid answer"):
        validate_fixture(wrong)


def test_no_model_can_be_invoked_and_recorded_detector_fails_closed():
    with pytest.raises(AssertionError, match="unexpected model call"):
        _NoGeneration().generate("prompt", {}, "baseline", [])
    detector, client = _recorded_product_detector(["NONE"], "current_pair")
    assert detector.detect_seeds({"text": "A normal answer.", "question": "Why?"}) == []
    with pytest.raises(AssertionError, match="scripted detector output exhausted"):
        detector.detect_seeds({"text": "Another answer.", "question": "Why?"})
    assert client.calls == 1


def test_cli_exports_explicitly_unvalidated_recorded_evidence(tmp_path: Path):
    output = tmp_path / "audit.json"
    completed = subprocess.run(
        [sys.executable, "-m",
         "shadowseed_research.benchmark.step1_gap_birth_instrument",
         "--fixture", str(FIXTURE), "--output", str(output)],
        capture_output=True, text=True, check=True, timeout=80,
    )
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["status"] == "offline_recorded_product_pipeline_mechanics_only"
    assert record["model_calls"] == record["hosted_embedding_calls"] == 0
    assert record["claimed_efficacy"] is False
    assert "real_model_calls" in completed.stdout
    assert len(record["fixture_sha256"]) == 64
    assert len(record["runs"]) == 2
