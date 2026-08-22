"""Explicit production backup restore workflow preserving ledger continuity."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from shadowseed.storage.integrity import authority_digest, verify_chain_rows
from shadowseed.storage.schema import SCHEMA_VERSION


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


def _read_backup(path: Path) -> tuple[str, dict[str, Any], dict[str, list[tuple[Any, ...]]]]:
    try:
        with sqlite3.connect(f"file:{path}?mode=ro", uri=True) as source:
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
            ledger_rows = [
                dict(row)
                for row in source.execute(
                    "SELECT * FROM production_ledger ORDER BY sequence_no"
                ).fetchall()
            ]
            report = verify_chain_rows(ledger_rows)
            if report["event_count"] == 0:
                raise ValueError("backup has no production ledger genesis")
            if report["workspace_id"] != workspace[0]:
                raise ValueError("backup ledger workspace identity mismatch")
            rows: dict[str, list[tuple[Any, ...]]] = {}
            for table, columns in _MUTABLE_TABLE_COLUMNS.items():
                projection = ", ".join(columns)
                rows[table] = [
                    tuple(row[column] for column in columns)
                    for row in source.execute(f"SELECT {projection} FROM {table}").fetchall()
                ]
    except (sqlite3.DatabaseError, ValueError) as exc:
        raise ValueError(f"backup is not a valid production workspace: {exc}") from exc
    return str(workspace[0]), report, rows


def _authority_baseline(rows: list[tuple[Any, ...]]) -> str:
    baseline: list[dict[str, str]] = []
    session_columns = _MUTABLE_TABLE_COLUMNS["sessions"]
    state_index = session_columns.index("state_json")
    id_index = session_columns.index("session_id")
    for row in sorted(rows, key=lambda item: str(item[id_index])):
        state = json.loads(str(row[state_index]))
        baseline.append(
            {
                "session_id": str(row[id_index]),
                "authority_digest": authority_digest(state),
            }
        )
    canonical = json.dumps(
        baseline, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def restore_production_backup(repository: Any, source: str | Path) -> dict[str, Any]:
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
                    },
                    created_at=datetime.now().isoformat(),
                )
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        with sqlite3.connect(f"file:{stage}?mode=ro", uri=True) as verification:
            verification.row_factory = sqlite3.Row
            check = verification.execute("PRAGMA integrity_check").fetchone()
            if check is None or check[0] != "ok":
                raise ValueError("staged restore failed SQLite integrity check")
            report = verify_chain_rows(
                [
                    dict(row)
                    for row in verification.execute(
                        "SELECT * FROM production_ledger ORDER BY sequence_no"
                    ).fetchall()
                ]
            )
        if report["head_hash"] != event["event_hash"]:
            raise ValueError("staged restore ledger head is inconsistent")
        for suffix in ("-wal", "-shm"):
            Path(str(repository.database_path) + suffix).unlink(missing_ok=True)
        os.replace(stage, repository.database_path)
        repository._advance_anchor()
        return {
            "workspace_id": workspace_id,
            "audit_epoch": new_epoch,
            "ledger_event_id": event["event_id"],
            "ledger_sequence_no": event["sequence_no"],
            "ledger_event_hash": event["event_hash"],
            "backup_head_hash": backup_report["head_hash"],
        }
    except Exception:
        stage.unlink(missing_ok=True)
        raise
