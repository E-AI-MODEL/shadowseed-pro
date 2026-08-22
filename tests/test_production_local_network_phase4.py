from __future__ import annotations

import inspect
from pathlib import Path

from shadowseed.workbench import production_local


def test_production_local_launcher_exposes_no_remote_host_override() -> None:
    parameters = inspect.signature(production_local.launch_production_local_workbench).parameters
    assert "host" not in parameters
    assert "allow_remote" not in parameters
    assert production_local.PRODUCTION_LOCAL_HOST == "127.0.0.1"


def test_production_local_launcher_forces_loopback(monkeypatch, tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    def fake_launch(workspace, **kwargs):
        captured["workspace"] = workspace
        captured.update(kwargs)
        return "launched"

    import shadowseed.workbench.app as app

    monkeypatch.setattr(app, "launch_workbench", fake_launch)
    result = production_local.launch_production_local_workbench(
        tmp_path / "workspace",
        port=8899,
        inbrowser=False,
    )

    assert result == "launched"
    assert captured["host"] == "127.0.0.1"
    assert captured["allow_remote"] is False
    assert captured["port"] == 8899
