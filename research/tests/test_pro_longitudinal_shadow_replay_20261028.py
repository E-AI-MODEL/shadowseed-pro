"""Offline contract tests for the frozen multi-turn replay runner."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.scripts.pro_longitudinal_shadow_replay_20261028 import (
    FrozenDetector, load_source, replay, toy_embedding,
)


def synthetic() -> dict:
    cases = []
    n = 0
    for i in range(12):
        turns = []
        for j in range(4):
            # 48 accepted and 46 historically not-atomic (94 total).
            accepted = f"Could sample {i} and trial {j} depend on sampling time?"
            # Two genuinely separate sentences; test the new unresolved path.
            excluded = (
                f"Check instrument {i} at trial {j}. "
                "Check sensor response under the same conditions."
            )
            values = [accepted, excluded] if n < 46 else [accepted]
            lineage = [
                {"outcome": "accepted", "reason": None},
            ] + ([{"outcome": "rejected", "reason": "not_atomic"}] if n < 46 else [])
            turns.append({
                "turn": j,
                "user_input": f"Synthetic question {i} {j}?",
                "host_answer": "Synthetic answer only, not evidence.",
                "canonical_report": {
                    "detected_candidates": values,
                    "intake_diagnostics": {"item_lineage": lineage},
                },
            })
            n += 1
        cases.append({"case_id": f"SYN-{i:02d}", "model_id": (
            "synthetic-model-a" if i % 2 else "synthetic-model-b"
        ), "turns": turns})
    return {"cases": cases}


def test_toy_embedding_is_deterministic():
    a = toy_embedding("A new, testable uncertainty")
    b = toy_embedding("A new, testable uncertainty")
    assert list(a) == list(b)
    assert len(a) == 128


def test_detectors_replay_exact_source_without_provider_calls():
    detector = FrozenDetector([["First sentence."], [], ["Question?"]])
    assert detector.detect_seeds({}) == ["First sentence."]
    assert detector.detect_seeds({}) == []
    assert detector.detect_seeds({}) == ["Question?"]
    with pytest.raises(RuntimeError, match="extra detector"):
        detector.detect_seeds({})


def test_source_integrity_does_not_accept_unpinned_json():
    with pytest.raises(ValueError, match="SHA mismatch"):
        load_source(json.dumps(synthetic()).encode())


def test_chronological_engine_replay_accounts_for_all_candidate_beginnings():
    result = replay(synthetic())
    assert result["counts"]["turns"] == 48
    assert result["counts"]["archived_candidates"] == 94
    assert result["counts"]["historical_not_atomic"] == 46
    assert result["counts"]["observed_unresolved"] == 46
    assert result["counts"]["host_seed_exposures"] == 0
    assert result["counts"]["nonzero_weight_seeds"] == 0
    assert result["independent_human_reviews"] == 0
    assert result["q1_q2_efficacy"].startswith("NOT TESTED")
