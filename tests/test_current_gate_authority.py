from __future__ import annotations

from shadowseed.gate.current_authority import snapshot_meets_current_gate
from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.gate.signals import SignalKind, ValidationSignal, recurrence_signal


def _seed(**overrides):
    seed = {
        "id": "ss_1",
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


def _event(
    decision: GateDecision,
    *signals: ValidationSignal,
    policy_id: str = "exploratory",
    sequence: int = 1,
) -> GateEvent:
    return GateEvent(
        event_id=f"gate::ss_1::{sequence:06d}",
        seed_id="ss_1",
        policy_id=policy_id,
        decision=decision,
        signals=signals,
        status_before="ACTIVE",
        status_after="PROMOTED",
        weight_before=0.4,
        weight_after=0.6,
        authority_version=sequence,
    )


def _recurrence() -> ValidationSignal:
    return recurrence_signal(3, threshold=3, source_ref="turn:2")


def _evidence(source_ref: str = "doc:1") -> ValidationSignal:
    return ValidationSignal(
        kind=SignalKind.SSOT,
        verified=True,
        source_ref=source_ref,
    )


def test_current_gate_rejects_nonpromoted_blocked_and_underweight() -> None:
    history = [_event(GateDecision.PROMOTED, _recurrence())]
    assert snapshot_meets_current_gate(
        _seed(status="ACTIVE"), _config(), "exploratory", gate_events=history
    ) is False
    assert snapshot_meets_current_gate(
        _seed(), _config(), "exploratory", blocking=True, gate_events=history
    ) is False
    assert snapshot_meets_current_gate(
        _seed(weight=0.4),
        _config(promotion_threshold=0.5),
        "exploratory",
        gate_events=history,
    ) is False


def test_exploratory_reuses_canonical_signal_semantics() -> None:
    recurrence_history = [_event(GateDecision.PROMOTED, _recurrence())]
    evidence_history = [
        _event(GateDecision.PROMOTED, _evidence(), policy_id="evidence_backed")
    ]

    assert snapshot_meets_current_gate(
        _seed(occurrence_count=0, evidence_count=0),
        _config(min_occurrences_for_gate=99),
        "exploratory",
        gate_events=recurrence_history,
    ) is True
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=0, evidence_count=1),
        _config(min_occurrences_for_gate=99),
        "exploratory",
        gate_events=evidence_history,
    ) is True
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=9, evidence_count=9),
        _config(),
        "exploratory",
        gate_events=[],
    ) is False


def test_evidence_backed_requires_verified_external_signal_not_recurrence() -> None:
    evidence_history = [
        _event(GateDecision.PROMOTED, _evidence(), policy_id="evidence_backed")
    ]
    recurrence_history = [_event(GateDecision.PROMOTED, _recurrence())]

    assert snapshot_meets_current_gate(
        _seed(occurrence_count=0, evidence_count=1),
        _config(min_occurrences_for_gate=99, min_evidence_for_gate=99),
        "evidence_backed",
        gate_events=evidence_history,
    ) is True
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=99, evidence_count=0),
        _config(min_occurrences_for_gate=1),
        "evidence_backed",
        gate_events=recurrence_history,
    ) is False
    assert snapshot_meets_current_gate(
        _seed(occurrence_count=99, evidence_count=99),
        _config(),
        "evidence_backed",
        gate_events=[],
    ) is False


def test_current_support_before_latest_contradiction_does_not_reauthorize() -> None:
    before = _event(
        GateDecision.PROMOTED,
        _evidence("doc:before"),
        policy_id="evidence_backed",
        sequence=1,
    )
    contradicted = _event(
        GateDecision.CONTRADICTED,
        ValidationSignal(kind=SignalKind.CONTRADICTION),
        sequence=2,
    )
    resolved = _event(
        GateDecision.CONTRADICTION_RESOLVED,
        ValidationSignal(kind=SignalKind.CONTRADICTION_RESOLUTION),
        policy_id="contradiction_resolution",
        sequence=3,
    )

    history = [before, contradicted, resolved]
    assert snapshot_meets_current_gate(
        _seed(), _config(), "evidence_backed", gate_events=history
    ) is False

    history.append(
        _event(
            GateDecision.PROMOTED,
            _evidence("doc:after"),
            policy_id="evidence_backed",
            sequence=4,
        )
    )
    assert snapshot_meets_current_gate(
        _seed(), _config(), "evidence_backed", gate_events=history
    ) is True


def test_legacy_policy_reuses_its_canonical_accumulated_thresholds() -> None:
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
    assert snapshot_meets_current_gate(
        _seed(), _config(), "unknown", gate_events=[]
    ) is False
