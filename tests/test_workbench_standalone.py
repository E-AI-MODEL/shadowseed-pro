from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from shadowseed.workbench.standalone import (
    _choose_loopback_port,
    build_parser,
    main,
    run_standalone_self_test,
)


def test_standalone_parser_has_no_remote_bind_option() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "--allow-remote" not in help_text
    assert "--legacy-gradio" in help_text
    args = parser.parse_args([])
    assert args.port == 7860
    assert args.workspace is None
    assert args.self_test is False
    assert args.legacy_gradio is False
    assert parser.parse_args(["--web"]).web is True


def test_standalone_defaults_to_web_client(tmp_path: Path, monkeypatch) -> None:
    import shadowseed_webapi.launcher as launcher

    calls: list[list[str]] = []
    monkeypatch.setattr(launcher, "main", lambda argv: calls.append(argv) or 0)

    assert main(["--workspace", str(tmp_path), "--no-browser", "--self-test"]) == 0
    assert main(["--workspace", str(tmp_path), "--web", "--port", "9000"]) == 0
    assert calls[0][-2:] == ["--no-browser", "--self-test"]
    assert calls[1][2:] == ["--port", "9000"]


def test_standalone_rejects_web_with_legacy_gradio(tmp_path: Path) -> None:
    assert main(["--workspace", str(tmp_path), "--web", "--legacy-gradio"]) == 1


def test_standalone_port_falls_back_to_another_loopback_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        port = int(occupied.getsockname()[1])
        chosen = _choose_loopback_port(port)
    assert chosen > 0
    assert chosen != port


def test_standalone_product_self_test(tmp_path: Path) -> None:
    pytest.importorskip("gradio")
    pytest.importorskip("httpx")
    pytest.importorskip("numpy")

    output = tmp_path / "self-test.json"
    payload = run_standalone_self_test(tmp_path / "workspace", output_path=output)

    assert payload["frozen"] is False  # source-tree execution; frozen builds assert True in CI
    assert payload["runtime_mode"] == "live"
    assert payload["comparison_generated"] is True
    assert payload["report_verified"] is True
    assert payload["support_verified"] is True
    assert payload["multiprocessing_spawn"] is None
    assert set(payload["runtime_imports"]) >= {
        "gradio",
        "httpx",
        "numpy",
    }
    assert set(payload["optional_provider_modules"]) == {
        "sentence_transformers",
        "transformers",
        "torch",
        "openai",
    }
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["artifact"] == "shadowseed_standalone_self_test"


def test_standalone_entrypoint_calls_freeze_support_before_main() -> None:
    source = Path("src/shadowseed/workbench/standalone.py").read_text(encoding="utf-8")
    entrypoint = source[source.index('if __name__ == "__main__":'):]

    assert "multiprocessing.freeze_support()" in entrypoint
    assert entrypoint.index("multiprocessing.freeze_support()") < entrypoint.index("main()")


def test_frozen_build_excludes_optional_provider_stacks() -> None:
    source = Path("scripts/build_standalone.py").read_text(encoding="utf-8")

    for module in ("sentence_transformers", "transformers", "torch", "openai"):
        assert f'"--exclude-module",\n        "{module}",' in source
    assert '"--collect-data",\n        "sentence_transformers",' not in source
    assert '"--collect-submodules",\n        "transformers.models",' not in source
    assert '"--collect-data",\n        "shadowseed_webapi",' in source
    assert "_verify_frozen_web(" in source
    assert '"web_static_assets_bundled": True' in source
