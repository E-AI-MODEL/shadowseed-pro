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
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
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
    intel_macos = sys.platform == "darwin" and platform.machine().lower() == "x86_64"
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
        "--collect-submodules",
        "openai",
        "--hidden-import",
        "socksio",
    ]
    metadata_packages = [
        "shadowseed",
        "gradio",
        "gradio_client",
        "fastapi",
        "pydantic",
        "openai",
    ]
    if not intel_macos:
        command.extend(
            [
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
            ]
        )
        metadata_packages.extend(
            [
                "huggingface_hub",
                "sentence-transformers",
                "transformers",
                "torch",
            ]
        )
    for package in metadata_packages:
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


def _install_macos_first_launch_files(
    distribution_dir: Path,
    *,
    machine: str | None = None,
) -> tuple[Path, Path]:
    """Create a terminal-backed macOS launcher with visible diagnostics."""

    expected_machine = (machine or platform.machine()).lower() or "unknown"
    helper = distribution_dir / "Open Shadowseed.command"
    helper.write_text(
        "#!/bin/bash\n"
        "set -u\n"
        "HERE=\"$(cd \"$(dirname \"$0\")\" && pwd)\"\n"
        "APP=\"$HERE/Shadowseed.app\"\n"
        "BIN=\"$APP/Contents/MacOS/Shadowseed\"\n"
        f"EXPECTED_ARCH=\"{expected_machine}\"\n"
        "if [ ! -x \"$BIN\" ]; then\n"
        "  echo \"Shadowseed executable was not found next to this helper.\" >&2\n"
        "  read -r -p \"Press Enter to close...\" _ || true\n"
        "  exit 1\n"
        "fi\n"
        "HOST_ARCH=\"$(uname -m)\"\n"
        "if [ \"$HOST_ARCH\" = \"x86_64\" ] && [ \"$EXPECTED_ARCH\" = \"arm64\" ]; then\n"
        "  echo \"This is the Apple Silicon build, but this Mac is Intel.\" >&2\n"
        "  echo \"Download the darwin-x86_64 Shadowseed Workbench archive.\" >&2\n"
        "  read -r -p \"Press Enter to close...\" _ || true\n"
        "  exit 1\n"
        "fi\n"
        "xattr -dr com.apple.quarantine \"$APP\" 2>/dev/null || true\n"
        "cd \"$HERE\"\n"
        "echo \"Starting Shadowseed Workbench ($EXPECTED_ARCH)...\"\n"
        "echo \"Keep this Terminal window open while using Shadowseed.\"\n"
        "\"$BIN\"\n"
        "STATUS=$?\n"
        "if [ \"$STATUS\" -ne 0 ]; then\n"
        "  echo \"\" >&2\n"
        "  echo \"Shadowseed stopped during startup (exit $STATUS).\" >&2\n"
        "  LOG_DIR=\"$HOME/.shadowseed/logs\"\n"
        "  LATEST_LOG=\"$(ls -t \"$LOG_DIR\"/standalone-startup-error-*.log 2>/dev/null | head -n 1 || true)\"\n"
        "  if [ -n \"$LATEST_LOG\" ]; then\n"
        "    echo \"Diagnostic log: $LATEST_LOG\" >&2\n"
        "    echo \"---\" >&2\n"
        "    cat \"$LATEST_LOG\" >&2 || true\n"
        "  fi\n"
        "  read -r -p \"Press Enter to close...\" _ || true\n"
        "fi\n"
        "exit \"$STATUS\"\n",
        encoding="utf-8",
    )
    helper.chmod(0o755)

    readme = distribution_dir / "README_FIRST_START.txt"
    readme.write_text(
        "Shadowseed Workbench for macOS\n"
        "=============================\n\n"
        f"This archive was built for: {expected_machine}.\n"
        "Use the darwin-arm64 archive on Apple Silicon and the darwin-x86_64\n"
        "archive on Intel Macs.\n\n"
        "This build is ad-hoc signed and does not require an Apple Developer ID.\n"
        "Because browsers may add a macOS quarantine flag, start Shadowseed via\n"
        "Open Shadowseed.command. The helper removes quarantine only from the\n"
        "bundled Shadowseed.app and runs its executable directly.\n\n"
        "Start:\n"
        "1. Keep Shadowseed.app and Open Shadowseed.command in this folder.\n"
        "2. Double-click Open Shadowseed.command.\n"
        "3. If macOS asks whether Terminal may open it, allow it.\n"
        "4. Keep the Terminal window open while using Shadowseed.\n"
        "5. The Workbench opens in your browser on 127.0.0.1.\n\n"
        "If startup fails, the Terminal window remains available and shows the\n"
        "path to the sanitized diagnostic log in ~/.shadowseed/logs.\n"
        "The helper does not change global macOS security.\n",
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
        _install_macos_first_launch_files(
            distribution_dir,
            machine=platform.machine().lower() or "unknown",
        )
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
    for required in ("gradio", "openai"):
        if required not in imports or imports.get(required) == "not-bundled":
            raise RuntimeError(f"packaged self-test is missing runtime dependency: {required}")

    intel_macos = sys.platform == "darwin" and platform.machine().lower() == "x86_64"
    local_stack = ("sentence_transformers", "transformers", "torch")
    if intel_macos:
        if payload.get("local_hf_stack_bundled") is not False:
            raise RuntimeError("Intel macOS bundle unexpectedly claims local HF stack")
    else:
        for required in local_stack:
            if required not in imports or imports.get(required) == "not-bundled":
                raise RuntimeError(
                    f"packaged self-test is missing runtime dependency: {required}"
                )
        if payload.get("local_hf_stack_bundled") is not True:
            raise RuntimeError("standalone bundle did not prove local HF stack availability")
    return payload


def _verify_frozen_server_startup(
    executable: Path,
    root: Path,
    work_dir: Path,
    *,
    timeout_seconds: float = 90.0,
) -> dict[str, object]:
    """Prove that the frozen product starts its real loopback web server."""

    work_dir.mkdir(parents=True, exist_ok=True)
    launch_cwd = work_dir / "launch-cwd"
    launch_cwd.mkdir(parents=True, exist_ok=True)
    workspace = work_dir / "server-probe-workspace"
    log_path = work_dir / "server-startup.log"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = int(sock.getsockname()[1])

    command = [
        str(executable),
        "--workspace",
        str(workspace),
        "--port",
        str(port),
        "--no-browser",
    ]
    print("+", " ".join(command), flush=True)
    env = os.environ.copy()
    env["GRADIO_ANALYTICS_ENABLED"] = "False"
    with log_path.open("wb") as log_handle:
        process = subprocess.Popen(
            command,
            cwd=launch_cwd,
            env=env,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + timeout_seconds
            url = f"http://127.0.0.1:{port}/"
            last_error = "server did not answer"
            while time.monotonic() < deadline:
                returncode = process.poll()
                if returncode is not None:
                    last_error = f"frozen server exited early with code {returncode}"
                    break
                try:
                    with urllib.request.urlopen(url, timeout=2.0) as response:
                        status = int(response.status)
                    if 200 <= status < 500:
                        return {
                            "started": True,
                            "host": "127.0.0.1",
                            "http_status": status,
                        }
                    last_error = f"unexpected HTTP status {status}"
                except (OSError, urllib.error.URLError) as exc:
                    last_error = f"{type(exc).__name__}: {exc}"
                time.sleep(1.0)

            log_handle.flush()
            details = log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(
                f"frozen server startup probe failed: {last_error}\n{details[-8000:]}"
            )
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=10)


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
    server_startup_probe = (
        None
        if skip_self_test
        else _verify_frozen_server_startup(
            executable,
            root,
            work_dir / "server-startup-probe",
        )
    )
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
    archive_roundtrip_server_probe = None
    if roundtrip_bundle is not None and not skip_self_test:
        roundtrip_executable = roundtrip_bundle / "Contents" / "MacOS" / "Shadowseed"
        if not roundtrip_executable.is_file():
            raise RuntimeError("round-tripped macOS bundle is missing its executable")
        archive_roundtrip_self_test = _verify_frozen(
            roundtrip_executable,
            root,
            work_dir / "archive-roundtrip-self-test",
        )
        archive_roundtrip_server_probe = _verify_frozen_server_startup(
            roundtrip_executable,
            root,
            work_dir / "archive-roundtrip-server-probe",
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
        "local_hf_stack_bundled": bool(
            self_test and self_test.get("local_hf_stack_bundled")
        ),
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
        "server_startup_probe": server_startup_probe,
        "archive_roundtrip_server_probe": archive_roundtrip_server_probe,
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
