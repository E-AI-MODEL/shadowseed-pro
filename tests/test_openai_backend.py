"""Tests for the OpenAI model backends (no network, no SDK required).

The wrapper accepts an injected client, so these tests exercise the chat and
embedding paths with a fake that mimics the OpenAI SDK response shapes. The
backend wiring in all three factories (model-benefit suite, open-set detector,
retrieval/ssl-vs-rag output model) is checked for construction-time validation
and name shape. No test reads OPENAI_API_KEY or hits the network.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from shadowseed.adapters.openai_client import OpenAIClient, openai_api_key
from shadowseed.detection.model_detector import (
    SUPPORTED_MODEL_BACKENDS,
    OpenAIDetectorBackend,
    make_detector_backend,
)
from shadowseed.benchmark.retrieval_model_benchmark import make_output_model
from shadowseed.benchmark.ssl45_model_benefit_suite import (
    OpenAIBackend,
    make_backend,
)


class _FakeChatCompletions:
    def __init__(self, text: str, captured: dict) -> None:
        self._text = text
        self._captured = captured

    def create(self, **kwargs):
        self._captured.update(kwargs)
        message = SimpleNamespace(content=self._text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class _FakeEmbeddings:
    def __init__(self, vectors: list[list[float]], captured: dict) -> None:
        self._vectors = vectors
        self._captured = captured

    def create(self, **kwargs):
        self._captured.update(kwargs)
        return SimpleNamespace(data=[SimpleNamespace(embedding=v) for v in self._vectors])


class _FakeOpenAISDK:
    def __init__(self, *, text="een antwoord", vectors=None) -> None:
        self.captured: dict = {}
        self.embed_captured: dict = {}
        self.chat = SimpleNamespace(
            completions=_FakeChatCompletions(text, self.captured)
        )
        self.embeddings = _FakeEmbeddings(vectors or [[0.1, 0.2]], self.embed_captured)


def test_openai_api_key_missing_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY is not set"):
        openai_api_key()


def test_openai_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "  sk-test  ")
    assert openai_api_key() == "sk-test"


def test_client_generate_sends_expected_request():
    sdk = _FakeOpenAISDK(text="  hallo wereld  ")
    client = OpenAIClient(model="gpt-4o-mini", client=sdk)

    out = client.generate("vraag?", max_new_tokens=64)

    assert out == "hallo wereld"
    assert sdk.captured["model"] == "gpt-4o-mini"
    assert sdk.captured["messages"] == [{"role": "user", "content": "vraag?"}]
    assert sdk.captured["temperature"] == 0.0
    assert sdk.captured["seed"] == 0
    assert sdk.captured["max_tokens"] == 64


def test_client_generate_handles_none_content():
    sdk = _FakeOpenAISDK(text=None)
    client = OpenAIClient(client=sdk)
    assert client.generate("vraag?") == ""


def test_client_embed_returns_vectors_in_order():
    sdk = _FakeOpenAISDK(vectors=[[1.0, 2.0], [3.0, 4.0]])
    client = OpenAIClient(client=sdk)

    out = client.embed(["a", "b"])

    assert out == [[1.0, 2.0], [3.0, 4.0]]
    assert sdk.embed_captured["input"] == ["a", "b"]
    assert sdk.embed_captured["model"] == "text-embedding-3-small"


def test_client_embed_empty_skips_call():
    sdk = _FakeOpenAISDK()
    client = OpenAIClient(client=sdk)
    assert client.embed([]) == []
    assert sdk.embed_captured == {}


def test_benefit_openai_backend_generates():
    backend = OpenAIBackend(model_id="gpt-4o-mini")
    backend.client = OpenAIClient(model="gpt-4o-mini", client=_FakeOpenAISDK(text="x"))
    assert backend.name == "openai:gpt-4o-mini"
    assert backend.generate("prompt", {}, "baseline", []) == "x"


def test_detector_openai_backend_parses_seeds():
    backend = OpenAIDetectorBackend(model_id="gpt-4o-mini")
    backend.client = OpenAIClient(
        client=_FakeOpenAISDK(text="Ontbrekende toelichting bij Federal Mogul.")
    )
    assert backend.name == "openai:gpt-4o-mini"
    seeds = backend.detect_seeds({"text": "Federal Mogul is a stricken parent firm."})
    assert seeds and any("Federal Mogul" in seed for seed in seeds)


def test_detector_openai_backend_empty_text_skips_call():
    backend = OpenAIDetectorBackend(model_id="gpt-4o-mini")

    def _boom(*args, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("client should not be used for empty text")

    backend.client = SimpleNamespace(generate=_boom)
    assert backend.detect_seeds({"text": ""}) == []


def test_make_backend_openai_requires_model_id():
    with pytest.raises(ValueError, match="model-id is required for backend openai"):
        make_backend("openai", None, 220)


def test_make_detector_backend_openai_requires_model_id():
    with pytest.raises(ValueError, match="model-id is required"):
        make_detector_backend("openai", None)


def test_make_output_model_openai_requires_model_id():
    with pytest.raises(ValueError, match="model-id is required for openai"):
        make_output_model("openai", None, 220)


def test_supported_model_backends_includes_openai():
    assert "openai" in SUPPORTED_MODEL_BACKENDS
