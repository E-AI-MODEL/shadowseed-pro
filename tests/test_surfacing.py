"""Unit tests for the shared use-time surfacing policy."""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.surfacing import (
    SurfacingPolicy,
    collect_eligible_promoted_seeds,
    mark_surfaced,
    seed_threshold,
    select_cross_turn_seeds,
    turn_threshold,
)


def _embedding(text: str) -> np.ndarray:
    if "seed" in text.lower():
        return np.array([1.0, 0.0])
    return np.array([0.35, np.sqrt(1.0 - 0.35**2)])


def _promoted_manager() -> tuple[SSLManager, str]:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("seed perspective")
    seed = manager.seeds[seed_id]
    seed.unsafe_set_authority(status=SeedStatus.PROMOTED, weight=1.0)
    return manager, seed_id


def test_policy_rejects_invalid_margins() -> None:
    with pytest.raises(ValueError):
        SurfacingPolicy(early_turn_margin=-0.01)
    with pytest.raises(ValueError):
        SurfacingPolicy(early_turn_history=-1)
    with pytest.raises(ValueError):
        SurfacingPolicy(resurface_margin=-0.01)


def test_early_turn_and_resurface_thresholds_share_one_implementation() -> None:
    policy = SurfacingPolicy(
        surface_threshold=0.30,
        early_turn_margin=0.10,
        early_turn_history=5,
        resurface_margin=0.08,
    )
    assert turn_threshold(4, policy) == pytest.approx(0.40)
    assert turn_threshold(5, policy) == pytest.approx(0.30)
    assert seed_threshold(6, "s1", policy, {"s1": 5}) == pytest.approx(0.38)
    assert seed_threshold(7, "s1", policy, {"s1": 5}) == pytest.approx(0.34)


def test_collection_requires_promotion_previous_birth_and_current_fit() -> None:
    manager, seed_id = _promoted_manager()
    policy = SurfacingPolicy(early_turn_margin=0.0, early_turn_history=0, resurface_margin=0.0)
    assert collect_eligible_promoted_seeds(
        manager,
        "question",
        turn=0,
        born_turn={seed_id: 0},
        last_surfaced={},
        policy=policy,
    ) == []
    eligible = collect_eligible_promoted_seeds(
        manager,
        "question",
        turn=1,
        born_turn={seed_id: 0},
        last_surfaced={},
        policy=policy,
    )
    assert eligible and eligible[0][1] == seed_id


def test_mark_surfaced_records_only_actual_influence_candidates() -> None:
    selected = [(0.9, "allowed", "A"), (0.8, "blocked", "B")]
    allowed = [selected[0]]
    last: dict[str, int] = {}
    mark_surfaced(last, allowed, 4)
    assert last == {"allowed": 4}
    assert select_cross_turn_seeds(selected, 1) == [selected[0]]
