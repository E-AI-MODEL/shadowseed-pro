"""Temporary materializer for acyclic application/storage package exports."""

from pathlib import Path


APPLICATION_INIT = '''"""Application services for the local Shadowseed tester environment.

Data contracts and profiles are safe eager imports. Services that depend on
storage are resolved lazily so importing ``shadowseed.application.models`` does
not initialize the storage-dependent service graph and create a circular import.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shadowseed.application.models import (
    DoctorReport,
    HealthCheck,
    SessionConfig,
    SessionSummary,
    TesterFeedback,
)
from shadowseed.application.profiles import WorkbenchProfile, get_profile, list_profiles

if TYPE_CHECKING:
    from shadowseed.application.sessions import SessionService
    from shadowseed.application.workspace import WorkspacePaths, WorkspaceService

__all__ = [
    "DoctorReport",
    "HealthCheck",
    "SessionConfig",
    "SessionService",
    "SessionSummary",
    "TesterFeedback",
    "WorkbenchProfile",
    "WorkspacePaths",
    "WorkspaceService",
    "get_profile",
    "list_profiles",
]


def __getattr__(name: str) -> Any:
    if name == "SessionService":
        from shadowseed.application.sessions import SessionService

        return SessionService
    if name in {"WorkspacePaths", "WorkspaceService"}:
        from shadowseed.application.workspace import WorkspacePaths, WorkspaceService

        return {"WorkspacePaths": WorkspacePaths, "WorkspaceService": WorkspaceService}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
'''


STORAGE_INIT = '''"""Local persistence adapters for Shadowseed tester workspaces.

Schema metadata is safe to import eagerly. The SQLite implementation is resolved
lazily so importing ``shadowseed.storage.schema`` never initializes application
services as a side effect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shadowseed.storage.schema import SCHEMA_VERSION

if TYPE_CHECKING:
    from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError

__all__ = ["SCHEMA_VERSION", "SQLiteWorkspaceRepository", "WorkspaceStorageError"]


def __getattr__(name: str) -> Any:
    if name in {"SQLiteWorkspaceRepository", "WorkspaceStorageError"}:
        from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError

        return {
            "SQLiteWorkspaceRepository": SQLiteWorkspaceRepository,
            "WorkspaceStorageError": WorkspaceStorageError,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
'''


def main() -> None:
    Path("src/shadowseed/application/__init__.py").write_text(
        APPLICATION_INIT, encoding="utf-8"
    )
    Path("src/shadowseed/storage/__init__.py").write_text(
        STORAGE_INIT, encoding="utf-8"
    )


if __name__ == "__main__":
    main()
