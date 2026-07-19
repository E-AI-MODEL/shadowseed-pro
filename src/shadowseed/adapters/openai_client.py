"""Minimal OpenAI client wrapper for real-model SSL runs.

This lets the detector and the model-benefit / SSL-vs-RAG suites call a strong
hosted model instead of a CPU-bound local SLM. The whole point of adding it is
that the *payoff* experiments (does acting on a seed help? does retrieving
toward the gap beat retrieving toward the question?) were bottlenecked on model
capability — a 3.8B model on a CI runner derails on the rewrite step. A capable
API model removes that confound so the result reflects the method, not the
model's weakness.

Design mirrors ``ollama_client.py``:

- The ``openai`` package is an *optional* dependency (the ``openai`` extra).
  This module imports cleanly without it; the import only happens when a client
  is actually constructed, so fixture/CI paths never need the package.
- The API key is read from ``OPENAI_API_KEY`` and is NEVER taken as a function
  argument that could end up in a logged artifact. If it is missing we fail
  with a clear message rather than a deep SDK stack trace.
- Decoding defaults to ``temperature=0`` with a fixed ``seed`` so the same
  prompt produces the same output across runs as far as the API allows. (The
  API does not guarantee bit-exact determinism, only best-effort with seed.)

No network call happens at import or construction time, so unit tests can
inject a fake client and exercise the wrapper without credentials.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def openai_api_key() -> str:
    """Resolve the OpenAI API key from ``OPENAI_API_KEY`` or fail clearly."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Export it locally "
            "(export OPENAI_API_KEY=...) or add it as a GitHub Actions secret "
            "named OPENAI_API_KEY. Never paste the key into source or logs."
        )
    return key


def _make_sdk_client(api_key: str, base_url: str | None) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Install the optional OpenAI dependency first: "
            "pip install -e '.[openai]' (or pip install openai)."
        ) from exc
    kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


class OpenAIClient:
    """Thin wrapper around the OpenAI chat-completions and embeddings APIs.

    ``client`` may be injected for testing; when omitted it is constructed from
    ``OPENAI_API_KEY`` on first use.
    """

    def __init__(
        self,
        model: str = DEFAULT_CHAT_MODEL,
        *,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        base_url: str | None = None,
        timeout: float = 120.0,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.embedding_model = embedding_model
        self.base_url = base_url
        self.timeout = timeout
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _make_sdk_client(openai_api_key(), self.base_url)
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        max_new_tokens: int = 220,
        temperature: float = 0.0,
        seed: int = 0,
    ) -> str:
        """Generate a chat completion for ``prompt`` and return the text."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            seed=seed,
            max_tokens=max_new_tokens,
            timeout=self.timeout,
        )
        content = response.choices[0].message.content
        return (content or "").strip()

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return embedding vectors for ``texts`` (order preserved)."""
        if not texts:
            return []
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=texts,
            timeout=self.timeout,
        )
        return [list(item.embedding) for item in response.data]
