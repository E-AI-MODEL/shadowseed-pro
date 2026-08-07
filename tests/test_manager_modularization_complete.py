"""Structural completion guards for manager modularization (#25)."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src/shadowseed"
MANAGER = SOURCE_ROOT / "manager.py"


def test_manager_stays_a_bounded_orchestration_facade() -> None:
    source = MANAGER.read_text(encoding="utf-8")
    assert len(source.splitlines()) <= 800

    tree = ast.parse(source)
    imported_modules = {
        alias.asname or alias.name
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module == "shadowseed"
        for alias in node.names
    }
    assert {"intake_engine", "lifecycle_engine", "vector_workflows"} <= imported_modules

    forbidden_calls = {
        ("np", "dot"),
        ("np", "mean"),
        ("np", "linalg"),
        ("math", "exp"),
        ("re", "findall"),
    }
    seen_calls: set[tuple[str, str]] = set()
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Attribute):
            continue
        if isinstance(call.func.value, ast.Name):
            seen_calls.add((call.func.value.id, call.func.attr))
    assert forbidden_calls.isdisjoint(seen_calls)


def test_modularized_runtime_has_explicit_authority_ownership() -> None:
    authority = (ROOT / "repository-authority.yaml").read_text(encoding="utf-8")
    for path in (
        "src/shadowseed/manager.py",
        "src/shadowseed/models.py",
        "src/shadowseed/contradictions.py",
        "src/shadowseed/intake.py",
        "src/shadowseed/lifecycle.py",
        "src/shadowseed/vector_workflows.py",
        "src/shadowseed/gate/**",
    ):
        assert f"- path: {path}" in authority


def test_active_ownership_docs_name_the_final_boundaries() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    overview = (ROOT / "docs/architecture/overview.md").read_text(encoding="utf-8")
    structure = (ROOT / "docs/architecture/repository-structure.md").read_text(
        encoding="utf-8"
    )

    for module in (
        "shadowseed.models",
        "shadowseed.contradictions",
        "shadowseed.intake",
        "shadowseed.lifecycle",
        "shadowseed.vector_workflows",
        "shadowseed.gate",
    ):
        assert module in readme
        assert module in overview
        assert module in structure

    assert "orchestration" in readme
    assert "orchestration" in overview
    assert "Manager modularization" in structure
