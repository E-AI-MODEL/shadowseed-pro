"""Endpoint policy for the bounded production-local product surface."""

from __future__ import annotations

import ipaddress
import os
from urllib.parse import urlparse


class ProviderPolicyError(ValueError):
    """Raised when a production-local provider target crosses the accepted boundary."""


def _is_loopback_hostname(hostname: str | None) -> bool:
    if not hostname:
        return False
    normalized = hostname.strip().casefold()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def production_local_ollama_host() -> str:
    """Return a loopback-only Ollama endpoint for the production-local surface."""

    raw = os.environ.get("OLLAMA_HOST", "").strip() or "http://localhost:11434"
    candidate = raw if raw.startswith(("http://", "https://")) else f"http://{raw}"
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not _is_loopback_hostname(parsed.hostname):
        raise ProviderPolicyError(
            "production-local Ollama must use a loopback endpoint; remote OLLAMA_HOST "
            "belongs to a trusted-development or separately governed deployment"
        )
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ProviderPolicyError("production-local Ollama endpoint contains unsupported URL fields")
    return candidate.rstrip("/")


def validate_production_local_backend(backend: str, embedding_backend: str) -> None:
    """Validate provider endpoint policy without changing Gate or model semantics."""

    if backend == "ollama":
        production_local_ollama_host()
    if backend == "openai" or embedding_backend == "openai":
        # The product OpenAI adapters construct the official SDK client without a
        # caller-controlled base URL. Research clients may expose a base URL, but
        # the production-local controller does not route one through.
        return
