"""Production-bound SQLite repository with snapshot-to-ledger consistency checks."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from uuid import uuid4

from shadowseed.storage.integrity import (
    EVENT_FORMAT_VERSION,
    authority_digest,
    canonical_json,
    event_digest,
)
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

    @staticmethod
    def _validate_bootstrap_marker_payload(payload: Any) -> dict[str, Any]:
        """Accept a strictly validated protected checkpoint plan during sealing."""

        if not isinstance(payload, dict):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        checkpoint_plan = payload.get("checkpoint_plan")
        base_payload = dict(payload)
        base_payload.pop("checkpoint_plan", None)
        validated = SQLiteWorkspaceRepository._validate_bootstrap_marker_payload(base_payload)
        if checkpoint_plan is None:
            return validated
        if not isinstance(checkpoint_plan, dict):
            raise WorkspaceStorageError("protected checkpoint plan is invalid")
        expected_keys = {
            "sequence_no",
            "event_id",
            "workspace_id",
            "audit_epoch",
            "session_id",
            "seed_id",
            "event_type",
            "request_id",
            "actor_id",
            "actor_scope_id",
            "capability",
            "auth_method",
            "policy_version",
            "payload_json",
            "previous_hash",
            "event_hash",
            "created_at",
            "event_format_version",
        }
        if set(checkpoint_plan) != expected_keys:
            raise WorkspaceStorageError("protected checkpoint plan is invalid")
        expected_values = {
            "sequence_no": 2,
            "workspace_id": validated["workspace_id"],
            "audit_epoch": validated["audit_epoch"],
            "session_id": None,
            "seed_id": None,
            "event_type": "production.authority_checkpoint",
            "request_id": None,
            "actor_id": validated["bootstrap_actor_id"],
            "actor_scope_id": validated["workspace_id"],
            "capability": None,
            "auth_method": "local-install-bootstrap",
            "policy_version": "production-bootstrap-v1",
            "previous_hash": validated["expected_genesis_hash"],
            "event_format_version": EVENT_FORMAT_VERSION,
        }
        for field, expected_value in expected_values.items():
            if checkpoint_plan.get(field) != expected_value:
                raise WorkspaceStorageError("protected checkpoint plan is invalid")
        event_id = checkpoint_plan.get("event_id")
        created_at = checkpoint_plan.get("created_at")
        payload_json = checkpoint_plan.get("payload_json")
        event_hash = checkpoint_plan.get("event_hash")
        if not isinstance(event_id, str) or not event_id.startswith("ledger::"):
            raise WorkspaceStorageError("protected checkpoint plan is invalid")
        if not isinstance(created_at, str) or not created_at:
            raise WorkspaceStorageError("protected checkpoint plan is invalid")
        if not isinstance(payload_json, str):
            raise WorkspaceStorageError("protected checkpoint plan is invalid")
        try:
            checkpoint_payload = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise WorkspaceStorageError("protected checkpoint plan is invalid") from exc
        if not isinstance(checkpoint_payload, dict) or set(checkpoint_payload) != {
            "authority_snapshot"
        }:
            raise WorkspaceStorageError("protected checkpoint plan is invalid")
        authority_snapshot_from_payload(checkpoint_payload["authority_snapshot"])
        digest_input = {
            key: value for key, value in checkpoint_plan.items() if key != "event_hash"
        }
        if not isinstance(event_hash, str) or event_hash != event_digest(digest_input):
            raise WorkspaceStorageError("protected checkpoint plan is invalid")
        validated["checkpoint_plan"] = dict(checkpoint_plan)
        return validated

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
            self._fsync_directory(target.parent)
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
        if not workspace_id.startswith("workspace::"):
            raise WorkspaceStorageError("production workspace_id is invalid")
        self._workspace_id = None
        self._anchor_path = None
        self._key_path = None
        self._integrity_dir = Path(integrity_dir).expanduser().resolve()
        with self._bootstrap_lock():
            self._hold_bootstrap_marker = True
            self._bootstrap_marker_required = False
            try:
                resumed_pending = False
                try:
                    binding_report = self._bind_production_locked(
                        workspace_id=workspace_id,
                        integrity_dir=self._integrity_dir,
                        bootstrap_actor_id=bootstrap_actor_id,
                    )
                except WorkspaceStorageError as exc:
                    if str(exc) != (
                        "incomplete production bootstrap cannot be resumed safely; "
                        "explicit recovery is required"
                    ):
                        raise
                    binding_report = self._resume_pending_authority_checkpoint(
                        workspace_id=workspace_id,
                        bootstrap_actor_id=bootstrap_actor_id,
                    )
                    if binding_report is None:
                        raise exc
                    resumed_pending = True

                pending = self._read_bootstrap_marker()
                if (
                    resumed_pending or int(binding_report["event_count"]) == 1
                ) and pending is None:
                    raise WorkspaceStorageError(
                        "protected bootstrap marker disappeared before authority checkpoint "
                        "sealing; explicit recovery is required"
                    )
                self._bootstrap_marker_required = pending is not None

                self._ensure_authority_checkpoint(bootstrap_actor_id=bootstrap_actor_id)
                sealed_marker = self._read_bootstrap_marker()
                if self._bootstrap_marker_required:
                    if sealed_marker is None or sealed_marker.get("checkpoint_plan") is None:
                        raise WorkspaceStorageError(
                            "protected checkpoint commitment disappeared before bootstrap "
                            "sealing; explicit recovery is required"
                        )
                report = self.verify_production_integrity()
                if sealed_marker is not None:
                    self._hold_bootstrap_marker = False
                    super()._clear_bootstrap_marker(workspace_id)
                return report
            finally:
                self._bootstrap_marker_required = False
                self._hold_bootstrap_marker = False

    def _clear_bootstrap_marker(self, workspace_id: str) -> None:
        """Retain bootstrap commitment until the first authority anchor is sealed."""

        if getattr(self, "_hold_bootstrap_marker", False):
            marker = self._read_bootstrap_marker()
            if marker is None or marker["workspace_id"] != workspace_id:
                raise WorkspaceStorageError(
                    "protected bootstrap marker is missing or does not match workspace identity"
                )
            return
        super()._clear_bootstrap_marker(workspace_id)

    def _write_bootstrap_marker_payload(self, marker: Mapping[str, Any]) -> dict[str, Any]:
        """Atomically and durably replace the protected bootstrap commitment."""

        marker_payload = self._validate_bootstrap_marker_payload(dict(marker))
        path = self._bootstrap_marker_path()
        self._ensure_durable_directory(path.parent)
        temporary = path.with_name(path.name + ".checkpoint.tmp")
        temporary.unlink(missing_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(temporary, flags, 0o600)
        try:
            if os.name != "nt":
                os.fchmod(fd, 0o600)
            handle = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
            fd = -1
            with handle:
                handle.write(canonical_json(marker_payload) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
            self._fsync_directory(path.parent)
            try:
                path.chmod(0o600)
            except OSError:
                pass
        finally:
            if fd >= 0:
                os.close(fd)
            temporary.unlink(missing_ok=True)
        verified = self._read_bootstrap_marker()
        if verified != marker_payload:
            raise WorkspaceStorageError(
                "protected checkpoint commitment could not be verified"
            )
        return marker_payload

    def _validate_pending_bootstrap_context(
        self,
        connection: sqlite3.Connection,
        *,
        marker: Mapping[str, Any],
        workspace_id: str,
        bootstrap_actor_id: str,
    ) -> None:
        if (
            marker["workspace_id"] != workspace_id
            or marker["bootstrap_actor_id"] != bootstrap_actor_id
        ):
            raise WorkspaceStorageError(
                "protected bootstrap marker does not match checkpoint sealing"
            )
        workspace_row = connection.execute(
            "SELECT value FROM workspace_meta WHERE key='workspace_id'"
        ).fetchone()
        if workspace_row is None or str(workspace_row["value"]) != workspace_id:
            raise WorkspaceStorageError(
                "workspace identity changed while production bootstrap was pending; "
                "explicit recovery is required"
            )
        epoch_row = connection.execute(
            "SELECT value FROM workspace_meta WHERE key='audit_epoch'"
        ).fetchone()
        if epoch_row is None or str(epoch_row["value"]) != str(marker["audit_epoch"]):
            raise WorkspaceStorageError(
                "production bootstrap audit epoch changed while checkpoint sealing was "
                "pending; explicit recovery is required"
            )
        live_authority_baseline = self._workspace_authority_baseline(connection)
        protected_authority_baseline = str(
            marker["bootstrap_payload"]["authority_baseline"]
        )
        if live_authority_baseline != protected_authority_baseline:
            raise WorkspaceStorageError(
                "production bootstrap authority baseline changed before checkpoint sealing; "
                "explicit recovery is required"
            )

    def _build_checkpoint_plan(
        self,
        connection: sqlite3.Connection,
        *,
        marker: Mapping[str, Any],
        bootstrap_actor_id: str,
    ) -> dict[str, Any]:
        snapshot = self._current_authority_snapshot(connection)
        row: dict[str, Any] = {
            "sequence_no": 2,
            "event_id": f"ledger::{uuid4()}",
            "workspace_id": str(marker["workspace_id"]),
            "audit_epoch": str(marker["audit_epoch"]),
            "session_id": None,
            "seed_id": None,
            "event_type": "production.authority_checkpoint",
            "request_id": None,
            "actor_id": bootstrap_actor_id,
            "actor_scope_id": str(marker["workspace_id"]),
            "capability": None,
            "auth_method": "local-install-bootstrap",
            "policy_version": "production-bootstrap-v1",
            "payload_json": canonical_json(
                {"authority_snapshot": self._snapshot_payload(snapshot)}
            ),
            "previous_hash": str(marker["expected_genesis_hash"]),
            "created_at": datetime.now().isoformat(),
            "event_format_version": EVENT_FORMAT_VERSION,
        }
        row["event_hash"] = event_digest(row)
        return row

    @staticmethod
    def _insert_checkpoint_plan(
        connection: sqlite3.Connection, checkpoint_plan: Mapping[str, Any]
    ) -> None:
        connection.execute(
            """
            INSERT INTO production_ledger(
                sequence_no, event_id, workspace_id, audit_epoch, session_id, seed_id,
                event_type, request_id, actor_id, actor_scope_id, capability,
                auth_method, policy_version, payload_json, previous_hash, event_hash,
                created_at, event_format_version
            ) VALUES(
                :sequence_no, :event_id, :workspace_id, :audit_epoch, :session_id, :seed_id,
                :event_type, :request_id, :actor_id, :actor_scope_id, :capability,
                :auth_method, :policy_version, :payload_json, :previous_hash, :event_hash,
                :created_at, :event_format_version
            )
            """,
            dict(checkpoint_plan),
        )

    @staticmethod
    def _validate_pending_checkpoint_row(
        checkpoint: Mapping[str, Any], *, marker: Mapping[str, Any]
    ) -> None:
        checkpoint_plan = marker.get("checkpoint_plan")
        if not isinstance(checkpoint_plan, dict) or dict(checkpoint) != checkpoint_plan:
            raise WorkspaceStorageError(
                "pending production authority checkpoint does not match protected bootstrap "
                "commitment; explicit recovery is required"
            )

    def _resume_pending_authority_checkpoint(
        self,
        *,
        workspace_id: str,
        bootstrap_actor_id: str,
    ) -> dict[str, Any] | None:
        """Validate the only safe two-row bootstrap resume state without anchoring it."""

        marker = self._read_bootstrap_marker()
        if marker is None or marker.get("checkpoint_plan") is None:
            return None
        if (
            marker["workspace_id"] != workspace_id
            or marker["bootstrap_actor_id"] != bootstrap_actor_id
        ):
            return None

        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                rows = connection.execute(
                    "SELECT * FROM production_ledger ORDER BY sequence_no"
                ).fetchall()
                if len(rows) != 2:
                    connection.rollback()
                    return None
                bootstrap, checkpoint = rows
                if (
                    int(bootstrap["sequence_no"]) != 1
                    or bootstrap["event_type"] != "production.bootstrap"
                    or str(bootstrap["event_hash"])
                    != str(marker["expected_genesis_hash"])
                    or int(checkpoint["sequence_no"]) != 2
                    or checkpoint["event_type"] != "production.authority_checkpoint"
                ):
                    connection.rollback()
                    return None

                self._validate_pending_bootstrap_context(
                    connection,
                    marker=marker,
                    workspace_id=workspace_id,
                    bootstrap_actor_id=bootstrap_actor_id,
                )
                self._validate_pending_checkpoint_row(checkpoint, marker=marker)
                verify_authority_snapshot_connection(connection)
                connection.commit()
            except Exception:
                connection.rollback()
                raise

        report = self._verify_chain_only()
        if (
            int(report["event_count"]) != 2
            or report["workspace_id"] != workspace_id
            or str(report["audit_epoch"]) != str(marker["audit_epoch"])
            or str(report["head_hash"])
            != str(marker["checkpoint_plan"]["event_hash"])
        ):
            raise WorkspaceStorageError(
                "pending production authority checkpoint does not match protected bootstrap "
                "commitment; explicit recovery is required"
            )
        return report

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
        marker = self._read_bootstrap_marker()
        if getattr(self, "_bootstrap_marker_required", False) and marker is None:
            raise WorkspaceStorageError(
                "protected bootstrap marker disappeared before checkpoint sealing; "
                "explicit recovery is required"
            )
        should_advance_anchor = False
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                if marker is not None:
                    self._validate_pending_bootstrap_context(
                        connection,
                        marker=marker,
                        workspace_id=self._workspace_id,
                        bootstrap_actor_id=bootstrap_actor_id,
                    )

                existing = connection.execute(
                    "SELECT * FROM production_ledger "
                    "WHERE event_type='production.authority_checkpoint' LIMIT 1"
                ).fetchone()
                if existing is not None:
                    if marker is None:
                        connection.rollback()
                        return
                    self._validate_pending_checkpoint_row(existing, marker=marker)
                    verify_authority_snapshot_connection(connection)
                    connection.rollback()
                    should_advance_anchor = True
                elif marker is not None:
                    checkpoint_plan = marker.get("checkpoint_plan")
                    if checkpoint_plan is None:
                        checkpoint_plan = self._build_checkpoint_plan(
                            connection,
                            marker=marker,
                            bootstrap_actor_id=bootstrap_actor_id,
                        )
                        updated_marker = dict(marker)
                        updated_marker["checkpoint_plan"] = checkpoint_plan
                        marker = self._write_bootstrap_marker_payload(updated_marker)
                        checkpoint_plan = marker["checkpoint_plan"]
                    current_snapshot = self._current_authority_snapshot(connection)
                    checkpoint_payload = json.loads(str(checkpoint_plan["payload_json"]))
                    planned_snapshot = self._payload_snapshot(
                        checkpoint_payload["authority_snapshot"]
                    )
                    if planned_snapshot != current_snapshot:
                        raise WorkspaceStorageError(
                            "protected checkpoint plan does not match live authority; "
                            "explicit recovery is required"
                        )
                    ledger_rows = connection.execute(
                        "SELECT sequence_no, event_type, event_hash "
                        "FROM production_ledger ORDER BY sequence_no"
                    ).fetchall()
                    if (
                        len(ledger_rows) != 1
                        or int(ledger_rows[0]["sequence_no"]) != 1
                        or ledger_rows[0]["event_type"] != "production.bootstrap"
                        or str(ledger_rows[0]["event_hash"])
                        != str(marker["expected_genesis_hash"])
                    ):
                        raise WorkspaceStorageError(
                            "protected checkpoint plan cannot be applied to this ledger; "
                            "explicit recovery is required"
                        )
                    self._insert_checkpoint_plan(connection, checkpoint_plan)
                    connection.commit()
                    should_advance_anchor = True
                else:
                    snapshot = self._current_authority_snapshot(connection)
                    epoch_row = connection.execute(
                        "SELECT value FROM workspace_meta WHERE key='audit_epoch'"
                    ).fetchone()
                    if epoch_row is None:
                        raise WorkspaceStorageError("workspace audit epoch is missing")
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
                    should_advance_anchor = True
            except Exception:
                connection.rollback()
                raise
        if should_advance_anchor:
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
