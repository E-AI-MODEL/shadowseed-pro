"""Transactional SQLite repository for local Shadowseed tester workspaces."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, Mapping
from uuid import uuid4

from shadowseed.application.models import SessionSummary, TesterFeedback
from shadowseed.storage.integrity import (
    EVENT_FORMAT_VERSION,
    GENESIS_HASH,
    AnchorState,
    authority_digest,
    canonical_json,
    create_integrity_key,
    event_digest,
    key_id,
    load_integrity_key,
    minimal_runtime_commit,
    read_anchor,
    verify_chain_rows,
    write_anchor,
)
from shadowseed.storage.schema import DDL, MIGRATION_1_TO_2, SCHEMA_VERSION


class WorkspaceStorageError(RuntimeError):
    """Raised when a workspace cannot be opened, migrated, or restored safely."""


_SECRET_FRAGMENTS = ("api_key", "apikey", "access_token", "secret", "password")
_BOOTSTRAP_MARKER_FORMAT_VERSION = 1


def _json(value: Any) -> str:
    return canonical_json(value)


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


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class SQLiteWorkspaceRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path).expanduser().resolve()
        self._workspace_id: str | None = None
        self._integrity_dir: Path | None = None
        self._anchor_path: Path | None = None
        self._key_path: Path | None = None

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

    def _existing_schema_version(self) -> int | None:
        if not self.database_path.is_file() or self.database_path.stat().st_size == 0:
            return None
        try:
            with sqlite3.connect(
                f"file:{self.database_path}?mode=ro", uri=True, timeout=10.0
            ) as connection:
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
        if row is None:
            return None
        try:
            return int(row[0])
        except (TypeError, ValueError) as exc:
            raise WorkspaceStorageError("workspace schema version is invalid") from exc

    def _pre_migration_backup_path(self, from_version: int = 1) -> Path:
        return self.database_path.with_name(
            f"{self.database_path.name}.pre-migration-v{from_version}-to-v{SCHEMA_VERSION}.bak"
        )

    def _pre_migration_backup(self, from_version: int) -> Path:
        target = self._pre_migration_backup_path(from_version)
        if target.exists():
            return target
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.unlink(missing_ok=True)
        try:
            with sqlite3.connect(
                f"file:{self.database_path}?mode=ro", uri=True, timeout=10.0
            ) as source:
                destination = sqlite3.connect(temporary)
                try:
                    source.backup(destination)
                    destination.commit()
                finally:
                    destination.close()
            with sqlite3.connect(f"file:{temporary}?mode=ro", uri=True) as candidate:
                check = candidate.execute("PRAGMA integrity_check").fetchone()
                if check is None or check[0] != "ok":
                    raise WorkspaceStorageError("pre-migration backup failed integrity check")
            os.replace(temporary, target)
            self._fsync_directory(target.parent)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        return target

    def initialize(self) -> None:
        current_version = self._existing_schema_version()
        if current_version is not None and current_version > SCHEMA_VERSION:
            raise WorkspaceStorageError(
                "workspace schema is newer than this Shadowseed installation"
            )
        if current_version is not None and current_version < SCHEMA_VERSION:
            if current_version != 1:
                raise WorkspaceStorageError(
                    f"no migration path from workspace schema {current_version} "
                    f"to {SCHEMA_VERSION}"
                )
            self._pre_migration_backup(current_version)

        with self._connect() as connection:
            try:
                with connection:
                    if current_version == 1:
                        self._migrate(connection, current_version)
                    else:
                        for statement in DDL:
                            connection.execute(statement)
                        current = connection.execute(
                            "SELECT value FROM workspace_meta WHERE key = 'schema_version'"
                        ).fetchone()
                        if current is None:
                            connection.execute(
                                "INSERT INTO workspace_meta(key, value) "
                                "VALUES('schema_version', ?)",
                                (str(SCHEMA_VERSION),),
                            )
                        elif int(current["value"]) != SCHEMA_VERSION:
                            raise WorkspaceStorageError(
                                "workspace schema changed during initialization"
                            )
                    check = connection.execute("PRAGMA integrity_check").fetchone()
                    if check is None or check[0] != "ok":
                        raise WorkspaceStorageError("workspace database failed integrity check")
            except sqlite3.DatabaseError as exc:
                raise WorkspaceStorageError(f"workspace database is invalid: {exc}") from exc

        if self._workspace_id is not None:
            self._verify_bound_integrity(recover_anchor=True)

    def _migrate(self, connection: sqlite3.Connection, from_version: int) -> None:
        if from_version != 1 or SCHEMA_VERSION != 2:
            raise WorkspaceStorageError(
                f"no migration path from workspace schema {from_version} to {SCHEMA_VERSION}"
            )
        for statement in MIGRATION_1_TO_2:
            connection.execute(statement)
        connection.execute(
            "UPDATE workspace_meta SET value = ? WHERE key = 'schema_version'",
            (str(SCHEMA_VERSION),),
        )

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        if os.name == "nt":
            return
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        try:
            fd = os.open(path, flags)
        except OSError as exc:
            raise WorkspaceStorageError(
                "protected integrity directory is unavailable for durability sync"
            ) from exc
        try:
            os.fsync(fd)
        except OSError as exc:
            raise WorkspaceStorageError(
                "protected integrity directory durability sync failed"
            ) from exc
        finally:
            os.close(fd)

    def _ensure_durable_directory(self, path: Path) -> None:
        path = Path(path)
        if path.exists():
            if not path.is_dir():
                raise WorkspaceStorageError(
                    "protected integrity directory path is not a directory"
                )
            try:
                path.chmod(0o700)
            except OSError:
                pass
            return

        missing: list[Path] = []
        cursor = path
        while not cursor.exists():
            parent = cursor.parent
            if parent == cursor:
                raise WorkspaceStorageError(
                    "protected integrity directory has no existing ancestor"
                )
            missing.append(cursor)
            cursor = parent
        if not cursor.is_dir():
            raise WorkspaceStorageError(
                "protected integrity directory ancestor is not a directory"
            )

        for directory in reversed(missing):
            try:
                directory.mkdir()
            except FileExistsError:
                if not directory.is_dir():
                    raise WorkspaceStorageError(
                        "protected integrity directory path is not a directory"
                    )
            try:
                directory.chmod(0o700)
            except OSError:
                pass
            self._fsync_directory(directory)
            self._fsync_directory(directory.parent)

    @contextmanager
    def _bootstrap_lock(self) -> Iterator[None]:
        if self._integrity_dir is None:
            raise WorkspaceStorageError("production integrity directory is not bound")
        self._ensure_durable_directory(self._integrity_dir)
        path = self._integrity_dir / "bootstrap.lock"
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(path, timeout=30.0, isolation_level=None)
            connection.execute("BEGIN EXCLUSIVE")
        except sqlite3.Error as exc:
            if connection is not None:
                connection.close()
            raise WorkspaceStorageError(
                "production bootstrap lock could not be acquired"
            ) from exc
        assert connection is not None
        try:
            yield
        finally:
            try:
                connection.rollback()
            finally:
                connection.close()

    def _bootstrap_marker_path(self) -> Path:
        if self._integrity_dir is None:
            raise WorkspaceStorageError("production integrity directory is not bound")
        return self._integrity_dir / "bootstrap.pending"

    @staticmethod
    def _validate_bootstrap_marker_payload(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        expected_keys = {
            "format_version",
            "workspace_id",
            "audit_epoch",
            "event_id",
            "created_at",
            "bootstrap_actor_id",
            "bootstrap_payload",
            "expected_genesis_hash",
        }
        if set(payload) != expected_keys:
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if payload.get("format_version") != _BOOTSTRAP_MARKER_FORMAT_VERSION:
            raise WorkspaceStorageError("protected bootstrap marker format is unsupported")
        workspace_id = payload.get("workspace_id")
        audit_epoch = payload.get("audit_epoch")
        event_id = payload.get("event_id")
        created_at = payload.get("created_at")
        bootstrap_actor_id = payload.get("bootstrap_actor_id")
        bootstrap_payload = payload.get("bootstrap_payload")
        expected_genesis_hash = payload.get("expected_genesis_hash")
        if not isinstance(workspace_id, str) or not workspace_id.startswith("workspace::"):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if not isinstance(audit_epoch, str) or not audit_epoch.startswith("epoch::"):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if not isinstance(event_id, str) or not event_id.startswith("ledger::"):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if not isinstance(created_at, str) or not created_at:
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if not isinstance(bootstrap_actor_id, str) or not bootstrap_actor_id:
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if not isinstance(bootstrap_payload, dict) or set(bootstrap_payload) != {
            "pre_production_history",
            "source_schema_version",
            "source_database_sha256",
            "authority_baseline",
        }:
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        pre_production_history = bootstrap_payload.get("pre_production_history")
        source_schema_version = bootstrap_payload.get("source_schema_version")
        source_database_sha256 = bootstrap_payload.get("source_database_sha256")
        authority_baseline = bootstrap_payload.get("authority_baseline")
        if not isinstance(pre_production_history, bool):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if source_schema_version not in {1, SCHEMA_VERSION}:
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if pre_production_history != (source_schema_version == 1):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if pre_production_history:
            if (
                not isinstance(source_database_sha256, str)
                or len(source_database_sha256) != 64
                or any(
                    character not in "0123456789abcdef"
                    for character in source_database_sha256
                )
            ):
                raise WorkspaceStorageError("protected bootstrap marker is invalid")
        elif source_database_sha256 is not None:
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if (
            not isinstance(authority_baseline, str)
            or len(authority_baseline) != 64
            or any(
                character not in "0123456789abcdef"
                for character in authority_baseline
            )
        ):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if (
            not isinstance(expected_genesis_hash, str)
            or len(expected_genesis_hash) != 64
            or any(character not in "0123456789abcdef" for character in expected_genesis_hash)
        ):
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        return dict(payload)

    def _read_bootstrap_marker(self) -> dict[str, Any] | None:
        path = self._bootstrap_marker_path()
        if not path.exists():
            return None
        if not path.is_file():
            raise WorkspaceStorageError("protected bootstrap marker is invalid")
        if os.name != "nt":
            try:
                mode = path.stat().st_mode & 0o777
            except OSError as exc:
                raise WorkspaceStorageError(
                    "protected bootstrap marker is unavailable"
                ) from exc
            if mode & 0o077:
                raise WorkspaceStorageError(
                    "protected bootstrap marker permissions are too broad"
                )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkspaceStorageError(
                "protected bootstrap marker is unavailable or malformed"
            ) from exc
        return self._validate_bootstrap_marker_payload(payload)

    def _production_bootstrap_payload(
        self, connection: sqlite3.Connection
    ) -> dict[str, Any]:
        backup = self._pre_migration_backup_path(1)
        pre_production_history = backup.is_file()
        source_schema = 1 if pre_production_history else SCHEMA_VERSION
        source_digest = _file_sha256(backup) if pre_production_history else None
        return {
            "pre_production_history": pre_production_history,
            "source_schema_version": source_schema,
            "source_database_sha256": source_digest,
            "authority_baseline": self._workspace_authority_baseline(connection),
        }

    def _bootstrap_event_row(
        self,
        connection: sqlite3.Connection,
        marker: Mapping[str, Any],
    ) -> dict[str, Any]:
        return {
            "sequence_no": 1,
            "event_id": str(marker["event_id"]),
            "workspace_id": str(marker["workspace_id"]),
            "audit_epoch": str(marker["audit_epoch"]),
            "session_id": None,
            "seed_id": None,
            "event_type": "production.bootstrap",
            "request_id": None,
            "actor_id": str(marker["bootstrap_actor_id"]),
            "actor_scope_id": str(marker["workspace_id"]),
            "capability": None,
            "auth_method": "local-install-bootstrap",
            "policy_version": "production-bootstrap-v1",
            "payload_json": _json(marker["bootstrap_payload"]),
            "previous_hash": GENESIS_HASH,
            "created_at": str(marker["created_at"]),
            "event_format_version": EVENT_FORMAT_VERSION,
        }

    def _prepare_bootstrap_marker(
        self, *, workspace_id: str, bootstrap_actor_id: str
    ) -> dict[str, Any]:
        with self._connect() as connection:
            existing = connection.execute(
                "SELECT COUNT(*) FROM production_ledger"
            ).fetchone()
            if existing is None or int(existing[0]) != 0:
                raise WorkspaceStorageError("production genesis already exists")
            marker: dict[str, Any] = {
                "format_version": _BOOTSTRAP_MARKER_FORMAT_VERSION,
                "workspace_id": workspace_id,
                "audit_epoch": f"epoch::{uuid4()}",
                "event_id": f"ledger::{uuid4()}",
                "created_at": datetime.now().isoformat(),
                "bootstrap_actor_id": bootstrap_actor_id,
                "bootstrap_payload": self._production_bootstrap_payload(connection),
                "expected_genesis_hash": "0" * 64,
            }
            planned = self._bootstrap_event_row(connection, marker)
        marker["expected_genesis_hash"] = event_digest(planned)
        return self._validate_bootstrap_marker_payload(marker)

    def _ensure_bootstrap_marker(self, marker: Mapping[str, Any]) -> None:
        marker_payload = self._validate_bootstrap_marker_payload(dict(marker))
        path = self._bootstrap_marker_path()
        existing = self._read_bootstrap_marker()
        if existing is not None:
            if existing != marker_payload:
                raise WorkspaceStorageError(
                    "protected bootstrap marker does not match pending genesis"
                )
            return

        self._ensure_durable_directory(path.parent)
        temporary = path.with_name(path.name + ".tmp")
        temporary.unlink(missing_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        fd = os.open(temporary, flags, 0o600)
        try:
            if os.name != "nt":
                os.fchmod(fd, 0o600)
            handle = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
            fd = -1
            with handle:
                handle.write(_json(marker_payload) + "\n")
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

        if self._read_bootstrap_marker() != marker_payload:
            raise WorkspaceStorageError("protected bootstrap marker could not be verified")

    def _clear_bootstrap_marker(self, workspace_id: str) -> None:
        path = self._bootstrap_marker_path()
        marker = self._read_bootstrap_marker()
        if marker is None or marker["workspace_id"] != workspace_id:
            raise WorkspaceStorageError(
                "protected bootstrap marker is missing or does not match workspace identity"
            )
        try:
            path.unlink()
            self._fsync_directory(path.parent)
        except OSError as exc:
            raise WorkspaceStorageError(
                "protected bootstrap marker could not be cleared"
            ) from exc

    def bind_production(
        self,
        *,
        workspace_id: str,
        integrity_dir: str | Path,
        bootstrap_actor_id: str,
    ) -> dict[str, Any]:
        if not workspace_id.startswith("workspace::"):
            raise WorkspaceStorageError("production workspace_id is invalid")
        self._integrity_dir = Path(integrity_dir).expanduser().resolve()
        with self._bootstrap_lock():
            return self._bind_production_locked(
                workspace_id=workspace_id,
                integrity_dir=self._integrity_dir,
                bootstrap_actor_id=bootstrap_actor_id,
            )

    def _bind_production_locked(
        self,
        *,
        workspace_id: str,
        integrity_dir: str | Path,
        bootstrap_actor_id: str,
    ) -> dict[str, Any]:
        """Bind a stable workspace identity and protected anchor to this repository.

        Existing ledgers never recreate missing key/anchor material silently. The only
        automatic anchor advancement is crash recovery for a verified unique extension
        of the previously authenticated head.
        """

        if not workspace_id.startswith("workspace::"):
            raise WorkspaceStorageError("production workspace_id is invalid")
        self.initialize()
        self._workspace_id = workspace_id
        self._integrity_dir = Path(integrity_dir).expanduser().resolve()
        self._anchor_path = self._integrity_dir / "anchor.json"
        self._key_path = self._integrity_dir / "integrity.key"

        with self._connect() as connection:
            stored_workspace = connection.execute(
                "SELECT value FROM workspace_meta WHERE key='workspace_id'"
            ).fetchone()
            ledger_count = int(
                connection.execute("SELECT COUNT(*) FROM production_ledger").fetchone()[0]
            )

        pending = self._read_bootstrap_marker()
        if stored_workspace is not None and stored_workspace["value"] != workspace_id:
            raise WorkspaceStorageError(
                "workspace identity does not match the production database"
            )
        if pending is not None and pending["workspace_id"] != workspace_id:
            raise WorkspaceStorageError(
                "protected bootstrap marker does not match workspace identity"
            )
        if pending is not None and pending["bootstrap_actor_id"] != bootstrap_actor_id:
            raise WorkspaceStorageError(
                "protected bootstrap marker does not match bootstrap actor"
            )

        if ledger_count == 0:
            if self._anchor_path.exists():
                raise WorkspaceStorageError(
                    "production ledger history is missing while protected integrity "
                    "material exists; explicit recovery is required"
                )
            if self._key_path.exists() and pending is None:
                raise WorkspaceStorageError(
                    "production ledger history is missing while protected integrity "
                    "material exists; explicit recovery is required"
                )
            if pending is None:
                pending = self._prepare_bootstrap_marker(
                    workspace_id=workspace_id,
                    bootstrap_actor_id=bootstrap_actor_id,
                )
                self._ensure_bootstrap_marker(pending)

            key = create_integrity_key(self._key_path)
            self._create_production_genesis(
                workspace_id=workspace_id,
                bootstrap_actor_id=bootstrap_actor_id,
            )
            report = self._verify_chain_only()
            if report["head_hash"] != pending["expected_genesis_hash"]:
                raise WorkspaceStorageError(
                    "production bootstrap genesis does not match protected commitment; "
                    "explicit recovery is required"
                )
            write_anchor(
                self._anchor_path,
                AnchorState(
                    workspace_id=workspace_id,
                    audit_epoch=str(report["audit_epoch"]),
                    sequence_no=int(report["sequence_no"]),
                    head_hash=str(report["head_hash"]),
                    key_id=key_id(key),
                ),
                key,
            )
            verified = self._verify_bound_integrity(recover_anchor=False)
            self._clear_bootstrap_marker(workspace_id)
            return verified

        if stored_workspace is None:
            raise WorkspaceStorageError(
                "production ledger exists without bound workspace identity"
            )

        if pending is not None:
            with self._connect() as connection:
                bootstrap_events = connection.execute(
                    "SELECT event_type FROM production_ledger ORDER BY sequence_no"
                ).fetchall()
            if (
                len(bootstrap_events) != 1
                or bootstrap_events[0]["event_type"] != "production.bootstrap"
            ):
                raise WorkspaceStorageError(
                    "incomplete production bootstrap cannot be resumed safely; "
                    "explicit recovery is required"
                )
            report = self._verify_chain_only()
            if report["head_hash"] != pending["expected_genesis_hash"]:
                raise WorkspaceStorageError(
                    "incomplete production bootstrap does not match protected genesis "
                    "commitment; explicit recovery is required"
                )
            if not self._key_path.is_file():
                raise WorkspaceStorageError(
                    "protected integrity material is missing; explicit recovery is required"
                )
            key = load_integrity_key(self._key_path)
            if self._anchor_path.is_file():
                verified = self._verify_bound_integrity(recover_anchor=False)
            else:
                write_anchor(
                    self._anchor_path,
                    AnchorState(
                        workspace_id=workspace_id,
                        audit_epoch=str(report["audit_epoch"]),
                        sequence_no=int(report["sequence_no"]),
                        head_hash=str(report["head_hash"]),
                        key_id=key_id(key),
                    ),
                    key,
                )
                verified = self._verify_bound_integrity(recover_anchor=False)
            self._clear_bootstrap_marker(workspace_id)
            return verified

        if not self._key_path.is_file() or not self._anchor_path.is_file():
            raise WorkspaceStorageError(
                "protected integrity material is missing; explicit recovery is required"
            )
        return self._verify_bound_integrity(recover_anchor=True)

    def _create_production_genesis(
        self,
        *,
        workspace_id: str,
        bootstrap_actor_id: str,
    ) -> None:
        marker = self._read_bootstrap_marker()
        if marker is None:
            raise WorkspaceStorageError(
                "production bootstrap requires a protected genesis commitment"
            )
        if (
            marker["workspace_id"] != workspace_id
            or marker["bootstrap_actor_id"] != bootstrap_actor_id
        ):
            raise WorkspaceStorageError(
                "protected bootstrap marker does not match production bootstrap"
            )

        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT COUNT(*) FROM production_ledger"
                ).fetchone()
                if existing is None or int(existing[0]) != 0:
                    raise WorkspaceStorageError("production genesis already exists")
                stored_workspace = connection.execute(
                    "SELECT value FROM workspace_meta WHERE key='workspace_id'"
                ).fetchone()
                if stored_workspace is None:
                    connection.execute(
                        "INSERT INTO workspace_meta(key, value) VALUES('workspace_id', ?)",
                        (workspace_id,),
                    )
                elif stored_workspace["value"] != workspace_id:
                    raise WorkspaceStorageError(
                        "workspace identity mismatch during bootstrap"
                    )

                live_authority_baseline = self._workspace_authority_baseline(connection)
                protected_authority_baseline = str(
                    marker["bootstrap_payload"]["authority_baseline"]
                )
                if live_authority_baseline != protected_authority_baseline:
                    raise WorkspaceStorageError(
                        "production bootstrap authority baseline changed after protected "
                        "commitment; explicit recovery is required"
                    )

                planned = self._bootstrap_event_row(connection, marker)
                expected_hash = str(marker["expected_genesis_hash"])
                if event_digest(planned) != expected_hash:
                    raise WorkspaceStorageError(
                        "production bootstrap state changed after protected commitment; "
                        "explicit recovery is required"
                    )
                row = {**planned, "event_hash": expected_hash}
                connection.execute(
                    "INSERT OR REPLACE INTO workspace_meta(key, value) "
                    "VALUES('audit_epoch', ?)",
                    (str(marker["audit_epoch"]),),
                )
                connection.execute(
                    """
                    INSERT INTO production_ledger(
                        sequence_no, event_id, workspace_id, audit_epoch, session_id,
                        seed_id, event_type, request_id, actor_id, actor_scope_id,
                        capability, auth_method, policy_version, payload_json,
                        previous_hash, event_hash, created_at, event_format_version
                    ) VALUES(
                        :sequence_no, :event_id, :workspace_id, :audit_epoch, :session_id,
                        :seed_id, :event_type, :request_id, :actor_id, :actor_scope_id,
                        :capability, :auth_method, :policy_version, :payload_json,
                        :previous_hash, :event_hash, :created_at, :event_format_version
                    )
                    """,
                    row,
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    def _workspace_authority_baseline(self, connection: sqlite3.Connection) -> str:
        rows = connection.execute(
            "SELECT session_id, state_json FROM sessions ORDER BY session_id"
        ).fetchall()
        baseline: list[dict[str, str]] = []
        for row in rows:
            try:
                state = json.loads(row["state_json"])
            except json.JSONDecodeError as exc:
                raise WorkspaceStorageError(
                    f"session {row['session_id']!r} contains invalid JSON"
                ) from exc
            baseline.append(
                {
                    "session_id": str(row["session_id"]),
                    "authority_digest": authority_digest(state),
                }
            )
        return hashlib.sha256(_json(baseline).encode("utf-8")).hexdigest()

    def _append_ledger_event(
        self,
        connection: sqlite3.Connection,
        *,
        workspace_id: str,
        audit_epoch: str,
        event_type: str,
        payload: Mapping[str, Any],
        session_id: str | None = None,
        seed_id: str | None = None,
        request_id: str | None = None,
        actor_id: str | None = None,
        actor_scope_id: str | None = None,
        capability: str | None = None,
        auth_method: str | None = None,
        policy_version: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        latest = connection.execute(
            "SELECT sequence_no, event_hash FROM production_ledger "
            "ORDER BY sequence_no DESC LIMIT 1"
        ).fetchone()
        sequence_no = 1 if latest is None else int(latest["sequence_no"]) + 1
        previous_hash = GENESIS_HASH if latest is None else str(latest["event_hash"])
        row: dict[str, Any] = {
            "sequence_no": sequence_no,
            "event_id": f"ledger::{uuid4()}",
            "workspace_id": workspace_id,
            "audit_epoch": audit_epoch,
            "session_id": session_id,
            "seed_id": seed_id,
            "event_type": event_type,
            "request_id": request_id,
            "actor_id": actor_id,
            "actor_scope_id": actor_scope_id,
            "capability": capability,
            "auth_method": auth_method,
            "policy_version": policy_version,
            "payload_json": _json(dict(payload)),
            "previous_hash": previous_hash,
            "created_at": created_at or datetime.now().isoformat(),
            "event_format_version": EVENT_FORMAT_VERSION,
        }
        row["event_hash"] = event_digest(row)
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
            row,
        )
        return row

    def _ledger_rows(self, connection: sqlite3.Connection) -> list[dict[str, Any]]:
        rows = connection.execute(
            "SELECT * FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
        return [dict(row) for row in rows]

    def _verify_chain_only(self) -> dict[str, Any]:
        with self._connect() as connection:
            try:
                return verify_chain_rows(self._ledger_rows(connection))
            except ValueError as exc:
                raise WorkspaceStorageError(f"production ledger verification failed: {exc}") from exc

    def _verify_bound_integrity(self, *, recover_anchor: bool) -> dict[str, Any]:
        if (
            self._workspace_id is None
            or self._anchor_path is None
            or self._key_path is None
        ):
            raise WorkspaceStorageError("production integrity context is not bound")
        report = self._verify_chain_only()
        if report["event_count"] == 0:
            raise WorkspaceStorageError("production ledger genesis is missing")
        if report["workspace_id"] != self._workspace_id:
            raise WorkspaceStorageError("production ledger workspace identity mismatch")
        try:
            key = load_integrity_key(self._key_path)
            anchor = read_anchor(self._anchor_path, key)
        except ValueError as exc:
            raise WorkspaceStorageError(str(exc)) from exc
        if anchor.workspace_id != self._workspace_id:
            raise WorkspaceStorageError("protected anchor workspace identity mismatch")
        if anchor.key_id != key_id(key):
            raise WorkspaceStorageError("protected anchor key identity mismatch")

        db_sequence = int(report["sequence_no"])
        db_head = str(report["head_hash"])
        if db_sequence < anchor.sequence_no:
            raise WorkspaceStorageError("workspace database is behind the protected anchor")
        if db_sequence == anchor.sequence_no:
            if db_head != anchor.head_hash:
                raise WorkspaceStorageError("workspace ledger conflicts with protected anchor")
            if str(report["audit_epoch"]) != anchor.audit_epoch:
                raise WorkspaceStorageError("workspace audit epoch conflicts with protected anchor")
        else:
            with self._connect() as connection:
                anchored_row = connection.execute(
                    "SELECT event_hash FROM production_ledger WHERE sequence_no = ?",
                    (anchor.sequence_no,),
                ).fetchone()
            if anchored_row is None or anchored_row["event_hash"] != anchor.head_hash:
                raise WorkspaceStorageError(
                    "workspace ledger is not a continuation of the protected anchor"
                )
            if not recover_anchor:
                raise WorkspaceStorageError("protected anchor update is pending")
            write_anchor(
                self._anchor_path,
                AnchorState(
                    workspace_id=self._workspace_id,
                    audit_epoch=str(report["audit_epoch"]),
                    sequence_no=db_sequence,
                    head_hash=db_head,
                    key_id=key_id(key),
                ),
                key,
            )
        return {
            **report,
            "anchor_sequence_no": db_sequence,
            "anchor_head_hash": db_head,
            "key_id": key_id(key),
        }

    def verify_production_integrity(self) -> dict[str, Any]:
        self.initialize()
        return self._verify_bound_integrity(recover_anchor=True)

    def _current_epoch(self, connection: sqlite3.Connection) -> str:
        row = connection.execute(
            "SELECT value FROM workspace_meta WHERE key='audit_epoch'"
        ).fetchone()
        if row is None:
            raise WorkspaceStorageError("workspace audit epoch is missing")
        return str(row["value"])

    def _advance_anchor(self) -> None:
        self._verify_bound_integrity(recover_anchor=True)

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
                connection.execute("BEGIN IMMEDIATE")
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
                if self._workspace_id is not None:
                    self._append_ledger_event(
                        connection,
                        workspace_id=self._workspace_id,
                        audit_epoch=self._current_epoch(connection),
                        session_id=session_id,
                        event_type="session.create",
                        payload={"authority_digest": authority_digest(state)},
                        created_at=created_at,
                    )
                connection.commit()
            except sqlite3.IntegrityError as exc:
                connection.rollback()
                raise WorkspaceStorageError(f"session {session_id!r} already exists") from exc
            except Exception:
                connection.rollback()
                raise
        if self._workspace_id is not None:
            self._advance_anchor()

    def _save_session_state(
        self,
        connection: sqlite3.Connection,
        session_id: str,
        state: dict[str, Any],
        *,
        updated_at: str,
    ) -> None:
        cursor = connection.execute(
            "UPDATE sessions SET state_json = ?, updated_at = ? WHERE session_id = ?",
            (_json(state), updated_at, session_id),
        )
        if cursor.rowcount != 1:
            raise KeyError(f"unknown session id: {session_id}")
        self._sync_normalized(connection, session_id, state)

    def save_session(self, session_id: str, state: dict[str, Any], *, updated_at: str) -> None:
        self.initialize()
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._save_session_state(
                    connection, session_id, state, updated_at=updated_at
                )
                if self._workspace_id is not None:
                    self._append_ledger_event(
                        connection,
                        workspace_id=self._workspace_id,
                        audit_epoch=self._current_epoch(connection),
                        session_id=session_id,
                        event_type="runtime.session_commit",
                        payload=minimal_runtime_commit(state),
                        created_at=updated_at,
                    )
                connection.commit()
            except sqlite3.DatabaseError as exc:
                connection.rollback()
                if isinstance(exc, sqlite3.IntegrityError):
                    raise WorkspaceStorageError(f"cannot save session: {exc}") from exc
                raise
            except Exception:
                connection.rollback()
                raise
        if self._workspace_id is not None:
            self._advance_anchor()

    def authorized_request_result(
        self,
        request_id: str,
        *,
        event_type: str,
        session_id: str,
        seed_id: str,
    ) -> dict[str, Any] | None:
        self.initialize()
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM production_ledger WHERE request_id = ?", (request_id,)
            ).fetchone()
        if row is None:
            return None
        if (
            row["event_type"] != event_type
            or row["session_id"] != session_id
            or row["seed_id"] != seed_id
        ):
            raise WorkspaceStorageError(
                "request_id was already used for a different authority operation"
            )
        payload = json.loads(row["payload_json"])
        result = payload.get("operation_result")
        if not isinstance(result, dict):
            raise WorkspaceStorageError("stored authority operation result is invalid")
        return {**result, "idempotent_replay": True, "ledger_event_id": row["event_id"]}

    def save_authorized_session(
        self,
        session_id: str,
        state: dict[str, Any],
        *,
        updated_at: str,
        authorization: Mapping[str, Any],
        event_type: str,
        seed_id: str,
        operation_result: Mapping[str, Any],
        event_metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.initialize()
        if self._workspace_id is None:
            raise WorkspaceStorageError(
                "authorized production persistence requires a bound workspace"
            )
        request_id = str(authorization.get("request_id") or "").strip()
        actor_id = str(authorization.get("actor_id") or "").strip()
        actor_scope_id = str(authorization.get("scope_id") or "").strip()
        capability = str(authorization.get("capability") or "").strip()
        auth_method = str(authorization.get("auth_method") or "").strip()
        policy_version = str(authorization.get("policy_version") or "").strip()
        if not all(
            (request_id, actor_id, actor_scope_id, capability, auth_method, policy_version)
        ):
            raise WorkspaceStorageError("authorization metadata is incomplete")
        if actor_scope_id != self._workspace_id:
            raise WorkspaceStorageError("authorization scope does not match workspace")

        existing = self.authorized_request_result(
            request_id,
            event_type=event_type,
            session_id=session_id,
            seed_id=seed_id,
        )
        if existing is not None:
            return existing

        payload = {
            "operation_result": dict(operation_result),
            "runtime_commit": minimal_runtime_commit(state),
            "metadata": dict(event_metadata or {}),
        }
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                duplicate = connection.execute(
                    "SELECT * FROM production_ledger WHERE request_id = ?",
                    (request_id,),
                ).fetchone()
                if duplicate is not None:
                    connection.rollback()
                    return self.authorized_request_result(
                        request_id,
                        event_type=event_type,
                        session_id=session_id,
                        seed_id=seed_id,
                    ) or {}
                self._save_session_state(
                    connection, session_id, state, updated_at=updated_at
                )
                ledger = self._append_ledger_event(
                    connection,
                    workspace_id=self._workspace_id,
                    audit_epoch=self._current_epoch(connection),
                    session_id=session_id,
                    seed_id=seed_id,
                    event_type=event_type,
                    request_id=request_id,
                    actor_id=actor_id,
                    actor_scope_id=actor_scope_id,
                    capability=capability,
                    auth_method=auth_method,
                    policy_version=policy_version,
                    payload=payload,
                    created_at=updated_at,
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        self._advance_anchor()
        return {
            **dict(operation_result),
            "idempotent_replay": False,
            "ledger_event_id": ledger["event_id"],
            "ledger_sequence_no": ledger["sequence_no"],
            "ledger_event_hash": ledger["event_hash"],
        }

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
            config = json.loads(row["config_json"])
            state_config = dict(state.get("session_config", {}))
            runtime_mode = state_config.get("runtime_mode") or config.get(
                "runtime_mode", "evaluation"
            )
            if runtime_mode not in {"evaluation", "live"}:
                runtime_mode = "evaluation"
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
                    runtime_mode=runtime_mode,
                )
            )
        return summaries

    def delete_session(self, session_id: str) -> None:
        self.initialize()
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                if self._workspace_id is not None:
                    stored = connection.execute(
                        "SELECT state_json FROM sessions WHERE session_id = ?", (session_id,)
                    ).fetchone()
                    if stored is None:
                        raise KeyError(f"unknown session id: {session_id}")
                    state = json.loads(stored["state_json"])
                    self._append_ledger_event(
                        connection,
                        workspace_id=self._workspace_id,
                        audit_epoch=self._current_epoch(connection),
                        session_id=session_id,
                        event_type="session.delete",
                        payload={
                            "authority_digest_before_delete": authority_digest(state),
                            "content_removed": True,
                        },
                    )
                cursor = connection.execute(
                    "DELETE FROM sessions WHERE session_id = ?", (session_id,)
                )
                if cursor.rowcount != 1:
                    raise KeyError(f"unknown session id: {session_id}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        if self._workspace_id is not None:
            self._advance_anchor()

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
                    "production_ledger",
                    "tester_feedback",
                )
            }

    def backup_to(self, destination: str | Path) -> Path:
        self.initialize()
        if self._workspace_id is not None:
            self._verify_bound_integrity(recover_anchor=True)
        target = Path(destination).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        if temporary.exists():
            temporary.unlink()
        with self._connect() as source:
            destination_db = sqlite3.connect(temporary)
            try:
                source.backup(destination_db)
                destination_db.commit()
            finally:
                destination_db.close()
        with sqlite3.connect(f"file:{temporary}?mode=ro", uri=True) as candidate:
            check = candidate.execute("PRAGMA integrity_check").fetchone()
            if check is None or check[0] != "ok":
                temporary.unlink(missing_ok=True)
                raise WorkspaceStorageError("backup failed integrity check")
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
                check = connection.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.DatabaseError as exc:
            raise WorkspaceStorageError(f"backup is not a valid workspace database: {exc}") from exc
        if row is None or int(row[0]) > SCHEMA_VERSION:
            raise WorkspaceStorageError("backup schema is missing or unsupported")
        if check is None or check[0] != "ok":
            raise WorkspaceStorageError("backup failed integrity check")
        if self._workspace_id is not None:
            raise WorkspaceStorageError(
                "production restore requires the explicit audit-epoch recovery workflow"
            )
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.database_path.with_suffix(".restore.tmp")
        temporary.unlink(missing_ok=True)
        shutil.copy2(source_path, temporary)
        try:
            candidate = SQLiteWorkspaceRepository(temporary)
            candidate.initialize()
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        os.replace(temporary, self.database_path)
        self.initialize()

    def database_sha256(self) -> str:
        self.initialize()
        return _file_sha256(self.database_path)

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
