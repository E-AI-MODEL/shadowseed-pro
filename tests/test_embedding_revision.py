from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.chat import ShadowChatSession


def test_sentence_transformer_revision_is_applied_at_load(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeSentenceTransformer:
        def __init__(self, model: str, **kwargs: object) -> None:
            calls.append((model, kwargs))

        def get_sentence_embedding_dimension(self) -> int:
            return 3

        def encode(self, text: str, normalize_embeddings: bool = False) -> list[float]:
            assert normalize_embeddings is True
            return [1.0, 2.0, 3.0]

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=FakeSentenceTransformer),
    )

    embed, dimension = make_embedding_fn(
        "sentence-transformers",
        "org/model",
        revision="abc123",
    )

    assert calls == [("org/model", {"revision": "abc123"})]
    assert dimension == 3
    assert np.array_equal(embed("hello"), np.array([1.0, 2.0, 3.0]))


def test_ollama_embedding_backend_uses_injected_local_client() -> None:
    calls: list[object] = []

    class FakeOllama:
        def embed(self, text):
            calls.append(text)
            if text == "dimension probe":
                return [[1.0, 0.0, 0.0, 0.0]]
            return [[0.0, 1.0, 0.0, 0.0]]

    embed, dimension = make_embedding_fn(
        "ollama",
        "embeddinggemma",
        client=FakeOllama(),
    )

    assert dimension == 4
    assert np.array_equal(embed("hello"), np.array([0.0, 1.0, 0.0, 0.0]))
    assert calls == ["dimension probe", "hello"]


def test_runtime_state_persists_resolved_ollama_embedding_model() -> None:
    session = ShadowChatSession(
        backend="fixture",
        embedding_backend="ollama",
        embedding_fn=lambda _text: np.asarray([1.0, 0.0], dtype=float),
    )

    assert session.embedding_model == "embeddinggemma"
    assert session.to_state()["session_config"]["embedding_model"] == "embeddinggemma"


def test_unappliable_embedding_revisions_fail_closed() -> None:
    with pytest.raises(ValueError, match="lexical embeddings"):
        make_embedding_fn("lexical", revision="not-applicable")

    with pytest.raises(ValueError, match="Ollama embedding identity"):
        make_embedding_fn("ollama", "embeddinggemma", revision="separate-revision")

    with pytest.raises(ValueError, match="OpenAI embedding snapshot identity"):
        make_embedding_fn("openai", "text-embedding-3-small", revision="separate-revision")
