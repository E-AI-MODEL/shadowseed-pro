from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from shadowseed.storage.production import ProductionSQLiteWorkspaceRepository
from shadowseed.storage.sqlite import WorkspaceStorageError


def test_checkpoint_crash_keeps_bootstrap_commitment_until_safe_reseal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
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
    anchor_before = anchor.read_bytes()
    with sqlite3.connect(database) as connection:
        events = connection.execute(
            "SELECT event_type FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
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

    assert events == [
        ("production.bootstrap",),
        ("production.authority_checkpoint",),
    ]

    attacked = ProductionSQLiteWorkspaceRepository(database)
    with pytest.raises(WorkspaceStorageError, match="authority baseline changed"):
        attacked.bind_production(
            workspace_id=workspace_id,
            integrity_dir=integrity_dir,
            bootstrap_actor_id=bootstrap_actor_id,
        )

    assert marker.is_file()
    assert anchor.read_bytes() == anchor_before

    with sqlite3.connect(database) as connection:
        connection.execute(
            "DELETE FROM sessions WHERE session_id = ?",
            ("session::forged-checkpoint-window",),
        )
        connection.commit()

    reopened = ProductionSQLiteWorkspaceRepository(database)
    report = reopened.bind_production(
        workspace_id=workspace_id,
        integrity_dir=integrity_dir,
        bootstrap_actor_id=bootstrap_actor_id,
    )

    assert report["authority_snapshot_verified"] is True
    assert report["sequence_no"] == 2
    assert report["anchor_sequence_no"] == 2
    assert not marker.exists()
