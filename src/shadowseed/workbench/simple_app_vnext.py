"""Next-generation Workbench surface for Shadow Seed Learning.

This module intentionally stays thin. It reuses the existing WorkbenchController
and canonical SSL runtime, but presents one active conversation across Chat,
Shadow and Sources. Research mechanisms remain outside the normal path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowseed.workbench.controller import WorkbenchController


_CSS = """
.gradio-container { max-width: 1380px !important; margin: 0 auto; padding: 1rem 1.2rem 3rem !important; }
#ssv-hero {
  border: 1px solid var(--border-color-primary);
  border-radius: 24px;
  padding: 1rem 1.15rem;
  margin-bottom: .8rem;
  background: var(--background-fill-secondary);
}
#ssv-chat, #ssv-shadow, #ssv-sources {
  border: 1px solid var(--border-color-primary);
  border-radius: 22px;
  padding: .85rem;
  background: var(--background-fill-secondary);
}
#ssv-status, #ssv-shadow-summary, #ssv-source-result {
  border: 1px solid var(--border-color-primary);
  border-radius: 14px;
  padding: .7rem .8rem;
  background: var(--background-fill-primary);
}
#ssv-composer {
  position: sticky;
  bottom: .7rem;
  z-index: 20;
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: .65rem;
  margin-top: .65rem;
  background: var(--background-fill-primary);
}
.ssv-muted { opacity: .72; font-size: .9rem; }
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


def _recommended_setup(ctl: WorkbenchController) -> tuple[str, str | None, str]:
    try:
        models = ctl.discover_models("ollama")
    except Exception:
        models = []
    if models:
        return "ollama", models[0], f"Lokaal model gevonden: `{models[0]}`."
    return "fixture", None, "Geen lokaal Ollama-model gevonden. De offline demo is geselecteerd."


def _status(view: dict[str, Any] | None) -> str:
    if not view:
        return "Nog geen gesprek actief."

    reports = list(view.get("turn_reports", []))
    last = reports[-1] if reports else {}
    surfaced = list(last.get("surfaced_seed_ids", []) or [])
    used = (
        f"**{len(surfaced)} eerdere inzicht(en) als context aangeboden**"
        if surfaced
        else "**Geen geheugen aan het laatste antwoord aangeboden**"
    )
    model = str(view.get("model_id") or view.get("backend") or "onbekend")
    return (
        f"{used}  \n"
        f"Model: `{model}` · {int(view.get('turn', 0))} beurt(en) · "
        f"{len(view.get('seeds', []) or [])} geheugenpunt(en)"
    )


def _shadow_summary(view: dict[str, Any] | None) -> str:
    if not view:
        return "Start of kies een gesprek. Shadowseed werkt daarna automatisch mee."

    seeds = list(view.get("seeds", []) or [])
    if not seeds:
        return (
            "### Nog geen geheugenpunten\n"
            "Shadowseed heeft in dit gesprek nog niets als blijvend mogelijk relevant punt opgeslagen."
        )

    authorized = sum(bool(seed.get("current_gate_authorized", False)) for seed in seeds)
    blocked = sum(bool(seed.get("blocking", False)) for seed in seeds)
    reports = list(view.get("turn_reports", []) or [])
    used_ids = {
        str(seed_id)
        for report in reports
        for seed_id in (report.get("surfaced_seed_ids", []) or [])
    }
    return (
        "### Shadow\n"
        f"**{len(seeds)}** onthouden · **{authorized}** mogen nu meedenken · "
        f"**{len(used_ids)}** zijn ooit aan een antwoord aangeboden · **{blocked}** geblokkeerd\n\n"
        "Onthouden, toegestaan en gebruikt zijn verschillende stappen."
    )


def _seed_story(seed: dict[str, Any] | None) -> str:
    if not seed:
        return "Kies een geheugenpunt om de ontwikkeling te bekijken."

    text = str(seed.get("text", "")).strip() or "(geen tekst)"
    authorized = bool(seed.get("current_gate_authorized", False))
    blocking = bool(seed.get("blocking", False))
    occurrence = int(seed.get("occurrence_count", 0))
    evidence = int(seed.get("evidence_count", 0))

    if blocking:
        state = "Geblokkeerd: dit punt mag nu geen antwoord beïnvloeden."
    elif authorized:
        state = "Toegestaan: dit punt mag bij een relevante vraag worden aangeboden."
    else:
        state = "Onthouden, maar nog niet toegestaan om een antwoord te sturen."

    return (
        f"### {text}\n\n"
        f"**Status:** {state}\n\n"
        f"Teruggezien: **{occurrence}** · geverifieerde steun: **{evidence}**"
    )


def _comparison(comparison: dict[str, Any] | None) -> tuple[str, str, str]:
    if not comparison:
        return "", "", "Zet **Vergelijk dit antwoord zonder SSL** aan voor een same-turn control."

    a = str(comparison.get("candidate_a", ""))
    b = str(comparison.get("candidate_b", ""))
    a_label = str(comparison.get("candidate_a_label", "A"))
    b_label = str(comparison.get("candidate_b_label", "B"))
    mapping = {a_label: a, b_label: b}
    no_ssl = mapping.get("ssl_off") or mapping.get("vanilla") or a
    ssl_on = mapping.get("ssl_on") or mapping.get("shadowseed") or b
    used = bool(comparison.get("current_ssl_influence_observed", False))
    note = (
        "**SSL-context was op deze beurt aanwezig.**"
        if used
        else "**Er was op deze beurt geen geautoriseerde seed-context.** "
             "Een tekstverschil is dan geen bewijs van SSL-invloed."
    )
    return ssl_on, no_ssl, note


def _source_summary(result: dict[str, Any] | None) -> str:
    if not result:
        return "Voeg tekst of bestanden toe wanneer je Shadowseed buiten de chat wilt laten observeren."
    if result.get("error"):
        return f"**Fout:** {result['error']}"
    return (
        f"**{int(result.get('sources', 0))}** bron(nen) verwerkt · "
        f"**{int(result.get('new_seed_count', 0))}** nieuwe geheugenpunten.\n\n"
        "Een bron wordt niet automatisch waarheid of geverifieerd bewijs."
    )


def build_vnext_app(
    workspace: str | Path | None = None,
    *,
    controller: WorkbenchController | None = None,
):
    """Build the reset Workbench with one active session across all normal views."""

    gr = _gradio()
    ctl = controller or WorkbenchController(workspace)

    sessions = ctl.session_choices(ctl.list_sessions())
    initial_id = sessions[0][1] if sessions else None
    try:
        initial_view = ctl.session_view(initial_id) if initial_id else None
    except Exception:
        initial_view = None

    initial_chat = ctl.chat_messages(initial_view) if initial_view else []
    initial_seeds = ctl.seed_choices(initial_view) if initial_view else []
    auto_backend, auto_model, auto_note = _recommended_setup(ctl)

    def choices(selected: str | None = None):
        values = ctl.session_choices(ctl.list_sessions())
        valid = {value for _label, value in values}
        active = selected if selected in valid else (values[0][1] if values else None)
        return gr.update(choices=values, value=active), active

    def bundle(session_id: str | None):
        if not session_id:
            return [], _status(None), _shadow_summary(None), gr.update(choices=[], value=None), None
        view = ctl.session_view(session_id)
        return (
            ctl.chat_messages(view),
            _status(view),
            _shadow_summary(view),
            gr.update(choices=ctl.seed_choices(view), value=None),
            view,
        )

    def select_session(session_id: str | None):
        chat_value, status_value, shadow_value, seed_update, view = bundle(session_id)
        return (
            session_id,
            chat_value,
            status_value,
            shadow_value,
            seed_update,
            view,
            _seed_story(None),
            None,
            "",
            "",
            "Zet **Vergelijk dit antwoord zonder SSL** aan voor een same-turn control.",
            _source_summary(None),
        )

    def provider_changed(provider: str):
        if provider == "ollama":
            try:
                models = ctl.discover_models("ollama")
            except Exception as exc:
                return gr.update(choices=[], value=None), f"Ollama-modellen ophalen lukte niet: {exc}"
            return (
                gr.update(choices=models, value=(models[0] if models else None)),
                ("Lokaal Ollama-model geselecteerd." if models else "Geen lokaal Ollama-model gevonden."),
            )
        if provider == "fixture":
            return gr.update(choices=[], value=None), "Offline demo. Geen extern model nodig."
        return gr.update(choices=[], value=None), "Vul een model-ID in. Deze provider kan extern zijn."

    def create_chat(
        title: str,
        provider: str,
        model_id: str | None,
        hosted_confirmed: bool,
    ):
        session_id = ctl.create_session(
            title=(title or "").strip() or "Nieuwe chat",
            profile_id="balanced",
            backend=provider,
            model_id=(None if provider == "fixture" else (model_id or None)),
            runtime_mode="live",
            embedding_backend=ctl.default_embedding_backend(provider),
            external_confirmed=bool(hosted_confirmed),
        )
        selector, _selected = choices(session_id)
        chat, status, shadow, seed_update, view = bundle(session_id)
        return (
            session_id,
            selector,
            chat,
            status,
            shadow,
            seed_update,
            view,
            _seed_story(None),
            None,
            "",
            "",
            "Zet **Vergelijk dit antwoord zonder SSL** aan voor een same-turn control.",
            _source_summary(None),
        )

    def send(
        session_id: str | None,
        question: str,
        compare_without_ssl: bool,
        hosted_confirmed: bool,
    ):
        if not session_id:
            return gr.update(), "Maak eerst een gesprek.", gr.update(), gr.update(), gr.update(), question, "", "", ""
        if not str(question or "").strip():
            return gr.update(), "Typ eerst een bericht.", gr.update(), gr.update(), gr.update(), question, "", "", ""

        result = ctl.send_turn(
            session_id,
            question,
            compare_without_ssl=bool(compare_without_ssl),
            comparison_mode="authorized",
            external_confirmed=bool(hosted_confirmed),
        )
        view = result["session"]
        ssl_on, no_ssl, comparison_note = _comparison(result.get("comparison"))
        return (
            ctl.chat_messages(view),
            _status(view),
            _shadow_summary(view),
            gr.update(choices=ctl.seed_choices(view), value=None),
            view,
            "",
            ssl_on,
            no_ssl,
            comparison_note,
        )

    def inspect_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return _seed_story(None), None
        seed = ctl.seed_view(session_id, seed_id)
        return _seed_story(seed), seed

    def falsify(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return "Kies eerst een geheugenpunt.", gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        ctl.falsify_seed(session_id, seed_id)
        view = ctl.session_view(session_id)
        seed = ctl.seed_view(session_id, seed_id)
        return (
            _seed_story(seed),
            _shadow_summary(view),
            _status(view),
            view,
            gr.update(choices=ctl.seed_choices(view), value=seed_id),
        )

    def verify_evidence(
        session_id: str | None,
        seed_id: str | None,
        source_ref: str,
        note: str,
        attested: bool,
    ):
        if not session_id or not seed_id:
            return "Kies eerst een geheugenpunt.", gr.update(), gr.update(), gr.update()
        ctl.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=source_ref,
            note=note,
            operator_verified=bool(attested),
        )
        view = ctl.session_view(session_id)
        seed = ctl.seed_view(session_id, seed_id)
        return (
            _seed_story(seed),
            _shadow_summary(view),
            _status(view),
            view,
            gr.update(choices=ctl.seed_choices(view), value=seed_id),
        )

    def ingest(
        session_id: str | None,
        pasted: str,
        files: list[str] | str | None,
        hosted_confirmed: bool,
    ):
        if not session_id:
            return _source_summary({"error": "Maak of kies eerst een gesprek."}), gr.update(), gr.update(), gr.update(), gr.update(), pasted

        if files is None:
            paths: list[str] = []
        elif isinstance(files, (str, Path)):
            paths = [str(files)]
        else:
            paths = [str(item) for item in files if item]

        result = ctl.ingest_sources(
            session_id,
            pasted_text=pasted or "",
            file_paths=paths,
            external_confirmed=bool(hosted_confirmed),
        )
        view = result["session"]
        return (
            _source_summary(result),
            _shadow_summary(view),
            _status(view),
            gr.update(choices=ctl.seed_choices(view), value=None),
            view,
            "",
        )

    with gr.Blocks(title="Shadowseed", css=_CSS) as app:
        active_session = gr.State(initial_id)

        with gr.Group(elem_id="ssv-hero"):
            gr.Markdown("# Shadowseed")
            gr.Markdown(
                "Chat normaal. Shadowseed merkt mogelijke ontbrekende inzichten op, "
                "onthoudt ze zonder ze meteen te geloven en gebruikt ze alleen wanneer dat mag en relevant is."
            )

        with gr.Row():
            session_select = gr.Dropdown(
                choices=sessions,
                value=initial_id,
                label="Gesprek",
                scale=4,
            )
            with gr.Accordion("Nieuwe chat", open=False):
                new_title = gr.Textbox(label="Naam", value="Nieuwe chat")
                provider = gr.Dropdown(
                    choices=[
                        ("Ollama · lokaal", "ollama"),
                        ("OpenAI · online", "openai"),
                        ("Hugging Face · lokaal", "hf-transformers"),
                        ("Offline demo", "fixture"),
                    ],
                    value=auto_backend,
                    label="Modelprovider",
                )
                model_id = gr.Dropdown(
                    choices=([auto_model] if auto_model else []),
                    value=auto_model,
                    allow_custom_value=True,
                    label="Model",
                )
                model_note = gr.Markdown(auto_note, elem_classes=["ssv-muted"])
                rescan_models = gr.Button("Zoek lokale modellen opnieuw", variant="secondary")
                hosted_confirm = gr.Checkbox(
                    label="Ik begrijp dat deze provider inhoud extern kan verwerken",
                    value=False,
                )
                create_button = gr.Button("Start nieuwe chat", variant="primary")

        with gr.Tabs():
            with gr.Tab("Chat"):
                with gr.Column(elem_id="ssv-chat"):
                    chat = gr.Chatbot(value=initial_chat, label="Gesprek", height=520)
                    status = gr.Markdown(_status(initial_view), elem_id="ssv-status")
                    with gr.Row(elem_id="ssv-composer"):
                        question = gr.Textbox(
                            label="Bericht",
                            placeholder="Typ je bericht…",
                            lines=2,
                            scale=5,
                        )
                        send_button = gr.Button("Versturen", variant="primary", scale=1)
                    compare = gr.Checkbox(
                        label="Vergelijk dit antwoord zonder SSL",
                        value=False,
                    )
                    with gr.Accordion("Vergelijking", open=False):
                        comparison_note = gr.Markdown(
                            "Zet **Vergelijk dit antwoord zonder SSL** aan voor een same-turn control."
                        )
                        with gr.Row():
                            ssl_answer = gr.Markdown(label="Met SSL")
                            no_ssl_answer = gr.Markdown(label="Zonder SSL")

            with gr.Tab("Shadow"):
                with gr.Column(elem_id="ssv-shadow"):
                    shadow_summary = gr.Markdown(_shadow_summary(initial_view), elem_id="ssv-shadow-summary")
                    seed_select = gr.Dropdown(
                        choices=initial_seeds,
                        value=None,
                        label="Geheugenpunt",
                    )
                    seed_story = gr.Markdown(_seed_story(None))
                    with gr.Accordion("Menselijke controle", open=False):
                        gr.Markdown(
                            "Alleen hier is jouw inhoudelijke beslissing nodig: een punt tegenspreken "
                            "of onafhankelijk geverifieerde steun toevoegen."
                        )
                        contradict_button = gr.Button("Markeer als tegengesproken", variant="stop")
                        evidence_source = gr.Textbox(label="Bronreferentie")
                        evidence_note = gr.Textbox(label="Notitie", lines=2)
                        evidence_attest = gr.Checkbox(
                            label="Ik heb deze steun onafhankelijk van modeloutput gecontroleerd",
                            value=False,
                        )
                        evidence_button = gr.Button("Voeg geverifieerde steun toe")
                    with gr.Accordion("Technische audit", open=False):
                        session_json = gr.JSON(value=initial_view, label="Gesprekstoestand")
                        seed_json = gr.JSON(label="Geheugenpunt")

            with gr.Tab("Bronnen"):
                with gr.Column(elem_id="ssv-sources"):
                    gr.Markdown(
                        "Voeg materiaal toe aan hetzelfde actieve gesprek. Shadowseed observeert dit automatisch; "
                        "de bron wordt niet automatisch bewijs."
                    )
                    source_text = gr.Textbox(label="Tekst", lines=9)
                    source_files = gr.File(
                        label="Bestanden",
                        file_count="multiple",
                        type="filepath",
                        file_types=[".txt", ".md", ".markdown", ".json", ".csv"],
                    )
                    ingest_button = gr.Button("Verwerk", variant="primary")
                    source_result = gr.Markdown(_source_summary(None), elem_id="ssv-source-result")

            with gr.Tab("Onderzoek"):
                gr.Markdown(
                    "### Onderzoeksmethoden\n"
                    "Longitudinale vanilla-trajecten, shadow pressure, self-reinforcement, "
                    "Gate-experimenten en alternatieve embeddings horen hier thuis, niet in de gewone chat.\n\n"
                    "Deze reset bouwt eerst de normale Workbench opnieuw op. De bestaande researchmechanismen "
                    "blijven in de backend behouden en worden daarna hier expliciet teruggebracht."
                )

        session_select.change(
            select_session,
            inputs=[session_select],
            outputs=[
                active_session,
                chat,
                status,
                shadow_summary,
                seed_select,
                session_json,
                seed_story,
                seed_json,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
                source_result,
            ],
        )

        provider.change(
            provider_changed,
            inputs=[provider],
            outputs=[model_id, model_note],
        )
        rescan_models.click(
            provider_changed,
            inputs=[provider],
            outputs=[model_id, model_note],
        )

        create_button.click(
            create_chat,
            inputs=[new_title, provider, model_id, hosted_confirm],
            outputs=[
                active_session,
                session_select,
                chat,
                status,
                shadow_summary,
                seed_select,
                session_json,
                seed_story,
                seed_json,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
                source_result,
            ],
        )

        send_button.click(
            send,
            inputs=[active_session, question, compare, hosted_confirm],
            outputs=[
                chat,
                status,
                shadow_summary,
                seed_select,
                session_json,
                question,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
            ],
        )
        question.submit(
            send,
            inputs=[active_session, question, compare, hosted_confirm],
            outputs=[
                chat,
                status,
                shadow_summary,
                seed_select,
                session_json,
                question,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
            ],
        )

        seed_select.change(
            inspect_seed,
            inputs=[active_session, seed_select],
            outputs=[seed_story, seed_json],
        )
        contradict_button.click(
            falsify,
            inputs=[active_session, seed_select],
            outputs=[seed_story, shadow_summary, status, session_json, seed_select],
        )
        evidence_button.click(
            verify_evidence,
            inputs=[active_session, seed_select, evidence_source, evidence_note, evidence_attest],
            outputs=[seed_story, shadow_summary, status, session_json, seed_select],
        )

        ingest_button.click(
            ingest,
            inputs=[active_session, source_text, source_files, hosted_confirm],
            outputs=[source_result, shadow_summary, status, seed_select, session_json, source_text],
        )

    return app
