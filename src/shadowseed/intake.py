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

from shadowseed.models import SeedOrigin, SeedStatus, ShadowSeed
from shadowseed.seed_normalization import (
    BROAD_PREFIXES,
    normalize_detection_candidates as normalize_candidates,
    normalize_detection_candidates_with_sources,
)




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


_ENGLISH_MARKERS = frozenset(
    {"the", "a", "an", "is", "are", "were", "to", "for", "with", "in", "on", "at", "by",
     "from", "into", "about", "between", "than", "and", "not", "as", "its", "their", "how",
     "whether", "what", "which", "who", "why", "when", "if", "does", "do", "has", "have",
     "been", "can", "could", "should", "would", "be", "this", "that"}
)


def _looks_english(lowered: str) -> bool:
    words = re.findall(r"[a-z]+", lowered)
    return sum(word in _ENGLISH_MARKERS for word in words) >= 2


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
    # Structural rejection must not depend on the language of the model.
    # One long copied instruction paragraph is not an atomic candidate.
    if re.search(r"[.!?]\s+[A-Z]", text):
        return False
    if any(lowered.startswith(prefix) for prefix in BROAD_PREFIXES):
        return False
    from shadowseed.atomicity import is_single_question

    question_verdict = is_single_question(text)
    if question_verdict is not None:
        return question_verdict
    # English declarative candidates are admitted unless they are a bare
    # category stack ("Security, privacy and scalability are missing."). In a
    # blind review of 60 fixed22 candidates, 22 of the 24 that the broader
    # separator guard rejected were useful gaps: a relation with examples in
    # it is one direction, not a list. The broader guard stays for the
    # historical Dutch corpus only.
    if _looks_english(lowered):
        list_marks = lowered.count(",") + lowered.count(";") + len(re.findall(r"\b(?:and|or)\b", lowered))
        return not (list_marks >= 2 and len(re.findall(r"\w+", text)) <= 8)
    separators = [",", ";", " and ", " or ", " en ", " of ", "zoals", "bijvoorbeeld"]
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
    # max_seed_words is retained for compatibility; structural atomicity is
    # a single investigable direction, not a pre-birth judgement of value.
    del max_seed_words
    has_many_separators = sum(separator in lowered for separator in separators) >= 2
    # Questions returned above. Retain the historical lexical guard for
    # declarative omission lists only; it must not pre-judge a question.
    has_broad_terms = any(term in lowered for term in broad_terms)
    word_count = len(re.findall(r"\w+", text))
    if (
        word_count <= 3
        and any(term in lowered for term in generic_category_terms)
        and ("ontbreekt" in lowered or "ontbreken" in lowered)
    ):
        return False
    return not has_many_separators and not has_broad_terms


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


def _canonical_source_indices(
    manager: Any,
    raw_candidates: list[str],
    normalized: list[str],
    *,
    expand_short_fragments: bool,
    split_broad: bool,
) -> tuple[list[int | None], str]:
    """Do not claim item lineage for a caller's replaced normalization hook.

    The manager's historical overridable normalization method remains the
    actual source of normalized items. Only the unmodified canonical facade
    can be attributed to the shared normalizer. No fallback matching by
    text/similarity is allowed: identical strings can occur at many indices.
    """
    from shadowseed.manager import SSLManager

    if (
        getattr(manager.normalize_detection_candidates, "__func__", None)
        is not SSLManager.normalize_detection_candidates
    ):
        return [None] * len(normalized), "unresolved_normalizer_override"

    pairs = normalize_detection_candidates_with_sources(
        raw_candidates,
        expand_short_fragments=expand_short_fragments,
        split_broad=split_broad,
    )
    if [text for _raw_index, text in pairs] != normalized:
        return [None] * len(normalized), "unresolved_normalizer_mismatch"
    return [index for index, _text in pairs], "canonical"


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
    """Normalize and ingest once, with an observational per-item path.

    Existing acceptance, rejection, recurrence and Gate behavior is unchanged.
    The additional lineage does not count as evidence or as an independent
    model observation. Unknown custom normalization remains explicitly unknown.
    """
    raw_candidates = list(candidates)
    normalized = manager.normalize_detection_candidates(
        raw_candidates,
        expand_short_fragments=expand_short_fragments,
        split_broad=split_broad,
    )
    source_indices, mapping_status = _canonical_source_indices(
        manager, raw_candidates, normalized,
        expand_short_fragments=expand_short_fragments,
        split_broad=split_broad,
    )
    accepted: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    lineage: list[dict[str, Any]] = []
    seen_texts: set[str] = set()
    accepted_ids: set[str] = set()

    for normalized_index, candidate in enumerate(normalized):
        row: dict[str, Any] = {
            "normalized_index": normalized_index,
            "raw_candidate_index": source_indices[normalized_index],
            "source_mapping_status": mapping_status,
            "normalized_text": candidate,
            "outcome": "rejected",
            "reason": None,
            "seed_id": None,
            "seed_transition": None,
        }
        lineage.append(row)

        if min_seed_words and len(re.findall(r"\w+", candidate)) < min_seed_words:
            rejected.append({"text": candidate, "reason": "too_vague"})
            row["reason"] = "too_vague"
            continue
        key = candidate.strip().lower()
        if key in seen_texts:
            rejected.append({"text": candidate, "reason": "duplicate"})
            row["reason"] = "duplicate"
            continue

        event_start = len(manager.event_log)
        try:
            seed_id = manager.add_or_update_seed(
                candidate,
                trigger_keywords=trigger_keywords,
                deduplicate=deduplicate,
                origin=origin,
                suppress_reinforcement_for=accepted_ids,
            )
        except ValueError:
            rejected.append({"text": candidate, "reason": "not_atomic"})
            row["reason"] = "not_atomic"
            continue
        if seed_id in accepted_ids:
            rejected.append({"text": candidate, "reason": "duplicate"})
            row["reason"] = "duplicate"
            continue

        accepted.append({"seed_id": seed_id, "text": candidate})
        accepted_ids.add(seed_id)
        seen_texts.add(key)
        row["outcome"] = "accepted"
        row["seed_id"] = seed_id
        transitions = [
            event.event_type
            for event in manager.event_log[event_start:]
            if event.seed_id == seed_id
        ]
        # The recorded transition is a historical fact, not an inference
        # about the semantic relation between source text and the seed.
        row["seed_transition"] = (
            "created" if "created" in transitions else
            "deduplicated" if "deduplicated" in transitions else
            "unresolved_custom_adapter"
        )

    if mapping_status == "canonical":
        represented = {index for index in source_indices if index is not None}
        for raw_index in range(len(raw_candidates)):
            if raw_index in represented:
                continue
            lineage.append({
                "normalized_index": None,
                "raw_candidate_index": raw_index,
                "source_mapping_status": mapping_status,
                "normalized_text": None,
                "outcome": "dropped",
                "reason": "normalizer_dropped",
                "seed_id": None,
                "seed_transition": None,
            })

    return {
        "input_count": len(raw_candidates),
        "normalized_candidates": normalized,
        "accepted": accepted,
        "rejected": rejected,
        "lineage_status": mapping_status,
        "lineage": lineage,
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
    suppress_reinforcement_for: set[str] | None = None,
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
            if (
                suppress_reinforcement_for is not None
                and seed_id in suppress_reinforcement_for
            ):
                return seed_id
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
