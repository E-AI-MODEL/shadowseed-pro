"""Contract tests for COMPATIBILITY_ONLY import paths.

These tests protect the legacy import paths documented in
``docs/architecture/compatibility-policy.md``. They verify that each
compatibility module:

* imports successfully;
* re-exports the same objects as its canonical module
  (``legacy_object is canonical_object``);
* declares an ``__all__`` that matches exactly what it imports;
* defines no independent functions or classes.

Behavioral tests belong to the canonical modules, not here.
"""

from __future__ import annotations

import ast
import importlib
import pathlib

import pytest

# Legacy compatibility path -> canonical module path.
COMPATIBILITY_MAP = {
    "shadowseed.benchmark.embedding_backends": "shadowseed.adapters.embedding",
    "shadowseed.benchmark.openai_client": "shadowseed.adapters.openai_client",
    "shadowseed.benchmark.ollama_client": "shadowseed.adapters.ollama_client",
    "shadowseed.benchmark.open_set_model_detector": (
        "shadowseed.detection.model_detector"
    ),
    "shadowseed.benchmark.recurrence_clustering": (
        "shadowseed.recurrence_clustering"
    ),
    "shadowseed.benchmark.seed_retrieval_probe": "shadowseed.retrieval_probe",
    "shadowseed.prompt_templates": "shadowseed.prompts",
}

_SRC_ROOT = pathlib.Path(__file__).resolve().parent.parent / "src"


def _module_source(dotted: str) -> str:
    return (_SRC_ROOT / (dotted.replace(".", "/") + ".py")).read_text()


@pytest.mark.parametrize("legacy", sorted(COMPATIBILITY_MAP))
def test_compat_module_imports(legacy: str) -> None:
    assert importlib.import_module(legacy) is not None


@pytest.mark.parametrize("legacy", sorted(COMPATIBILITY_MAP))
def test_compat_declares_all(legacy: str) -> None:
    module = importlib.import_module(legacy)
    assert hasattr(module, "__all__"), f"{legacy} must declare __all__"
    assert module.__all__, f"{legacy}.__all__ must not be empty"


@pytest.mark.parametrize("legacy", sorted(COMPATIBILITY_MAP))
def test_legacy_objects_are_canonical(legacy: str) -> None:
    canonical = COMPATIBILITY_MAP[legacy]
    legacy_mod = importlib.import_module(legacy)
    canonical_mod = importlib.import_module(canonical)
    for name in legacy_mod.__all__:
        assert hasattr(canonical_mod, name), (
            f"{canonical} is missing supported name {name!r}"
        )
        assert getattr(legacy_mod, name) is getattr(canonical_mod, name), (
            f"{legacy}.{name} is not the canonical {canonical}.{name}"
        )


@pytest.mark.parametrize("legacy", sorted(COMPATIBILITY_MAP))
def test_all_matches_imports(legacy: str) -> None:
    """``__all__`` must equal exactly the names the wrapper imports."""
    tree = ast.parse(_module_source(legacy))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported.add(alias.asname or alias.name)
    module = importlib.import_module(legacy)
    assert set(module.__all__) == imported, (
        f"{legacy}: __all__ {sorted(module.__all__)} != "
        f"imported names {sorted(imported)}"
    )


@pytest.mark.parametrize("legacy", sorted(COMPATIBILITY_MAP))
def test_no_independent_definitions(legacy: str) -> None:
    """A compatibility module must not define its own functions or classes."""
    tree = ast.parse(_module_source(legacy))
    defined = [
        node.name
        for node in tree.body
        if isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        )
    ]
    assert not defined, f"{legacy} defines independent objects: {defined}"


@pytest.mark.parametrize("legacy", sorted(COMPATIBILITY_MAP))
def test_declares_compatibility_only(legacy: str) -> None:
    """The module must identify itself as COMPATIBILITY_ONLY and name its target."""
    source = _module_source(legacy)
    canonical = COMPATIBILITY_MAP[legacy]
    assert "COMPATIBILITY_ONLY" in source, (
        f"{legacy} must identify itself as COMPATIBILITY_ONLY"
    )
    assert canonical in source, (
        f"{legacy} must name its canonical module {canonical}"
    )
