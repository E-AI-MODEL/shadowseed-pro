"""Minimal Ollama HTTP client (standard library only).

This talks to a running Ollama server (default ``http://localhost:11434``) so
SSL model runs can use quantized GGUF models without pulling in the heavy
``transformers`` / ``torch`` stack. Requests use an explicit bounded timeout
and are never retried automatically.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_OLLAMA_HOST = "http://localhost:11434"
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 120.0
DEFAULT_OLLAMA_EMBEDDING_MODEL = "embeddinggemma"


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


def ollama_model_capabilities(
    model: str,
    *,
    host: str | None = None,
    timeout: float = 5.0,
) -> tuple[str, ...]:
    """Return model capabilities reported by Ollama /api/show."""

    base = (host or ollama_host()).rstrip("/")
    data = json.dumps({"model": model}).encode("utf-8")
    request = urllib.request.Request(
        f"{base}/api/show",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    payload = _read_json(request, timeout=timeout)
    raw = payload.get("capabilities", [])
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise RuntimeError("Ollama /api/show response contains invalid capabilities")
    return tuple(
        str(item).strip().casefold()
        for item in raw
        if str(item).strip()
    )


def list_ollama_chat_models(
    *,
    host: str | None = None,
    timeout: float = 5.0,
) -> list[str]:
    """Return installed models that Ollama reports as completion-capable.

    Older Ollama servers may omit capabilities. Those models remain visible as a
    compatibility fallback instead of being hidden from the user.
    """

    models = list_ollama_models(host=host, timeout=timeout)
    selected: list[str] = []
    for model in models:
        try:
            capabilities = ollama_model_capabilities(
                model,
                host=host,
                timeout=timeout,
            )
        except RuntimeError:
            selected.append(model)
            continue
        if not capabilities or "completion" in capabilities:
            selected.append(model)
    return selected


class OllamaClient:
    """Thin wrapper around the Ollama ``/api/generate`` endpoint.

    Generation performs one HTTP attempt. Failures are surfaced immediately to
    the application, which can then preserve the pre-call persisted state.
    """

    def __init__(
        self,
        model: str,
        host: str | None = None,
        timeout: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    ) -> None:
        if timeout <= 0:
            raise ValueError("provider timeout must be positive")
        self.model = model
        self.host = (host or ollama_host()).rstrip("/")
        self.timeout = float(timeout)

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
                "Is `ollama serve` running and has the model been pulled with "
                f"`ollama pull {self.model}`? {exc}"
            ) from exc
        return str(body.get("response", "")).strip()

    def generate_chat(
        self,
        messages: list[dict[str, str]],
        *,
        max_new_tokens: int = 220,
        temperature: float = 0.0,
        seed: int = 0,
    ) -> str:
        """Generate from Ollama's native chat endpoint using role-structured turns."""

        payload = {
            "model": self.model,
            "messages": [dict(message) for message in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_new_tokens,
                "seed": seed,
            },
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            body = _read_json(request, timeout=self.timeout)
        except RuntimeError as exc:  # pragma: no cover - network dependent
            raise RuntimeError(
                f"Could not chat with Ollama model {self.model!r} at {self.host}. "
                "Is `ollama serve` running and has the model been pulled with "
                f"`ollama pull {self.model}`? {exc}"
            ) from exc
        message = body.get("message", {})
        if not isinstance(message, dict):
            raise RuntimeError("Ollama /api/chat response does not contain a message")
        return str(message.get("content", "")).strip()

    def embed(self, text: str | list[str]) -> list[list[float]]:
        """Generate one or more embeddings through Ollama\'s local /api/embed endpoint."""

        payload = {
            "model": self.model,
            "input": text,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host}/api/embed",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            body = _read_json(request, timeout=self.timeout)
        except RuntimeError as exc:  # pragma: no cover - network dependent
            raise RuntimeError(
                f"Could not embed with Ollama model {self.model!r} at {self.host}. "
                "Is `ollama serve` running and has the embedding model been pulled with "
                f"`ollama pull {self.model}`? {exc}"
            ) from exc

        embeddings = body.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise RuntimeError("Ollama /api/embed response does not contain embeddings")
        expected = len(text) if isinstance(text, list) else 1
        if expected <= 0:
            raise ValueError("Ollama embedding input must not be empty")
        if len(embeddings) != expected:
            raise RuntimeError(
                "Ollama /api/embed returned a different number of vectors than inputs"
            )

        normalized: list[list[float]] = []
        for vector in embeddings:
            if not isinstance(vector, list) or not vector:
                raise RuntimeError("Ollama /api/embed returned an invalid embedding vector")
            try:
                normalized.append([float(value) for value in vector])
            except (TypeError, ValueError) as exc:
                raise RuntimeError(
                    "Ollama /api/embed returned a non-numeric embedding vector"
                ) from exc
        return normalized
