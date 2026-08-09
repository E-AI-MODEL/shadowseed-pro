"""Vector search, external feedback, and constellation workflows.

This module owns the non-authority vector orchestration that used to live in
:mod:`shadowseed.manager`: uncertain-region search, external-feedback routing,
and in-memory constellation construction. Probe-feedback authority decisions
remain in :mod:`shadowseed.gate.runtime_adapter`.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
)
from shadowseed.models import Constellation, SeedStatus, ShadowSeed


def find_uncertain_region(
    manager: Any,
    text: str,
    threshold: float = 0.85,
    include_promoted: bool = False,
) -> list[dict[str, Any]]:
    """Return vector-near weightless seeds from the configured vector store."""

    if manager.vector_constellation is None:
        return []
    query_emb = manager.get_embedding(text)
    matches = manager.vector_constellation.search_similar_seeds(
        query_emb,
        threshold=threshold,
    )
    uncertain: list[dict[str, Any]] = []
    for seed_id, score, metadata in matches:
        seed = manager._seeds.get(seed_id)
        if seed is None:
            continue
        if not include_promoted and seed.status == SeedStatus.PROMOTED:
            continue
        if seed.weight == 0.0:
            uncertain.append(
                {
                    "seed_id": seed_id,
                    "similarity": score,
                    "text": seed.text,
                    "status": seed.status.value,
                    "weight": seed.weight,
                    "metadata": metadata,
                }
            )
    return uncertain


def apply_external_feedback(
    manager: Any,
    feedback_text: str,
    context: str,
    positive: bool = True,
    threshold: float = 0.75,
    source_ref: str | None = None,
) -> list[dict[str, Any]]:
    """Route vector-matched external feedback through the manager Gate facade.

    ``source_ref`` identifies the reviewer or evidence item for Gate
    idempotency. The historical context value remains the fallback so existing
    callers preserve their provenance semantics.
    """

    if manager.vector_constellation is None:
        return []
    feedback_emb = manager.get_embedding(f"FEEDBACK: {feedback_text} ON: {context}")
    matches = manager.vector_constellation.search_similar_seeds(
        feedback_emb,
        threshold=threshold,
    )
    updates: list[dict[str, Any]] = []
    for seed_id, score, _metadata in matches:
        if seed_id not in manager._seeds:
            continue
        if positive:
            result = manager.run_validation_gate(
                seed_id,
                external_evidence=True,
                signals=[
                    ValidationSignal(
                        kind=SignalKind.HUMAN_FEEDBACK,
                        direction=SignalDirection.SUPPORT,
                        strength=float(score),
                        source_ref=source_ref or context,
                        verified=True,
                        reason="external feedback (positive)",
                    )
                ],
            )
        else:
            result = manager.run_validation_gate(
                seed_id,
                contradiction=True,
                signals=[
                    ValidationSignal(
                        kind=SignalKind.CONTRADICTION,
                        direction=SignalDirection.OPPOSE,
                        strength=float(score),
                        source_ref=source_ref or context,
                        reason="external feedback (negative)",
                    )
                ],
            )
        manager.vector_constellation.record_feedback(
            seed_id=seed_id,
            feedback=feedback_text,
            is_correction=positive,
            similarity=score,
        )
        updates.append(
            {
                "seed_id": seed_id,
                "similarity": score,
                "gate_result": result,
                "seed": manager._seeds[seed_id].to_dict(),
            }
        )
    return updates


def constellation_label(cluster: list[ShadowSeed]) -> str:
    """Build the historical human-readable label for one cluster."""

    for seed in cluster:
        for keyword in seed.trigger_keywords:
            clean = keyword.strip()
            if clean:
                return f"Cluster around {clean}."
    seed_text = cluster[0].text.strip().rstrip(".")
    return f"Cluster around {seed_text[:48]}."


def find_constellations(
    manager: Any,
    threshold: float = 0.70,
    min_members: int = 3,
) -> list[Constellation]:
    """Build deterministic in-memory constellations from promoted seeds."""

    promoted = [
        seed
        for seed in manager._seeds.values()
        if seed.status == SeedStatus.PROMOTED
    ]
    constellations: list[Constellation] = []
    seen: set[tuple[str, ...]] = set()

    for index, seed in enumerate(promoted):
        cluster = [seed]
        for other in promoted[index + 1 :]:
            similarity = float(np.dot(seed.embedding, other.embedding))
            if similarity >= threshold:
                cluster.append(other)

        if len(cluster) >= min_members:
            member_ids = tuple(sorted(item.id for item in cluster))
            if member_ids in seen:
                continue
            seen.add(member_ids)
            centroid = np.mean([item.embedding for item in cluster], axis=0)
            constellations.append(
                Constellation(
                    members=list(member_ids),
                    centroid=centroid.tolist(),
                    combined_weight=float(
                        np.mean([item.weight for item in cluster])
                    ),
                    id=f"const_{len(constellations) + 1:03d}",
                    label=manager._constellation_label(cluster),
                    probe_type="retrieval" if len(cluster) >= 5 else "socratic",
                )
            )

    return constellations


__all__ = [
    "apply_external_feedback",
    "constellation_label",
    "find_constellations",
    "find_uncertain_region",
]
