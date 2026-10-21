"""New-chat setup failures must be actionable and leave no persisted session."""

from __future__ import annotations

import pytest

from shadowseed.application.provider_policy import ProviderPolicyError
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
from shadowseed_webapi.service import WebApiService


@pytest.mark.parametrize(("requested", "installed"), [
    (None, "embeddinggemma:latest"),
    ("embeddinggemma", "embeddinggemma:latest"),
    ("embeddinggemma:latest", "embeddinggemma"),
    ("embeddinggemma:v2", "embeddinggemma:v2"),
    ("registry:5000/team/embed", "registry:5000/team/embed:latest"),
])
def test_embedding_preflight_resolves_only_exact_or_default_tag(
    monkeypatch, requested, installed,
):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: [installed],
    )
    WorkbenchController.validate_ollama_embedding_model(requested)


@pytest.mark.parametrize("requested", ["embeddinggemma", "embeddinggemma:v1"])
def test_embedding_preflight_does_not_substitute_another_tag(monkeypatch, requested):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["embeddinggemma:v2"],
    )
    with pytest.raises(ValueError, match=f"ollama pull {requested}"):
        WorkbenchController.validate_ollama_embedding_model(requested)


@pytest.mark.parametrize("controller_type", [
    WorkbenchController, ProductionLocalWorkbenchController,
])
def test_all_workbench_entry_points_preflight_before_persisting(
    monkeypatch, tmp_path, controller_type,
):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["qwen3:8b"],
    )
    controller = controller_type(tmp_path / "workspace")
    with pytest.raises(ValueError, match="ollama pull embeddinggemma"):
        controller.create_session(
            title="Missing dependency", profile_id="balanced",
            backend="ollama", model_id="qwen3:8b",
        )
    assert controller.list_sessions() == []


def test_web_api_missing_model_is_actionable_and_does_not_create_chat(monkeypatch, tmp_path):
    installed = ["qwen3:8b"]
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: installed,
    )
    api = WebApiService(tmp_path / "workspace")
    with pytest.raises(ValueError, match="ollama pull embeddinggemma"):
        api.create_session({"backend": "ollama", "model_id": "qwen3:8b"})
    assert api.list_sessions()["sessions"] == []

    # A corrected local installation can retry in the same workspace.
    installed.append("embeddinggemma:latest")
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.OllamaClient.embed",
        lambda self, text: [[1.0, 0.0, 0.0]],
    )
    session = api.create_session({"backend": "ollama", "model_id": "qwen3:8b"})
    assert session["session_id"]
    assert len(api.list_sessions()["sessions"]) == 1


def test_unreachable_ollama_does_not_create_chat(monkeypatch, tmp_path):
    def unavailable():
        raise RuntimeError("connection refused")

    monkeypatch.setattr("shadowseed.adapters.ollama_client.list_ollama_models", unavailable)
    controller = WorkbenchController(tmp_path / "workspace")
    with pytest.raises(ValueError, match="Start Ollama"):
        controller.create_session(
            title="Offline", profile_id="balanced", backend="ollama", model_id="qwen3:8b",
        )
    assert controller.list_sessions() == []


def test_remote_endpoint_is_rejected_before_preflight_io(monkeypatch, tmp_path):
    monkeypatch.setenv("OLLAMA_HOST", "https://remote.example.invalid")
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: pytest.fail("must reject endpoint before making a request"),
    )
    api = WebApiService(tmp_path / "workspace")
    with pytest.raises(ProviderPolicyError, match="loopback"):
        api.create_session({"backend": "ollama", "model_id": "qwen3:8b"})
    assert api.list_sessions()["sessions"] == []


def test_fixture_setup_never_contacts_ollama(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: pytest.fail("fixture must work without Ollama"),
    )
    controller = WorkbenchController(tmp_path / "workspace")
    controller.create_session(title="Offline demo", profile_id="demo", backend="fixture")
    assert len(controller.list_sessions()) == 1
