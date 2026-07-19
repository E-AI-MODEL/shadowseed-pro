"""Tests for the Ollama model backends (no network).

The HTTP path is exercised with a fake ``urlopen`` so the tests stay offline.
The backend wiring in both factories (model-benefit suite and open-set
detector) is checked for construction-time validation and name shape.
"""

from __future__ import annotations

import io
import json

import pytest

from shadowseed.adapters import ollama_client
from shadowseed.adapters.ollama_client import OllamaClient, ollama_host
from shadowseed.detection.model_detector import (
    SUPPORTED_MODEL_BACKENDS,
    OllamaDetectorBackend,
    make_detector_backend,
)
from shadowseed.benchmark.ssl45_model_benefit_suite import (
    OllamaBackend,
    make_backend,
)


class _FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def _fake_urlopen(response_text: str):
    captured: dict = {}

    def _urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        payload = json.dumps({"response": response_text}).encode("utf-8")
        return _FakeResponse(payload)

    return _urlopen, captured


def test_ollama_host_defaults_and_normalizes(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert ollama_host() == "http://localhost:11434"

    monkeypatch.setenv("OLLAMA_HOST", "myhost:1234")
    assert ollama_host() == "http://myhost:1234"

    monkeypatch.setenv("OLLAMA_HOST", "https://remote:443/")
    assert ollama_host() == "https://remote:443"


def test_client_generate_posts_expected_payload(monkeypatch):
    urlopen, captured = _fake_urlopen("  hallo wereld  ")
    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", urlopen)

    client = OllamaClient(model="tinyllama", host="http://localhost:11434")
    out = client.generate("vraag?", max_new_tokens=64)

    assert out == "hallo wereld"
    assert captured["url"] == "http://localhost:11434/api/generate"
    body = captured["body"]
    assert body["model"] == "tinyllama"
    assert body["prompt"] == "vraag?"
    assert body["stream"] is False
    assert body["options"]["num_predict"] == 64
    assert body["options"]["temperature"] == 0.0
    assert body["options"]["seed"] == 0


def test_benefit_ollama_backend_generates(monkeypatch):
    urlopen, _ = _fake_urlopen("een antwoord")
    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", urlopen)

    backend = OllamaBackend(model_id="tinyllama", max_new_tokens=32)
    assert backend.name == "ollama:tinyllama"
    assert backend.generate("prompt", {}, "baseline", []) == "een antwoord"


def test_detector_ollama_backend_parses_seeds(monkeypatch):
    urlopen, _ = _fake_urlopen("Ontbrekende toelichting bij Federal Mogul.")
    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", urlopen)

    backend = OllamaDetectorBackend(model_id="tinyllama")
    assert backend.name == "ollama:tinyllama"
    seeds = backend.detect_seeds(
        {"text": "Federal Mogul is a stricken parent firm."}
    )
    assert seeds and any("Federal Mogul" in seed for seed in seeds)


def test_detector_ollama_backend_empty_text_skips_network(monkeypatch):
    def _boom(*args, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("network should not be hit for empty text")

    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", _boom)
    assert OllamaDetectorBackend(model_id="tinyllama").detect_seeds({"text": ""}) == []


def test_make_backend_ollama_requires_model_id():
    with pytest.raises(ValueError, match="model-id is required for backend ollama"):
        make_backend("ollama", None, 220)


def test_make_detector_backend_ollama_requires_model_id():
    with pytest.raises(ValueError, match="model-id is required"):
        make_detector_backend("ollama", None)


def test_supported_model_backends_includes_ollama():
    assert "ollama" in SUPPORTED_MODEL_BACKENDS
