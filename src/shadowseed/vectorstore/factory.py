"""Factory for optional vectorstore backends."""

from __future__ import annotations

from shadowseed.vectorstore.base import VectorStore
from shadowseed.vectorstore.memory import InMemoryVectorStore


def create_vector_store(
    backend: str = "memory",
    dimensions: int = 128,
    collection_name: str = "shadowseed",
    persist_directory: str | None = None,
) -> VectorStore:
    if backend == "memory":
        return InMemoryVectorStore()
    if backend == "faiss":
        from shadowseed.vectorstore.faiss_store import FaissVectorStore

        return FaissVectorStore(dimensions=dimensions)
    if backend == "chroma":
        from shadowseed.vectorstore.chroma_store import ChromaVectorStore

        return ChromaVectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory,
        )
    raise ValueError(f"Unknown vectorstore backend: {backend}")
