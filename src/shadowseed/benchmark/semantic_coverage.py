"""Semantic gap-coverage metric.

Round 012 showed the lexical ``coverage()`` (jaccard >= 0.70 against the gap's
noun-phrase) only fires when an answer repeats the gap text *verbatim*. It
therefore rewards parroting and scores 0.0 when a model integrates the same gap
in its own words — exactly the well-written case we want to credit.

This metric instead asks, per expected gap: *does any sentence of the answer
mean roughly the same thing?* — max cosine similarity between the gap's embedding
and the answer's sentence embeddings, thresholded. With the deterministic
``lexical_embedding`` it stays a hash (still verbatim-ish, CI-safe); with a real
embedder (``openai``) it becomes genuinely semantic. Raw ``max_sim`` is always
reported so the threshold is transparent and re-judgeable, not hidden.

It is a corroborator, not an oracle: the blind answer-pair reader remains the
primary payoff measure.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from shadowseed.benchmark.ssl45_model_benefit_suite import answer_fragments

EmbedFn = Callable[[str], np.ndarray]

DEFAULT_SEMANTIC_THRESHOLD = 0.55


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def semantic_coverage(
    answer: str,
    expected_additions: list[str],
    embed_fn: EmbedFn,
    threshold: float = DEFAULT_SEMANTIC_THRESHOLD,
) -> tuple[float, list[str], list[dict[str, Any]]]:
    """Fraction of expected gaps semantically present in ``answer``.

    Returns ``(fraction, covered_texts, per_gap)`` where ``per_gap`` carries the
    raw ``max_sim`` per gap so the thresholded ``covered`` flag is auditable.
    An empty ``expected_additions`` is full coverage by definition (1.0).
    """
    if not expected_additions:
        return 1.0, [], []
    fragments = answer_fragments(answer)
    frag_vecs = [embed_fn(f) for f in fragments] if fragments else []
    covered: list[str] = []
    per_gap: list[dict[str, Any]] = []
    for expected in expected_additions:
        gap_vec = embed_fn(expected)
        best = max((_cosine(gap_vec, fv) for fv in frag_vecs), default=0.0)
        is_covered = best >= threshold
        per_gap.append({"gap": expected, "max_sim": round(best, 4), "covered": is_covered})
        if is_covered:
            covered.append(expected)
    return len(covered) / len(expected_additions), covered, per_gap
