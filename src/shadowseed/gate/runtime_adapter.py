"""Compatibility adapters that route every Gate call through one engine.

The manager historically exposed a boolean Gate API alongside the newer typed
signal API. This module keeps the public boolean methods working while replacing
their decision path with the signal-native ``submit_signals`` implementation.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.gate.policies import (
    AuthoritySnapshot,
    LegacyEvidenceRequiredPolicy,
    ProposedVerdict,
    resolve_policy,
)
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)

LEGACY_POLICY_ID = "legacy_evidence_required"


def _policy_for(manager: Any, policy_id: str | None):
    if policy_id == LEGACY_POLICY_ID:
        return LegacyEvidenceRequiredPolicy(
            weight_increment=manager.validation_increment
        )
    return resolve_policy(policy_id)


def _unified_submit_signals(
    self: Any,
    seed_id: str,
    signals: Iterable[ValidationSignal],
    policy_id: str | None = None,
) -> GateEvent:
    """Apply one named policy and record one authoritative Gate event."""

    seed = self._seeds[seed_id]
    policy = _policy_for(self, policy_id)
    signal_list = list(signals)
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

    snapshot = AuthoritySnapshot(
        weight=seed.weight,
        status=seed.status.value,
        has_blocking_contradiction=contradiction_before.blocking,
    )
    proposal = policy.propose(signal_list, snapshot)

    if proposal.verdict is ProposedVerdict.CONTRADICT:
        contradiction_signal = next(
            (
                signal
                for signal in signal_list
                if signal.kind is SignalKind.CONTRADICTION
            ),
            None,
        )
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
        external_support = sum(
            1
            for signal in signal_list
            if signal.is_external_evidence
            and signal.direction is SignalDirection.SUPPORT
        )
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


def _result_from_event(self: Any, event: GateEvent):
    from shadowseed.manager import ValidationGateResult

    if self.validation_log:
        last = self.validation_log[-1]
        if last.seed_id == event.seed_id and last.status_after == event.status_after:
            return last

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
    event = self.submit_signals(
        seed_id,
        signal_list,
        policy_id=policy_id or LEGACY_POLICY_ID,
    )
    return _result_from_event(self, event)


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
    """Replace the duplicate manager path with compatibility adapters."""

    from shadowseed.manager import SSLManager

    SSLManager.submit_signals = _unified_submit_signals
    SSLManager.run_validation_gate_detailed = _run_validation_gate_detailed
    SSLManager.run_validation_gate = _run_validation_gate
    SSLManager._run_validation_gate_core = _run_validation_gate_detailed
