from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"guard not found: {label}")
    return text.replace(old, new, 1)


sqlite_path = Path("src/shadowseed/storage/sqlite.py")
text = sqlite_path.read_text(encoding="utf-8")
old = '''        if pending is not None:
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
'''
new = '''        if pending is not None:
            with self._connect() as connection:
                try:
                    connection.execute("BEGIN IMMEDIATE")
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
                    live_authority_baseline = self._workspace_authority_baseline(connection)
                    protected_authority_baseline = str(
                        pending["bootstrap_payload"]["authority_baseline"]
                    )
                    if live_authority_baseline != protected_authority_baseline:
                        raise WorkspaceStorageError(
                            "production bootstrap authority baseline changed after protected "
                            "commitment; explicit recovery is required"
                        )
                    connection.commit()
                except Exception:
                    connection.rollback()
                    raise
            report = self._verify_chain_only()
'''
text = replace_once(text, old, new, "committed bootstrap authority revalidation")
sqlite_path.write_text(text, encoding="utf-8")


tests_path = Path("tests/test_production_persistence_phase3.py")
tests = tests_path.read_text(encoding="utf-8")
insert = '''

def test_interrupted_bootstrap_after_genesis_rejects_live_authority_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shadowseed.storage.sqlite as sqlite_storage

    root = tmp_path / "workspace"
    root.mkdir()
    (root / "workspace.id").write_text("workspace::legacy\\n", encoding="utf-8")
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

'''
anchor = "\ndef test_interrupted_bootstrap_rejects_rewritten_genesis_before_reseal(\n"
if "test_interrupted_bootstrap_after_genesis_rejects_live_authority_drift" not in tests:
    tests = replace_once(tests, anchor, insert + anchor, "round 9 regression insertion")
tests_path.write_text(tests, encoding="utf-8")
