from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from shadowseed.application.workspace import WorkspaceService
from shadowseed.storage import recovery
from shadowseed.storage.sqlite import WorkspaceStorageError
from shadowseed.workbench.controller import WorkbenchController


def _live_seed(controller: WorkbenchController) -> tuple[str, str]:
    session_id = controller.create_session(
        title="Phase 3 recovery",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What should be verified in this plan?")
    return session_id, result["session"]["seeds"][0]["id"]


def test_fresh_machine_import_preserves_workspace_identity_and_records_break(tmp_path: Path) -> None:
    source = WorkbenchController(tmp_path / "source")
    session_id, _ = _live_seed(source)
    source_workspace_id = source.workspace.workspace_id
    backup = source.workspace.backup(tmp_path / "portable.db")
    source_report = source.workspace.repository.verify_production_integrity()

    target = WorkspaceService(tmp_path / "target")
    result = target.restore(backup)

    assert target.workspace_id == source_workspace_id
    assert target.repository.load_session(session_id)["session_id"] == session_id
    assert result["continuity_break"] is True
    target_report = target.repository.verify_production_integrity()
    assert target_report["sequence_no"] == source_report["sequence_no"] + 1
    assert target_report["audit_epoch"] != source_report["audit_epoch"]

    connection = sqlite3.connect(target.paths.database)
    try:
        row = connection.execute(
            "SELECT event_type, payload_json FROM production_ledger ORDER BY sequence_no DESC LIMIT 1"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    assert row[0] == "workspace.import"
    assert '"continuity_break":true' in row[1]


def test_same_workspace_restore_keeps_live_ledger_and_creates_new_epoch(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, _ = _live_seed(controller)
    backup = controller.workspace.backup(tmp_path / "older.db")
    backup_turn = controller.sessions.load(session_id)["state"]["turn"]

    controller.send_turn(session_id, "A turn that should be rolled back intentionally")
    before = controller.workspace.repository.verify_production_integrity()
    assert controller.sessions.load(session_id)["state"]["turn"] > backup_turn

    result = controller.workspace.restore(backup)

    after = controller.workspace.repository.verify_production_integrity()
    assert controller.sessions.load(session_id)["state"]["turn"] == backup_turn
    assert after["sequence_no"] == before["sequence_no"] + 1
    assert after["audit_epoch"] != before["audit_epoch"]
    assert result["ledger_sequence_no"] == after["sequence_no"]

    connection = sqlite3.connect(controller.workspace.paths.database)
    try:
        row = connection.execute(
            "SELECT event_type, payload_json FROM production_ledger ORDER BY sequence_no DESC LIMIT 1"
        ).fetchone()
    finally:
        connection.close()
    assert row is not None
    assert row[0] == "workspace.restore"
    assert before["head_hash"] in row[1]


def test_restore_stage_validation_failure_never_replaces_live_database(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, _ = _live_seed(controller)
    backup = controller.workspace.backup(tmp_path / "older.db")
    controller.send_turn(session_id, "This newer turn must survive failed restore validation")
    state_before = controller.sessions.load(session_id)["state"]
    integrity_before = controller.workspace.repository.verify_production_integrity()

    def reject_stage(*args, **kwargs):
        raise WorkspaceStorageError("synthetic staged snapshot mismatch")

    monkeypatch.setattr(recovery, "_verify_and_seal_stage", reject_stage)
    with pytest.raises(WorkspaceStorageError, match="staged snapshot mismatch"):
        controller.workspace.restore(backup)

    assert controller.sessions.load(session_id)["state"] == state_before
    integrity_after = controller.workspace.repository.verify_production_integrity()
    assert integrity_after["head_hash"] == integrity_before["head_hash"]
    assert integrity_after["sequence_no"] == integrity_before["sequence_no"]


def test_tampered_backup_snapshot_is_rejected_before_import(tmp_path: Path) -> None:
    source = WorkbenchController(tmp_path / "source")
    session_id, _ = _live_seed(source)
    backup = source.workspace.backup(tmp_path / "tampered.db")

    connection = sqlite3.connect(backup)
    try:
        connection.execute(
            "UPDATE sessions SET state_json = '{}' WHERE session_id = ?",
            (session_id,),
        )
        connection.commit()
    finally:
        connection.close()

    target = WorkspaceService(tmp_path / "target")
    with pytest.raises(ValueError, match="mutable authority snapshot diverges"):
        target.restore(backup)
    assert not target.paths.database.exists()


def test_backup_does_not_export_private_integrity_material(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    workspace.initialize()
    backup = workspace.backup(tmp_path / "backup.db")

    assert backup.is_file()
    connection = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        meta = {
            row[0]
            for row in connection.execute("SELECT key FROM workspace_meta").fetchall()
        }
    finally:
        connection.close()
    assert "production_ledger" in tables
    assert "integrity_key" not in tables
    assert "anchor" not in meta
    assert "integrity_key" not in meta


def test_same_request_id_with_different_evidence_input_fails_without_mutation(
    tmp_path: Path,
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    actor = controller.workspace.local_actor_context(request_id="request::conflicting-replay")

    controller.sessions.submit_verified_evidence_authorized(
        session_id,
        seed_id,
        source_ref="reviewer:first",
        note="first note",
        actor=actor,
    )
    before = controller.sessions.load(session_id)["state"]

    with pytest.raises(WorkspaceStorageError, match="different authority-operation input"):
        controller.sessions.submit_verified_evidence_authorized(
            session_id,
            seed_id,
            source_ref="reviewer:second",
            note="changed note",
            actor=actor,
        )

    after = controller.sessions.load(session_id)["state"]
    assert after == before
    connection = sqlite3.connect(controller.workspace.paths.database)
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM production_ledger WHERE request_id = ?",
            (actor.request_id,),
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1
