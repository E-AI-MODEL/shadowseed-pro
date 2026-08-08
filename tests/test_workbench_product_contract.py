from __future__ import annotations

import ast
from pathlib import Path

import pytest

from shadowseed.workbench.app import launch_workbench


REQUIRED_PRODUCT_FILES = (
    "src/shadowseed/workbench/app.py",
    "src/shadowseed/workbench/controller.py",
    "src/shadowseed/application/inspection.py",
    "src/shadowseed/application/feedback.py",
    "src/shadowseed/application/scenarios.py",
    "src/shadowseed/application/comparison.py",
)


def test_workbench_product_files_are_normal_source_files() -> None:
    for path in REQUIRED_PRODUCT_FILES:
        file = Path(path)
        assert file.is_file(), path
        assert file.stat().st_size > 100, path


def test_workbench_ui_does_not_import_runtime_authority_modules() -> None:
    forbidden = {
        "shadowseed.manager",
        "shadowseed.gate",
        "shadowseed.gate.runtime_adapter",
        "shadowseed.lifecycle",
    }
    for path in Path("src/shadowseed/workbench").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)
        assert not any(
            imported == denied or imported.startswith(f"{denied}.")
            for imported in imports
            for denied in forbidden
        ), f"{path} crosses Workbench authority boundary: {sorted(imports & forbidden)}"


def test_remote_binding_requires_explicit_opt_in(tmp_path) -> None:
    with pytest.raises(ValueError, match="remote Workbench binding is disabled"):
        launch_workbench(
            tmp_path / "workspace",
            host="0.0.0.0",
            allow_remote=False,
            inbrowser=False,
        )


def test_gradio_app_builds_when_optional_dependency_is_installed(tmp_path) -> None:
    pytest.importorskip("gradio")
    from shadowseed.workbench.app import build_app

    app = build_app(tmp_path / "workspace")
    assert app is not None
