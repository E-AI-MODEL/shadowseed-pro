"""Vectorstore interface for Shadow Seed Learning.

The vectorstore is an index, not the source of truth. SSLManager.seeds remains
leading for weight, trace, status and Validation Gate decisions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np


SearchResult = tuple[str, float, dict[str, Any]]


class VectorStore(ABC):
    @abstractmethod
    def add(self, id: str, embedding: np.ndarray, metadata: dict[str, Any]) -> None:
        """Add or replace a vector and its metadata."""

    @abstractmethod
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[SearchResult]:
        """Return top_k matches as (id, similarity_score, metadata)."""

    @abstractmethod
    def update_metadata(self, id: str, metadata: dict[str, Any]) -> None:
        """Merge metadata into an existing vector entry."""

    @abstractmethod
    def get_metadata(self, id: str) -> dict[str, Any]:
        """Return metadata for an entry."""

    @abstractmethod
    def get_all_ids(self) -> list[str]:
        """Return all ids in the store."""

    @abstractmethod
    def delete(self, id: str) -> None:
        """Delete an entry if it exists."""
