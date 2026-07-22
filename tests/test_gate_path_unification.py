"""Regression tests for the single executable Validation Gate path."""

from __future__ import annotations

import numpy as np

from shadowseed.gate import SignalKind, ValidationSignal, recurrence_signal
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


def test_legacy_boolean_api_records_one_event_from_real_policy():
    manager = _manager()
    seed_id = _recurrent_seed(manager)

    result = manager.run_validation_gate_detailed(
        seed_id,
        external_evidence=True,
    )

    assert result.verdict == "validated"
    assert len(manager.gate_events) == 1
    assert len(manager.validation_log) == 1
    event = manager.gate_events[0]
    assert event.policy_id == "legacy_evidence_required"
    assert {signal.kind for signal in event.signals} == {
        SignalKind.RECURRENCE,
        SignalKind.SSOT,
    }


def test_legacy_policy_preserves_manager_validation_increment():
    manager = _manager(validation_increment=0.35, promotion_threshold=0.3)
    seed_id = _recurrent_seed(manager)

    allowed = manager.run_validation_gate(seed_id, external_evidence=True)

    assert allowed is True
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

    result = manager._run_validation_gate_core(
        seed_id,
        external_evidence=True,
    )

    assert result.verdict == "validated"
    assert len(manager.gate_events) == 1
    assert manager.gate_events[0].policy_id == "legacy_evidence_required"


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
    assert manager.get_seed(seed_id).weight == 0.0
