"""One-process launcher for the packaged Shadowseed web product."""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
import threading
import webbrowser
from pathlib import Path
from typing import Any

from shadowseed_webapi.server import DEFAULT_HOST, DEFAULT_PORT, create_server
from shadowseed_webapi.service import WebApiService


def packaged_static_root() -> Path:
    """Return the generated static export bundled with the Python package."""

    root = Path(__file__).resolve().with_name("static")
    if not (root / "index.html").is_file():
        raise RuntimeError(
            "Shadowseed web assets are missing from this installation. "
            "Build apps/web and sync the static export before packaging."
        )
    return root


def _static_manifest(root: Path) -> dict[str, Any]:
    manifest_path = root / "web-assets-manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("Shadowseed web asset manifest is missing")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not payload.get("files"):
        raise RuntimeError("Shadowseed web asset manifest is invalid")
    return payload


def _verify_static_assets(root: Path) -> dict[str, Any]:
    """Verify every generated asset against the packaging-time manifest."""

    payload = _static_manifest(root)
    for item in payload["files"]:
        if not isinstance(item, dict):
            raise RuntimeError("Shadowseed web asset manifest entry is invalid")
        relative = str(item.get("path") or "")
        expected = str(item.get("sha256") or "")
        path = root / relative
        if not relative or not expected or not path.is_file():
            raise RuntimeError(f"Shadowseed web asset is missing: {relative}")
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Shadowseed web asset failed integrity check: {relative}")
    return payload


def _create_server_with_fallback(
    *,
    workspace: str | Path | None,
    preferred_port: int,
    static_root: Path,
):
    """Bind the preferred loopback port or fall back to an OS-assigned port."""

    candidates = [int(preferred_port), 0] if preferred_port else [0]
    last_error: OSError | None = None
    for port in candidates:
        try:
            return create_server(
                workspace=workspace,
                host=DEFAULT_HOST,
                port=port,
                static_root=static_root,
            )
        except OSError as exc:
            last_error = exc
    raise RuntimeError("Could not allocate a loopback port for Shadowseed Web") from last_error


def run_web_self_test(
    workspace: str | Path,
    *,
    static_root: str | Path | None = None,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Exercise packaged assets and the canonical fixture runtime without networking."""

    root = Path(static_root) if static_root is not None else packaged_static_root()
    manifest = _verify_static_assets(root)
    api = WebApiService(workspace)
    created = api.create_session(
        {
            "title": "Web launcher self-test",
            "backend": "fixture",
            "authority_mode": "assisted",
        }
    )
    result = api.run_turn(
        created["session_id"],
        {
            "question": "Which boundary remains in this packaged web smoke test?",
            "request_id": "web-launcher:self-test",
        },
    )
    payload: dict[str, Any] = {
        "artifact": "shadowseed_web_launcher_self_test",
        "static_assets_verified": True,
        "static_asset_count": len(manifest["files"]),
        "api_version": api.health()["api_version"],
        "runtime_mode": result["session"]["runtime_mode"],
        "turn": result["session"]["turn"],
        "provider_ready": result["session"].get("provider_ready", True),
        "loopback_only": True,
    }
    if output_path is not None:
        destination = Path(output_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="shadowseed-web",
        description="Run the packaged Shadowseed web product on loopback.",
    )
    parser.add_argument("--workspace", default=None)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-output", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--static-root", default=None, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        static_root = (
            Path(args.static_root).resolve()
            if args.static_root
            else packaged_static_root()
        )
        _verify_static_assets(static_root)

        if args.self_test:
            run_web_self_test(
                args.workspace,
                static_root=static_root,
                output_path=args.self_test_output,
            )
            return 0

        server = _create_server_with_fallback(
            workspace=args.workspace,
            preferred_port=args.port,
            static_root=static_root,
        )
        port = int(server.server_address[1])
        url = f"http://{DEFAULT_HOST}:{port}/"
        print(f"Shadowseed Web: {url}", flush=True)
        if not args.no_browser:
            opener = threading.Timer(0.2, webbrowser.open, args=(url,))
            opener.daemon = True
            opener.start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    except BaseException as exc:
        from shadowseed.application.error_safety import sanitized_exception_line

        print(f"Shadowseed Web failed to start: {sanitized_exception_line(exc)}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
