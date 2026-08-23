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

    class FakeApp:
        def launch(self, **kwargs):
            captured.update(kwargs)
            return "launched"

    import shadowseed.workbench.app as app
    import shadowseed.workbench.production_controller as production_controller

    class FakeController:
        def __init__(self, workspace):
            captured["workspace"] = workspace

    monkeypatch.setattr(production_controller, "ProductionLocalWorkbenchController", FakeController)
    monkeypatch.setattr(app, "build_app", lambda *, controller: FakeApp())

    result = production_local.launch_production_local_workbench(
        tmp_path / "workspace",
        port=8899,
        inbrowser=False,
    )

    assert result == "launched"
    assert captured["server_name"] == "127.0.0.1"
    assert captured["share"] is False
    assert captured["server_port"] == 8899
