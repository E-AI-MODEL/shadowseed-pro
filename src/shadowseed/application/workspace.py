"""Workspace creation, backup, restore, and deletion services."""

from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from shadowseed.application.auth import (
    LOCAL_PRODUCTION_CAPABILITIES,
    WORKSPACE_BACKUP_RESTORE,
    WORKSPACE_INTEGRITY_RECOVER,
    ActorContext,
    require_capability,
)
from shadowseed.storage.production import ProductionSQLiteWorkspaceRepository
from shadowseed.storage.recovery import (
    import_production_backup,
    inspect_production_backup,
    restore_production_backup,
)


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
        self.repository = ProductionSQLiteWorkspaceRepository(self.paths.database)

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
        location_id = hashlib.sha256(str(self.paths.root).encode("utf-8")).hexdigest()[:20]
        return self.paths.root.parent / ".shadowseed-integrity" / location_id / identity

    def _initialize_structure(self) -> None:
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

    @staticmethod
    def _local_actor_for_workspace(
        workspace_id: str,
        *,
        request_id: str | None = None,
        auth_method: str = "local-install",
    ) -> ActorContext:
        return ActorContext(
            actor_id=f"local-owner::{workspace_id.removeprefix('workspace::')}",
            scope_id=workspace_id,
            capabilities=LOCAL_PRODUCTION_CAPABILITIES,
            auth_method=auth_method,
            assurance={"profile": "single-user-local"},
            request_id=request_id or f"request::{uuid4()}",
            policy_version="production-authz-v1",
        )

    def initialize(self) -> WorkspacePaths:
        self._initialize_structure()
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

        return self._local_actor_for_workspace(
            self.workspace_id,
            request_id=request_id,
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

    def restore(self, source: str | Path) -> dict[str, object]:
        """Run the trusted local restore/recovery boundary.

        Fresh-machine imports use integrity-recovery authority because the previous
        protected anchor is unavailable. Restores into an existing workspace use the
        narrower backup/restore capability. Neither path accepts a client-supplied
        authorization boolean.
        """

        fresh_target = not self.paths.database.exists() and not self.paths.identity.exists()
        if fresh_target:
            backup = inspect_production_backup(source)
            workspace_id = self._validate_workspace_id(str(backup["workspace_id"]))
            actor = self._local_actor_for_workspace(
                workspace_id,
                auth_method="local-import-recovery",
            )
            authorization = require_capability(
                actor,
                scope_id=workspace_id,
                capability=WORKSPACE_INTEGRITY_RECOVER,
            )
            self._initialize_structure()
            self.paths.identity.write_text(f"{workspace_id}\n", encoding="utf-8")
            try:
                return import_production_backup(
                    self.repository,
                    source,
                    integrity_dir=self._integrity_dir(workspace_id),
                    authorization=authorization,
                )
            except Exception:
                self.paths.identity.unlink(missing_ok=True)
                raise

        self.initialize()
        workspace_id = self._read_workspace_id()
        actor = self._local_actor_for_workspace(workspace_id)
        authorization = require_capability(
            actor,
            scope_id=workspace_id,
            capability=WORKSPACE_BACKUP_RESTORE,
        )
        return restore_production_backup(
            self.repository,
            source,
            authorization=authorization,
        )

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
            location_dir = integrity_dir.parent
            try:
                location_dir.rmdir()
                location_dir.parent.rmdir()
            except OSError:
                pass
