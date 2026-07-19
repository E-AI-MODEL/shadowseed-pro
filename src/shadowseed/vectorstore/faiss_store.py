"""Optional FAISS vectorstore adapter.

Install with:

    pip install -e ".[vector-faiss]"

The adapter keeps metadata in Python dictionaries and uses FAISS only for vector
similarity search. It implements the same VectorStore interface as the in-memory
store.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from shadowseed.vectorstore.base import SearchResult, VectorStore


class FaissVectorStore(VectorStore):
    def __init__(self, dimensions: int) -> None:
        try:
            import faiss  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "FAISS is optional. Install it with: pip install -e '.[vector-faiss]'"
            ) from exc

        self._faiss = faiss
        self.dimensions = dimensions
        self.index = faiss.IndexFlatIP(dimensions)
        self._ids: list[str] = []
        self._metadata: dict[str, dict[str, Any]] = {}
        self._embeddings: dict[str, np.ndarray] = {}

    @staticmethod
    def _normalize(embedding: np.ndarray) -> np.ndarray:
        vector = np.asarray(embedding, dtype="float32")
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def _rebuild_index(self) -> None:
        self.index = self._faiss.IndexFlatIP(self.dimensions)
        self._ids = list(self._embeddings.keys())
        if not self._ids:
            return
        matrix = np.vstack([self._embeddings[id] for id in self._ids]).astype("float32")
        self.index.add(matrix)

    def add(self, id: str, embedding: np.ndarray, metadata: dict[str, Any]) -> None:
        vector = self._normalize(embedding)
        if vector.shape[0] != self.dimensions:
            raise ValueError(f"Expected {self.dimensions} dimensions, got {vector.shape[0]}")
        self._embeddings[id] = vector
        self._metadata[id] = dict(metadata)
        self._rebuild_index()

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        if top_k <= 0 or not self._ids:
            return []
        query = self._normalize(query_embedding)
        if query.shape[0] != self.dimensions:
            return []
        scores, indices = self.index.search(query.reshape(1, -1).astype("float32"), min(top_k, len(self._ids)))
        results: list[SearchResult] = []
        for score, index in zip(scores[0], indices[0]):
            if index < 0:
                continue
            id = self._ids[int(index)]
            results.append((id, float(score), dict(self._metadata[id])))
        return results

    def update_metadata(self, id: str, metadata: dict[str, Any]) -> None:
        if id not in self._metadata:
            raise KeyError(f"Unknown vector id: {id}")
        self._metadata[id].update(metadata)

    def get_metadata(self, id: str) -> dict[str, Any]:
        if id not in self._metadata:
            raise KeyError(f"Unknown vector id: {id}")
        return dict(self._metadata[id])

    def get_all_ids(self) -> list[str]:
        return list(self._metadata.keys())

    def delete(self, id: str) -> None:
        self._metadata.pop(id, None)
        self._embeddings.pop(id, None)
        self._rebuild_index()
