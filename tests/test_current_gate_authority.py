from __future__ import annotations

from shadowseed.gate.current_authority import snapshot_meets_current_gate


def _seed(**overrides):
    seed = {
        "status": "PROMOTED",
        "weight": 0.6,
        "occurrence_count": 4,
        "evidence_count": 3,
        "trace": 1.0,
    }
    seed.update(overrides)
    return seed


def _config(**overrides):
    config = {
        "promotion_threshold": 0.5,
        "min_occurrences_for_gate": 3,
        "min_evidence_for_gate": 2,
        "min_trace_for_gate": 0.5,
        "validation_increment": 0.2,
    }
    config.update(overrides)
    return config


def test_current_gate_rejects_nonpromoted_blocked_and_underweight() -> None:
    assert snapshot_meets_current_gate(_seed(status="ACTIVE"), _config(), "exploratory") is False
    assert snapshot_meets_current_gate(_seed(), _config(), "exploratory", blocking=True) is False
    assert snapshot_meets_current_gate(
        _seed(weight=0.4),
        _config(promotion_threshold=0.5),
        "exploratory",
    ) is False


def test_exploratory_accepts_recurrence_or_external_support() -> None:
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=3, evidence_count=0),
        _config(min_occurrences_for_gate=3),
        "exploratory",
    ) is True
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=0, evidence_count=1),
        _config(min_occurrences_for_gate=3),
        "exploratory",
    ) is True
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=0, evidence_count=0),
        _config(min_occurrences_for_gate=3),
        "exploratory",
    ) is False


def test_evidence_backed_requires_verified_external_support_not_recurrence() -> None:
    config = _config(min_occurrences_for_gate=99, min_evidence_for_gate=99)
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=0, evidence_count=1),
        config,
        "evidence_backed",
    ) is True
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=99, evidence_count=0),
        config,
        "evidence_backed",
    ) is False


def test_legacy_strict_gate_requires_recurrence_evidence_and_trace() -> None:
    config = _config(
        min_occurrences_for_gate=4,
        min_evidence_for_gate=3,
        min_trace_for_gate=0.5,
    )
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=4, evidence_count=3, trace=0.6),
        config,
        "legacy_evidence_required",
    ) is True
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=3, evidence_count=3, trace=0.6),
        config,
        "legacy_evidence_required",
    ) is False
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=4, evidence_count=2, trace=0.6),
        config,
        "legacy_evidence_required",
    ) is False
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=4, evidence_count=3, trace=0.5),
        config,
        "legacy_evidence_required",
    ) is False


def test_unknown_policy_is_fail_closed() -> None:
    assert snapshot_meets_current_gate(_seed(), _config(), "unknown") is False
