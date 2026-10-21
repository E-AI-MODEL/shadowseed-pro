"""Candidate web-only frozen bundle. No Gradio dependency or release publishing.

Reuses established archive/signature helpers from build_standalone.py, but
the executable is the existing shadowseed-web launcher, not the Gradio UI.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

from build_standalone import (
    _archive_bundle,
    _bundle_path,
    _executable_path,
    _install_license,
    _project_version,
    _run,
    _seal_macos_bundle,
    _sha256,
    _source_sha,
    _verify_macos_archive_round_trip,
)


EXCLUDED_DISTRIBUTIONS = frozenset(
    {"gradio", "gradio-client", "pillow", "torch", "transformers", "openai"}
)


def _web_pyinstaller_command(root: Path, dist: Path, work: Path) -> list[str]:
    command = [
        sys.executable, "-m", "PyInstaller",
        "--clean", "--noconfirm", "--onedir", "--windowed",
        "--name", "Shadowseed",
        "--paths", str(root / "src"),
        "--distpath", str(dist),
        "--workpath", str(work),
        "--specpath", str(work / "spec"),
        "--collect-data", "shadowseed",
        "--collect-data", "shadowseed_webapi",
    ]
    for package in sorted(EXCLUDED_DISTRIBUTIONS | {"sentence_transformers", "gradio_client"}):
        command.extend(["--exclude-module", package.replace("-", "_")])
    for package in ("shadowseed", "numpy"):
        command.extend(["--copy-metadata", package])
    command.append(str(root / "src" / "shadowseed_webapi" / "launcher.py"))
    return command


def _assert_no_legacy_runtime(bundle: Path) -> None:
    """Inspect collected filesystem; exclude-module alone is not proof."""
    found: list[str] = []
    for path in bundle.rglob("*"):
        name = path.name.lower().replace("_", "-")
        if (
            any(
                name == package
                or name.startswith(package + ".")
                or name.startswith(package + "-")
                for package in EXCLUDED_DISTRIBUTIONS
            )
            and (path.is_file() or path.is_dir())
        ):
            found.append(str(path.relative_to(bundle)))
    if found:
        raise RuntimeError(f"Forbidden legacy package in web bundle: {found[:20]}")


def _smoke(executable: Path, workspace: Path) -> dict[str, object]:
    destination = workspace.parent / "web-smoke.json"
    command = [
        str(executable), "--self-test", "--workspace", str(workspace),
        "--self-test-output", str(destination),
    ]
    subprocess.run(command, check=True, timeout=120)
    payload = json.loads(destination.read_text(encoding="utf-8"))
    for key in ("static_assets_verified", "loopback_only"):
        if payload.get(key) is not True:
            raise RuntimeError(f"Frozen web launcher did not prove {key}")
    if payload.get("runtime_mode") != "live" or payload.get("turn") != 1:
        raise RuntimeError("Frozen web launcher did not complete a canonical fixture turn")
    return payload


def build(output_dir: Path) -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    output_dir = output_dir.resolve()
    dist = root / "build" / "web-standalone-dist"
    work = root / "build" / "web-standalone-work"
    shutil.rmtree(dist, ignore_errors=True)
    shutil.rmtree(work, ignore_errors=True)
    (work / "spec").mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    static = root / "src" / "shadowseed_webapi" / "static"
    if not (static / "index.html").is_file() or not (static / "web-assets-manifest.json").is_file():
        raise RuntimeError("Web export missing; run npm build and sync_web_assets.py first")

    _run(_web_pyinstaller_command(root, dist, work), cwd=root)
    bundle = _bundle_path(dist)
    executable = _executable_path(dist)
    if not executable.is_file():
        raise RuntimeError(f"Frozen web executable missing: {executable}")
    _assert_no_legacy_runtime(bundle)
    license_path = _install_license(root, bundle)
    smoke = _smoke(executable, work / "first-smoke" / "workspace")

    macos_signature = _seal_macos_bundle(bundle)
    system = platform.system().lower() or sys.platform
    machine = platform.machine().lower() or "unknown"
    stem = f"shadowseed-web-{_project_version(root)}-{system}-{machine}"
    archive = _archive_bundle(bundle, output_dir, stem)
    roundtrip_bundle = _verify_macos_archive_round_trip(archive, work)
    roundtrip_smoke = None
    if roundtrip_bundle is not None:
        _assert_no_legacy_runtime(roundtrip_bundle)
        roundtrip_smoke = _smoke(
            roundtrip_bundle / "Contents" / "MacOS" / "Shadowseed",
            work / "roundtrip-smoke" / "workspace",
        )

    manifest: dict[str, object] = {
        "artifact": "shadowseed_web_only_candidate",
        "release_approved": False,
        "version": _project_version(root),
        "source_sha": _source_sha(root),
        "system": system,
        "machine": machine,
        "python": platform.python_version(),
        "pyinstaller": importlib.metadata.version("pyinstaller"),
        "archive": archive.name,
        "archive_sha256": _sha256(archive),
        "license_file": str(license_path.relative_to(bundle)),
        "license_sha256": _sha256(license_path),
        "self_contained_python_runtime": True,
        "loopback_only_default": True,
        "web_static_assets_bundled": True,
        "gradio_source_files_bundled": False,
        "legacy_packages_excluded": sorted(EXCLUDED_DISTRIBUTIONS),
        "macos_signature_mode": macos_signature,
        "macos_archive_roundtrip_verified": roundtrip_bundle is not None if system == "darwin" else None,
        "self_test": smoke,
        "archive_roundtrip_web_self_test": roundtrip_smoke,
    }
    (output_dir / f"{stem}.manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="web-candidate-assets")
    args = parser.parse_args()
    print(json.dumps(build(Path(args.output_dir)), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
