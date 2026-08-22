"""Explicit production backup restore and import workflows."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from shadowseed.storage.integrity import (
    AnchorState,
    authority_digest,
    create_integrity_key,
    key_id,
    verify_chain_rows,
    write_anchor,
)
from shadowseed.storage.production import verify_authority_snapshot_connection
from shadowseed.storage.schema import SCHEMA_VERSION
from shadowseed.storage.sqlite import WorkspaceStorageError


_MUTABLE_TABLE_COLUMNS: dict[str, tuple[str, ...]] = {
    "sessions": (
        "session_id",
        "title",
        "profile_id",
        "backend",
        "model_id",
        "config_json",
        "state_json",
        "created_at",
        "updated_at",
    ),
    "turns": (
        "session_id",
        "turn_index",
        "question",
        "answer",
        "baseline_answer",
        "ssl_answer",
        "report_json",
    ),
    "seeds": ("session_id", "seed_id", "snapshot_json"),
    "audit_events": (
        "session_id",
        "event_type",
        "event_key",
        "sequence_no",
        "payload_json",
    ),
    "tester_feedback": (
        "feedback_id",
        "session_id",
        "turn_index",
        "seed_id",
        "overall",
        "seed_effect",
        "note",
        "action",
        "created_at",
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _close_sqlite(connection: sqlite3.Connection | None) -> None:
    if connection is not None:
        connection.close()


def _read_backup(
    path: Path,
) -> tuple[str, dict[str, Any], dict[str, list[tuple[Any, ...]]]]:
    source: sqlite3.Connection | None = None
    workspace_id = ""
    report: dict[str, Any]
    rows: dict[str, list[tuple[Any, ...]]] = {}
    try:
        source = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        source.row_factory = sqlite3.Row
        check = source.execute("PRAGMA integrity_check").fetchone()
        if check is None or check[0] != "ok":
            raise ValueError("backup failed SQLite integrity check")
        version = source.execute(
            "SELECT value FROM workspace_meta WHERE key='schema_version'"
        ).fetchone()
        if version is None or int(version[0]) != SCHEMA_VERSION:
            raise ValueError("production restore requires a current-schema backup")
        workspace = source.execute(
            "SELECT value FROM workspace_meta WHERE key='workspace_id'"
        ).fetchone()
        if workspace is None:
            raise ValueError("backup has no production workspace identity")
        workspace_id = str(workspace[0])
        ledger_rows = [
            dict(row)
            for row in source.execute(
                "SELECT * FROM production_ledger ORDER BY sequence_no"
            ).fetchall()
        ]
        report = verify_chain_rows(ledger_rows)
        if report["event_count"] == 0:
            raise ValueError("backup has no production ledger genesis")
        if report["workspace_id"] != workspace_id:
            raise ValueError("backup ledger workspace identity mismatch")
        verify_authority_snapshot_connection(source)
        for table, columns in _MUTABLE_TABLE_COLUMNS.items():
            projection = ", ".join(columns)
            rows[table] = [
                tuple(row[column] for column in columns)
                for row in source.execute(f"SELECT {projection} FROM {table}").fetchall()
            ]
    except (sqlite3.DatabaseError, ValueError, WorkspaceStorageError) as exc:
        raise ValueError(f"backup is not a valid production workspace: {exc}") from exc
    finally:
        _close_sqlite(source)
    return workspace_id, report, rows


def inspect_production_backup(source: str | Path) -> dict[str, Any]:
    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"backup does not exist: {source_path}")
    workspace_id, report, _ = _read_backup(source_path)
    return {
        "workspace_id": workspace_id,
        "audit_epoch": report["audit_epoch"],
        "sequence_no": report["sequence_no"],
        "head_hash": report["head_hash"],
        "backup_sha256": _sha256(source_path),
    }


def _authority_snapshot(rows: list[tuple[Any, ...]]) -> list[dict[str, str]]:
    snapshot: list[dict[str, str]] = []
    session_columns = _MUTABLE_TABLE_COLUMNS["sessions"]
    state_index = session_columns.index("state_json")
    id_index = session_columns.index("session_id")
    for row in sorted(rows, key=lambda item: str(item[id_index])):
        state = json.loads(str(row[state_index]))
        snapshot.append(
            {
                "session_id": str(row[id_index]),
                "authority_digest": authority_digest(state),
            }
        )
    return snapshot


def _authority_baseline(rows: list[tuple[Any, ...]]) -> str:
    canonical = json.dumps(
        _authority_snapshot(rows),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _auth_fields(
    authorization: Mapping[str, Any],
    *,
    workspace_id: str,
) -> dict[str, str]:
    values = {
        "request_id": str(authorization.get("request_id") or "").strip(),
        "actor_id": str(authorization.get("actor_id") or "").strip(),
        "actor_scope_id": str(authorization.get("scope_id") or "").strip(),
        "capability": str(authorization.get("capability") or "").strip(),
        "auth_method": str(authorization.get("auth_method") or "").strip(),
        "policy_version": str(authorization.get("policy_version") or "").strip(),
    }
    if not all(values.values()):
        raise ValueError("recovery authorization metadata is incomplete")
    if values["actor_scope_id"] != workspace_id:
        raise ValueError("recovery authorization scope does not match workspace")
    return values


def _verify_and_seal_stage(
    stage: Path,
    *,
    label: str,
    expected_head_hash: str,
) -> dict[str, Any]:
    """Validate a recovery candidate completely before it can replace live state.

    The stage is checked for SQLite integrity, ledger-chain integrity and mutable
    authority snapshot consistency. It is then checkpointed out of WAL mode so the
    replacement is a single closed main-database file on Linux, macOS and Windows.
    """

    verification: sqlite3.Connection | None = None
    try:
        verification = sqlite3.connect(stage, timeout=10.0)
        verification.row_factory = sqlite3.Row
        verification.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        mode = verification.execute("PRAGMA journal_mode=DELETE").fetchone()
        if mode is None or str(mode[0]).lower() != "delete":
            raise ValueError(f"staged {label} could not leave WAL mode safely")
        check = verification.execute("PRAGMA integrity_check").fetchone()
        if check is None or check[0] != "ok":
            raise ValueError(f"staged {label} failed SQLite integrity check")
        report = verify_chain_rows(
            [
                dict(row)
                for row in verification.execute(
                    "SELECT * FROM production_ledger ORDER BY sequence_no"
                ).fetchall()
            ]
        )
        if report["head_hash"] != expected_head_hash:
            raise ValueError(f"staged {label} ledger head is inconsistent")
        verify_authority_snapshot_connection(verification)
        verification.commit()
    finally:
        _close_sqlite(verification)
    for suffix in ("-wal", "-shm"):
        Path(str(stage) + suffix).unlink(missing_ok=True)
    return report


def _prepare_live_replacement(database_path: Path) -> None:
    """Close WAL state cleanly before atomically replacing the live DB file."""

    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(database_path, timeout=10.0)
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        mode = connection.execute("PRAGMA journal_mode=DELETE").fetchone()
        if mode is None or str(mode[0]).lower() != "delete":
            raise ValueError("live workspace could not leave WAL mode for restore")
        connection.commit()
    finally:
        _close_sqlite(connection)
    for suffix in ("-wal", "-shm"):
        Path(str(database_path) + suffix).unlink(missing_ok=True)


def import_production_backup(
    repository: Any,
    source: str | Path,
    *,
    integrity_dir: str | Path,
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    """Import a verified backup on a machine without the previous protected anchor.

    The logical workspace identity and retained ledger are preserved, but a new local
    integrity key and audit epoch explicitly mark the cross-machine continuity break.
    """

    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"backup does not exist: {source_path}")
    workspace_id, backup_report, source_rows = _read_backup(source_path)
    auth = _auth_fields(authorization, workspace_id=workspace_id)
    if repository.database_path.exists() and repository.database_path.stat().st_size:
        raise ValueError("cross-machine import requires an empty target workspace")

    integrity_path = Path(integrity_dir).expanduser().resolve()
    key_path = integrity_path / "integrity.key"
    anchor_path = integrity_path / "anchor.json"
    key = create_integrity_key(key_path)
    stage = repository.database_path.with_suffix(".import-stage")
    stage.parent.mkdir(parents=True, exist_ok=True)
    stage.unlink(missing_ok=True)
    shutil.copy2(source_path, stage)
    new_epoch = f"epoch::{uuid4()}"
    try:
        candidate = repository.__class__(stage)
        with candidate._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    "INSERT OR REPLACE INTO workspace_meta(key, value) VALUES('audit_epoch', ?)",
                    (new_epoch,),
                )
                event = candidate._append_ledger_event(
                    connection,
                    workspace_id=workspace_id,
                    audit_epoch=new_epoch,
                    event_type="workspace.import",
                    payload={
                        "continuity_break": True,
                        "previous_anchor_available": False,
                        "backup_sha256": _sha256(source_path),
                        "backup_epoch": backup_report["audit_epoch"],
                        "backup_sequence_no": backup_report["sequence_no"],
                        "backup_head_hash": backup_report["head_hash"],
                        "imported_authority_baseline": _authority_baseline(
                            source_rows["sessions"]
                        ),
                        "authority_snapshot": _authority_snapshot(source_rows["sessions"]),
                    },
                    **auth,
                    created_at=datetime.now().isoformat(),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        report = _verify_and_seal_stage(
            stage,
            label="import",
            expected_head_hash=str(event["event_hash"]),
        )
        os.replace(stage, repository.database_path)
        repository._workspace_id = workspace_id
        repository._integrity_dir = integrity_path
        repository._anchor_path = anchor_path
        repository._key_path = key_path
        write_anchor(
            anchor_path,
            AnchorState(
                workspace_id=workspace_id,
                audit_epoch=new_epoch,
                sequence_no=int(report["sequence_no"]),
                head_hash=str(report["head_hash"]),
                key_id=key_id(key),
            ),
            key,
        )
        repository.verify_production_integrity()
        return {
            "workspace_id": workspace_id,
            "audit_epoch": new_epoch,
            "ledger_event_id": event["event_id"],
            "ledger_sequence_no": event["sequence_no"],
            "ledger_event_hash": event["event_hash"],
            "continuity_break": True,
            "authorization": dict(authorization),
        }
    except Exception:
        stage.unlink(missing_ok=True)
        for suffix in ("-wal", "-shm"):
            Path(str(stage) + suffix).unlink(missing_ok=True)
        if not repository.database_path.exists():
            shutil.rmtree(integrity_path, ignore_errors=True)
        raise


def restore_production_backup(
    repository: Any,
    source: str | Path,
    *,
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    """Restore mutable state from an older same-workspace backup into a new audit epoch.

    The current append-only ledger is preserved. The restore event commits to the
    verified backup head and restored authority baseline, so an intentional rollback
    is distinguishable from replacement by an old database file.
    """

    source_path = Path(source).expanduser().resolve()
    if not source_path.is_file():
        raise ValueError(f"backup does not exist: {source_path}")
    live = repository.verify_production_integrity()
    workspace_id = getattr(repository, "_workspace_id", None)
    if not workspace_id:
        raise ValueError("production restore requires a bound workspace")
    auth = _auth_fields(authorization, workspace_id=workspace_id)
    backup_workspace, backup_report, source_rows = _read_backup(source_path)
    if backup_workspace != workspace_id:
        raise ValueError("backup belongs to a different workspace identity")

    stage = repository.database_path.with_suffix(".restore-stage")
    stage.unlink(missing_ok=True)
    repository.backup_to(stage)
    new_epoch = f"epoch::{uuid4()}"
    try:
        candidate = repository.__class__(stage)
        with candidate._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                for table in (
                    "tester_feedback",
                    "audit_events",
                    "seeds",
                    "turns",
                    "sessions",
                ):
                    connection.execute(f"DELETE FROM {table}")
                for table in (
                    "sessions",
                    "turns",
                    "seeds",
                    "audit_events",
                    "tester_feedback",
                ):
                    columns = _MUTABLE_TABLE_COLUMNS[table]
                    rows = source_rows[table]
                    if not rows:
                        continue
                    placeholders = ", ".join("?" for _ in columns)
                    connection.executemany(
                        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})",
                        rows,
                    )
                connection.execute(
                    "INSERT OR REPLACE INTO workspace_meta(key, value) VALUES('audit_epoch', ?)",
                    (new_epoch,),
                )
                event = candidate._append_ledger_event(
                    connection,
                    workspace_id=workspace_id,
                    audit_epoch=new_epoch,
                    event_type="workspace.restore",
                    payload={
                        "backup_sha256": _sha256(source_path),
                        "backup_epoch": backup_report["audit_epoch"],
                        "backup_sequence_no": backup_report["sequence_no"],
                        "backup_head_hash": backup_report["head_hash"],
                        "previous_live_epoch": live["audit_epoch"],
                        "previous_live_sequence_no": live["sequence_no"],
                        "previous_live_head_hash": live["head_hash"],
                        "restored_authority_baseline": _authority_baseline(
                            source_rows["sessions"]
                        ),
                        "authority_snapshot": _authority_snapshot(source_rows["sessions"]),
                    },
                    **auth,
                    created_at=datetime.now().isoformat(),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        report = _verify_and_seal_stage(
            stage,
            label="restore",
            expected_head_hash=str(event["event_hash"]),
        )
        _prepare_live_replacement(repository.database_path)
        os.replace(stage, repository.database_path)
        repository._advance_anchor()
        return {
            "workspace_id": workspace_id,
            "audit_epoch": new_epoch,
            "ledger_event_id": event["event_id"],
            "ledger_sequence_no": event["sequence_no"],
            "ledger_event_hash": event["event_hash"],
            "backup_head_hash": backup_report["head_hash"],
            "authorization": dict(authorization),
        }
    except Exception:
        stage.unlink(missing_ok=True)
        for suffix in ("-wal", "-shm"):
            Path(str(stage) + suffix).unlink(missing_ok=True)
        raise
