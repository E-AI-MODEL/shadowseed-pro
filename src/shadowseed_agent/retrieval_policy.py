"""Retrieval policy helpers for SSL-backed agents."""

from __future__ import annotations

from typing import Any, Iterable

from shadowseed_agent.agent_contract import AgentSafetyContract, InfluenceAction, SeedLike


def can_seed_trigger_retrieval(
    seed: SeedLike,
    gate_log: Iterable[Any] = (),
    contract: AgentSafetyContract | None = None,
) -> bool:
    """Return whether a seed may trigger retrieval.

    Retrieval is an influence surface. By default it requires a promoted seed,
    positive weight, and a logged Validation Gate promotion.
    """

    active_contract = contract or AgentSafetyContract()
    return active_contract.can_influence(seed, InfluenceAction.RETRIEVAL, gate_log)
