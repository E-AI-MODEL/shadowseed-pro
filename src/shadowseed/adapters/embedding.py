"""Pluggable embedding backends for retrieval experiments.

The gap-2/gap-3 probe and the SSL-vs-RAG head-to-head originally hard-wired the
deterministic ``lexical_embedding`` (a 128-d hash). That is CI-safe but a toy:
it makes both the RAG arm and the SSL-probe arm brittle, so a gap-3 result under
it shows the *mechanism*, not a real RAG comparison. This module lets the same
experiment run on a real embedder (OpenAI) so the retriever stops being the
confound.

``make_embedding_fn`` returns ``(embed_fn, dimensions)``: a single-text -> vector
callable plus the vector width (needed to size dimension-checked stores like
FAISS; the in-memory store is dimension-agnostic). The OpenAI client is injected
in tests, so nothing here needs network or a key to import or unit-test.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from shadowseed.text_similarity import lexical_embedding

EmbedFn = Callable[[str], np.ndarray]

SUPPORTED_EMBEDDING_BACKENDS: tuple[str, ...] = ("lexical", "openai")

# Output widths for common OpenAI embedding models; if a model is not listed we
# probe it once (one embedding call) to discover its dimension.
_OPENAI_EMBEDDING_DIMS: dict[str, int] = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
}


def make_embedding_fn(
    backend: str = "lexical",
    model_id: str | None = None,
    *,
    dimensions: int = 128,
    client: Any | None = None,
) -> tuple[EmbedFn, int]:
    """Return ``(embed_fn, dimensions)`` for the chosen embedding backend.

    - ``lexical``: the deterministic CI hash (``lexical_embedding``), width
      ``dimensions``.
    - ``openai``: real embeddings via ``OpenAIClient.embed`` (needs the
      ``openai`` extra and ``OPENAI_API_KEY``, or an injected ``client``).
    """
    if backend == "lexical":
        dim = dimensions

        def lexical_embed(text: str) -> np.ndarray:
            return lexical_embedding(text, dimensions=dim)

        return lexical_embed, dim

    if backend == "openai":
        from shadowseed.adapters.openai_client import DEFAULT_EMBEDDING_MODEL, OpenAIClient

        model = model_id or DEFAULT_EMBEDDING_MODEL
        oc = client if client is not None else OpenAIClient(embedding_model=model)

        def openai_embed(text: str) -> np.ndarray:
            return np.asarray(oc.embed([text])[0], dtype=float)

        dim = _OPENAI_EMBEDDING_DIMS.get(model)
        if dim is None:
            dim = int(len(openai_embed("dimension probe")))
        return openai_embed, dim

    raise ValueError(
        f"Unknown embedding backend {backend!r}. Allowed: {SUPPORTED_EMBEDDING_BACKENDS}."
    )
