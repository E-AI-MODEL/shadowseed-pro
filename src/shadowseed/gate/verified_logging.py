"""Verified-evidence semantics for compatibility validation logs.

Gate events retain every submitted signal for auditability. The derived legacy
validation fields, however, may call external support "evidence" only when the
signal was explicitly verified.
"""

from __future__ import annotations

from typing import Any

from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal


def _verified_log_validation_from_signals(
    self: Any,
    seed: Any,
    decision: GateDecision,
    signals: list[ValidationSignal],
    *,
    status_before: str,
    weight_before: float,
) -> None:
    from shadowseed.manager import ValidationGateResult

    has_recurrence_support = any(
        signal.kind is SignalKind.RECURRENCE
        and signal.direction is SignalDirection.SUPPORT
        for signal in signals
    )
    has_verified_external_support = any(
        signal.is_external_evidence
        and signal.direction is SignalDirection.SUPPORT
        and signal.verified
        for signal in signals
    )
    result = ValidationGateResult(
        seed_id=seed.id,
        status_before=status_before,
        status_after=seed.status.value,
        weight_before=weight_before,
        weight_after=seed.weight,
        occurrence_count=seed.occurrence_count,
        evidence_count=seed.evidence_count,
        internal_recognition_passed=has_recurrence_support,
        external_evidence_passed=has_verified_external_support,
        contradiction_free=decision is not GateDecision.CONTRADICTED,
        external_evidence_applied=has_verified_external_support,
        contradiction_applied=decision is GateDecision.CONTRADICTED,
        promoted=decision is GateDecision.PROMOTED,
        verdict=self._DECISION_TO_VERDICT.get(decision, "blocked"),
    )
    self.validation_log.append(result)


def install_verified_gate_logging() -> None:
    """Make derived validation logs count only verified external support."""

    from shadowseed.manager import SSLManager

    SSLManager._log_validation_from_signals = _verified_log_validation_from_signals
