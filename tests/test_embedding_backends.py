"""Tests for pluggable embedding backends (no network, no SDK, no key).

The OpenAI path is exercised with an injected fake client so the wrapper and the
gap-3 wiring can be tested offline. The lexical path stays the deterministic
default; the OpenAI path proves the embedder is actually threaded through the
SSL-vs-RAG probe instead of the hard-wired hash.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.adapters.openai_client import OpenAIClient
from shadowseed.retrieval_probe import retrieval_probe_vs_question
from shadowseed.benchmark.ssl_vs_rag_benchmark import run_ssl_vs_rag_benchmark
from shadowseed.vectorstore import create_vector_store


class _FakeEmbeddings:
    """Maps text -> vector by keyword, so retrieval is controllable in tests."""

    def __init__(self, table: dict[str, list[float]], captured: dict) -> None:
        self._table = table
        self._captured = captured

    def _vector_for(self, text: str) -> list[float]:
        lowered = text.lower()
        for keyword, vector in self._table.items():
            if keyword in lowered:
                return vector
        return [0.0, 0.0, 1.0]

    def create(self, **kwargs):
        self._captured.update(kwargs)
        inputs = kwargs["input"]
        return SimpleNamespace(data=[SimpleNamespace(embedding=self._vector_for(t)) for t in inputs])


class _FakeSDK:
    def __init__(self, table: dict[str, list[float]]) -> None:
        self.embed_captured: dict = {}
        self.embeddings = _FakeEmbeddings(table, self.embed_captured)


def test_lexical_backend_is_default_128d():
    embed, dim = make_embedding_fn("lexical")
    assert dim == 128
    assert embed("hallo wereld").shape == (128,)


def test_openai_backend_known_model_dim_and_calls_client():
    sdk = _FakeSDK({"x": [1.0, 0.0, 0.0]})
    client = OpenAIClient(embedding_model="text-embedding-3-small", client=sdk)
    embed, dim = make_embedding_fn("openai", "text-embedding-3-small", client=client)
    assert dim == 1536  # from the known-dims table, no probe call
    vec = embed("x marks it")
    assert isinstance(vec, np.ndarray)
    assert vec.tolist() == [1.0, 0.0, 0.0]
    assert sdk.embed_captured["model"] == "text-embedding-3-small"


def test_openai_backend_unknown_model_probes_dimension():
    sdk = _FakeSDK({"": [0.1, 0.2, 0.3, 0.4]})  # matches any text
    client = OpenAIClient(embedding_model="some-future-model", client=sdk)
    _embed, dim = make_embedding_fn("openai", "some-future-model", client=client)
    assert dim == 4  # discovered by probing


def test_unknown_backend_raises():
    with pytest.raises(ValueError, match="Unknown embedding backend"):
        make_embedding_fn("nope")


def test_probe_uses_injected_embedder_not_the_hash():
    # Index a tiny corpus with a fake embedder; the gap chunk and the seed share
    # a vector, so the seed probe must surface it even though the question would
    # point elsewhere. This proves embed_fn is threaded through both arms.
    table = {
        "industrie": [1.0, 0.0, 0.0],
        "fabriek": [1.0, 0.0, 0.0],
        "recht": [0.0, 1.0, 0.0],
        "consument": [0.0, 1.0, 0.0],
    }
    sdk = _FakeSDK(table)
    client = OpenAIClient(embedding_model="text-embedding-3-small", client=sdk)
    embed, _dim = make_embedding_fn("openai", client=client)

    store = create_vector_store(backend="memory")
    store.add("law", embed("recht en consument"), {"text": "recht", "doc_id": "d", "chunk_id": "law"})
    store.add("ind", embed("industrie fabriek"), {"text": "industrie", "doc_id": "d", "chunk_id": "ind"})

    contrast = retrieval_probe_vs_question(
        store,
        "Vraag over de industrie en fabriek?",
        ["Consumentenrecht als ontbrekend kader."],
        top_k=1,
        embed_fn=embed,
    )
    assert contrast["question_chunk_ids"] == ["ind"]
    assert contrast["probe_chunk_ids"] == ["law"]
    assert contrast["seed_only_chunk_ids"] == ["law"]


def test_ssl_vs_rag_runs_with_openai_embeddings(tmp_path, monkeypatch):
    # End-to-end: fixture output model + injected OpenAI embedder, no network.
    table = {
        "industrie": [1.0, 0.0, 0.0],
        "koloni": [1.0, 0.0, 0.0],
        "katoen": [1.0, 0.0, 0.0],
        "recht": [0.0, 1.0, 0.0],
        "consument": [0.0, 1.0, 0.0],
        "rechter": [0.0, 1.0, 0.0],
    }
    sdk = _FakeSDK(table)

    import shadowseed.adapters.embedding as eb

    real_make = eb.make_embedding_fn

    def fake_make(backend="lexical", model_id=None, **kwargs):
        if backend == "openai":
            kwargs.setdefault("client", OpenAIClient(embedding_model="text-embedding-3-small", client=sdk))
        return real_make(backend, model_id, **kwargs)

    monkeypatch.setattr(
        "shadowseed.benchmark.ssl_vs_rag_benchmark.make_embedding_fn", fake_make
    )

    out = run_ssl_vs_rag_benchmark(
        "src/shadowseed/data/ssl_vs_rag_benchmark.json",
        str(tmp_path / "out.json"),
        model_backend="fixture",
        embedding_backend="openai",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["embedding_backend"] == "openai"
    assert payload["summary"]["embedding_dimensions"] == 1536
    assert len(payload["results"]) == 2
