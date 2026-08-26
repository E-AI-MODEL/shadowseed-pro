from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"guard not found: {label}")
    return text.replace(old, new, 1)


sqlite_path = Path("src/shadowseed/storage/sqlite.py")
sqlite_text = sqlite_path.read_text(encoding="utf-8")
sqlite_text = replace_once(
    sqlite_text,
    "                planned = self._bootstrap_event_row(connection, marker)\n",
    "                live_authority_baseline = self._workspace_authority_baseline(connection)\n"
    "                protected_authority_baseline = str(\n"
    "                    marker[\"bootstrap_payload\"][\"authority_baseline\"]\n"
    "                )\n"
    "                if live_authority_baseline != protected_authority_baseline:\n"
    "                    raise WorkspaceStorageError(\n"
    "                        \"production bootstrap authority baseline changed after protected \"\n"
    "                        \"commitment; explicit recovery is required\"\n"
    "                    )\n\n"
    "                planned = self._bootstrap_event_row(connection, marker)\n",
    "live authority baseline check",
)
sqlite_path.write_text(sqlite_text, encoding="utf-8")

production_path = Path("src/shadowseed/storage/production.py")
production_text = production_path.read_text(encoding="utf-8")
old_bind = '''    def bind_production(
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
'''
new_bind = '''    def bind_production(
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
            self._bind_production_locked(
                workspace_id=workspace_id,
                integrity_dir=self._integrity_dir,
                bootstrap_actor_id=bootstrap_actor_id,
            )
            self._ensure_authority_checkpoint(bootstrap_actor_id=bootstrap_actor_id)
            return self.verify_production_integrity()
'''
production_text = replace_once(
    production_text, old_bind, new_bind, "production bind lock boundary"
)
production_path.write_text(production_text, encoding="utf-8")

tests_path = Path("tests/test_production_persistence_phase3.py")
tests = tests_path.read_text(encoding="utf-8")
insert = '''

def test_interrupted_bootstrap_rejects_live_authority_baseline_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "workspace"
    root.mkdir()
    (root / "workspace.id").write_text("workspace::legacy\\n", encoding="utf-8")
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

'''
anchor = "\ndef test_concurrent_production_bind_serializes_bootstrap(tmp_path: Path) -> None:\n"
if "test_interrupted_bootstrap_rejects_live_authority_baseline_drift" not in tests:
    tests = replace_once(tests, anchor, insert + anchor, "round 8 regression insertion")
tests_path.write_text(tests, encoding="utf-8")
