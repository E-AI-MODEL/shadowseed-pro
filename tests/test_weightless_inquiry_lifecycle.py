"""Longitudinal weightless inquiry invariants, not candidate-quality evidence.

Uses the actual manager, lifecycle, recurrence and Gate. Embeddings/candidates
are controlled fixtures; no LLM model performance or learning is measured.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import recurrence_signal
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.seed_normalization import normalize_detection_candidates


QUESTION = "Hoe hangen oorzaken en gevolgen samen?"
OTHER = "Wat als de aannames niet kloppen?"


def _embed(text: str) -> np.ndarray:
    return (
        np.array([1.0, 0.0]) if "oorzaken" in text.lower()
        else np.array([0.0, 1.0])
    )


def _manager() -> SSLManager:
    return SSLManager(embedding_fn=_embed)


def _birth(manager: SSLManager, text: str = QUESTION) -> str:
    result = manager.ingest_detection_candidates(
        [text],
        expand_short_fragments=False,
        split_broad=False,
    )
    assert result["rejected"] == []
    assert len(result["accepted"]) == 1
    return result["accepted"][0]["seed_id"]


def test_open_relation_birth_is_weightless_and_keeps_question_punctuation():
    manager = _manager()
    assert normalize_detection_candidates(
        [QUESTION], expand_short_fragments=False, split_broad=False,
    ) == [QUESTION]
    sid = _birth(manager)
    seed = manager.seeds[sid]
    assert seed.text == QUESTION
    assert seed.trace > 0
    assert seed.weight == 0.0
    assert seed.evidence_count == 0
    assert seed.status is SeedStatus.NEW
    assert manager.gate_events == []


@pytest.mark.parametrize("candidate", [
    "Oorzaken, gevolgen, contexten en perspectieven ontbreken.",
    "Hoe hangen oorzaken, gevolgen, contexten en perspectieven samen?",
    "Welke oorzaken en gevolgen?",
])
def test_broad_category_lists_still_fail(candidate: str):
    assert not SSLManager.is_atomic_seed(candidate)


def test_clean_reappearance_preserves_zero_authority_under_evidence_backed_gate():
    manager = _manager()
    sid = _birth(manager)
    for _ in range(2):
        assert manager.add_or_update_seed(QUESTION) == sid
    seed = manager.seeds[sid]
    assert seed.occurrence_count == 3
    assert seed.trace > 0
    assert seed.weight == 0.0
    signal = recurrence_signal(3, threshold=2, source_ref="test:clean:occurrences")
    assert not signal.is_external_evidence
    gate = manager.submit_signals(sid, [signal], policy_id="evidence_backed")
    assert gate.decision is GateDecision.BLOCKED
    assert gate.policy_id == "evidence_backed"
    assert seed.weight == 0.0
    assert seed.evidence_count == 0


def test_trtl_reactivation_keeps_weight_zero_then_ttl_expires_terminally():
    manager = _manager()
    sid = _birth(manager)
    seed = manager.seeds[sid]
    before_trace = seed.trace
    for step in range(1, 40):
        manager.decay_traces()
        assert seed.trace <= before_trace
        before_trace = seed.trace
        assert seed.weight == 0.0
        if seed.status is SeedStatus.DORMANT:
            assert step > 1
            break
    else:
        pytest.fail("no dormancy within a bounded number of turns")

    assert seed.turns_dormant == 1
    hits = manager.scan_trtl_triggers("Wat betekenen die oorzaken in dit geval?")
    assert hits == [sid]
    assert seed.status is SeedStatus.NEW
    assert seed.turns_dormant == 0
    assert seed.weight == 0.0
    assert seed.trace > before_trace

    for _ in range(40):
        manager.decay_traces()
        if seed.status is SeedStatus.EXPIRED:
            break
    assert seed.status is SeedStatus.EXPIRED
    assert seed.weight == 0.0
    assert manager.scan_trtl_triggers("oorzaken") == []
    assert seed.status is SeedStatus.EXPIRED
    assert manager.gate_events[-1].decision is GateDecision.EXPIRED
    assert manager.gate_events[-1].policy_id == "lifecycle_expiry"


def test_same_question_after_expiry_is_new_weightless_idea_not_resurrection():
    manager = _manager()
    old = _birth(manager)
    for _ in range(40):
        manager.decay_traces()
        if manager.seeds[old].status is SeedStatus.EXPIRED:
            break
    assert manager.seeds[old].status is SeedStatus.EXPIRED
    fresh = _birth(manager)
    assert fresh != old
    assert manager.seeds[old].status is SeedStatus.EXPIRED
    assert manager.seeds[fresh].weight == 0.0
    assert manager.seeds[fresh].status is SeedStatus.NEW


def test_recurrence_has_policy_specific_authority_but_never_becomes_truth():
    manager = _manager()
    sid = _birth(manager)
    manager.add_or_update_seed(QUESTION)
    manager.add_or_update_seed(QUESTION)
    signal = recurrence_signal(3, threshold=2, source_ref="test:synthetic:repeat")
    gate = manager.submit_signals(sid, [signal], policy_id="exploratory")
    assert gate.policy_id == "exploratory"
    # One exploratory signal can grant limited weight while still failing the
    # separate promotion/point-of-use threshold.
    assert gate.decision is GateDecision.VALIDATED
    assert manager.seeds[sid].status is SeedStatus.ACTIVE
    assert 0.0 < manager.seeds[sid].weight < manager.promotion_threshold
    assert not manager.current_gate_authorizes(
        sid, policy_id="exploratory", enforce_current_gate=True,
    )
    assert manager.seeds[sid].evidence_count == 0
    assert signal.is_external_evidence is False
    # Neither recurrent recognition nor positive weight is proof of truth.


@pytest.mark.parametrize("invalid", [-1, -5])
def test_negative_turn_count_cannot_reverse_trace_time(invalid: int):
    manager = _manager()
    sid = _birth(manager)
    before = manager.seeds[sid].trace
    before_log = len(manager.event_log)
    with pytest.raises(ValueError, match="turns_passed"):
        manager.decay_traces(turns_passed=invalid)
    assert manager.seeds[sid].trace == before
    assert len(manager.event_log) == before_log


@pytest.mark.parametrize("invalid", [True, "2"])
def test_nonnumeric_turn_counts_fail_closed(invalid):
    manager = _manager()
    _birth(manager)
    with pytest.raises(TypeError, match="turns_passed"):
        manager.decay_traces(turns_passed=invalid)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_elapsed_time_is_rejected(invalid):
    manager = _manager()
    _birth(manager)
    with pytest.raises(ValueError, match="turns_passed"):
        manager.decay_traces(turns_passed=invalid)


def test_fractional_half_life_remains_supported_for_calibration():
    manager = _manager()
    sid = _birth(manager)
    before = manager.seeds[sid].trace
    manager.decay_traces(turns_passed=manager.half_life_turns)
    assert manager.seeds[sid].trace == pytest.approx(before / 2)
    assert manager.seeds[sid].weight == 0.0


def test_zero_turns_are_genuine_noop_without_audit_noise():
    manager = _manager()
    sid = _birth(manager)
    trace_before = manager.seeds[sid].trace
    events_before = len(manager.event_log)
    manager.decay_traces(turns_passed=0)
    assert manager.seeds[sid].trace == trace_before
    assert manager.seeds[sid].status is SeedStatus.NEW
    assert len(manager.event_log) == events_before
