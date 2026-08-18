"""Regression tests for acyclic application/storage package exports."""

from __future__ import annotations

import subprocess
import sys


def test_storage_and_application_public_imports_work_in_fresh_interpreter():
    code = """
from shadowseed.storage.schema import SCHEMA_VERSION
from shadowseed.storage import SQLiteWorkspaceRepository, WorkspaceStorageError
from shadowseed.application import SessionService, WorkspacePaths, WorkspaceService
assert SCHEMA_VERSION >= 1
assert SQLiteWorkspaceRepository is not None
assert WorkspaceStorageError is not None
assert SessionService is not None
assert WorkspacePaths is not None
assert WorkspaceService is not None
print('acyclic public imports OK')
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "acyclic public imports OK" in completed.stdout
