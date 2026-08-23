from __future__ import annotations

from pathlib import Path

from shadowseed.application.health import run_doctor


def test_doctor_reports_production_integrity_and_permissions(tmp_path: Path) -> None:
    report = run_doctor(tmp_path / "workspace")
    checks = {check.name: check for check in report.checks}

    assert checks["workspace"].status == "ok"
    assert checks["production_integrity"].status == "ok"
    assert checks["workspace_permissions"].status == "ok"


def test_doctor_workspace_error_has_recovery_guidance(tmp_path: Path) -> None:
    root = tmp_path / "workspace"
    first = run_doctor(root)
    assert first.ready

    identity = root / "workspace.id"
    identity.write_text("not-a-workspace-id\n", encoding="utf-8")
    report = run_doctor(root)
    workspace = next(check for check in report.checks if check.name == "workspace")

    assert workspace.status == "error"
    assert workspace.repair is not None
    assert "workspace restore" in workspace.repair
