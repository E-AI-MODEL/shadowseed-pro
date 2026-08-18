"""Build and verify a self-contained Shadowseed Workbench bundle.

The produced archive contains its own Python runtime. Model weights are not
bundled; local/hosted model acquisition remains an explicit user choice.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


def _run(command: list[str], *, cwd: Path) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True)


def _source_sha(root: Path) -> str:
    env_sha = os.environ.get("SHADOWSEED_SOURCE_SHA") or os.environ.get("GITHUB_SHA")
    if env_sha:
        return env_sha.strip()
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _project_version(root: Path) -> str:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
        import tomli as tomllib  # type: ignore[no-redef]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return str(data["project"]["version"])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pyinstaller_command(root: Path, dist_dir: Path, work_dir: Path) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name",
        "Shadowseed",
        "--paths",
        str(root / "src"),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(work_dir / "spec"),
        "--collect-data",
        "shadowseed",
        "--collect-data",
        "gradio",
        "--collect-data",
        "gradio_client",
        "--collect-data",
        "sentence_transformers",
        "--collect-data",
        "transformers",
        "--collect-submodules",
        "sentence_transformers",
        "--collect-submodules",
        "transformers.models",
        "--collect-submodules",
        "openai",
        "--hidden-import",
        "socksio",
    ]
    for package in (
        "shadowseed",
        "gradio",
        "gradio_client",
        "fastapi",
        "pydantic",
        "huggingface_hub",
        "sentence-transformers",
        "transformers",
        "torch",
        "openai",
    ):
        command.extend(["--copy-metadata", package])
    command.append(str(root / "src" / "shadowseed" / "workbench" / "standalone.py"))
    return command


def _executable_path(dist_dir: Path) -> Path:
    if sys.platform == "darwin":
        return dist_dir / "Shadowseed.app" / "Contents" / "MacOS" / "Shadowseed"
    if os.name == "nt":
        return dist_dir / "Shadowseed" / "Shadowseed.exe"
    return dist_dir / "Shadowseed" / "Shadowseed"


def _bundle_path(dist_dir: Path) -> Path:
    if sys.platform == "darwin":
        return dist_dir / "Shadowseed.app"
    return dist_dir / "Shadowseed"


def _archive_bundle(bundle: Path, output_dir: Path, stem: str) -> Path:
    if sys.platform == "darwin":
        archive = output_dir / f"{stem}.zip"
        _run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(bundle),
                str(archive),
            ],
            cwd=bundle.parent,
        )
        return archive
    if os.name == "nt":
        archive_base = output_dir / stem
        archive = Path(
            shutil.make_archive(
                str(archive_base),
                "zip",
                root_dir=bundle.parent,
                base_dir=bundle.name,
            )
        )
        return archive

    archive = output_dir / f"{stem}.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(bundle, arcname=bundle.name)
    return archive


def _verify_frozen(executable: Path, root: Path, work_dir: Path) -> dict[str, object]:
    workspace = work_dir / "self-test-workspace"
    result_file = work_dir / "standalone-self-test.json"
    _run(
        [
            str(executable),
            "--self-test",
            "--workspace",
            str(workspace),
            "--self-test-output",
            str(result_file),
        ],
        cwd=root,
    )
    payload = json.loads(result_file.read_text(encoding="utf-8"))
    required_true = (
        "frozen",
        "comparison_generated",
        "report_verified",
        "support_verified",
    )
    for key in required_true:
        if payload.get(key) is not True:
            raise RuntimeError(f"packaged self-test did not prove {key}=true")
    if payload.get("runtime_mode") != "live":
        raise RuntimeError("packaged self-test did not use the live product runtime")
    imports = payload.get("runtime_imports", {})
    for required in ("gradio", "sentence_transformers", "transformers", "torch", "openai"):
        if required not in imports:
            raise RuntimeError(f"packaged self-test is missing runtime dependency: {required}")
    return payload


def build(output_dir: Path, *, skip_self_test: bool = False) -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    output_dir = output_dir.resolve()
    dist_dir = root / "build" / "standalone-dist"
    work_dir = root / "build" / "standalone-work"
    shutil.rmtree(dist_dir, ignore_errors=True)
    shutil.rmtree(work_dir, ignore_errors=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "spec").mkdir(parents=True, exist_ok=True)

    _run(_pyinstaller_command(root, dist_dir, work_dir), cwd=root)
    executable = _executable_path(dist_dir)
    bundle = _bundle_path(dist_dir)
    if not executable.is_file() or not bundle.exists():
        raise RuntimeError(f"PyInstaller output is incomplete: {bundle}")

    self_test = None if skip_self_test else _verify_frozen(executable, root, work_dir)
    version = _project_version(root)
    machine = platform.machine().lower() or "unknown"
    system = platform.system().lower() or sys.platform
    stem = f"shadowseed-workbench-{version}-{system}-{machine}"
    archive = _archive_bundle(bundle, output_dir, stem)

    manifest: dict[str, object] = {
        "artifact": "shadowseed_standalone_bundle",
        "version": version,
        "source_sha": _source_sha(root),
        "system": system,
        "machine": machine,
        "python": platform.python_version(),
        "pyinstaller": importlib.metadata.version("pyinstaller"),
        "archive": archive.name,
        "archive_size": archive.stat().st_size,
        "archive_sha256": _sha256(archive),
        "model_weights_bundled": False,
        "self_contained_python_runtime": True,
        "loopback_only_default": True,
        "self_test": self_test,
    }
    manifest_path = output_dir / f"{stem}.manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="release-assets")
    parser.add_argument("--skip-self-test", action="store_true")
    args = parser.parse_args(argv)
    build(Path(args.output_dir), skip_self_test=args.skip_self_test)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
