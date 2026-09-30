"""Effective authorization under the Gate configuration active now.

Historical promotion stays immutable audit history. Product sessions that opt in
to live Gate revalidation can additionally require a promoted seed to satisfy
the current slider-derived thresholds before point-of-use influence.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

from shadowseed.models import SeedStatus


def snapshot_meets_current_gate(
    seed: Mapping[str, Any],
    config: Mapping[str, Any],
    policy_id: str | None,
    *,
    blocking: bool = False,
) -> bool:
    """Return whether a historically promoted snapshot satisfies today's Gate."""

    if str(seed.get("status", "")) != SeedStatus.PROMOTED.value:
        return False
    if blocking:
        return False

    weight = float(seed.get("weight", 0.0))
    promotion_threshold = float(config.get("promotion_threshold", 0.5))
    if weight < promotion_threshold:
        return False

    occurrence_count = int(seed.get("occurrence_count", 0))
    evidence_count = int(seed.get("evidence_count", 0))
    min_occurrences = int(config.get("min_occurrences_for_gate", 3))
    occurrence_ok = occurrence_count >= min_occurrences
    selected_policy = str(policy_id or "exploratory")

    if selected_policy == "exploratory":
        return occurrence_ok or evidence_count >= 1

    if selected_policy == "evidence_backed":
        return (
            occurrence_ok
            and evidence_count >= int(config.get("min_evidence_for_gate", 1))
        )

    if selected_policy == "legacy_evidence_required":
        return (
            occurrence_ok
            and evidence_count >= int(config.get("min_evidence_for_gate", 2))
            and float(seed.get("trace", 0.0))
            > float(config.get("min_trace_for_gate", 0.5))
        )

    return False
