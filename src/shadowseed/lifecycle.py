"""TTL, dormancy, TrTL reactivation, and expiry workflows.

This module owns the executable seed-lifecycle concern that used to live in
:mod:`shadowseed.manager`. ``SSLManager`` keeps its historical public and private
methods as thin compatibility facades, while mechanical authority transitions
remain explicit and separately allowlisted from Gate-controlled decisions.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from shadowseed.models import SeedStatus, ShadowSeed


def status_after_decay(manager: Any, seed: ShadowSeed) -> SeedStatus:
    """Return the historical status transition after trace decay."""

    if seed.trace < manager.dormant_threshold and seed.weight == 0.0:
        return SeedStatus.DORMANT
    if seed.trace < manager.config.min_trace_for_gate and seed.status not in {
        SeedStatus.PROMOTED,
        SeedStatus.DORMANT,
    }:
        return SeedStatus.DECAYING
    return seed.status


def decay_traces(manager: Any, turns_passed: int = 1) -> None:
    """Decay trace and run the dormant TTL clock for every live seed."""

    for seed_id, seed in manager._seeds.items():
        if seed.status == SeedStatus.EXPIRED:
            continue

        before_trace = seed.trace
        seed.trace *= math.exp(-turns_passed / manager.half_life_turns)
        manager._set_authority(seed, status=manager._status_after_decay(seed))

        expired = False
        if seed.status == SeedStatus.DORMANT:
            seed.turns_dormant += turns_passed
            if (
                manager.dormant_ttl_turns > 0
                and seed.turns_dormant >= manager.dormant_ttl_turns
            ):
                manager._set_authority(
                    seed,
                    status=SeedStatus.EXPIRED,
                    weight=0.0,
                )
                expired = True
        else:
            seed.turns_dormant = 0

        manager._touch_seed(seed)
        manager._record_and_sync(
            "trace_decayed",
            seed_id,
            turns_passed=turns_passed,
            trace_before=before_trace,
            trace_after=seed.trace,
            status=seed.status.value,
            turns_dormant=seed.turns_dormant,
        )
        if expired:
            manager._record_event(
                "expired",
                seed_id,
                reason="dormant_ttl",
                turns_dormant=seed.turns_dormant,
            )


def reactivate_by_text(
    manager: Any,
    text: str,
    threshold: float = 0.65,
) -> list[str]:
    """Reactivate matching dormant seeds through semantic or keyword triggers."""

    query_emb = manager.get_embedding(text)
    reactivated: list[str] = []

    for seed_id, seed in manager._seeds.items():
        if seed.status != SeedStatus.DORMANT:
            continue

        similarity = float(np.dot(query_emb, seed.embedding))
        keyword_hit = any(
            keyword.lower() in text.lower() for keyword in seed.trigger_keywords
        )

        if similarity >= threshold or keyword_hit:
            seed.trace = min(
                seed.trace + manager.reactivation_increment,
                manager.max_trace,
            )
            manager._set_authority(seed, status=SeedStatus.NEW)
            seed.turns_dormant = 0
            manager._touch_seed(seed)
            semantic_hit = similarity >= threshold
            if semantic_hit and keyword_hit:
                basis = "semantic+keyword"
            elif semantic_hit:
                basis = "semantic"
            else:
                basis = "keyword"
            manager._record_and_sync(
                "reactivated",
                seed_id,
                similarity=similarity,
                keyword_hit=keyword_hit,
                basis=basis,
                trace=seed.trace,
            )
            reactivated.append(seed_id)

    return reactivated


def scan_trtl_triggers(
    manager: Any,
    text: str,
    threshold: float = 0.65,
) -> list[str]:
    """Canonical TrTL alias that preserves the manager override point."""

    return manager.reactivate_by_text(text, threshold=threshold)


def expire_vector_only_open_seeds(
    manager: Any,
    max_age_days: int = 30,
) -> list[str]:
    """Apply terminal expiry returned by vector-store housekeeping."""

    if manager.vector_constellation is None:
        return []
    expired = manager.vector_constellation.housekeeping(max_age_days=max_age_days)
    for seed_id in expired:
        if seed_id in manager._seeds:
            seed = manager._seeds[seed_id]
            manager._set_authority(
                seed,
                status=SeedStatus.EXPIRED,
                weight=0.0,
            )
            manager._touch_seed(seed)
            manager._record_event("expired", seed_id, max_age_days=max_age_days)
    return expired


__all__ = [
    "decay_traces",
    "expire_vector_only_open_seeds",
    "reactivate_by_text",
    "scan_trtl_triggers",
    "status_after_decay",
]
