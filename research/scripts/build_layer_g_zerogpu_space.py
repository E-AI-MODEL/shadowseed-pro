"""Build an auditable ZeroGPU Space from the canonical L2 source files.

Do not copy credentials, .env files, user content or large model weights.
Every published instrument file is byte-for-byte from the GitHub source.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SPACE_SOURCE = ROOT / "research" / "spaces" / "layer-g-zerogpu"
CANONICAL = ROOT / "research" / "src" / "shadowseed_research" / "benchmark"
RESEARCH_LICENSE = ROOT / "research" / "LICENSE"
COPY_MODULES = ("layer_g_vnext.py", "layer_g_live_generation.py")


def git_sha() -> str:
    sha = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        text=True, stderr=subprocess.DEVNULL,
    ).strip()
    if len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
        raise ValueError("Source Git commit must be an immutable 40-hex SHA")
    return sha


def build_space(destination: Path, *, source_sha: str | None = None) -> dict:
    if destination.exists():
        raise FileExistsError("Space bundle destination already exists")
    sha = source_sha or git_sha()
    if len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
        raise ValueError("Expected a pinned 40-hex source commit")
    required = ("app.py", "README.md", "requirements.txt")
    for name in required:
        if not (SPACE_SOURCE / name).is_file():
            raise FileNotFoundError(SPACE_SOURCE / name)
    for name in COPY_MODULES:
        if not (CANONICAL / name).is_file():
            raise FileNotFoundError(CANONICAL / name)
    if not RESEARCH_LICENSE.is_file():
        raise FileNotFoundError(RESEARCH_LICENSE)
    destination.mkdir(parents=True)
    for name in required:
        shutil.copyfile(SPACE_SOURCE / name, destination / name)
    shutil.copyfile(RESEARCH_LICENSE, destination / "LICENSE")
    package = destination / "layer_g_capture"
    package.mkdir()
    (package / "__init__.py").write_text(
        '"""Canonical Shadowseed L2 capture code (packaged; not forked)."""\n',
        encoding="utf-8",
    )
    for name in COPY_MODULES:
        shutil.copyfile(CANONICAL / name, package / name)
    manifest = {
        "source_git_sha": sha,
        "status": "unexecuted_zero_gpu_space_bundle",
        "research_claim": "none",
        "capture_path": "original-generation-before-seed",
        "model_id": "Qwen/Qwen2.5-14B-Instruct",
        "quantization": "bnb-nf4-double-quant-bfloat16",
        "copied_instrument_paths": {
            "layer_g_capture/" + name:
                "research/src/shadowseed_research/benchmark/" + name
            for name in COPY_MODULES
        },
    }
    (destination / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-sha", default=None)
    args = parser.parse_args()
    manifest = build_space(args.output_dir, source_sha=args.source_sha)
    print(json.dumps({
        "status": manifest["status"],
        "source_git_sha": manifest["source_git_sha"],
        "research_claim": manifest["research_claim"],
        "bundle": str(args.output_dir),
    }))


if __name__ == "__main__":
    main()
