from __future__ import annotations

import json
import shutil
import sqlite3
import threading
from pathlib import Path

import pytest

from shadowseed.application.auth import ActorContext, EVIDENCE_VERIFY
from shadowseed.application.workspace import WorkspaceService
from shadowseed.storage.integrity import canonical_json, event_digest
from shadowseed.storage.production import ProductionSQLiteWorkspaceRepository
from shadowseed.storage.schema import SCHEMA_VERSION
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError
from shadowseed.workbench.controller import WorkbenchController


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


def _live_seed(controller: WorkbenchController) -> tuple[str, str]:
    session_id = controller.create_session(
        title="Phase 3 live",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What is missing from this privacy plan?")
    return session_id, result["session"]["seeds"][0]["id"]


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



def test_v1_interrupted_bootstrap_replays_protected_payload_without_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "workspace.id").write_text("workspace::legacy\n", encoding="utf-8")
    _create_v1_workspace(root / "workspace.db")
    workspace = WorkspaceService(root)

    def interrupt_genesis(*, workspace_id: str, bootstrap_actor_id: str) -> None:
        del workspace_id, bootstrap_actor_id
        raise RuntimeError("synthetic v1 pre-genesis interruption")

    monkeypatch.setattr(
        workspace.repository, "_create_production_genesis", interrupt_genesis
    )
    with pytest.raises(RuntimeError, match="synthetic v1 pre-genesis interruption"):
        workspace.initialize()

    workspace_id = workspace._read_workspace_id()
    marker = workspace._integrity_dir(workspace_id) / "bootstrap.pending"
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    planned_payload = marker_payload["bootstrap_payload"]
    backup = root / "workspace.db.pre-migration-v1-to-v2.bak"
    assert planned_payload["pre_production_history"] is True
    assert len(planned_payload["source_database_sha256"]) == 64
    backup.unlink()

    reopened = WorkspaceService(root)
    reopened.initialize()
    with sqlite3.connect(reopened.paths.database) as connection:
        committed = json.loads(
            connection.execute(
                "SELECT payload_json FROM production_ledger WHERE sequence_no = 1"
            ).fetchone()[0]
        )
    assert committed == planned_payload
    assert not marker.exists()



def test_interrupted_bootstrap_rejects_live_authority_baseline_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "workspace.id").write_text("workspace::legacy\n", encoding="utf-8")
    _create_v1_workspace(root / "workspace.db")
    workspace = WorkspaceService(root)

    def interrupt_genesis(*, workspace_id: str, bootstrap_actor_id: str) -> None:
        del workspace_id, bootstrap_actor_id
        raise RuntimeError("synthetic pre-genesis interruption")

    monkeypatch.setattr(
        workspace.repository, "_create_production_genesis", interrupt_genesis
    )
    with pytest.raises(RuntimeError, match="synthetic pre-genesis interruption"):
        workspace.initialize()

    workspace_id = workspace._read_workspace_id()
    integrity_dir = workspace._integrity_dir(workspace_id)
    marker = integrity_dir / "bootstrap.pending"
    assert marker.is_file()
    with sqlite3.connect(root / "workspace.db") as connection:
        connection.execute(
            "UPDATE sessions SET state_json = ? WHERE session_id = 'session::legacy'",
            (
                json.dumps(
                    {
                        "turn": 0,
                        "manager": {
                            "seeds": [
                                {
                                    "id": "seed::forged",
                                    "status": "active",
                                    "weight": 1.0,
                                    "trace": [],
                                    "authority_version": 1,
                                    "evidence_count": 0,
                                }
                            ]
                        },
                    }
                ),
            ),
        )

    reopened = WorkspaceService(root)
    with pytest.raises(WorkspaceStorageError, match="authority baseline changed"):
        reopened.initialize()

    with sqlite3.connect(root / "workspace.db") as connection:
        ledger_count = connection.execute(
            "SELECT COUNT(*) FROM production_ledger"
        ).fetchone()[0]
    assert ledger_count == 0
    assert marker.is_file()
    assert not (integrity_dir / "anchor.json").exists()


def test_production_bind_holds_bootstrap_lock_through_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    database = tmp_path / "workspace.db"
    integrity_dir = tmp_path / "integrity"
    repository = ProductionSQLiteWorkspaceRepository(database)
    original = ProductionSQLiteWorkspaceRepository._ensure_authority_checkpoint
    observations: list[bool] = []

    def checked_checkpoint(
        self: ProductionSQLiteWorkspaceRepository, *, bootstrap_actor_id: str
    ) -> None:
        assert self._integrity_dir is not None
        probe = sqlite3.connect(
            self._integrity_dir / "bootstrap.lock", timeout=0.0, isolation_level=None
        )
        acquired = False
        try:
            try:
                probe.execute("BEGIN EXCLUSIVE")
                acquired = True
                probe.rollback()
            except sqlite3.OperationalError as exc:
                if "locked" not in str(exc).lower():
                    raise
        finally:
            probe.close()
        observations.append(not acquired)
        if acquired:
            raise AssertionError(
                "bootstrap lock was released before authority checkpoint publication"
            )
        original(self, bootstrap_actor_id=bootstrap_actor_id)

    monkeypatch.setattr(
        ProductionSQLiteWorkspaceRepository,
        "_ensure_authority_checkpoint",
        checked_checkpoint,
    )
    report = repository.bind_production(
        workspace_id="workspace::lock-boundary",
        integrity_dir=integrity_dir,
        bootstrap_actor_id="local-owner::lock-boundary",
    )

    assert observations == [True]
    assert report["authority_snapshot_verified"] is True
    assert (integrity_dir / "anchor.json").is_file()


def test_concurrent_production_bind_serializes_bootstrap(tmp_path: Path) -> None:
    database = tmp_path / "workspace.db"
    seed_repository = ProductionSQLiteWorkspaceRepository(database)
    seed_repository.initialize()
    first = ProductionSQLiteWorkspaceRepository(database)
    second = ProductionSQLiteWorkspaceRepository(database)
    workspace_id = "workspace::concurrent"
    bootstrap_actor_id = "local-owner::concurrent"
    integrity_dir = tmp_path / "integrity"
    barrier = threading.Barrier(2)
    reports: list[dict[str, object]] = []
    errors: list[BaseException] = []

    def bind(repository: ProductionSQLiteWorkspaceRepository) -> None:
        try:
            barrier.wait(timeout=5)
            reports.append(
                repository.bind_production(
                    workspace_id=workspace_id,
                    integrity_dir=integrity_dir,
                    bootstrap_actor_id=bootstrap_actor_id,
                )
            )
        except BaseException as exc:
            errors.append(exc)

    threads = [
        threading.Thread(target=bind, args=(first,)),
        threading.Thread(target=bind, args=(second,)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=20)

    assert all(not thread.is_alive() for thread in threads)
    assert errors == []
    assert len(reports) == 2
    with sqlite3.connect(database) as connection:
        events = connection.execute(
            "SELECT event_type, COUNT(*) FROM production_ledger "
            "GROUP BY event_type ORDER BY event_type"
        ).fetchall()
    assert events == [
        ("production.authority_checkpoint", 1),
        ("production.bootstrap", 1),
    ]
    assert not (integrity_dir / "bootstrap.pending").exists()


def test_v1_product_bootstrap_creates_explicit_preproduction_genesis(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "workspace.id").write_text("workspace::legacy\n", encoding="utf-8")
    _create_v1_workspace(root / "workspace.db")

    workspace = WorkspaceService(root)
    workspace.initialize()

    with sqlite3.connect(root / "workspace.db") as connection:
        connection.row_factory = sqlite3.Row
        meta = dict(connection.execute("SELECT key, value FROM workspace_meta").fetchall())
        rows = connection.execute(
            "SELECT * FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
    assert meta["workspace_id"] == "workspace::legacy"
    assert meta["audit_epoch"].startswith("epoch::")
    assert [row["event_type"] for row in rows] == [
        "production.bootstrap",
        "production.authority_checkpoint",
    ]
    payload = json.loads(rows[0]["payload_json"])
    assert payload["pre_production_history"] is True
    assert payload["source_schema_version"] == 1
    assert len(payload["source_database_sha256"]) == 64
    report = workspace.repository.verify_production_integrity()
    assert report["event_count"] == 2
    assert report["authority_snapshot_verified"] is True


def test_new_product_workspace_binds_identity_and_anchor_outside_workspace(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    workspace = WorkspaceService(root)
    workspace.initialize()
    workspace_id = workspace.workspace_id

    integrity_dir = workspace._integrity_dir(workspace_id)
    assert (integrity_dir / "integrity.key").is_file()
    assert (integrity_dir / "anchor.json").is_file()
    assert not (root / "integrity.key").exists()

    report = workspace.repository.verify_production_integrity()
    assert report["workspace_id"] == workspace_id
    assert report["event_count"] == 2
    assert report["authority_snapshot_verified"] is True
    assert report["sequence_no"] == report["anchor_sequence_no"]


def test_authorized_evidence_is_atomic_attributable_and_content_minimized(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    actor = controller.workspace.local_actor_context(request_id="request::phase3-evidence")
    source_ref = "reviewer:phase3-secret-ref"
    note = "private evidence note that must not enter the production ledger"

    result = controller.sessions.submit_verified_evidence_authorized(
        session_id,
        seed_id,
        source_ref=source_ref,
        note=note,
        actor=actor,
    )

    assert result["authorization"]["actor_id"] == actor.actor_id
    assert result["authorization"]["capability"] == EVIDENCE_VERIFY
    assert result["idempotent_replay"] is False
    assert result["ledger_event_id"].startswith("ledger::")

    with sqlite3.connect(controller.workspace.paths.database) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute(
            "SELECT * FROM production_ledger WHERE request_id = ?", (actor.request_id,)
        ).fetchone()
    assert row is not None
    assert row["actor_id"] == actor.actor_id
    assert row["actor_scope_id"] == actor.scope_id
    assert row["capability"] == EVIDENCE_VERIFY
    assert row["auth_method"] == actor.auth_method
    assert row["policy_version"] == actor.policy_version
    assert source_ref not in row["payload_json"]
    assert note not in row["payload_json"]
    payload = json.loads(row["payload_json"])
    assert len(payload["metadata"]["source_ref_sha256"]) == 64
    assert len(payload["metadata"]["note_sha256"]) == 64


def test_authorized_retry_does_not_double_apply_evidence(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    actor = controller.workspace.local_actor_context(request_id="request::retry")

    first = controller.sessions.submit_verified_evidence_authorized(
        session_id,
        seed_id,
        source_ref="reviewer:retry",
        actor=actor,
    )
    before = controller.session_view(session_id)
    second = controller.sessions.submit_verified_evidence_authorized(
        session_id,
        seed_id,
        source_ref="reviewer:retry",
        actor=actor,
    )
    after = controller.session_view(session_id)

    assert first["idempotent_replay"] is False
    assert second["idempotent_replay"] is True
    assert second["ledger_event_id"] == first["ledger_event_id"]
    assert before == after
    with sqlite3.connect(controller.workspace.paths.database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM production_ledger WHERE request_id = ?", (actor.request_id,)
        ).fetchone()[0]
    assert count == 1


def test_authorized_ledger_failure_rolls_back_session_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, seed_id = _live_seed(controller)
    actor = controller.workspace.local_actor_context(request_id="request::rollback")
    before = controller.sessions.load(session_id)["state"]
    original = controller.workspace.repository._append_ledger_event

    def fail_authority_append(*args, **kwargs):
        if kwargs.get("request_id") == actor.request_id:
            raise RuntimeError("synthetic ledger failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(
        controller.workspace.repository, "_append_ledger_event", fail_authority_append
    )
    with pytest.raises(RuntimeError, match="synthetic ledger failure"):
        controller.sessions.submit_verified_evidence_authorized(
            session_id,
            seed_id,
            source_ref="reviewer:rollback",
            actor=actor,
        )

    after = controller.sessions.load(session_id)["state"]
    assert after == before
    with sqlite3.connect(controller.workspace.paths.database) as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM production_ledger WHERE request_id = ?", (actor.request_id,)
        ).fetchone()[0]
    assert count == 0


def test_ledger_payload_mutation_fails_verification(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    workspace.initialize()
    with sqlite3.connect(workspace.paths.database) as connection:
        connection.execute(
            "UPDATE production_ledger SET payload_json = '{}' WHERE sequence_no = 1"
        )

    with pytest.raises(WorkspaceStorageError, match="event hash mismatch"):
        workspace.repository.verify_production_integrity()


def test_ledger_deletion_fails_verification(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    _live_seed(controller)
    with sqlite3.connect(controller.workspace.paths.database) as connection:
        connection.execute("DELETE FROM production_ledger WHERE sequence_no = 1")

    with pytest.raises(WorkspaceStorageError, match="sequence discontinuity"):
        controller.workspace.repository.verify_production_integrity()


def test_ledger_reordering_fails_verification(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    _live_seed(controller)
    with sqlite3.connect(controller.workspace.paths.database) as connection:
        rows = connection.execute(
            "SELECT sequence_no FROM production_ledger ORDER BY sequence_no LIMIT 2"
        ).fetchall()
        assert len(rows) == 2
        connection.execute(
            "UPDATE production_ledger SET sequence_no = -1 WHERE sequence_no = ?",
            (rows[0][0],),
        )
        connection.execute(
            "UPDATE production_ledger SET sequence_no = ? WHERE sequence_no = ?",
            (rows[0][0], rows[1][0]),
        )
        connection.execute(
            "UPDATE production_ledger SET sequence_no = ? WHERE sequence_no = -1",
            (rows[1][0],),
        )

    with pytest.raises(WorkspaceStorageError, match="verification failed"):
        controller.workspace.repository.verify_production_integrity()


def test_session_delete_removes_content_but_preserves_minimal_tombstone(tmp_path: Path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id, _ = _live_seed(controller)
    state_before = controller.sessions.load(session_id)["state"]
    raw_content = state_before["turn_reports"][0]["question"]

    controller.sessions.delete_session(session_id)

    with sqlite3.connect(controller.workspace.paths.database) as connection:
        session = connection.execute(
            "SELECT 1 FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        tombstone = connection.execute(
            "SELECT payload_json FROM production_ledger "
            "WHERE event_type='session.delete' AND session_id = ? "
            "ORDER BY sequence_no DESC LIMIT 1",
            (session_id,),
        ).fetchone()
    assert session is None
    assert tombstone is not None
    assert raw_content not in tombstone[0]
    payload = json.loads(tombstone[0])
    assert payload["content_removed"] is True
    assert len(payload["authority_digest_before_delete"]) == 64


def test_missing_protected_anchor_fails_closed_instead_of_recreating(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    workspace = WorkspaceService(root)
    workspace.initialize()
    workspace_id = workspace.workspace_id
    anchor = workspace._integrity_dir(workspace_id) / "anchor.json"
    anchor.unlink()

    reopened = WorkspaceService(root)
    with pytest.raises(WorkspaceStorageError, match="integrity material is missing"):
        reopened.initialize()
    assert not anchor.exists()


def test_interrupted_initial_bootstrap_is_retryable_without_resetting_continuity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    workspace = WorkspaceService(root)
    import shadowseed.storage.integrity as integrity_storage

    durability_barriers: list[Path] = []
    protected_file_barriers: list[Path] = []
    original_fsync_directory = SQLiteWorkspaceRepository._fsync_directory
    original_fsync_parent = integrity_storage._fsync_parent_directory

    def record_fsync_directory(path: Path) -> None:
        durability_barriers.append(path)
        original_fsync_directory(path)

    def record_fsync_parent(path: Path) -> None:
        protected_file_barriers.append(path)
        original_fsync_parent(path)

    monkeypatch.setattr(
        SQLiteWorkspaceRepository,
        "_fsync_directory",
        staticmethod(record_fsync_directory),
    )
    monkeypatch.setattr(
        integrity_storage, "_fsync_parent_directory", record_fsync_parent
    )

    def interrupt_genesis(*, workspace_id: str, bootstrap_actor_id: str) -> None:
        del workspace_id, bootstrap_actor_id
        raise RuntimeError("synthetic pre-genesis interruption")

    monkeypatch.setattr(
        workspace.repository, "_create_production_genesis", interrupt_genesis
    )
    with pytest.raises(RuntimeError, match="synthetic pre-genesis interruption"):
        workspace.initialize()

    workspace_id = workspace._read_workspace_id()
    integrity_dir = workspace._integrity_dir(workspace_id)
    key = integrity_dir / "integrity.key"
    anchor = integrity_dir / "anchor.json"
    marker = integrity_dir / "bootstrap.pending"
    key_before = key.read_bytes()
    assert not anchor.exists()
    with sqlite3.connect(workspace.paths.database) as connection:
        ledger_count = connection.execute(
            "SELECT COUNT(*) FROM production_ledger"
        ).fetchone()[0]
    assert ledger_count == 0
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_payload["workspace_id"] == workspace_id
    assert len(marker_payload["expected_genesis_hash"]) == 64
    integrity_location = integrity_dir.parent
    integrity_root = integrity_location.parent
    assert integrity_dir in durability_barriers
    assert integrity_location in durability_barriers
    assert integrity_root in durability_barriers
    assert integrity_root.parent in durability_barriers
    assert protected_file_barriers == [key]

    reopened = WorkspaceService(root)
    reopened.initialize()

    assert key.read_bytes() == key_before
    assert anchor.is_file()
    assert not marker.exists()
    assert durability_barriers[-1] == integrity_dir
    assert protected_file_barriers[0] == key
    assert protected_file_barriers[1:]
    assert all(path == anchor for path in protected_file_barriers[1:])
    assert reopened.repository.verify_production_integrity()["sequence_no"] >= 2


def test_interrupted_bootstrap_after_genesis_reseals_before_normal_use(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shadowseed.storage.sqlite as sqlite_storage

    root = tmp_path / "workspace"
    workspace = WorkspaceService(root)
    original_write_anchor = sqlite_storage.write_anchor

    def interrupt_anchor(*args, **kwargs) -> None:
        del args, kwargs
        raise OSError("synthetic post-genesis interruption")

    monkeypatch.setattr(sqlite_storage, "write_anchor", interrupt_anchor)
    with pytest.raises(OSError, match="synthetic post-genesis interruption"):
        workspace.initialize()

    workspace_id = workspace._read_workspace_id()
    integrity_dir = workspace._integrity_dir(workspace_id)
    key = integrity_dir / "integrity.key"
    anchor = integrity_dir / "anchor.json"
    marker = integrity_dir / "bootstrap.pending"
    key_before = key.read_bytes()
    assert not anchor.exists()
    with sqlite3.connect(workspace.paths.database) as connection:
        events = connection.execute(
            "SELECT event_type FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
    assert events == [("production.bootstrap",)]
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert marker_payload["workspace_id"] == workspace_id
    with sqlite3.connect(workspace.paths.database) as connection:
        committed_hash = connection.execute(
            "SELECT event_hash FROM production_ledger WHERE sequence_no = 1"
        ).fetchone()[0]
    assert committed_hash == marker_payload["expected_genesis_hash"]

    monkeypatch.setattr(sqlite_storage, "write_anchor", original_write_anchor)
    reopened = WorkspaceService(root)
    reopened.initialize()

    assert key.read_bytes() == key_before
    assert anchor.is_file()
    assert not marker.exists()
    assert reopened.repository.verify_production_integrity()["sequence_no"] >= 2



def test_interrupted_bootstrap_after_genesis_rejects_live_authority_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shadowseed.storage.sqlite as sqlite_storage

    root = tmp_path / "workspace"
    root.mkdir()
    (root / "workspace.id").write_text("workspace::legacy\n", encoding="utf-8")
    _create_v1_workspace(root / "workspace.db")
    workspace = WorkspaceService(root)
    original_write_anchor = sqlite_storage.write_anchor

    def interrupt_anchor(*args, **kwargs) -> None:
        del args, kwargs
        raise OSError("synthetic post-genesis interruption")

    monkeypatch.setattr(sqlite_storage, "write_anchor", interrupt_anchor)
    with pytest.raises(OSError, match="synthetic post-genesis interruption"):
        workspace.initialize()

    workspace_id = workspace._read_workspace_id()
    integrity_dir = workspace._integrity_dir(workspace_id)
    marker = integrity_dir / "bootstrap.pending"
    anchor = integrity_dir / "anchor.json"
    assert marker.is_file()
    assert not anchor.exists()

    with sqlite3.connect(root / "workspace.db") as connection:
        events = connection.execute(
            "SELECT event_type FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
        assert events == [("production.bootstrap",)]
        connection.execute(
            "UPDATE sessions SET state_json = ? WHERE session_id = 'session::legacy'",
            (
                json.dumps(
                    {
                        "turn": 0,
                        "manager": {
                            "seeds": [
                                {
                                    "id": "seed::post-genesis-forged",
                                    "status": "active",
                                    "weight": 1.0,
                                    "trace": [],
                                    "authority_version": 1,
                                    "evidence_count": 0,
                                }
                            ]
                        },
                    }
                ),
            ),
        )
        connection.commit()

    monkeypatch.setattr(sqlite_storage, "write_anchor", original_write_anchor)
    reopened = WorkspaceService(root)
    with pytest.raises(WorkspaceStorageError, match="authority baseline changed"):
        reopened.initialize()

    assert marker.is_file()
    assert not anchor.exists()
    with sqlite3.connect(root / "workspace.db") as connection:
        events = connection.execute(
            "SELECT event_type FROM production_ledger ORDER BY sequence_no"
        ).fetchall()
    assert events == [("production.bootstrap",)]


def test_interrupted_bootstrap_rejects_rewritten_genesis_before_reseal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shadowseed.storage.sqlite as sqlite_storage

    root = tmp_path / "workspace"
    workspace = WorkspaceService(root)
    original_write_anchor = sqlite_storage.write_anchor

    def interrupt_anchor(*args, **kwargs) -> None:
        del args, kwargs
        raise OSError("synthetic post-genesis interruption")

    monkeypatch.setattr(sqlite_storage, "write_anchor", interrupt_anchor)
    with pytest.raises(OSError, match="synthetic post-genesis interruption"):
        workspace.initialize()

    workspace_id = workspace._read_workspace_id()
    integrity_dir = workspace._integrity_dir(workspace_id)
    anchor = integrity_dir / "anchor.json"
    marker = integrity_dir / "bootstrap.pending"
    marker_payload = json.loads(marker.read_text(encoding="utf-8"))
    assert not anchor.exists()

    with sqlite3.connect(workspace.paths.database) as connection:
        connection.row_factory = sqlite3.Row
        row = dict(
            connection.execute(
                "SELECT * FROM production_ledger WHERE sequence_no = 1"
            ).fetchone()
        )
        payload = json.loads(row["payload_json"])
        payload["authority_baseline"] = "f" * 64
        row["payload_json"] = canonical_json(payload)
        digest_input = {
            key: value for key, value in row.items() if key != "event_hash"
        }
        rewritten_hash = event_digest(digest_input)
        assert rewritten_hash != marker_payload["expected_genesis_hash"]
        connection.execute(
            "UPDATE production_ledger SET payload_json = ?, event_hash = ? "
            "WHERE sequence_no = 1",
            (row["payload_json"], rewritten_hash),
        )
        connection.commit()

    monkeypatch.setattr(sqlite_storage, "write_anchor", original_write_anchor)
    reopened = WorkspaceService(root)
    with pytest.raises(
        WorkspaceStorageError, match="protected genesis commitment"
    ):
        reopened.initialize()
    assert not anchor.exists()
    assert marker.exists()


def test_empty_replacement_database_cannot_reset_protected_history(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    workspace = WorkspaceService(root)
    workspace.initialize()
    workspace_id = workspace.workspace_id

    integrity_dir = workspace._integrity_dir(workspace_id)
    key = integrity_dir / "integrity.key"
    anchor = integrity_dir / "anchor.json"
    key_before = key.read_bytes()
    anchor_before = anchor.read_bytes()

    database = workspace.paths.database
    Path(str(database) + "-wal").unlink(missing_ok=True)
    Path(str(database) + "-shm").unlink(missing_ok=True)
    database.unlink()
    sqlite3.connect(database).close()

    reopened = WorkspaceService(root)
    with pytest.raises(WorkspaceStorageError, match="protected integrity material exists"):
        reopened.initialize()

    marker = integrity_dir / "bootstrap.pending"
    assert key.read_bytes() == key_before
    assert anchor.read_bytes() == anchor_before
    with sqlite3.connect(database) as connection:
        ledger_count = connection.execute(
            "SELECT COUNT(*) FROM production_ledger"
        ).fetchone()[0]
    assert ledger_count == 0
    assert not marker.exists()

    anchor.unlink()
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO workspace_meta(key, value) VALUES(?, ?)",
            ("production_bootstrap_pending", workspace_id),
        )
        connection.commit()
    key_only_reopen = WorkspaceService(root)
    with pytest.raises(WorkspaceStorageError, match="protected integrity material exists"):
        key_only_reopen.initialize()
    assert key.read_bytes() == key_before
    assert not marker.exists()


def test_old_valid_backup_cannot_silently_replace_newer_live_workspace(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    controller = WorkbenchController(root)
    session_id, _ = _live_seed(controller)
    backup = tmp_path / "older.db"
    controller.workspace.backup(backup)

    controller.send_turn(session_id, "Add a newer committed turn")
    current = controller.workspace.repository.verify_production_integrity()

    Path(str(controller.workspace.paths.database) + "-wal").unlink(missing_ok=True)
    Path(str(controller.workspace.paths.database) + "-shm").unlink(missing_ok=True)
    shutil.copy2(backup, controller.workspace.paths.database)

    reopened = WorkspaceService(root)
    with pytest.raises(WorkspaceStorageError, match="behind the protected anchor"):
        reopened.initialize()
    assert current["sequence_no"] > 1


def test_database_ahead_of_anchor_recovers_only_valid_chain_extension(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    workspace.initialize()
    workspace_id = workspace.workspace_id
    before = workspace.repository.verify_production_integrity()

    with workspace.repository._connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        workspace.repository._append_ledger_event(
            connection,
            workspace_id=workspace_id,
            audit_epoch=str(before["audit_epoch"]),
            event_type="test.crash_after_db_commit",
            payload={"content_minimized": True},
        )
        connection.commit()

    recovered = workspace.repository.verify_production_integrity()
    assert recovered["sequence_no"] == before["sequence_no"] + 1
    assert recovered["anchor_sequence_no"] == recovered["sequence_no"]


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
