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
        "--additional-hooks-dir",
        str(root / "scripts" / "pyinstaller_hooks"),
        "--distpath",
        str(dist_dir),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(work_dir / "spec"),
        "--collect-data",
        "shadowseed",
        "--collect-data",
        "gradio_client",
        "--collect-data",
        "safehttpx",
        "--collect-data",
        "groovy",
        "--collect-data",
        "sentence_transformers",
        "--collect-data",
        "transformers",
        "--collect-submodules",
        "sentence_transformers",
        "--collect-submodules",
        "transformers.models",
        "--collect-submodules",
        "scipy._external.array_api_compat",
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
        command.extend(["--copy-metadata", package])    command.append(str(root / "src" / "shadowseed" / "workbench" / "standalone.py"))
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


def _install_license(root: Path, bundle: Path, *, macos: bool | None = None) -> Path:
    """Copy the repository license into the user-visible frozen bundle."""

    source = root / "LICENSE"
    if not source.is_file():
        raise RuntimeError("standalone build requires repository LICENSE")
    if macos is None:
        macos = sys.platform == "darwin"
    target = (
        bundle / "Contents" / "Resources" / "SHADOWSEED_LICENSE.txt"
        if macos
        else bundle / "SHADOWSEED_LICENSE.txt"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    if _sha256(target) != _sha256(source):
        raise RuntimeError("standalone license copy failed integrity check")
    return target


def _verify_macos_bundle(bundle: Path, *, macos: bool | None = None) -> None:
    """Fail closed if the final macOS application resource seal is invalid."""

    if macos is None:
        macos = sys.platform == "darwin"
    if not macos:
        return
    _run(
        ["codesign", "--verify", "--deep", "--strict", "--verbose=4", str(bundle)],
        cwd=bundle.parent,
    )


def _seal_macos_bundle(bundle: Path, *, macos: bool | None = None) -> str | None:
    """Apply and verify an ad-hoc macOS resource seal.

    This project deliberately does not require Apple Developer ID credentials.
    Browser-downloaded archives may therefore retain macOS quarantine. The
    distributable ZIP includes a first-launch helper that removes quarantine
    only from the bundled Shadowseed.app before opening it.
    """

    if macos is None:
        macos = sys.platform == "darwin"
    if not macos:
        return None
    _run(
        [
            "codesign",
            "--force",
            "--sign",
            "-",
            "--timestamp=none",
            str(bundle),
        ],
        cwd=bundle.parent,
    )
    _verify_macos_bundle(bundle, macos=True)
    return "adhoc"


def _install_macos_first_launch_files(distribution_dir: Path) -> tuple[Path, Path]:
    """Create the no-credentials first-launch helper and user instructions."""

    helper = distribution_dir / "Open Shadowseed.command"
    helper.write_text(
        "#!/bin/bash\n"
        "set -euo pipefail\n"
        "HERE=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
        "APP=\"$HERE/Shadowseed.app\"\n"
        "if [ ! -d \"$APP\" ]; then\n"
        "  echo \"Shadowseed.app was not found next to this helper.\" >&2\n"
        "  exit 1\n"
        "fi\n"
        "xattr -dr com.apple.quarantine \"$APP\" 2>/dev/null || true\n"
        "open \"$APP\"\n",
        encoding="utf-8",
    )
    helper.chmod(0o755)

    readme = distribution_dir / "README_FIRST_START.txt"
    readme.write_text(
        "Shadowseed Workbench for macOS\n"
        "=============================\n\n"
        "This build is ad-hoc signed and does not require an Apple Developer ID.\n"
        "Because browsers may add a macOS quarantine flag, the first launch can\n"
        "be blocked by Gatekeeper even though the app bundle seal is valid.\n\n"
        "First launch:\n"
        "1. Keep Shadowseed.app and Open Shadowseed.command in this folder.\n"
        "2. Double-click Open Shadowseed.command.\n"
        "3. If macOS asks whether Terminal may open it, allow it.\n"
        "4. Later launches can use Shadowseed.app normally.\n\n"
        "The helper removes com.apple.quarantine only from this Shadowseed.app\n"
        "and then opens the app. It does not change global macOS security.\n",
        encoding="utf-8",
    )
    return helper, readme


def _archive_bundle(bundle: Path, output_dir: Path, stem: str) -> Path:
    if sys.platform == "darwin":
        archive = output_dir / f"{stem}.zip"
        distribution_dir = output_dir / "Shadowseed Workbench"
        shutil.rmtree(distribution_dir, ignore_errors=True)
        distribution_dir.mkdir(parents=True)
        copied_bundle = distribution_dir / bundle.name
        _run(["ditto", str(bundle), str(copied_bundle)], cwd=bundle.parent)
        _verify_macos_bundle(copied_bundle, macos=True)
        _install_macos_first_launch_files(distribution_dir)
        _run(
            [
                "ditto",
                "-c",
                "-k",
                "--sequesterRsrc",
                "--keepParent",
                str(distribution_dir),
                str(archive),
            ],
            cwd=output_dir,
        )
        shutil.rmtree(distribution_dir)
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


def _verify_macos_archive_round_trip(
    archive: Path,
    work_dir: Path,
    *,
    macos: bool | None = None,
) -> Path | None:
    """Extract the distributable ZIP and verify the exact macOS user bundle."""

    if macos is None:
        macos = sys.platform == "darwin"
    if not macos:
        return None
    extract_dir = work_dir / "archive-roundtrip"
    shutil.rmtree(extract_dir, ignore_errors=True)
    extract_dir.mkdir(parents=True, exist_ok=True)
    _run(["ditto", "-x", "-k", str(archive), str(extract_dir)], cwd=work_dir)
    bundles = list(extract_dir.rglob("Shadowseed.app"))
    if len(bundles) != 1:
        raise RuntimeError(
            f"macOS archive round-trip expected one Shadowseed.app, found {len(bundles)}"
        )
    bundle = bundles[0]
    _verify_macos_bundle(bundle, macos=True)
    helper = bundle.parent / "Open Shadowseed.command"
    readme = bundle.parent / "README_FIRST_START.txt"
    if not helper.is_file() or not os.access(helper, os.X_OK):
        raise RuntimeError("macOS archive round-trip is missing executable first-launch helper")
    if not readme.is_file():
        raise RuntimeError("macOS archive round-trip is missing first-launch README")
    return bundle


def _verify_frozen(executable: Path, root: Path, work_dir: Path) -> dict[str, object]:
    work_dir.mkdir(parents=True, exist_ok=True)
    workspace = work_dir / "self-test-workspace"
    result_file = work_dir / "standalone-self-test.json"
    command = [
        str(executable),
        "--self-test",
        "--workspace",
        str(workspace),
        "--self-test-output",
        str(result_file),
    ]
    print("+", " ".join(command), flush=True)
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode != 0:
        logs = sorted((workspace / "logs").glob("standalone-startup-error-*.log"))
        if logs:
            print("\n===== frozen startup diagnostic =====", file=sys.stderr)
            print(logs[-1].read_text(encoding="utf-8", errors="replace"), file=sys.stderr)
            print("===== end frozen startup diagnostic =====\n", file=sys.stderr)
        raise subprocess.CalledProcessError(completed.returncode, command)
    if not result_file.is_file():
        raise RuntimeError("frozen self-test exited successfully without writing its result artifact")

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

    license_path = _install_license(root, bundle)
    license_relative = str(license_path.relative_to(bundle))
    license_sha256 = _sha256(license_path)
    self_test = None if skip_self_test else _verify_frozen(executable, root, work_dir)
    macos_signature_mode = _seal_macos_bundle(bundle)
    macos_notarized = False if sys.platform == "darwin" else None

    version = _project_version(root)
    machine = platform.machine().lower() or "unknown"
    system = platform.system().lower() or sys.platform
    stem = f"shadowseed-workbench-{version}-{system}-{machine}"
    archive = _archive_bundle(bundle, output_dir, stem)

    roundtrip_bundle = _verify_macos_archive_round_trip(
        archive,
        work_dir,
    )
    archive_roundtrip_self_test = None
    if roundtrip_bundle is not None and not skip_self_test:
        roundtrip_executable = roundtrip_bundle / "Contents" / "MacOS" / "Shadowseed"
        if not roundtrip_executable.is_file():
            raise RuntimeError("round-tripped macOS bundle is missing its executable")
        archive_roundtrip_self_test = _verify_frozen(
            roundtrip_executable,
            root,
            work_dir / "archive-roundtrip-self-test",
        )

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
        "license_file": license_relative,
        "license_sha256": license_sha256,
        "license_identifier": "PolyForm-Noncommercial-1.0.0",
        "model_weights_bundled": False,
        "self_contained_python_runtime": True,
        "loopback_only_default": True,
        "gradio_source_files_bundled": True,
        "macos_signature_mode": macos_signature_mode if system == "darwin" else None,
        "macos_bundle_seal_verified": macos_signature_mode is not None if system == "darwin" else None,
        "macos_notarized": macos_notarized if system == "darwin" else None,
        "macos_gatekeeper_assessed": False if system == "darwin" else None,
        "macos_first_launch_helper": roundtrip_bundle is not None if system == "darwin" else None,
        "macos_archive_roundtrip_verified": roundtrip_bundle is not None if system == "darwin" else None,
        "archive_roundtrip_self_test": archive_roundtrip_self_test,
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
