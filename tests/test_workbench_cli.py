from __future__ import annotations

from pathlib import Path

from shadowseed.cli import build_parser
from shadowseed.cli_dispatch import COMMAND_HANDLERS


def test_workbench_cli_contract_is_registered() -> None:
    args = build_parser().parse_args(
        [
            "workbench",
            "--workspace",
            "example-workspace",
            "--host",
            "127.0.0.1",
            "--port",
            "8877",
            "--no-browser",
        ]
    )
    assert args.command == "workbench"
    assert args.host == "127.0.0.1"
    assert args.port == 8877
    assert args.no_browser is True
    assert "workbench" in COMMAND_HANDLERS


def test_workbench_optional_dependency_is_declared() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert "workbench = [" in pyproject
    assert '"gradio>=5.0,<7"' in pyproject
