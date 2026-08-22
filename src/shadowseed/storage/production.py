"""Production-bound SQLite repository with snapshot-to-ledger consistency checks."""

from __future__ import annotations

import json
from typing import Any

from shadowseed.storage.integrity import authority_digest
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError


class ProductionSQLiteWorkspaceRepository(SQLiteWorkspaceRepository):
    """SQLite repository that fails closed when mutable authority diverges from audit."""

    def initialize(self) -> None:
        super().initialize()
        if self._workspace_id is not None:
            self._verify_authority_snapshot_consistency()

    def bind_production(
        self,
        *,
        workspace_id: str,
        integrity_dir: str,
        bootstrap_actor_id: str,
    ) -> dict[str, Any]:
        report = super().bind_production(
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

    def _current_authority_snapshot(self, connection: Any) -> dict[str, str]:
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

    @staticmethod
    def _snapshot_payload(snapshot: dict[str, str]) -> list[dict[str, str]]:
        return [
            {"session_id": session_id, "authority_digest": digest}
            for session_id, digest in sorted(snapshot.items())
        ]

    @staticmethod
    def _payload_snapshot(value: Any) -> dict[str, str]:
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
            current = self._current_authority_snapshot(connection)
            rows = connection.execute(
                "SELECT session_id, event_type, payload_json "
                "FROM production_ledger ORDER BY sequence_no"
            ).fetchall()

        expected: dict[str, str] = {}
        checkpoint_seen = False
        for row in rows:
            event_type = str(row["event_type"])
            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError as exc:
                raise WorkspaceStorageError("production ledger payload JSON is invalid") from exc

            if event_type in {
                "production.authority_checkpoint",
                "workspace.restore",
                "workspace.import",
            }:
                expected = self._payload_snapshot(payload.get("authority_snapshot"))
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
            elif event_type in {"evidence.verify", "contradiction.submit"}:
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
        if current != expected:
            raise WorkspaceStorageError(
                "mutable authority snapshot diverges from the production ledger"
            )
