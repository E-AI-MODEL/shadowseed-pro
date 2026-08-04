"""Verified-evidence semantics for the derived validation log.

Gate events retain every submitted signal for auditability. The derived legacy
validation fields, however, may call external support "evidence" only when the
signal was explicitly verified. ``SSLManager._log_validation_from_signals``
delegates here; nothing is installed onto the class at import time.
"""

from __future__ import annotations

from typing import Any

from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal


def log_validation_from_signals(
    manager: Any,
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
        # Derived from the seed's actual contradiction state, not from the
        # decision: a call blocked by an already-open contradiction returns
        # BLOCKED (not CONTRADICTED), so keying off the decision would log
        # contradiction_free=True while the record is still open.
        contradiction_free=not manager._contradiction_state(seed).blocking,
        external_evidence_applied=has_verified_external_support,
        contradiction_applied=decision is GateDecision.CONTRADICTED,
        promoted=decision is GateDecision.PROMOTED,
        verdict=manager._DECISION_TO_VERDICT.get(decision, "blocked"),
    )
    manager.validation_log.append(result)


__all__ = ["log_validation_from_signals"]
