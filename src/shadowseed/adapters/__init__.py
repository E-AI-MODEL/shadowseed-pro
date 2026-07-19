"""Runtime adapters for model, embedding, and hosted-service backends."""

from shadowseed.adapters.embedding import SUPPORTED_EMBEDDING_BACKENDS, make_embedding_fn
from shadowseed.adapters.models import (
    FixtureBackend,
    HFTransformersBackend,
    ModelBackend,
    OllamaBackend,
    OpenAIBackend,
    make_backend,
)

__all__ = [
    "SUPPORTED_EMBEDDING_BACKENDS",
    "FixtureBackend",
    "HFTransformersBackend",
    "ModelBackend",
    "OllamaBackend",
    "OpenAIBackend",
    "make_backend",
    "make_embedding_fn",
]
