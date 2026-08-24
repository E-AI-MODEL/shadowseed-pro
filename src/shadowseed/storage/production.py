"""Production-bound SQLite repository with snapshot-to-ledger consistency checks."""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any, Mapping, Sequence

from shadowseed.storage.integrity import authority_digest
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError


def authority_snapshot_from_connection(connection: sqlite3.Connection) -> dict[str, str]:
    """Return the content-minimized authority snapshot for persisted sessions."""

    rows = connection.execute(
        "SELECT session_id, state_json FROM sessions ORDER BY session_id"
    ).fetchall()
    current: dict[str, str] = {}
    for row in rows:
        try:
            state = json.loads(row["state_json"])
        except json.JSONDecodeError as exc:
            raise WorkspaceStorageError(
                f"session {row['session_id']!r} contains invalid JSON"
            ) from exc
        current[str(row["session_id"])] = authority_digest(state)
    return current


def authority_snapshot_payload(snapshot: Mapping[str, str]) -> list[dict[str, str]]:
    return [
        {"session_id": session_id, "authority_digest": digest}
        for session_id, digest in sorted(snapshot.items())
    ]


def authority_snapshot_from_payload(value: Any) -> dict[str, str]:
    if not isinstance(value, list):
        raise WorkspaceStorageError("ledger authority snapshot is malformed")
    snapshot: dict[str, str] = {}
    for item in value:
        if not isinstance(item, dict):
            raise WorkspaceStorageError("ledger authority snapshot is malformed")
        session_id = str(item.get("session_id") or "")
        digest = str(item.get("authority_digest") or "")
        if not session_id or len(digest) != 64:
            raise WorkspaceStorageError("ledger authority snapshot is malformed")
        snapshot[session_id] = digest
    return snapshot


def expected_authority_snapshot_from_ledger(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    expected: dict[str, str] = {}
    checkpoint_seen = False
    for row in rows:
        event_type = str(row["event_type"])
        try:
            payload = json.loads(str(row["payload_json"]))
        except json.JSONDecodeError as exc:
            raise WorkspaceStorageError("production ledger payload JSON is invalid") from exc

        if event_type in {
            "production.authority_checkpoint",
            "workspace.restore",
            "workspace.import",
        }:
            expected = authority_snapshot_from_payload(payload.get("authority_snapshot"))
            checkpoint_seen = True
            continue

        session_id = row["session_id"]
        if event_type == "session.delete" and session_id:
            expected.pop(str(session_id), None)
            continue
        if not session_id:
            continue

        digest: str | None = None
        if event_type in {"session.create", "runtime.session_commit"}:
            candidate = payload.get("authority_digest")
            if isinstance(candidate, str):
                digest = candidate
        elif event_type in {
            "evidence.verify",
            "contradiction.submit",
            "contradiction.resolve",
        }:
            runtime_commit = payload.get("runtime_commit")
            if isinstance(runtime_commit, dict):
                candidate = runtime_commit.get("authority_digest")
                if isinstance(candidate, str):
                    digest = candidate
        if digest is not None:
            if len(digest) != 64:
                raise WorkspaceStorageError("ledger authority digest is malformed")
            expected[str(session_id)] = digest

    if not checkpoint_seen:
        raise WorkspaceStorageError("production authority checkpoint is missing")
    return expected


def verify_authority_snapshot_connection(connection: sqlite3.Connection) -> None:
    """Fail closed when mutable authority no longer matches the append-only ledger."""

    current = authority_snapshot_from_connection(connection)
    rows = [
        dict(row)
        for row in connection.execute(
            "SELECT session_id, event_type, payload_json "
            "FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
    ]
    expected = expected_authority_snapshot_from_ledger(rows)
    if current != expected:
        raise WorkspaceStorageError(
            "mutable authority snapshot diverges from the production ledger"
        )


class ProductionSQLiteWorkspaceRepository(SQLiteWorkspaceRepository):
    """SQLite repository that fails closed when mutable authority diverges from audit."""

    def _existing_schema_version(self) -> int | None:
        """Read schema metadata without leaking a file handle on Windows."""

        if not self.database_path.is_file() or self.database_path.stat().st_size == 0:
            return None
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(
                f"file:{self.database_path}?mode=ro", uri=True, timeout=10.0
            )
            table = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='workspace_meta'"
            ).fetchone()
            if table is None:
                return None
            row = connection.execute(
                "SELECT value FROM workspace_meta WHERE key = 'schema_version'"
            ).fetchone()
        except sqlite3.DatabaseError as exc:
            raise WorkspaceStorageError(f"workspace database is invalid: {exc}") from exc
        finally:
            if connection is not None:
                connection.close()
        if row is None:
            return None
        try:
            return int(row[0])
        except (TypeError, ValueError) as exc:
            raise WorkspaceStorageError("workspace schema version is invalid") from exc

    def _pre_migration_backup(self, from_version: int) -> Path:
        """Create the backup-first migration copy with all SQLite handles closed."""

        target = self._pre_migration_backup_path(from_version)
        if target.exists():
            return target
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.unlink(missing_ok=True)
        source: sqlite3.Connection | None = None
        destination: sqlite3.Connection | None = None
        candidate: sqlite3.Connection | None = None
        try:
            source = sqlite3.connect(
                f"file:{self.database_path}?mode=ro", uri=True, timeout=10.0
            )
            destination = sqlite3.connect(temporary)
            source.backup(destination)
            destination.commit()
            destination.close()
            destination = None
            source.close()
            source = None

            candidate = sqlite3.connect(f"file:{temporary}?mode=ro", uri=True)
            check = candidate.execute("PRAGMA integrity_check").fetchone()
            if check is None or check[0] != "ok":
                raise WorkspaceStorageError("pre-migration backup failed integrity check")
            candidate.close()
            candidate = None
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        finally:
            if candidate is not None:
                candidate.close()
            if destination is not None:
                destination.close()
            if source is not None:
                source.close()
        return target

    def initialize(self) -> None:
        super().initialize()
        if self._workspace_id is not None:
            self._verify_authority_snapshot_consistency()

    def bind_production(
        self,
        *,
        workspace_id: str,
        integrity_dir: str | Path,
        bootstrap_actor_id: str,
    ) -> dict[str, Any]:
        super().bind_production(
            workspace_id=workspace_id,
            integrity_dir=integrity_dir,
            bootstrap_actor_id=bootstrap_actor_id,
        )
        self._ensure_authority_checkpoint(bootstrap_actor_id=bootstrap_actor_id)
        return self.verify_production_integrity()

    def verify_production_integrity(self) -> dict[str, Any]:
        report = super().verify_production_integrity()
        self._verify_authority_snapshot_consistency()
        return {**report, "authority_snapshot_verified": True}

    def _advance_anchor(self) -> None:
        """Prove the mutable snapshot before authenticating a newer ledger head."""

        self._verify_authority_snapshot_consistency()
        super()._advance_anchor()

    def _current_authority_snapshot(self, connection: sqlite3.Connection) -> dict[str, str]:
        return authority_snapshot_from_connection(connection)

    @staticmethod
    def _snapshot_payload(snapshot: dict[str, str]) -> list[dict[str, str]]:
        return authority_snapshot_payload(snapshot)

    @staticmethod
    def _payload_snapshot(value: Any) -> dict[str, str]:
        return authority_snapshot_from_payload(value)

    def _ensure_authority_checkpoint(self, *, bootstrap_actor_id: str) -> None:
        if self._workspace_id is None:
            raise WorkspaceStorageError("production workspace is not bound")
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT 1 FROM production_ledger "
                "WHERE event_type='production.authority_checkpoint' LIMIT 1"
            ).fetchone()
            if existing is not None:
                return
            snapshot = self._current_authority_snapshot(connection)
            epoch_row = connection.execute(
                "SELECT value FROM workspace_meta WHERE key='audit_epoch'"
            ).fetchone()
            if epoch_row is None:
                raise WorkspaceStorageError("workspace audit epoch is missing")
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._append_ledger_event(
                    connection,
                    workspace_id=self._workspace_id,
                    audit_epoch=str(epoch_row["value"]),
                    event_type="production.authority_checkpoint",
                    payload={"authority_snapshot": self._snapshot_payload(snapshot)},
                    actor_id=bootstrap_actor_id,
                    actor_scope_id=self._workspace_id,
                    auth_method="local-install-bootstrap",
                    policy_version="production-bootstrap-v1",
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        self._advance_anchor()

    def _verify_authority_snapshot_consistency(self) -> None:
        with self._connect() as connection:
            verify_authority_snapshot_connection(connection)

    def backup_to(self, destination: str | Path) -> Path:
        """Create a closed-handle, integrity-checked portable SQLite backup."""

        self.initialize()
        if self._workspace_id is not None:
            self._verify_bound_integrity(recover_anchor=True)
            self._verify_authority_snapshot_consistency()
        target = Path(destination).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.unlink(missing_ok=True)

        with self._connect() as source:
            destination_db = sqlite3.connect(temporary)
            try:
                source.backup(destination_db)
                destination_db.commit()
            finally:
                destination_db.close()

        candidate = sqlite3.connect(f"file:{temporary}?mode=ro", uri=True)
        try:
            candidate.row_factory = sqlite3.Row
            check = candidate.execute("PRAGMA integrity_check").fetchone()
            if check is None or check[0] != "ok":
                raise WorkspaceStorageError("backup failed integrity check")
            if self._workspace_id is not None:
                verify_authority_snapshot_connection(candidate)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        finally:
            candidate.close()

        os.replace(temporary, target)
        return target
