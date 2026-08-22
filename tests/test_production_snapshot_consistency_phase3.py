from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from shadowseed.application.workspace import WorkspaceService
from shadowseed.storage.sqlite import WorkspaceStorageError
from shadowseed.workbench.controller import WorkbenchController


def test_mutable_authority_snapshot_cannot_silently_diverge_from_ledger(
    tmp_path: Path,
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Authority snapshot",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What should this plan verify?")
    seed_id = result["session"]["seeds"][0]["id"]

    with sqlite3.connect(controller.workspace.paths.database) as connection:
        raw = connection.execute(
            "SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        assert raw is not None
        state = json.loads(raw[0])
        seed = next(item for item in state["manager"]["seeds"] if item["id"] == seed_id)
        seed["weight"] = 999.0
        connection.execute(
            "UPDATE sessions SET state_json = ? WHERE session_id = ?",
            (json.dumps(state, sort_keys=True), session_id),
        )

    with pytest.raises(WorkspaceStorageError, match="snapshot diverges"):
        controller.workspace.repository.verify_production_integrity()


def test_production_checkpoint_is_content_minimized_and_verified(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    workspace.initialize()

    report = workspace.repository.verify_production_integrity()
    assert report["authority_snapshot_verified"] is True

    with sqlite3.connect(workspace.paths.database) as connection:
        row = connection.execute(
            "SELECT payload_json FROM production_ledger "
            "WHERE event_type='production.authority_checkpoint'"
        ).fetchone()
    assert row is not None
    payload = json.loads(row[0])
    assert payload == {"authority_snapshot": []}
