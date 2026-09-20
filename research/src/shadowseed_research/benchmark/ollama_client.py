"""Compatibility import path for a historical module.

Authority: COMPATIBILITY_ONLY
Canonical module: shadowseed.adapters.ollama_client

This module contains no implementation.
Do not add new behavior here. New internal code must import from the
canonical module above.
"""
from shadowseed.adapters.ollama_client import (
    DEFAULT_OLLAMA_HOST,
    OllamaClient,
    ollama_host,
)

__all__ = [
    "DEFAULT_OLLAMA_HOST",
    "OllamaClient",
    "ollama_host",
]
