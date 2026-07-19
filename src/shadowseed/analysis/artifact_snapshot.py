from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Iterable


ALLOWED_SUFFIXES = {".json", ".md", ".svg"}


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return cleaned or "artifact"


def build_artifact_snapshot(
    source_dir: str | Path,
    target_dir: str | Path,
    *,
    artifacts_dir: str | Path | None = None,
    manifest_path: str | Path | None = None,
    source_workflow: str | None = None,
    source_run_id: str | None = None,
    repository: str | None = None,
    published_via: Iterable[str] = (),
    path_key: str = "snapshot_path",
    committed_back_to_main: bool | None = None,
    required_files: Iterable[str] = (),
) -> Path:
    source = Path(source_dir)
    if not source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source}")

    target = Path(target_dir)
    target.mkdir(parents=True, exist_ok=True)

    copied_artifacts_dir: Path | None = None
    if artifacts_dir is not None:
        copied_artifacts_dir = Path(artifacts_dir)
        copied_artifacts_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, copied_artifacts_dir, dirs_exist_ok=True)

    output_manifest = Path(manifest_path) if manifest_path is not None else target / "manifest.json"
    manifest: dict[str, object] = {
        "source_workflow": source_workflow,
        "source_run_id": source_run_id,
        "repository": repository,
        "published_via": list(published_via),
        "copied_files": [],
    }
    if committed_back_to_main is not None:
        manifest["committed_back_to_main"] = committed_back_to_main

    required_names = {name for name in required_files if name}
    discovered_names: set[str] = set()
    used_names: set[str] = set()
    target_root = target.parent
    artifacts_root = copied_artifacts_dir.parent if copied_artifacts_dir is not None else None

    for file_path in sorted(path for path in source.rglob("*") if path.is_file()):
        if file_path.suffix.lower() not in ALLOWED_SUFFIXES:
            continue
        discovered_names.add(file_path.name)
        relative = file_path.relative_to(source)
        artifact = relative.parts[0] if relative.parts else "artifact"
        base = file_path.name
        target_name = base
        if target_name in used_names:
            target_name = f"{safe_name(artifact)}__{base}"
        counter = 2
        while target_name in used_names:
            stem = Path(base).stem
            suffix = Path(base).suffix
            target_name = f"{safe_name(artifact)}__{stem}_{counter}{suffix}"
            counter += 1
        used_names.add(target_name)
        snapshot_path = target / target_name
        shutil.copy2(file_path, snapshot_path)

        entry = {
            "artifact": artifact,
            "source_path": str(relative),
            path_key: str(snapshot_path.relative_to(target_root)),
            "bytes": file_path.stat().st_size,
        }
        if copied_artifacts_dir is not None and artifacts_root is not None:
            entry["original_artifact_path"] = str((copied_artifacts_dir / relative).relative_to(artifacts_root))
        manifest["copied_files"].append(entry)

    missing_required = sorted(required_names - discovered_names)
    if missing_required:
        missing_text = ", ".join(missing_required)
        raise ValueError(f"Missing required artifact files: {missing_text}")

    output_manifest.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output_manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m shadowseed.analysis.artifact_snapshot")
    parser.add_argument("--source", required=True)
    parser.add_argument("--target-dir", required=True)
    parser.add_argument("--artifacts-dir")
    parser.add_argument("--manifest-path")
    parser.add_argument("--source-workflow")
    parser.add_argument("--source-run-id")
    parser.add_argument("--repository")
    parser.add_argument("--published-via", nargs="*", default=[])
    parser.add_argument("--path-key", default="snapshot_path")
    parser.add_argument("--committed-back-to-main", choices=["true", "false"])
    parser.add_argument("--require-files", nargs="*", default=[])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    committed_back_to_main = None
    if args.committed_back_to_main is not None:
        committed_back_to_main = args.committed_back_to_main == "true"

    path = build_artifact_snapshot(
        args.source,
        args.target_dir,
        artifacts_dir=args.artifacts_dir,
        manifest_path=args.manifest_path,
        source_workflow=args.source_workflow,
        source_run_id=args.source_run_id,
        repository=args.repository,
        published_via=args.published_via,
        path_key=args.path_key,
        committed_back_to_main=committed_back_to_main,
        required_files=args.require_files,
    )
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
