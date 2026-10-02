from __future__ import annotations

import sys
from types import SimpleNamespace

import numpy as np
import pytest

from shadowseed.adapters.embedding import make_embedding_fn


def test_sentence_transformer_revision_is_applied_at_load(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeSentenceTransformer:
        def __init__(self, model: str, **kwargs: object) -> None:
            calls.append((model, kwargs))

        def get_embedding_dimension(self) -> int:
            return 3

        def get_sentence_embedding_dimension(self) -> int:
            raise AssertionError("legacy dimension API should not be used when current API exists")

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



def test_sentence_transformer_dimension_falls_back_to_legacy_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeLegacySentenceTransformer:
        def __init__(self, model: str, **kwargs: object) -> None:
            assert model == "org/legacy-model"
            assert kwargs == {}

        def get_sentence_embedding_dimension(self) -> int:
            return 2

        def encode(self, text: str, normalize_embeddings: bool = False) -> list[float]:
            assert normalize_embeddings is True
            return [4.0, 5.0]

    monkeypatch.setitem(
        sys.modules,
        "sentence_transformers",
        SimpleNamespace(SentenceTransformer=FakeLegacySentenceTransformer),
    )

    embed, dimension = make_embedding_fn(
        "sentence-transformers",
        "org/legacy-model",
    )

    assert dimension == 2
    assert np.array_equal(embed("hello"), np.array([4.0, 5.0]))


def test_unappliable_embedding_revisions_fail_closed() -> None:
    with pytest.raises(ValueError, match="lexical embeddings"):
        make_embedding_fn("lexical", revision="not-applicable")

    with pytest.raises(ValueError, match="OpenAI embedding snapshot identity"):
        make_embedding_fn("openai", "text-embedding-3-small", revision="separate-revision")
