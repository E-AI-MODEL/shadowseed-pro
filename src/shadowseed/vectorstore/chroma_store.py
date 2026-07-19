"""Optional Chroma vectorstore adapter.

Install with:

    pip install -e ".[vector-chroma]"

The adapter stores vectors and metadata in a Chroma collection while keeping the
same VectorStore interface used by the rest of SSL. When a persistent Chroma
collection is opened, existing ids and metadata are hydrated back into the
adapter cache so the public VectorStore methods remain valid after restart.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

import numpy as np

from shadowseed.vectorstore.base import SearchResult, VectorStore


def _as_list(value: Any) -> list:
    """Normalize a Chroma payload field to a list.

    Chroma returns embeddings as a numpy array in recent versions. The old
    `value or []` idiom raised "truth value of an empty array is ambiguous"
    on those arrays, which crashed hydration of a persisted collection. An
    explicit None check avoids evaluating the array in a boolean context.
    """
    if value is None:
        return []
    return list(value)


class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name: str = "shadowseed", persist_directory: str | None = None) -> None:
        try:
            import chromadb  # type: ignore
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Chroma is optional. Install it with: pip install -e '.[vector-chroma]'"
            ) from exc

        self.collection_name = collection_name
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        self.collection = self.client.get_or_create_collection(
            name=f"{collection_name}_{uuid4().hex[:8]}" if persist_directory is None else collection_name
        )
        self._metadata: dict[str, dict[str, Any]] = {}
        self._embeddings: dict[str, np.ndarray] = {}
        self._hydrate_cache_from_collection()

    @staticmethod
    def _normalize(embedding: np.ndarray) -> list[float]:
        vector = np.asarray(embedding, dtype=float)
        norm = np.linalg.norm(vector)
        if norm != 0:
            vector = vector / norm
        return vector.tolist()

    @staticmethod
    def _to_chroma_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool]:
        clean: dict[str, str | int | float | bool] = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                clean[key] = value
            else:
                clean[key] = str(value)
        return clean

    def _collection_count(self) -> int:
        try:
            return int(self.collection.count())
        except Exception:  # pragma: no cover - defensive around optional backend versions
            return len(self._metadata)

    def _hydrate_cache_from_collection(self) -> None:
        """Load ids and metadata from the backing Chroma collection.

        Chroma is optional and versioned independently from the rest of the repo,
        so this method is deliberately conservative: metadata hydration is enough
        for the VectorStore contract, while embeddings are only cached when the
        backend returns them.
        """
        try:
            payload = self.collection.get(include=["metadatas", "embeddings"])
        except Exception:  # pragma: no cover - optional backend compatibility
            try:
                payload = self.collection.get(include=["metadatas"])
            except Exception:
                return

        ids = _as_list(payload.get("ids"))
        metadatas = _as_list(payload.get("metadatas"))
        embeddings = _as_list(payload.get("embeddings"))

        for id, metadata in zip(ids, metadatas):
            self._metadata[str(id)] = dict(metadata or {})

        for id, embedding in zip(ids, embeddings):
            if embedding is not None:
                self._embeddings[str(id)] = np.asarray(embedding, dtype=float)

    def add(self, id: str, embedding: np.ndarray, metadata: dict[str, Any]) -> None:
        vector = self._normalize(embedding)
        self.delete(id)
        self.collection.add(
            ids=[id],
            embeddings=[vector],
            metadatas=[self._to_chroma_metadata(metadata)],
            documents=[str(metadata.get("text", id))],
        )
        self._metadata[id] = dict(metadata)
        self._embeddings[id] = np.asarray(vector, dtype=float)

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        count = self._collection_count()
        if top_k <= 0 or count <= 0:
            return []
        query = self._normalize(query_embedding)
        results = self.collection.query(
            query_embeddings=[query],
            n_results=min(top_k, count),
            include=["metadatas", "distances"],
        )
        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        output: list[SearchResult] = []
        for id, distance, metadata in zip(ids, distances, metadatas):
            id = str(id)
            merged_metadata = dict(metadata or self._metadata.get(id, {}))
            self._metadata[id] = merged_metadata
            # Chroma returns distance. Convert to a bounded similarity-like score.
            similarity = 1.0 / (1.0 + float(distance))
            output.append((id, similarity, dict(merged_metadata)))
        output.sort(key=lambda item: item[1], reverse=True)
        return output

    def update_metadata(self, id: str, metadata: dict[str, Any]) -> None:
        current = self.get_metadata(id)
        current.update(metadata)
        self.collection.update(
            ids=[id],
            metadatas=[self._to_chroma_metadata(current)],
        )
        self._metadata[id] = current

    def get_metadata(self, id: str) -> dict[str, Any]:
        if id not in self._metadata:
            self._hydrate_cache_from_collection()
        if id not in self._metadata:
            raise KeyError(f"Unknown vector id: {id}")
        return dict(self._metadata[id])

    def get_all_ids(self) -> list[str]:
        self._hydrate_cache_from_collection()
        return list(self._metadata.keys())

    def delete(self, id: str) -> None:
        try:
            self.collection.delete(ids=[id])
        except Exception:
            pass
        self._metadata.pop(id, None)
        self._embeddings.pop(id, None)
