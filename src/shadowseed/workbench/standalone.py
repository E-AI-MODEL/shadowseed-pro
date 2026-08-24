"""Standalone launcher for the local Shadowseed tester application.

This module is intentionally thin: it owns first-run workspace/bootstrap concerns
and delegates the product UI and all SSL authority decisions to the canonical
Workbench/controller/runtime.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import platform
import socket
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from shadowseed.application.error_safety import sanitize_error_text, sanitized_exception_line
from shadowseed.application.workspace import WorkspaceService


def _choose_loopback_port(preferred: int = 7860) -> int:
    """Return ``preferred`` when free, otherwise ask the OS for a free port."""

    candidates = [preferred, 0] if preferred else [0]
    for candidate in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", int(candidate)))
            except OSError:
                continue
            return int(sock.getsockname()[1])
    raise RuntimeError("Could not allocate a loopback port for the Shadowseed Workbench")


def _write_startup_error(workspace: Path, exc: BaseException) -> Path:
    """Persist a sanitized startup failure because GUI bundles may have no console."""

    logs = workspace / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = logs / f"standalone-startup-error-{stamp}.log"
    trace = sanitize_error_text("".join(traceback.format_exception(exc)))
    path.write_text(
        "Shadowseed standalone startup failed.\n\n"
        f"{sanitized_exception_line(exc)}\n\n"
        f"{trace}",
        encoding="utf-8",
    )
    if os.name != "nt":
        try:
            path.chmod(0o600)
        except OSError:
            pass
    return path


def _runtime_imports() -> dict[str, str]:
    """Import product dependencies so packaged self-tests catch missing modules."""

    versions: dict[str, str] = {}
    for module_name in (
        "gradio",
        "sentence_transformers",
        "transformers",
        "torch",
        "openai",
    ):
        module = importlib.import_module(module_name)
        versions[module_name] = str(getattr(module, "__version__", "present"))
    return versions


def run_standalone_self_test(
    workspace: str | Path,
    *,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Exercise the installed production-local product surface without a server."""

    from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
    from shadowseed.workbench.production_local import build_production_local_app

    service = WorkspaceService(workspace)
    paths = service.initialize()
    controller = ProductionLocalWorkbenchController(paths.root)
    session_id = controller.create_session(
        title="Standalone self-test",
        profile_id="demo",
        backend="fixture",
    )
    result = controller.send_turn(
        session_id,
        "Which uncertainty remains in this standalone smoke test?",
        compare_without_ssl=True,
    )
    if result.get("comparison") is None:
        raise RuntimeError("standalone self-test did not produce the paired SSL-off control")

    report = controller.export_report(session_id, paths.exports / "standalone-self-test-report.zip")
    support = controller.export_support_bundle(
        session_id,
        paths.exports / "standalone-self-test-support.zip",
    )
    if not controller.verify_export(report)["valid"]:
        raise RuntimeError("standalone self-test report export failed verification")
    if not controller.verify_export(support)["valid"]:
        raise RuntimeError("standalone self-test support export failed verification")
    if build_production_local_app(controller=controller) is None:
        raise RuntimeError("standalone self-test could not build the production-local UI")

    payload: dict[str, Any] = {
        "artifact": "shadowseed_standalone_self_test",
        "frozen": bool(getattr(sys, "frozen", False)),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "runtime_imports": _runtime_imports(),
        "runtime_mode": result["session"]["runtime_mode"],
        "comparison_generated": True,
        "report_verified": True,
        "support_verified": True,
        "production_local_controller": True,
        "production_resolution_ui": True,
        "workspace": str(paths.root),
    }
    destination = Path(output_path) if output_path else paths.exports / "standalone-self-test.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="Shadowseed", add_help=True)
    parser.add_argument("--workspace", default=None, help="Override the local tester workspace.")
    parser.add_argument("--port", type=int, default=7860, help="Preferred local UI port.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the browser.")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run the packaged product smoke test and exit.",
    )
    parser.add_argument("--self-test-output", default=None, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")
    os.environ.setdefault("GRADIO_SERVER_NAME", "127.0.0.1")

    service = WorkspaceService(args.workspace)
    try:
        paths = service.initialize()
        if args.self_test:
            run_standalone_self_test(paths.root, output_path=args.self_test_output)
            return 0

        from shadowseed.workbench.production_local import launch_production_local_workbench

        launch_production_local_workbench(
            paths.root,
            port=_choose_loopback_port(args.port),
            inbrowser=not args.no_browser,
        )
        return 0
    except BaseException as exc:
        try:
            workspace = service.paths.root
            log_path = _write_startup_error(workspace, exc)
            print(f"Shadowseed failed to start. Diagnostic log: {log_path}", file=sys.stderr)
            print(sanitized_exception_line(exc), file=sys.stderr)
        except Exception as logging_exc:
            print(
                "Shadowseed failed to start and the sanitized diagnostic log could not be written: "
                f"{sanitized_exception_line(logging_exc)}",
                file=sys.stderr,
            )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
