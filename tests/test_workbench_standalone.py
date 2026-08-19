from __future__ import annotations

import json
import socket
from pathlib import Path

import pytest

from shadowseed.workbench.standalone import (
    _choose_loopback_port,
    build_parser,
    run_standalone_self_test,
)


def test_standalone_parser_has_no_remote_bind_option() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    assert "--allow-remote" not in help_text
    args = parser.parse_args([])
    assert args.port == 7860
    assert args.workspace is None
    assert args.self_test is False


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
    pytest.importorskip("sentence_transformers")
    pytest.importorskip("transformers")
    pytest.importorskip("torch")
    pytest.importorskip("openai")

    output = tmp_path / "self-test.json"
    payload = run_standalone_self_test(tmp_path / "workspace", output_path=output)

    assert payload["frozen"] is False  # source-tree execution; frozen builds assert True in CI
    assert payload["runtime_mode"] == "live"
    assert payload["comparison_generated"] is True
    assert payload["report_verified"] is True
    assert payload["support_verified"] is True
    assert set(payload["runtime_imports"]) >= {
        "gradio",
        "sentence_transformers",
        "transformers",
        "torch",
        "openai",
    }
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert persisted["artifact"] == "shadowseed_standalone_self_test"
