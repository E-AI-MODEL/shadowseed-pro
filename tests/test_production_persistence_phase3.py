from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from shadowseed.storage.schema import SCHEMA_VERSION
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError


def _create_v1_workspace(path: Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.executescript(
            """
            CREATE TABLE workspace_meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            INSERT INTO workspace_meta(key, value) VALUES('schema_version', '1');
            CREATE TABLE sessions (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                profile_id TEXT NOT NULL,
                backend TEXT NOT NULL,
                model_id TEXT,
                config_json TEXT NOT NULL,
                state_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE turns (
                session_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                baseline_answer TEXT NOT NULL,
                ssl_answer TEXT NOT NULL,
                report_json TEXT NOT NULL,
                PRIMARY KEY (session_id, turn_index)
            );
            CREATE TABLE seeds (
                session_id TEXT NOT NULL,
                seed_id TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                PRIMARY KEY (session_id, seed_id)
            );
            CREATE TABLE audit_events (
                session_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_key TEXT NOT NULL,
                sequence_no INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (session_id, event_type, event_key)
            );
            CREATE TABLE tester_feedback (
                feedback_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                seed_id TEXT,
                overall TEXT NOT NULL,
                seed_effect TEXT NOT NULL,
                note TEXT NOT NULL,
                action TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX idx_sessions_updated ON sessions(updated_at DESC);
            CREATE INDEX idx_feedback_session ON tester_feedback(session_id, turn_index);
            INSERT INTO sessions(
                session_id, title, profile_id, backend, model_id,
                config_json, state_json, created_at, updated_at
            ) VALUES(
                'session::legacy', 'Legacy', 'demo', 'fixture', NULL,
                '{}', '{"turn":0,"manager":{"seeds":[]}}',
                '2026-01-01T00:00:00', '2026-01-01T00:00:00'
            );
            """
        )


def test_new_workspace_uses_current_schema_and_production_ledger(tmp_path: Path) -> None:
    database = tmp_path / "workspace.db"
    repository = SQLiteWorkspaceRepository(database)

    repository.initialize()

    assert repository.schema_version() == SCHEMA_VERSION == 2
    with sqlite3.connect(database) as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='production_ledger'"
        ).fetchone()
    assert table == ("production_ledger",)


def test_v1_workspace_migrates_backup_first_and_preserves_state(tmp_path: Path) -> None:
    database = tmp_path / "workspace.db"
    _create_v1_workspace(database)
    repository = SQLiteWorkspaceRepository(database)

    repository.initialize()

    backup = tmp_path / "workspace.db.pre-migration-v1-to-v2.bak"
    assert backup.is_file()
    assert repository.schema_version() == 2
    assert repository.load_session("session::legacy")["title"] == "Legacy"

    with sqlite3.connect(f"file:{backup}?mode=ro", uri=True) as connection:
        version = connection.execute(
            "SELECT value FROM workspace_meta WHERE key='schema_version'"
        ).fetchone()
        ledger = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='production_ledger'"
        ).fetchone()
    assert version == ("1",)
    assert ledger is None

    repository.initialize()
    assert list(tmp_path.glob("workspace.db.pre-migration-v1-to-v2.bak")) == [backup]


def test_newer_workspace_schema_fails_without_mutation(tmp_path: Path) -> None:
    database = tmp_path / "workspace.db"
    with sqlite3.connect(database) as connection:
        connection.execute(
            "CREATE TABLE workspace_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
        )
        connection.execute(
            "INSERT INTO workspace_meta(key, value) VALUES('schema_version', '99')"
        )

    before = database.read_bytes()
    repository = SQLiteWorkspaceRepository(database)

    with pytest.raises(WorkspaceStorageError, match="newer than this Shadowseed installation"):
        repository.initialize()

    assert database.read_bytes() == before
