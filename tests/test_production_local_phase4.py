from __future__ import annotations

import os
import shutil
from pathlib import Path

import pytest

from shadowseed.application.limits import (
    MAX_BACKUP_BYTES,
    MAX_EVIDENCE_NOTE_CHARS,
    MAX_MESSAGE_CHARS,
    ResourceLimitError,
    validate_backup_file,
    validate_evidence,
    validate_message,
)
from shadowseed.application.workspace import WorkspaceEraseError, WorkspaceService
from shadowseed.workbench.controller import WorkbenchController


def _live_seed(controller: WorkbenchController) -> tuple[str, str]:
    session_id = controller.create_session(
        title="Phase 4 limits",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What should be checked?")
    return session_id, result["session"]["seeds"][0]["id"]


def test_message_limit_rejects_before_product_use() -> None:
    assert validate_message("hello") == "hello"
    with pytest.raises(ResourceLimitError, match="message exceeds"):
        validate_message("x" * (MAX_MESSAGE_CHARS + 1))


def test_evidence_note_limit_is_explicit() -> None:
    source, note = validate_evidence("reviewer:source", "checked")
    assert source == "reviewer:source"
    assert note == "checked"
    with pytest.raises(ResourceLimitError, match="evidence note exceeds"):
        validate_evidence("reviewer:source", "x" * (MAX_EVIDENCE_NOTE_CHARS + 1))


def test_oversized_message_does_not_mutate_session_or_ledger(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, _ = _live_seed(controller)
    before_state = controller.sessions.load(session_id)["state"]
    before_integrity = controller.workspace.repository.verify_production_integrity()

    with pytest.raises(ResourceLimitError, match="message exceeds"):
        controller.send_turn(session_id, "x" * (MAX_MESSAGE_CHARS + 1))

    after_state = controller.sessions.load(session_id)["state"]
    after_integrity = controller.workspace.repository.verify_production_integrity()
    assert after_state == before_state
    assert after_integrity["sequence_no"] == before_integrity["sequence_no"]
    assert after_integrity["head_hash"] == before_integrity["head_hash"]


def test_oversized_evidence_does_not_mutate_authority_or_ledger(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    before_state = controller.sessions.load(session_id)["state"]
    before_integrity = controller.workspace.repository.verify_production_integrity()

    with pytest.raises(ResourceLimitError, match="evidence note exceeds"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="reviewer:source",
            note="x" * (MAX_EVIDENCE_NOTE_CHARS + 1),
            operator_verified=True,
        )

    after_state = controller.sessions.load(session_id)["state"]
    after_integrity = controller.workspace.repository.verify_production_integrity()
    assert after_state == before_state
    assert after_integrity["sequence_no"] == before_integrity["sequence_no"]
    assert after_integrity["head_hash"] == before_integrity["head_hash"]


def test_oversized_backup_is_rejected_without_creating_workspace(tmp_path: Path) -> None:
    source = tmp_path / "oversized.db"
    with source.open("wb") as handle:
        handle.truncate(MAX_BACKUP_BYTES + 1)

    target = tmp_path / "target"
    service = WorkspaceService(target)
    with pytest.raises(ResourceLimitError, match="backup exceeds"):
        service.restore(source)

    assert not target.exists()


def test_backup_validator_accepts_normal_file(tmp_path: Path) -> None:
    source = tmp_path / "backup.db"
    source.write_bytes(b"sqlite-ish")
    assert validate_backup_file(source) == source.resolve()


@pytest.mark.skipif(os.name == "nt", reason="POSIX chmod semantics are not portable to Windows")
def test_workspace_uses_restrictive_posix_permissions(tmp_path: Path) -> None:
    service = WorkspaceService(tmp_path / "workspace")
    paths = service.initialize()

    assert paths.root.stat().st_mode & 0o777 == 0o700
    assert paths.exports.stat().st_mode & 0o777 == 0o700
    assert paths.logs.stat().st_mode & 0o777 == 0o700
    assert paths.config.stat().st_mode & 0o777 == 0o600
    assert paths.identity.stat().st_mode & 0o777 == 0o600
    assert paths.database.stat().st_mode & 0o777 == 0o600


def test_full_workspace_erase_removes_live_state_but_not_external_backup(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    service = WorkspaceService(root)
    service.initialize()
    workspace_id = service.workspace_id
    integrity_dir = service._integrity_dir(workspace_id)
    backup = service.backup(tmp_path / "independent-backup.db")

    assert root.exists()
    assert integrity_dir.exists()
    assert backup.exists()

    result = service.delete()

    assert result["deleted"] is True
    assert result["components"]["workspace"] == "deleted"
    assert result["components"]["integrity_material"] == "deleted"
    assert result["independent_backups_and_exports_untouched"] is True
    assert not root.exists()
    assert not integrity_dir.exists()
    assert backup.exists()


def test_full_workspace_erase_reports_incomplete_integrity_cleanup(
    tmp_path: Path,
    monkeypatch,
) -> None:
    root = tmp_path / "workspace"
    service = WorkspaceService(root)
    service.initialize()
    integrity_dir = service._integrity_dir(service.workspace_id)
    original_rmtree = shutil.rmtree

    def _selective_rmtree(path, *args, **kwargs):
        candidate = Path(path).resolve()
        if candidate == integrity_dir.resolve():
            raise PermissionError("simulated protected-material cleanup failure")
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "rmtree", _selective_rmtree)

    with pytest.raises(WorkspaceEraseError, match="integrity_material") as caught:
        service.delete()

    assert caught.value.failed_components == {"integrity_material": "PermissionError"}
    assert caught.value.component_status["workspace"] == "deleted"
    assert caught.value.component_status["integrity_material"] == "remaining"
    assert not root.exists()
    assert integrity_dir.exists()
