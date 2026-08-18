"""Minimal Ollama HTTP client (standard library only).

This talks to a running Ollama server (default ``http://localhost:11434``) so
SSL model runs can use quantized GGUF models without pulling in the heavy
``transformers`` / ``torch`` stack. The same local API is also used by the
Workbench to discover models that are already installed, removing manual model
ID entry from the normal local tester path.

Decoding defaults to greedy (temperature 0, fixed seed) so the same prompt
produces the same output across runs as far as the selected model/runtime allows.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def ollama_host() -> str:
    """Resolve the Ollama base URL from ``OLLAMA_HOST`` or the local default."""
    host = os.environ.get("OLLAMA_HOST", "").strip() or DEFAULT_OLLAMA_HOST
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host.rstrip("/")


def _read_json(request: urllib.request.Request, *, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError) as exc:  # pragma: no cover - network dependent
        raise RuntimeError(f"Could not reach Ollama at {request.full_url}: {exc}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Ollama returned an invalid JSON response") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Ollama returned an unexpected response shape")
    return payload


def list_ollama_models(
    *,
    host: str | None = None,
    timeout: float = 5.0,
) -> list[str]:
    """Return locally installed Ollama model names in deterministic order.

    Discovery is read-only and talks only to the configured Ollama host. It does
    not pull models, send chat content, or change SSL state. Names are
    deduplicated case-insensitively while preserving the first spelling returned
    by Ollama.
    """

    base = (host or ollama_host()).rstrip("/")
    request = urllib.request.Request(f"{base}/api/tags", method="GET")
    payload = _read_json(request, timeout=timeout)
    raw_models = payload.get("models", [])
    if not isinstance(raw_models, list):
        raise RuntimeError("Ollama /api/tags response does not contain a model list")
    names_by_key: dict[str, str] = {}
    for item in raw_models:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("model") or "").strip()
        if name:
            names_by_key.setdefault(name.casefold(), name)
    return sorted(names_by_key.values(), key=str.casefold)


class OllamaClient:
    """Thin wrapper around the Ollama ``/api/generate`` endpoint."""

    def __init__(
        self,
        model: str,
        host: str | None = None,
        timeout: float = 600.0,
    ) -> None:
        self.model = model
        self.host = (host or ollama_host()).rstrip("/")
        self.timeout = timeout

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 220,
        temperature: float = 0.0,
        seed: int = 0,
    ) -> str:
        """Generate a completion for ``prompt`` and return the response text."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_new_tokens,
                "seed": seed,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            body = _read_json(request, timeout=self.timeout)
        except RuntimeError as exc:  # pragma: no cover - network dependent
            raise RuntimeError(
                f"Could not generate with Ollama model {self.model!r} at {self.host}. "
                f"Is `ollama serve` running and has the model been pulled with "
                f"`ollama pull {self.model}`? {exc}"
            ) from exc
        return str(body.get("response", "")).strip()
