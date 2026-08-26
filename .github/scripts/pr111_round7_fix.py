from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"guard not found: {label}")
    return text.replace(old, new, 1)


sqlite_path = Path("src/shadowseed/storage/sqlite.py")
text = sqlite_path.read_text(encoding="utf-8")

start = text.index("    def _pre_migration_backup(self, from_version: int) -> Path:\n")
end = text.index("    def initialize(self) -> None:\n", start)
block = text[start:end]
block = replace_once(
    block,
    "            os.replace(temporary, target)\n",
    "            os.replace(temporary, target)\n"
    "            self._fsync_directory(target.parent)\n",
    "base backup fsync",
)
text = text[:start] + block + text[end:]

marker_anchor = "    def _bootstrap_marker_path(self) -> Path:\n"
lock_block = '''    @contextmanager
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

'''
if "    def _bootstrap_lock(self)" not in text:
    text = replace_once(text, marker_anchor, lock_block + marker_anchor, "bootstrap lock")

text = replace_once(
    text,
    '            "bootstrap_actor_id",\n            "expected_genesis_hash",\n',
    '            "bootstrap_actor_id",\n'
    '            "bootstrap_payload",\n'
    '            "expected_genesis_hash",\n',
    "marker key",
)
text = replace_once(
    text,
    '        bootstrap_actor_id = payload.get("bootstrap_actor_id")\n'
    '        expected_genesis_hash = payload.get("expected_genesis_hash")\n',
    '        bootstrap_actor_id = payload.get("bootstrap_actor_id")\n'
    '        bootstrap_payload = payload.get("bootstrap_payload")\n'
    '        expected_genesis_hash = payload.get("expected_genesis_hash")\n',
    "marker payload variable",
)
validation = '''        if not isinstance(bootstrap_payload, dict) or set(bootstrap_payload) != {
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
'''
digest_anchor = '''        if (
            not isinstance(expected_genesis_hash, str)
            or len(expected_genesis_hash) != 64
            or any(character not in "0123456789abcdef" for character in expected_genesis_hash)
        ):
'''
text = replace_once(
    text,
    digest_anchor,
    validation + digest_anchor,
    "marker payload validation",
)
text = replace_once(
    text,
    '            "payload_json": _json(self._production_bootstrap_payload(connection)),\n',
    '            "payload_json": _json(marker["bootstrap_payload"]),\n',
    "bootstrap row payload",
)

prepare_start = text.index("    def _prepare_bootstrap_marker(\n")
prepare_end = text.index("    def _ensure_bootstrap_marker(", prepare_start)
prepare_block = '''    def _prepare_bootstrap_marker(
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

'''
text = text[:prepare_start] + prepare_block + text[prepare_end:]

bind_start = text.index("    def bind_production(\n")
bind_end = text.index("    def _create_production_genesis(\n", bind_start)
bind_block = text[bind_start:bind_end]
bind_block = bind_block.replace(
    "    def bind_production(\n", "    def _bind_production_locked(\n", 1
)
wrapper = '''    def bind_production(
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

'''
text = text[:bind_start] + wrapper + bind_block + text[bind_end:]
sqlite_path.write_text(text, encoding="utf-8")

production_path = Path("src/shadowseed/storage/production.py")
production = production_path.read_text(encoding="utf-8")
start = production.index("    def _pre_migration_backup(self, from_version: int) -> Path:\n")
end = production.index("    def initialize(self) -> None:\n", start)
block = production[start:end]
block = replace_once(
    block,
    "            os.replace(temporary, target)\n",
    "            os.replace(temporary, target)\n"
    "            self._fsync_directory(target.parent)\n",
    "production backup fsync",
)
production = production[:start] + block + production[end:]

checkpoint_start = production.index("    def _ensure_authority_checkpoint(")
checkpoint_end = production.index(
    "    def _verify_authority_snapshot_consistency(", checkpoint_start
)
checkpoint_block = '''    def _ensure_authority_checkpoint(self, *, bootstrap_actor_id: str) -> None:
        if self._workspace_id is None:
            raise WorkspaceStorageError("production workspace is not bound")
        with self._connect() as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT 1 FROM production_ledger "
                    "WHERE event_type='production.authority_checkpoint' LIMIT 1"
                ).fetchone()
                if existing is not None:
                    connection.rollback()
                    return
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
            except Exception:
                connection.rollback()
                raise
        self._advance_anchor()

'''
production = (
    production[:checkpoint_start] + checkpoint_block + production[checkpoint_end:]
)
production_path.write_text(production, encoding="utf-8")

tests_path = Path("tests/test_production_persistence_phase3.py")
tests = tests_path.read_text(encoding="utf-8")
if "import threading\n" not in tests:
    tests = tests.replace("import sqlite3\n", "import sqlite3\nimport threading\n", 1)
if (
    "from shadowseed.storage.production import ProductionSQLiteWorkspaceRepository\n"
    not in tests
):
    tests = tests.replace(
        "from shadowseed.storage.integrity import canonical_json, event_digest\n",
        "from shadowseed.storage.integrity import canonical_json, event_digest\n"
        "from shadowseed.storage.production import ProductionSQLiteWorkspaceRepository\n",
        1,
    )
insert = '''

def test_v1_interrupted_bootstrap_replays_protected_payload_without_backup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "workspace.id").write_text("workspace::legacy\\n", encoding="utf-8")
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

'''
anchor = (
    "\ndef test_v1_product_bootstrap_creates_explicit_preproduction_genesis("
    "tmp_path: Path) -> None:\n"
)
if "test_concurrent_production_bind_serializes_bootstrap" not in tests:
    tests = replace_once(tests, anchor, insert + anchor, "test insertion")
tests_path.write_text(tests, encoding="utf-8")
