"""Minimal Ollama HTTP client (standard library only).

This talks to a running Ollama server (default ``http://localhost:11434``) so
SSL model runs can use quantized GGUF models without pulling in the heavy
``transformers`` / ``torch`` stack. That makes a real small-model run feasible
inside a standard CI runner: install Ollama, ``ollama pull`` a model, point the
run at it.

Decoding defaults to greedy (temperature 0, fixed seed) so the same prompt
produces the same output across runs.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def ollama_host() -> str:
    """Resolve the Ollama base URL from ``OLLAMA_HOST`` or the local default."""
    host = os.environ.get("OLLAMA_HOST", "").strip() or DEFAULT_OLLAMA_HOST
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    return host.rstrip("/")


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
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:  # pragma: no cover - network dependent
            raise RuntimeError(
                f"Could not reach Ollama at {self.host}. Is `ollama serve` running "
                f"and has the model been pulled with `ollama pull {self.model}`? "
                f"Original error: {exc}"
            ) from exc
        return str(body.get("response", "")).strip()
