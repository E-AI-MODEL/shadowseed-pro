from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one match, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    readme = Path("README.md")
    replace_once(
        readme,
        "| [`shadowseed.manager`](src/shadowseed/manager.py) | `SSLManager` configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |\n",
        "| [`shadowseed.manager`](src/shadowseed/manager.py) | `SSLManager` runtime orchestration, configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |\n",
    )
    replace_once(
        readme,
        "| [`shadowseed.vector_workflows`](src/shadowseed/vector_workflows.py) | Uncertain-region search, external-feedback routing, and in-memory constellation construction |\n"
        "| [`shadowseed.seed_normalization`](src/shadowseed/seed_normalization.py) | Candidate cleanup and atomic splitting |\n",
        "| [`shadowseed.vector_workflows`](src/shadowseed/vector_workflows.py) | Uncertain-region search, external-feedback routing, and in-memory constellation construction |\n"
        "| [`shadowseed.gate`](src/shadowseed/gate/) | Typed signals, named policies, immutable events, verified logging, and the executable Gate-controlled decision engine |\n"
        "| [`shadowseed.seed_normalization`](src/shadowseed/seed_normalization.py) | Candidate cleanup and atomic splitting |\n",
    )

    replace_once(
        Path("docs/architecture/overview.md"),
        "| `shadowseed.manager` | `SSLManager` configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |\n",
        "| `shadowseed.manager` | `SSLManager` runtime orchestration, configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |\n",
    )

    Path(".github/workflows/polish-final-ownership-docs.yml").unlink()
    Path(".github/scripts/polish_final_ownership_docs.py").unlink()


if __name__ == "__main__":
    main()
