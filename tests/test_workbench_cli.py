from __future__ import annotations

import json
from pathlib import Path

from shadowseed.application.sessions import service_for_workspace
from shadowseed.cli import build_parser
from shadowseed.cli_dispatch import COMMAND_HANDLERS, execute_command


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


def test_workbench_optional_dependency_and_version_are_declared() -> None:
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.4.0"' in pyproject
    assert "workbench = [" in pyproject
    assert '"gradio>=6.0,<7"' in pyproject


def test_workbench_export_cli_roundtrip(tmp_path) -> None:
    workspace = tmp_path / "workspace"
    sessions = service_for_workspace(workspace)
    session_id = sessions.create_session(title="CLI export", profile_id="demo")
    sessions.run_turn(session_id, "What uncertainty remains?")

    report = tmp_path / "report.zip"
    args = build_parser().parse_args(
        [
            "export-workbench-report",
            session_id,
            "--workspace",
            str(workspace),
            "--output",
            str(report),
        ]
    )
    assert Path(execute_command(args)) == report.resolve()
    assert report.is_file()

    support = tmp_path / "support.zip"
    support_args = build_parser().parse_args(
        [
            "export-support-bundle",
            session_id,
            "--workspace",
            str(workspace),
            "--output",
            str(support),
        ]
    )
    assert Path(execute_command(support_args)) == support.resolve()

    verify_args = build_parser().parse_args(["verify-workbench-export", str(support)])
    verification = json.loads(execute_command(verify_args))
    assert verification["valid"] is True
    assert verification["kind"] == "support"

    assert {
        "export-workbench-report",
        "export-support-bundle",
        "verify-workbench-export",
    }.issubset(COMMAND_HANDLERS)
