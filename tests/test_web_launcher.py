from __future__ import annotations

import hashlib
import json
import socket
from pathlib import Path

import pytest

from scripts.sync_web_assets import sync_web_assets
from shadowseed_webapi.launcher import (
    _create_server_with_fallback,
    _verify_static_assets,
    build_parser,
    run_web_self_test,
)


def _write_static_fixture(root: Path) -> None:
    asset = root / "_next" / "static" / "chunks" / "app.js"
    asset.parent.mkdir(parents=True)
    index = root / "index.html"
    index.write_text("<!doctype html><title>Shadowseed</title>", encoding="utf-8")
    asset.write_text("console.log('shadowseed')", encoding="utf-8")
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        files.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    (root / "web-assets-manifest.json").write_text(
        json.dumps(
            {
                "artifact": "shadowseed_web_static_export",
                "files": files,
            }
        ),
        encoding="utf-8",
    )


def test_web_launcher_parser_has_no_remote_bind_option() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "--host" not in help_text
    assert "--allow-remote" not in help_text
    args = parser.parse_args([])
    assert args.port == 8765
    assert args.no_browser is False


def test_web_launcher_static_integrity_detects_tampering(tmp_path: Path) -> None:
    root = tmp_path / "static"
    _write_static_fixture(root)
    assert _verify_static_assets(root)["files"]

    (root / "index.html").write_text("tampered", encoding="utf-8")
    with pytest.raises(RuntimeError, match="failed integrity check"):
        _verify_static_assets(root)


def test_web_launcher_self_test_uses_canonical_fixture_runtime(tmp_path: Path) -> None:
    root = tmp_path / "static"
    _write_static_fixture(root)
    output = tmp_path / "self-test.json"

    payload = run_web_self_test(
        tmp_path / "workspace",
        static_root=root,
        output_path=output,
    )

    assert payload["static_assets_verified"] is True
    assert payload["static_asset_count"] >= 2
    assert payload["api_version"] == "v1"
    assert payload["runtime_mode"] == "live"
    assert payload["turn"] == 1
    assert payload["loopback_only"] is True
    assert json.loads(output.read_text(encoding="utf-8")) == payload


def test_web_launcher_falls_back_when_preferred_port_is_busy(tmp_path: Path) -> None:
    root = tmp_path / "static"
    _write_static_fixture(root)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        preferred = int(occupied.getsockname()[1])
        server = _create_server_with_fallback(
            workspace=tmp_path / "workspace",
            preferred_port=preferred,
            static_root=root,
        )
    try:
        assert int(server.server_address[1]) > 0
        assert int(server.server_address[1]) != preferred
    finally:
        server.server_close()



def test_sync_web_assets_builds_integrity_manifest(tmp_path: Path) -> None:
    source = tmp_path / "out"
    asset = source / "_next" / "static" / "chunks" / "bundle.js"
    asset.parent.mkdir(parents=True)
    (source / "index.html").write_text("<html>packaged</html>", encoding="utf-8")
    asset.write_text("console.log('bundle')", encoding="utf-8")
    target = tmp_path / "package-static"

    payload = sync_web_assets(source, target)

    assert (target / "index.html").is_file()
    assert (target / "_next" / "static" / "chunks" / "bundle.js").is_file()
    assert (target / "web-assets-manifest.json").is_file()
    assert len(payload["files"]) == 2
    assert _verify_static_assets(target)["artifact"] == "shadowseed_web_static_export"


def test_web_launcher_rejects_manifest_path_escape(tmp_path: Path) -> None:
    root = tmp_path / "static"
    root.mkdir()
    outside = tmp_path / "outside.js"
    outside.write_text("secret", encoding="utf-8")
    (root / "index.html").write_text("ok", encoding="utf-8")
    (root / "web-assets-manifest.json").write_text(
        json.dumps(
            {
                "artifact": "shadowseed_web_static_export",
                "files": [
                    {
                        "path": "../outside.js",
                        "size": outside.stat().st_size,
                        "sha256": hashlib.sha256(outside.read_bytes()).hexdigest(),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="missing or unsafe"):
        _verify_static_assets(root)
