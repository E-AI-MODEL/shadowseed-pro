"""Compatibility import path for a historical module.

Authority: COMPATIBILITY_ONLY
Canonical module: shadowseed.adapters.openai_client

This module contains no implementation.
Do not add new behavior here. New internal code must import from the
canonical module above.
"""
from shadowseed.adapters.openai_client import (
    DEFAULT_CHAT_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    OpenAIClient,
    openai_api_key,
)

__all__ = [
    "DEFAULT_CHAT_MODEL",
    "DEFAULT_EMBEDDING_MODEL",
    "OpenAIClient",
    "openai_api_key",
]
