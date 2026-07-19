"""Safe in-memory vectorstore for SSL 4.5.

This implementation is intentionally dependency-free. It is suitable for tests,
CI smoke runs and local research. FAISS or Chroma can be added later behind the
same VectorStore interface.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from shadowseed.vectorstore.base import SearchResult, VectorStore


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._embeddings: dict[str, np.ndarray] = {}
        self._metadata: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _normalize(embedding: np.ndarray) -> np.ndarray:
        vector = np.asarray(embedding, dtype=float)
        norm = np.linalg.norm(vector)
        if norm == 0:
            return vector
        return vector / norm

    def add(self, id: str, embedding: np.ndarray, metadata: dict[str, Any]) -> None:
        self._embeddings[id] = self._normalize(embedding)
        self._metadata[id] = dict(metadata)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        if top_k <= 0:
            return []
        query = self._normalize(query_embedding)
        results: list[SearchResult] = []
        for id, embedding in self._embeddings.items():
            if query.shape != embedding.shape:
                continue
            score = float(np.dot(query, embedding))
            results.append((id, score, dict(self._metadata[id])))
        results.sort(key=lambda item: item[1], reverse=True)
        return results[:top_k]

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
