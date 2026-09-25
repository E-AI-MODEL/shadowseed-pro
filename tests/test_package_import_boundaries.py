"""Regression tests for acyclic application/storage package exports."""

from __future__ import annotations

import subprocess
import sys

import pytest

from shadowseed import cli_dispatch


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

def test_product_imports_do_not_load_benchmark_package():
    code = """
import sys

class BlockResearchImports:
    def find_spec(self, fullname, path=None, target=None):
        legacy = fullname == "shadowseed.benchmark" or fullname.startswith(
            "shadowseed.benchmark."
        )
        separate = fullname == "shadowseed_research" or fullname.startswith(
            "shadowseed_research."
        )
        if legacy or separate:
            raise AssertionError(f"product import crossed into research package: {fullname}")
        return None

sys.meta_path.insert(0, BlockResearchImports())

from shadowseed import ShadowseedEngine
from shadowseed.cli import build_parser
from shadowseed.cli_dispatch import COMMAND_HANDLERS

assert ShadowseedEngine is not None
assert build_parser().parse_args(["chat", "--backend", "fixture"]).command == "chat"
assert "chat" in COMMAND_HANDLERS
assert not any(
    name == "shadowseed.benchmark"
    or name.startswith("shadowseed.benchmark.")
    or name == "shadowseed_research"
    or name.startswith("shadowseed_research.")
    for name in sys.modules
)
print("product imports are research-free")
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "product imports are research-free" in completed.stdout

def test_research_command_reports_missing_research_distribution(monkeypatch) -> None:
    def missing_research(_qualified: str):
        raise ModuleNotFoundError(
            "No module named 'shadowseed_research'",
            name="shadowseed_research",
        )

    monkeypatch.setattr(cli_dispatch, "import_module", missing_research)

    with pytest.raises(RuntimeError, match="shadowseed-research"):
        cli_dispatch._research_attr("ssl45_gap_suite", "run_ssl45_gap_suite")


def test_research_dependency_errors_are_not_hidden(monkeypatch) -> None:
    def missing_dependency(_qualified: str):
        raise ModuleNotFoundError("No module named 'optional_backend'", name="optional_backend")

    monkeypatch.setattr(cli_dispatch, "import_module", missing_dependency)

    with pytest.raises(ModuleNotFoundError, match="optional_backend"):
        cli_dispatch._research_attr("ssl45_gap_suite", "run_ssl45_gap_suite")

