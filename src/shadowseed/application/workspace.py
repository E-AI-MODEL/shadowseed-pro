"""Workspace creation, backup, restore, and deletion services."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from shadowseed.application.auth import ActorContext, LOCAL_PRODUCTION_CAPABILITIES
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    database: Path
    config: Path
    identity: Path
    exports: Path
    attachments: Path
    logs: Path


def workspace_paths(root: str | Path | None = None) -> WorkspacePaths:
    resolved = Path(root or "~/.shadowseed").expanduser().resolve()
    return WorkspacePaths(
        root=resolved,
        database=resolved / "workspace.db",
        config=resolved / "config.toml",
        identity=resolved / "workspace.id",
        exports=resolved / "exports",
        attachments=resolved / "attachments",
        logs=resolved / "logs",
    )


class WorkspaceService:
    def __init__(self, root: str | Path | None = None) -> None:
        self.paths = workspace_paths(root)
        self.repository = SQLiteWorkspaceRepository(self.paths.database)

    @staticmethod
    def _validate_workspace_id(workspace_id: str) -> str:
        value = workspace_id.strip()
        if not value.startswith("workspace::") or len(value) <= len("workspace::"):
            raise ValueError("workspace identity is missing or malformed")
        return value

    def _read_workspace_id(self) -> str:
        return self._validate_workspace_id(
            self.paths.identity.read_text(encoding="utf-8")
        )

    def _integrity_dir(self, workspace_id: str) -> Path:
        identity = workspace_id.removeprefix("workspace::")
        return self.paths.root.parent / ".shadowseed-integrity" / identity

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
        if not self.paths.identity.exists():
            self.paths.identity.write_text(f"workspace::{uuid4()}\n", encoding="utf-8")
        workspace_id = self._read_workspace_id()
        self.repository.initialize()
        self.repository.bind_production(
            workspace_id=workspace_id,
            integrity_dir=self._integrity_dir(workspace_id),
            bootstrap_actor_id=f"local-owner::{workspace_id.removeprefix('workspace::')}",
        )
        return self.paths

    @property
    def workspace_id(self) -> str:
        self.initialize()
        return self._read_workspace_id()

    def local_actor_context(self, *, request_id: str | None = None) -> ActorContext:
        """Create trusted local-owner context at the product boundary."""

        workspace_id = self.workspace_id
        return ActorContext(
            actor_id=f"local-owner::{workspace_id.removeprefix('workspace::')}",
            scope_id=workspace_id,
            capabilities=LOCAL_PRODUCTION_CAPABILITIES,
            auth_method="local-install",
            assurance={"profile": "single-user-local"},
            request_id=request_id or f"request::{uuid4()}",
            policy_version="production-authz-v1",
        )

    def info(self) -> dict[str, object]:
        self.initialize()
        return {
            "root": str(self.paths.root),
            "database": str(self.paths.database),
            "workspace_id": self._read_workspace_id(),
            "schema_version": self.repository.schema_version(),
            "counts": self.repository.counts(),
            "integrity": self.repository.verify_production_integrity(),
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
        markers = (self.paths.database, self.paths.config, self.paths.identity)
        if root.exists() and not any(path.exists() for path in markers):
            raise ValueError(
                f"refusing to delete a directory that is not a Shadowseed workspace: {root}"
            )
        integrity_dir: Path | None = None
        if self.paths.identity.is_file():
            integrity_dir = self._integrity_dir(self._read_workspace_id())
        if root.exists():
            shutil.rmtree(root)
        if integrity_dir is not None and integrity_dir.exists():
            shutil.rmtree(integrity_dir)
            parent = integrity_dir.parent
            try:
                parent.rmdir()
            except OSError:
                pass
