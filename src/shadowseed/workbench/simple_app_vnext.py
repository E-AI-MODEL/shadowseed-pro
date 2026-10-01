"""Next-generation Workbench surface for Shadow Seed Learning.

This module intentionally stays thin. It reuses the existing WorkbenchController
and canonical SSL runtime, but presents one active conversation across Chat,
Shadow and Sources. Research mechanisms remain outside the normal path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from shadowseed.application.error_safety import sanitized_exception_line
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.feature_help import render_feature_help


_CSS = """
:root {
  --ss-blue: #1488e8;
  --ss-blue-soft: #eaf5ff;
  --ss-ink: #111827;
  --ss-muted: #667085;
  --ss-border: #dce5ee;
  --ss-panel: #ffffff;
  --ss-canvas: #f5f8fb;
  --ss-green: #179c7d;
  --ss-red: #ef5b47;
}
body { background: var(--ss-canvas) !important; }
.gradio-container {
  max-width: 1540px !important;
  margin: 0 auto !important;
  padding: 1.1rem !important;
  background: transparent !important;
}
#ss-shell {
  border: 1px solid var(--ss-border);
  border-radius: 18px;
  overflow: hidden;
  background: var(--ss-panel);
  box-shadow: 0 20px 60px rgba(38, 74, 103, .13);
}
#ss-topbar {
  padding: .6rem 1rem;
  border-bottom: 1px solid var(--ss-border);
  align-items: center;
  background: rgba(255,255,255,.98);
}
#ss-brand h2 { margin: 0 !important; letter-spacing: .02em; }
#ss-model-badge { text-align: right; color: var(--ss-muted); }
#ss-left {
  min-width: 230px;
  max-width: 270px;
  padding: 1rem .8rem;
  border-right: 1px solid var(--ss-border);
  background: #fbfdff;
}
#ss-center {
  padding: 1rem 1rem .8rem;
  min-width: 0;
}
#ss-right {
  min-width: 240px;
  max-width: 280px;
  padding: 1rem .8rem;
  border-left: 1px solid var(--ss-border);
  background: #fbfdff;
}
#ss-conversation-title h2 { margin: 0 0 .4rem !important; }
#ss-context-banner {
  border: 1px solid #d8eaf9;
  background: #f4faff;
  border-radius: 12px;
  padding: .55rem .75rem;
  margin: .35rem 0 .7rem;
}
#ss-composer {
  border-top: 1px solid var(--ss-border);
  padding-top: .7rem;
  margin-top: .35rem;
}
#ss-shadow-metrics {
  border-bottom: 1px solid var(--ss-border);
  padding-bottom: .75rem;
  margin-bottom: .75rem;
}
#ss-shadow-metrics p { margin: .18rem 0 !important; }
#ss-recent {
  border-top: 1px solid var(--ss-border);
  padding-top: .7rem;
  margin-top: .7rem;
}
.ss-primary button {
  background: var(--ss-blue) !important;
  border-color: var(--ss-blue) !important;
  color: white !important;
}
.ss-info-button button {
  min-width: 38px !important;
  width: 38px !important;
  padding-left: 0 !important;
  padding-right: 0 !important;
  border-radius: 999px !important;
  font-weight: 800 !important;
}
.ss-quiet button {
  background: transparent !important;
  border-color: var(--ss-border) !important;
}
.ss-drawer {
  position: fixed !important;
  z-index: 1000 !important;
  top: 72px !important;
  right: 28px !important;
  width: min(460px, calc(100vw - 40px)) !important;
  max-height: calc(100vh - 100px) !important;
  overflow-y: auto !important;
  padding: 1rem !important;
  border: 1px solid var(--ss-border) !important;
  border-radius: 18px !important;
  background: rgba(255,255,255,.995) !important;
  box-shadow: 0 24px 70px rgba(31, 65, 92, .24) !important;
}
#ss-menu-panel {
  width: 250px !important;
  top: 66px !important;
  right: 42px !important;
}
#ss-help-panel { width: min(520px, calc(100vw - 40px)) !important; }
.ss-drawer-title h2, .ss-drawer-title h3 { margin: 0 !important; }
.ss-section-label {
  font-size: .78rem;
  font-weight: 800;
  letter-spacing: .06em;
  color: #344054;
  text-transform: uppercase;
}
.ss-muted { color: var(--ss-muted); font-size: .9rem; }
.ss-status-pill {
  display: inline-block;
  border-radius: 999px;
  padding: .16rem .5rem;
  font-size: .72rem;
  font-weight: 800;
  background: #dff7ef;
  color: #16785f;
}
#ss-seed-story {
  border: 1px solid var(--ss-border);
  border-radius: 14px;
  padding: .8rem;
  background: #fcfdff;
}
#ss-technical-json { max-height: 420px; overflow-y: auto; }
@media (max-width: 1100px) {
  #ss-right { display: none !important; }
  #ss-left { min-width: 205px; }
}
@media (max-width: 780px) {
  .gradio-container { padding: .4rem !important; }
  #ss-left { display: none !important; }
  #ss-center { padding: .7rem; }
  .ss-drawer { top: 12px !important; right: 12px !important; width: calc(100vw - 24px) !important; max-height: calc(100vh - 24px) !important; }
}
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


def _ui_error(exc: BaseException) -> str:
    return f"**Fout:** {sanitized_exception_line(exc)}"


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



def _compact_session_choices(summaries: list[dict[str, Any]]) -> list[tuple[str, str]]:
    return [
        (str(item.get("title") or "Zonder titel"), str(item["session_id"]))
        for item in summaries
    ]


def _session_title(summaries: list[dict[str, Any]], session_id: str | None) -> str:
    for item in summaries:
        if str(item.get("session_id")) == str(session_id):
            return str(item.get("title") or "Gesprek")
    return "Nieuw gesprek"


def _model_badge(view: dict[str, Any] | None) -> str:
    if not view:
        return "Geen actief model"
    backend = str(view.get("backend") or "onbekend")
    model = str(view.get("model_id") or backend)
    location = "Online" if backend == "openai" else ("Demo" if backend == "fixture" else "Lokaal")
    return f"**{location} · {model}**"


def _context_banner(view: dict[str, Any] | None) -> str:
    if not view:
        return "Nog geen actief gesprek."
    reports = list(view.get("turn_reports", []) or [])
    if not reports:
        return "Shadowseed heeft nog geen geheugenpunt aan een antwoord aangeboden."
    surfaced = list(reports[-1].get("surfaced_seed_ids", []) or [])
    if surfaced:
        return f"📄 **{len(surfaced)} geheugenpunt(en) als context aangeboden**"
    return "📄 **Geen geheugenpunt als context aangeboden in de laatste beurt**"


def _shadow_rail(view: dict[str, Any] | None) -> str:
    if not view:
        return "### SHADOW\nGeen actief gesprek."
    seeds = list(view.get("seeds", []) or [])
    authorized = sum(bool(seed.get("current_gate_authorized", False)) for seed in seeds)
    blocked = sum(bool(seed.get("blocking", False)) for seed in seeds)
    reports = list(view.get("turn_reports", []) or [])
    offered = {
        str(seed_id)
        for report in reports
        for seed_id in (report.get("surfaced_seed_ids", []) or [])
    }
    return (
        "### SHADOW\n"
        f"🔵 **{len(seeds)}**  onthouden  \n"
        f"🟢 **{authorized}**  toegestaan  \n"
        f"⚪ **{len(offered)}**  aangeboden  \n"
        f"🔴 **{blocked}**  geblokkeerd"
    )


def _recent_seed_choices(view: dict[str, Any] | None) -> list[tuple[str, str]]:
    if not view:
        return []
    choices: list[tuple[str, str]] = []
    for seed in reversed(list(view.get("seeds", []) or [])):
        seed_id = str(seed.get("id", ""))
        text = str(seed.get("text", "")).replace("\n", " ").strip()
        if not seed_id:
            continue
        if bool(seed.get("blocking", False)):
            state = "Geblokkeerd"
        elif bool(seed.get("current_gate_authorized", False)):
            state = "Toegestaan"
        else:
            state = "Onthouden"
        choices.append((f"{state} · {text[:52]}", seed_id))
        if len(choices) == 3:
            break
    return choices


def _seed_lifecycle(seed: dict[str, Any] | None) -> str:
    if not seed:
        return "Selecteer een geheugenpunt."
    occurrence = int(seed.get("occurrence_count", 0))
    evidence = int(seed.get("evidence_count", 0))
    authorized = bool(seed.get("current_gate_authorized", False))
    blocked = bool(seed.get("blocking", False))
    surfaced = seed.get("last_surfaced_turn") is not None
    stages = [
        ("✓", "Opgemerkt", True),
        ("✓" if occurrence > 1 else "○", "Opnieuw gezien", occurrence > 1),
        ("✓" if evidence > 0 else "○", "Ondersteund", evidence > 0),
        ("!" if blocked else ("✓" if authorized else "○"), "Toegestaan", authorized and not blocked),
        ("✓" if surfaced else "○", "Aangeboden", surfaced),
    ]
    line = "  →  ".join(
        f"**{icon} {label}**" if active else f"{icon} {label}"
        for icon, label, active in stages
    )
    return line


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

    def show_help(
        feature_id: str,
        session_id: str | None,
        compare_enabled: bool,
        provider: str | None,
        hosted_confirmed: bool,
        seed_id: str | None,
    ):
        view = None
        seed = None
        if session_id:
            try:
                view = ctl.session_view(session_id)
                if seed_id:
                    seed = ctl.seed_view(session_id, seed_id)
            except Exception:
                view = None
                seed = None
        if feature_id in {"new_chat", "model", "external_consent"}:
            effective_provider = provider
        else:
            effective_provider = (
                str(view.get("backend"))
                if view and view.get("backend")
                else provider
            )
        return (
            feature_id,
            render_feature_help(
                feature_id,
                view=view,
                compare_enabled=bool(compare_enabled),
                provider=effective_provider,
                hosted_confirmed=bool(hosted_confirmed),
                seed=seed,
            ),
        )

    def refresh_help(
        feature_id: str,
        session_id: str | None,
        compare_enabled: bool,
        provider: str | None,
        hosted_confirmed: bool,
        seed_id: str | None,
    ):
        return show_help(
            feature_id,
            session_id,
            compare_enabled,
            provider,
            hosted_confirmed,
            seed_id,
        )[1]

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
                return (
                    gr.update(choices=[], value=None),
                    f"Ollama-modellen ophalen lukte niet. {_ui_error(exc)}",
                )
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
        try:
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
        except Exception as exc:
            error = _ui_error(exc)
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                error,
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                "",
                "",
                error,
                gr.update(),
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

        try:
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
        except Exception as exc:
            error = _ui_error(exc)
            return (
                gr.update(),
                error,
                gr.update(),
                gr.update(),
                gr.update(),
                question,
                "",
                "",
                error,
            )

    def inspect_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return _seed_story(None), None
        try:
            seed = ctl.seed_view(session_id, seed_id)
            return _seed_story(seed), seed
        except Exception as exc:
            error = _ui_error(exc)
            return error, {"error": sanitized_exception_line(exc)}

    def falsify(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return "Kies eerst een geheugenpunt.", gr.update(), gr.update(), gr.update(), gr.update()
        try:
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
        except Exception as exc:
            return _ui_error(exc), gr.update(), gr.update(), gr.update(), gr.update()

    def _submit_verified_evidence_action(
        session_id: str | None,
        seed_id: str | None,
        source_ref: str,
        note: str,
        attested: bool,
    ):
        if not session_id or not seed_id:
            return (
                "Kies eerst een geheugenpunt.",
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                note,
                attested,
            )
        try:
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
                "",
                False,
            )
        except Exception as exc:
            return (
                _ui_error(exc),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                note,
                attested,
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

        try:
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
        except Exception as exc:
            return (
                _source_summary({"error": sanitized_exception_line(exc)}),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                pasted,
            )

    def run_longitudinal_comparison(
        session_id: str | None,
        question: str,
        hosted_confirmed: bool,
    ):
        if not session_id:
            return (
                "**Niet uitgevoerd:** maak of kies eerst een gesprek.",
                "",
                "",
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                question,
            )
        if not str(question or "").strip():
            return (
                "**Niet uitgevoerd:** typ eerst een onderzoeksvraag.",
                "",
                "",
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                question,
            )

        try:
            result = ctl.send_turn(
                session_id,
                question,
                compare_without_ssl=True,
                comparison_mode="longitudinal",
                external_confirmed=bool(hosted_confirmed),
            )
            view = result["session"]
            comparison = result.get("comparison") or {}
            ssl_on, vanilla, _note = _comparison(comparison)
            replayed = int(comparison.get("control_replayed_turns", 0))
            history_before = int(comparison.get("control_history_turns_before", 0))
            research_note = (
                "### Longitudinale vergelijking uitgevoerd\n"
                "Dit is **geen same-turn A/B**. Het vanilla-pad heeft een eigen antwoordgeschiedenis. "
                f"Voor deze run zijn **{replayed}** eerdere userbeurt(en) opnieuw opgebouwd "
                f"uit **{history_before}** eerdere beurt(en)."
            )
            return (
                research_note,
                ssl_on,
                vanilla,
                ctl.chat_messages(view),
                _status(view),
                _shadow_summary(view),
                gr.update(choices=ctl.seed_choices(view), value=None),
                view,
                "",
            )
        except Exception as exc:
            return (
                _ui_error(exc),
                "",
                "",
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                question,
            )

    summaries = ctl.list_sessions()
    compact_sessions = _compact_session_choices(summaries)
    initial_title = _session_title(summaries, initial_id)
    recent_choices = _recent_seed_choices(initial_view)

    def refresh_shell(session_id: str | None):
        current_summaries = ctl.list_sessions()
        if not session_id:
            return (
                [],
                "Nieuw gesprek",
                "Geen actief model",
                _context_banner(None),
                _shadow_rail(None),
                gr.update(choices=[], value=None),
                gr.update(choices=[], value=None),
                None,
            )
        view = ctl.session_view(session_id)
        seeds = ctl.seed_choices(view)
        recent = _recent_seed_choices(view)
        return (
            ctl.chat_messages(view),
            f"## {_session_title(current_summaries, session_id)}",
            _model_badge(view),
            _context_banner(view),
            _shadow_rail(view),
            gr.update(choices=seeds, value=None),
            gr.update(choices=recent, value=(recent[0][1] if recent else None)),
            view,
        )

    def select_shell_session(session_id: str | None):
        shell = refresh_shell(session_id)
        return (
            session_id,
            *shell,
            _seed_story(None),
            _seed_lifecycle(None),
            None,
            "",
            "",
            "Zet **Vergelijk deze beurt zonder SSL** aan voor een same-turn control.",
        )

    def create_chat_shell(
        title: str,
        provider_value: str,
        model_value: str | None,
        hosted_confirmed: bool,
    ):
        result = create_chat(title, provider_value, model_value, hosted_confirmed)
        if not isinstance(result[0], str):
            error = result[3] if len(result) > 3 else "Chat starten is niet gelukt."
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                error,
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                _seed_lifecycle(None),
                gr.update(),
                "",
                "",
                error,
                gr.update(visible=True),
            )
        session_id = result[0]
        current_summaries = ctl.list_sessions()
        compact = _compact_session_choices(current_summaries)
        shell = refresh_shell(session_id)
        return (
            session_id,
            gr.update(choices=compact, value=session_id),
            *shell,
            _seed_story(None),
            _seed_lifecycle(None),
            None,
            "",
            "",
            "Zet **Vergelijk deze beurt zonder SSL** aan voor een same-turn control.",
            gr.update(visible=False),
        )

    def inspect_seed_shell(session_id: str | None, seed_id: str | None):
        story, seed = inspect_seed(session_id, seed_id)
        return story, _seed_lifecycle(seed if isinstance(seed, dict) else None), seed

    def send_shell(
        session_id: str | None,
        question_value: str,
        compare_enabled: bool,
        hosted_confirmed: bool,
    ):
        result = send(session_id, question_value, compare_enabled, hosted_confirmed)
        if session_id:
            try:
                view = ctl.session_view(session_id)
                current_summaries = ctl.list_sessions()
                return (
                    result[0],
                    f"## {_session_title(current_summaries, session_id)}",
                    _model_badge(view),
                    (result[1] if isinstance(result[1], str) and result[1].startswith("**Fout:**") else _context_banner(view)),
                    _shadow_rail(view),
                    gr.update(choices=ctl.seed_choices(view), value=None),
                    gr.update(
                        choices=_recent_seed_choices(view),
                        value=(_recent_seed_choices(view)[0][1] if _recent_seed_choices(view) else None),
                    ),
                    view,
                    result[5],
                    result[6],
                    result[7],
                    result[8],
                )
            except Exception:
                pass
        return (
            result[0],
            gr.update(),
            gr.update(),
            result[1],
            gr.update(),
            result[3],
            gr.update(),
            result[4],
            result[5],
            result[6],
            result[7],
            result[8],
        )

    def ingest_shell(
        session_id: str | None,
        pasted: str,
        files: list[str] | str | None,
        hosted_confirmed: bool,
    ):
        result = ingest(session_id, pasted, files, hosted_confirmed)
        if not session_id:
            return (*result, gr.update(), gr.update())
        try:
            view = ctl.session_view(session_id)
            failed = isinstance(result[0], str) and result[0].startswith("**Fout:**")
            return (
                result[0],
                _shadow_rail(view),
                _context_banner(view),
                gr.update(choices=ctl.seed_choices(view), value=None),
                view,
                result[5],
                gr.update(
                    choices=_recent_seed_choices(view),
                    value=(_recent_seed_choices(view)[0][1] if _recent_seed_choices(view) else None),
                ),
                gr.update(visible=failed),
            )
        except Exception:
            return (*result, gr.update(), gr.update())

    def mutation_shell(
        session_id: str | None,
        seed_id: str | None,
        *,
        action: str,
        source_ref: str = "",
        note: str = "",
        attested: bool = False,
    ):
        if action == "contradict":
            result = falsify(session_id, seed_id)
            extra_note, extra_attest = note, attested
        else:
            evidence_result = _submit_verified_evidence_action(
                session_id,
                seed_id,
                source_ref,
                note,
                attested,
            )
            result = evidence_result[:5]
            extra_note = evidence_result[5]
            extra_attest = evidence_result[6]
        if not session_id:
            return (*result, _seed_lifecycle(None), gr.update(), extra_note, extra_attest)
        try:
            view = ctl.session_view(session_id)
            seed = ctl.seed_view(session_id, seed_id) if seed_id else None
            return (
                result[0],
                _shadow_rail(view),
                _context_banner(view),
                view,
                gr.update(choices=ctl.seed_choices(view), value=seed_id),
                _seed_lifecycle(seed),
                gr.update(
                    choices=_recent_seed_choices(view),
                    value=seed_id,
                ),
                extra_note,
                extra_attest,
            )
        except Exception:
            return (*result, _seed_lifecycle(None), gr.update(), extra_note, extra_attest)

    def contradict_shell(session_id: str | None, seed_id: str | None):
        return mutation_shell(session_id, seed_id, action="contradict")

    def submit_verified_evidence(
        session_id: str | None,
        seed_id: str | None,
        source_ref: str,
        note: str,
        attested: bool,
    ):
        return mutation_shell(
            session_id,
            seed_id,
            action="evidence",
            source_ref=source_ref,
            note=note,
            attested=attested,
        )

    def research_comparison_shell(
        session_id: str | None,
        question_value: str,
        hosted_confirmed: bool,
    ):
        result = run_longitudinal_comparison(
            session_id,
            question_value,
            hosted_confirmed,
        )
        if not session_id:
            return result
        try:
            view = ctl.session_view(session_id)
            return (
                result[0],
                result[1],
                result[2],
                ctl.chat_messages(view),
                _context_banner(view),
                _shadow_rail(view),
                gr.update(choices=ctl.seed_choices(view), value=None),
                view,
                result[8],
            )
        except Exception:
            return result

    with gr.Blocks(title="Shadowseed") as app:
        active_session = gr.State(initial_id)
        help_feature = gr.State("conversation")

        with gr.Group(elem_id="ss-shell"):
            with gr.Row(elem_id="ss-topbar"):
                brand = gr.Markdown("## SHADOWSEED", elem_id="ss-brand", scale=4)
                model_badge = gr.Markdown(_model_badge(initial_view), elem_id="ss-model-badge", scale=2)
                model_top_info = gr.Button("ⓘ", scale=0, min_width=40, elem_classes=["ss-info-button"])
                menu_button = gr.Button("☰  Menu", scale=0, min_width=100)

            with gr.Row(equal_height=True):
                with gr.Column(scale=2, min_width=220, elem_id="ss-left"):
                    with gr.Row():
                        gr.Markdown("### GESPREKKEN", scale=4)
                        conversation_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
                    new_chat_open = gr.Button("＋  Nieuwe chat", variant="primary", elem_classes=["ss-primary"])
                    gr.Markdown('<span class="ss-section-label">Vandaag</span>')
                    session_select = gr.Radio(
                        choices=compact_sessions,
                        value=initial_id,
                        label=None,
                        container=False,
                    )

                with gr.Column(scale=6, min_width=520, elem_id="ss-center"):
                    conversation_title = gr.Markdown(
                        f"## {initial_title}",
                        elem_id="ss-conversation-title",
                    )
                    chat = gr.Chatbot(value=initial_chat, label=None, height=500)
                    context_banner = gr.Markdown(_context_banner(initial_view), elem_id="ss-context-banner")
                    with gr.Column(elem_id="ss-composer"):
                        with gr.Row():
                            source_open = gr.Button("＋  Bron toevoegen", scale=1)
                            source_info_inline = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
                            question = gr.Textbox(
                                label=None,
                                placeholder="Stel je vraag...",
                                lines=2,
                                scale=5,
                                container=False,
                            )
                            send_button = gr.Button("Versturen", variant="primary", scale=1, elem_classes=["ss-primary"])
                            send_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
                        with gr.Row():
                            compare = gr.Checkbox(
                                label="Vergelijk deze beurt zonder SSL",
                                value=False,
                                scale=5,
                            )
                            compare_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
                    with gr.Accordion("Vergelijking", open=False):
                        comparison_note = gr.Markdown(
                            "Zet **Vergelijk deze beurt zonder SSL** aan voor een same-turn control."
                        )
                        with gr.Row():
                            ssl_answer = gr.Markdown(label="Met SSL")
                            no_ssl_answer = gr.Markdown(label="Zonder SSL")

                with gr.Column(scale=2, min_width=235, elem_id="ss-right"):
                    shadow_metrics = gr.Markdown(_shadow_rail(initial_view), elem_id="ss-shadow-metrics")
                    with gr.Row():
                        shadow_open = gr.Button("Bekijk Shadow", scale=4)
                        shadow_info_inline = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
                    gr.Markdown('<span class="ss-section-label">Recent opgemerkt</span>', elem_id="ss-recent")
                    recent_seed = gr.Radio(
                        choices=recent_choices,
                        value=(recent_choices[0][1] if recent_choices else None),
                        label=None,
                        container=False,
                    )
                    recent_open = gr.Button("Bekijk geheugenpunt", variant="secondary")

        with gr.Group(visible=False, elem_id="ss-panel-new-chat", elem_classes=["ss-drawer"]) as new_chat_panel:
            with gr.Row():
                gr.Markdown("## Nieuwe chat", elem_classes=["ss-drawer-title"], scale=5)
                new_chat_close = gr.Button("×", scale=0, min_width=40, elem_classes=["ss-info-button"])
            new_title = gr.Textbox(label="Naam", value="Nieuw gesprek")
            with gr.Row():
                provider = gr.Dropdown(
                    choices=[
                        ("Ollama · lokaal", "ollama"),
                        ("OpenAI · online", "openai"),
                        ("Hugging Face · lokaal", "hf-transformers"),
                        ("Offline demo", "fixture"),
                    ],
                    value=auto_backend,
                    label="Provider",
                    scale=5,
                )
                model_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            model_id = gr.Dropdown(
                choices=([auto_model] if auto_model else []),
                value=auto_model,
                allow_custom_value=True,
                label="Model",
            )
            model_note = gr.Markdown(auto_note, elem_classes=["ss-muted"])
            with gr.Row():
                rescan_models = gr.Button("↻  Lokale modellen opnieuw zoeken", scale=5)
                rescan_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            with gr.Row():
                hosted_confirm = gr.Checkbox(
                    label="Ik begrijp dat deze provider inhoud extern kan verwerken",
                    value=False,
                    scale=5,
                )
                consent_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            with gr.Row():
                create_button = gr.Button("Chat starten", variant="primary", scale=5, elem_classes=["ss-primary"])
                create_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])

        with gr.Group(visible=False, elem_id="ss-panel-source", elem_classes=["ss-drawer"]) as source_panel:
            with gr.Row():
                gr.Markdown("## Bron toevoegen", elem_classes=["ss-drawer-title"], scale=5)
                source_close = gr.Button("×", scale=0, min_width=40, elem_classes=["ss-info-button"])
            gr.Markdown(
                "Voeg een tekstbron toe aan **dit gesprek**. De inhoud is observatie-input voor "
                "Shadowseed en wordt niet automatisch waarheid of geverifieerd bewijs."
            )
            source_text = gr.Textbox(
                label=None,
                placeholder="Plak hier je tekst, aantekeningen of onderzoeksfragment...",
                lines=8,
            )
            source_files = gr.File(
                label="Bestand kiezen",
                file_count="multiple",
                type="filepath",
                file_types=[".txt", ".md", ".markdown", ".json", ".csv"],
            )
            with gr.Row():
                ingest_button = gr.Button("Toevoegen aan gesprek", variant="primary", scale=5, elem_classes=["ss-primary"])
                source_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            source_result = gr.Markdown(_source_summary(None))

        with gr.Group(visible=False, elem_id="ss-panel-shadow", elem_classes=["ss-drawer"]) as shadow_panel:
            with gr.Row():
                gr.Markdown("## SHADOW", elem_classes=["ss-drawer-title"], scale=5)
                shadow_close = gr.Button("×", scale=0, min_width=40, elem_classes=["ss-info-button"])
            gr.Markdown(
                "Onthouden, toegestaan, aangeboden en geblokkeerd zijn verschillende SSL-stappen."
            )
            seed_select = gr.Dropdown(
                choices=initial_seeds,
                value=None,
                label="Geheugenpunt",
            )
            seed_story = gr.Markdown(_seed_story(None), elem_id="ss-seed-story")
            lifecycle = gr.Markdown(_seed_lifecycle(None))
            with gr.Row():
                contradiction_button = gr.Button("Tegenspraak registreren", scale=4)
                contradiction_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            gr.Markdown("### Geverifieerde ondersteuning")
            evidence_source = gr.Textbox(label="Bronreferentie")
            evidence_note = gr.Textbox(label="Toelichting", lines=2)
            with gr.Row():
                evidence_attest = gr.Checkbox(
                    label="Ik heb deze ondersteuning onafhankelijk van modeloutput gecontroleerd",
                    value=False,
                    scale=5,
                )
                evidence_attest_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            with gr.Row():
                evidence_button = gr.Button(
                    "Geverifieerde ondersteuning toevoegen",
                    variant="primary",
                    scale=5,
                    elem_classes=["ss-primary"],
                )
                evidence_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            technical_open_from_seed = gr.Button("Technische audit", variant="secondary")

        with gr.Group(visible=False, elem_id="ss-menu-panel", elem_classes=["ss-drawer"]) as menu_panel:
            menu_close = gr.Button("× Sluiten", variant="secondary")
            about_button = gr.Button("ⓘ  Over Shadowseed")
            research_open = gr.Button("⚗  Onderzoek")
            audit_open = gr.Button("▣  Technische audit")
            model_menu_info = gr.Button("⚙  Model & provider")
            gr.Markdown("Versie **0.10**", elem_classes=["ss-muted"])

        with gr.Group(visible=False, elem_id="ss-panel-research", elem_classes=["ss-drawer"]) as research_panel:
            with gr.Row():
                gr.Markdown("## ONDERZOEK", elem_classes=["ss-drawer-title"], scale=5)
                research_close = gr.Button("×", scale=0, min_width=40, elem_classes=["ss-info-button"])
            gr.Markdown(
                "ℹ️ **Experimenten en analyses staan los van je normale chatgesprekken.**"
            )
            with gr.Accordion("Longitudinale vergelijking", open=True):
                longitudinal_info = gr.Button("ⓘ Uitleg")
                research_question = gr.Textbox(
                    label="Onderzoeksvraag",
                    placeholder="Typ de volgende vraag voor het longitudinale experiment...",
                    lines=2,
                )
                with gr.Row():
                    research_run = gr.Button("Voer longitudinale vergelijking uit", variant="secondary", scale=5)
                    research_run_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
                research_result = gr.Markdown("Nog geen longitudinale vergelijking uitgevoerd.")
                with gr.Row():
                    research_ssl_answer = gr.Markdown(label="Shadowseed-pad")
                    research_vanilla_answer = gr.Markdown(label="Onafhankelijk vanilla-pad")
            with gr.Accordion("Matching", open=False):
                semantic_info = gr.Button("ⓘ Leg semantisch matchen uit")
            with gr.Accordion("Self-reinforcement", open=False):
                self_reinforcement_info = gr.Button("ⓘ Leg self-reinforcement uit")
            with gr.Accordion("Validation Gate", open=False):
                gr.Markdown(
                    "De Gate bepaalt authority. In de gewone chat is dit geen losse schuifregelaar."
                )
                gate_info = gr.Button("ⓘ Leg de Validation Gate uit")

        with gr.Group(visible=False, elem_id="ss-panel-audit", elem_classes=["ss-drawer"]) as audit_panel:
            with gr.Row():
                gr.Markdown("## Technische audit", elem_classes=["ss-drawer-title"], scale=5)
                audit_close = gr.Button("×", scale=0, min_width=40, elem_classes=["ss-info-button"])
            audit_info = gr.Button("ⓘ Wat zie ik hier?")
            session_json = gr.JSON(value=initial_view, label="Gesprekstoestand", elem_id="ss-technical-json")
            seed_json = gr.JSON(label="Geheugenpunt")

        with gr.Group(visible=False, elem_id="ss-help-panel", elem_classes=["ss-drawer"]) as help_panel_group:
            with gr.Row():
                gr.Markdown("## Uitleg", elem_classes=["ss-drawer-title"], scale=5)
                help_close = gr.Button("×", scale=0, min_width=40, elem_classes=["ss-info-button"])
            help_panel = gr.Markdown(
                render_feature_help(
                    "conversation",
                    view=initial_view,
                    compare_enabled=False,
                    provider=(str(initial_view.get("backend")) if initial_view else auto_backend),
                    hosted_confirmed=False,
                )
            )

        def open_panel(panel):
            return gr.update(visible=True)

        def close_panel():
            return gr.update(visible=False)

        def bind_help(button, feature_id: str):
            button.click(
                lambda session_id, compare_enabled, provider_value, consent_value, seed_id, _feature=feature_id:
                    (
                        _feature,
                        render_feature_help(
                            _feature,
                            view=(ctl.session_view(session_id) if session_id else None),
                            compare_enabled=bool(compare_enabled),
                            provider=(
                                provider_value
                                if _feature in {"new_chat", "model", "external_consent"}
                                else (
                                    str(ctl.session_view(session_id).get("backend"))
                                    if session_id else provider_value
                                )
                            ),
                            hosted_confirmed=bool(consent_value),
                            seed=(ctl.seed_view(session_id, seed_id) if session_id and seed_id else None),
                        ),
                        gr.update(visible=True),
                    ),
                inputs=[active_session, compare, provider, hosted_confirm, seed_select],
                outputs=[help_feature, help_panel, help_panel_group],
            )

        for button, feature_id in (
            (conversation_info, "conversation"),
            (model_top_info, "model"),
            (model_info, "model"),
            (rescan_info, "model"),
            (consent_info, "external_consent"),
            (create_info, "new_chat"),
            (send_info, "send"),
            (compare_info, "compare"),
            (source_info_inline, "sources"),
            (source_info, "sources"),
            (shadow_info_inline, "shadow"),
            (contradiction_info, "contradiction"),
            (evidence_attest_info, "verified_support"),
            (evidence_info, "verified_support"),
            (about_button, "shadow"),
            (longitudinal_info, "longitudinal"),
            (research_run_info, "longitudinal"),
            (semantic_info, "semantic_matching"),
            (self_reinforcement_info, "self_reinforcement"),
            (gate_info, "research"),
            (audit_info, "technical_audit"),
            (model_menu_info, "model"),
        ):
            bind_help(button, feature_id)

        new_chat_open.click(lambda: gr.update(visible=True), outputs=[new_chat_panel])
        new_chat_close.click(close_panel, outputs=[new_chat_panel])
        source_open.click(lambda: gr.update(visible=True), outputs=[source_panel])
        source_close.click(close_panel, outputs=[source_panel])
        shadow_open.click(lambda: gr.update(visible=True), outputs=[shadow_panel])
        shadow_close.click(close_panel, outputs=[shadow_panel])
        menu_button.click(lambda: gr.update(visible=True), outputs=[menu_panel])
        menu_close.click(close_panel, outputs=[menu_panel])
        research_open.click(
            lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[research_panel, menu_panel],
        )
        research_close.click(close_panel, outputs=[research_panel])
        audit_open.click(
            lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[audit_panel, menu_panel],
        )
        technical_open_from_seed.click(
            lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[audit_panel, shadow_panel],
        )
        audit_close.click(close_panel, outputs=[audit_panel])
        help_close.click(close_panel, outputs=[help_panel_group])

        recent_open.click(
            lambda seed_id: (seed_id, gr.update(visible=True)),
            inputs=[recent_seed],
            outputs=[seed_select, shadow_panel],
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

        session_select.change(
            select_shell_session,
            inputs=[session_select],
            outputs=[
                active_session,
                chat,
                conversation_title,
                model_badge,
                context_banner,
                shadow_metrics,
                seed_select,
                recent_seed,
                session_json,
                seed_story,
                lifecycle,
                seed_json,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
            ],
        )

        create_button.click(
            create_chat_shell,
            inputs=[new_title, provider, model_id, hosted_confirm],
            outputs=[
                active_session,
                session_select,
                chat,
                conversation_title,
                model_badge,
                context_banner,
                shadow_metrics,
                seed_select,
                recent_seed,
                session_json,
                seed_story,
                lifecycle,
                seed_json,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
                new_chat_panel,
            ],
        )

        send_button.click(
            send_shell,
            inputs=[active_session, question, compare, hosted_confirm],
            outputs=[
                chat,
                conversation_title,
                model_badge,
                context_banner,
                shadow_metrics,
                seed_select,
                recent_seed,
                session_json,
                question,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
            ],
        )
        question.submit(
            send_shell,
            inputs=[active_session, question, compare, hosted_confirm],
            outputs=[
                chat,
                conversation_title,
                model_badge,
                context_banner,
                shadow_metrics,
                seed_select,
                recent_seed,
                session_json,
                question,
                ssl_answer,
                no_ssl_answer,
                comparison_note,
            ],
        )

        seed_select.change(
            inspect_seed_shell,
            inputs=[active_session, seed_select],
            outputs=[seed_story, lifecycle, seed_json],
        )

        contradiction_button.click(
            contradict_shell,
            inputs=[active_session, seed_select],
            outputs=[
                seed_story,
                shadow_metrics,
                context_banner,
                session_json,
                seed_select,
                lifecycle,
                recent_seed,
                evidence_note,
                evidence_attest,
            ],
        )

        evidence_button.click(
            submit_verified_evidence,
            inputs=[active_session, seed_select, evidence_source, evidence_note, evidence_attest],
            outputs=[
                seed_story,
                shadow_metrics,
                context_banner,
                session_json,
                seed_select,
                lifecycle,
                recent_seed,
                evidence_note,
                evidence_attest,
            ],
        )

        ingest_button.click(
            ingest_shell,
            inputs=[active_session, source_text, source_files, hosted_confirm],
            outputs=[
                source_result,
                shadow_metrics,
                context_banner,
                seed_select,
                session_json,
                source_text,
                recent_seed,
                source_panel,
            ],
        )

        research_run.click(
            research_comparison_shell,
            inputs=[active_session, research_question, hosted_confirm],
            outputs=[
                research_result,
                research_ssl_answer,
                research_vanilla_answer,
                chat,
                context_banner,
                shadow_metrics,
                seed_select,
                session_json,
                research_question,
            ],
        )

    return app
