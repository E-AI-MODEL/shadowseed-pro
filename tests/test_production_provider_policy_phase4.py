from __future__ import annotations

from pathlib import Path

import pytest

from shadowseed.application.provider_policy import (
    ProviderPolicyError,
    production_local_ollama_host,
)
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController


def test_production_local_ollama_accepts_loopback(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    assert production_local_ollama_host() == "http://127.0.0.1:11434"


def test_production_local_ollama_rejects_remote_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://192.0.2.25:11434")
    with pytest.raises(ProviderPolicyError, match="loopback endpoint"):
        production_local_ollama_host()


def test_production_controller_rejects_remote_ollama_before_session_creation(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://192.0.2.25:11434")
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    before = controller.workspace.repository.counts()["sessions"]

    with pytest.raises(ProviderPolicyError, match="loopback endpoint"):
        controller.create_session(
            title="remote target",
            profile_id="demo",
            backend="ollama",
            model_id="example",
            runtime_mode="live",
            embedding_backend="sentence-transformers",
        )

    assert controller.workspace.repository.counts()["sessions"] == before


def test_production_operational_log_never_contains_prompt_or_evidence_text(tmp_path: Path) -> None:
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    sentinel_prompt = "PRIVATE-PROMPT-SENTINEL"
    session_id = controller.create_session(
        title="logging",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, sentinel_prompt)
    seed_id = result["session"]["seeds"][0]["id"]
    controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="PRIVATE-SOURCE-SENTINEL",
        note="PRIVATE-NOTE-SENTINEL",
        operator_verified=True,
    )

    text = controller.operations.path.read_text(encoding="utf-8")
    assert sentinel_prompt not in text
    assert "PRIVATE-SOURCE-SENTINEL" not in text
    assert "PRIVATE-NOTE-SENTINEL" not in text
    assert '"event":"session.turn"' in text
    assert '"event":"evidence.verify"' in text
