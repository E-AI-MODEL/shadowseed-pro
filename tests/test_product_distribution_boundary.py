import ast
from pathlib import Path


PRODUCT_BENCHMARK_MODULES = {
    "__init__.py",
    "embedding_backends.py",
    "ollama_client.py",
    "open_set_model_detector.py",
    "openai_client.py",
    "recurrence_clustering.py",
    "seed_retrieval_probe.py",
}


def test_product_benchmark_namespace_contains_only_compatibility_facades() -> None:
    root = Path(__file__).resolve().parent.parent
    package = root / "src" / "shadowseed" / "benchmark"
    actual = {path.name for path in package.glob("*.py")}
    assert actual == PRODUCT_BENCHMARK_MODULES


def test_product_source_tree_does_not_embed_research_distribution() -> None:
    root = Path(__file__).resolve().parent.parent
    assert not (root / "src" / "shadowseed_research").exists()


def test_remaining_benchmark_modules_are_marked_compatibility_only() -> None:
    root = Path(__file__).resolve().parent.parent
    package = root / "src" / "shadowseed" / "benchmark"
    for path in package.glob("*.py"):
        if path.name == "__init__.py":
            continue
        assert "COMPATIBILITY_ONLY" in path.read_text(encoding="utf-8"), path.name

def test_runtime_scripts_and_experiments_do_not_import_legacy_benchmark_implementation() -> None:
    root = Path(__file__).resolve().parent.parent
    scan_roots = [
        root / "src" / "shadowseed",
        root / "scripts",
        root / "experiments",
    ]
    violations: list[str] = []

    for scan_root in scan_roots:
        for path in scan_root.rglob("*.py"):
            if "src/shadowseed/benchmark" in path.as_posix():
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                modules: list[str] = []
                if isinstance(node, ast.ImportFrom) and node.module:
                    modules.append(node.module)
                elif isinstance(node, ast.Import):
                    modules.extend(alias.name for alias in node.names)
                for module in modules:
                    if module == "shadowseed.benchmark" or module.startswith(
                        "shadowseed.benchmark."
                    ):
                        violations.append(
                            f"{path.relative_to(root)}:{node.lineno}: {module}"
                        )

    assert not violations, "\n".join(violations)

