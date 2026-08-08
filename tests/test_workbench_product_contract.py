from __future__ import annotations

import ast
from pathlib import Path


def test_workbench_product_files_are_present() -> None:
    required = [
        Path("src/shadowseed/workbench/app.py"),
        Path("src/shadowseed/workbench/controller.py"),
        Path("src/shadowseed/application/inspection.py"),
        Path("src/shadowseed/application/feedback.py"),
        Path("src/shadowseed/application/scenarios.py"),
        Path("src/shadowseed/application/comparison.py"),
    ]
    assert not [str(path) for path in required if not path.exists()]


def test_workbench_ui_does_not_import_authority_internals() -> None:
    forbidden = {
        "shadowseed.manager",
        "shadowseed.gate",
        "shadowseed.gate.runtime_adapter",
    }
    for path in Path("src/shadowseed/workbench").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert imports.isdisjoint(forbidden), (path, imports & forbidden)


def test_cli_exposes_workbench_command() -> None:
    source = Path("src/shadowseed/cli.py").read_text(encoding="utf-8")
    assert '"workbench"' in source
    assert "launch_workbench" in source
