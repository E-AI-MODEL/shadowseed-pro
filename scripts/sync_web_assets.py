"""Copy the deterministic Next static export into the Python package tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sync_web_assets(source: Path, target: Path) -> dict[str, object]:
    source = source.resolve()
    target = target.resolve()
    index = source / "index.html"
    if not index.is_file():
        raise RuntimeError(
            f"Next static export is incomplete; expected {index}"
        )
    next_static = source / "_next" / "static"
    if not next_static.is_dir():
        raise RuntimeError(
            f"Next static export is incomplete; expected {next_static}"
        )

    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)

    files = []
    for path in sorted(target.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(target).as_posix()
        if relative == "web-assets-manifest.json":
            continue
        files.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )

    if not files:
        raise RuntimeError("Next static export produced no packageable files")

    payload: dict[str, object] = {
        "artifact": "shadowseed_web_static_export",
        "files": files,
    }
    manifest = target / "web-assets-manifest.json"
    manifest.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="apps/web/out")
    parser.add_argument("--target", default="src/shadowseed_webapi/static")
    args = parser.parse_args(argv)
    payload = sync_web_assets(Path(args.source), Path(args.target))
    print(
        json.dumps(
            {
                "artifact": payload["artifact"],
                "file_count": len(payload["files"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
