"""Compatibility import path for a historical module.

Authority: COMPATIBILITY_ONLY
Canonical module: shadowseed.adapters.embedding

This module contains no implementation.
Do not add new behavior here. New internal code must import from the
canonical module above.
"""
from shadowseed.adapters.embedding import (
    EmbedFn,
    SUPPORTED_EMBEDDING_BACKENDS,
    make_embedding_fn,
)

__all__ = [
    "EmbedFn",
    "SUPPORTED_EMBEDDING_BACKENDS",
    "make_embedding_fn",
]
