"""Pluggable embedding backends for retrieval experiments.

The gap-2/gap-3 probe and the SSL-vs-RAG head-to-head originally hard-wired the
deterministic ``lexical_embedding`` (a 128-d hash). That is CI-safe but a toy:
it makes both the RAG arm and the SSL-probe arm brittle, so a gap-3 result under
it shows the *mechanism*, not a real RAG comparison. This module lets the same
experiment run on a real embedder so the retriever stops being the confound.

``make_embedding_fn`` returns ``(embed_fn, dimensions)``: a single-text -> vector
callable plus the vector width (needed to size dimension-checked stores like
FAISS; the in-memory store is dimension-agnostic). Optional model revisions are
applied at load time when the backend supports them, so provenance is not merely
recorded after the fact.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from shadowseed.text_similarity import lexical_embedding

EmbedFn = Callable[[str], np.ndarray]

SUPPORTED_EMBEDDING_BACKENDS: tuple[str, ...] = (
    "lexical",
    "sentence-transformers",
    "openai",
)

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
    revision: str | None = None,
) -> tuple[EmbedFn, int]:
    """Return ``(embed_fn, dimensions)`` for the chosen embedding backend.

    - ``lexical``: the deterministic CI hash (``lexical_embedding``), width
      ``dimensions``. ``revision`` is invalid because there is no remote model.
    - ``sentence-transformers``: local SentenceTransformer inference. When a
      revision is supplied it is passed to ``SentenceTransformer`` and therefore
      constrains the actual loaded model snapshot.
    - ``openai``: real embeddings via ``OpenAIClient.embed`` (needs the
      ``openai`` extra and ``OPENAI_API_KEY``, or an injected ``client``). Hosted
      model snapshot identity is represented by the chosen model id; a separate
      revision argument is rejected rather than merely recorded.
    """
    if backend == "lexical":
        if revision is not None:
            raise ValueError("lexical embeddings do not accept a model revision")
        dim = dimensions

        def lexical_embed(text: str) -> np.ndarray:
            return lexical_embedding(text, dimensions=dim)

        return lexical_embed, dim

    if backend == "sentence-transformers":
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Install shadowseed[models] to use sentence-transformers embeddings"
            ) from exc
        model = model_id or "sentence-transformers/all-MiniLM-L6-v2"
        kwargs = {"revision": revision} if revision is not None else {}
        encoder = SentenceTransformer(model, **kwargs)
        dimension = int(encoder.get_sentence_embedding_dimension())

        def sentence_transformer_embed(text: str) -> np.ndarray:
            return np.asarray(encoder.encode(text, normalize_embeddings=True), dtype=float)

        return sentence_transformer_embed, dimension

    if backend == "openai":
        if revision is not None:
            raise ValueError(
                "OpenAI embedding snapshot identity must be expressed by model_id; "
                "a separate revision cannot be applied by this adapter"
            )
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
