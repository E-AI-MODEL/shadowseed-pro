"""Shared recurrence helpers used by chat and benchmark pipelines."""

from __future__ import annotations

from typing import Any

from shadowseed.manager import SSLManager, SeedStatus


def refresh_cluster_representative(
    manager: SSLManager,
    representative_seed: Any,
    source_seed: Any,
) -> None:
    """Keep a cluster representative gate-eligible when a member recurs."""

    if representative_seed.status == SeedStatus.EXPIRED:
        return
    representative_seed.trace = min(
        manager.max_trace,
        max(
            representative_seed.trace,
            source_seed.trace,
            manager.config.min_trace_for_gate + 1e-9,
        ),
    )
    representative_seed.turns_dormant = 0
    if representative_seed.status != SeedStatus.PROMOTED:
        manager._set_authority(representative_seed, status=SeedStatus.ACTIVE)
    manager._touch_seed(representative_seed)
