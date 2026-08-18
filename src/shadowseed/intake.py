"""Candidate intake, embedding, normalization, and deduplication workflows.

This module owns the executable intake concern that used to live in
:mod:`shadowseed.manager`: embedding acquisition, atomicity heuristics,
detection-candidate normalization, embedding-backed deduplication, and seed
creation/update orchestration. ``SSLManager`` retains its historical methods as
thin compatibility facades.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

import numpy as np

from shadowseed.core_config import SSLCoreConfig
from shadowseed.models import SeedOrigin, SeedStatus, ShadowSeed
from shadowseed.seed_normalization import (
    normalize_detection_candidates as normalize_candidates,
)


_DEFAULT_MAX_SEED_WORDS = SSLCoreConfig().max_seed_words


def load_embedder(manager: Any):
    """Lazily load and cache the configured sentence-transformer backend."""

    if manager._embedder is not None:
        return manager._embedder
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise ImportError(
            "Install sentence-transformers to use SSLManager: "
            "pip install sentence-transformers"
        ) from exc
    manager._embedder = SentenceTransformer(manager.model_name)
    return manager._embedder


def get_embedding(manager: Any, text: str) -> np.ndarray:
    """Return one normalized embedding through the configured backend."""

    if manager._embedding_fn is not None:
        return manager._normalize_embedding(manager._embedding_fn(text))
    embedder = manager._load_embedder()
    return embedder.encode(text, normalize_embeddings=True)


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """L2-normalize an embedding while preserving the historical zero case."""

    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm


def is_atomic_seed(text: str, max_seed_words: int | None = None) -> bool:
    """Heuristic filter for whether a candidate is a single atomic seed.

    Human review is still needed. The separator/broad-term/category token lists
    include Dutch aliases retained for the historical research corpus. They are
    matched as substrings and never surfaced to the user; removing or translating
    them would silently weaken detection on existing material.
    """

    lowered = text.lower().strip()
    if not lowered:
        return False
    separators = [",", ";", " en ", " of ", "zoals", "bijvoorbeeld"]
    broad_terms = [
        "analysekader",
        "complete",
        "oorzaken",
        "gevolgen",
        "contexten",
        "perspectieven",
        "meerdere",
    ]
    generic_category_terms = {
        "security",
        "privacy",
        "schaalbaarheid",
        "kolonialisme",
        "context",
    }
    word_limit = _DEFAULT_MAX_SEED_WORDS if max_seed_words is None else max_seed_words
    has_many_separators = sum(separator in lowered for separator in separators) >= 2
    has_broad_terms = any(term in lowered for term in broad_terms)
    word_count = len(re.findall(r"\w+", text))
    if (
        word_count <= 3
        and any(term in lowered for term in generic_category_terms)
        and ("ontbreekt" in lowered or "ontbreken" in lowered)
    ):
        return False
    return not has_many_separators and not has_broad_terms and word_count <= word_limit


def normalize_detection_candidates(
    candidates: Iterable[str],
    expand_short_fragments: bool = True,
    split_broad: bool = True,
) -> list[str]:
    """Normalize raw detector output into candidate seed strings."""

    return normalize_candidates(
        list(candidates),
        expand_short_fragments=expand_short_fragments,
        split_broad=split_broad,
    )


def ingest_detection_candidates(
    manager: Any,
    candidates: Iterable[str],
    trigger_keywords: Iterable[str] | None = None,
    expand_short_fragments: bool = True,
    split_broad: bool = True,
    deduplicate: bool = True,
    min_seed_words: int = 0,
    origin: SeedOrigin | None = None,
) -> dict[str, Any]:
    """Normalize, validate, deduplicate, and install detector candidates."""

    raw_candidates = list(candidates)
    normalized = manager.normalize_detection_candidates(
        raw_candidates,
        expand_short_fragments=expand_short_fragments,
        split_broad=split_broad,
    )
    accepted: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    seen_texts: set[str] = set()
    accepted_ids: set[str] = set()
    for candidate in normalized:
        if min_seed_words and len(re.findall(r"\w+", candidate)) < min_seed_words:
            rejected.append({"text": candidate, "reason": "too_vague"})
            continue
        key = candidate.strip().lower()
        if key in seen_texts:
            rejected.append({"text": candidate, "reason": "duplicate"})
            continue
        try:
            seed_id = manager.add_or_update_seed(
                candidate,
                trigger_keywords=trigger_keywords,
                deduplicate=deduplicate,
                origin=origin,
            )
        except ValueError:
            rejected.append({"text": candidate, "reason": "not_atomic"})
            continue
        if seed_id in accepted_ids:
            rejected.append({"text": candidate, "reason": "duplicate"})
            continue
        accepted.append({"seed_id": seed_id, "text": candidate})
        accepted_ids.add(seed_id)
        seen_texts.add(key)
    return {
        "input_count": len(raw_candidates),
        "normalized_candidates": normalized,
        "accepted": accepted,
        "rejected": rejected,
    }


def maybe_deduplicate_seed(
    manager: Any, new_embedding: np.ndarray
) -> tuple[str, float] | None:
    """Return the most similar non-expired seed above the dedup threshold."""

    best_match: tuple[str, float] | None = None
    for seed_id, seed in manager._seeds.items():
        if seed.status == SeedStatus.EXPIRED:
            continue
        similarity = float(np.dot(new_embedding, seed.embedding))
        if best_match is None or similarity > best_match[1]:
            best_match = seed_id, similarity
    if best_match is not None and best_match[1] >= manager.dedup_threshold:
        return best_match
    return None


def activate_existing_seed(manager: Any, seed_id: str, similarity: float) -> str:
    """Apply the historical mechanical re-detection transition."""

    seed = manager._seeds[seed_id]
    seed.occurrence_count += 1
    seed.trace = min(seed.trace + 0.5, manager.max_trace)
    seed.turns_dormant = 0
    if seed.status != SeedStatus.PROMOTED:
        manager._set_authority(seed, status=SeedStatus.ACTIVE)
    manager._touch_seed(seed)
    manager._record_and_sync(
        "deduplicated",
        seed_id,
        similarity=similarity,
        occurrence_count=seed.occurrence_count,
        trace=seed.trace,
    )
    return seed_id


def create_seed(
    manager: Any,
    text: str,
    embedding: np.ndarray,
    trigger_keywords: Iterable[str] | None,
    origin: SeedOrigin | None = None,
) -> str:
    """Create one weightless seed and record the creation event."""

    numeric_ids: list[int] = []
    for existing_id in manager._seeds:
        match = re.fullmatch(r"ss_(\d+)", existing_id)
        if match is not None:
            numeric_ids.append(int(match.group(1)))
    seed_id = f"ss_{max(numeric_ids, default=0) + 1:03d}"
    manager._seeds[seed_id] = ShadowSeed(
        id=seed_id,
        text=text,
        embedding=embedding,
        trigger_keywords=list(trigger_keywords or []),
        trace=manager.config.trace_start,
        origin=origin,
    )
    manager._record_and_sync(
        "created",
        seed_id,
        text=text,
        origin=origin.to_dict() if origin is not None else None,
    )
    return seed_id


def add_or_update_seed(
    manager: Any,
    text: str,
    trigger_keywords: Iterable[str] | None = None,
    deduplicate: bool = True,
    origin: SeedOrigin | None = None,
) -> str:
    """Validate and either create or mechanically reinforce one seed."""

    if not manager.is_atomic_seed(
        text, max_seed_words=manager.config.max_seed_words
    ):
        raise ValueError("Seed appears too broad. Split it into atomic seeds first.")

    new_embedding = manager.get_embedding(text)
    if deduplicate:
        deduplicated = manager._maybe_deduplicate_seed(new_embedding)
        if deduplicated is not None:
            seed_id, similarity = deduplicated
            return manager._activate_existing_seed(seed_id, similarity)

    return manager._create_seed(
        text,
        new_embedding,
        trigger_keywords,
        origin=origin,
    )


__all__ = [
    "add_or_update_seed",
    "create_seed",
    "get_embedding",
    "ingest_detection_candidates",
    "is_atomic_seed",
    "normalize_detection_candidates",
    "normalize_embedding",
]
