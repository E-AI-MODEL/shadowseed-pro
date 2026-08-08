from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from shadowseed.application.health import run_doctor
from shadowseed.application.models import SessionConfig, TesterFeedback as FeedbackRecord
from shadowseed.application.profiles import get_profile, list_profiles
from shadowseed.application.sessions import SessionService
from shadowseed.application.workspace import WorkspaceService
from shadowseed.chat import ShadowChatSession
from shadowseed.cli import build_parser
from shadowseed.cli_dispatch import execute_command
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError


def test_profiles_are_small_named_surfacing_configurations() -> None:
    assert [profile.profile_id for profile in list_profiles()] == [
        "demo",
        "balanced",
        "conservative",
        "exploratory",
    ]
    conservative = get_profile("conservative").apply(
        SessionConfig(backend="ollama", model_id="local-model")
    )
    assert conservative.backend == "ollama"
    assert conservative.model_id == "local-model"
    assert conservative.surface_top_k == 1
    assert conservative.surface_threshold > get_profile("balanced").apply().surface_threshold


def test_shadow_chat_state_roundtrip_preserves_audit_and_continues() -> None:
    session = ShadowChatSession(backend="fixture")
    first = session.turn("What might be missing from this plan?")
    restored = ShadowChatSession.from_state(session.to_state())

    assert restored.transcript() == session.transcript()
    assert restored.manager.to_dict() == session.manager.to_dict()
    assert restored.audit() == session.audit()

    second = restored.turn("What should be checked next?")
    assert second["turn"] == first["turn"] + 1
    assert restored.to_state()["turn"] == 2


def test_sqlite_workspace_persists_session_normalized_rows_and_feedback(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    workspace.initialize()
    service = SessionService(workspace.repository)
    session_id = service.create_session(title="Fixture test", profile_id="demo")
    report = service.run_turn(session_id, "Review this proposal")

    reopened = SessionService(SQLiteWorkspaceRepository(workspace.paths.database))
    stored = reopened.load(session_id)
    assert stored["state"]["turn"] == 1
    assert stored["state"]["turn_reports"][0]["answer"] == report["answer"]
    assert reopened.list_sessions()[0].turn_count == 1

    feedback = reopened.record_feedback(
        FeedbackRecord(
            session_id=session_id,
            turn_index=0,
            overall="helpful",
            seed_effect="no_visible_effect",
            note="Clear baseline response.",
        )
    )
    assert feedback.feedback_id is not None
    assert reopened.list_feedback(session_id) == [feedback]

    counts = workspace.repository.counts()
    assert counts["sessions"] == 1
    assert counts["turns"] == 1
    assert counts["tester_feedback"] == 1


def test_feedback_is_record_only_in_foundation_release(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path)
    workspace.initialize()
    service = SessionService(workspace.repository)
    session_id = service.create_session(profile_id="demo")

    with pytest.raises(ValueError, match="record_only"):
        service.record_feedback(
            FeedbackRecord(
                session_id=session_id,
                turn_index=0,
                action="positive_signal",
            )
        )


def test_workspace_backup_restore_and_secret_rejection(tmp_path: Path) -> None:
    first = WorkspaceService(tmp_path / "first")
    first.initialize()
    service = SessionService(first.repository)
    session_id = service.create_session(profile_id="demo")
    service.run_turn(session_id, "Create one persisted turn")
    backup = first.backup(tmp_path / "backup.db")

    second = WorkspaceService(tmp_path / "second")
    second.restore(backup)
    assert second.repository.list_sessions()[0].session_id == session_id

    with pytest.raises(WorkspaceStorageError, match="secret-like"):
        second.repository.create_session(
            session_id="session::secret",
            title="bad",
            profile_id="demo",
            config={"backend": "openai", "api_key": "do-not-store"},
            state={"turn": 0, "manager": {"seeds": []}},
            created_at="2026-08-08T00:00:00",
        )


def test_doctor_and_workspace_cli_are_available(tmp_path: Path) -> None:
    report = run_doctor(tmp_path / "doctor")
    checks = {check.name: check for check in report.checks}
    assert checks["python"].ok
    assert checks["fixture_backend"].ok
    assert checks["workspace"].ok

    parser = build_parser()
    args = parser.parse_args(["workspace", "--workspace", str(tmp_path / "cli"), "info"])
    payload = json.loads(execute_command(args))
    assert payload["schema_version"] == 1

    doctor_args = Namespace(command="doctor", workspace=str(tmp_path / "cli"), json=True)
    doctor_payload = json.loads(execute_command(doctor_args))
    assert "checks" in doctor_payload
