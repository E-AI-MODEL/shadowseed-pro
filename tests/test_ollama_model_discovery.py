from __future__ import annotations

import json
import urllib.error
import urllib.request

import pytest

from shadowseed.adapters.ollama_client import list_ollama_models
from shadowseed.workbench.controller import WorkbenchController


class _Response:
    def __init__(self, payload) -> None:
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_list_ollama_models_reads_tags_without_sending_chat_content(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["data"] = request.data
        captured["timeout"] = timeout
        return _Response(
            {
                "models": [
                    {"name": "qwen2.5:7b"},
                    {"model": "llama3.2:3b"},
                    {"name": "QWEN2.5:7B"},
                    {"name": ""},
                ]
            }
        )

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)

    models = list_ollama_models(host="http://127.0.0.1:11434", timeout=1.5)

    assert models == ["llama3.2:3b", "qwen2.5:7b"]
    assert captured == {
        "url": "http://127.0.0.1:11434/api/tags",
        "method": "GET",
        "data": None,
        "timeout": 1.5,
    }


def test_list_ollama_models_rejects_invalid_tags_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda request, timeout: _Response({"models": "not-a-list"}),
    )

    with pytest.raises(RuntimeError, match="model list"):
        list_ollama_models()


def test_list_ollama_models_reports_unavailable_server(monkeypatch) -> None:
    def fail(request, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(urllib.request, "urlopen", fail)

    with pytest.raises(RuntimeError, match="Could not reach Ollama"):
        list_ollama_models(host="http://127.0.0.1:11434")


def test_workbench_controller_exposes_ollama_discovery(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["model-a:latest", "model-b:7b"],
    )
    controller = WorkbenchController(tmp_path / "workspace")

    assert controller.discover_models("ollama") == ["model-a:latest", "model-b:7b"]
    assert controller.discover_models("fixture") == []
    assert controller.discover_models("openai") == []
