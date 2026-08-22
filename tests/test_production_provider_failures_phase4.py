"""Production-local provider failure and retry-policy acceptance tests."""

from __future__ import annotations

import urllib.error

import pytest

from shadowseed.adapters import ollama_client, openai_client
from shadowseed.adapters.models import FixtureBackend
from shadowseed.adapters.ollama_client import OllamaClient
from shadowseed.adapters.openai_client import OpenAIClient
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController


def test_openai_client_uses_bounded_timeout_and_disables_automatic_retries(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}
    sentinel = object()

    def _fake_make_sdk_client(api_key: str, base_url: str | None, *, timeout: float):
        captured.update(api_key=api_key, base_url=base_url, timeout=timeout)
        return sentinel

    monkeypatch.setattr(openai_client, "openai_api_key", lambda: "sk-test")
    monkeypatch.setattr(openai_client, "_make_sdk_client", _fake_make_sdk_client)

    client = OpenAIClient()
    assert client.timeout == 120.0
    assert client.max_retries == 0
    assert client.client is sentinel
    assert captured == {
        "api_key": "sk-test",
        "base_url": None,
        "timeout": 120.0,
    }


def test_ollama_generation_uses_one_bounded_http_attempt(monkeypatch) -> None:
    calls: list[float | None] = []

    def _fail(_request, timeout=None):
        calls.append(timeout)
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(ollama_client.urllib.request, "urlopen", _fail)
    client = OllamaClient(model="tinyllama", host="http://localhost:11434")

    with pytest.raises(RuntimeError, match="Could not generate with Ollama"):
        client.generate("question")

    assert client.timeout == 120.0
    assert calls == [120.0]


def test_provider_failure_does_not_advance_persisted_state_or_ledger(
    tmp_path,
    monkeypatch,
) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Provider failure target",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    before = controller.workspace.repository.load_session(session_id)["state"]
    before_integrity = controller.workspace.repository.verify_production_integrity()

    def _timeout(*_args, **_kwargs):
        raise TimeoutError("provider timeout")

    monkeypatch.setattr(FixtureBackend, "generate", _timeout)

    with pytest.raises(TimeoutError, match="provider timeout"):
        controller.send_turn(session_id, "What is missing from this plan?")

    after = controller.workspace.repository.load_session(session_id)["state"]
    after_integrity = controller.workspace.repository.verify_production_integrity()
    assert after == before
    assert after_integrity["sequence_no"] == before_integrity["sequence_no"]
    assert after_integrity["head_hash"] == before_integrity["head_hash"]
