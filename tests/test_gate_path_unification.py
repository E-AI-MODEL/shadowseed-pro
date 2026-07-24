"""Regression tests for the single executable Validation Gate path."""

from __future__ import annotations

import numpy as np

from shadowseed.gate import (
    GateDecision,
    SignalDirection,
    SignalKind,
    ValidationSignal,
)
from shadowseed.gate.signals import recurrence_signal
from shadowseed.manager import SSLManager


def _manager(**kwargs) -> SSLManager:
    return SSLManager(
        embedding_fn=lambda _text: np.array([1.0, 0.0, 0.0]),
        **kwargs,
    )


def _recurrent_seed(manager: SSLManager) -> str:
    seed_id = manager.add_or_update_seed("A relevant boundary is missing.")
    manager.add_or_update_seed("A relevant boundary is missing.")
    manager.add_or_update_seed("A relevant boundary is missing.")
    return seed_id


def test_legacy_boolean_api_uses_one_real_policy_event_per_call():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    first = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    second = manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    assert first.verdict == "blocked"
    assert second.verdict == "validated"
    assert len(manager.gate_events) == 2
    assert len(manager.validation_log) == 2
    assert all(
        event.policy_id == "legacy_evidence_required"
        for event in manager.gate_events
    )
    assert {signal.kind for signal in manager.gate_events[-1].signals} == {
        SignalKind.RECURRENCE,
        SignalKind.SSOT,
    }


def test_legacy_policy_preserves_manager_validation_increment():
    manager = _manager(validation_increment=0.35, promotion_threshold=0.3)
    seed_id = _recurrent_seed(manager)

    assert manager.run_validation_gate(seed_id, external_evidence=True) is None
    assert manager.run_validation_gate(seed_id, external_evidence=True) is True

    assert manager.get_seed(seed_id).weight == 0.35
    assert manager.gate_events[-1].policy_id == "legacy_evidence_required"


def test_named_policy_is_executed_not_only_written_to_event():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A relevant boundary is missing.")

    result = manager.run_validation_gate_detailed(
        seed_id,
        signals=[recurrence_signal(3, threshold=2)],
        policy_id="exploratory",
    )

    assert result.verdict == "validated"
    assert manager.gate_events[-1].policy_id == "exploratory"
    assert manager.get_seed(seed_id).weight > 0.0


def test_private_legacy_core_is_redirected_to_signal_gate():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    first = manager._run_validation_gate_core(
        seed_id,
        external_evidence=True,
    )
    second = manager._run_validation_gate_core(
        seed_id,
        external_evidence=True,
    )

    assert first.verdict == "blocked"
    assert second.verdict == "validated"
    assert len(manager.gate_events) == 2
    assert all(
        event.policy_id == "legacy_evidence_required"
        for event in manager.gate_events
    )


def test_legacy_policy_blocks_unverified_external_signal():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    result = manager.run_validation_gate_detailed(
        seed_id,
        signals=[
            recurrence_signal(3, threshold=2),
            ValidationSignal(kind=SignalKind.SSOT, verified=False),
        ],
    )

    assert result.verdict == "blocked"
    assert result.external_evidence_passed is False
    assert result.external_evidence_applied is False
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager.get_seed(seed_id).evidence_count == 0


def test_exploratory_policy_blocks_unverified_external_support_alone():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A source boundary is missing.")
    signal = ValidationSignal(kind=SignalKind.RETRIEVAL, verified=False)

    event = manager.submit_signals(seed_id, [signal], policy_id="exploratory")

    assert event.decision is GateDecision.BLOCKED
    assert event.signals == (signal,)
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager.get_seed(seed_id).evidence_count == 0
    result = manager.validation_log[-1]
    assert result.external_evidence_passed is False
    assert result.external_evidence_applied is False


def test_exploratory_policy_accepts_verified_external_support():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A source boundary is missing.")

    event = manager.submit_signals(
        seed_id,
        [ValidationSignal(kind=SignalKind.RETRIEVAL, verified=True)],
        policy_id="exploratory",
    )

    assert event.decision is GateDecision.VALIDATED
    assert manager.get_seed(seed_id).weight > 0.0
    assert manager.get_seed(seed_id).evidence_count == 1
    result = manager.validation_log[-1]
    assert result.external_evidence_passed is True
    assert result.external_evidence_applied is True


def test_mixed_external_signals_count_only_verified_support():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A source boundary is missing.")

    manager.submit_signals(
        seed_id,
        [
            ValidationSignal(kind=SignalKind.SSOT, verified=False),
            ValidationSignal(kind=SignalKind.RETRIEVAL, verified=True),
            ValidationSignal(kind=SignalKind.HUMAN_FEEDBACK, verified=False),
        ],
        policy_id="exploratory",
    )

    assert manager.get_seed(seed_id).evidence_count == 1


def test_recurrence_can_validate_without_promoting_unverified_signal_to_evidence():
    manager = _manager()
    seed_id = manager.add_or_update_seed("A recurring boundary is missing.")
    unverified = ValidationSignal(kind=SignalKind.SSOT, verified=False)

    event = manager.submit_signals(
        seed_id,
        [recurrence_signal(3, threshold=2), unverified],
        policy_id="exploratory",
    )

    assert event.decision is GateDecision.VALIDATED
    assert unverified in event.signals
    assert manager.get_seed(seed_id).evidence_count == 0
    result = manager.validation_log[-1]
    assert result.internal_recognition_passed is True
    assert result.external_evidence_passed is False
    assert result.external_evidence_applied is False


def test_contradiction_boolean_synthesizes_opposition_when_supplied_signal_is_not_opposing():
    manager = _manager()
    seed_id = _recurrent_seed(manager)
    non_opposing = ValidationSignal(
        kind=SignalKind.CONTRADICTION,
        direction=SignalDirection.SUPPORT,
        reason="caller supplied a non-opposing contradiction signal",
    )

    result = manager.run_validation_gate_detailed(
        seed_id,
        external_evidence=True,
        contradiction=True,
        signals=[non_opposing],
    )

    assert result.verdict == "contradicted"
    assert result.contradiction_applied is True
    assert any(
        signal.kind is SignalKind.CONTRADICTION
        and signal.direction is SignalDirection.OPPOSE
        for signal in manager.gate_events[-1].signals
    )


def test_legacy_policy_blocks_while_a_contradiction_record_remains_open():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    contradicted = manager.run_validation_gate_detailed(seed_id, contradiction=True)
    assert contradicted.verdict == "contradicted"

    manager.add_or_update_seed("A relevant boundary is missing.")
    manager.add_or_update_seed("A relevant boundary is missing.")
    first = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    second = manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    assert first.verdict == "blocked"
    assert second.verdict == "blocked"
    assert first.contradiction_free is False
    assert second.contradiction_free is False
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager._contradiction_state(manager.get_seed(seed_id)).blocking is True
