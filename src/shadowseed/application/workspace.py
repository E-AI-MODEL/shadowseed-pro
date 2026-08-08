"""Workspace creation, backup, restore, and deletion services."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from shadowseed.storage.sqlite import SQLiteWorkspaceRepository


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    database: Path
    config: Path
    exports: Path
    attachments: Path
    logs: Path


def workspace_paths(root: str | Path | None = None) -> WorkspacePaths:
    resolved = Path(root or "~/.shadowseed").expanduser().resolve()
    return WorkspacePaths(
        root=resolved,
        database=resolved / "workspace.db",
        config=resolved / "config.toml",
        exports=resolved / "exports",
        attachments=resolved / "attachments",
        logs=resolved / "logs",
    )


class WorkspaceService:
    def __init__(self, root: str | Path | None = None) -> None:
        self.paths = workspace_paths(root)
        self.repository = SQLiteWorkspaceRepository(self.paths.database)

    def initialize(self) -> WorkspacePaths:
        self.paths.root.mkdir(parents=True, exist_ok=True)
        for path in (self.paths.exports, self.paths.attachments, self.paths.logs):
            path.mkdir(parents=True, exist_ok=True)
        if not self.paths.config.exists():
            self.paths.config.write_text(
                "# Shadowseed local tester workspace.\n"
                "# Secrets are never stored here. Use environment variables or an OS keyring.\n"
                'default_profile = "balanced"\n'
                'default_backend = "fixture"\n',
                encoding="utf-8",
            )
        self.repository.initialize()
        return self.paths

    def info(self) -> dict[str, object]:
        self.initialize()
        return {
            "root": str(self.paths.root),
            "database": str(self.paths.database),
            "schema_version": self.repository.schema_version(),
            "counts": self.repository.counts(),
        }

    def backup(self, destination: str | Path | None = None) -> Path:
        self.initialize()
        target = Path(destination).expanduser().resolve() if destination else (
            self.paths.exports
            / f"workspace-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
        )
        return self.repository.backup_to(target)

    def restore(self, source: str | Path) -> None:
        self.initialize()
        self.repository.restore_from(source)

    def delete(self) -> None:
        root = self.paths.root
        home = Path.home().resolve()
        protected = {Path(root.anchor).resolve(), home, home.parent.resolve()}
        if root in protected or len(root.parts) < 3:
            raise ValueError(f"refusing to delete unsafe workspace path: {root}")
        markers = (self.paths.database, self.paths.config)
        if root.exists() and not any(path.exists() for path in markers):
            raise ValueError(
                f"refusing to delete a directory that is not a Shadowseed workspace: {root}"
            )
        if root.exists():
            shutil.rmtree(root)
