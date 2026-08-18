"""Chat-first local Workbench UI for Shadow Seed Learning.

The Workbench is intentionally a presentation layer. It calls the application
controller and does not import or reimplement manager, Gate, lifecycle, or
point-of-use authority logic.
"""

from __future__ import annotations

import ipaddress
import json
from pathlib import Path
from typing import Any

from shadowseed.workbench.controller import WorkbenchController


_PRODUCT_CSS = """
.gradio-container { max-width: 1480px !important; margin: 0 auto; }
#product-title { margin-bottom: 0.25rem; }
#product-subtitle { opacity: 0.78; margin-bottom: 1rem; }
#chat-shell { min-height: 560px; }
#chat-status { font-size: 0.92rem; }
.comparison-note { font-size: 0.9rem; opacity: 0.82; }
"""


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


def _error_text(exc: Exception) -> str:
    return f"**Error:** {type(exc).__name__}: {exc}"


def _status_markdown(view: dict[str, Any] | None) -> str:
    if not view:
        return "Create or open a chat to begin."
    seeds = list(view.get("seeds", []))
    promoted = sum(str(seed.get("status", "")).lower() == "promoted" for seed in seeds)
    mode = str(view.get("runtime_mode", "evaluation"))
    experience = "Live SSL" if mode == "live" else "Research evaluation"
    model = str(view.get("model_id") or view.get("backend") or "unknown")
    return (
        f"**{experience}** · model `{model}` · {int(view.get('turn', 0))} turns · "
        f"{len(seeds)} shadow seeds · {promoted} promoted"
    )


def _comparison_outputs(comparison: dict[str, Any] | None) -> tuple[str, str, str]:
    if not comparison:
        return "", "", (
            "Enable **Compare this message with SSL off** before sending when you want a "
            "paired control."
        )
    labels = {
        str(comparison.get("candidate_a_label", "")): str(comparison.get("candidate_a", "")),
        str(comparison.get("candidate_b_label", "")): str(comparison.get("candidate_b", "")),
    }
    ssl_on = labels.get("ssl_on") or labels.get("shadowseed") or ""
    ssl_off = labels.get("ssl_off") or labels.get("baseline") or ""
    influenced = bool(comparison.get("ssl_influence_observed"))
    if influenced:
        note = (
            "An authorized Shadow Seed surfaced on this turn. The two answers form a paired "
            "same-model comparison; review quality rather than assuming the SSL answer is better."
        )
    else:
        note = (
            "No authorized Shadow Seed surfaced on this turn. Any difference between the two "
            "generations must not be attributed to SSL."
        )
    return ssl_on, ssl_off, note


def build_app(
    workspace: str | Path | None = None,
    *,
    controller: WorkbenchController | None = None,
):
    """Build the local Gradio product surface."""

    gr = _gradio()
    ctl = controller or WorkbenchController(workspace)
    profile_choices = [
        (f"{item['label']} — {item['description']}", item["profile_id"])
        for item in ctl.profiles()
    ]
    backend_choices = [
        ("Ollama — local model", "ollama"),
        ("OpenAI — hosted model", "openai"),
        ("Hugging Face Transformers — local model", "hf-transformers"),
        ("Offline demo — deterministic fixture", "fixture"),
    ]

    def session_choices() -> list[tuple[str, str]]:
        return ctl.session_choices(ctl.list_sessions())

    def dropdown_update(choices: list[tuple[str, str]], value: str | None = None):
        valid = {item[1] for item in choices}
        selected = value if value in valid else (choices[0][1] if choices else None)
        return gr.update(choices=choices, value=selected)

    def refresh_session_dropdown(current: str | None):
        return dropdown_update(session_choices(), current)

    def model_discovery_update(backend: str, current_model: str | None):
        note = next(
            (item["note"] for item in ctl.backends() if item["backend"] == backend),
            "",
        )
        if backend != "ollama":
            return gr.update(choices=[], value=current_model or None), note
        try:
            models = ctl.discover_models(backend)
        except Exception as exc:
            return (
                gr.update(choices=[], value=current_model or None),
                note + f"\n\nLocal model discovery unavailable: {exc}",
            )
        selected = (
            current_model
            if current_model in models
            else (models[0] if models else current_model or None)
        )
        discovery = (
            f"Detected {len(models)} local Ollama model(s)."
            if models
            else "Ollama is reachable but no local models were reported."
        )
        return gr.update(choices=models, value=selected), note + f"\n\n{discovery}"

    def backend_defaults(backend: str, current_model: str | None):
        model_update, note = model_discovery_update(backend, current_model)
        return ctl.default_embedding_backend(backend), note, model_update

    def refresh_models(backend: str, current_model: str | None):
        return model_discovery_update(backend, current_model)

    def create_chat(
        title: str,
        profile_id: str,
        backend: str,
        model_id: str,
        embedding_backend: str,
        embedding_model: str,
        allow_toy_embedder: bool,
        external_confirmed: bool,
        research_evaluation: bool,
    ):
        try:
            session_id = ctl.create_session(
                title=title,
                profile_id=profile_id,
                backend=backend,
                model_id=model_id or None,
                runtime_mode="evaluation" if research_evaluation else "live",
                embedding_backend=embedding_backend or None,
                embedding_model=embedding_model or None,
                allow_toy_embedder=bool(allow_toy_embedder),
                external_confirmed=bool(external_confirmed),
            )
            view = ctl.session_view(session_id)
            choices = session_choices()
            return (
                dropdown_update(choices, session_id),
                ctl.chat_messages(view),
                _status_markdown(view),
                dropdown_update(ctl.seed_choices(view)),
                view,
                "",
                "",
                "Chat created. Type a message below.",
            )
        except Exception as exc:
            return (
                gr.update(),
                [],
                _error_text(exc),
                gr.update(choices=[], value=None),
                None,
                "",
                "",
                _error_text(exc),
            )

    def load_chat(session_id: str | None):
        if not session_id:
            return [], "Create or open a chat to begin.", gr.update(choices=[], value=None), None, "", "", ""
        try:
            view = ctl.session_view(session_id)
            comparison = None
            reports = list(view.get("turn_reports", []))
            if reports and reports[-1].get("comparison_requested"):
                try:
                    comparison = ctl.compare_turn(
                        session_id,
                        int(reports[-1].get("turn", len(reports) - 1)),
                        blinded=False,
                        reveal=True,
                    )
                except ValueError:
                    comparison = None
            ssl_on, ssl_off, note = _comparison_outputs(comparison)
            return (
                ctl.chat_messages(view),
                _status_markdown(view),
                gr.update(choices=ctl.seed_choices(view), value=None),
                view,
                ssl_on,
                ssl_off,
                note,
            )
        except Exception as exc:
            return [], _error_text(exc), gr.update(), None, "", "", _error_text(exc)

    def send_message(
        session_id: str | None,
        question: str,
        compare_without_ssl: bool,
        external_confirmed: bool,
    ):
        if not session_id:
            return [], "Select or create a chat first.", gr.update(), None, "", "", "", question
        try:
            result = ctl.send_turn(
                session_id,
                question,
                compare_without_ssl=bool(compare_without_ssl),
                external_confirmed=bool(external_confirmed),
            )
            view = result["session"]
            ssl_on, ssl_off, note = _comparison_outputs(result.get("comparison"))
            return (
                ctl.chat_messages(view),
                _status_markdown(view),
                gr.update(choices=ctl.seed_choices(view), value=None),
                result["report"],
                ssl_on,
                ssl_off,
                note,
                "",
            )
        except Exception as exc:
            return gr.update(), _error_text(exc), gr.update(), None, "", "", _error_text(exc), question

    def shadow_session_changed(session_id: str | None):
        if not session_id:
            return gr.update(choices=[], value=None), "Select a chat."
        try:
            view = ctl.session_view(session_id)
            return dropdown_update(ctl.seed_choices(view)), _status_markdown(view)
        except Exception as exc:
            return gr.update(), _error_text(exc)

    def inspect_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return None, None
        try:
            view = ctl.seed_view(session_id, seed_id)
            return view, view.get("timeline", [])
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}, None

    def falsify_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return {"error": "Select a chat and seed first."}, None
        try:
            result = ctl.falsify_seed(session_id, seed_id)
            return result, ctl.seed_view(session_id, seed_id)
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}, None

    def submit_verified_evidence(
        session_id: str | None,
        seed_id: str | None,
        source_ref: str,
        note: str,
        operator_verified: bool,
    ):
        if not session_id or not seed_id:
            return {"error": "Select a live chat and seed first."}, None, "", False
        try:
            result = ctl.submit_verified_evidence(
                session_id,
                seed_id,
                source_ref=source_ref,
                note=note,
                operator_verified=bool(operator_verified),
            )
            return result, ctl.seed_view(session_id, seed_id), "", False
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}, None, "", False

    def record_feedback(
        session_id: str | None,
        turn_index: float,
        overall: str,
        seed_effect: str,
        note: str,
    ):
        if not session_id:
            return {"error": "Select a chat first."}
        try:
            return ctl.record_feedback(
                session_id=session_id,
                turn_index=int(turn_index),
                overall=overall,
                seed_effect=seed_effect,
                note=note,
            )
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}

    def export_report(session_id: str | None, destination: str):
        if not session_id:
            return "Select a chat first."
        try:
            return ctl.export_report(session_id, destination or "shadowseed-workbench-report.zip")
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"

    def export_support(session_id: str | None, destination: str):
        if not session_id:
            return "Select a chat first."
        try:
            return ctl.export_support_bundle(
                session_id,
                destination or "shadowseed-support-bundle.zip",
            )
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"

    def run_scenario(scenario_json: str, external_confirmed: bool):
        try:
            return ctl.run_scenario(
                scenario_json,
                external_confirmed=bool(external_confirmed),
            )
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}

    def advanced_compare(
        session_id: str | None,
        turn_index: float,
        blinded: bool,
        reveal: bool,
    ):
        if not session_id:
            return {"error": "Select a chat first."}
        try:
            return ctl.compare_turn(
                session_id,
                int(turn_index),
                blinded=bool(blinded),
                reveal=bool(reveal),
            )
        except Exception as exc:
            return {"error": f"{type(exc).__name__}: {exc}"}

    initial_choices = session_choices()

    with gr.Blocks(title="Shadowseed", css=_PRODUCT_CSS) as app:
        gr.Markdown("# Shadowseed", elem_id="product-title")
        gr.Markdown(
            "Chat normally with an LLM while Shadow Seed Learning runs as a gated shadow layer. "
            "When you want a direct check, generate the same turn with SSL off automatically.",
            elem_id="product-subtitle",
        )

        with gr.Tab("Chat"):
            with gr.Row(elem_id="chat-shell"):
                with gr.Column(scale=1, min_width=300):
                    session_select = gr.Dropdown(
                        choices=initial_choices,
                        label="Chats",
                        value=initial_choices[0][1] if initial_choices else None,
                    )
                    refresh_sessions = gr.Button("Refresh chats", variant="secondary")
                    gr.Markdown("### New chat")
                    title = gr.Textbox(label="Chat name", value="New SSL chat")
                    backend = gr.Dropdown(
                        choices=backend_choices,
                        value="ollama",
                        label="Model provider",
                    )
                    model_id = gr.Dropdown(
                        choices=[],
                        value=None,
                        allow_custom_value=True,
                        label="Model",
                        info="Local Ollama models can be detected automatically; custom IDs remain allowed.",
                    )
                    refresh_models_button = gr.Button("Detect local models", variant="secondary")
                    backend_note = gr.Markdown(
                        next(item["note"] for item in ctl.backends() if item["backend"] == "ollama")
                    )
                    with gr.Accordion("Model and SSL settings", open=False):
                        profile = gr.Dropdown(
                            choices=profile_choices,
                            value="balanced",
                            label="SSL surfacing profile",
                        )
                        embedding_backend = gr.Dropdown(
                            choices=list(ctl.embedding_backends()),
                            value="sentence-transformers",
                            label="Semantic embedding",
                        )
                        embedding_model = gr.Textbox(
                            label="Embedding model override",
                            placeholder="Optional",
                        )
                        allow_toy = gr.Checkbox(
                            label="Allow lexical toy embeddings for a real model (research only)",
                            value=False,
                        )
                        hosted_confirm = gr.Checkbox(
                            label="I understand this configuration may send chat content to a hosted provider",
                            value=False,
                        )
                        research_evaluation = gr.Checkbox(
                            label="Create legacy/research evaluation session instead of live SSL chat",
                            value=False,
                        )
                    create_button = gr.Button("Create chat", variant="primary")

                with gr.Column(scale=3, min_width=620):
                    chat = gr.Chatbot(label="Conversation", height=500)
                    chat_status = gr.Markdown("Create or open a chat to begin.", elem_id="chat-status")
                    question = gr.Textbox(
                        label="Message",
                        placeholder="Message the model...",
                        lines=3,
                    )
                    compare_checkbox = gr.Checkbox(
                        label="Compare this message with SSL off",
                        value=False,
                    )
                    send_button = gr.Button("Send", variant="primary")

                    with gr.Accordion("Compare SSL on/off", open=False):
                        comparison_note = gr.Markdown(
                            "Enable **Compare this message with SSL off** before sending when you want a paired control.",
                            elem_classes=["comparison-note"],
                        )
                        with gr.Row():
                            ssl_on = gr.Markdown(label="SSL on")
                            ssl_off = gr.Markdown(label="SSL off")
                    with gr.Accordion("Advanced turn diagnostics", open=False):
                        last_turn_json = gr.JSON(label="Last turn report")
                        session_json = gr.JSON(label="Read-only session view")
                    main_seed_select = gr.Dropdown(
                        choices=[],
                        label="Shadow seed quick selector",
                        visible=False,
                    )

            backend.change(
                backend_defaults,
                inputs=[backend, model_id],
                outputs=[embedding_backend, backend_note, model_id],
            )
            refresh_models_button.click(
                refresh_models,
                inputs=[backend, model_id],
                outputs=[model_id, backend_note],
            )
            refresh_sessions.click(
                refresh_session_dropdown,
                inputs=[session_select],
                outputs=[session_select],
            )
            create_button.click(
                create_chat,
                inputs=[
                    title,
                    profile,
                    backend,
                    model_id,
                    embedding_backend,
                    embedding_model,
                    allow_toy,
                    hosted_confirm,
                    research_evaluation,
                ],
                outputs=[
                    session_select,
                    chat,
                    chat_status,
                    main_seed_select,
                    session_json,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                ],
            )
            session_select.change(
                load_chat,
                inputs=[session_select],
                outputs=[
                    chat,
                    chat_status,
                    main_seed_select,
                    session_json,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                ],
            )
            send_button.click(
                send_message,
                inputs=[session_select, question, compare_checkbox, hosted_confirm],
                outputs=[
                    chat,
                    chat_status,
                    main_seed_select,
                    last_turn_json,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                    question,
                ],
            )
            question.submit(
                send_message,
                inputs=[session_select, question, compare_checkbox, hosted_confirm],
                outputs=[
                    chat,
                    chat_status,
                    main_seed_select,
                    last_turn_json,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                    question,
                ],
            )

        with gr.Tab("Shadow"):
            gr.Markdown(
                "Inspect candidate seeds and their audit history. Seed text is a hypothesis to "
                "investigate, not an instruction or a fact."
            )
            with gr.Row():
                shadow_session = gr.Dropdown(choices=initial_choices, label="Chat")
                shadow_refresh = gr.Button("Refresh")
            shadow_status = gr.Markdown("Select a chat.")
            seed_select = gr.Dropdown(choices=[], label="Shadow seed")
            with gr.Row():
                seed_json = gr.JSON(label="Seed snapshot")
                seed_timeline = gr.JSON(label="Audit timeline")
            inspect_button = gr.Button("Inspect seed")
            falsify_button = gr.Button("Mark seed contradicted", variant="stop")
            falsify_result = gr.JSON(label="Falsification result")

            with gr.Accordion("Submit independently verified support", open=False):
                gr.Markdown(
                    "This is an authority-bearing action. Confirm support outside model output and "
                    "use a stable source reference. Reusing one source does not add authority twice."
                )
                evidence_source = gr.Textbox(label="Source reference")
                evidence_note = gr.Textbox(label="Verification note", lines=2)
                evidence_attest = gr.Checkbox(
                    label="I independently checked this support outside the model output",
                    value=False,
                )
                evidence_button = gr.Button("Submit verified support")
                evidence_result = gr.JSON(label="Gate result")

            shadow_refresh.click(
                refresh_session_dropdown,
                inputs=[shadow_session],
                outputs=[shadow_session],
            )
            shadow_session.change(
                shadow_session_changed,
                inputs=[shadow_session],
                outputs=[seed_select, shadow_status],
            )
            inspect_button.click(
                inspect_seed,
                inputs=[shadow_session, seed_select],
                outputs=[seed_json, seed_timeline],
            )
            seed_select.change(
                inspect_seed,
                inputs=[shadow_session, seed_select],
                outputs=[seed_json, seed_timeline],
            )
            falsify_button.click(
                falsify_seed,
                inputs=[shadow_session, seed_select],
                outputs=[falsify_result, seed_json],
            )
            evidence_button.click(
                submit_verified_evidence,
                inputs=[
                    shadow_session,
                    seed_select,
                    evidence_source,
                    evidence_note,
                    evidence_attest,
                ],
                outputs=[evidence_result, seed_json, evidence_source, evidence_attest],
            )

        with gr.Tab("Feedback and export"):
            feedback_session = gr.Dropdown(choices=initial_choices, label="Chat")
            feedback_refresh = gr.Button("Refresh chats")
            gr.Markdown(
                "Tester feedback is record-only. It never changes seed weight, promotion, or Gate authority."
            )
            turn_index = gr.Number(value=0, precision=0, label="Turn index")
            overall = gr.Dropdown(
                choices=["better", "neutral", "worse", "helpful", "unhelpful"],
                value="neutral",
                label="Overall impression",
            )
            seed_effect = gr.Dropdown(
                choices=["helpful", "harmful", "no_visible_effect", "unclear"],
                value="no_visible_effect",
                label="Visible SSL effect",
            )
            feedback_note = gr.Textbox(label="Optional note", lines=3)
            feedback_button = gr.Button("Record feedback")
            feedback_result = gr.JSON(label="Recorded feedback")

            gr.Markdown("### Export")
            report_destination = gr.Textbox(
                value="shadowseed-workbench-report.zip",
                label="Full report destination",
            )
            support_destination = gr.Textbox(
                value="shadowseed-support-bundle.zip",
                label="Privacy-minimized support destination",
            )
            with gr.Row():
                export_report_button = gr.Button("Export full report")
                export_support_button = gr.Button("Export support bundle")
            export_result = gr.Textbox(label="Export result")

            feedback_refresh.click(
                refresh_session_dropdown,
                inputs=[feedback_session],
                outputs=[feedback_session],
            )
            feedback_button.click(
                record_feedback,
                inputs=[feedback_session, turn_index, overall, seed_effect, feedback_note],
                outputs=[feedback_result],
            )
            export_report_button.click(
                export_report,
                inputs=[feedback_session, report_destination],
                outputs=[export_result],
            )
            export_support_button.click(
                export_support,
                inputs=[feedback_session, support_destination],
                outputs=[export_result],
            )

        with gr.Tab("Advanced / research"):
            gr.Markdown(
                "Research tools are intentionally separate from normal chat. Scenario JSON, the "
                "historical evaluation runtime and blinded review exist for reproducibility and "
                "experiments; ordinary testers do not need them."
            )
            with gr.Accordion("Scenario runner", open=False):
                scenario_json = gr.Code(
                    language="json",
                    label="Scenario JSON",
                    value=json.dumps(
                        {
                            "title": "Research scenario",
                            "questions": ["First question", "Second question"],
                            "profile_id": "balanced",
                            "backend": "fixture",
                            "runtime_mode": "evaluation",
                            "embedding_backend": "lexical",
                        },
                        indent=2,
                    ),
                )
                scenario_external_confirm = gr.Checkbox(
                    label="I understand this scenario may send content to a hosted provider",
                    value=False,
                )
                scenario_button = gr.Button("Run scenario")
                scenario_result = gr.JSON(label="Scenario result")
                scenario_button.click(
                    run_scenario,
                    inputs=[scenario_json, scenario_external_confirm],
                    outputs=[scenario_result],
                )

            with gr.Accordion("Inspect a stored comparison", open=False):
                advanced_session = gr.Dropdown(choices=initial_choices, label="Chat")
                advanced_refresh = gr.Button("Refresh chats")
                advanced_turn = gr.Number(value=0, precision=0, label="Turn index")
                advanced_blind = gr.Checkbox(label="Blind A/B", value=True)
                advanced_reveal = gr.Checkbox(label="Reveal mapping", value=False)
                advanced_compare_button = gr.Button("Load comparison")
                advanced_compare_result = gr.JSON(label="Comparison")
                advanced_refresh.click(
                    refresh_session_dropdown,
                    inputs=[advanced_session],
                    outputs=[advanced_session],
                )
                advanced_compare_button.click(
                    advanced_compare,
                    inputs=[advanced_session, advanced_turn, advanced_blind, advanced_reveal],
                    outputs=[advanced_compare_result],
                )

    return app


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
    app = build_app(workspace)
    return app.launch(
        server_name=host,
        server_port=int(port),
        inbrowser=bool(inbrowser),
        share=False,
    )
