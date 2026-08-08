"""Transactional SQLite repository for local Shadowseed tester workspaces."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from uuid import uuid4

from shadowseed.application.models import SessionSummary, TesterFeedback
from shadowseed.storage.schema import DDL, SCHEMA_VERSION


class WorkspaceStorageError(RuntimeError):
    """Raised when a workspace cannot be opened, migrated, or restored safely."""


_SECRET_FRAGMENTS = ("api_key", "apikey", "access_token", "secret", "password")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _reject_secrets(value: Any, path: str = "config") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in _SECRET_FRAGMENTS) and item not in (None, ""):
                raise WorkspaceStorageError(
                    f"refusing to persist a secret-like field at {path}.{key}; "
                    "use environment variables or an OS keyring"
                )
            _reject_secrets(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _reject_secrets(item, f"{path}[{index}]")


class SQLiteWorkspaceRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            connection = sqlite3.connect(self.database_path, timeout=10.0)
        except sqlite3.Error as exc:
            raise WorkspaceStorageError(f"cannot open workspace database: {exc}") from exc
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self._connect() as connection:
            try:
                with connection:
                    for statement in DDL:
                        connection.execute(statement)
                    current = connection.execute(
                        "SELECT value FROM workspace_meta WHERE key = 'schema_version'"
                    ).fetchone()
                    if current is None:
                        connection.execute(
                            "INSERT INTO workspace_meta(key, value) VALUES('schema_version', ?)",
                            (str(SCHEMA_VERSION),),
                        )
                    elif int(current["value"]) > SCHEMA_VERSION:
                        raise WorkspaceStorageError(
                            "workspace schema is newer than this Shadowseed installation"
                        )
                    elif int(current["value"]) < SCHEMA_VERSION:
                        self._migrate(connection, int(current["value"]))
            except sqlite3.DatabaseError as exc:
                raise WorkspaceStorageError(f"workspace database is invalid: {exc}") from exc

    def _migrate(self, connection: sqlite3.Connection, from_version: int) -> None:
        if from_version != SCHEMA_VERSION:
            raise WorkspaceStorageError(
                f"no migration path from workspace schema {from_version} to {SCHEMA_VERSION}"
            )

    def schema_version(self) -> int:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value FROM workspace_meta WHERE key = 'schema_version'"
            ).fetchone()
            if row is None:
                raise WorkspaceStorageError("workspace schema version is missing")
            return int(row["value"])

    def create_session(
        self,
        *,
        session_id: str,
        title: str,
        profile_id: str,
        config: dict[str, Any],
        state: dict[str, Any],
        created_at: str,
    ) -> None:
        self.initialize()
        _reject_secrets(config)
        with self._connect() as connection:
            try:
                with connection:
                    connection.execute(
                        """
                        INSERT INTO sessions(
                            session_id, title, profile_id, backend, model_id,
                            config_json, state_json, created_at, updated_at
                        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            session_id,
                            title,
                            profile_id,
                            str(config.get("backend", "fixture")),
                            config.get("model_id"),
                            _json(config),
                            _json(state),
                            created_at,
                            created_at,
                        ),
                    )
                    self._sync_normalized(connection, session_id, state)
            except sqlite3.IntegrityError as exc:
                raise WorkspaceStorageError(f"session {session_id!r} already exists") from exc

    def save_session(self, session_id: str, state: dict[str, Any], *, updated_at: str) -> None:
        self.initialize()
        with self._connect() as connection:
            try:
                with connection:
                    cursor = connection.execute(
                        "UPDATE sessions SET state_json = ?, updated_at = ? WHERE session_id = ?",
                        (_json(state), updated_at, session_id),
                    )
                    if cursor.rowcount != 1:
                        raise KeyError(f"unknown session id: {session_id}")
                    self._sync_normalized(connection, session_id, state)
            except sqlite3.DatabaseError as exc:
                if isinstance(exc, sqlite3.IntegrityError):
                    raise WorkspaceStorageError(f"cannot save session: {exc}") from exc
                raise

    def load_session(self, session_id: str) -> dict[str, Any]:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown session id: {session_id}")
        try:
            state = json.loads(row["state_json"])
            config = json.loads(row["config_json"])
        except json.JSONDecodeError as exc:
            raise WorkspaceStorageError(f"session {session_id!r} contains invalid JSON") from exc
        return {
            "session_id": row["session_id"],
            "title": row["title"],
            "profile_id": row["profile_id"],
            "backend": row["backend"],
            "model_id": row["model_id"],
            "config": config,
            "state": state,
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    def list_sessions(self) -> list[SessionSummary]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC, created_at DESC"
            ).fetchall()
        summaries: list[SessionSummary] = []
        for row in rows:
            state = json.loads(row["state_json"])
            summaries.append(
                SessionSummary(
                    session_id=row["session_id"],
                    title=row["title"],
                    profile_id=row["profile_id"],
                    backend=row["backend"],
                    model_id=row["model_id"],
                    turn_count=int(state.get("turn", len(state.get("turn_reports", [])))),
                    seed_count=len(state.get("manager", {}).get("seeds", [])),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return summaries

    def delete_session(self, session_id: str) -> None:
        self.initialize()
        with self._connect() as connection, connection:
            cursor = connection.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
            if cursor.rowcount != 1:
                raise KeyError(f"unknown session id: {session_id}")

    def add_feedback(self, feedback: TesterFeedback) -> TesterFeedback:
        self.initialize()
        feedback_id = feedback.feedback_id or f"feedback::{uuid4()}"
        created_at = feedback.created_at or datetime.now().isoformat()
        stored = TesterFeedback(
            session_id=feedback.session_id,
            turn_index=feedback.turn_index,
            overall=feedback.overall,
            seed_effect=feedback.seed_effect,
            note=feedback.note,
            action=feedback.action,
            seed_id=feedback.seed_id,
            created_at=created_at,
            feedback_id=feedback_id,
        )
        with self._connect() as connection, connection:
            connection.execute(
                """
                INSERT INTO tester_feedback(
                    feedback_id, session_id, turn_index, seed_id, overall,
                    seed_effect, note, action, created_at
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    feedback_id,
                    stored.session_id,
                    stored.turn_index,
                    stored.seed_id,
                    stored.overall,
                    stored.seed_effect,
                    stored.note,
                    stored.action,
                    created_at,
                ),
            )
        return stored

    def list_feedback(self, session_id: str) -> list[TesterFeedback]:
        self.initialize()
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM tester_feedback
                WHERE session_id = ? ORDER BY turn_index, created_at
                """,
                (session_id,),
            ).fetchall()
        return [
            TesterFeedback(
                session_id=row["session_id"],
                turn_index=row["turn_index"],
                overall=row["overall"],
                seed_effect=row["seed_effect"],
                note=row["note"],
                action=row["action"],
                seed_id=row["seed_id"],
                created_at=row["created_at"],
                feedback_id=row["feedback_id"],
            )
            for row in rows
        ]

    def counts(self) -> dict[str, int]:
        self.initialize()
        with self._connect() as connection:
            return {
                table: int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in (
                    "sessions",
                    "turns",
                    "seeds",
                    "audit_events",
                    "tester_feedback",
                )
            }

    def backup_to(self, destination: str | Path) -> Path:
        self.initialize()
        target = Path(destination).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        if temporary.exists():
            temporary.unlink()
        source = self._connect()
        destination_db = sqlite3.connect(temporary)
        try:
            source.backup(destination_db)
            destination_db.commit()
        finally:
            destination_db.close()
            source.close()
        os.replace(temporary, target)
        return target

    def restore_from(self, source: str | Path) -> None:
        source_path = Path(source).expanduser().resolve()
        if not source_path.is_file():
            raise WorkspaceStorageError(f"backup does not exist: {source_path}")
        try:
            with sqlite3.connect(f"file:{source_path}?mode=ro", uri=True) as connection:
                row = connection.execute(
                    "SELECT value FROM workspace_meta WHERE key = 'schema_version'"
                ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise WorkspaceStorageError(f"backup is not a valid workspace database: {exc}") from exc
        if row is None or int(row[0]) > SCHEMA_VERSION:
            raise WorkspaceStorageError("backup schema is missing or unsupported")
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.database_path.with_suffix(".restore.tmp")
        shutil.copy2(source_path, temporary)
        os.replace(temporary, self.database_path)
        self.initialize()

    def _sync_normalized(
        self, connection: sqlite3.Connection, session_id: str, state: dict[str, Any]
    ) -> None:
        connection.execute("DELETE FROM turns WHERE session_id = ?", (session_id,))
        connection.execute("DELETE FROM seeds WHERE session_id = ?", (session_id,))
        connection.execute("DELETE FROM audit_events WHERE session_id = ?", (session_id,))

        for report in state.get("turn_reports", []):
            turn_index = int(report.get("turn", 0))
            connection.execute(
                """
                INSERT INTO turns(
                    session_id, turn_index, question, answer, baseline_answer,
                    ssl_answer, report_json
                ) VALUES(?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    turn_index,
                    str(report.get("question", "")),
                    str(report.get("answer", "")),
                    str(report.get("baseline_answer", "")),
                    str(report.get("ssl_answer", "")),
                    _json(report),
                ),
            )

        manager = state.get("manager", {})
        for seed in manager.get("seeds", []):
            connection.execute(
                "INSERT INTO seeds(session_id, seed_id, snapshot_json) VALUES(?, ?, ?)",
                (session_id, str(seed["id"]), _json(seed)),
            )

        ledgers = (
            ("seed_event", manager.get("event_log", []), "event_id"),
            ("validation", manager.get("validation_log", []), "event_id"),
            ("gate", manager.get("gate_events", []), "event_id"),
            ("contradiction", manager.get("contradiction_records", []), "contradiction_id"),
            ("probe_feedback", manager.get("feedback_log", []), "event_id"),
            ("influence", state.get("influence_records", []), "event_id"),
        )
        for event_type, items, key_name in ledgers:
            for sequence, item in enumerate(items):
                event_key = str(item.get(key_name) or f"{event_type}::{sequence:06d}")
                connection.execute(
                    """
                    INSERT INTO audit_events(
                        session_id, event_type, event_key, sequence_no, payload_json
                    ) VALUES(?, ?, ?, ?, ?)
                    """,
                    (session_id, event_type, event_key, sequence, _json(item)),
                )
