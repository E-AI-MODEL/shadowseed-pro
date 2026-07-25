"""The one executable Validation Gate engine.

This module holds the *only* implementation that decides authority changes.
``SSLManager`` does not re-implement it: its Gate methods (``submit_signals``,
``run_validation_gate``, ``run_validation_gate_detailed``) delegate here
explicitly, so a reader of ``manager.py`` can follow one call into the real
body. Nothing is installed onto the class at import time.

The historical boolean API is retained as an input/output adapter only: it
translates booleans into typed signals, runs this same engine, and translates
the resulting event back into the legacy return shape. Every call applies one
policy and records exactly one ``GateEvent`` under the policy that actually
decided it.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.gate.policies import AuthoritySnapshot, ProposedVerdict, resolve_policy
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)
from shadowseed.gate.verified_logging import log_validation_from_signals

LEGACY_POLICY_ID = "legacy_evidence_required"


def _supporting_recurrence(signals: list[ValidationSignal]) -> bool:
    return any(
        signal.kind is SignalKind.RECURRENCE
        and signal.direction is SignalDirection.SUPPORT
        for signal in signals
    )


def _verified_external(signals: list[ValidationSignal]) -> list[ValidationSignal]:
    return [
        signal
        for signal in signals
        if signal.is_external_evidence
        and signal.direction is SignalDirection.SUPPORT
        and signal.verified
    ]


def _opposing_contradiction(signals: list[ValidationSignal]) -> ValidationSignal | None:
    return next(
        (
            signal
            for signal in signals
            if signal.kind is SignalKind.CONTRADICTION
            and signal.direction is SignalDirection.OPPOSE
        ),
        None,
    )


def _legacy_result(
    manager: Any,
    *,
    seed: Any,
    status_before: str,
    weight_before: float,
    internal_recognition_passed: bool,
    external_evidence_passed: bool,
    contradiction_free: bool,
    external_evidence_applied: bool,
    contradiction_applied: bool,
    verdict: str,
):
    from shadowseed.manager import ValidationGateResult

    result = ValidationGateResult(
        seed_id=seed.id,
        status_before=status_before,
        status_after=seed.status.value,
        weight_before=weight_before,
        weight_after=seed.weight,
        occurrence_count=seed.occurrence_count,
        evidence_count=seed.evidence_count,
        internal_recognition_passed=internal_recognition_passed,
        external_evidence_passed=external_evidence_passed,
        contradiction_free=contradiction_free,
        external_evidence_applied=external_evidence_applied,
        contradiction_applied=contradiction_applied,
        promoted=verdict == "promoted",
        verdict=verdict,
    )
    manager.validation_log.append(result)
    return result


def _submit_legacy_signals(
    manager: Any,
    seed_id: str,
    signal_list: list[ValidationSignal],
) -> GateEvent:
    """Apply historical threshold semantics through the unified Gate boundary."""

    seed = manager._seeds[seed_id]
    status_before = seed.status.value
    weight_before = seed.weight
    contradiction_before = manager._contradiction_state(seed)
    external_signals = _verified_external(signal_list)
    contradiction_signal = _opposing_contradiction(signal_list)
    external_applied = bool(external_signals)
    contradiction_applied = contradiction_signal is not None

    if seed.status.value == "EXPIRED":
        _legacy_result(
            manager,
            seed=seed,
            status_before=status_before,
            weight_before=weight_before,
            internal_recognition_passed=False,
            external_evidence_passed=False,
            contradiction_free=not contradiction_applied
            and not contradiction_before.blocking,
            external_evidence_applied=False,
            contradiction_applied=contradiction_applied,
            verdict="expired",
        )
        event = manager._record_gate_event(
            seed,
            GateDecision.EXPIRED,
            signal_list,
            policy_id=LEGACY_POLICY_ID,
            status_before=status_before,
            weight_before=weight_before,
            contradiction_before=contradiction_before,
            reason="expired seed is terminal",
        )
        manager._sync_seed(seed_id)
        return event

    if external_signals:
        manager._set_authority(
            seed,
            evidence_count=seed.evidence_count + len(external_signals),
        )

    internal_passed = (
        seed.occurrence_count >= manager.config.min_occurrences_for_gate
        and seed.trace > manager.config.min_trace_for_gate
    )
    evidence_passed = seed.evidence_count >= manager.config.min_evidence_for_gate
    contradiction_free = (
        contradiction_signal is None and not contradiction_before.blocking
    )

    if contradiction_signal is not None:
        manager._open_contradiction_record(
            seed,
            reason=contradiction_signal.reason or "validation gate contradiction",
            source_ref=contradiction_signal.source_ref,
            strength=contradiction_signal.strength,
        )
        manager._set_authority(
            seed,
            weight=max(0.0, seed.weight - manager.contradiction_penalty),
            contradiction_score=min(1.0, seed.contradiction_score + 0.25),
            status=type(seed.status).NEW,
        )
        seed.occurrence_count = 1
        if manager.contradiction_trace_penalty:
            seed.trace = max(0.0, seed.trace - manager.contradiction_trace_penalty)
        seed.turns_dormant = 0
        manager._touch_seed(seed)
        verdict = "contradicted"
        decision = GateDecision.CONTRADICTED
        event_type = "contradicted"
        event_detail = {"weight_after": seed.weight}
    elif internal_passed and evidence_passed and contradiction_free:
        new_weight = min(1.0, seed.weight + manager.validation_increment)
        new_status = (
            type(seed.status).PROMOTED
            if new_weight >= manager.promotion_threshold
            else type(seed.status).ACTIVE
        )
        manager._set_authority(seed, weight=new_weight, status=new_status)
        manager._touch_seed(seed)
        verdict = "promoted" if new_status.value == "PROMOTED" else "validated"
        decision = (
            GateDecision.PROMOTED
            if new_status.value == "PROMOTED"
            else GateDecision.VALIDATED
        )
        event_type = "validated"
        event_detail = {
            "promoted": verdict == "promoted",
            "weight_after": seed.weight,
            "evidence_count": seed.evidence_count,
        }
    else:
        verdict = "blocked"
        decision = GateDecision.BLOCKED
        event_type = "validation_blocked"
        event_detail = {
            "internal_recognition_passed": internal_passed,
            "external_evidence_passed": evidence_passed,
            "contradiction_free": contradiction_free,
        }

    _legacy_result(
        manager,
        seed=seed,
        status_before=status_before,
        weight_before=weight_before,
        internal_recognition_passed=internal_passed,
        external_evidence_passed=evidence_passed,
        contradiction_free=contradiction_free,
        external_evidence_applied=external_applied,
        contradiction_applied=contradiction_applied,
        verdict=verdict,
    )
    manager._record_event(event_type, seed_id, **event_detail)
    event = manager._record_gate_event(
        seed,
        decision,
        signal_list,
        policy_id=LEGACY_POLICY_ID,
        status_before=status_before,
        weight_before=weight_before,
        contradiction_before=contradiction_before,
        reason=f"legacy compatibility verdict={verdict}",
    )
    manager._sync_seed(seed_id)
    return event


def submit_signals(
    manager: Any,
    seed_id: str,
    signals: Iterable[ValidationSignal],
    policy_id: str | None = None,
) -> GateEvent:
    """Apply one policy, one authority transition, and one Gate event."""

    signal_list = list(signals)
    selected_policy = policy_id or "exploratory"
    if selected_policy == LEGACY_POLICY_ID:
        return _submit_legacy_signals(manager, seed_id, signal_list)

    seed = manager._seeds[seed_id]
    policy = resolve_policy(selected_policy)
    status_before = seed.status.value
    weight_before = seed.weight
    contradiction_before = manager._contradiction_state(seed)

    if seed.status.value == "EXPIRED":
        return manager._record_gate_event(
            seed,
            GateDecision.EXPIRED,
            signal_list,
            policy_id=policy.policy_id,
            status_before=status_before,
            weight_before=weight_before,
            contradiction_before=contradiction_before,
            reason="expired seed is terminal",
        )

    proposal = policy.propose(
        signal_list,
        AuthoritySnapshot(
            weight=seed.weight,
            status=seed.status.value,
            has_blocking_contradiction=contradiction_before.blocking,
        ),
    )

    if proposal.verdict is ProposedVerdict.CONTRADICT:
        contradiction_signal = _opposing_contradiction(signal_list)
        manager._open_contradiction_record(
            seed,
            reason=(contradiction_signal.reason if contradiction_signal else "")
            or "contradiction signal",
            source_ref=(
                contradiction_signal.source_ref if contradiction_signal else None
            ),
            strength=(
                contradiction_signal.strength if contradiction_signal else 1.0
            ),
        )
        manager._set_authority(
            seed,
            weight=max(0.0, seed.weight - manager.contradiction_penalty),
            contradiction_score=min(1.0, seed.contradiction_score + 0.25),
            status=type(seed.status).NEW,
        )
        seed.occurrence_count = 1
        if manager.contradiction_trace_penalty:
            seed.trace = max(0.0, seed.trace - manager.contradiction_trace_penalty)
        seed.turns_dormant = 0
        manager._touch_seed(seed)
        decision = GateDecision.CONTRADICTED
    elif (
        proposal.verdict is ProposedVerdict.PROMOTE_OR_VALIDATE
        and proposal.satisfied
    ):
        new_weight = min(1.0, seed.weight + proposal.weight_delta)
        new_status = (
            type(seed.status).PROMOTED
            if new_weight >= manager.promotion_threshold
            else type(seed.status).ACTIVE
        )
        external_support = len(_verified_external(signal_list))
        manager._set_authority(
            seed,
            weight=new_weight,
            status=new_status,
            evidence_count=(
                seed.evidence_count + external_support
                if external_support
                else None
            ),
        )
        manager._touch_seed(seed)
        decision = (
            GateDecision.PROMOTED
            if new_status.value == "PROMOTED"
            else GateDecision.VALIDATED
        )
    else:
        decision = GateDecision.BLOCKED

    manager._log_validation_from_signals(
        seed,
        decision,
        signal_list,
        status_before=status_before,
        weight_before=weight_before,
    )
    event = manager._record_gate_event(
        seed,
        decision,
        signal_list,
        policy_id=policy.policy_id,
        status_before=status_before,
        weight_before=weight_before,
        contradiction_before=contradiction_before,
        reason=proposal.reason,
    )
    manager._sync_seed(seed_id)
    return event


def _compatibility_signals(
    manager: Any,
    seed_id: str,
    *,
    external_evidence: bool,
    contradiction: bool,
    signals: Iterable[ValidationSignal] | None,
) -> list[ValidationSignal]:
    seed = manager._seeds[seed_id]
    collected = list(signals or ())
    if not any(signal.kind is SignalKind.RECURRENCE for signal in collected):
        collected.insert(
            0,
            recurrence_signal(
                seed.occurrence_count,
                threshold=manager.config.min_occurrences_for_gate,
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
        signal.kind is SignalKind.CONTRADICTION
        and signal.direction is SignalDirection.OPPOSE
        for signal in collected
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


def run_validation_gate_detailed(
    manager: Any,
    seed_id: str,
    external_evidence: bool = False,
    contradiction: bool = False,
    signals: Iterable[ValidationSignal] | None = None,
    policy_id: str | None = None,
):
    before = len(manager.validation_log)
    event = submit_signals(
        manager,
        seed_id,
        _compatibility_signals(
            manager,
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
            signals=signals,
        ),
        policy_id=policy_id or LEGACY_POLICY_ID,
    )
    if len(manager.validation_log) > before:
        return manager.validation_log[-1]

    from shadowseed.manager import ValidationGateResult

    seed = manager._seeds[seed_id]
    return ValidationGateResult(
        seed_id=seed_id,
        status_before=event.status_before,
        status_after=event.status_after,
        weight_before=event.weight_before,
        weight_after=event.weight_after,
        occurrence_count=seed.occurrence_count,
        evidence_count=seed.evidence_count,
        internal_recognition_passed=False,
        external_evidence_passed=False,
        contradiction_free=event.decision is not GateDecision.CONTRADICTED,
        external_evidence_applied=False,
        contradiction_applied=event.decision is GateDecision.CONTRADICTED,
        promoted=event.decision is GateDecision.PROMOTED,
        verdict=event.decision.value,
    )


def run_validation_gate(
    manager: Any,
    seed_id: str,
    external_evidence: bool = False,
    contradiction: bool = False,
    signals: Iterable[ValidationSignal] | None = None,
    policy_id: str | None = None,
) -> bool | None:
    result = run_validation_gate_detailed(
        manager,
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


__all__ = [
    "submit_signals",
    "run_validation_gate",
    "run_validation_gate_detailed",
    "log_validation_from_signals",
    "LEGACY_POLICY_ID",
]
