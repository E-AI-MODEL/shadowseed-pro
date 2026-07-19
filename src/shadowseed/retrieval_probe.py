"""The SSL→RAG bridge: a Retrieval Probe whose query is the *seed*, not the
question (vision gap 2, `docs/research/vision-generative-seeds.md`).

Ordinary RAG retrieves against the user's question — it can only surface
answers to questions you already know to ask. SSL puts the shadow seed
*upstream* of retrieval: a promoted seed (or a constellation centroid) is the
gap the model noticed about its own answer, and *that* drives the query. So the
probe can pull in context that the question alone would never have retrieved.

The manager already computes a constellation centroid and marks
`probe_type="retrieval"` (4.5 §9.2); this module is the missing consumer that
turns that centroid / those seeds into an actual search against a vector store.

Deterministic and model-free (uses `lexical_embedding`), so it is unit-testable
in CI. It does not generate answers; it returns the retrieved context and,
crucially, what the seed probe finds that the question retrieval does *not* —
the operational handle for the SSL-vs-RAG head-to-head (gap 3).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from shadowseed.text_similarity import lexical_embedding

EmbedFn = Callable[[str], np.ndarray]


def _resolve_embed_fn(embed_fn: EmbedFn | None, dimensions: int) -> EmbedFn:
    if embed_fn is not None:
        return embed_fn
    return lambda text: lexical_embedding(text, dimensions=dimensions)


def centroid_of(
    seed_texts: list[str],
    dimensions: int = 128,
    *,
    embed_fn: EmbedFn | None = None,
) -> np.ndarray:
    """Mean embedding of the seeds — the constellation query (4.5 §9.1)."""
    if not seed_texts:
        raise ValueError("centroid_of needs at least one seed text")
    embed = _resolve_embed_fn(embed_fn, dimensions)
    vectors = [embed(t) for t in seed_texts]
    return np.mean(vectors, axis=0)


def _hit_dict(query: str, hit: tuple[str, float, dict[str, Any]]) -> dict[str, Any]:
    chunk_id, score, metadata = hit
    return {
        "probe_query": query,
        "chunk_id": chunk_id,
        "score": float(score),
        "text": metadata.get("text", ""),
        "doc_id": metadata.get("doc_id"),
    }


def run_seed_retrieval_probe(
    store: Any,
    seed_texts: list[str],
    top_k: int = 5,
    *,
    use_centroid: bool = False,
    embed_fn: EmbedFn | None = None,
    dimensions: int = 128,
) -> list[dict[str, Any]]:
    """Retrieve context driven by the seeds.

    - ``use_centroid=True`` issues one search from the mean seed embedding (the
      constellation case: the cluster as a single conceptual query).
    - otherwise each seed is its own probe query; hits are unioned and
      deduplicated by ``chunk_id`` keeping the strongest score.

    ``embed_fn`` selects the embedder (defaults to the deterministic
    ``lexical_embedding``); pass a real embedder to remove the toy-retriever
    confound. Returns hit dicts with the originating ``probe_query``.
    """
    if not seed_texts:
        return []
    embed = _resolve_embed_fn(embed_fn, dimensions)
    if use_centroid:
        hits = store.search(centroid_of(seed_texts, dimensions, embed_fn=embed), top_k=top_k)
        return [_hit_dict("__centroid__", h) for h in hits]

    best: dict[str, dict[str, Any]] = {}
    for seed in seed_texts:
        for hit in store.search(embed(seed), top_k=top_k):
            d = _hit_dict(seed, hit)
            prev = best.get(d["chunk_id"])
            if prev is None or d["score"] > prev["score"]:
                best[d["chunk_id"]] = d
    return sorted(best.values(), key=lambda d: d["score"], reverse=True)


def retrieval_probe_vs_question(
    store: Any,
    question: str,
    seed_texts: list[str],
    top_k: int = 5,
    *,
    use_centroid: bool = False,
    embed_fn: EmbedFn | None = None,
    dimensions: int = 128,
) -> dict[str, Any]:
    """Contrast plain-RAG (query = question) with the seed probe (query = gap).

    The headline is ``seed_only_chunk_ids``: context the seed probe surfaces that
    the question retrieval does not — the concrete embodiment of "a shadow seed
    finds what RAG, given the same question and corpus, would not". This is the
    measurement handle for the SSL-vs-RAG head-to-head (gap 3); it makes no
    quality claim by itself.

    Both arms use the same ``embed_fn`` so the only variable is the query (the
    question vs the gap), not the embedder.
    """
    embed = _resolve_embed_fn(embed_fn, dimensions)
    question_hits = [
        _hit_dict(question, h) for h in store.search(embed(question), top_k=top_k)
    ]
    probe_hits = run_seed_retrieval_probe(
        store, seed_texts, top_k=top_k, use_centroid=use_centroid, embed_fn=embed
    )
    question_ids = {h["chunk_id"] for h in question_hits}
    probe_ids = {h["chunk_id"] for h in probe_hits}
    return {
        "question": question,
        "seed_texts": seed_texts,
        "top_k": top_k,
        "use_centroid": use_centroid,
        "question_chunk_ids": sorted(question_ids),
        "probe_chunk_ids": sorted(probe_ids),
        "seed_only_chunk_ids": sorted(probe_ids - question_ids),
        "shared_chunk_ids": sorted(probe_ids & question_ids),
        "question_hits": question_hits,
        "probe_hits": probe_hits,
    }
