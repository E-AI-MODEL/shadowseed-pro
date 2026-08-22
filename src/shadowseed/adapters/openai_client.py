"""Minimal OpenAI client wrapper for real-model SSL runs.

The client keeps provider behavior explicit: bounded requests, no automatic SDK
retries, and no network activity at import or construction time. Product code
reads credentials from the environment and does not accept them as arguments.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_CHAT_MODEL = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_PROVIDER_TIMEOUT_SECONDS = 120.0
DEFAULT_PROVIDER_MAX_RETRIES = 0


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


def _make_sdk_client(
    api_key: str,
    base_url: str | None,
    *,
    timeout: float,
) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "Install the optional OpenAI dependency first: "
            "pip install -e '.[openai]' (or pip install openai)."
        ) from exc
    kwargs: dict[str, Any] = {
        "api_key": api_key,
        "timeout": timeout,
        "max_retries": DEFAULT_PROVIDER_MAX_RETRIES,
    }
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


class OpenAIClient:
    """Thin wrapper around the OpenAI chat-completions and embeddings APIs.

    ``client`` may be injected for testing; when omitted it is constructed from
    ``OPENAI_API_KEY`` on first use. Automatic SDK retries are disabled so a
    provider failure is surfaced to the application instead of being silently
    replayed behind an authority-bearing product flow.
    """

    def __init__(
        self,
        model: str = DEFAULT_CHAT_MODEL,
        *,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        base_url: str | None = None,
        timeout: float = DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        client: Any | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("provider timeout must be positive")
        self.model = model
        self.embedding_model = embedding_model
        self.base_url = base_url
        self.timeout = float(timeout)
        self.max_retries = DEFAULT_PROVIDER_MAX_RETRIES
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = _make_sdk_client(
                openai_api_key(),
                self.base_url,
                timeout=self.timeout,
            )
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
