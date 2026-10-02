"""Thin entrypoint for the current local Shadowseed Workbench."""

from __future__ import annotations

import ipaddress
from pathlib import Path

from shadowseed.workbench.controller import WorkbenchController


def _gradio():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "The Workbench UI requires the workbench extra: "
            "python -m pip install 'shadowseed[workbench]'"
        ) from exc
    return gr


def _is_loopback(host: str) -> bool:
    normalized = str(host).strip().lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False


def build_app(
    workspace: str | Path | None = None,
    *,
    controller: WorkbenchController | None = None,
):
    """Build the current Dutch, chat-first Workbench interface."""

    from shadowseed.workbench.simple_app_vnext import build_vnext_app

    return build_vnext_app(workspace, controller=controller)


def launch_workbench(
    workspace: str | Path | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 7860,
    allow_remote: bool = False,
    inbrowser: bool = True,
):
    """Launch the local Workbench and reject accidental remote exposure."""

    if not _is_loopback(host) and not allow_remote:
        raise ValueError(
            "remote Workbench binding is disabled by default; use --allow-remote only "
            "inside a trusted environment because the preview has no multi-user auth layer"
        )

    from shadowseed.workbench.simple_app_vnext import _CSS

    app = build_app(workspace)
    return app.launch(
        server_name=host,
        server_port=int(port),
        inbrowser=bool(inbrowser),
        share=False,
        css=_CSS,
    )
