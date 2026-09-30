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
:root {
  --ss-radius-xl: 28px;
  --ss-radius-lg: 20px;
  --ss-radius-md: 14px;
  --ss-shadow: 0 20px 60px rgba(15, 23, 42, .10);
  --ss-shadow-soft: 0 8px 28px rgba(15, 23, 42, .07);
  --ss-border: color-mix(in srgb, var(--border-color-primary) 70%, transparent);
  --ss-surface: color-mix(in srgb, var(--background-fill-secondary) 92%, transparent);
  --ss-surface-strong: color-mix(in srgb, var(--background-fill-secondary) 98%, transparent);
}

body {
  background:
    radial-gradient(circle at 12% -10%, rgba(79, 70, 229, .10), transparent 34rem),
    radial-gradient(circle at 96% 4%, rgba(13, 148, 136, .08), transparent 30rem),
    var(--body-background-fill);
}

.gradio-container {
  max-width: 1600px !important;
  margin: 0 auto;
  padding: 1rem 1.2rem 3rem !important;
}

#ss-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--ss-border);
  border-radius: var(--ss-radius-xl);
  padding: 1.05rem 1.25rem;
  margin-bottom: .75rem;
  background:
    linear-gradient(135deg, rgba(79,70,229,.075), rgba(13,148,136,.035) 58%, transparent),
    var(--ss-surface-strong);
  box-shadow: var(--ss-shadow-soft);
}
#ss-hero:after {
  content: "";
  position: absolute;
  width: 260px;
  height: 260px;
  right: -150px;
  top: -170px;
  border-radius: 999px;
  background: rgba(79,70,229,.10);
  pointer-events: none;
}
#ss-hero h1 {
  margin: 0 0 .1rem 0;
  font-size: clamp(1.55rem, 2vw, 2.15rem);
  letter-spacing: -.045em;
}
#ss-hero p { margin: .12rem 0 .22rem; max-width: 1000px; }

#ss-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: .65rem;
  margin: .35rem 0 .65rem;
}
#ss-menu-button button {
  border-radius: 14px !important;
  font-weight: 760 !important;
  min-width: 112px;
}
#ss-menu-panel {
  border: 1px solid var(--ss-border);
  border-radius: 18px;
  padding: .65rem;
  margin: 0 0 .8rem;
  background: color-mix(in srgb, var(--background-fill-primary) 94%, transparent);
  box-shadow: var(--ss-shadow-soft);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}
#ss-menu-panel button {
  justify-content: flex-start !important;
  text-align: left !important;
  border-radius: 12px !important;
}
.ss-menu-copy {
  opacity: .68;
  font-size: .82rem;
  padding: .05rem .15rem .35rem;
}

.tab-nav {
  position: sticky !important;
  top: .55rem;
  z-index: 50;
  display: flex !important;
  gap: .25rem !important;
  padding: .32rem !important;
  border: 1px solid var(--ss-border) !important;
  border-radius: 18px !important;
  background: color-mix(in srgb, var(--background-fill-primary) 86%, transparent) !important;
  box-shadow: 0 8px 30px rgba(15,23,42,.08);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  margin-bottom: 1rem !important;
  overflow-x: auto;
  scrollbar-width: none;
}
.tab-nav::-webkit-scrollbar { display: none; }
.tab-nav button {
  flex: 0 0 auto;
  border: 0 !important;
  border-radius: 13px !important;
  font-weight: 680 !important;
  letter-spacing: -.012em;
  padding: .58rem .84rem !important;
  transition: transform .16s ease, background .16s ease, box-shadow .16s ease;
}
.tab-nav button:hover { transform: translateY(-1px); }
.tab-nav button.selected {
  background: var(--button-primary-background-fill) !important;
  color: var(--button-primary-text-color) !important;
  box-shadow: 0 5px 14px rgba(15,23,42,.12);
}

#ss-side {
  position: sticky;
  top: 5rem;
  border: 1px solid var(--ss-border);
  border-radius: 24px;
  padding: .9rem;
  background: var(--ss-surface-strong);
  box-shadow: var(--ss-shadow-soft);
}
#ss-side h3 { margin-top: .15rem; letter-spacing: -.025em; }

.ss-control-card {
  border: 1px solid var(--ss-border) !important;
  border-radius: 18px !important;
  padding: .78rem .84rem !important;
  background: var(--ss-surface) !important;
  margin-bottom: .45rem !important;
  transition: border-color .16s ease, transform .16s ease;
}
.ss-control-card:hover {
  transform: translateY(-1px);
  border-color: color-mix(in srgb, var(--button-primary-background-fill) 38%, var(--ss-border)) !important;
}
.ss-control-card label { font-weight: 720 !important; }
.ss-control-copy {
  margin: -.15rem 0 .45rem !important;
  padding: .05rem .22rem .2rem !important;
  font-size: .86rem !important;
  opacity: .78;
}
.ss-feedback-card {
  border: 1px dashed color-mix(in srgb, var(--button-primary-background-fill) 45%, var(--ss-border)) !important;
  border-radius: 18px !important;
  padding: .72rem .82rem !important;
  background: color-mix(in srgb, var(--button-primary-background-fill) 5%, var(--ss-surface)) !important;
  margin-bottom: .45rem !important;
}
.ss-regie-summary {
  border: 1px solid color-mix(in srgb, var(--button-primary-background-fill) 28%, var(--ss-border));
  border-radius: 16px;
  padding: .72rem .82rem;
  margin: .2rem 0 .6rem;
  background: linear-gradient(135deg, color-mix(in srgb, var(--button-primary-background-fill) 7%, transparent), transparent);
}
.ss-regie-summary p { margin: .1rem 0 !important; }
.ss-gate-alert {
  border: 1px solid color-mix(in srgb, #f59e0b 48%, var(--ss-border));
  border-radius: 18px;
  padding: .82rem .95rem;
  margin: .6rem 0;
  background: color-mix(in srgb, #f59e0b 7%, var(--ss-surface));
  box-shadow: var(--ss-shadow-soft);
}
.ss-gate-alert:empty { display: none; }

#ss-chat {
  border: 1px solid var(--ss-border);
  border-radius: 24px;
  overflow: hidden;
  background: var(--ss-surface-strong);
  box-shadow: var(--ss-shadow-soft);
}
#ss-chat .message {
  border-radius: 18px !important;
  box-shadow: none !important;
}
#ss-status {
  margin-top: .55rem;
  padding: .72rem .9rem;
  border: 1px solid var(--ss-border);
  border-radius: 14px;
  background: var(--ss-surface);
  font-size: .89rem;
}
#ss-composer {
  position: sticky;
  bottom: .75rem;
  z-index: 35;
  border: 1px solid var(--ss-border);
  border-radius: 22px;
  padding: .72rem;
  margin-top: .7rem;
  background: color-mix(in srgb, var(--background-fill-primary) 91%, transparent);
  box-shadow: 0 14px 38px rgba(15,23,42,.13);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
}
#ss-composer textarea { font-size: 1rem !important; line-height: 1.5 !important; }

button.primary, button.secondary, button.stop {
  border-radius: 13px !important;
  font-weight: 680 !important;
  min-height: 40px;
  transition: transform .14s ease, box-shadow .14s ease;
}
button.primary:hover, button.secondary:hover, button.stop:hover { transform: translateY(-1px); }

.ss-card, .ss-detail, #ss-memory-story, #ss-source-result, #ss-verify-result {
  border: 1px solid var(--ss-border);
  border-radius: 20px;
  padding: .95rem 1rem;
  background: var(--ss-surface);
  box-shadow: var(--ss-shadow-soft);
}
.ss-muted { opacity: .70; font-size: .88rem; }
.ss-kicker {
  opacity: .60;
  font-size: .70rem;
  font-weight: 820;
  letter-spacing: .12em;
  text-transform: uppercase;
  margin-top: .78rem !important;
}
#ss-memory-story { min-height: 240px; }
#ss-source-result, #ss-verify-result { min-height: 140px; }

#ss-about-flow {
  font-size: 1.01rem;
  padding: .9rem 1rem;
  border: 1px solid var(--ss-border);
  border-radius: 16px;
  background: var(--ss-surface);
}

#ss-dashboard {
  border: 1px solid var(--ss-border);
  border-radius: 24px;
  padding: 1.1rem 1.2rem;
  background:
    linear-gradient(145deg, rgba(79,70,229,.055), transparent 60%),
    var(--ss-surface-strong);
  box-shadow: var(--ss-shadow);
}
.ss-metric {
  border: 1px solid var(--ss-border);
  border-radius: 20px;
  padding: .9rem 1rem;
  background: var(--ss-surface-strong);
  min-height: 128px;
  box-shadow: var(--ss-shadow-soft);
  transition: transform .16s ease, border-color .16s ease;
}
.ss-metric:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--button-primary-background-fill) 36%, var(--ss-border));
}
.ss-metric h2, .ss-metric h3 { margin: 0 0 .15rem; letter-spacing: -.035em; }
.ss-detail { min-height: 180px; }

details {
  border: 1px solid var(--ss-border) !important;
  border-radius: 16px !important;
  background: var(--ss-surface) !important;
  overflow: hidden;
}
details summary { font-weight: 680 !important; padding: .15rem .1rem !important; }
input, textarea, select { border-radius: 12px !important; }
input[type="range"] { accent-color: var(--button-primary-background-fill); }

@media (max-width: 900px) {
  .gradio-container { padding: .65rem .65rem 2rem !important; }
  #ss-hero { border-radius: 20px; padding: .95rem 1rem; }
  #ss-side { position: static; border-radius: 20px; }
  .tab-nav { top: .35rem; border-radius: 15px !important; }
  #ss-chat { border-radius: 20px; }
  #ss-composer { bottom: .35rem; border-radius: 18px; }
  .ss-metric { min-height: 104px; }
}
@media (prefers-reduced-motion: reduce) {
  *, *:before, *:after {
    scroll-behavior: auto !important;
    transition: none !important;
    animation: none !important;
  }
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
        f"**{label}**  \n{explanation}\n\n"
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


def _ssl_intensity_explainer(percent: int | float) -> str:
    value = max(0, min(100, int(round(float(percent)))))
    if value == 0:
        label = "Alleen meekijken"
        detail = "Shadowseed leert wel, maar niets uit het geheugen mag een antwoord beïnvloeden."
    elif value <= 25:
        label = "Zeer terughoudend"
        detail = "Alleen uitzonderlijk relevante toegestane geheugenpunten mogen meedoen."
    elif value <= 50:
        label = "Beperkt"
        detail = "Shadowseed kan af en toe een sterk relevant geheugenpunt laten meedenken."
    elif value <= 75:
        label = "Actief"
        detail = "Relevante toegestane geheugenpunten kunnen normaal meedoen."
    else:
        label = "Volledig aan"
        detail = "Shadowseed krijgt de volledige normale ruimte om toegestane relevante punten te gebruiken."
    return (
        f"**SSL-invloed {value}% · {label}**  \n{detail}\n\n"
        "Deze schuif bepaalt **hoeveel invloed** toegestane geheugenpunten krijgen."
    )


def _gate_strictness_explainer(percent: int | float) -> str:
    value = max(0, min(100, int(round(float(percent)))))
    if value <= 10:
        label = "Open"
        detail = (
            "De eerste waarneming kan direct autoriteit krijgen en vanaf een volgende "
            "relevante beurt invloed hebben."
        )
    elif value <= 30:
        label = "Licht"
        detail = "Een idee moet minimaal terugkomen voordat het autoriteit kan krijgen."
    elif value <= 50:
        label = "Herhaling vereist"
        detail = "Meerdere onafhankelijke herhalingen zijn nodig voordat invloed mogelijk wordt."
    elif value <= 70:
        label = "Bewijs vereist"
        detail = "Herhaling alleen is niet genoeg; geverifieerde externe onderbouwing is nodig."
    elif value < 100:
        label = "Zwaar bewijs"
        detail = "Meerdere onafhankelijke geverifieerde bronnen zijn nodig voor promotie."
    else:
        label = "Maximaal strikt"
        detail = (
            "Een geheugenpunt moet minstens vier keer onafhankelijk terugkomen én drie "
            "onafhankelijke geverifieerde bewijsbronnen hebben. Tegenspraak blijft blokkeren."
        )
    return (
        f"**Validation Gate {value}% · {label}**  \n{detail}\n\n"
        "0% = lage toegangsdrempel · 100% = keiharde bewijsdrempel. "
        "Audittrail en tegenspraakcontrole blijven altijd actief."
    )


def _control_preset_values(preset: str | None) -> tuple[int, int, bool]:
    presets = {
        "observeren": (0, 100, False),
        "gebalanceerd": (60, 70, False),
        "vrij": (100, 0, True),
        "strikt": (100, 100, False),
    }
    return presets.get(str(preset or "strikt"), presets["strikt"])


def _control_preset_id(
    ssl_intensity: int | float,
    gate_strictness: int | float,
    self_reinforcement: bool,
) -> str | None:
    target = (
        int(round(float(ssl_intensity))),
        int(round(float(gate_strictness))),
        bool(self_reinforcement),
    )
    for preset in ("observeren", "gebalanceerd", "vrij", "strikt"):
        if _control_preset_values(preset) == target:
            return preset
    return None


def _legacy_control_summary(self_reinforcement: bool) -> str:
    loop_label = "aan" if self_reinforcement else "uit"
    return (
        "**Aangepaste/legacy-regie**  \n"
        f"feedbacklus **{loop_label}**  \n"
        "Deze sessie heeft geen exact 0–100%-label. Kies een snelle stand "
        "of beweeg een schuif om SSL en Gate expliciet over te nemen."
    )


def _control_state_summary(
    ssl_intensity: int | float,
    gate_strictness: int | float,
    self_reinforcement: bool,
) -> str:
    ssl_value = max(0, min(100, int(round(float(ssl_intensity)))))
    gate_value = max(0, min(100, int(round(float(gate_strictness)))))
    if self_reinforcement and gate_value <= 20 and ssl_value >= 80:
        mode = "Vrij experiment"
        detail = "Snelle promotie, hoge invloed en een actieve feedbacklus."
    elif ssl_value == 0:
        mode = "Observeren"
        detail = "Shadowseed leert en auditeert, maar beïnvloedt het antwoord niet."
    elif gate_value >= 90 and not self_reinforcement:
        mode = "Strikt"
        detail = "Invloed is mogelijk, maar alleen na een zware autoriteitsdrempel."
    else:
        mode = "Aangepast"
        detail = "Je combineert invloed, Gate en feedbacklus handmatig."
    loop = "aan" if self_reinforcement else "uit"
    return (
        f"**{mode}**  \n"
        f"SSL **{ssl_value}%** · Gate **{gate_value}%** · feedbacklus **{loop}**  \n"
        f"{detail}"
    )


def _embedding_explainer(choice: str | None) -> str:
    key = str(choice or "auto")
    if key == "auto":
        return (
            "**Automatisch · aanbevolen**  \n"
            "Shadowseed kiest zelf de passende manier om betekenis/relevantie te vergelijken. "
            "Je hoeft hiervoor niets te weten over embeddings."
        )
    if key == "lexical":
        return (
            "**Snel lokaal · woordoverlap**  \n"
            "Geen extra model. Snel en volledig lokaal, maar minder goed in synoniemen "
            "en zinnen die hetzelfde bedoelen met andere woorden."
        )
    if key == "sentence-transformers":
        return (
            "**Slim lokaal · betekenis**  \n"
            "Een klein lokaal model vergelijkt betekenis in plaats van alleen woorden. "
            "Dit is meestal de beste handmatige keuze en stuurt geen tekst naar een online provider."
        )
    if key == "openai":
        return (
            "**Online · OpenAI betekenisvergelijking**  \n"
            "Tekst wordt voor embeddings naar OpenAI gestuurd. Alleen kiezen als je dit bewust wilt; "
            "voor de meeste Workbench-sessies is lokaal voldoende."
        )
    return "**Aangepaste technische keuze.**"


def _gate_notice(view: dict[str, Any] | None) -> str:
    if not view:
        return ""
    review_ids = [str(item) for item in view.get("authority_review_seed_ids", []) or []]
    if not review_ids:
        return ""
    seeds = {
        str(seed.get("id")): str(seed.get("text", "")).strip()
        for seed in view.get("seeds", []) or []
    }
    previews = [
        f"- **{seeds.get(seed_id, seed_id)[:180]}**"
        for seed_id in review_ids[:3]
    ]
    more = (
        f"\n- … en nog {len(review_ids) - 3}"
        if len(review_ids) > 3
        else ""
    )
    return (
        "### ⚠ Validation Gate vraagt jouw beoordeling\n"
        f"**{len(review_ids)} geheugenpunt(en)** zijn vaak genoeg teruggekomen, "
        "maar missen nog menselijke/geverifieerde onderbouwing. Tot die beoordeling "
        "krijgen ze in deze stand geen normale autoriteit.\n\n"
        + "\n".join(previews)
        + more
        + "\n\n**Wat jij moet doen:** open **Geheugen**, kies het gemarkeerde punt en "
        "voeg een onafhankelijke bron toe die je zelf hebt gecontroleerd, of blokkeer het punt "
        "als het niet klopt. Je hoeft hiervoor niets opnieuw te draaien of handmatig te refreshen."
    )


def _model_note(backend: str, model_id: str | None = None) -> str:
    label, explanation = _BACKEND_UI.get(
        backend,
        (backend or "Onbekend model", ""),
    )
    model = f" · `{model_id}`" if model_id else ""
    return f"**{label}**{model}  \n{explanation}"


def _seed_can_influence(seed: dict[str, Any]) -> bool:
    """Return the user-facing effective authorization for one seed snapshot."""

    if "current_gate_authorized" in seed:
        return bool(seed.get("current_gate_authorized"))
    return (
        str(seed.get("status", "")).upper() == "PROMOTED"
        and not bool(seed.get("blocking", False))
    )


def _historical_promotion_only(seed: dict[str, Any]) -> bool:
    return (
        str(seed.get("status", "")).upper() == "PROMOTED"
        and not _seed_can_influence(seed)
    )


def _chat_status(view: dict[str, Any] | None) -> str:
    if not view:
        return "Nog geen gesprek geopend. Klik op **Nieuwe chat** om te beginnen."

    seeds = list(view.get("seeds", []))
    authorized = sum(_seed_can_influence(seed) for seed in seeds)
    historical_only = sum(_historical_promotion_only(seed) for seed in seeds)
    blocked = sum(bool(seed.get("blocking", False)) for seed in seeds)
    review = len(view.get("authority_review_seed_ids", []) or [])
    turns = int(view.get("turn", 0) or 0)
    model = str(view.get("model_id") or view.get("backend") or "model")
    ssl_raw = view.get("ssl_intensity")
    gate_raw = view.get("gate_strictness")
    ssl_level = f"{int(ssl_raw)}%" if ssl_raw is not None else "aangepast"
    gate_level = f"{int(gate_raw)}%" if gate_raw is not None else "aangepast"

    extras: list[str] = []
    if authorized:
        extras.append(f"{authorized} mag later meedenken")
    if historical_only:
        extras.append(f"{historical_only} historisch promoted, nu niet toegelaten")
    if review:
        extras.append(f"{review} vraagt controle")
    if blocked:
        extras.append(f"{blocked} geblokkeerd")
    seed_text = (
        f"{len(seeds)} geheugenpunt(en)"
        + (f" · {' · '.join(extras)}" if extras else "")
    )

    loop = " · feedbacklus **aan**" if view.get("allow_self_reinforcement") else ""
    return (
        f"**{model}** · {turns} bericht(en) · SSL **{ssl_level}** · Gate **{gate_level}**{loop}  \n"
        f"Shadowseed: {seed_text}"
    )


def _memory_overview(view: dict[str, Any] | None) -> str:
    if not view:
        return "Kies een gesprek om het Shadowseed-geheugen te bekijken."

    seeds = list(view.get("seeds", []))
    authorized = sum(_seed_can_influence(item) for item in seeds)
    historical_only = sum(_historical_promotion_only(item) for item in seeds)
    blocked = sum(bool(item.get("blocking", False)) for item in seeds)
    used: set[str] = set()
    for report in view.get("turn_reports", []) or []:
        used.update(str(seed_id) for seed_id in report.get("surfaced_seed_ids", []) or [])

    return (
        f"**{len(seeds)}** geheugenpunt(en) · "
        f"**{authorized}** mag meedenken · "
        f"**{len(used)}** daadwerkelijk gebruikt · "
        f"**{blocked}** geblokkeerd"
        + (
            f" · **{historical_only}** historisch promoted, nu niet toegelaten"
            if historical_only
            else ""
        )
        + "\n\nEen geheugenpunt is een mogelijke ontbrekende invalshoek. "
        "Het is niet automatisch een feit."
    )



def _dashboard_summary(view: dict[str, Any] | None) -> tuple[str, str, str, str, str]:
    if not view:
        empty = "### —\nNog geen gesprek gekozen"
        return (
            "## Welkom bij Shadowseed\nKies of maak een gesprek. Daarna zie je hier in één oogopslag wat er gebeurt.",
            empty,
            empty,
            empty,
            "### Geen aandachtspunten\nShadowseed wacht op een gesprek.",
        )

    seeds = list(view.get("seeds", []) or [])
    turns = int(view.get("turn", 0) or 0)
    authorized = sum(_seed_can_influence(seed) for seed in seeds)
    historical_only = sum(_historical_promotion_only(seed) for seed in seeds)
    blocked = sum(bool(seed.get("blocking", False)) for seed in seeds)
    review = len(view.get("authority_review_seed_ids", []) or [])
    used: set[str] = set()
    for report in view.get("turn_reports", []) or []:
        used.update(str(seed_id) for seed_id in report.get("surfaced_seed_ids", []) or [])

    ssl_raw = view.get("ssl_intensity")
    gate_raw = view.get("gate_strictness")
    ssl_level = f"{int(ssl_raw)}%" if ssl_raw is not None else "aangepast"
    gate_level = f"{int(gate_raw)}%" if gate_raw is not None else "aangepast"
    model = str(view.get("model_id") or view.get("backend") or "model")

    headline = (
        f"## {view.get('title') or 'Gesprek'}\n"
        f"Model **{model}** · SSL **{ssl_level}** · Gate **{gate_level}** · "
        f"feedbacklus **{'aan' if view.get('allow_self_reinforcement') else 'uit'}** · "
        f"**{turns}** bericht(en)"
    )
    conversation = (
        f"### {turns}\n"
        "**berichten**\n\n"
        "Open **Chat** om verder te praten."
    )
    memory = (
        f"### {len(seeds)}\n"
        "**geheugenpunten**\n\n"
        f"{authorized} mag meedenken · {len(used)} daadwerkelijk gebruikt"
        + (
            f" · {historical_only} historisch promoted"
            if historical_only
            else ""
        )
    )
    authority = (
        f"### {review + blocked}\n"
        "**aandachtspunten**\n\n"
        f"{review} vraagt controle · {blocked} geblokkeerd"
    )
    if blocked:
        attention = (
            "### Actie nodig\n"
            f"Er {'is' if blocked == 1 else 'zijn'} **{blocked} geblokkeerde** geheugenpunt"
            f"{'' if blocked == 1 else 'en'}. Open hieronder een punt voor uitleg."
        )
    elif review:
        attention = (
            "### Controle gevraagd\n"
            f"**{review}** geheugenpunt(en) hebben voldoende ontwikkeling om menselijke controle te vragen."
        )
    elif authorized:
        attention = (
            "### Alles rustig\n"
            f"**{authorized}** geheugenpunt(en) mogen meedenken wanneer ze later relevant zijn."
        )
    elif historical_only:
        attention = (
            "### Gate is aangescherpt\n"
            f"**{historical_only}** geheugenpunt(en) zijn historisch promoted, maar voldoen "
            "niet meer aan de huidige Gate en kunnen nu niet meedenken."
        )
    else:
        attention = (
            "### Alles rustig\n"
            "Shadowseed bouwt het geheugen op. Er is op dit moment geen handmatige actie nodig."
        )
    return headline, conversation, memory, authority, attention


def _seed_story(view: dict[str, Any] | None) -> str:
    if not view:
        return (
            "## Kies een geheugenpunt\n"
            "Je ziet hier in gewone taal wat Shadowseed heeft opgemerkt en wat ermee is gebeurd."
        )

    status_raw = str(view.get("status", "UNKNOWN")).upper()
    status = _STATUS_NL.get(status_raw, status_raw.title())
    text = str(view.get("text", "")).strip() or "(geen tekst)"
    occurrences = int(view.get("occurrence_count", 0) or 0)
    evidence = int(view.get("evidence_count", 0) or 0)
    blocking = bool(view.get("blocking", False))
    current_authorized = _seed_can_influence(view)
    historical_only = _historical_promotion_only(view)
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
    elif historical_only:
        status = "Historisch promoted · nu niet toegelaten"
        action = (
            "**Wat nu?** Dit punt passeerde eerder de Gate, maar voldoet niet meer aan de "
            "huidige Gate-instellingen. Het kan nu niet meedenken."
        )
    elif status_raw == "PROMOTED" and current_authorized and used:
        action = (
            f"**Wat nu?** Dit punt mocht meedenken en is al **{used}×** daadwerkelijk gebruikt. "
            "De technische audit laat precies zien wanneer."
        )
    elif status_raw == "PROMOTED" and current_authorized:
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
        f"### {status}\n"
        f"## {text}\n\n"
        f"**Gezien:** {occurrences}× · **onderbouwing:** {evidence} · **gebruikt:** {used}×\n\n"
        f"{action}"
    )


def _source_summary(result: dict[str, Any] | None) -> str:
    if not result:
        return (
            "## Nog niets toegevoegd\n"
            "Plak tekst of kies bestanden. Shadowseed leest de inhoud in stukken en bouwt "
            "daarmee het geheugen van het gekozen gesprek op."
        )
    if result.get("error"):
        return f"**Bronnen konden niet worden verwerkt:** {result['error']}"

    promoted = len(result.get("promoted_seed_ids", []) or [])
    review = len(result.get("authority_review_seed_ids", []) or [])
    names = ", ".join(result.get("source_names", []) or []) or "bron"
    return (
        "## Klaar\n"
        f"**{int(result.get('sources', 0))}** bron(nen) · "
        f"**{int(result.get('chunks', 0))}** tekstdeel/delen · "
        f"**{int(result.get('new_seed_count', 0))}** nieuwe geheugenpunten  \n"
        f"**{promoted}** mag meedenken · **{review}** vraagt controle  \n"
        f"Bronnen: {names}\n\n"
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
    mode = str(comparison.get("comparison_mode", "authorized"))
    with_ssl = (
        labels.get("shadow_pressure")
        or labels.get("ssl_on")
        or labels.get("shadowseed")
        or ""
    )
    without_ssl = labels.get("ssl_off") or labels.get("baseline") or ""
    influenced = bool(comparison.get("ssl_influence_observed"))
    if mode == "shadow_pressure":
        candidates = list(comparison.get("shadow_pressure_candidates", []) or [])
        if candidates:
            note = (
                f"**Shadow pressure actief:** {len(candidates)} nog niet-gepromoveerde seed(s) "
                "zijn read-only aan de experimentele arm aangeboden. Dit meet mogelijke "
                "pre-promotie sturing, niet Gate-geautoriseerde invloed."
            )
        else:
            note = (
                "**Geen shadow pressure op deze vraag.** Er waren geen voldoende ontwikkelde "
                "én relevante niet-gepromoveerde seeds; gelijke antwoorden zijn dan logisch."
            )
    else:
        note = (
            "**Geautoriseerde SSL-invloed aangetoond.** Minstens één promoted en relevante seed "
            "bereikte de treatment prompt."
            if influenced
            else
            "**Geen geautoriseerde SSL-invloed op deze beurt.** A en B krijgen dan inhoudelijk "
            "dezelfde context; bij deterministische modellen hoort het verschil vaak nul te zijn."
        )
    return with_ssl, without_ssl, note


def _verify_summary(comparison: dict[str, Any] | None) -> str:
    if not comparison:
        return (
            "## Nog niets gecontroleerd\n"
            "Kies een gesprek en berichtnummer. Een controle is alleen beschikbaar als voor dat "
            "bericht vooraf een vergelijking zonder Shadowseed is opgeslagen."
        )
    mode = str(comparison.get("comparison_mode", "authorized"))
    influenced = bool(comparison.get("ssl_influence_observed"))
    surfaced = list(comparison.get("surfaced_seed_ids", []) or [])
    question = str(comparison.get("question", "")).strip()

    if mode == "shadow_pressure":
        if influenced:
            verdict = (
                "### Experimentele pre-authority invloed zichtbaar\n"
                f"Er zijn **{len(surfaced)}** nog niet-gepromoveerde geheugenpunt(en) "
                "read-only aan de treatment-arm aangeboden. Dit zijn **geen "
                "Gate-geautoriseerde** geheugenpunten."
            )
        else:
            verdict = (
                "### Geen shadow pressure op deze vergelijking\n"
                "Er waren geen voldoende ontwikkelde en relevante pre-promotie-seeds "
                "voor de experimentele treatment-arm."
            )
    elif influenced:
        verdict = (
            "### Ja, geautoriseerde Shadowseed-invloed is aangetoond\n"
            f"Er zijn **{len(surfaced)}** geautoriseerde geheugenpunt(en) gebruikt."
        )
    else:
        verdict = (
            "### Nee, voor dit antwoord is geen geautoriseerde Shadowseed-invloed aangetoond\n"
            "Eventuele verschillen tussen twee generaties kunnen normale modelvariatie zijn."
        )
    return verdict + (f"\n\n**Vraag:** {question}" if question else "")


def build_simple_app(
    workspace: str | Path | None = None,
    *,
    controller: WorkbenchController | None = None,
):
    """Bouw de Nederlandse, chatgerichte Workbench."""

    gr = _gradio()
    ctl = controller or WorkbenchController(workspace)

    initial_sessions = ctl.session_choices(ctl.list_sessions())
    initial_session_id = initial_sessions[0][1] if initial_sessions else None
    try:
        initial_view = (
            ctl.session_view(initial_session_id)
            if initial_session_id is not None
            else None
        )
    except Exception:
        initial_view = None
    initial_chat_messages = ctl.chat_messages(initial_view) if initial_view else []
    initial_dashboard = _dashboard_summary(initial_view)
    initial_seed_choices = ctl.seed_choices(initial_view) if initial_view else []
    initial_ssl = (
        int(initial_view["ssl_intensity"])
        if initial_view and initial_view.get("ssl_intensity") is not None
        else 100
    )
    initial_gate = (
        int(initial_view["gate_strictness"])
        if initial_view and initial_view.get("gate_strictness") is not None
        else 100
    )
    initial_loop = bool(
        initial_view.get("allow_self_reinforcement", False)
        if initial_view
        else False
    )
    initial_controls_explicit = bool(
        initial_view
        and initial_view.get("ssl_intensity") is not None
        and initial_view.get("gate_strictness") is not None
    )
    initial_control_preset = (
        _control_preset_id(initial_ssl, initial_gate, initial_loop)
        if initial_controls_explicit
        else None
    )
    initial_control_summary = (
        _control_state_summary(initial_ssl, initial_gate, initial_loop)
        if initial_controls_explicit
        else _legacy_control_summary(initial_loop)
    )

    auto_backend, auto_model, auto_setup_note = _recommended_setup(ctl)

    provider_choices = [
        (_BACKEND_UI[key][0], key)
        for key in ("ollama", "openai", "hf-transformers", "fixture")
    ]
    embedding_choices = [
        ("Automatisch · aanbevolen", "auto"),
        ("Slim lokaal · vergelijkt betekenis", "sentence-transformers"),
        ("Snel lokaal · vergelijkt woorden", "lexical"),
        ("Online · OpenAI vergelijkt betekenis", "openai"),
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
                    _model_note("ollama") + f"\n\n**Lokaal model zoeken lukte niet:** {exc}",
                    "auto",
                )
            selected = current_model if current_model in models else (models[0] if models else None)
            note = _model_note("ollama", selected)
            if not models:
                note += "\n\nGeen lokaal Ollama-model gevonden."
            return (
                gr.update(choices=models, value=selected),
                note,
                "auto",
            )
        selected = None
        return (
            gr.update(choices=[], value=None),
            _model_note(backend, selected),
            "auto",
        )

    def refresh_models(backend: str, current_model: str | None):
        model_update, note, _embedding = provider_changed(backend, current_model)
        return model_update, note

    def _control_view_state(view: dict[str, Any] | None):
        if not view:
            return (
                gr.update(value=None),
                gr.update(value=100),
                _ssl_intensity_explainer(100),
                gr.update(value=100),
                _gate_strictness_explainer(100),
                gr.update(value=False),
                _control_state_summary(100, 100, False),
            )
        ssl_raw = view.get("ssl_intensity")
        gate_raw = view.get("gate_strictness")
        loop = bool(view.get("allow_self_reinforcement", False))
        ssl_value = int(ssl_raw) if ssl_raw is not None else 100
        gate_value = int(gate_raw) if gate_raw is not None else 100
        preset = (
            _control_preset_id(ssl_value, gate_value, loop)
            if ssl_raw is not None and gate_raw is not None
            else None
        )
        summary = (
            _control_state_summary(ssl_value, gate_value, loop)
            if ssl_raw is not None and gate_raw is not None
            else _legacy_control_summary(loop)
        )
        return (
            gr.update(value=preset),
            gr.update(value=ssl_value),
            _ssl_intensity_explainer(ssl_value),
            gr.update(value=gate_value),
            _gate_strictness_explainer(gate_value),
            gr.update(value=loop),
            summary,
        )

    def _persist_controls(
        session_id: str | None,
        ssl_value: float,
        gate_value: float,
        loop: bool,
    ) -> tuple[str | Any, Any, str]:
        if not session_id:
            return gr.update(), gr.update(), ""
        view = ctl.update_session_controls(
            session_id,
            ssl_intensity=ssl_value,
            gate_strictness=gate_value,
            allow_self_reinforcement=bool(loop),
        )
        notice = _gate_notice(view)
        if notice:
            gr.Warning("Validation Gate vraagt jouw beoordeling.")
        return _chat_status(view), view, notice

    def apply_control_preset(session_id: str | None, preset: str):
        ssl_value, gate_value, loop = _control_preset_values(preset)
        status, view, notice = _persist_controls(
            session_id, ssl_value, gate_value, loop
        )
        return (
            gr.update(value=ssl_value),
            _ssl_intensity_explainer(ssl_value),
            gr.update(value=gate_value),
            _gate_strictness_explainer(gate_value),
            gr.update(value=loop),
            _control_state_summary(ssl_value, gate_value, loop),
            status,
            view,
            notice,
        )

    def update_ssl_control(
        session_id: str | None,
        value: float,
        gate: float,
        loop: bool,
    ):
        status, view, notice = _persist_controls(session_id, value, gate, loop)
        return (
            _ssl_intensity_explainer(value),
            gr.update(value=None),
            _control_state_summary(value, gate, loop),
            status,
            view,
            notice,
        )

    def update_gate_control(
        session_id: str | None,
        value: float,
        ssl: float,
        loop: bool,
    ):
        status, view, notice = _persist_controls(session_id, ssl, value, loop)
        return (
            _gate_strictness_explainer(value),
            gr.update(value=None),
            _control_state_summary(ssl, value, loop),
            status,
            view,
            notice,
        )

    def update_loop_control(
        session_id: str | None,
        loop: bool,
        ssl: float,
        gate: float,
    ):
        if not session_id:
            return (
                gr.update(value=None),
                _control_state_summary(ssl, gate, loop),
                gr.update(),
                gr.update(),
                "",
            )
        view = ctl.update_session_self_reinforcement(
            session_id,
            allow_self_reinforcement=bool(loop),
        )
        ssl_raw = view.get("ssl_intensity")
        gate_raw = view.get("gate_strictness")
        if ssl_raw is None or gate_raw is None:
            loop_label = "aan" if loop else "uit"
            summary = (
                "**Aangepaste/legacy-regie**  \n"
                f"feedbacklus **{loop_label}**  \n"
                "SSL- en Gate-instellingen blijven ongewijzigd; kies een snelle stand "
                "of beweeg een schuif om ze expliciet over te nemen."
            )
            preset = None
        else:
            ssl_value = int(ssl_raw)
            gate_value = int(gate_raw)
            preset = _control_preset_id(ssl_value, gate_value, loop)
            summary = _control_state_summary(ssl_value, gate_value, loop)
        notice = _gate_notice(view)
        return (
            gr.update(value=preset),
            summary,
            _chat_status(view),
            view,
            notice,
        )

    def create_chat(
        title: str,
        backend: str,
        model_id: str,
        ssl_intensity: float,
        gate_strictness: float,
        allow_self_reinforcement: bool,
        embedding_backend: str,
        embedding_model: str,
        hosted_confirmed: bool,
    ):
        try:
            clean_title = (title or "").strip() or "Nieuwe chat"
            resolved_embedding = (
                ctl.default_embedding_backend(backend)
                if embedding_backend == "auto"
                else embedding_backend
            )
            session_id = ctl.create_session(
                title=clean_title,
                profile_id="balanced",
                authority_profile_id="strict",
                backend=backend,
                model_id=(None if backend == "fixture" else (model_id or None)),
                runtime_mode="live",
                embedding_backend=resolved_embedding,
                embedding_model=embedding_model or None,
                allow_toy_embedder=False,
                external_confirmed=bool(hosted_confirmed),
                ssl_intensity=ssl_intensity,
                gate_strictness=gate_strictness,
                allow_self_reinforcement=bool(allow_self_reinforcement),
            )
            view = ctl.session_view(session_id)
            return (
                dropdown_update(session_choices(), session_id),
                ctl.chat_messages(view),
                _chat_status(view),
                view,
                "",
                _gate_notice(view),
            )
        except Exception as exc:
            return gr.update(), [], _fout(exc), None, "", ""

    def load_chat(session_id: str | None):
        if not session_id:
            return (
                [],
                _chat_status(None),
                None,
                *_control_view_state(None),
                "",
            )
        try:
            view = ctl.session_view(session_id)
            notice = _gate_notice(view)
            if notice:
                gr.Warning("Validation Gate vraagt jouw beoordeling.")
            return (
                ctl.chat_messages(view),
                _chat_status(view),
                view,
                *_control_view_state(view),
                notice,
            )
        except Exception as exc:
            return (
                [],
                _fout(exc),
                None,
                *_control_view_state(None),
                "",
            )

    def send_message(
        session_id: str | None,
        question: str,
        compare_without_ssl: bool,
        comparison_mode: str,
        hosted_confirmed: bool,
    ):
        if not session_id:
            return (
                gr.update(),
                "Maak eerst een nieuwe chat.",
                None,
                question,
                "",
                "",
                "",
                gr.update(),
                "",
            )
        if not str(question or "").strip():
            return (
                gr.update(),
                "Typ eerst een bericht.",
                None,
                question,
                "",
                "",
                "",
                gr.update(),
                "",
            )
        try:
            result = ctl.send_turn(
                session_id,
                question,
                compare_without_ssl=bool(compare_without_ssl),
                comparison_mode=comparison_mode or "authorized",
                external_confirmed=bool(hosted_confirmed),
            )
            view = result["session"]
            with_ssl, without_ssl, note = _comparison_view(result.get("comparison"))
            notice = _gate_notice(view)
            if notice:
                gr.Warning("Validation Gate vraagt jouw beoordeling.")
            return (
                ctl.chat_messages(view),
                _chat_status(view),
                result["report"],
                "",
                with_ssl,
                without_ssl,
                note,
                view,
                notice,
            )
        except Exception as exc:
            return (
                gr.update(),
                _fout(exc),
                None,
                question,
                "",
                "",
                _fout(exc),
                gr.update(),
                "",
            )

    def ingest_sources(
        session_id: str | None,
        pasted_text: str,
        uploaded_files: list[str] | str | None,
        hosted_confirmed: bool,
    ):
        if not session_id:
            return (
                _source_summary({"error": "Kies eerst een gesprek."}),
                gr.update(),
                None,
                pasted_text,
                "",
            )
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
            notice = _gate_notice(view)
            if notice:
                gr.Warning("Validation Gate vraagt jouw beoordeling.")
            return (
                _source_summary(result),
                gr.update(choices=ctl.seed_choices(view), value=None),
                view,
                "",
                notice,
            )
        except Exception as exc:
            return (
                _source_summary({"error": f"{type(exc).__name__}: {exc}"}),
                gr.update(),
                None,
                pasted_text,
                "",
            )

    def dashboard_session_changed(session_id: str | None):
        if not session_id:
            summary = _dashboard_summary(None)
            return (*summary, gr.update(choices=[], value=None), _seed_story(None), None, None)
        try:
            view = ctl.session_view(session_id)
            summary = _dashboard_summary(view)
            seed_update = dropdown_update(ctl.seed_choices(view))
            return (*summary, seed_update, _seed_story(None), None, None)
        except Exception as exc:
            error = _fout(exc)
            return (error, error, error, error, error, gr.update(), error, None, None)

    def refresh_dashboard(current: str | None):
        choices = session_choices()
        valid = {item[1] for item in choices}
        selected = current if current in valid else (choices[0][1] if choices else None)
        return (
            dropdown_update(choices, selected),
            *dashboard_session_changed(selected),
        )

    def memory_session_changed(session_id: str | None):
        if not session_id:
            return gr.update(choices=[], value=None), _memory_overview(None)
        try:
            view = ctl.session_view(session_id)
            return dropdown_update(ctl.seed_choices(view)), _memory_overview(view)
        except Exception as exc:
            return gr.update(), _fout(exc)

    def refresh_memory(current: str | None):
        choices = session_choices()
        valid = {item[1] for item in choices}
        selected = current if current in valid else (choices[0][1] if choices else None)
        seed_update, overview = memory_session_changed(selected)
        return (
            dropdown_update(choices, selected),
            seed_update,
            overview,
        )

    def _notice_for_selected_session(
        selected_session_id: str | None,
        *,
        mutated_session_id: str,
        mutated_view: dict[str, Any],
    ):
        if not selected_session_id:
            return ""
        try:
            view = (
                mutated_view
                if selected_session_id == mutated_session_id
                else ctl.session_view(selected_session_id)
            )
            return _gate_notice(view)
        except Exception:
            # A review mutation must not clear or fail an unrelated tab merely
            # because that tab's selected session cannot be refreshed.
            return gr.update()

    def inspect_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return _seed_story(None), None, None
        try:
            view = ctl.seed_view(session_id, seed_id)
            return _seed_story(view), view, view.get("timeline", [])
        except Exception as exc:
            err = {"error": f"{type(exc).__name__}: {exc}"}
            return _fout(exc), err, None

    def falsify_seed(
        session_id: str | None,
        seed_id: str | None,
        chat_session_id: str | None = None,
        source_session_id: str | None = None,
    ):
        if not session_id or not seed_id:
            return (
                {"error": "Kies eerst een gesprek en geheugenpunt."},
                _seed_story(None),
                None,
                None,
                gr.update(),
                _memory_overview(None),
                gr.update(),
                gr.update(),
            )
        try:
            result = ctl.falsify_seed(session_id, seed_id)
            view = ctl.seed_view(session_id, seed_id)
            session_view = ctl.session_view(session_id)
            memory_notice = _gate_notice(session_view)
            chat_notice = _notice_for_selected_session(
                chat_session_id,
                mutated_session_id=session_id,
                mutated_view=session_view,
            )
            source_notice = _notice_for_selected_session(
                source_session_id,
                mutated_session_id=session_id,
                mutated_view=session_view,
            )
            if memory_notice:
                gr.Warning("Validation Gate vraagt nog om beoordeling.")
            return (
                result,
                _seed_story(view),
                view,
                view.get("timeline", []),
                dropdown_update(ctl.seed_choices(session_view), seed_id),
                _memory_overview(session_view),
                chat_notice,
                source_notice,
            )
        except Exception as exc:
            err = {"error": f"{type(exc).__name__}: {exc}"}
            return (
                err,
                _fout(exc),
                err,
                None,
                gr.update(),
                _fout(exc),
                gr.update(),
                gr.update(),
            )

    def submit_verified_evidence(
        session_id: str | None,
        seed_id: str | None,
        source_ref: str,
        note: str,
        operator_verified: bool,
        chat_session_id: str | None = None,
        source_session_id: str | None = None,
    ):
        if not session_id or not seed_id:
            return (
                {"error": "Kies eerst een gesprek en geheugenpunt."},
                _seed_story(None),
                None,
                None,
                gr.update(),
                _memory_overview(None),
                gr.update(),
                gr.update(),
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
            session_view = ctl.session_view(session_id)
            memory_notice = _gate_notice(session_view)
            chat_notice = _notice_for_selected_session(
                chat_session_id,
                mutated_session_id=session_id,
                mutated_view=session_view,
            )
            source_notice = _notice_for_selected_session(
                source_session_id,
                mutated_session_id=session_id,
                mutated_view=session_view,
            )
            if memory_notice:
                gr.Warning("Validation Gate vraagt nog om beoordeling.")
            return (
                result,
                _seed_story(view),
                view,
                view.get("timeline", []),
                dropdown_update(ctl.seed_choices(session_view), seed_id),
                _memory_overview(session_view),
                chat_notice,
                source_notice,
                "",
                False,
            )
        except Exception as exc:
            err = {"error": f"{type(exc).__name__}: {exc}"}
            return (
                err,
                _fout(exc),
                err,
                None,
                gr.update(),
                _fout(exc),
                gr.update(),
                gr.update(),
                "",
                False,
            )

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
                "### Geen opgeslagen vergelijking beschikbaar\n"
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

    with gr.Blocks(title="Shadowseed", css=_NL_CSS, theme=gr.themes.Soft()) as app:
        with gr.Group(elem_id="ss-hero"):
            gr.Markdown("# Shadowseed Workbench")
            gr.Markdown(
                "**Chat met een model en zie hoe geheugen, Gate en invloed zich ontwikkelen.**"
            )
            gr.Markdown(
                "Nederlands · chat-first · auditbaar · experimentele feedbacklus optioneel",
                elem_classes=["ss-muted"],
            )

        with gr.Row(elem_id="ss-topbar"):
            gr.Markdown(
                "**Werkruimte** · kies een onderdeel via de tabs of het menu.",
                elem_classes=["ss-muted"],
            )
            menu_button = gr.Button("☰ Menu", variant="secondary", elem_id="ss-menu-button")

        with gr.Column(visible=False, elem_id="ss-menu-panel") as menu_panel:
            gr.Markdown(
                "Ga direct naar een onderdeel",
                elem_classes=["ss-menu-copy"],
            )
            with gr.Row():
                menu_overview = gr.Button("Overzicht", variant="secondary")
                menu_chat = gr.Button("Chat", variant="secondary")
                menu_memory = gr.Button("Geheugen", variant="secondary")
                menu_sources = gr.Button("Bronnen", variant="secondary")
            with gr.Row():
                menu_verify = gr.Button("Controleren", variant="secondary")
                menu_about = gr.Button("Uitleg", variant="secondary")
                menu_more = gr.Button("Meer", variant="secondary")

        with gr.Tab("Overzicht", id="overzicht", elem_id="ss-tab-overzicht"):
            with gr.Row():
                dashboard_session = gr.Dropdown(
                    choices=initial_sessions,
                    value=initial_session_id,
                    label="Gesprek",
                )
                dashboard_refresh = gr.Button("Vernieuwen", variant="secondary")

            dashboard_headline = gr.Markdown(
                initial_dashboard[0],
                elem_id="ss-dashboard",
            )
            with gr.Row():
                dashboard_conversation = gr.Markdown(
                    initial_dashboard[1],
                    elem_classes=["ss-metric"],
                )
                dashboard_memory = gr.Markdown(
                    initial_dashboard[2],
                    elem_classes=["ss-metric"],
                )
                dashboard_authority = gr.Markdown(
                    initial_dashboard[3],
                    elem_classes=["ss-metric"],
                )

            dashboard_attention = gr.Markdown(
                initial_dashboard[4],
                elem_classes=["ss-detail"],
            )

            gr.Markdown("### Doorklikken naar detail")
            with gr.Row():
                dashboard_seed = gr.Dropdown(
                    choices=initial_seed_choices,
                    label="Geheugenpunt",
                    scale=2,
                )
                dashboard_open_seed = gr.Button("Open detail", variant="primary", scale=1)
            dashboard_seed_story = gr.Markdown(
                _seed_story(None),
                elem_classes=["ss-detail"],
            )
            with gr.Accordion("Technische audit van dit punt", open=False):
                dashboard_seed_json = gr.JSON(label="Ruwe toestand")
                dashboard_seed_timeline = gr.JSON(label="Gebeurtenissen")

            dashboard_refresh.click(
                refresh_dashboard,
                inputs=[dashboard_session],
                outputs=[
                    dashboard_session,
                    dashboard_headline,
                    dashboard_conversation,
                    dashboard_memory,
                    dashboard_authority,
                    dashboard_attention,
                    dashboard_seed,
                    dashboard_seed_story,
                    dashboard_seed_json,
                    dashboard_seed_timeline,
                ],
            )
            dashboard_session.change(
                dashboard_session_changed,
                inputs=[dashboard_session],
                outputs=[
                    dashboard_headline,
                    dashboard_conversation,
                    dashboard_memory,
                    dashboard_authority,
                    dashboard_attention,
                    dashboard_seed,
                    dashboard_seed_story,
                    dashboard_seed_json,
                    dashboard_seed_timeline,
                ],
            )
            dashboard_open_seed.click(
                inspect_seed,
                inputs=[dashboard_session, dashboard_seed],
                outputs=[
                    dashboard_seed_story,
                    dashboard_seed_json,
                    dashboard_seed_timeline,
                ],
            )

        with gr.Tab("Chat", id="chat", elem_id="ss-tab-chat"):
            with gr.Row():
                with gr.Column(scale=1, min_width=300):
                    with gr.Group(elem_id="ss-side"):
                        gr.Markdown("### Gesprekken")
                        session_select = gr.Dropdown(
                            choices=initial_sessions,
                            value=initial_session_id,
                            label="Open gesprek",
                        )
                        refresh_sessions = gr.Button("Vernieuwen", variant="secondary")
                        new_chat = gr.Button("＋ Nieuwe chat", variant="primary")

                        gr.Markdown("Regie", elem_classes=["ss-kicker"])
                        control_preset = gr.Dropdown(
                            choices=[
                                ("Observeren", "observeren"),
                                ("Gebalanceerd", "gebalanceerd"),
                                ("Vrij experiment", "vrij"),
                                ("Strikt", "strikt"),
                            ],
                            value=initial_control_preset,
                            label="Snelle stand",
                        )
                        control_summary = gr.Markdown(
                            initial_control_summary,
                            elem_classes=["ss-regie-summary"],
                        )
                        ssl_intensity = gr.Slider(
                            minimum=0,
                            maximum=100,
                            step=10,
                            value=initial_ssl,
                            label="SSL-invloed",
                            info="0% alleen leren · 100% maximale toegestane invloed",
                            elem_classes=["ss-control-card"],
                        )
                        ssl_intensity_help = gr.Markdown(
                            _ssl_intensity_explainer(initial_ssl),
                            elem_classes=["ss-control-copy"],
                        )
                        gate_strictness = gr.Slider(
                            minimum=0,
                            maximum=100,
                            step=10,
                            value=initial_gate,
                            label="Validation Gate",
                            info="0% vrijwel direct door · 100% zware bewijsdrempel",
                            elem_classes=["ss-control-card"],
                        )
                        gate_strictness_help = gr.Markdown(
                            _gate_strictness_explainer(initial_gate),
                            elem_classes=["ss-control-copy"],
                        )
                        allow_self_reinforcement = gr.Checkbox(
                            label="Zelfversterking · experimenteel",
                            value=initial_loop,
                            info="Laat SSL-beïnvloede antwoorden de geheugenlus opnieuw voeden.",
                            elem_classes=["ss-feedback-card"],
                        )

                        gr.Markdown("Model", elem_classes=["ss-kicker"])
                        auto_note = gr.Markdown(auto_setup_note, elem_classes=["ss-muted"])
                        model_note = gr.Markdown(
                            _model_note(auto_backend, auto_model),
                            elem_classes=["ss-muted"],
                        )
                        with gr.Accordion("Model en geavanceerd", open=False):
                            title = gr.Textbox(
                                label="Naam nieuwe chat",
                                value="Nieuwe chat",
                            )
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
                                label=(
                                    "Ik begrijp dat bij een online taalmodel of online "
                                    "betekenisvergelijking tekst naar de provider wordt gestuurd"
                                ),
                                value=False,
                            )
                            with gr.Accordion("Technisch", open=False):
                                embedding_backend = gr.Dropdown(
                                    choices=embedding_choices,
                                    value="auto",
                                    label="Hoe vergelijkt Shadowseed betekenis?",
                                )
                                embedding_help = gr.Markdown(
                                    _embedding_explainer("auto"),
                                    elem_classes=["ss-control-copy"],
                                )
                                embedding_model = gr.Textbox(
                                    label="Eigen embeddingmodel (optioneel)",
                                )

                with gr.Column(scale=3, min_width=620):
                    chat = gr.Chatbot(
                        value=initial_chat_messages,
                        label="Gesprek",
                        height=560,
                        elem_id="ss-chat",
                    )
                    chat_status = gr.Markdown(
                        _chat_status(initial_view),
                        elem_id="ss-status",
                    )
                    gate_alert = gr.Markdown(
                        _gate_notice(initial_view),
                        elem_classes=["ss-gate-alert"],
                    )
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
                        comparison_mode = gr.Radio(
                            choices=[
                                ("Geautoriseerde SSL · alleen promoted seeds", "authorized"),
                                ("Shadow pressure · pre-promotie experiment", "shadow_pressure"),
                            ],
                            value="authorized",
                            label="Wat wil je vergelijken?",
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
                            session_json = gr.JSON(
                                value=initial_view,
                                label="Gesprekstoestand · technisch",
                            )

            control_preset.input(
                apply_control_preset,
                inputs=[session_select, control_preset],
                outputs=[
                    ssl_intensity,
                    ssl_intensity_help,
                    gate_strictness,
                    gate_strictness_help,
                    allow_self_reinforcement,
                    control_summary,
                    chat_status,
                    session_json,
                    gate_alert,
                ],
            )
            ssl_intensity.input(
                update_ssl_control,
                inputs=[
                    session_select,
                    ssl_intensity,
                    gate_strictness,
                    allow_self_reinforcement,
                ],
                outputs=[
                    ssl_intensity_help,
                    control_preset,
                    control_summary,
                    chat_status,
                    session_json,
                    gate_alert,
                ],
            )
            gate_strictness.input(
                update_gate_control,
                inputs=[
                    session_select,
                    gate_strictness,
                    ssl_intensity,
                    allow_self_reinforcement,
                ],
                outputs=[
                    gate_strictness_help,
                    control_preset,
                    control_summary,
                    chat_status,
                    session_json,
                    gate_alert,
                ],
            )
            allow_self_reinforcement.input(
                update_loop_control,
                inputs=[
                    session_select,
                    allow_self_reinforcement,
                    ssl_intensity,
                    gate_strictness,
                ],
                outputs=[
                    control_preset,
                    control_summary,
                    chat_status,
                    session_json,
                    gate_alert,
                ],
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
            embedding_backend.change(
                _embedding_explainer,
                inputs=[embedding_backend],
                outputs=[embedding_help],
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
                    backend,
                    model_id,
                    ssl_intensity,
                    gate_strictness,
                    allow_self_reinforcement,
                    embedding_backend,
                    embedding_model,
                    hosted_confirm,
                ],
                outputs=[
                    session_select,
                    chat,
                    chat_status,
                    session_json,
                    question,
                    gate_alert,
                ],
            )
            session_select.change(
                load_chat,
                inputs=[session_select],
                outputs=[
                    chat,
                    chat_status,
                    session_json,
                    control_preset,
                    ssl_intensity,
                    ssl_intensity_help,
                    gate_strictness,
                    gate_strictness_help,
                    allow_self_reinforcement,
                    control_summary,
                    gate_alert,
                ],
            )
            send_button.click(
                send_message,
                inputs=[
                    session_select,
                    question,
                    compare_checkbox,
                    comparison_mode,
                    hosted_confirm,
                ],
                outputs=[
                    chat,
                    chat_status,
                    last_turn_json,
                    question,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                    session_json,
                    gate_alert,
                ],
            )
            question.submit(
                send_message,
                inputs=[
                    session_select,
                    question,
                    compare_checkbox,
                    comparison_mode,
                    hosted_confirm,
                ],
                outputs=[
                    chat,
                    chat_status,
                    last_turn_json,
                    question,
                    ssl_on,
                    ssl_off,
                    comparison_note,
                    session_json,
                    gate_alert,
                ],
            )

        with gr.Tab("Bronnen", id="bronnen", elem_id="ss-tab-bronnen"):
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
                    source_gate_alert = gr.Markdown(
                        "",
                        elem_classes=["ss-gate-alert"],
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
                outputs=[
                    source_result,
                    source_seed_preview,
                    source_state,
                    source_paste,
                    source_gate_alert,
                ],
            )

        with gr.Tab("Geheugen", id="geheugen", elem_id="ss-tab-geheugen"):
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
                refresh_memory,
                inputs=[memory_session],
                outputs=[memory_session, seed_select, memory_overview],
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
                inputs=[
                    memory_session,
                    seed_select,
                    session_select,
                    source_session,
                ],
                outputs=[
                    falsify_result,
                    seed_story,
                    seed_json,
                    seed_timeline,
                    seed_select,
                    memory_overview,
                    gate_alert,
                    source_gate_alert,
                ],
            )
            evidence_button.click(
                submit_verified_evidence,
                inputs=[
                    memory_session,
                    seed_select,
                    evidence_source,
                    evidence_note,
                    evidence_attest,
                    session_select,
                    source_session,
                ],
                outputs=[
                    evidence_result,
                    seed_story,
                    seed_json,
                    seed_timeline,
                    seed_select,
                    memory_overview,
                    gate_alert,
                    source_gate_alert,
                    evidence_source,
                    evidence_attest,
                ],
            )

        with gr.Tab("Controleren", id="controleren", elem_id="ss-tab-controleren"):
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

        with gr.Tab("Uitleg", id="uitleg", elem_id="ss-tab-uitleg"):
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
                    "opgedeeld, kandidaten worden gededupliceerd en geclusterd en herhaling wordt bijgehouden. "
                    "Je stuurt vervolgens twee dingen zelf: **SSL-invloed** bepaalt hoeveel toegestane "
                    "geheugenpunten in antwoorden mogen meedoen; **Validation Gate** bepaalt hoeveel "
                    "herhaling en onafhankelijk bewijs nodig is voordat zo'n punt überhaupt autoriteit krijgt. "
                    "Daardoor kun je bijvoorbeeld een heel open Gate combineren met 0% invloed, of juist "
                    "100% SSL combineren met een maximaal strikte bewijsdrempel."
                )
            with gr.Accordion("6 · Wat gebeurt er met uploads?", open=False):
                gr.Markdown(
                    "Bronnen volgen een apart pad: **lezen → opdelen → kandidaten vinden → herhaling "
                    "herkennen → Gate → geheugen**. Een document wordt dus niet automatisch een "
                    "waarheidsbron. De herkomst blijft gekoppeld aan de waarneming."
                )
            with gr.Accordion("7 · Wat is de experimentele feedbacklus?", open=False):
                gr.Markdown(
                    "Normaal telt een antwoord dat al door Shadowseed is beïnvloed niet opnieuw mee als "
                    "onafhankelijke recurrence. Met **Zelfversterking toestaan** zet je die bescherming "
                    "bewust uit. Een SSL-beïnvloed antwoord kan dan nieuwe of terugkerende geheugenpunten "
                    "opnieuw voeden, waardoor een zelfversterkende lus kan ontstaan. Als zo'n punt in die "
                    "beurt direct autoriteit krijgt, mag Shadowseed maximaal **één extra generatie** doen "
                    "voor hetzelfde gebruikersbericht. Dat tweede antwoord wordt het zichtbare eindantwoord. "
                    "De tweede generatie wordt niet opnieuw gedetecteerd, zodat de lus per beurt begrensd "
                    "blijft. De audittrail bewaart het eerste conceptantwoord en de gebruikte seed."
                )
            with gr.Accordion("8 · Is dit hetzelfde als RAG of fine-tuning?", open=False):
                gr.Markdown(
                    "**Fine-tuning** verandert modelgewichten; Shadowseed niet. **RAG** zoekt meestal "
                    "informatie naar aanleiding van de huidige vraag. Shadowseed bouwt juist door de tijd "
                    "heen een geschiedenis op van mogelijke ontbrekende perspectieven. De technieken kunnen "
                    "naast elkaar bestaan."
                )
            with gr.Accordion("9 · Wat kan Shadowseed níet bewijzen?", open=False):
                gr.Markdown(
                    "Een geheugenpunt is niet automatisch waar. Meer tekst betekent niet automatisch beter "
                    "geheugen. Twee verschillende antwoorden bewijzen geen Shadowseed-effect. En een "
                    "gepromoveerd punt hoeft niet gebruikt te worden. Daarom blijven herkomst, Gate-besluiten, "
                    "tegenspraken en daadwerkelijke influence-events inspecteerbaar."
                )
            with gr.Accordion("10 · Technische woorden vertaald", open=False):
                gr.Markdown(
                    "**Shadow seed** — mogelijk ontbrekende invalshoek.  \n"
                    "**Shadow memory** — verzameling geheugenpunten met hun geschiedenis.  \n"
                    "**Trace** — afnemende maat voor hoe levend een punt nog is.  \n"
                    "**Validation Gate** — beslisgrens voor autoriteit.  \n"
                    "**Promoted** — mag later meedenken als het relevant is.  \n"
                    "**Surfacing** — een toegestaan punt wordt voor een nieuwe vraag beschikbaar gemaakt.  \n"
                    "**Point of use** — laatste controle vlak voordat een punt invloed kan hebben."
                )

        with gr.Tab("Meer", id="meer", elem_id="ss-tab-meer"):
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

        menu_button.click(
            lambda: gr.update(visible=True),
            outputs=[menu_panel],
            queue=False,
        )

        def _close_menu():
            return gr.update(visible=False)

        for _button, _tab_elem_id in (
            (menu_overview, "ss-tab-overzicht"),
            (menu_chat, "ss-tab-chat"),
            (menu_memory, "ss-tab-geheugen"),
            (menu_sources, "ss-tab-bronnen"),
            (menu_verify, "ss-tab-controleren"),
            (menu_about, "ss-tab-uitleg"),
            (menu_more, "ss-tab-meer"),
        ):
            _button.click(
                _close_menu,
                outputs=[menu_panel],
                queue=False,
                js=(
                    f"() => {{ "
                    f"document.getElementById('{_tab_elem_id}-button')?.click(); "
                    f"window.scrollTo({{ top: 0, behavior: 'smooth' }}); "
                    f"}}"
                ),
            )

    return app
