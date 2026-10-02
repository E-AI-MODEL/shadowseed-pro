"""Next-generation Workbench surface for Shadow Seed Learning.

This module intentionally stays thin. It reuses the existing WorkbenchController
and canonical SSL runtime, but presents one active conversation across Chat,
Shadow and Sources. Research mechanisms remain outside the normal path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shadowseed.application.error_safety import sanitized_exception_line
from shadowseed.workbench.controller import WorkbenchController
from shadowseed.workbench.feature_help import render_feature_help
from shadowseed.workbench.updates import WorkbenchUpdateService


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


_PRESET_SETTINGS: dict[str, dict[str, Any]] = {
    "observeren": {
        "surface_threshold": 1.0,
        "surface_top_k": 0,
        "early_turn_margin": 0.20,
        "resurface_margin": 0.25,
        "authority_profile_id": "strict",
        "gate_policy_id": "evidence_backed",
        "min_occurrences_for_gate": 4,
        "min_evidence_for_gate": 3,
        "min_trace_for_gate": 0.5,
        "promotion_threshold": 0.6,
        "validation_increment": 0.2,
        "allow_same_turn_revision": False,
    },
    "gebalanceerd": {
        "surface_threshold": 0.30,
        "surface_top_k": 2,
        "early_turn_margin": 0.10,
        "resurface_margin": 0.15,
        "authority_profile_id": "strict",
        "gate_policy_id": "evidence_backed",
        "min_occurrences_for_gate": 3,
        "min_evidence_for_gate": 2,
        "min_trace_for_gate": 0.5,
        "promotion_threshold": 0.5,
        "validation_increment": 0.2,
        "allow_same_turn_revision": False,
    },
    "onderzoekend": {
        "surface_threshold": 0.20,
        "surface_top_k": 3,
        "early_turn_margin": 0.05,
        "resurface_margin": 0.10,
        "authority_profile_id": "autonomous",
        "gate_policy_id": "exploratory",
        "min_occurrences_for_gate": 2,
        "min_evidence_for_gate": 0,
        "min_trace_for_gate": 0.0,
        "promotion_threshold": 0.4,
        "validation_increment": 0.2,
        "allow_same_turn_revision": False,
    },
}

_PRESET_HELP = {
    "observeren": (
        "**Observeren** · Shadowseed mag detecteren en onthouden, maar levert niets aan het "
        "antwoord. Geschikt om eerst te zien wat het systeem opslaat zonder invloed op de chat."
    ),
    "gebalanceerd": (
        "**Gebalanceerd** · Normale onderzoeksstand. Alleen Gate-geautoriseerde en relevante "
        "seeds kunnen beperkt worden aangeboden. Zelfversterking staat uit."
    ),
    "onderzoekend": (
        "**Onderzoekend** · Lagere drempels en meer surfacing. Recurrence mag via de "
        "exploratory Gate authority opbouwen. Bedoeld voor experimenten, niet als bewijsstand."
    ),
    "custom": (
        "**Aangepast** · Een of meer waarden wijken af van een preset. De werkelijk opgeslagen "
        "waarden hieronder zijn leidend."
    ),
}


def _preset_help(preset: str | None) -> str:
    return _PRESET_HELP.get(str(preset or "custom"), _PRESET_HELP["custom"])


def _full_settings(view: dict[str, Any] | None) -> dict[str, Any]:
    if not view:
        return {}
    persisted = dict(view.get("persisted_config", {}))
    core = dict(view.get("core_config", {}))
    return {**persisted, **core}


def _settings_json(view: dict[str, Any] | None) -> str:
    return json.dumps(_full_settings(view), indent=2, sort_keys=True, ensure_ascii=False)


def _authority_gate_summary(view: dict[str, Any] | None) -> str:
    if not view:
        return (
            "**Authority & Gate** · het profiel bepaalt de standaardroute; "
            "een expliciete Gate-policy kan die standaard overschrijven."
        )
    profile = str(view.get("authority_profile_id") or "onbekend")
    default_gate = str(view.get("profile_default_gate_policy_id") or "onbekend")
    effective_gate = str(view.get("effective_gate_policy_id") or "onbekend")
    configured = view.get("configured_gate_policy_id")
    if bool(view.get("gate_policy_override_active", False)):
        relation = (
            f"Profiel `{profile}` heeft standaard Gate `{default_gate}`. "
            f"Expliciete override `{configured}` is actief, dus effectief `{effective_gate}`."
        )
    else:
        relation = (
            f"Profiel `{profile}` → standaard Gate `{default_gate}` → "
            f"effectief `{effective_gate}`."
        )
    return f"**Authority & Validation Gate · stateful**  \n{relation}"


def _statefulness_summary(view: dict[str, Any] | None) -> str:
    metadata = dict((view or {}).get("setting_metadata") or {})
    rebuild = sorted(
        key
        for key, item in metadata.items()
        if isinstance(item, dict) and item.get("apply_mode") == "rebuild_required"
    )
    if not rebuild:
        return (
            "**Instellingencontract** · structurele wijzigingen mogen bestaande "
            "semantic-memory-state niet stilzwijgend herinterpreteren."
        )
    return (
        "**Rebuild required na bestaande state:** "
        + ", ".join(f"`{key}`" for key in rebuild)
        + ". Deze grens kan niet met God mode worden omzeild."
    )


def _audit_summary(view: dict[str, Any] | None) -> str:
    if not view:
        return "### Live audit\nGeen actief gesprek."
    reports = list(view.get("turn_reports", []))
    last = reports[-1] if reports else {}
    seeds = list(view.get("seeds", []))
    authorized = sum(bool(item.get("current_gate_authorized")) for item in seeds)
    surfaced = list(last.get("surfaced_seed_ids", []))
    decisions = list(last.get("influence_decisions", []))
    return (
        "### Live audit\n"
        f"**Turn:** {int(view.get('turn', 0))}  \n"
        f"**Seeds:** {len(seeds)} · **nu geautoriseerd:** {authorized}  \n"
        f"**Gesurfaced laatste turn:** {len(surfaced)} · **invloedbesluiten:** {len(decisions)}  \n"
        f"**Authority:** `{view.get('authority_profile_id', 'onbekend')}` · "
        f"Gate `{view.get('effective_gate_policy_id', 'onbekend')}`  \n"
        f"**Recurrence:** `{view.get('recurrence_mode', 'onbekend')}` · "
        f"top-k **{int(view.get('surface_top_k', 0))}**  \n"
        f"**Behavior epoch:** `{view.get('behavior_config_epoch', 'onbekend')}`"
    )


def _preset_from_view(view: dict[str, Any] | None) -> str:
    if not view:
        return "gebalanceerd"
    current = _full_settings(view)
    for preset, settings in _PRESET_SETTINGS.items():
        if all(current.get(key) == value for key, value in settings.items()):
            return preset
    return "custom"


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


def _ollama_note(models: list[str], selected: str | None) -> str:
    from shadowseed.adapters.ollama_client import DEFAULT_OLLAMA_EMBEDDING_MODEL

    if not models:
        return "Geen lokaal Ollama-chatmodel gevonden."
    return (
        f"Lokaal chatmodel geselecteerd: `{selected or models[0]}`. "
        f"Semantisch matchen gebruikt lokaal `{DEFAULT_OLLAMA_EMBEDDING_MODEL}`. "
        f"Ontbreekt dat model, voer eenmalig `ollama pull {DEFAULT_OLLAMA_EMBEDDING_MODEL}` uit."
    )


def _recommended_setup(ctl: WorkbenchController) -> tuple[str, str | None, str]:
    try:
        models = ctl.discover_models("ollama")
    except Exception:
        models = []
    if models:
        return "ollama", models[0], _ollama_note(models, models[0])
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


def _orchestration_copy(payload: dict[str, Any] | None) -> tuple[str, str, str]:
    """Translate derived orchestration state into Dutch presentation copy only."""

    data = dict(payload or {})
    state = str(data.get("state") or "ssl_turn")
    reason_code = str(data.get("reason_code") or "")
    state_labels = {
        "ssl_turn": "Shadowseed is aan zet",
        "optional_review": "Shadowseed kan door; jij kunt meekijken",
        "human_turn": "Jij bent aan zet",
        "blocked": "Eerst een blokkade oplossen",
    }
    reason_labels = {
        "no_seed_action": "Er is nu geen geheugenpunt dat menselijke actie vraagt.",
        "blocking_contradiction": "Een open tegenspraak blokkeert verdere invloed van dit geheugenpunt.",
        "expired_terminal": "Dit geheugenpunt is verlopen en doet niet meer mee.",
        "authorized_for_consideration": "Dit geheugenpunt is geautoriseerd; relevantie bepaalt of het bij een vraag wordt gebruikt.",
        "current_gate_requires_verified_support": "De huidige Gate vraagt geverifieerde ondersteuning voordat dit geheugenpunt weer invloed kan krijgen.",
        "current_gate_not_yet_satisfied": "De huidige Gate is nog niet voldaan; Shadowseed blijft observeren.",
        "verified_support_required": "Dit geheugenpunt is voldoende teruggekomen, maar deze route vraagt nu geverifieerde ondersteuning.",
        "autonomous_observation": "Shadowseed kan dit geheugenpunt zelfstandig verder observeren.",
        "awaiting_more_observation": "Er is eerst meer geldige observatie nodig; menselijke actie is nu niet nodig.",
    }
    action_labels = {
        "submit_verified_support": "Voeg geverifieerde ondersteuning toe.",
        "resolve_contradiction": "Leg vast waarom de tegenspraak is opgelost.",
    }
    required_action = str(data.get("required_action") or "")
    return (
        state_labels.get(state, state_labels["ssl_turn"]),
        reason_labels.get(reason_code, reason_code or "Geen aanvullende toelichting."),
        action_labels.get(required_action, ""),
    )


def _orchestration_panel(view: dict[str, Any] | None) -> str:
    if not view:
        return "### Wie is aan zet?\nNog geen actief gesprek."

    title, reason, action = _orchestration_copy(
        dict(view.get("orchestration") or {})
    )
    action_line = f"  \n**Jouw volgende stap:** {action}" if action else ""
    return f"### Wie is aan zet?\n**{title}**  \n{reason}{action_line}"


def _seed_action_flags(seed: dict[str, Any] | None) -> dict[str, bool]:
    """Render action availability from the application orchestration result."""

    if not seed:
        return {
            "contradict": False,
            "verified_support": False,
            "resolve_contradiction": False,
        }
    orchestration = dict(seed.get("orchestration") or {})
    required_action = str(orchestration.get("required_action") or "")
    return {
        "contradict": not bool(seed.get("blocking", False)),
        "verified_support": required_action == "submit_verified_support",
        "resolve_contradiction": required_action == "resolve_contradiction",
    }


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

    turn_title, reason, action = _orchestration_copy(
        dict(seed.get("orchestration") or {})
    )
    action_line = f"  \n**Volgende stap:** {action}" if action else ""

    return (
        f"### {text}\n\n"
        f"**Status:** {state}\n\n"
        f"**Wie is aan zet:** {turn_title}  \n"
        f"{reason}{action_line}\n\n"
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
    orchestration = _orchestration_panel(view)
    if not view:
        return orchestration
    reports = list(view.get("turn_reports", []) or [])
    if not reports:
        context = "📄 Nog geen geheugenpunt aan een antwoord aangeboden."
    else:
        surfaced = list(reports[-1].get("surfaced_seed_ids", []) or [])
        context = (
            f"📄 **{len(surfaced)} geheugenpunt(en) als context aangeboden**"
            if surfaced
            else "📄 **Geen geheugenpunt als context aangeboden in de laatste beurt**"
        )
    return f"{orchestration}\n\n{context}"


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
    update_service = WorkbenchUpdateService(ctl.workspace_root)

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
                _ollama_note(models, models[0] if models else None),
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
        preset: str,
    ):
        try:
            session_id = create_chat_with_preset(
                title,
                provider_value,
                model_value,
                hosted_confirmed,
                preset,
            )
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
        except Exception as exc:
            error = _ui_error(exc)
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

    def _seed_action_updates(seed: dict[str, Any] | None):
        flags = _seed_action_flags(seed)
        return (
            gr.update(visible=flags["contradict"]),
            gr.update(visible=flags["verified_support"]),
            gr.update(
                visible=flags["resolve_contradiction"],
                value="",
            ),
            gr.update(visible=flags["resolve_contradiction"]),
        )

    def inspect_seed_shell(session_id: str | None, seed_id: str | None):
        story, seed = inspect_seed(session_id, seed_id)
        normalized = seed if isinstance(seed, dict) else None
        return (
            story,
            _seed_lifecycle(normalized),
            seed,
            *_seed_action_updates(normalized),
        )

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
            return (
                *result,
                _seed_lifecycle(None),
                gr.update(),
                *_seed_action_updates(None),
                extra_note,
                extra_attest,
            )
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
                *_seed_action_updates(seed),
                extra_note,
                extra_attest,
            )
        except Exception:
            return (
                *result,
                _seed_lifecycle(None),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                extra_note,
                extra_attest,
            )

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

    def resolve_contradiction_shell(
        session_id: str | None,
        seed_id: str | None,
        basis: str,
    ):
        if not session_id or not seed_id:
            return (
                "Kies eerst een geblokkeerd geheugenpunt.",
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                _seed_lifecycle(None),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(value=basis),
                gr.update(),
            )
        try:
            ctl.resolve_contradiction(
                session_id,
                seed_id,
                basis=basis,
            )
            view = ctl.session_view(session_id)
            seed = ctl.seed_view(session_id, seed_id)
            return (
                _seed_story(seed),
                _shadow_rail(view),
                _context_banner(view),
                view,
                gr.update(choices=ctl.seed_choices(view), value=seed_id),
                _seed_lifecycle(seed),
                gr.update(
                    choices=_recent_seed_choices(view),
                    value=seed_id,
                ),
                gr.update(),
                gr.update(),
                *_seed_action_updates(seed),
            )
        except Exception as exc:
            return (
                _ui_error(exc),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(value=basis),
                gr.update(),
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

    def _control_values(view: dict[str, Any] | None):
        settings = _full_settings(view)
        preset = _preset_from_view(view)
        return (
            preset,
            _preset_help(preset),
            str(settings.get("backend", "fixture")),
            settings.get("model_id"),
            float(settings.get("surface_threshold", 0.30)),
            int(settings.get("surface_top_k", 2)),
            str(settings.get("authority_profile_id", "strict")),
            str(settings.get("gate_policy_id") or "evidence_backed"),
            str(settings.get("recurrence_mode", "cluster")),
            bool(
                settings.get(
                    "allow_same_turn_revision",
                    settings.get("allow_self_reinforcement", False),
                )
            ),
            _settings_json(view),
            _authority_gate_summary(view),
            _statefulness_summary(view),
        )

    def refresh_controls(session_id: str | None):
        if not session_id:
            return _control_values(None)
        try:
            return _control_values(ctl.session_view(session_id))
        except Exception:
            return _control_values(None)

    def refresh_live_audit(session_id: str | None):
        if not session_id:
            return _audit_summary(None), {}, {}
        try:
            view = ctl.session_view(session_id)
            reports = list(view.get("turn_reports", []))
            return (
                _audit_summary(view),
                _full_settings(view),
                reports[-1] if reports else {},
            )
        except Exception as exc:
            return f"### Live audit\n**Fout:** {_ui_error(exc)}", {}, {}

    def apply_preset(
        session_id: str | None,
        preset: str,
        external_confirmed: bool,
    ):
        if not session_id:
            return (*_control_values(None), "Maak of kies eerst een gesprek.", _context_banner(None))
        if preset not in _PRESET_SETTINGS:
            view = ctl.session_view(session_id)
            return (*_control_values(view), "Kies een preset om toe te passen.", _context_banner(view))
        try:
            view = ctl.update_session_advanced(
                session_id,
                settings=dict(_PRESET_SETTINGS[preset]),
                external_confirmed=bool(external_confirmed),
            )
            return (*_control_values(view), "Preset toegepast op de actieve sessie.", _context_banner(view))
        except Exception as exc:
            view = ctl.session_view(session_id)
            return (*_control_values(view), _ui_error(exc), _context_banner(view))

    def apply_micro_settings(
        session_id: str | None,
        backend_value: str,
        model_value: str | None,
        surface_threshold_value: float,
        surface_top_k_value: float,
        authority_value: str,
        gate_policy_value: str,
        recurrence_value: str,
        same_turn_revision_value: bool,
        external_confirmed: bool,
        force: bool,
    ):
        if not session_id:
            return (*_control_values(None), "Maak of kies eerst een gesprek.", _context_banner(None))
        settings = {
            "backend": backend_value,
            "model_id": (model_value or None),
            "surface_threshold": float(surface_threshold_value),
            "surface_top_k": int(surface_top_k_value),
            "authority_profile_id": authority_value,
            "gate_policy_id": gate_policy_value,
            "recurrence_mode": recurrence_value,
            "allow_same_turn_revision": bool(same_turn_revision_value),
        }
        try:
            view = ctl.update_session_advanced(
                session_id,
                settings=settings,
                external_confirmed=bool(external_confirmed),
                force=bool(force),
            )
            return (*_control_values(view), "Instellingen opgeslagen.", _context_banner(view))
        except Exception as exc:
            view = ctl.session_view(session_id)
            return (*_control_values(view), _ui_error(exc), _context_banner(view))

    def apply_god_json(
        session_id: str | None,
        raw_json: str,
        external_confirmed: bool,
        force: bool,
    ):
        if not session_id:
            return (*_control_values(None), "Maak of kies eerst een gesprek.", _context_banner(None))
        try:
            payload = json.loads(raw_json or "{}")
            if not isinstance(payload, dict):
                raise ValueError("God mode verwacht één JSON-object met instellingen.")
            view = ctl.update_session_advanced(
                session_id,
                settings=payload,
                external_confirmed=bool(external_confirmed),
                force=bool(force),
            )
            return (*_control_values(view), "God-modeconfiguratie opgeslagen.", _context_banner(view))
        except Exception as exc:
            view = ctl.session_view(session_id)
            return (*_control_values(view), _ui_error(exc), _context_banner(view))

    def create_chat_with_preset(
        title: str,
        provider_value: str,
        model_value: str | None,
        hosted_confirmed: bool,
        preset: str,
    ):
        settings = dict(_PRESET_SETTINGS.get(preset, _PRESET_SETTINGS["gebalanceerd"]))
        session_id = ctl.create_session(
            title=(title or "").strip() or "Nieuwe chat",
            profile_id="balanced",
            backend=provider_value,
            model_id=(None if provider_value == "fixture" else (model_value or None)),
            runtime_mode="live",
            authority_profile_id=str(settings.get("authority_profile_id", "strict")),
            embedding_backend=ctl.default_embedding_backend(provider_value),
            external_confirmed=bool(hosted_confirmed),
            allow_same_turn_revision=bool(settings.get("allow_same_turn_revision", False)),
        )
        ctl.update_session_advanced(
            session_id,
            settings=settings,
            external_confirmed=bool(hosted_confirmed),
        )
        return session_id

    initial_controls = _control_values(initial_view)

    def _update_result_view(result: dict[str, Any]) -> tuple[str, dict[str, Any], Any]:
        status = str(result.get("status", ""))
        if status == "available":
            candidate = dict(result.get("candidate") or {})
            version = candidate.get("version", "?")
            channel = "Research Preview" if candidate.get("prerelease") else "Release"
            message = (
                f"### Update beschikbaar: {version}\n"
                f"{channel}. De update wordt **niet automatisch geïnstalleerd**. "
                "Klik op downloaden om de officiële build op te halen en te verifiëren."
            )
            return message, candidate, gr.update(visible=True)
        if status == "up_to_date":
            return (
                "### Geen nieuwere release beschikbaar\n"
                f"Geïnstalleerde pakketversie: **{result.get('current_version', '?')}**. "
                "Een development-build kan daarnaast nog niet-uitgebrachte wijzigingen bevatten.",
                {},
                gr.update(visible=False),
            )
        return "### Updatecontrole\nNog niet gecontroleerd.", {}, gr.update(visible=False)

    def check_updates():
        try:
            return _update_result_view(update_service.check())
        except Exception as exc:
            return (
                f"### Updatecontrole mislukt\n{_ui_error(exc)}",
                {},
                gr.update(visible=False),
            )

    def maybe_check_updates(enabled: bool):
        if not bool(enabled):
            return (
                f"### Updates\nGeïnstalleerde versie: **{update_service.current_version}**. "
                "Automatisch controleren staat uit.",
                {},
                gr.update(visible=False),
            )
        return check_updates()

    def save_auto_update(enabled: bool):
        try:
            value = update_service.set_auto_check(bool(enabled))
            suffix = "aan" if value else "uit"
            return f"Automatisch controleren bij starten staat **{suffix}**."
        except Exception as exc:
            return _ui_error(exc)

    def download_update(candidate_payload: dict[str, Any] | None):
        if not candidate_payload:
            return "Controleer eerst of er een update beschikbaar is."
        try:
            result = update_service.download(dict(candidate_payload))
            return (
                f"### Update {result['version']} gecontroleerd gedownload\n"
                f"Bestand: `{result['archive']}`  \n"
                "Manifest en SHA-256 zijn gecontroleerd. Sluit Shadowseed voordat je "
                "de huidige app vervangt door deze nieuwe build."
            )
        except Exception as exc:
            return f"### Download mislukt\n{_ui_error(exc)}"

    def toggle_sidebar(is_open: bool):
        next_state = not bool(is_open)
        return next_state, gr.update(visible=next_state)

    with gr.Blocks(title="Shadowseed") as app:
        active_session = gr.State(initial_id)
        help_feature = gr.State("conversation")
        left_open = gr.State(True)
        right_open = gr.State(True)

        with gr.Group(elem_id="ss-shell"):
            with gr.Row(elem_id="ss-topbar"):
                brand = gr.Markdown("## SHADOWSEED", elem_id="ss-brand", scale=4)
                model_badge = gr.Markdown(_model_badge(initial_view), elem_id="ss-model-badge", scale=2)
                model_top_info = gr.Button("ⓘ", scale=0, min_width=40, elem_classes=["ss-info-button"])
                controls_toggle = gr.Button("⚙  Regie", scale=0, min_width=92)
                audit_toggle = gr.Button("▣  Audit", scale=0, min_width=86)
                menu_button = gr.Button("☰  Menu", scale=0, min_width=100)

            with gr.Row(equal_height=True):
                with gr.Column(scale=2, min_width=250, elem_id="ss-left") as left_sidebar:
                    with gr.Row():
                        gr.Markdown("### REGIE", scale=4)
                        conversation_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
                    new_chat_open = gr.Button("＋  Nieuwe chat", variant="primary", elem_classes=["ss-primary"])
                    session_select = gr.Dropdown(
                        choices=compact_sessions,
                        value=initial_id,
                        label="Gesprek",
                        container=True,
                    )
                    control_preset = gr.Dropdown(
                        choices=[
                            ("Observeren", "observeren"),
                            ("Gebalanceerd", "gebalanceerd"),
                            ("Onderzoekend", "onderzoekend"),
                            ("Aangepast", "custom"),
                        ],
                        value=initial_controls[0],
                        label="Preset",
                    )
                    preset_help = gr.Markdown(initial_controls[1], elem_classes=["ss-muted"])
                    apply_preset_button = gr.Button("Preset toepassen", variant="secondary")

                    with gr.Accordion("Model & runtime", open=True):
                        settings_provider = gr.Dropdown(
                            choices=[
                                ("Ollama · lokaal", "ollama"),
                                ("OpenAI · online", "openai"),
                                ("Hugging Face · lokaal", "hf-transformers"),
                                ("Offline demo", "fixture"),
                            ],
                            value=initial_controls[2],
                            label="Provider",
                        )
                        settings_model = gr.Dropdown(
                            choices=([initial_controls[3]] if initial_controls[3] else []),
                            value=initial_controls[3],
                            allow_custom_value=True,
                            label="Model",
                        )
                        settings_external_confirm = gr.Checkbox(
                            label="Externe verwerking toegestaan",
                            value=False,
                        )

                    with gr.Accordion("Microcontrole per component", open=False):
                        gr.Markdown("**Relevantie & surfacing · direct toepasbaar**")
                        surface_threshold_control = gr.Slider(
                            minimum=0.0,
                            maximum=1.0,
                            step=0.01,
                            value=initial_controls[4],
                            label="Surfacing-drempel",
                        )
                        surface_top_k_control = gr.Slider(
                            minimum=0,
                            maximum=10,
                            step=1,
                            value=initial_controls[5],
                            label="Max. seeds per antwoord",
                        )

                        authority_gate_note = gr.Markdown(
                            initial_controls[11],
                            elem_classes=["ss-muted"],
                        )
                        authority_control = gr.Dropdown(
                            choices=["strict", "assisted", "autonomous", "open"],
                            value=initial_controls[6],
                            label="Authority-profiel · stateful",
                        )
                        gate_policy_control = gr.Dropdown(
                            choices=["evidence_backed", "exploratory"],
                            value=initial_controls[7],
                            label="Gate-policy · expliciete override",
                        )

                        gr.Markdown(
                            "**Recurrence · structurele semantic-memory-state**  \n"
                            "Wijzigen nadat seeds bestaan vereist een nieuwe sessie of expliciete rebuild."
                        )
                        recurrence_control = gr.Dropdown(
                            choices=["cluster", "pairwise"],
                            value=initial_controls[8],
                            label="Recurrence · rebuild required",
                        )

                        gr.Markdown("**Same-turn revision · stateful**")
                        same_turn_revision_control = gr.Checkbox(
                            label="Herziening in dezelfde beurt",
                            value=initial_controls[9],
                        )
                        god_force = gr.Checkbox(
                            label="God mode force (structurele grenzen blijven gelden)",
                            value=False,
                        )
                        apply_micro_button = gr.Button("Micro-instellingen opslaan", variant="primary")

                    with gr.Accordion("God mode · alle instellingen", open=False):
                        statefulness_note = gr.Markdown(
                            initial_controls[12],
                            elem_classes=["ss-muted"],
                        )
                        gr.Markdown(
                            "Hier staat de werkelijk opgeslagen configuratie. Wijzig alleen waarden die je bewust wilt overschrijven."
                        )
                        god_json = gr.Textbox(
                            value=initial_controls[10],
                            label=None,
                            lines=18,
                            max_lines=30,
                        )
                        apply_god_button = gr.Button("Volledige configuratie schrijven", variant="stop")
                    control_result = gr.Markdown("", elem_classes=["ss-muted"])

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

                with gr.Column(scale=2, min_width=255, elem_id="ss-right") as right_sidebar:
                    live_audit = gr.Markdown(_audit_summary(initial_view), elem_id="ss-shadow-metrics")
                    with gr.Accordion("Actieve configuratie", open=False):
                        live_config = gr.JSON(value=_full_settings(initial_view), label=None)
                    with gr.Accordion("Laatste turn", open=False):
                        live_turn = gr.JSON(
                            value=(list(initial_view.get("turn_reports", []))[-1] if initial_view and initial_view.get("turn_reports") else {}),
                            label=None,
                        )
                    shadow_metrics = gr.Markdown(_shadow_rail(initial_view))
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
            new_preset = gr.Dropdown(
                choices=[
                    ("Observeren", "observeren"),
                    ("Gebalanceerd", "gebalanceerd"),
                    ("Onderzoekend", "onderzoekend"),
                ],
                value="gebalanceerd",
                label="Preset",
            )
            gr.Markdown(
                "Preset bepaalt de startwaarden. Daarna kun je links iedere instelling afzonderlijk aanpassen.",
                elem_classes=["ss-muted"],
            )
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
                contradiction_button = gr.Button(
                    "Tegenspraak registreren",
                    scale=4,
                    visible=False,
                )
                contradiction_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            resolution_basis = gr.Textbox(
                label="Waarom is de tegenspraak opgelost?",
                lines=2,
                visible=False,
            )
            resolve_contradiction_button = gr.Button(
                "Tegenspraak afhandelen",
                variant="primary",
                visible=False,
            )
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
                    visible=False,
                )
                evidence_info = gr.Button("ⓘ", scale=0, min_width=38, elem_classes=["ss-info-button"])
            technical_open_from_seed = gr.Button("Technische audit", variant="secondary")

        with gr.Group(visible=False, elem_id="ss-menu-panel", elem_classes=["ss-drawer"]) as menu_panel:
            menu_close = gr.Button("× Sluiten", variant="secondary")
            about_button = gr.Button("ⓘ  Over Shadowseed")
            research_open = gr.Button("⚗  Onderzoek")
            audit_open = gr.Button("▣  Technische audit")
            updates_open = gr.Button("↻  Updates")
            model_menu_info = gr.Button("⚙  Model & provider")
            gr.Markdown(
                f"Versie **{update_service.current_version}**",
                elem_classes=["ss-muted"],
            )

        with gr.Group(visible=False, elem_id="ss-panel-updates", elem_classes=["ss-drawer"]) as updates_panel:
            with gr.Row():
                gr.Markdown("## Updates", elem_classes=["ss-drawer-title"], scale=5)
                updates_close = gr.Button("×", scale=0, min_width=40, elem_classes=["ss-info-button"])
            gr.Markdown(
                "Updates komen alleen uit de officiële Shadowseed GitHub Releases. "
                "Downloaden en installeren gebeurt nooit zonder jouw keuze."
            )
            auto_updates = gr.Checkbox(
                label="Automatisch controleren bij starten",
                value=update_service.auto_check_enabled(),
            )
            auto_update_note = gr.Markdown(
                "Automatisch controleren staat standaard uit.",
                elem_classes=["ss-muted"],
            )
            check_update_button = gr.Button("Controleer nu", variant="secondary")
            update_status = gr.Markdown(
                f"### Updates\nGeïnstalleerde versie: **{update_service.current_version}**."
            )
            update_candidate = gr.State({})
            download_update_button = gr.Button(
                "Download en verifieer update",
                variant="primary",
                visible=False,
                elem_classes=["ss-primary"],
            )
            update_download_result = gr.Markdown("")

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
            with gr.Accordion("Herziening in dezelfde beurt", open=False):
                same_turn_revision_info = gr.Button("ⓘ Leg same-turn revision uit")
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
            (same_turn_revision_info, "same_turn_revision"),
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
        updates_open.click(
            lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[updates_panel, menu_panel],
        )
        updates_close.click(close_panel, outputs=[updates_panel])
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

        controls_toggle.click(
            toggle_sidebar,
            inputs=[left_open],
            outputs=[left_open, left_sidebar],
        )
        audit_toggle.click(
            toggle_sidebar,
            inputs=[right_open],
            outputs=[right_open, right_sidebar],
        )

        settings_provider.change(
            provider_changed,
            inputs=[settings_provider],
            outputs=[settings_model, control_result],
        )

        control_preset.change(
            lambda preset: _preset_help(preset),
            inputs=[control_preset],
            outputs=[preset_help],
        )

        control_outputs = [
            control_preset,
            preset_help,
            settings_provider,
            settings_model,
            surface_threshold_control,
            surface_top_k_control,
            authority_control,
            gate_policy_control,
            recurrence_control,
            same_turn_revision_control,
            god_json,
            authority_gate_note,
            statefulness_note,
            control_result,
        ]

        apply_preset_button.click(
            apply_preset,
            inputs=[active_session, control_preset, settings_external_confirm],
            outputs=control_outputs + [context_banner],
        )

        apply_micro_button.click(
            apply_micro_settings,
            inputs=[
                active_session,
                settings_provider,
                settings_model,
                surface_threshold_control,
                surface_top_k_control,
                authority_control,
                gate_policy_control,
                recurrence_control,
                same_turn_revision_control,
                settings_external_confirm,
                god_force,
            ],
            outputs=control_outputs + [context_banner],
        )

        apply_god_button.click(
            apply_god_json,
            inputs=[active_session, god_json, settings_external_confirm, god_force],
            outputs=control_outputs + [context_banner],
        )

        session_select.change(
            refresh_controls,
            inputs=[session_select],
            outputs=control_outputs[:-1],
        )

        audit_timer = gr.Timer(1.0)
        audit_timer.tick(
            refresh_live_audit,
            inputs=[active_session],
            outputs=[live_audit, live_config, live_turn],
        )

        auto_updates.change(
            save_auto_update,
            inputs=[auto_updates],
            outputs=[auto_update_note],
        )
        check_update_button.click(
            check_updates,
            outputs=[update_status, update_candidate, download_update_button],
        )
        download_update_button.click(
            download_update,
            inputs=[update_candidate],
            outputs=[update_download_result],
        )
        app.load(
            maybe_check_updates,
            inputs=[auto_updates],
            outputs=[update_status, update_candidate, download_update_button],
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
            inputs=[new_title, provider, model_id, hosted_confirm, new_preset],
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
            outputs=[
                seed_story,
                lifecycle,
                seed_json,
                contradiction_button,
                evidence_button,
                resolution_basis,
                resolve_contradiction_button,
            ],
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
                contradiction_button,
                evidence_button,
                resolution_basis,
                resolve_contradiction_button,
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
                contradiction_button,
                evidence_button,
                resolution_basis,
                resolve_contradiction_button,
                evidence_note,
                evidence_attest,
            ],
        )

        resolve_contradiction_button.click(
            resolve_contradiction_shell,
            inputs=[active_session, seed_select, resolution_basis],
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
                contradiction_button,
                evidence_button,
                resolution_basis,
                resolve_contradiction_button,
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
