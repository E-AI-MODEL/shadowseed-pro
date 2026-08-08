"""Structural completion guards for manager modularization (#25)."""

from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "src/shadowseed"
MANAGER = SOURCE_ROOT / "manager.py"

FORBIDDEN_CALL_PREFIXES = {
    ("np", "dot"),
    ("np", "mean"),
    ("np", "linalg"),
    ("math", "exp"),
    ("re", "findall"),
}


def _attribute_chain(node: ast.AST) -> tuple[str, ...] | None:
    """Return a complete dotted call target such as ``np.linalg.norm``."""

    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if not isinstance(node, ast.Name):
        return None
    return (node.id, *reversed(parts))


def _forbidden_call_chains(source: str) -> set[tuple[str, ...]]:
    tree = ast.parse(source)
    found: set[tuple[str, ...]] = set()
    for call in ast.walk(tree):
        if not isinstance(call, ast.Call):
            continue
        chain = _attribute_chain(call.func)
        if chain is None:
            continue
        if any(
            chain[: len(prefix)] == prefix
            for prefix in FORBIDDEN_CALL_PREFIXES
        ):
            found.add(chain)
    return found


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

    assert not _forbidden_call_chains(source)


def test_nested_numpy_attribute_chain_is_rejected() -> None:
    source = "def normalize(vector):\n    return np.linalg.norm(vector)\n"
    assert _forbidden_call_chains(source) == {("np", "linalg", "norm")}

    facade = (
        "def normalize(vector):\n"
        "    return intake_engine.normalize_embedding(vector)\n"
    )
    assert not _forbidden_call_chains(facade)


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
