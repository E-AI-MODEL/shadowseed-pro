"""Cluster-based semantic recurrence without collapsing seed identity.

Semantic clustering exists because a detector may express the same underlying
epistemic candidate in different words across turns. Storage identity stays
strict while a cluster representative can accumulate recurrence.

A crucial distinction is now explicit: **cluster membership is not recurrence**.
Several paraphrases emitted by one detector call may all improve a cluster's
centroid and remain separate stored seeds, but that single observation context
may contribute at most one recurrence credit. A later independent observation
may contribute another credit.

Legacy callers that omit ``observation_ref`` retain the historical member-count
behavior. Canonical runtime callers provide an observation reference, so new
product/research execution uses observation-scoped recurrence without silently
rewriting historical artifacts or direct low-level compatibility tests.
"""

from __future__ import annotations

import numpy as np

DEFAULT_CLUSTER_THRESHOLD = 0.6


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


class RecurrenceClusterer:
    """Track semantic cluster membership separately from recurrence credit.

    ``add(text, embedding, observation_ref=...)`` assigns a new stored candidate
    to the nearest semantic cluster (or creates one) and updates the centroid.
    With an observation reference, the cluster's recurrence count increases only
    when that reference has not already contributed to the cluster.

    ``bump(cluster_id, observation_ref=...)`` is used for re-detection of an
    already stored member. It follows the same idempotent observation rule while
    leaving centroid membership unchanged.

    When ``observation_ref`` is omitted, historical member-count semantics are
    preserved for compatibility with legacy low-level callers and artifacts.
    """

    def __init__(self, threshold: float = DEFAULT_CLUSTER_THRESHOLD) -> None:
        self.threshold = threshold
        self.centroids: list[np.ndarray] = []
        self.centroid_counts: list[int] = []
        self.recurrence_counts: list[int] = []
        # Backward-compatible alias for code that inspected counts directly.
        self.counts = self.recurrence_counts
        self.members: list[list[str]] = []
        self.seen_observation_refs: list[set[str]] = []

    @staticmethod
    def _normalize_observation_ref(observation_ref: str | None) -> str | None:
        if observation_ref is None:
            return None
        normalized = str(observation_ref).strip()
        if not normalized:
            raise ValueError("observation_ref must not be empty when supplied")
        return normalized

    def _credit_observation(self, cluster_id: int, observation_ref: str | None) -> bool:
        """Return whether this call added recurrence credit to ``cluster_id``."""

        normalized = self._normalize_observation_ref(observation_ref)
        if normalized is None:
            self.recurrence_counts[cluster_id] += 1
            return True
        seen = self.seen_observation_refs[cluster_id]
        if normalized in seen:
            return False
        seen.add(normalized)
        self.recurrence_counts[cluster_id] += 1
        return True

    def add(
        self,
        text: str,
        embedding: np.ndarray,
        *,
        observation_ref: str | None = None,
    ) -> int:
        emb = np.asarray(embedding, dtype=float)
        normalized_ref = self._normalize_observation_ref(observation_ref)
        best = -1
        best_sim = self.threshold
        for i, centroid in enumerate(self.centroids):
            similarity = _cosine(emb, centroid)
            if similarity >= best_sim:
                best_sim = similarity
                best = i
        if best < 0:
            self.centroids.append(emb.copy())
            self.centroid_counts.append(1)
            self.recurrence_counts.append(0 if normalized_ref is not None else 1)
            self.members.append([text])
            self.seen_observation_refs.append(set())
            cluster_id = len(self.centroids) - 1
            if normalized_ref is not None:
                self._credit_observation(cluster_id, normalized_ref)
            return cluster_id

        n = self.centroid_counts[best]
        self.centroids[best] = (self.centroids[best] * n + emb) / (n + 1)
        self.centroid_counts[best] += 1
        self.members[best].append(text)
        self._credit_observation(best, normalized_ref)
        return best

    def bump(self, cluster_id: int, *, observation_ref: str | None = None) -> int:
        """Credit a re-detected stored member without changing cluster membership."""

        self._credit_observation(cluster_id, observation_ref)
        return self.recurrence_counts[cluster_id]

    def recurrence(self, cluster_id: int) -> int:
        return self.recurrence_counts[cluster_id]


def auto_calibrated_min_occurrences(n_turns: int, lo: int = 2, hi: int = 4) -> int:
    """Per-topic heuristic: scale the recurrence bar to conversation length."""

    return max(lo, min(hi, n_turns // 3))
