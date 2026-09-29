"""Nederlandse, chatgerichte Workbench-interface voor Shadow Seed Learning.

Deze module is bewust een presentatielaag. De bestaande controller, Validation
Gate, opslag, audittrail en point-of-use veiligheidsgrenzen blijven leidend.
De eenvoudige interface verbergt technische keuzes standaard, maar verwijdert
geen controleerbaarheid.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shadowseed.workbench.controller import WorkbenchController


_NL_CSS = """
.gradio-container {
  max-width: 1500px !important;
  margin: 0 auto;
  padding: 0.85rem 1rem 2rem !important;
}
#ss-hero {
  border: 1px solid var(--border-color-primary);
  border-radius: 24px;
  padding: 1.2rem 1.35rem;
  margin-bottom: .8rem;
  background: linear-gradient(145deg, var(--background-fill-secondary), rgba(255,255,255,.025));
  box-shadow: 0 16px 45px rgba(0,0,0,.12);
}
#ss-hero h1 { margin: 0 0 .2rem 0; letter-spacing: -.03em; }
#ss-hero p { margin-bottom: .35rem; }
#ss-side {
  border: 1px solid var(--border-color-primary);
  border-radius: 20px;
  padding: .9rem;
  background: var(--background-fill-secondary);
}
#ss-chat {
  border: 1px solid var(--border-color-primary);
  border-radius: 20px;
  overflow: hidden;
}
#ss-status {
  padding: .65rem .8rem;
  border-radius: 12px;
  background: var(--background-fill-secondary);
  font-size: .9rem;
}
#ss-composer {
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: .7rem;
  margin-top: .65rem;
  background: var(--background-fill-primary);
  box-shadow: 0 10px 28px rgba(0,0,0,.08);
}
.ss-card {
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: .85rem 1rem;
  background: var(--background-fill-secondary);
}
.ss-muted { opacity: .76; font-size: .9rem; }
.ss-kicker {
  opacity: .7;
  font-size: .75rem;
  font-weight: 700;
  letter-spacing: .08em;
  text-transform: uppercase;
}
#ss-memory-story {
  min-height: 240px;
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: 1rem 1.1rem;
  background: var(--background-fill-secondary);
}
#ss-source-result, #ss-verify-result {
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: .9rem 1rem;
  background: var(--background-fill-secondary);
  min-height: 140px;
}
#ss-about-flow {
  font-size: 1.03rem;
  padding: .8rem 1rem;
  border-radius: 14px;
  background: var(--background-fill-secondary);
}
"""


_AUTHORITY_UI: dict[str, tuple[str, str]] = {
    "strict": (
        "Veilig",
        "Shadowseed observeert automatisch, maar verhoogt zijn invloed niet alleen omdat iets vaak terugkomt.",
    ),
    "assisted": (
        "Meedenkend",
        "Shadowseed doet het voorbereidende werk automatisch en vraagt aandacht wanneer extra controle nodig is.",
    ),
    "autonomous": (
        "Zelfstandig",
        "Terugkerende patronen mogen via de bestaande Validation Gate zelfstandig meer invloed verdienen.",
    ),
    "open": (
        "Onderzoek",
        "De ruimste experimentele stand. Audit, herkomst en veiligheidscontroles blijven zichtbaar.",
    ),
}

_PROFILE_UI: dict[str, tuple[str, str]] = {
    "demo": ("Demo", "Voorspelbare demostand voor uitleg en controle."),
    "balanced": ("Normaal", "Praktische standaard voor dagelijks gebruik."),
    "conservative": ("Voorzichtig", "Laat minder geheugenpunten terugkomen en stelt hogere relevantie-eisen."),
    "exploratory": ("Ruim", "Laat meer relevante geheugenpunten meedoen wanneer dat volgens de regels mag."),
}

_BACKEND_UI: dict[str, tuple[str, str]] = {
    "ollama": (
        "Ollama · lokaal",
        "Draait met een lokaal Ollama-model. Je chatinhoud blijft voor het taalmodel op deze computer.",
    ),
    "openai": (
        "OpenAI · online",
        "Gebruikt een hosted OpenAI-model. Chatinhoud wordt naar de gekozen provider gestuurd.",
    ),
    "hf-transformers": (
        "Hugging Face · lokaal",
        "Draait het gekozen Transformers-model lokaal nadat het model beschikbaar is.",
    ),
    "fixture": (
        "Demomodel · offline",
        "Voorspelbare offline demonstratie. Handig om Shadowseed te bekijken, niet bedoeld als krachtig taalmodel.",
    ),
}

_STATUS_NL = {
    "NEW": "Nieuw",
    "ACTIVE": "Actief",
    "DORMANT": "Slapend",
    "DECAYING": "Vervaagt",
    "PROMOTED": "Mag meedenken",
    "CONTRADICTED": "Geblokkeerd",
    "EXPIRED": "Verlopen",
}


def _gradio():
    try:
        import gradio as gr
    except ImportError as exc:  # pragma: no cover - optionele dependency
        raise RuntimeError(
            "De Workbench-interface vereist de workbench-extra: "
            "python -m pip install 'shadowseed[workbench]'"
        ) from exc
    return gr


def _fout(exc: Exception) -> str:
    return f"**Fout:** {type(exc).__name__}: {exc}"


def _authority_explainer(profile_id: str | None) -> str:
    label, explanation = _AUTHORITY_UI.get(
        str(profile_id or "strict"),
        _AUTHORITY_UI["strict"],
    )
    return (
        f"**{label}**  \\n{explanation}\\n\\n"
        "De technische autoriteitsregels blijven op de achtergrond volledig auditbaar."
    )


def _recommended_setup(controller: WorkbenchController) -> tuple[str, str | None, str]:
    """Kies automatisch een veilige, bruikbare startconfiguratie."""

    try:
        models = controller.discover_models("ollama")
    except Exception:
        models = []
    if models:
        return (
            "ollama",
            models[0],
            f"**Automatisch gekozen:** lokaal Ollama-model `{models[0]}`.",
        )
    return (
        "fixture",
        None,
        "**Automatisch gekozen:** offline demomodel. "
        "Geen lokaal Ollama-model gevonden. Je kunt dit onder Instellingen wijzigen.",
    )


def _model_note(backend: str, model_id: str | None = None) -> str:
    label, explanation = _BACKEND_UI.get(
        backend,
        (backend or "Onbekend model", ""),
    )
    model = f" · `{model_id}`" if model_id else ""
    return f"**{label}**{model}  \\n{explanation}"


def _chat_status(view: dict[str, Any] | None) -> str:
    if not view:
        return "Nog geen gesprek geopend. Klik op **Nieuwe chat** om te beginnen."

    seeds = list(view.get("seeds", []))
    promoted = sum(str(seed.get("status", "")).upper() == "PROMOTED" for seed in seeds)
    blocked = sum(bool(seed.get("blocking", False)) for seed in seeds)
    review = len(view.get("authority_review_seed_ids", []) or [])
    turns = int(view.get("turn", 0) or 0)
    model = str(view.get("model_id") or view.get("backend") or "model")
    profile = _AUTHORITY_UI.get(
        str(view.get("authority_profile_id", "strict")),
        ("Aangepast", ""),
    )[0]

    extras: list[str] = []
    if promoted:
        extras.append(f"{promoted} mag later meedenken")
    if review:
        extras.append(f"{review} vraagt controle")
    if blocked:
        extras.append(f"{blocked} geblokkeerd")
    seed_text = (
        f"{len(seeds)} geheugenpunt(en)"
        + (f" · {' · '.join(extras)}" if extras else "")
    )

    return (
        f"**{model}** · {turns} bericht(en) · werkwijze **{profile}**  \\n"
        f"Shadowseed: {seed_text}"
    )


def _memory_overview(view: dict[str, Any] | None) -> str:
    if not view:
        return "Kies een gesprek om het Shadowseed-geheugen te bekijken."

    seeds = list(view.get("seeds", []))
    promoted = sum(str(item.get("status", "")).upper() == "PROMOTED" for item in seeds)
    blocked = sum(bool(item.get("blocking", False)) for item in seeds)
    used: set[str] = set()
    for report in view.get("turn_reports", []) or []:
        used.update(str(seed_id) for seed_id in report.get("surfaced_seed_ids", []) or [])

    return (
        f"**{len(seeds)}** geheugenpunt(en) · "
        f"**{promoted}** mag meedenken · "
        f"**{len(used)}** daadwerkelijk gebruikt · "
        f"**{blocked}** geblokkeerd\\n\\n"
        "Een geheugenpunt is een mogelijke ontbrekende invalshoek. Het is niet automatisch een feit."
    )


def _seed_story(view: dict[str, Any] | None) -> str:
    if not view:
        return (
            "## Kies een geheugenpunt\\n"
            "Je ziet hier in gewone taal wat Shadowseed heeft opgemerkt en wat ermee is gebeurd."
        )

    status_raw = str(view.get("status", "UNKNOWN")).upper()
    status = _STATUS_NL.get(status_raw, status_raw.title())
    text = str(view.get("text", "")).strip() or "(geen tekst)"
    occurrences = int(view.get("occurrence_count", 0) or 0)
    evidence = int(view.get("evidence_count", 0) or 0)
    blocking = bool(view.get("blocking", False))
    review = bool(view.get("review_required", False))
    timeline = list(view.get("timeline", []) or [])
    used = sum(str(item.get("type", "")) == "influence" for item in timeline)

    if blocking:
        action = (
            "**Wat nu?** Dit punt is geblokkeerd door een tegenspraak en kan niet normaal "
            "meedenken totdat die situatie bewust wordt beoordeeld."
        )
    elif review:
        action = (
            "**Wat nu?** Shadowseed ziet voldoende herhaling om aandacht te vragen, "
            "maar de gekozen veilige werkwijze vereist nog onafhankelijke onderbouwing."
        )
    elif status_raw == "PROMOTED" and used:
        action = (
            f"**Wat nu?** Dit punt mocht meedenken en is al **{used}×** daadwerkelijk gebruikt. "
            "De technische audit laat precies zien wanneer."
        )
    elif status_raw == "PROMOTED":
        action = (
            "**Wat nu?** Niets. Dit punt mág later meedenken, maar alleen als het bij een nieuwe "
            "vraag ook echt relevant is."
        )
    else:
        action = (
            "**Wat nu?** Meestal niets. Shadowseed laat dit punt automatisch verder ontwikkelen, "
            "vervagen of terugkomen."
        )

    return (
        f"### {status}\\n"
        f"## {text}\\n\\n"
        f"**Gezien:** {occurrences}× · **onderbouwing:** {evidence} · **gebruikt:** {used}×\\n\\n"
        f"{action}"
    )


def _source_summary(result: dict[str, Any] | None) -> str:
    if not result:
        return (
            "## Nog niets toegevoegd\\n"
            "Plak tekst of kies bestanden. Shadowseed leest de inhoud in stukken en bouwt "
            "daarmee het geheugen van het gekozen gesprek op."
        )
    if result.get("error"):
        return f"**Bronnen konden niet worden verwerkt:** {result['error']}"

    promoted = len(result.get("promoted_seed_ids", []) or [])
    review = len(result.get("authority_review_seed_ids", []) or [])
    names = ", ".join(result.get("source_names", []) or []) or "bron"
    return (
        "## Klaar\\n"
        f"**{int(result.get('sources', 0))}** bron(nen) · "
        f"**{int(result.get('chunks', 0))}** tekstdeel/delen · "
        f"**{int(result.get('new_seed_count', 0))}** nieuwe geheugenpunten  \\n"
        f"**{promoted}** mag meedenken · **{review}** vraagt controle  \\n"
        f"Bronnen: {names}\\n\\n"
        "**Belangrijk:** een upload wordt niet automatisch waarheid of bewijs. "
        "De normale autoriteitsregels blijven gelden."
    )


def _comparison_view(comparison: dict[str, Any] | None) -> tuple[str, str, str]:
    if not comparison:
        return (
            "",
            "",
            "Zet **Vergelijk dit antwoord zonder Shadowseed** aan vóór je een bericht verstuurt "
            "als je een directe vergelijking wilt.",
        )
    labels = {
        str(comparison.get("candidate_a_label", "")): str(comparison.get("candidate_a", "")),
        str(comparison.get("candidate_b_label", "")): str(comparison.get("candidate_b", "")),
    }
    with_ssl = labels.get("ssl_on") or labels.get("shadowseed") or ""
    without_ssl = labels.get("ssl_off") or labels.get("baseline") or ""
    influenced = bool(comparison.get("ssl_influence_observed"))
    note = (
        "**Shadowseed heeft bij dit antwoord aantoonbaar een geautoriseerd geheugenpunt gebruikt.** "
        "Vergelijk de antwoorden inhoudelijk; het Shadowseed-antwoord is niet automatisch beter."
        if influenced
        else
        "**Bij dit antwoord is geen geautoriseerd geheugenpunt gebruikt.** "
        "Een tekstverschil mag daarom niet aan Shadowseed worden toegeschreven."
    )
    return with_ssl, without_ssl, note


def _verify_summary(comparison: dict[str, Any] | None) -> str:
    if not comparison:
        return (
            "## Nog niets gecontroleerd\\n"
            "Kies een gesprek en berichtnummer. Een controle is alleen beschikbaar als voor dat "
            "bericht vooraf een vergelijking zonder Shadowseed is opgeslagen."
        )
    influenced = bool(comparison.get("ssl_influence_observed"))
    surfaced = list(comparison.get("surfaced_seed_ids", []) or [])
    question = str(comparison.get("question", "")).strip()
    if influenced:
        verdict = (
            "### Ja, Shadowseed heeft hier aantoonbaar meegedacht\\n"
            f"Er zijn **{len(surfaced)}** geautoriseerde geheugenpunt(en) gebruikt."
        )
    else:
        verdict = (
            "### Nee, voor dit antwoord is geen Shadowseed-invloed aangetoond\\n"
            "Eventuele verschillen tussen twee generaties kunnen normale modelvariatie zijn."
        )
    return verdict + (f"\\n\\n**Vraag:** {question}" if question else "")


def build_simple_app(
    workspace: str | Path | None = None,
    *,
    controller: WorkbenchController | None = None,
):
    """Bouw de Nederlandse, chatgerichte Workbench."""

    gr = _gradio()
    ctl = controller or WorkbenchController(workspace)

    initial_sessions = ctl.session_choices(ctl.list_sessions())
    auto_backend, auto_model, auto_setup_note = _recommended_setup(ctl)

    authority_choices = [
        (f"{label} — {description}", profile_id)
        for profile_id, (label, description) in _AUTHORITY_UI.items()
    ]
    provider_choices = [
        (_BACKEND_UI[key][0], key)
        for key in ("ollama", "openai", "hf-transformers", "fixture")
    ]
    relevance_choices = [
        (f"{_PROFILE_UI.get(item['profile_id'], (item['label'], ''))[0]} — "
         f"{_PROFILE_UI.get(item['profile_id'], (item['label'], item['description']))[1]}",
         item["profile_id"])
        for item in ctl.profiles()
    ]

    def session_choices() -> list[tuple[str, str]]:
        return ctl.session_choices(ctl.list_sessions())

    def dropdown_update(choices: list[tuple[str, str]], value: str | None = None):
        valid = {item[1] for item in choices}
        selected = value if value in valid else (choices[0][1] if choices else None)
        return gr.update(choices=choices, value=selected)

    def refresh_session_dropdown(current: str | None):
        return dropdown_update(session_choices(), current)

    def provider_changed(backend: str, current_model: str | None):
        if backend == "ollama":
            try:
                models = ctl.discover_models("ollama")
            except Exception as exc:
                return (
                    gr.update(choices=[], value=current_model or None),
                    _model_note("ollama") + f"\\n\\n**Lokaal model zoeken lukte niet:** {exc}",
                    ctl.default_embedding_backend("ollama"),
                )
            selected = current_model if current_model in models else (models[0] if models else None)
            note = _model_note("ollama", selected)
            if not models:
                note += "\\n\\nGeen lokaal Ollama-model gevonden."
            return (
                gr.update(choices=models, value=selected),
                note,
                ctl.default_embedding_backend("ollama"),
            )
        selected = None if backend == "fixture" else current_model or None
        return (
            gr.update(choices=[], value=selected),
            _model_note(backend, selected),
            ctl.default_embedding_backend(backend),
        )

    def refresh_models(backend: str, current_model: str | None):
        model_update, note, _embedding = provider_changed(backend, current_model)
        return model_update, note

    def create_chat(
        title: str,
        authority_profile_id: str,
        backend: str,
        model_id: str,
        profile_id: str,
        embedding_backend: str,
        embedding_model: str,
        hosted_confirmed: bool,
    ):
        try:
            clean_title = (title or "").strip() or "Nieuwe chat"
            session_id = ctl.create_session(
                title=clean_title,
                profile_id=profile_id or "balanced",
                authority_profile_id=authority_profile_id or "strict",
                backend=backend,
                model_id=(None if backend == "fixture" else (model_id or None)),
                runtime_mode="live",
                embedding_backend=embedding_backend or ctl.default_embedding_backend(backend),
                embedding_model=embedding_model or None,
                allow_toy_embedder=False,
                external_confirmed=bool(hosted_confirmed),
            )
            view = ctl.session_view(session_id)
            return (
                dropdown_update(session_choices(), session_id),
                ctl.chat_messages(view),
                _chat_status(view),
                view,
                "",
            )
        except Exception as exc:
            return gr.update(), [], _fout(exc), None, ""

    def load_chat(session_id: str | None):
        if not session_id:
            return [], _chat_status(None), None
        try:
            view = ctl.session_view(session_id)
            return ctl.chat_messages(view), _chat_status(view), view
        except Exception as exc:
            return [], _fout(exc), None

    def send_message(
        session_id: str | None,
        question: str,
        compare_without_ssl: bool,
        hosted_confirmed: bool,
    ):
        if not session_id:
            return gr.update(), "Maak eerst een nieuwe chat.", None, question, "", "", ""
        if not str(question or "").strip():
            return gr.update(), "Typ eerst een bericht.", None, question, "", "", ""
        try:
            result = ctl.send_turn(
                session_id,
                question,
                compare_without_ssl=bool(compare_without_ssl),
                external_confirmed=bool(hosted_confirmed),
            )
            view = result["session"]
            with_ssl, without_ssl, note = _comparison_view(result.get("comparison"))
            return (
                ctl.chat_messages(view),
                _chat_status(view),
                result["report"],
                "",
                with_ssl,
                without_ssl,
                note,
            )
        except Exception as exc:
            return gr.update(), _fout(exc), None, question, "", "", _fout(exc)

    def ingest_sources(
        session_id: str | None,
        pasted_text: str,
        uploaded_files: list[str] | str | None,
        hosted_confirmed: bool,
    ):
        if not session_id:
            return _source_summary({"error": "Kies eerst een gesprek."}), gr.update(), None, pasted_text
        try:
            if uploaded_files is None:
                paths: list[str] = []
            elif isinstance(uploaded_files, (str, Path)):
                paths = [str(uploaded_files)]
            else:
                paths = [str(item) for item in uploaded_files if item]
            result = ctl.ingest_sources(
                session_id,
                pasted_text=pasted_text or "",
                file_paths=paths,
                external_confirmed=bool(hosted_confirmed),
            )
            view = result["session"]
            return (
                _source_summary(result),
                gr.update(choices=ctl.seed_choices(view), value=None),
                view,
                "",
            )
        except Exception as exc:
            return _source_summary({"error": f"{type(exc).__name__}: {exc}"}), gr.update(), None, pasted_text

    def memory_session_changed(session_id: str | None):
        if not session_id:
            return gr.update(choices=[], value=None), _memory_overview(None)
        try:
            view = ctl.session_view(session_id)
            return dropdown_update(ctl.seed_choices(view)), _memory_overview(view)
        except Exception as exc:
            return gr.update(), _fout(exc)

    def inspect_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return _seed_story(None), None, None
        try:
            view = ctl.seed_view(session_id, seed_id)
            return _seed_story(view), view, view.get("timeline", [])
        except Exception as exc:
            err = {"error": f"{type(exc).__name__}: {exc}"}
            return _fout(exc), err, None

    def falsify_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return {"error": "Kies eerst een gesprek en geheugenpunt."}, _seed_story(None), None, None
        try:
            result = ctl.falsify_seed(session_id, seed_id)
            view = ctl.seed_view(session_id, seed_id)
            return result, _seed_story(view), view, view.get("timeline", [])
        except Exception as exc:
            err = {"error": f"{type(exc).__name__}: {exc}"}
            return err, _fout(exc), err, None

    def submit_verified_evidence(
        session_id: str | None,
        seed_id: str | None,
        source_ref: str,
        note: str,
        operator_verified: bool,
    ):
        if not session_id or not seed_id:
            return (
                {"error": "Kies eerst een gesprek en geheugenpunt."},
                _seed_story(None),
                None,
                None,
                "",
                False,
            )
        try:
            result = ctl.submit_verified_evidence(
                session_id,
                seed_id,
                source_ref=source_ref,
                note=note,
                operator_verified=bool(operator_verified),
            )
            view = ctl.seed_view(session_id, seed_id)
            return result, _seed_story(view), view, view.get("timeline", []), "", False
        except Exception as exc:
            err = {"error": f"{type(exc).__name__}: {exc}"}
            return err, _fout(exc), err, None, "", False

    def verify_turn(session_id: str | None, turn_index: float):
        if not session_id:
            return "Kies eerst een gesprek.", None
        try:
            comparison = ctl.compare_turn(
                session_id,
                int(turn_index),
                blinded=False,
                reveal=True,
            )
            return _verify_summary(comparison), comparison
        except Exception as exc:
            return (
                "### Geen opgeslagen vergelijking beschikbaar\\n"
                "Zet in de chat vóór het versturen **Vergelijk dit antwoord zonder Shadowseed** aan. "
                f"Technische melding: {type(exc).__name__}: {exc}",
                {"error": f"{type(exc).__name__}: {exc}"},
            )

    def record_feedback(
        session_id: str | None,
        turn_index: float,
        overall: str,
        seed_effect: str,
        note: str,
    ):
        if not session_id:
            return {"error": "Kies eerst een gesprek."}
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
            return "Kies eerst een gesprek."
        try:
            return ctl.export_report(
                session_id,
                destination or "shadowseed-volledig-rapport.zip",
            )
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"

    def export_support(session_id: str | None, destination: str):
        if not session_id:
            return "Kies eerst een gesprek."
        try:
            return ctl.export_support_bundle(
                session_id,
                destination or "shadowseed-support.zip",
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

    with gr.Blocks(title="Shadowseed", css=_NL_CSS) as app:
        with gr.Group(elem_id="ss-hero"):
            gr.Markdown("# Shadowseed")
            gr.Markdown(
                "**Praat gewoon met je model. Shadowseed kijkt op de achtergrond mee.**  \\n"
                "Het onthoudt mogelijke ontbrekende invalshoeken, laat die gecontroleerd groeien "
                "en brengt ze alleen terug wanneer ze later relevant én toegestaan zijn."
            )
            gr.Markdown(
                "Chat centraal · geheugen zichtbaar · uitleg in gewone taal · techniek alleen wanneer jij die wilt",
                elem_classes=["ss-muted"],
            )

        with gr.Tab("Chat"):
            with gr.Row():
                with gr.Column(scale=1, min_width=300):
                    with gr.Group(elem_id="ss-side"):
                        gr.Markdown("### Gesprekken")
                        session_select = gr.Dropdown(
                            choices=initial_sessions,
                            value=initial_sessions[0][1] if initial_sessions else None,
                            label="Open gesprek",
                        )
                        refresh_sessions = gr.Button("Vernieuwen", variant="secondary")
                        new_chat = gr.Button("＋ Nieuwe chat", variant="primary")

                        gr.Markdown("### Automatische start", elem_classes=["ss-kicker"])
                        auto_note = gr.Markdown(auto_setup_note)
                        model_note = gr.Markdown(_model_note(auto_backend, auto_model))

                        with gr.Accordion("Instellingen voor nieuwe chats", open=False):
                            title = gr.Textbox(
                                label="Naam van het gesprek",
                                value="Nieuwe chat",
                            )
                            authority_profile = gr.Radio(
                                choices=authority_choices,
                                value="strict",
                                label="Hoe zelfstandig mag Shadowseed werken?",
                            )
                            authority_help = gr.Markdown(_authority_explainer("strict"))
                            backend = gr.Dropdown(
                                choices=provider_choices,
                                value=auto_backend,
                                label="Taalmodel",
                            )
                            model_id = gr.Dropdown(
                                choices=([auto_model] if auto_model else []),
                                value=auto_model,
                                allow_custom_value=True,
                                label="Model",
                            )
                            refresh_models_button = gr.Button(
                                "Lokale modellen opnieuw zoeken",
                                variant="secondary",
                            )
                            hosted_confirm = gr.Checkbox(
                                label="Ik begrijp dat chatinhoud bij een online model naar de provider wordt gestuurd",
                                value=False,
                            )
                            with gr.Accordion("Technische instellingen", open=False):
                                profile = gr.Dropdown(
                                    choices=relevance_choices,
                                    value="balanced",
                                    label="Relevantieprofiel",
                                )
                                embedding_backend = gr.Dropdown(
                                    choices=list(ctl.embedding_backends()),
                                    value=ctl.default_embedding_backend(auto_backend),
                                    label="Semantische vergelijking",
                                )
                                embedding_model = gr.Textbox(
                                    label="Eigen embeddingmodel (optioneel)",
                                )

                with gr.Column(scale=3, min_width=620):
                    chat = gr.Chatbot(label="Gesprek", height=560, elem_id="ss-chat")
                    chat_status = gr.Markdown(_chat_status(None), elem_id="ss-status")
                    with gr.Group(elem_id="ss-composer"):
                        question = gr.Textbox(
                            label="Bericht",
                            placeholder="Typ je bericht…",
                            lines=3,
                        )
                        send_button = gr.Button("Versturen", variant="primary")

                    with gr.Accordion("Extra", open=False):
                        compare_checkbox = gr.Checkbox(
                            label="Vergelijk dit antwoord zonder Shadowseed",
                            value=False,
                        )
                        comparison_note = gr.Markdown(
                            "Zet de vergelijking aan vóór het versturen wanneer je wilt controleren "
                            "of Shadowseed aantoonbaar invloed had."
                        )
                        with gr.Row():
                            ssl_on = gr.Markdown(label="Met Shadowseed")
                            ssl_off = gr.Markdown(label="Zonder Shadowseed")
                        with gr.Accordion("Technische gegevens", open=False):
                            last_turn_json = gr.JSON(label="Laatste beurt · technisch")
                            session_json = gr.JSON(label="Gesprekstoestand · technisch")

            authority_profile.change(
                lambda profile_id: _authority_explainer(profile_id),
                inputs=[authority_profile],
                outputs=[authority_help],
            )
            backend.change(
                provider_changed,
                inputs=[backend, model_id],
                outputs=[model_id, model_note, embedding_backend],
            )
            refresh_models_button.click(
                refresh_models,
                inputs=[backend, model_id],
                outputs=[model_id, model_note],
            )
            refresh_sessions.click(
                refresh_session_dropdown,
                inputs=[session_select],
                outputs=[session_select],
            )
            new_chat.click(
                create_chat,
                inputs=[
                    title,
                    authority_profile,
                    backend,
                    model_id,
                    profile,
                    embedding_backend,
                    embedding_model,
                    hosted_confirm,
                ],
                outputs=[session_select, chat, chat_status, session_json, question],
            )
            session_select.change(
                load_chat,
                inputs=[session_select],
                outputs=[chat, chat_status, session_json],
            )
            send_button.click(
                send_message,
                inputs=[session_select, question, compare_checkbox, hosted_confirm],
                outputs=[
                    chat,
                    chat_status,
                    last_turn_json,
                    question,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                ],
            )
            question.submit(
                send_message,
                inputs=[session_select, question, compare_checkbox, hosted_confirm],
                outputs=[
                    chat,
                    chat_status,
                    last_turn_json,
                    question,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                ],
            )

        with gr.Tab("Bronnen"):
            gr.Markdown("## Voeg materiaal toe aan hetzelfde geheugen")
            gr.Markdown(
                "Plak tekst of voeg bestanden toe. Shadowseed verwerkt ze op de achtergrond zonder "
                "ieder tekstdeel in een nep-chatbericht te veranderen."
            )
            with gr.Row():
                with gr.Column(scale=2):
                    source_session = gr.Dropdown(
                        choices=initial_sessions,
                        value=initial_sessions[0][1] if initial_sessions else None,
                        label="Gesprek",
                    )
                    source_refresh = gr.Button("Gesprekken vernieuwen", variant="secondary")
                    source_paste = gr.Textbox(
                        label="Tekst plakken",
                        placeholder="Artikel, notities, transcript, rapport…",
                        lines=10,
                    )
                    source_files = gr.File(
                        label="Bestanden kiezen",
                        file_count="multiple",
                        type="filepath",
                        file_types=[".txt", ".md", ".markdown", ".json", ".csv"],
                    )
                    source_confirm = gr.Checkbox(
                        label="Ik begrijp dat broninhoud bij een online model naar de provider kan worden gestuurd",
                        value=False,
                    )
                    source_button = gr.Button("Toevoegen aan geheugen", variant="primary")
                with gr.Column(scale=1):
                    source_result = gr.Markdown(_source_summary(None), elem_id="ss-source-result")
                    gr.Markdown(
                        "**Achter de schermen:** lezen → opdelen → mogelijke invalshoeken vinden → "
                        "herhaling herkennen → autoriteitsregels toepassen → geheugen bijwerken.",
                        elem_classes=["ss-card"],
                    )
                    source_seed_preview = gr.Dropdown(
                        choices=[],
                        label="Geheugenpunten na verwerking",
                        interactive=False,
                    )
                    source_state = gr.JSON(label="Technische gesprekstoestand", visible=False)

            source_refresh.click(
                refresh_session_dropdown,
                inputs=[source_session],
                outputs=[source_session],
            )
            source_button.click(
                ingest_sources,
                inputs=[source_session, source_paste, source_files, source_confirm],
                outputs=[source_result, source_seed_preview, source_state, source_paste],
            )

        with gr.Tab("Geheugen"):
            gr.Markdown("## Wat heeft Shadowseed onthouden?")
            gr.Markdown(
                "Hier zie je mogelijke ontbrekende invalshoeken in gewone taal. "
                "Een geheugenpunt is geen feit en krijgt niet automatisch invloed."
            )
            with gr.Row():
                memory_session = gr.Dropdown(
                    choices=initial_sessions,
                    label="Gesprek",
                )
                memory_refresh = gr.Button("Gesprekken vernieuwen", variant="secondary")
            memory_overview = gr.Markdown(_memory_overview(None), elem_classes=["ss-card"])
            with gr.Row():
                with gr.Column(scale=1):
                    seed_select = gr.Dropdown(choices=[], label="Geheugenpunt")
                    inspect_button = gr.Button("Bekijken", variant="primary")
                    with gr.Accordion("Handmatig ingrijpen", open=False):
                        gr.Markdown(
                            "Normaal hoef je hier niets te doen. Gebruik dit alleen als je bewust "
                            "een geheugenpunt wilt tegenspreken of onderbouwen."
                        )
                        falsify_button = gr.Button("Dit klopt niet / blokkeren", variant="stop")
                        falsify_result = gr.JSON(label="Resultaat")
                with gr.Column(scale=2):
                    seed_story = gr.Markdown(_seed_story(None), elem_id="ss-memory-story")
                    with gr.Accordion("Technische audit", open=False):
                        seed_json = gr.JSON(label="Ruwe toestand")
                        seed_timeline = gr.JSON(label="Gebeurtenissen")

            with gr.Accordion("Onafhankelijke onderbouwing toevoegen", open=False):
                evidence_source = gr.Textbox(
                    label="Bronverwijzing",
                    placeholder="Bijvoorbeeld URL, document-ID of reviewer:naam",
                )
                evidence_note = gr.Textbox(label="Korte toelichting", lines=2)
                evidence_attest = gr.Checkbox(
                    label="Ik heb deze onderbouwing buiten de modeluitvoer gecontroleerd",
                    value=False,
                )
                evidence_button = gr.Button("Onderbouwing toevoegen")
                evidence_result = gr.JSON(label="Resultaat")

            memory_refresh.click(
                refresh_session_dropdown,
                inputs=[memory_session],
                outputs=[memory_session],
            )
            memory_session.change(
                memory_session_changed,
                inputs=[memory_session],
                outputs=[seed_select, memory_overview],
            )
            inspect_button.click(
                inspect_seed,
                inputs=[memory_session, seed_select],
                outputs=[seed_story, seed_json, seed_timeline],
            )
            seed_select.change(
                inspect_seed,
                inputs=[memory_session, seed_select],
                outputs=[seed_story, seed_json, seed_timeline],
            )
            falsify_button.click(
                falsify_seed,
                inputs=[memory_session, seed_select],
                outputs=[falsify_result, seed_story, seed_json, seed_timeline],
            )
            evidence_button.click(
                submit_verified_evidence,
                inputs=[
                    memory_session,
                    seed_select,
                    evidence_source,
                    evidence_note,
                    evidence_attest,
                ],
                outputs=[
                    evidence_result,
                    seed_story,
                    seed_json,
                    seed_timeline,
                    evidence_source,
                    evidence_attest,
                ],
            )

        with gr.Tab("Controleren"):
            gr.Markdown("## Heeft Shadowseed dit antwoord echt beïnvloed?")
            gr.Markdown(
                "Twee verschillende antwoorden bewijzen niets. Shadowseed kan alleen als oorzaak "
                "worden aangewezen wanneer een geautoriseerd geheugenpunt daadwerkelijk is gebruikt."
            )
            with gr.Row():
                verify_session = gr.Dropdown(choices=initial_sessions, label="Gesprek")
                verify_refresh = gr.Button("Gesprekken vernieuwen", variant="secondary")
                verify_turn_index = gr.Number(value=0, precision=0, label="Berichtnummer (vanaf 0)")
            verify_button = gr.Button("Controle uitvoeren", variant="primary")
            verify_summary = gr.Markdown(_verify_summary(None), elem_id="ss-verify-result")
            with gr.Accordion("Technisch bewijs", open=False):
                verify_json = gr.JSON(label="Opgeslagen vergelijkingsrecord")

            verify_refresh.click(
                refresh_session_dropdown,
                inputs=[verify_session],
                outputs=[verify_session],
            )
            verify_button.click(
                verify_turn,
                inputs=[verify_session, verify_turn_index],
                outputs=[verify_summary, verify_json],
            )

        with gr.Tab("Uitleg"):
            gr.Markdown("# Wat is Shadowseed?")
            gr.Markdown(
                "Shadowseed is **geen nieuw taalmodel en geen fine-tuning**. Het is een aparte, "
                "zichtbare geheugen- en beslislaag rond een taalmodel. Die laag probeert te onthouden "
                "welke nuttige invalshoeken mogelijk ontbraken en beslist zorgvuldig of zo'n punt "
                "later nog een keer mag meedoen."
            )
            gr.Markdown(
                "**Chat → opmerken → geheugenpunt → herhaling/onderbouwing → Validation Gate → "
                "mag meedenken → relevantiecheck → eventueel invloed**",
                elem_id="ss-about-flow",
            )

            with gr.Accordion("1 · Wat gebeurt er tijdens een gewone chat?", open=True):
                gr.Markdown(
                    "Jij typt een bericht en het gekozen taalmodel geeft antwoord. Tegelijk bekijkt "
                    "Shadowseed het gesprek op de achtergrond. Mogelijke ontbrekende perspectieven "
                    "worden als kleine geheugenpunten opgeslagen. Dat verandert het huidige antwoord "
                    "niet automatisch. Eerst moet zo'n punt een geschiedenis opbouwen."
                )
            with gr.Accordion("2 · Wat is een geheugenpunt (shadow seed)?", open=False):
                gr.Markdown(
                    "Een shadow seed is een **mogelijke ontbrekende invalshoek**. Geen feit, geen opdracht "
                    "en geen geheime prompt. Shadowseed bewaart onder andere waar het punt vandaan kwam, "
                    "hoe vaak iets vergelijkbaars terugkwam, welke onderbouwing of tegenspraak bestaat "
                    "en of het ooit echt een antwoord heeft beïnvloed."
                )
            with gr.Accordion("3 · Wanneer mag zo'n punt meedenken?", open=False):
                gr.Markdown(
                    "Autoriteit en relevantie zijn twee verschillende dingen. Een geheugenpunt moet eerst "
                    "volgens de gekozen werkwijze voldoende autoriteit hebben. Daarna moet het bij een "
                    "nieuwe vraag ook nog relevant zijn. Pas dan kan het als begrensde extra context aan "
                    "het taalmodel worden aangeboden."
                )
            with gr.Accordion("4 · Wat is de Validation Gate?", open=False):
                gr.Markdown(
                    "De Validation Gate is de beslisgrens tussen **iets opmerken** en **iets invloed laten "
                    "krijgen**. Daar worden signalen zoals herhaling, onafhankelijke onderbouwing en "
                    "tegenspraak volgens een vaste policy beoordeeld. De beslissing wordt opgeslagen in "
                    "de audittrail; automatisering mag de beslissing sneller maken, maar niet onzichtbaar."
                )
            with gr.Accordion("5 · Wat doet Shadowseed automatisch?", open=False):
                gr.Markdown(
                    "In de normale interface worden zoveel mogelijk technische keuzes automatisch gedaan: "
                    "een lokaal model wordt gezocht, een passend embeddingtype wordt gekozen, tekst wordt "
                    "opgedeeld, kandidaten worden gededupliceerd en geclusterd, herhaling wordt bijgehouden "
                    "en alleen relevante geautoriseerde punten worden aangeboden. Welke autoriteitsstappen "
                    "automatisch mogen verlopen hangt af van **Veilig, Meedenkend, Zelfstandig of Onderzoek**."
                )
            with gr.Accordion("6 · Wat gebeurt er met uploads?", open=False):
                gr.Markdown(
                    "Bronnen volgen een apart pad: **lezen → opdelen → kandidaten vinden → herhaling "
                    "herkennen → Gate → geheugen**. Een document wordt dus niet automatisch een "
                    "waarheidsbron. De herkomst blijft gekoppeld aan de waarneming."
                )
            with gr.Accordion("7 · Is dit hetzelfde als RAG of fine-tuning?", open=False):
                gr.Markdown(
                    "**Fine-tuning** verandert modelgewichten; Shadowseed niet. **RAG** zoekt meestal "
                    "informatie naar aanleiding van de huidige vraag. Shadowseed bouwt juist door de tijd "
                    "heen een geschiedenis op van mogelijke ontbrekende perspectieven. De technieken kunnen "
                    "naast elkaar bestaan."
                )
            with gr.Accordion("8 · Wat kan Shadowseed níet bewijzen?", open=False):
                gr.Markdown(
                    "Een geheugenpunt is niet automatisch waar. Meer tekst betekent niet automatisch beter "
                    "geheugen. Twee verschillende antwoorden bewijzen geen Shadowseed-effect. En een "
                    "gepromoveerd punt hoeft niet gebruikt te worden. Daarom blijven herkomst, Gate-besluiten, "
                    "tegenspraken en daadwerkelijke influence-events inspecteerbaar."
                )
            with gr.Accordion("9 · Technische woorden vertaald", open=False):
                gr.Markdown(
                    "**Shadow seed** — mogelijk ontbrekende invalshoek.  \\n"
                    "**Shadow memory** — verzameling geheugenpunten met hun geschiedenis.  \\n"
                    "**Trace** — afnemende maat voor hoe levend een punt nog is.  \\n"
                    "**Validation Gate** — beslisgrens voor autoriteit.  \\n"
                    "**Promoted** — mag later meedenken als het relevant is.  \\n"
                    "**Surfacing** — een toegestaan punt wordt voor een nieuwe vraag beschikbaar gemaakt.  \\n"
                    "**Point of use** — laatste controle vlak voordat een punt invloed kan hebben."
                )

        with gr.Tab("Meer"):
            gr.Markdown("## Feedback, export en onderzoek")
            gr.Markdown(
                "Deze onderdelen zijn nuttig voor testers en onderzoekers, maar niet nodig om gewoon te chatten."
            )

            with gr.Accordion("Feedback en export", open=True):
                feedback_session = gr.Dropdown(choices=initial_sessions, label="Gesprek")
                feedback_refresh = gr.Button("Gesprekken vernieuwen", variant="secondary")
                turn_index = gr.Number(value=0, precision=0, label="Berichtnummer")
                overall = gr.Dropdown(
                    choices=[
                        ("Beter", "better"),
                        ("Neutraal", "neutral"),
                        ("Slechter", "worse"),
                    ],
                    value="neutral",
                    label="Algemene indruk",
                )
                seed_effect = gr.Dropdown(
                    choices=[
                        ("Hielp", "helpful"),
                        ("Werkte tegen", "harmful"),
                        ("Geen zichtbaar effect", "no_visible_effect"),
                        ("Onduidelijk", "unclear"),
                    ],
                    value="no_visible_effect",
                    label="Zichtbaar Shadowseed-effect",
                )
                feedback_note = gr.Textbox(label="Toelichting (optioneel)", lines=3)
                feedback_button = gr.Button("Feedback opslaan")
                feedback_result = gr.JSON(label="Opgeslagen feedback")

                gr.Markdown("### Exporteren")
                report_destination = gr.Textbox(
                    value="shadowseed-volledig-rapport.zip",
                    label="Volledig rapport",
                )
                support_destination = gr.Textbox(
                    value="shadowseed-support.zip",
                    label="Privacy-beperkte supportbundel",
                )
                with gr.Row():
                    export_report_button = gr.Button("Volledig rapport maken")
                    export_support_button = gr.Button("Supportbundel maken")
                export_result = gr.Textbox(label="Resultaat")

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

            with gr.Accordion("Onderzoek · scenario uitvoeren", open=False):
                gr.Markdown(
                    "De normale chat gebruikt live SSL. Deze scenariofunctie bestaat voor reproduceerbare "
                    "onderzoekstests en staat daarom bewust buiten de gewone chat."
                )
                scenario_json = gr.Code(
                    language="json",
                    label="Scenario JSON",
                    value=json.dumps(
                        {
                            "title": "Onderzoeksscenario",
                            "questions": ["Eerste vraag", "Tweede vraag"],
                            "profile_id": "balanced",
                            "backend": "fixture",
                            "runtime_mode": "evaluation",
                            "embedding_backend": "lexical",
                        },
                        indent=2,
                    ),
                )
                scenario_confirm = gr.Checkbox(
                    label="Ik begrijp dat een online scenario inhoud naar de provider kan sturen",
                    value=False,
                )
                scenario_button = gr.Button("Scenario uitvoeren")
                scenario_result = gr.JSON(label="Resultaat")
                scenario_button.click(
                    run_scenario,
                    inputs=[scenario_json, scenario_confirm],
                    outputs=[scenario_result],
                )

    return app
