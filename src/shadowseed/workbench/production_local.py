"""Production-local Workbench launcher with a non-configurable loopback boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowseed.application.error_safety import sanitize_error_text


PRODUCTION_LOCAL_HOST = "127.0.0.1"


def build_production_local_app(
    workspace: str | Path | None = None,
    *,
    controller: Any | None = None,
) -> Any:
    """Build the supported production-local UI including authority-bearing actions."""

    from shadowseed.workbench.app import _gradio, build_app
    from shadowseed.workbench.production_controller import ProductionLocalWorkbenchController

    ctl = controller or ProductionLocalWorkbenchController(workspace)
    workbench = build_app(controller=ctl)

    # Keep the generic presentation boundary usable with lightweight controller
    # doubles and research controllers. The supported production controller always
    # provides this distinct authority-bearing operation, so its UI must expose it.
    if not callable(getattr(ctl, "resolve_contradiction", None)):
        return workbench

    gr = _gradio()

    def session_choices() -> list[tuple[str, str]]:
        return ctl.session_choices(ctl.list_sessions())

    def seed_choices_for_session(session_id: str | None) -> list[tuple[str, str]]:
        if not session_id:
            return []
        try:
            return ctl.seed_choices(ctl.session_view(session_id))
        except Exception:
            return []

    def refresh_sessions(current: str | None):
        choices = session_choices()
        valid = {item[1] for item in choices}
        selected = current if current in valid else (choices[0][1] if choices else None)
        seed_choices = seed_choices_for_session(selected)
        return (
            gr.update(choices=choices, value=selected),
            gr.update(
                choices=seed_choices,
                value=seed_choices[0][1] if seed_choices else None,
            ),
        )

    def refresh_seeds(session_id: str | None):
        choices = seed_choices_for_session(session_id)
        return gr.update(
            choices=choices,
            value=choices[0][1] if choices else None,
        )

    def resolve_contradiction(
        session_id: str | None,
        seed_id: str | None,
        basis: str,
        contradiction_id: str,
    ):
        if not session_id or not seed_id:
            return {"error": "Select a live chat and blocked seed first."}, None, basis
        try:
            result = ctl.resolve_contradiction(
                session_id,
                seed_id,
                basis=basis,
                contradiction_id=contradiction_id.strip() or None,
            )
            return result, ctl.seed_view(session_id, seed_id), ""
        except Exception as exc:
            return {"error": sanitize_error_text(f"{type(exc).__name__}: {exc}")}, None, basis

    initial_sessions = session_choices()
    initial_session = initial_sessions[0][1] if initial_sessions else None
    initial_seed_choices = seed_choices_for_session(initial_session)
    with gr.Blocks(title="Production contradiction resolution") as resolution:
        gr.Markdown("## Resolve a blocking contradiction")
        gr.Markdown(
            "This is an authority-bearing production action. Use it only after the blocking "
            "contradiction has been checked and the resolution basis is independently justified. "
            "Resolution clears the contradiction through the Gate; it does not directly restore "
            "seed weight or bypass point-of-use authority."
        )
        with gr.Row():
            resolution_session = gr.Dropdown(
                choices=initial_sessions,
                value=initial_session,
                label="Live chat",
            )
            refresh_button = gr.Button("Refresh chats", variant="secondary")
        resolution_seed = gr.Dropdown(
            choices=initial_seed_choices,
            value=initial_seed_choices[0][1] if initial_seed_choices else None,
            label="Blocked shadow seed",
        )
        contradiction_id = gr.Textbox(
            label="Contradiction ID",
            placeholder="Optional: leave empty to resolve the seed's current blocking contradiction(s)",
        )
        basis = gr.Textbox(
            label="Independent resolution basis",
            lines=4,
            placeholder="Record the checked basis that justifies clearing the contradiction.",
        )
        resolve_button = gr.Button("Resolve contradiction", variant="primary")
        resolution_result = gr.JSON(label="Resolution result")
        updated_seed = gr.JSON(label="Updated seed snapshot")

        refresh_button.click(
            refresh_sessions,
            inputs=[resolution_session],
            outputs=[resolution_session, resolution_seed],
        )
        resolution_session.change(
            refresh_seeds,
            inputs=[resolution_session],
            outputs=[resolution_seed],
        )
        resolve_button.click(
            resolve_contradiction,
            inputs=[resolution_session, resolution_seed, basis, contradiction_id],
            outputs=[resolution_result, updated_seed, basis],
        )

    return gr.TabbedInterface(
        [workbench, resolution],
        ["Workbench", "Resolve contradiction"],
        title="Shadowseed production-local",
    )


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

    app = build_production_local_app(workspace)
    return app.launch(
        server_name=PRODUCTION_LOCAL_HOST,
        server_port=int(port),
        inbrowser=bool(inbrowser),
        share=False,
    )
