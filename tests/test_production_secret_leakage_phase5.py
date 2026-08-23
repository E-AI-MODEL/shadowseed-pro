"""Production-local negative tests for credential leakage in logs, exports, and errors."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController
from shadowseed.workbench.standalone import _write_startup_error


def _archive_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        return "\n".join(
            archive.read(name).decode("utf-8", errors="replace")
            for name in archive.namelist()
        )


def test_environment_secret_is_absent_from_report_and_support_exports(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sentinel = "sk-PRODUCTION-EXPORT-SECRET-SENTINEL"
    monkeypatch.setenv("OPENAI_API_KEY", sentinel)
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Secret export check",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    controller.send_turn(session_id, "What export metadata is safe to share?")

    report = Path(controller.export_report(session_id, tmp_path / "report.zip"))
    support = Path(controller.export_support_bundle(session_id, tmp_path / "support.zip"))

    assert sentinel not in _archive_text(report)
    assert sentinel not in _archive_text(support)


def test_production_controller_redacts_environment_secret_from_raised_error_and_log(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sentinel = "sk-PRODUCTION-ERROR-SECRET-SENTINEL"
    monkeypatch.setenv("OPENAI_API_KEY", sentinel)
    controller = ProductionLocalWorkbenchController(tmp_path / "workspace")

    def _leaking_provider_failure(*args, **kwargs):
        raise RuntimeError(f"provider rejected api_key={sentinel}")

    monkeypatch.setattr(WorkbenchController, "send_turn", _leaking_provider_failure)

    with pytest.raises(RuntimeError) as caught:
        controller.send_turn("session::synthetic", "hello")

    rendered = str(caught.value)
    assert sentinel not in rendered
    assert "<redacted-secret>" in rendered
    assert sentinel not in controller.operations.path.read_text(encoding="utf-8")


def test_standalone_startup_diagnostic_redacts_environment_secret(
    tmp_path: Path,
    monkeypatch,
) -> None:
    sentinel = "sk-PRODUCTION-STARTUP-SECRET-SENTINEL"
    monkeypatch.setenv("OPENAI_API_KEY", sentinel)
    error = RuntimeError(f"Authorization: Bearer {sentinel}")

    path = _write_startup_error(tmp_path / "workspace", error)
    text = path.read_text(encoding="utf-8")

    assert sentinel not in text
    assert "<redacted-secret>" in text
