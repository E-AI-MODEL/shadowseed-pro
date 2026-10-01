"""Production-local Workbench launcher with a non-configurable loopback boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

PRODUCTION_LOCAL_HOST = "127.0.0.1"


def _live_session_choices(controller: Any) -> list[tuple[str, str]]:
    """Return only live sessions eligible for production contradiction resolution."""

    summaries = [
        item
        for item in controller.list_sessions()
        if str(item.get("runtime_mode", "evaluation")) == "live"
    ]
    return controller.session_choices(summaries)


def _blocking_seed_choices(controller: Any, session_id: str | None) -> list[tuple[str, str]]:
    """Return only seeds that currently have an open blocking contradiction."""

    if not session_id:
        return []
    try:
        session_view = controller.session_view(session_id)
        choices = controller.seed_choices(session_view)
    except Exception:
        return []

    blocking: list[tuple[str, str]] = []
    for label, seed_id in choices:
        try:
            seed_view = controller.seed_view(session_id, seed_id)
        except Exception:
            continue
        if bool(seed_view.get("blocking")):
            blocking.append((label, seed_id))
    return blocking


def build_production_local_app(
    workspace: str | Path | None = None,
    *,
    controller: Any | None = None,
) -> Any:
    """Build the supported local UI on the same product surface as the Workbench.

    Authority-bearing contradiction resolution is exposed contextually inside
    the Shadow drawer when the production controller provides the authorized
    resolution command. Keeping one product shell avoids a second legacy UI.
    """

    from shadowseed.workbench.app import build_app
    from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController

    ctl = controller or ProductionLocalWorkbenchController(workspace)
    return build_app(controller=ctl)

def launch_production_local_workbench(
    workspace: str | Path | None = None,
    *,
    port: int = 7860,
    inbrowser: bool = True,
) -> Any:
    """Launch the supported single-user local profile on IPv4 loopback only.

    This API intentionally has no host or remote-allow parameter. Trusted remote
    preview/development use remains a separate generic Workbench surface and is
    never upgraded into the production-local deployment contract.
    """

    from shadowseed.workbench.simple_app_vnext import _CSS, _gradio, _theme

    gr = _gradio()
    app = build_production_local_app(workspace)
    return app.launch(
        server_name=PRODUCTION_LOCAL_HOST,
        server_port=int(port),
        inbrowser=bool(inbrowser),
        share=False,
        css=_CSS,
        theme=_theme(gr),
    )
