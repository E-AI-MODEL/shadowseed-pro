"""Compatibility adapters that route legacy Gate calls through one engine.

The historical boolean API remains callable, but it now translates its inputs
into typed signals and delegates authority changes to ``SSLManager.submit_signals``.
"""

from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from threading import RLock
from typing import Any

from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.gate.policies import LegacyEvidenceRequiredPolicy
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)

LEGACY_POLICY_ID = "legacy_evidence_required"
_POLICY_LOCK = RLock()


@contextmanager
def _configured_legacy_policy(manager: Any):
    """Use the manager's configured increment without creating another Gate."""

    from shadowseed.gate import policies

    with _POLICY_LOCK:
        previous = policies._COMPATIBILITY_REGISTRY[LEGACY_POLICY_ID]
        policies._COMPATIBILITY_REGISTRY[LEGACY_POLICY_ID] = (
            LegacyEvidenceRequiredPolicy(
                weight_increment=manager.validation_increment
            )
        )
        try:
            yield
        finally:
            policies._COMPATIBILITY_REGISTRY[LEGACY_POLICY_ID] = previous


def _compatibility_signals(
    self: Any,
    seed_id: str,
    *,
    external_evidence: bool,
    contradiction: bool,
    signals: Iterable[ValidationSignal] | None,
) -> list[ValidationSignal]:
    seed = self._seeds[seed_id]
    collected = list(signals or ())

    if not any(signal.kind is SignalKind.RECURRENCE for signal in collected):
        collected.insert(
            0,
            recurrence_signal(
                seed.occurrence_count,
                threshold=self.config.min_occurrences_for_gate,
            ),
        )
    if external_evidence and not any(
        signal.is_external_evidence and signal.verified for signal in collected
    ):
        collected.append(
            ValidationSignal(
                kind=SignalKind.SSOT,
                direction=SignalDirection.SUPPORT,
                strength=1.0,
                verified=True,
                reason="legacy external_evidence=True",
            )
        )
    if contradiction and not any(
        signal.kind is SignalKind.CONTRADICTION for signal in collected
    ):
        collected.append(
            ValidationSignal(
                kind=SignalKind.CONTRADICTION,
                direction=SignalDirection.OPPOSE,
                strength=1.0,
                reason="legacy contradiction=True",
            )
        )
    return collected


def _result_from_event(self: Any, event: GateEvent, log_size_before: int):
    from shadowseed.manager import ValidationGateResult

    if len(self.validation_log) > log_size_before:
        return self.validation_log[-1]

    signals = list(event.signals)
    seed = self._seeds[event.seed_id]
    recurrence = any(
        signal.kind is SignalKind.RECURRENCE
        and signal.direction is SignalDirection.SUPPORT
        for signal in signals
    )
    external = any(
        signal.is_external_evidence
        and signal.direction is SignalDirection.SUPPORT
        and signal.verified
        for signal in signals
    )
    contradicted = event.decision is GateDecision.CONTRADICTED
    return ValidationGateResult(
        seed_id=event.seed_id,
        status_before=event.status_before,
        status_after=event.status_after,
        weight_before=event.weight_before,
        weight_after=event.weight_after,
        occurrence_count=seed.occurrence_count,
        evidence_count=seed.evidence_count,
        internal_recognition_passed=recurrence,
        external_evidence_passed=external,
        contradiction_free=not contradicted,
        external_evidence_applied=external,
        contradiction_applied=contradicted,
        promoted=event.decision is GateDecision.PROMOTED,
        verdict=event.decision.value,
    )


def _run_validation_gate_detailed(
    self: Any,
    seed_id: str,
    external_evidence: bool = False,
    contradiction: bool = False,
    signals: Iterable[ValidationSignal] | None = None,
    policy_id: str | None = None,
):
    signal_list = _compatibility_signals(
        self,
        seed_id,
        external_evidence=external_evidence,
        contradiction=contradiction,
        signals=signals,
    )
    selected_policy = policy_id or LEGACY_POLICY_ID
    log_size_before = len(self.validation_log)

    if selected_policy == LEGACY_POLICY_ID:
        with _configured_legacy_policy(self):
            event = self.submit_signals(
                seed_id,
                signal_list,
                policy_id=selected_policy,
            )
    else:
        event = self.submit_signals(
            seed_id,
            signal_list,
            policy_id=selected_policy,
        )
    return _result_from_event(self, event, log_size_before)


def _run_validation_gate(
    self: Any,
    seed_id: str,
    external_evidence: bool = False,
    contradiction: bool = False,
    signals: Iterable[ValidationSignal] | None = None,
    policy_id: str | None = None,
) -> bool | None:
    result = self.run_validation_gate_detailed(
        seed_id,
        external_evidence=external_evidence,
        contradiction=contradiction,
        signals=signals,
        policy_id=policy_id,
    )
    if result.verdict == "contradicted":
        return False
    if result.verdict in {"validated", "promoted"}:
        return True
    return None


def install_gate_runtime_adapter() -> None:
    """Replace legacy decision methods with signal-native adapters."""

    from shadowseed.manager import SSLManager

    SSLManager.run_validation_gate_detailed = _run_validation_gate_detailed
    SSLManager.run_validation_gate = _run_validation_gate
    SSLManager._run_validation_gate_core = _run_validation_gate_detailed
