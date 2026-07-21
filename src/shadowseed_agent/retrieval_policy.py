"""Retrieval policy helpers for SSL-backed agents."""

from __future__ import annotations

from typing import Any, Iterable

from shadowseed_agent.agent_contract import AgentSafetyContract, InfluenceAction, SeedLike


def can_seed_trigger_retrieval(
    seed: SeedLike,
    *,
    gate_events: Iterable[Any],
    ledger: list,
    contradiction_blocking: bool,
    contract: AgentSafetyContract | None = None,
    context_ref: str | None = None,
) -> bool:
    """Return whether a seed may trigger retrieval, recording the decision.

    Retrieval is an influence surface, so this goes through the atomic
    point-of-use API (#14): the decision is recorded on ``ledger`` and linked to
    the authorizing Gate event before the boolean is returned. It requires a
    promoted seed, positive weight, a current-version Gate promotion, and no
    blocking contradiction.
    """

    active_contract = contract or AgentSafetyContract()
    record = active_contract.decide_and_record(
        seed,
        InfluenceAction.RETRIEVAL,
        gate_events=gate_events,
        ledger=ledger,
        context_ref=context_ref,
        contradiction_blocking=contradiction_blocking,
    )
    return record.allowed
