from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest

from shadowseed.storage.integrity import event_digest
from shadowseed.storage.production import ProductionSQLiteWorkspaceRepository
from shadowseed.storage.sqlite import WorkspaceStorageError


def _interrupted_checkpoint_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> dict[str, Any]:
    database = tmp_path / "workspace.db"
    integrity_dir = tmp_path / "integrity"
    workspace_id = "workspace::checkpoint-crash"
    bootstrap_actor_id = "local-owner::checkpoint-crash"
    marker = integrity_dir / "bootstrap.pending"
    anchor = integrity_dir / "anchor.json"

    repository = ProductionSQLiteWorkspaceRepository(database)
    original_advance = ProductionSQLiteWorkspaceRepository._advance_anchor
    interrupted = False

    def interrupt_first_checkpoint_anchor(
        self: ProductionSQLiteWorkspaceRepository,
    ) -> None:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            assert marker.is_file()
            marker_payload = json.loads(marker.read_text(encoding="utf-8"))
            assert marker_payload["checkpoint_plan"]["event_type"] == (
                "production.authority_checkpoint"
            )
            raise RuntimeError("synthetic checkpoint-before-anchor interruption")
        original_advance(self)

    monkeypatch.setattr(
        ProductionSQLiteWorkspaceRepository,
        "_advance_anchor",
        interrupt_first_checkpoint_anchor,
    )

    with pytest.raises(RuntimeError, match="checkpoint-before-anchor interruption"):
        repository.bind_production(
            workspace_id=workspace_id,
            integrity_dir=integrity_dir,
            bootstrap_actor_id=bootstrap_actor_id,
        )

    assert marker.is_file()
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    checkpoint_plan = marker_payload["checkpoint_plan"]
    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
    assert [row["event_type"] for row in rows] == [
        "production.bootstrap",
        "production.authority_checkpoint",
    ]
    assert dict(rows[1]) == checkpoint_plan
    assert rows[0]["event_hash"] == marker_payload["expected_genesis_hash"]
    assert rows[1]["event_hash"] == checkpoint_plan["event_hash"]

    return {
        "database": database,
        "integrity_dir": integrity_dir,
        "workspace_id": workspace_id,
        "bootstrap_actor_id": bootstrap_actor_id,
        "marker": marker,
        "anchor": anchor,
        "anchor_before": anchor.read_bytes(),
        "marker_payload": marker_payload,
    }


def test_checkpoint_crash_keeps_bootstrap_commitment_until_safe_reseal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _interrupted_checkpoint_state(tmp_path, monkeypatch)
    database = state["database"]
    marker = state["marker"]
    anchor = state["anchor"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            """
            INSERT INTO sessions(
                session_id, title, profile_id, backend, model_id,
                config_json, state_json, created_at, updated_at
            ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "session::forged-checkpoint-window",
                "Forged",
                "demo",
                "fixture",
                None,
                "{}",
                json.dumps({"turn": 0, "manager": {"seeds": []}}),
                "2026-08-26T00:00:00",
                "2026-08-26T00:00:00",
            ),
        )
        connection.commit()

    attacked = ProductionSQLiteWorkspaceRepository(database)
    with pytest.raises(WorkspaceStorageError, match="authority baseline changed"):
        attacked.bind_production(
            workspace_id=state["workspace_id"],
            integrity_dir=state["integrity_dir"],
            bootstrap_actor_id=state["bootstrap_actor_id"],
        )

    assert marker.is_file()
    assert anchor.read_bytes() == state["anchor_before"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            ("session::forged-checkpoint-window",),
        )
        connection.commit()

    reopened = ProductionSQLiteWorkspaceRepository(database)
    report = reopened.bind_production(
        workspace_id=state["workspace_id"],
        integrity_dir=state["integrity_dir"],
        bootstrap_actor_id=state["bootstrap_actor_id"],
    )

    assert report["authority_snapshot_verified"] is True
    assert report["sequence_no"] == 2
    assert report["anchor_sequence_no"] == 2
    assert not marker.exists()


def test_checkpoint_crash_rejects_rewritten_complete_checkpoint_row(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _interrupted_checkpoint_state(tmp_path, monkeypatch)
    database = state["database"]
    marker = state["marker"]
    anchor = state["anchor"]

    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        checkpoint = dict(
            connection.execute(
                "SELECT * FROM production_ledger WHERE sequence_no = 2"
            ).fetchone()
        )
        checkpoint["event_id"] = "ledger::forged-checkpoint-event"
        digest_input = {
            key: value for key, value in checkpoint.items() if key != "event_hash"
        }
        checkpoint["event_hash"] = event_digest(digest_input)
        assert checkpoint["event_hash"] != state["marker_payload"]["checkpoint_plan"][
            "event_hash"
        ]
        connection.execute(
            "UPDATE production_ledger SET event_id = ?, event_hash = ? "
            "WHERE sequence_no = 2",
            (checkpoint["event_id"], checkpoint["event_hash"]),
        )
        connection.commit()

    attacked = ProductionSQLiteWorkspaceRepository(database)
    with pytest.raises(
        WorkspaceStorageError,
        match="does not match protected bootstrap commitment",
    ):
        attacked.bind_production(
            workspace_id=state["workspace_id"],
            integrity_dir=state["integrity_dir"],
            bootstrap_actor_id=state["bootstrap_actor_id"],
        )

    assert marker.is_file()
    assert anchor.read_bytes() == state["anchor_before"]


def test_pending_bootstrap_rejects_live_audit_epoch_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _interrupted_checkpoint_state(tmp_path, monkeypatch)
    database = state["database"]
    marker = state["marker"]
    anchor = state["anchor"]

    with sqlite3.connect(database) as connection:
        connection.execute(
            "UPDATE workspace_meta SET value = ? WHERE key = 'audit_epoch'",
            ("epoch::forged-during-bootstrap",),
        )
        connection.commit()

    attacked = ProductionSQLiteWorkspaceRepository(database)
    with pytest.raises(WorkspaceStorageError, match="audit epoch changed"):
        attacked.bind_production(
            workspace_id=state["workspace_id"],
            integrity_dir=state["integrity_dir"],
            bootstrap_actor_id=state["bootstrap_actor_id"],
        )

    assert marker.is_file()
    assert anchor.read_bytes() == state["anchor_before"]
