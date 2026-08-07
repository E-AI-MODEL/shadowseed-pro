"""The one executable Validation Gate engine.

This module holds the *only* implementation that decides Gate-controlled
authority changes.
``SSLManager`` does not re-implement them: its signal-native Gate methods and
the bounded probe-feedback / contradiction-resolution authority workflows
delegate here explicitly, so a reader of ``manager.py`` can follow one call
into the real decision body. Nothing is installed onto the class at import time.

The historical boolean API is retained as an input/output adapter only: it
translates booleans into typed signals, runs this same engine, and translates
the resulting event back into the legacy return shape. Every call applies one
policy and records exactly one ``GateEvent`` under the policy that actually
decided it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
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

    # The legacy verdict is decided by the registered legacy policy itself,
    # rebuilt from this manager's configured thresholds. Resolving and calling
    # the policy here is what makes the recorded policy_id truthful: there is no
    # second decision rule living in this adapter.
    policy = replace(
        resolve_policy(LEGACY_POLICY_ID),
        weight_increment=manager.validation_increment,
        min_occurrences=manager.config.min_occurrences_for_gate,
        min_trace=manager.config.min_trace_for_gate,
        min_evidence=manager.config.min_evidence_for_gate,
    )
    snapshot = AuthoritySnapshot(
        weight=seed.weight,
        status=seed.status.value,
        has_blocking_contradiction=contradiction_before.blocking,
        evidence_count=seed.evidence_count,
        occurrence_count=seed.occurrence_count,
        trace=seed.trace,
    )
    proposal = policy.propose(signal_list, snapshot)

    # The legacy result shape reports the individual gate conditions, so read
    # them back from the same policy that just decided.
    internal_passed = policy.internal_recognition(snapshot)
    evidence_passed = policy.evidence_satisfied(snapshot)
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


def resolve_contradiction(
    manager: Any,
    seed_id: str,
    *,
    basis: str,
    contradiction_id: str | None = None,
    superseded: bool = False,
    withdrawn: bool = False,
    resolver: str = "human",
) -> GateEvent:
    """Apply formal contradiction resolution at the authority boundary.

    The contradiction domain owns record lifecycle mechanics. This Gate engine
    owns the authority effect: the compatibility scalar clear, typed resolution
    signal, and immutable Gate event occur in one bounded workflow. Resolution
    only unblocks; it never restores weight or promotion.
    """

    from shadowseed.models import SeedStatus

    seed = manager._seeds[seed_id]
    if seed.status == SeedStatus.EXPIRED:
        raise ValueError(
            "expired seeds cannot recover through contradiction resolution"
        )

    status_before = seed.status.value
    weight_before = seed.weight
    contradiction_before = manager._contradiction_state(seed)
    manager._contradictions.resolve(
        seed_id,
        basis=basis,
        contradiction_id=contradiction_id,
        superseded=superseded,
        withdrawn=withdrawn,
        resolved_at=manager._now_iso,
        open_records=manager.open_contradictions(seed_id),
    )
    if not manager.open_contradictions(seed_id):
        manager._set_authority(seed, contradiction_score=0.0)
    manager._touch_seed(seed)
    signal = ValidationSignal(
        kind=SignalKind.CONTRADICTION_RESOLUTION,
        direction=SignalDirection.SUPPORT,
        strength=1.0,
        source_ref=resolver,
        reason=basis,
    )
    return manager._record_gate_event(
        seed,
        GateDecision.CONTRADICTION_RESOLVED,
        [signal],
        policy_id="contradiction_resolution",
        status_before=status_before,
        weight_before=weight_before,
        contradiction_before=contradiction_before,
        reason=f"resolved by {resolver}: {basis}",
    )


def apply_probe_feedback(
    manager: Any,
    seed_id: str,
    outcome: Any,
    probe_type: Any,
):
    """Apply bounded probe feedback at the canonical authority boundary.

    ACTIVE and PROMOTED seeds accept bounded weight nudges. Rewards cannot
    promote on their own; penalties may demote a promoted seed below the
    configured threshold. Non-feedbackable states retain the historical skipped
    result and do not create a Gate event.
    """

    from shadowseed.models import (
        ProbeFeedbackResult,
        ProbeOutcome,
        ProbeType,
        SeedStatus,
    )

    if seed_id not in manager._seeds:
        raise KeyError(f"Seed '{seed_id}' does not exist.")

    seed = manager._seeds[seed_id]
    outcome_enum = ProbeOutcome(outcome)
    probe_type_enum = ProbeType(probe_type)
    status_before = seed.status.value
    weight_before = seed.weight

    feedbackable = {SeedStatus.ACTIVE, SeedStatus.PROMOTED}
    if seed.status not in feedbackable:
        result = ProbeFeedbackResult(
            seed_id=seed_id,
            probe_type=probe_type_enum.value,
            outcome=outcome_enum.value,
            weight_before=weight_before,
            weight_after=weight_before,
            delta_applied=0.0,
            status_before=status_before,
            status_after=status_before,
            demoted=False,
            skipped=True,
            skip_reason=f"status '{seed.status.value}' does not accept feedback",
        )
        manager.feedback_log.append(result)
        return result

    delta_map = {
        ProbeOutcome.REWARD: manager.reward_step,
        ProbeOutcome.PENALTY: -manager.penalty_step,
        ProbeOutcome.NEUTRAL: 0.0,
    }
    delta_requested = delta_map[outcome_enum]
    new_weight = max(0.0, min(1.0, seed.weight + delta_requested))
    demoted = (
        seed.status == SeedStatus.PROMOTED
        and new_weight < manager.promotion_threshold
    )

    manager._set_authority(
        seed,
        weight=new_weight,
        status=SeedStatus.ACTIVE if demoted else None,
    )
    manager._touch_seed(seed)

    delta_applied = seed.weight - weight_before
    result = ProbeFeedbackResult(
        seed_id=seed_id,
        probe_type=probe_type_enum.value,
        outcome=outcome_enum.value,
        weight_before=weight_before,
        weight_after=seed.weight,
        delta_applied=delta_applied,
        status_before=status_before,
        status_after=seed.status.value,
        demoted=demoted,
        skipped=False,
        skip_reason="",
    )
    manager.feedback_log.append(result)

    probe_direction = {
        ProbeOutcome.REWARD: SignalDirection.SUPPORT,
        ProbeOutcome.PENALTY: SignalDirection.OPPOSE,
        ProbeOutcome.NEUTRAL: SignalDirection.NEUTRAL,
    }[outcome_enum]
    if demoted:
        decision = GateDecision.DEMOTED
    elif delta_applied != 0.0:
        decision = GateDecision.VALIDATED
    else:
        decision = GateDecision.NO_CHANGE
    manager._record_gate_event(
        seed,
        decision,
        [
            ValidationSignal(
                kind=SignalKind.PROBE,
                direction=probe_direction,
                strength=min(1.0, abs(delta_requested)),
                source_ref=probe_type_enum.value,
                reason=f"probe {outcome_enum.value} ({probe_type_enum.value})",
            )
        ],
        policy_id="probe_feedback",
        status_before=status_before,
        weight_before=weight_before,
        contradiction_before=manager._contradiction_state(seed),
        reason=f"probe {outcome_enum.value}",
    )
    manager._record_and_sync(
        "probe_feedback",
        seed_id,
        probe_type=probe_type_enum.value,
        outcome=outcome_enum.value,
        weight_before=weight_before,
        weight_after=seed.weight,
        delta_requested=delta_requested,
        delta_applied=delta_applied,
        demoted=demoted,
    )
    return result


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
    # Suppress synthesis only when a verified external signal that actually
    # *supports* is already present. Without the direction check a verified but
    # NEUTRAL/OPPOSE signal would cancel the synthesized support while
    # _verified_external() (which requires SUPPORT) still refuses to count it,
    # silently turning external_evidence=True into a no-op.
    if external_evidence and not any(
        signal.is_external_evidence
        and signal.direction is SignalDirection.SUPPORT
        and signal.verified
        for signal in collected
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

    # Fallback for calls that produce no validation_log entry (notably an
    # EXPIRED seed under an explicit public policy). It must carry the same
    # audit meaning as the normal logging route, so the fields are derived from
    # the signals that actually reached the Gate and from the seed's
    # contradiction state — never from the decision alone. An expired seed can
    # still hold an open contradiction record, and GateDecision.EXPIRED would
    # otherwise report contradiction_free=True.
    seed = manager._seeds[seed_id]
    submitted = list(event.signals)
    verified_external = bool(_verified_external(submitted))
    return ValidationGateResult(
        seed_id=seed_id,
        status_before=event.status_before,
        status_after=event.status_after,
        weight_before=event.weight_before,
        weight_after=event.weight_after,
        occurrence_count=seed.occurrence_count,
        evidence_count=seed.evidence_count,
        internal_recognition_passed=_supporting_recurrence(submitted),
        external_evidence_passed=verified_external,
        contradiction_free=not manager._contradiction_state(seed).blocking,
        external_evidence_applied=verified_external,
        contradiction_applied=(
            event.decision is GateDecision.CONTRADICTED
            or _opposing_contradiction(submitted) is not None
        ),
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
