from __future__ import annotations

import sqlite3
from pathlib import Path

from shadowseed.application.sessions import SessionService
from shadowseed.application.workspace import WorkspaceService


def test_workspace_backup_replaces_existing_target_after_handles_close(tmp_path: Path) -> None:
    workspace = WorkspaceService(tmp_path / "workspace")
    workspace.initialize()
    sessions = SessionService(workspace.repository)
    session_id = sessions.create_session(title="Backup portability", profile_id="demo")
    sessions.run_turn(session_id, "Persist one turn before backup")

    target = tmp_path / "backup.sqlite"
    first = workspace.backup(target)
    assert first == target.resolve()
    assert target.is_file()

    sessions.run_turn(session_id, "Persist a second turn before replacement")
    second = workspace.backup(target)
    assert second == target.resolve()
    assert not target.with_suffix(target.suffix + ".tmp").exists()

    with sqlite3.connect(f"file:{target}?mode=ro", uri=True) as connection:
        turn_count = connection.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
    assert turn_count == 2
