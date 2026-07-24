"""Install one executable Validation Gate engine on ``SSLManager``.

The historical boolean API is retained as an input/output adapter. All authority
changes are decided by the signal-native Gate path and produce one ``GateEvent``.
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
    self: Any,
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
    self.validation_log.append(result)
    return result


def _submit_legacy_signals(
    self: Any,
    seed_id: str,
    signal_list: list[ValidationSignal],
) -> GateEvent:
    """Apply historical threshold semantics through the unified Gate boundary."""

    seed = self._seeds[seed_id]
    status_before = seed.status.value
    weight_before = seed.weight
    contradiction_before = self._contradiction_state(seed)
    external_signals = _verified_external(signal_list)
    contradiction_signal = _opposing_contradiction(signal_list)
    external_applied = bool(external_signals)
    contradiction_applied = contradiction_signal is not None

    if seed.status.value == "EXPIRED":
        _legacy_result(
            self,
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
        event = self._record_gate_event(
            seed,
            GateDecision.EXPIRED,
            signal_list,
            policy_id=LEGACY_POLICY_ID,
            status_before=status_before,
            weight_before=weight_before,
            contradiction_before=contradiction_before,
            reason="expired seed is terminal",
        )
        self._sync_seed(seed_id)
        return event

    if external_signals:
        self._set_authority(
            seed,
            evidence_count=seed.evidence_count + len(external_signals),
        )

    internal_passed = (
        seed.occurrence_count >= self.config.min_occurrences_for_gate
        and seed.trace > self.config.min_trace_for_gate
    )
    evidence_passed = seed.evidence_count >= self.config.min_evidence_for_gate
    contradiction_free = (
        contradiction_signal is None and not contradiction_before.blocking
    )

    if contradiction_signal is not None:
        self._open_contradiction_record(
            seed,
            reason=contradiction_signal.reason or "validation gate contradiction",
            source_ref=contradiction_signal.source_ref,
            strength=contradiction_signal.strength,
        )
        self._set_authority(
            seed,
            weight=max(0.0, seed.weight - self.contradiction_penalty),
            contradiction_score=min(1.0, seed.contradiction_score + 0.25),
            status=type(seed.status).NEW,
        )
        seed.occurrence_count = 1
        if self.contradiction_trace_penalty:
            seed.trace = max(0.0, seed.trace - self.contradiction_trace_penalty)
        seed.turns_dormant = 0
        self._touch_seed(seed)
        verdict = "contradicted"
        decision = GateDecision.CONTRADICTED
        event_type = "contradicted"
        event_detail = {"weight_after": seed.weight}
    elif internal_passed and evidence_passed and contradiction_free:
        new_weight = min(1.0, seed.weight + self.validation_increment)
        new_status = (
            type(seed.status).PROMOTED
            if new_weight >= self.promotion_threshold
            else type(seed.status).ACTIVE
        )
        self._set_authority(seed, weight=new_weight, status=new_status)
        self._touch_seed(seed)
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
        self,
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
    self._record_event(event_type, seed_id, **event_detail)
    event = self._record_gate_event(
        seed,
        decision,
        signal_list,
        policy_id=LEGACY_POLICY_ID,
        status_before=status_before,
        weight_before=weight_before,
        contradiction_before=contradiction_before,
        reason=f"legacy compatibility verdict={verdict}",
    )
    self._sync_seed(seed_id)
    return event


def _unified_submit_signals(
    self: Any,
    seed_id: str,
    signals: Iterable[ValidationSignal],
    policy_id: str | None = None,
) -> GateEvent:
    """Apply one policy, one authority transition, and one Gate event."""

    signal_list = list(signals)
    selected_policy = policy_id or "exploratory"
    if selected_policy == LEGACY_POLICY_ID:
        return _submit_legacy_signals(self, seed_id, signal_list)

    seed = self._seeds[seed_id]
    policy = resolve_policy(selected_policy)
    status_before = seed.status.value
    weight_before = seed.weight
    contradiction_before = self._contradiction_state(seed)

    if seed.status.value == "EXPIRED":
        return self._record_gate_event(
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
        self._open_contradiction_record(
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
        self._set_authority(
            seed,
            weight=max(0.0, seed.weight - self.contradiction_penalty),
            contradiction_score=min(1.0, seed.contradiction_score + 0.25),
            status=type(seed.status).NEW,
        )
        seed.occurrence_count = 1
        if self.contradiction_trace_penalty:
            seed.trace = max(0.0, seed.trace - self.contradiction_trace_penalty)
        seed.turns_dormant = 0
        self._touch_seed(seed)
        decision = GateDecision.CONTRADICTED
    elif (
        proposal.verdict is ProposedVerdict.PROMOTE_OR_VALIDATE
        and proposal.satisfied
    ):
        new_weight = min(1.0, seed.weight + proposal.weight_delta)
        new_status = (
            type(seed.status).PROMOTED
            if new_weight >= self.promotion_threshold
            else type(seed.status).ACTIVE
        )
        external_support = len(_verified_external(signal_list))
        self._set_authority(
            seed,
            weight=new_weight,
            status=new_status,
            evidence_count=(
                seed.evidence_count + external_support
                if external_support
                else None
            ),
        )
        self._touch_seed(seed)
        decision = (
            GateDecision.PROMOTED
            if new_status.value == "PROMOTED"
            else GateDecision.VALIDATED
        )
    else:
        decision = GateDecision.BLOCKED

    self._log_validation_from_signals(
        seed,
        decision,
        signal_list,
        status_before=status_before,
        weight_before=weight_before,
    )
    event = self._record_gate_event(
        seed,
        decision,
        signal_list,
        policy_id=policy.policy_id,
        status_before=status_before,
        weight_before=weight_before,
        contradiction_before=contradiction_before,
        reason=proposal.reason,
    )
    self._sync_seed(seed_id)
    return event


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


def _run_validation_gate_detailed(
    self: Any,
    seed_id: str,
    external_evidence: bool = False,
    contradiction: bool = False,
    signals: Iterable[ValidationSignal] | None = None,
    policy_id: str | None = None,
):
    before = len(self.validation_log)
    event = self.submit_signals(
        seed_id,
        _compatibility_signals(
            self,
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
            signals=signals,
        ),
        policy_id=policy_id or LEGACY_POLICY_ID,
    )
    if len(self.validation_log) > before:
        return self.validation_log[-1]

    from shadowseed.manager import ValidationGateResult

    seed = self._seeds[seed_id]
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
    """Install one Gate engine and legacy input/output adapters."""

    from shadowseed.manager import SSLManager

    SSLManager.submit_signals = _unified_submit_signals
    SSLManager.run_validation_gate_detailed = _run_validation_gate_detailed
    SSLManager.run_validation_gate = _run_validation_gate
    SSLManager._run_validation_gate_core = _run_validation_gate_detailed
