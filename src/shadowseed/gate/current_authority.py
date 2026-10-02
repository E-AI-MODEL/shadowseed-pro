"""Effective authorization under the Gate configuration active now.

Historical promotion stays immutable audit history. Product sessions that opt in
to current-Gate revalidation additionally require a promoted seed to remain
eligible under the semantics of the Gate policy active now.

The current check is read-only. It never replays or reapplies authority. Instead,
it evaluates the canonical policy against authority-supporting signals that were
actually recorded in immutable Gate events after the latest contradiction.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Any, Mapping

from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.gate.policies import AuthoritySnapshot, ProposedVerdict, resolve_policy
from shadowseed.gate.signals import ValidationSignal
from shadowseed.models import SeedStatus


_AUTHORITY_CONFIRMING_DECISIONS = frozenset(
    {GateDecision.VALIDATED, GateDecision.PROMOTED}
)


def _coerce_gate_event(value: GateEvent | Mapping[str, Any]) -> GateEvent:
    if isinstance(value, GateEvent):
        return value
    return GateEvent.from_dict(dict(value))


def _current_support_signals(
    seed_id: str,
    gate_events: Iterable[GateEvent | Mapping[str, Any]],
) -> tuple[ValidationSignal, ...]:
    """Return audited support offered after the seed's latest contradiction."""

    events = [
        _coerce_gate_event(item)
        for item in gate_events
        if str(
            item.seed_id
            if isinstance(item, GateEvent)
            else item.get("seed_id", "")
        )
        == str(seed_id)
    ]
    latest_contradiction = max(
        (
            index
            for index, event in enumerate(events)
            if event.decision is GateDecision.CONTRADICTED
        ),
        default=-1,
    )

    signals: list[ValidationSignal] = []
    for index, event in enumerate(events):
        if index <= latest_contradiction:
            continue
        if event.decision not in _AUTHORITY_CONFIRMING_DECISIONS:
            continue
        signals.extend(event.signals)
    return tuple(signals)


def _policy_for_current_config(
    policy_id: str | None,
    config: Mapping[str, Any],
):
    selected = str(policy_id or "exploratory")
    policy = resolve_policy(selected)
    if selected == "legacy_evidence_required":
        return replace(
            policy,
            weight_increment=float(config.get("validation_increment", 0.2)),
            min_occurrences=int(config.get("min_occurrences_for_gate", 3)),
            min_evidence=int(config.get("min_evidence_for_gate", 2)),
            min_trace=float(config.get("min_trace_for_gate", 0.5)),
        )
    return policy


def snapshot_meets_current_gate(
    seed: Mapping[str, Any],
    config: Mapping[str, Any],
    policy_id: str | None,
    *,
    blocking: bool = False,
    gate_events: Iterable[GateEvent | Mapping[str, Any]] = (),
) -> bool:
    """Return whether a promoted snapshot remains eligible under today's policy."""

    if str(seed.get("status", "")) != SeedStatus.PROMOTED.value:
        return False
    if blocking:
        return False

    weight = float(seed.get("weight", 0.0))
    promotion_threshold = float(config.get("promotion_threshold", 0.5))
    if weight < promotion_threshold:
        return False

    try:
        policy = _policy_for_current_config(policy_id, config)
    except ValueError:
        return False

    snapshot = AuthoritySnapshot(
        weight=weight,
        status=SeedStatus.PROMOTED.value,
        has_blocking_contradiction=blocking,
        evidence_count=int(seed.get("evidence_count", 0)),
        occurrence_count=int(seed.get("occurrence_count", 0)),
        trace=float(seed.get("trace", 0.0)),
    )
    signals = _current_support_signals(str(seed.get("id", "")), gate_events)
    proposal = policy.propose(signals, snapshot)
    return bool(
        proposal.satisfied
        and proposal.verdict is ProposedVerdict.PROMOTE_OR_VALIDATE
    )


__all__ = ["snapshot_meets_current_gate"]
