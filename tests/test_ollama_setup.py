"""New-chat setup failures must be actionable and leave no persisted session."""

from __future__ import annotations

import pytest

from shadowseed.application.provider_policy import ProviderPolicyError
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
from shadowseed_webapi.service import WebApiService

@pytest.fixture(autouse=True)
def compatible_ollama_version(monkeypatch):
    """Existing installed-model tests use a compatible server version."""
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        lambda: "0.12.0",
    )


@pytest.fixture(autouse=True)
def compatible_ollama_version(monkeypatch):
    """Simulated model inventory also simulates a supported server version."""
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        lambda: "0.12.0",
    )



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


def test_old_ollama_rejects_installed_embeddinggemma_before_chat(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["embeddinggemma:latest", "qwen3:8b"],
    )
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        lambda: "0.11.9",
    )
    controller = WorkbenchController(tmp_path / "workspace")
    with pytest.raises(ValueError, match="EmbeddingGemma requires Ollama v0.11.10"):
        controller.create_session(
            title="Outdated server", profile_id="balanced",
            backend="ollama", model_id="qwen3:8b",
        )
    assert controller.list_sessions() == []


@pytest.mark.parametrize("reported", ["development", "v0.10.8"])
def test_invalid_or_old_ollama_version_is_not_accepted(monkeypatch, reported):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["embeddinggemma:latest"],
    )
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        lambda: reported,
    )
    with pytest.raises(ValueError, match="Update and restart Ollama"):
        WorkbenchController.validate_ollama_embedding_model("embeddinggemma")


def test_ollama_version_check_failure_is_actionable(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["embeddinggemma:latest"],
    )

    def unreachable():
        raise RuntimeError("version endpoint refused")

    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        unreachable,
    )
    controller = WorkbenchController(tmp_path / "workspace")
    with pytest.raises(ValueError, match="Could not verify the Ollama server version"):
        controller.create_session(
            title="Unknown server", profile_id="balanced",
            backend="ollama", model_id="qwen3:8b",
        )
    assert controller.list_sessions() == []


def test_other_embedding_models_do_not_require_embeddinggemma_version(monkeypatch):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["nomic-embed-text:latest"],
    )
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        lambda: pytest.fail("not required for other models"),
    )
    WorkbenchController.validate_ollama_embedding_model("nomic-embed-text")


@pytest.mark.parametrize("version", ["0.11.9", "v0.10.8", "development"])
def test_installed_embeddinggemma_requires_compatible_ollama_version(
    monkeypatch, tmp_path, version,
):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["embeddinggemma:latest", "qwen3:8b"],
    )
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        lambda: version,
    )
    controller = WorkbenchController(tmp_path / "workspace")
    with pytest.raises(ValueError, match="Update and restart Ollama"):
        controller.create_session(
            title="Outdated local server", profile_id="balanced",
            backend="ollama", model_id="qwen3:8b",
        )
    assert controller.list_sessions() == []


def test_ollama_version_check_failure_is_actionable(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["embeddinggemma:latest"],
    )

    def unavailable():
        raise RuntimeError("version endpoint refused")

    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        unavailable,
    )
    controller = WorkbenchController(tmp_path / "workspace")
    with pytest.raises(ValueError, match="Could not verify the Ollama server version"):
        controller.create_session(
            title="Unknown local version", profile_id="balanced",
            backend="ollama", model_id="qwen3:8b",
        )
    assert controller.list_sessions() == []


def test_other_embedding_models_skip_embeddinggemma_version_check(monkeypatch):
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.list_ollama_models",
        lambda: ["nomic-embed-text:latest"],
    )
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.ollama_version",
        lambda: pytest.fail("Unrelated model should not check EmbeddingGemma version"),
    )
    WorkbenchController.validate_ollama_embedding_model("nomic-embed-text")
