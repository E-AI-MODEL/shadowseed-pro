"""Gradio shell for the local Shadowseed tester Workbench."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowseed.workbench.controller import WorkbenchController


_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


def _gradio():
    try:
        import gradio as gr
    except ModuleNotFoundError as exc:  # pragma: no cover - exercised by installed CLI smoke
        raise RuntimeError(
            'Workbench UI requires the optional dependency: pip install "shadowseed[workbench]"'
        ) from exc
    return gr


def build_app(
    workspace: str | Path | None = None,
    *,
    controller: WorkbenchController | None = None,
):
    """Build the Workbench without starting a network listener."""

    gr = _gradio()
    ctl = controller or WorkbenchController(workspace)

    def session_choices() -> list[tuple[str, str]]:
        return ctl.session_choices(ctl.list_sessions())

    def dropdown_update(selected: str | None = None):
        choices = session_choices()
        values = {value for _label, value in choices}
        value = selected if selected in values else (choices[0][1] if choices else None)
        return gr.Dropdown(choices=choices, value=value)

    def seed_update(session_id: str | None, selected: str | None = None):
        if not session_id:
            return gr.Dropdown(choices=[], value=None)
        choices = ctl.seed_choices(ctl.session_view(session_id))
        values = {value for _label, value in choices}
        value = selected if selected in values else (choices[0][1] if choices else None)
        return gr.Dropdown(choices=choices, value=value)

    def backend_note(backend: str) -> str:
        notes = {item["backend"]: item["note"] for item in ctl.backends()}
        return notes.get(backend, "")

    def create_session(
        title: str,
        profile_id: str,
        backend: str,
        model_id: str,
        external_confirmed: bool,
    ):
        try:
            session_id = ctl.create_session(
                title=title,
                profile_id=profile_id,
                backend=backend,
                model_id=model_id or None,
                external_confirmed=external_confirmed,
            )
            view = ctl.session_view(session_id)
            return (
                dropdown_update(session_id),
                f"Created `{session_id}` in **{view['runtime_mode']}** mode "
                f"at `{ctl.workspace_root}`.",
                ctl.chat_messages(view),
                view,
                seed_update(session_id),
            )
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def load_session(session_id: str | None):
        if not session_id:
            return [], {}, gr.Dropdown(choices=[], value=None), "No session selected."
        try:
            view = ctl.session_view(session_id)
            return (
                ctl.chat_messages(view),
                view,
                seed_update(session_id),
                f"Loaded **{view['title']}** · **{view['runtime_mode']}** mode · "
                f"{view['turn']} turns · {len(view['seeds'])} seeds.",
            )
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def send_turn(
        session_id: str | None,
        question: str,
        external_confirmed: bool,
    ):
        if not session_id:
            raise gr.Error("Create or select a session first.")
        try:
            result = ctl.send_turn(
                session_id,
                question,
                external_confirmed=external_confirmed,
            )
            view = result["session"]
            return (
                ctl.chat_messages(view),
                result["report"],
                view,
                seed_update(session_id),
                "",
            )
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def inspect_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return {}, []
        try:
            view = ctl.seed_view(session_id, seed_id)
            return view, view.get("timeline", [])
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def record_feedback(
        session_id: str | None,
        turn_index: float,
        overall: str,
        seed_effect: str,
        seed_id: str,
        note: str,
    ):
        if not session_id:
            raise gr.Error("Select a session first.")
        try:
            stored = ctl.record_feedback(
                session_id=session_id,
                turn_index=int(turn_index),
                overall=overall,
                seed_effect=seed_effect,
                seed_id=seed_id.strip() or None,
                note=note,
            )
            return stored, "Feedback stored as **record-only audit data**. Runtime authority was not changed."
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def compare_turn(
        session_id: str | None,
        turn_index: float,
        blinded: bool,
        reveal: bool,
    ):
        if not session_id:
            raise gr.Error("Select a session first.")
        try:
            return ctl.compare_turn(
                session_id,
                int(turn_index),
                blinded=blinded,
                reveal=reveal,
            )
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def export_report(session_id: str | None, destination: str):
        if not session_id:
            raise gr.Error("Select a session first.")
        try:
            target = ctl.export_report(
                session_id,
                destination.strip() or "shadowseed-workbench-report.zip",
            )
            return target, ctl.verify_export(target)
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def export_support(session_id: str | None, destination: str):
        if not session_id:
            raise gr.Error("Select a session first.")
        try:
            target = ctl.export_support_bundle(
                session_id,
                destination.strip() or "shadowseed-support-bundle.zip",
            )
            return target, ctl.verify_export(target)
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def verify_export(path: str):
        try:
            return ctl.verify_export(path.strip())
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def parse_scenario(scenario_json: str):
        try:
            return ctl.parse_scenario(scenario_json)
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def scenario_status(result: dict[str, Any]) -> str:
        session_id = str(result["session_id"])
        if result.get("complete"):
            return (
                f"Scenario completed: **{result['completed']}/{result['total']}** questions "
                f"in resumable session `{session_id}`."
            )
        return (
            f"Scenario paused after **{result['completed']}/{result['total']}** completed "
            f"questions. Failure: `{result.get('error') or 'unknown error'}`. "
            f"Resume from index **{result['next_at']}** to retry the failed question without "
            "replaying completed turns."
        )

    def run_scenario(scenario_json: str, external_confirmed: bool):
        try:
            result = ctl.run_scenario(
                scenario_json,
                external_confirmed=external_confirmed,
            )
            session_id = str(result["session_id"])
            return (
                result,
                scenario_status(result),
                dropdown_update(session_id),
                int(result["next_at"]),
            )
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    def resume_scenario(
        scenario_json: str,
        session_id: str | None,
        start_at: float,
        external_confirmed: bool,
    ):
        if not session_id:
            raise gr.Error("Select the partial scenario session first.")
        try:
            result = ctl.resume_scenario(
                scenario_json,
                session_id,
                start_at=int(start_at),
                external_confirmed=external_confirmed,
            )
            return (
                result,
                scenario_status(result),
                dropdown_update(session_id),
                int(result["next_at"]),
            )
        except Exception as exc:
            raise gr.Error(str(exc)) from exc

    profiles = ctl.profiles()
    profile_choices = [(item["label"], item["profile_id"]) for item in profiles]
    initial_sessions = session_choices()
    initial_session = initial_sessions[0][1] if initial_sessions else None

    with gr.Blocks(title="Shadowseed Tester Workbench") as app:
        gr.Markdown(
            "# Shadowseed Tester Workbench\n"
            "Local-first tester environment. The UI explains and records runtime behavior; "
            "it does **not** authorize seed influence or edit weights/statuses directly.\n\n"
            f"Workspace: `{ctl.workspace_root}`"
        )

        with gr.Tab("Session"):
            with gr.Row():
                session_select = gr.Dropdown(
                    label="Saved session",
                    choices=initial_sessions,
                    value=initial_session,
                )
                refresh_sessions = gr.Button("Refresh sessions")
                load_session_button = gr.Button("Load")
            session_status = gr.Markdown("Select or create a session.")

            with gr.Accordion("Create session", open=not bool(initial_sessions)):
                with gr.Row():
                    new_title = gr.Textbox(label="Title", value="Tester session")
                    new_profile = gr.Dropdown(
                        label="Profile",
                        choices=profile_choices,
                        value="balanced",
                    )
                    new_backend = gr.Dropdown(
                        label="Backend",
                        choices=list(ctl.backends()[index]["backend"] for index in range(len(ctl.backends()))),
                        value="fixture",
                    )
                new_model = gr.Textbox(
                    label="Model id",
                    info="Required for Hugging Face, Ollama, and OpenAI backends.",
                )
                backend_info = gr.Markdown(backend_note("fixture"))
                external_confirm = gr.Checkbox(
                    label="I understand when the selected backend sends prompts to an external provider.",
                    value=False,
                )
                create_button = gr.Button("Create session", variant="primary")

            chatbot = gr.Chatbot(label="Conversation", height=460)
            with gr.Row():
                question = gr.Textbox(
                    label="Question",
                    placeholder="Ask the next question…",
                    lines=2,
                    scale=5,
                )
                send_button = gr.Button("Send", variant="primary", scale=1)
            send_external_confirm = gr.Checkbox(
                label="Confirm external-provider transmission for this turn (only required for hosted backends).",
                value=False,
            )
            turn_report = gr.JSON(label="Latest turn report")
            session_json = gr.JSON(label="Persisted session view")
            session_seed_select = gr.Dropdown(label="Seeds in current session", choices=[])

            refresh_sessions.click(fn=lambda: dropdown_update(), outputs=session_select)
            new_backend.change(fn=backend_note, inputs=new_backend, outputs=backend_info)
            create_button.click(
                fn=create_session,
                inputs=[new_title, new_profile, new_backend, new_model, external_confirm],
                outputs=[session_select, session_status, chatbot, session_json, session_seed_select],
            )
            load_session_button.click(
                fn=load_session,
                inputs=session_select,
                outputs=[chatbot, session_json, session_seed_select, session_status],
            )
            send_button.click(
                fn=send_turn,
                inputs=[session_select, question, send_external_confirm],
                outputs=[chatbot, turn_report, session_json, session_seed_select, question],
            )
            question.submit(
                fn=send_turn,
                inputs=[session_select, question, send_external_confirm],
                outputs=[chatbot, turn_report, session_json, session_seed_select, question],
            )

        with gr.Tab("Seed inspector"):
            with gr.Row():
                inspect_session = gr.Dropdown(
                    label="Session",
                    choices=initial_sessions,
                    value=initial_session,
                )
                inspect_refresh = gr.Button("Refresh")
            inspect_seed_select = gr.Dropdown(label="Seed", choices=[])
            inspect_load_seeds = gr.Button("Load seeds")
            inspect_button = gr.Button("Inspect seed", variant="primary")
            seed_json = gr.JSON(label="Seed snapshot + explanation")
            timeline_json = gr.JSON(label="Audit timeline")
            inspect_refresh.click(fn=lambda: dropdown_update(), outputs=inspect_session)
            inspect_load_seeds.click(
                fn=lambda sid: seed_update(sid),
                inputs=inspect_session,
                outputs=inspect_seed_select,
            )
            inspect_button.click(
                fn=inspect_seed,
                inputs=[inspect_session, inspect_seed_select],
                outputs=[seed_json, timeline_json],
            )

        with gr.Tab("Tester feedback"):
            feedback_session = gr.Dropdown(
                label="Session",
                choices=initial_sessions,
                value=initial_session,
            )
            feedback_refresh = gr.Button("Refresh sessions")
            feedback_turn = gr.Number(label="Turn index", value=0, precision=0)
            with gr.Row():
                feedback_overall = gr.Dropdown(
                    label="Overall answer",
                    choices=["better", "neutral", "worse", "unclear"],
                    value="neutral",
                )
                feedback_effect = gr.Dropdown(
                    label="Visible seed effect",
                    choices=["helpful", "harmful", "no_visible_effect", "unclear"],
                    value="no_visible_effect",
                )
            feedback_seed = gr.Textbox(
                label="Seed id (optional)",
                info="Leave empty for turn-level feedback.",
            )
            feedback_note = gr.Textbox(label="Tester note", lines=4)
            feedback_button = gr.Button("Record feedback", variant="primary")
            feedback_result = gr.JSON(label="Stored feedback")
            feedback_status = gr.Markdown()
            feedback_refresh.click(fn=lambda: dropdown_update(), outputs=feedback_session)
            feedback_button.click(
                fn=record_feedback,
                inputs=[
                    feedback_session,
                    feedback_turn,
                    feedback_overall,
                    feedback_effect,
                    feedback_seed,
                    feedback_note,
                ],
                outputs=[feedback_result, feedback_status],
            )

        with gr.Tab("Compare"):
            gr.Markdown(
                "Compare the uncontaminated baseline answer with the answer visible after the "
                "Shadowseed path. No automatic quality score is inferred."
            )
            compare_session = gr.Dropdown(
                label="Session",
                choices=initial_sessions,
                value=initial_session,
            )
            compare_refresh = gr.Button("Refresh sessions")
            compare_turn_index = gr.Number(label="Turn index", value=0, precision=0)
            compare_blind = gr.Checkbox(label="Blind labels", value=True)
            compare_reveal = gr.Checkbox(label="Reveal A/B mapping", value=False)
            compare_button = gr.Button("Compare", variant="primary")
            comparison_json = gr.JSON(label="Comparison")
            compare_refresh.click(fn=lambda: dropdown_update(), outputs=compare_session)
            compare_button.click(
                fn=compare_turn,
                inputs=[compare_session, compare_turn_index, compare_blind, compare_reveal],
                outputs=comparison_json,
            )

        with gr.Tab("Export"):
            gr.Markdown(
                "A full report contains the selected session's conversation and seed snapshots. "
                "A support bundle is privacy-minimized: no free session title, prompts, answers, "
                "seed text, feedback notes, or direct session id are included."
            )
            export_session = gr.Dropdown(
                label="Session",
                choices=initial_sessions,
                value=initial_session,
            )
            export_refresh = gr.Button("Refresh sessions")
            full_output = gr.Textbox(
                label="Full report ZIP",
                value="shadowseed-workbench-report.zip",
            )
            support_output = gr.Textbox(
                label="Support bundle ZIP",
                value="shadowseed-support-bundle.zip",
            )
            with gr.Row():
                export_full_button = gr.Button("Export full report", variant="primary")
                export_support_button = gr.Button("Export support bundle")
            export_path = gr.Textbox(label="Written export")
            export_verification = gr.JSON(label="Verification")
            gr.Markdown("### Verify an existing Workbench export")
            verify_path = gr.Textbox(label="ZIP path")
            verify_button = gr.Button("Verify")
            verify_result = gr.JSON(label="Verification result")
            export_refresh.click(fn=lambda: dropdown_update(), outputs=export_session)
            export_full_button.click(
                fn=export_report,
                inputs=[export_session, full_output],
                outputs=[export_path, export_verification],
            )
            export_support_button.click(
                fn=export_support,
                inputs=[export_session, support_output],
                outputs=[export_path, export_verification],
            )
            verify_button.click(fn=verify_export, inputs=verify_path, outputs=verify_result)

        with gr.Tab("Scenario"):
            gr.Markdown(
                "Import a JSON scenario. A batch backend failure preserves completed turns and "
                "returns the exact resume position, so retrying does not replay earlier calls. "
                "The resulting session also remains available in the Session tab."
            )
            scenario_json = gr.Textbox(
                label="Scenario JSON",
                lines=12,
                value=(
                    '{\n  "title": "Example scenario",\n  "questions": [\n'
                    '    "What is the main uncertainty?",\n'
                    '    "What evidence would change the answer?"\n'
                    '  ],\n  "profile_id": "balanced",\n  "backend": "fixture"\n}'
                ),
            )
            scenario_external_confirm = gr.Checkbox(
                label="Confirm external-provider transmission when this scenario uses a hosted backend.",
                value=False,
            )
            with gr.Row():
                scenario_parse = gr.Button("Validate")
                scenario_run = gr.Button("Run new scenario", variant="primary")
                scenario_resume = gr.Button("Resume partial scenario")
            scenario_result = gr.JSON(label="Scenario")
            scenario_status_output = gr.Markdown()
            scenario_session = gr.Dropdown(label="Scenario session", choices=initial_sessions)
            scenario_resume_at = gr.Number(
                label="Resume index",
                value=0,
                precision=0,
                info="Filled automatically after a partial run; persisted progress is authoritative.",
            )
            scenario_parse.click(fn=parse_scenario, inputs=scenario_json, outputs=scenario_result)
            scenario_run.click(
                fn=run_scenario,
                inputs=[scenario_json, scenario_external_confirm],
                outputs=[
                    scenario_result,
                    scenario_status_output,
                    scenario_session,
                    scenario_resume_at,
                ],
            )
            scenario_resume.click(
                fn=resume_scenario,
                inputs=[
                    scenario_json,
                    scenario_session,
                    scenario_resume_at,
                    scenario_external_confirm,
                ],
                outputs=[
                    scenario_result,
                    scenario_status_output,
                    scenario_session,
                    scenario_resume_at,
                ],
            )

    return app


def launch_workbench(
    workspace: str | Path | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 7860,
    allow_remote: bool = False,
    inbrowser: bool = True,
) -> None:
    """Launch the supported Workbench server.

    Remote binding is opt-in because this preview is a local, single-user
    tester environment and has no multi-user authentication layer.
    """

    if host not in _LOOPBACK_HOSTS and not allow_remote:
        raise ValueError(
            "remote Workbench binding is disabled by default; use --allow-remote only in a "
            "trusted environment and add your own network access controls"
        )
    app = build_app(workspace)
    app.launch(
        server_name=host,
        server_port=int(port),
        share=False,
        inbrowser=bool(inbrowser),
        show_error=True,
    )
