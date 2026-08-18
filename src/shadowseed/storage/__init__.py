"""Local persistence adapters for Shadowseed tester workspaces.

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
