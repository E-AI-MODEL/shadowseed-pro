"""Vectorstore abstractions for weightless Shadow Seeds."""

from shadowseed.vectorstore.base import VectorStore
from shadowseed.vectorstore.factory import create_vector_store
from shadowseed.vectorstore.memory import InMemoryVectorStore

__all__ = ["VectorStore", "InMemoryVectorStore", "create_vector_store"]
