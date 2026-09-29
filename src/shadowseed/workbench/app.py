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
.gradio-container { max-width: 1480px !important; margin: 0 auto; padding-top: 1.2rem !important; }
#product-hero {
  border: 1px solid var(--border-color-primary);
  border-radius: 22px;
  padding: 1.25rem 1.4rem;
  background: linear-gradient(135deg, rgba(255,255,255,.055), rgba(255,255,255,.015));
  box-shadow: 0 18px 50px rgba(0,0,0,.16);
  margin-bottom: 1rem;
}
#product-title { margin-bottom: 0.15rem; letter-spacing: -0.025em; }
#product-subtitle { opacity: 0.82; margin-bottom: .7rem; max-width: 980px; }
#journey { opacity: .9; font-size: .94rem; }
#chat-shell { min-height: 560px; }
#chat-status {
  font-size: 0.92rem;
  padding: .65rem .8rem;
  border-radius: 12px;
  background: var(--background-fill-secondary);
}
#authority-card {
  border: 1px solid var(--border-color-primary);
  border-radius: 20px;
  padding: 1rem 1rem .6rem 1rem;
  background: linear-gradient(145deg, var(--background-fill-secondary), rgba(255,255,255,.025));
}
#authority-profile-picker {
  margin-top: .45rem;
}
#authority-profile-picker label {
  border-radius: 14px !important;
}
#authority-explainer {
  margin-top: .55rem;
  padding: .7rem .8rem;
  border-radius: 12px;
  background: rgba(255,255,255,.035);
}
#setup-step {
  opacity: .68;
  font-size: .78rem;
  font-weight: 650;
  letter-spacing: .08em;
  text-transform: uppercase;
  margin-bottom: .15rem;
}
#advanced-setup {
  margin-top: .45rem;
}
.comparison-note { font-size: 0.9rem; opacity: 0.82; }
.section-kicker { opacity: .72; font-size: .9rem; }
#seed-story {
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: 1rem 1.05rem;
  min-height: 250px;
  background: linear-gradient(160deg, var(--background-fill-secondary), rgba(255,255,255,.018));
}
#seed-story h2 { margin-top: .15rem; }
#seed-story code { font-size: .84rem; }
#verify-callout {
  border: 1px solid var(--border-color-primary);
  border-radius: 16px;
  padding: .85rem 1rem;
  background: var(--background-fill-secondary);
}
#source-hero {
  border: 1px solid var(--border-color-primary);
  border-radius: 22px;
  padding: 1rem 1.1rem;
  background: linear-gradient(145deg, rgba(255,255,255,.055), rgba(255,255,255,.018));
  box-shadow: 0 14px 42px rgba(0,0,0,.12);
}
#source-result {
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: 1rem;
  min-height: 180px;
  background: var(--background-fill-secondary);
}
#about-hero {
  border: 1px solid var(--border-color-primary);
  border-radius: 24px;
  padding: 1.25rem 1.4rem;
  background: linear-gradient(145deg, rgba(255,255,255,.06), rgba(255,255,255,.018));
  box-shadow: 0 16px 48px rgba(0,0,0,.14);
  margin-bottom: 1rem;
}
#about-principle {
  border-left: 3px solid var(--border-color-primary);
  padding: .7rem 1rem;
  margin: .5rem 0 .85rem 0;
  background: rgba(255,255,255,.025);
  border-radius: 0 14px 14px 0;
}
.about-card {
  border: 1px solid var(--border-color-primary);
  border-radius: 18px;
  padding: .85rem 1rem;
  background: var(--background-fill-secondary);
  min-height: 190px;
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


def _authority_profile_markdown(profile_id: str | None, profiles: list[dict[str, Any]]) -> str:
    selected = next(
        (item for item in profiles if str(item.get("id")) == str(profile_id or "strict")),
        profiles[0] if profiles else {},
    )
    if not selected:
        return ""

    label = str(selected.get("label", profile_id or "Controlled"))
    description = str(selected.get("description", ""))
    validate = str(selected.get("validate_mode", "manual")).replace("_", " ")
    promote = str(selected.get("promote_mode", "gate")).replace("_", " ")
    contradiction = str(selected.get("contradiction_mode", "block")).replace("_", " ")

    return (
        f"**{label}**  \n{description}\n\n"
        f"Detect: **automatic** · Validate: **{validate}** · "
        f"Promote: **{promote}** · Contradictions: **{contradiction}**"
    )


def _status_markdown(view: dict[str, Any] | None) -> str:
    if not view:
        return "Create or open a chat to begin."
    seeds = list(view.get("seeds", []))
    promoted = sum(str(seed.get("status", "")).lower() == "promoted" for seed in seeds)
    mode = str(view.get("runtime_mode", "evaluation"))
    experience = "Live SSL" if mode == "live" else "Research evaluation"
    model = str(view.get("model_id") or view.get("backend") or "unknown")
    authority = str(view.get("authority_profile_id", "strict"))
    gate = str(view.get("effective_gate_policy_id", "unknown"))
    review_count = len(view.get("authority_review_seed_ids", []) or [])
    review = f" · **{review_count} need review**" if review_count else ""
    return (
        f"**{experience}** · model `{model}` · authority `{authority}` · "
        f"Gate `{gate}` · {int(view.get('turn', 0))} turns · "
        f"{len(seeds)} shadow seeds · {promoted} promoted{review}"
    )


def _shadow_overview_markdown(view: dict[str, Any] | None) -> str:
    if not view:
        return "Select a run to see its shadow memory."

    seeds = list(view.get("seeds", []))
    counts: dict[str, int] = {}
    for seed in seeds:
        status = str(seed.get("status", "unknown")).upper()
        counts[status] = counts.get(status, 0) + 1
    promoted = counts.get("PROMOTED", 0)
    blocked = sum(bool(seed.get("blocking", False)) for seed in seeds)
    used_ids: set[str] = set()
    for report in view.get("turn_reports", []):
        for seed_id in report.get("surfaced_seed_ids", []) or []:
            used_ids.add(str(seed_id))

    profile = str(view.get("authority_profile_id", "strict"))
    gate = str(view.get("effective_gate_policy_id", "unknown"))
    review_count = len(view.get("authority_review_seed_ids", []) or [])
    lifecycle = " · ".join(f"{name.title()} {count}" for name, count in sorted(counts.items()))
    if not lifecycle:
        lifecycle = "No seeds yet"

    return (
        f"**Authority:** `{profile}`  ·  **Gate:** `{gate}`  ·  **Seeds:** {len(seeds)}  ·  "
        f"**Promoted:** {promoted}  ·  **Used:** {len(used_ids)}  ·  **Blocked:** {blocked}  ·  "
        f"**Review:** {review_count}\n\n"
        f"{lifecycle}"
    )


def _control_overview_markdown(
    view: dict[str, Any] | None,
    profiles: list[dict[str, Any]],
) -> str:
    if not view:
        return (
            "## Control this run\n"
            "Select a run to see exactly how much authority Shadowseed has."
        )

    profile_id = str(view.get("authority_profile_id", "strict"))
    selected = next(
        (item for item in profiles if str(item.get("id")) == profile_id),
        {},
    )
    label = str(selected.get("label", profile_id))
    description = str(selected.get("description", ""))
    gate = str(view.get("effective_gate_policy_id", "unknown"))
    review_count = len(view.get("authority_review_seed_ids", []) or [])
    recurrence = (
        "automatic authority path"
        if bool(selected.get("auto_validate_recurrence", False))
        and gate == "exploratory"
        else "observed, but cannot raise authority by itself"
    )
    system_evidence = (
        "permitted only when an auditable producer and Gate policy accept it"
        if bool(selected.get("allow_unreviewed_system_evidence", False))
        else "must satisfy the normal verified-evidence boundary"
    )

    return (
        f"## {label}\n"
        f"{description}\n\n"
        f"**Effective Gate:** `{gate}`  \n"
        f"**Recurrence:** {recurrence}  \n"
        f"**System evidence:** {system_evidence}  \n"
        f"**Seeds currently asking for review:** {review_count}\n\n"
        "**Profile changes are run-level decisions.** This release does not silently "
        "change authority rules inside an existing run; create a new run when you "
        "want a different autonomy profile. Raw Gate and influence records remain "
        "available in Shadow and Verify."
    )


def _seed_story_markdown(view: dict[str, Any] | None) -> str:
    """Turn a technical seed snapshot into a compact human-readable lifecycle card."""

    if not view:
        return (
            "## Select a shadow seed\n"
            "Open a seed to see what Shadowseed noticed, why it has its current status, "
            "whether it has ever influenced an answer, and what you can do next."
        )

    status = str(view.get("status", "unknown")).upper()
    text = str(view.get("text", "")).strip() or "(empty seed)"
    evidence = int(view.get("evidence_count", 0) or 0)
    occurrences = int(view.get("occurrence_count", 0) or 0)
    weight = float(view.get("weight", 0.0) or 0.0)
    trace = float(view.get("trace", 0.0) or 0.0)
    blocking = bool(view.get("blocking", False))
    review_required = bool(view.get("review_required", False))
    timeline = list(view.get("timeline", []))
    influences = sum(str(item.get("type", "")) == "influence" for item in timeline)
    gate = dict(view.get("last_gate_event") or {})
    gate_decision = str(gate.get("decision") or "not yet")
    explanation = str(view.get("plain_explanation") or "")

    steps = [
        "Found ✓",
        f"Seen {occurrences}×",
        f"Evidence {evidence}",
        f"Gate {gate_decision}",
        f"Used {influences}×",
    ]

    if blocking:
        next_action = (
            "**Needs attention:** an open contradiction blocks this seed. Review the "
            "contradiction before resolving it."
        )
    elif review_required:
        next_action = (
            "**Review requested:** this seed has matured through recurrence, but the "
            "evidence-backed Gate still requires independently verified support before "
            "authority may increase."
        )
    elif status == "PROMOTED" and influences == 0:
        next_action = (
            "**Nothing required right now.** This seed is promoted. Shadowseed may use it "
            "later only when relevance and point-of-use checks allow it."
        )
    elif status == "PROMOTED":
        next_action = (
            "**Already used.** Open the audit trail to inspect the exact influence event(s) "
            "and the decision that allowed them."
        )
    elif evidence == 0:
        next_action = (
            "**Still developing.** You can leave it alone and let the lifecycle continue, "
            "or add independently verified support if your authority profile requires it."
        )
    else:
        next_action = (
            "**Still developing.** Evidence has been recorded, but the current Gate state "
            "does not yet authorize this seed for influence."
        )

    return (
        f"### {status}\n"
        f"## {text}\n\n"
        + "  ·  ".join(steps)
        + f"\n\n**Weight** {weight:.2f}  ·  **Trace** {trace:.2f}\n\n"
        + explanation
        + "\n\n"
        + next_action
    )


def _ingest_summary_markdown(result: dict[str, Any] | None) -> str:
    if not result:
        return (
            "## Feed the shadow memory\n"
            "Paste text or upload files. Shadowseed will inspect the content in chunks, "
            "record provenance and add candidate seeds without generating chat replies."
        )
    if result.get("error"):
        return f"**Could not process sources:** {result['error']}"

    source_names = ", ".join(result.get("source_names", [])) or "source"
    runtime = dict(result.get("authority_runtime") or {})
    gate = str(runtime.get("gate_policy_id", "unknown"))
    promoted = len(result.get("promoted_seed_ids", []) or [])
    review = len(result.get("authority_review_seed_ids", []) or [])
    return (
        "## Sources processed\n"
        f"**{int(result.get('sources', 0))}** source(s) · "
        f"**{int(result.get('chunks', 0))}** chunks · "
        f"**{int(result.get('characters', 0)):,}** characters  \n"
        f"Shadow memory: **{int(result.get('seeds_before', 0))} → "
        f"{int(result.get('seeds_after', 0))}** seeds · "
        f"**{int(result.get('new_seed_count', 0))}** new · "
        f"**{promoted}** promoted · **{review}** need review  \n"
        f"Gate: **{gate}**  \n\n"
        f"**Sources:** {source_names}\n\n"
        "Uploaded text is observation input, not trusted evidence. Seeds still follow the "
        "selected authority profile, Validation Gate and point-of-use checks."
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
    authority_profiles = ctl.authority_profiles()
    authority_choices = [
        (f"{item['label']} — {item['description']}", item["id"])
        for item in authority_profiles
    ]
    backend_choices = [
        ("Ollama — local model", "ollama"),
        ("OpenAI — hosted model", "openai"),
        ("Hugging Face Transformers — local model", "hf-transformers"),
        ("Offline demo — deterministic fixture", "fixture"),
    ]

    def explain_authority_profile(profile_id: str):
        return _authority_profile_markdown(profile_id, authority_profiles)

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
        authority_profile_id: str,
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
                authority_profile_id=authority_profile_id,
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
            return gr.update(choices=[], value=None), "Select a run to see its shadow memory."
        try:
            view = ctl.session_view(session_id)
            return dropdown_update(ctl.seed_choices(view)), _shadow_overview_markdown(view)
        except Exception as exc:
            return gr.update(), _error_text(exc)

    def control_session_changed(session_id: str | None):
        if not session_id:
            return _control_overview_markdown(None, authority_profiles)
        try:
            return _control_overview_markdown(
                ctl.session_view(session_id),
                authority_profiles,
            )
        except Exception as exc:
            return _error_text(exc)

    def inspect_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return _seed_story_markdown(None), None, None
        try:
            view = ctl.seed_view(session_id, seed_id)
            return _seed_story_markdown(view), view, view.get("timeline", [])
        except Exception as exc:
            error = {"error": f"{type(exc).__name__}: {exc}"}
            return f"**Could not inspect seed:** {error['error']}", error, None

    def falsify_seed(session_id: str | None, seed_id: str | None):
        if not session_id or not seed_id:
            return {"error": "Select a run and seed first."}, _seed_story_markdown(None), None, None
        try:
            result = ctl.falsify_seed(session_id, seed_id)
            view = ctl.seed_view(session_id, seed_id)
            return result, _seed_story_markdown(view), view, view.get("timeline", [])
        except Exception as exc:
            error = {"error": f"{type(exc).__name__}: {exc}"}
            return error, f"**Could not update seed:** {error['error']}", error, None

    def submit_verified_evidence(
        session_id: str | None,
        seed_id: str | None,
        source_ref: str,
        note: str,
        operator_verified: bool,
    ):
        if not session_id or not seed_id:
            return {"error": "Select a live run and seed first."}, _seed_story_markdown(None), None, None, "", False
        try:
            result = ctl.submit_verified_evidence(
                session_id,
                seed_id,
                source_ref=source_ref,
                note=note,
                operator_verified=bool(operator_verified),
            )
            view = ctl.seed_view(session_id, seed_id)
            return result, _seed_story_markdown(view), view, view.get("timeline", []), "", False
        except Exception as exc:
            error = {"error": f"{type(exc).__name__}: {exc}"}
            return error, f"**Could not add evidence:** {error['error']}", error, None, "", False

    def ingest_sources_ui(
        session_id: str | None,
        pasted_text: str,
        uploaded_files: list[str] | str | None,
        external_confirmed: bool,
    ):
        if not session_id:
            error = {"error": "Select or create a run first."}
            return _ingest_summary_markdown(error), None, gr.update(choices=[], value=None), ""
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
                external_confirmed=bool(external_confirmed),
            )
            view = result["session"]
            return (
                _ingest_summary_markdown(result),
                view,
                gr.update(choices=ctl.seed_choices(view), value=None),
                "",
            )
        except Exception as exc:
            error = {"error": f"{type(exc).__name__}: {exc}"}
            return _ingest_summary_markdown(error), None, gr.update(), pasted_text

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
        with gr.Group(elem_id="product-hero"):
            gr.Markdown("# Shadowseed", elem_id="product-title")
            gr.Markdown(
                "A learning shadow layer that notices candidate perspectives, lets them earn "
                "authority, and can bring them back when they are relevant later.",
                elem_id="product-subtitle",
            )
            gr.Markdown(
                "**Start → Run → Observe → Understand → Verify → Control → Inspect**  \n"
                "You can stay in normal chat, or open every seed, decision and raw JSON event when "
                "you want to check exactly what happened.",
                elem_id="journey",
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
                    gr.Markdown("### Start a new run")
                    gr.Markdown(
                        "Three choices are enough to begin. Everything technical stays available under Advanced.",
                        elem_classes=["section-kicker"],
                    )
                    title = gr.Textbox(label="Run name", value="New Shadowseed run")

                    gr.Markdown("Step 1 · Choose autonomy", elem_id="setup-step")
                    with gr.Group(elem_id="authority-card"):
                        authority_profile = gr.Radio(
                            choices=[(item["label"], item["id"]) for item in authority_profiles],
                            value="strict",
                            label="How much may Shadowseed do on its own?",
                            elem_id="authority-profile-picker",
                        )
                        authority_explainer = gr.Markdown(
                            _authority_profile_markdown("strict", authority_profiles),
                            elem_id="authority-explainer",
                        )

                    gr.Markdown("Step 2 · Choose the model", elem_id="setup-step")
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
                    gr.Markdown("Step 3 · Start, or tune Advanced settings", elem_id="setup-step")
                    with gr.Accordion("Advanced · relevance, embeddings and research controls", open=False, elem_id="advanced-setup"):
                        profile = gr.Dropdown(
                            choices=profile_choices,
                            value="balanced",
                            label="Relevance tuning",
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

            authority_profile.change(
                explain_authority_profile,
                inputs=[authority_profile],
                outputs=[authority_explainer],
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
                    authority_profile,
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



        with gr.Tab("Sources"):
            with gr.Row():
                with gr.Column(scale=2, min_width=560):
                    with gr.Group(elem_id="source-hero"):
                        gr.Markdown("## Feed Shadowseed")
                        gr.Markdown(
                            "Build shadow memory from material, not only from chat. Paste text or "
                            "upload multiple files; Shadowseed chunks and observes them without "
                            "turning every chunk into a chat message."
                        )
                        source_session = gr.Dropdown(
                            choices=initial_choices,
                            label="Run",
                            value=initial_choices[0][1] if initial_choices else None,
                        )
                        source_refresh = gr.Button("Refresh runs", variant="secondary")
                        source_paste = gr.Textbox(
                            label="Paste text",
                            placeholder="Paste an article, transcript, notes or a large text corpus...",
                            lines=10,
                        )
                        source_files = gr.File(
                            label="Upload files",
                            file_count="multiple",
                            type="filepath",
                            file_types=[".txt", ".md", ".markdown", ".json", ".csv"],
                        )
                        gr.Markdown(
                            "Supported now: **TXT, Markdown, JSON and CSV** · up to 25 MB per file. "
                            "PDF and DOCX will follow after their extraction path is made auditable.",
                            elem_classes=["section-kicker"],
                        )
                        source_hosted_confirm = gr.Checkbox(
                            label=(
                                "I understand source content may be sent to the hosted model or "
                                "embedding provider configured for this run"
                            ),
                            value=False,
                        )
                        ingest_button = gr.Button("Process into shadow memory", variant="primary")

                with gr.Column(scale=1, min_width=360):
                    source_result = gr.Markdown(
                        _ingest_summary_markdown(None),
                        elem_id="source-result",
                    )
                    with gr.Accordion("What happens to my upload?", open=False):
                        gr.Markdown(
                            "**Extract → chunk → detect candidate perspectives → cluster recurrence → "
                            "Gate → shadow memory.**\n\n"
                            "The upload itself does not become evidence or authority. You can inspect "
                            "every resulting seed in **Shadow**."
                        )
                    source_seed_preview = gr.Dropdown(
                        choices=[],
                        label="Seeds now in this run",
                        interactive=False,
                    )
                    source_session_json = gr.JSON(
                        label="Read-only run state",
                        visible=False,
                    )

            source_refresh.click(
                refresh_session_dropdown,
                inputs=[source_session],
                outputs=[source_session],
            )
            source_session.change(
                shadow_session_changed,
                inputs=[source_session],
                outputs=[source_seed_preview, source_result],
            )
            ingest_button.click(
                ingest_sources_ui,
                inputs=[source_session, source_paste, source_files, source_hosted_confirm],
                outputs=[
                    source_result,
                    source_session_json,
                    source_seed_preview,
                    source_paste,
                ],
            )

        with gr.Tab("Control"):
            gr.Markdown("## Authority and autonomy")
            gr.Markdown(
                "Authority profiles choose **how Shadowseed may move through the existing "
                "Gate and point-of-use pipeline**. They never create a second Gate."
            )
            with gr.Row():
                control_session = gr.Dropdown(
                    choices=initial_choices,
                    label="Run",
                    value=initial_choices[0][1] if initial_choices else None,
                )
                control_refresh = gr.Button("Refresh runs", variant="secondary")
            control_overview = gr.Markdown(
                _control_overview_markdown(None, authority_profiles),
                elem_id="source-result",
            )
            with gr.Accordion("Compare the four profiles", open=False):
                gr.Markdown(
                    "**Controlled** — verified authority support stays user-controlled.  \n"
                    "**Assisted** — mature recurrence is detected and surfaced for review; "
                    "verified support still decides authority.  \n"
                    "**Autonomous** — recurrence may earn authority through the exploratory "
                    "Gate and later surface when relevant.  \n"
                    "**Open research** — same auditable Gate path with the least restrictive "
                    "research permissions; unreviewed system evidence still requires an explicit "
                    "producer and a policy that accepts it."
                )

            control_refresh.click(
                refresh_session_dropdown,
                inputs=[control_session],
                outputs=[control_session],
            )
            control_session.change(
                control_session_changed,
                inputs=[control_session],
                outputs=[control_overview],
            )

        with gr.Tab("About SSL"):
            with gr.Group(elem_id="about-hero"):
                gr.Markdown("## Shadow Seed Learning, explained")
                gr.Markdown(
                    "SSL is an **external, inspectable experience layer around an LLM**. "
                    "It watches for potentially missing perspectives, stores them as shadow seeds, "
                    "lets those seeds earn or lose authority over time, and may bring an authorized "
                    "seed back when it becomes relevant later."
                )
                gr.Markdown(
                    "**One sentence:** Shadowseed remembers *what may have been missing*, not just "
                    "what was said, and keeps the entire path to later influence inspectable.",
                    elem_id="about-principle",
                )
                gr.Markdown(
                    "**Observe → Seed → Recur / Evidence → Validate → Promote → Relevance → Influence**"
                )

            with gr.Row():
                with gr.Column():
                    gr.Markdown(
                        "### What SSL does\n"
                        "- detects candidate missing perspectives\n"
                        "- gives each candidate a traceable lifecycle\n"
                        "- tracks recurrence, evidence and contradictions\n"
                        "- separates authority from relevance\n"
                        "- uses a Validation Gate before authority increases\n"
                        "- checks relevance again when a later question arrives\n"
                        "- records whether a seed actually surfaced",
                        elem_classes=["about-card"],
                    )
                with gr.Column():
                    gr.Markdown(
                        "### What SSL does not do\n"
                        "- it does **not** retrain the LLM weights\n"
                        "- a seed is **not** automatically a fact\n"
                        "- PROMOTED does **not** mean USED\n"
                        "- uploaded text is **not** automatically trusted evidence\n"
                        "- two different answers do **not** prove SSL influence\n"
                        "- more text does **not** automatically mean better memory",
                        elem_classes=["about-card"],
                    )

            with gr.Accordion("1 · Why add a shadow layer to an LLM?", open=True):
                gr.Markdown(
                    "A normal LLM answers from its trained weights, the current prompt and the "
                    "context it can currently see. SSL adds a separate persistent layer that can "
                    "track candidate omissions, alternative frames and recurring missing context "
                    "across time. The LLM remains the language model; SSL is the memory, authority "
                    "and selective-surfacing layer around it.\n\n"
                    "The goal is not to remember everything. The goal is to remember a small number "
                    "of potentially useful perspectives **with a history attached to them**."
                )

            with gr.Accordion("2 · What exactly is a shadow seed?", open=False):
                gr.Markdown(
                    "A shadow seed is a **hypothesis or candidate perspective**, not an instruction "
                    "and not a truth claim. A seed can accumulate an embedding, recurrence count, "
                    "trace, evidence, contradictions, Gate decisions, authority versions, provenance "
                    "and a record of whether it ever surfaced.\n\n"
                    "That history is what makes a seed different from simply adding another sentence "
                    "to the prompt."
                )

            with gr.Accordion("3 · The lifecycle, step by step", open=False):
                gr.Markdown(
                    "**Observe** — SSL detects a possible missing perspective in a chat turn or source chunk.\n\n"
                    "**Seed** — the candidate is stored as a traceable shadow seed.\n\n"
                    "**Recur / Evidence** — the same idea may reappear semantically, gain support or be challenged.\n\n"
                    "**Validate** — configured signals are evaluated by the Validation Gate.\n\n"
                    "**Promote** — a seed that satisfies policy becomes eligible for later use.\n\n"
                    "**Relevance** — on a later question, promoted seeds are compared with the current need.\n\n"
                    "**Influence** — only an authorized and relevant seed may be surfaced as bounded "
                    "candidate context for answer generation."
                )

            with gr.Accordion("4 · Authority is not the same as relevance", open=False):
                gr.Markdown(
                    "This is one of the most important SSL ideas. A seed can be **relevant but not "
                    "authorized**, or **authorized but irrelevant** to the current question. Only a "
                    "seed that satisfies both sides should normally influence a response.\n\n"
                    "That is why a promoted seed can sit silently in shadow memory for many turns. "
                    "Promotion means *eligible*, not *always inject this idea*."
                )

            with gr.Accordion("5 · The Validation Gate and contradictions", open=False):
                gr.Markdown(
                    "The Validation Gate protects the jump from observation to authority. It records "
                    "which signals were considered, under which policy, and what state or weight "
                    "change followed. Contradictions are first-class signals too: they may weaken, "
                    "block or require explicit resolution of a seed.\n\n"
                    "**Design principle:** authority decisions may become automated, but they should "
                    "never become invisible."
                )

            with gr.Accordion("6 · Is this training or fine-tuning?", open=False):
                gr.Markdown(
                    "**No, not in the classic ML sense.** Fine-tuning changes model weights. SSL "
                    "keeps its experience outside those weights. The same base LLM can therefore "
                    "remain unchanged while its Shadowseed memory becomes different over time.\n\n"
                    "Two installations using the same model can diverge because they processed "
                    "different conversations or corpora. That is better described as **inspectable "
                    "experience accumulation** than as ordinary training."
                )

            with gr.Accordion("7 · How is SSL different from RAG?", open=False):
                gr.Markdown(
                    "RAG typically begins with the current question and retrieves source material "
                    "that appears relevant. SSL begins earlier: it builds a persistent history of "
                    "candidate perspectives that were previously missing, recurring, supported or "
                    "contradicted.\n\n"
                    "**RAG:** question → retrieve material → answer  \n"
                    "**SSL:** observe → develop seed → authorize → later surface when relevant → answer\n\n"
                    "The two approaches can complement each other."
                )

            with gr.Accordion("8 · What happens when I upload lots of text?", open=False):
                gr.Markdown(
                    "The **Sources** workspace follows a separate non-chat path: **extract → chunk → "
                    "detect → cluster / recur → Gate → shadow memory**. Uploaded chunks do not become "
                    "fake chat turns and the upload itself is not automatically treated as trusted evidence.\n\n"
                    "With large corpora, useful differentiation comes from selection over time: many "
                    "candidates may disappear, some recur, some are contradicted, some are promoted, "
                    "and only a small subset should ever surface.\n\n"
                    "**More text is only useful when memory hygiene works:** deduplication, clustering, "
                    "provenance, contradiction handling, decay and selective surfacing."
                )

            with gr.Accordion("9 · Controlled, Assisted, Autonomous and Open research", open=False):
                gr.Markdown(
                    "**Controlled** is the backwards-compatible mode: authority-bearing evidence "
                    "remains user-controlled.\n\n"
                    "**Assisted** is intended to automate low-risk lifecycle work and ask when a true "
                    "authority decision still needs confirmation.\n\n"
                    "**Autonomous** is intended to let SSL validate, promote and surface automatically "
                    "where provenance, policy, Gate and point-of-use checks allow.\n\n"
                    "**Open research** is intended for the least restrictive experimental runs while "
                    "retaining provenance and audit records.\n\n"
                    "**0.8.0:** Controlled preserves the previous production behavior. Assisted "
                    "review semantics and Autonomous/Open recurrence authority are wired through "
                    "the canonical Gate. Machine-generated evidence still requires an explicit, "
                    "auditable producer and is never invented by the profile itself."
                )

            with gr.Accordion("10 · How can I prove SSL actually influenced an answer?", open=False):
                gr.Markdown(
                    "Do **not** judge this from wording differences alone. Two stochastic generations "
                    "can differ even when no seed surfaced.\n\n"
                    "A proper check asks: Was the seed promoted? Was it eligible? Was it selected? "
                    "Did it actually surface? Did the point-of-use check authorize it?\n\n"
                    "Use **Shadow** for the lifecycle, **Verify** for SSL-on / SSL-off attribution, "
                    "and **Technical inspection** for the exact JSON, Gate events, trace, relevance "
                    "and influence records."
                )

            with gr.Accordion("11 · A concrete example", open=False):
                gr.Markdown(
                    "Suppose repeated discussion about AI policy keeps underweighting long-term "
                    "implementation costs. SSL detects that as a candidate seed. Later the idea "
                    "recurs, gains support and passes the Gate. Weeks later the user asks about the "
                    "cost of scaling the policy. The promoted seed is now relevant and may surface.\n\n"
                    "If the next question is about the weather, the same promoted seed should stay "
                    "silent. That is the point of selective surfacing."
                )

            with gr.Accordion("12 · What can I inspect?", open=False):
                gr.Markdown(
                    "For an important seed you should be able to answer: **What was noticed? Where "
                    "did it come from? How often did it recur? What supports or contradicts it? Why "
                    "does it have this status? Which Gate event changed its authority? Has it ever "
                    "surfaced? Which answer did it influence? Why was it relevant then?**\n\n"
                    "The human-readable interface and the raw JSON are two views of the same event "
                    "history."
                )

            with gr.Accordion("13 · Limits and non-claims", open=False):
                gr.Markdown(
                    "SSL does not make every answer correct. It does not guarantee seeds are true, "
                    "does not make uploaded documents trustworthy, does not remove normal LLM "
                    "uncertainty, and does not automatically improve just because it has seen more "
                    "text. Its value depends on detection quality, memory hygiene, evidence, "
                    "contradiction handling, authority policy and point-of-use selection."
                )

            with gr.Accordion("14 · Mini glossary", open=False):
                gr.Markdown(
                    "**Shadow seed** — traceable candidate perspective or missing-context hypothesis.\n\n"
                    "**Shadow memory** — persistent collection of seeds and lifecycle state.\n\n"
                    "**Trace** — a decaying lifecycle measure.\n\n"
                    "**Validation Gate** — policy boundary that decides whether signals may change authority.\n\n"
                    "**Promoted** — authorized enough to become eligible for later use.\n\n"
                    "**Surfacing** — selecting an authorized seed as candidate context for a later turn.\n\n"
                    "**Point of use** — final decision point before a seed may influence generation.\n\n"
                    "**Authority profile** — configuration determining which lifecycle actions are manual, "
                    "assisted or automated."
                )

        with gr.Tab("Shadow"):
            gr.Markdown("## What is Shadowseed seeing?")
            gr.Markdown(
                "Seeds are candidate perspectives, not facts. The normal view explains the "
                "lifecycle in plain language; the exact JSON and audit events remain one click away."
            )
            with gr.Row():
                shadow_session = gr.Dropdown(choices=initial_choices, label="Run")
                shadow_refresh = gr.Button("Refresh", variant="secondary")
            shadow_status = gr.Markdown("Select a run to see its shadow memory.", elem_id="chat-status")

            with gr.Row():
                with gr.Column(scale=1, min_width=320):
                    seed_select = gr.Dropdown(choices=[], label="Shadow seed")
                    inspect_button = gr.Button("Open seed", variant="primary")
                    with gr.Accordion("Intervene manually", open=False):
                        gr.Markdown(
                            "You do not need to operate every seed. Use these controls only when "
                            "you intentionally want to add evidence or challenge a seed."
                        )
                        falsify_button = gr.Button("Mark seed contradicted", variant="stop")
                        falsify_result = gr.JSON(label="Contradiction result")
                with gr.Column(scale=2, min_width=560):
                    seed_story = gr.Markdown(_seed_story_markdown(None), elem_id="seed-story")
                    with gr.Accordion("Technical inspection · JSON and events", open=False):
                        with gr.Row():
                            seed_json = gr.JSON(label="Raw seed JSON")
                            seed_timeline = gr.JSON(label="Raw audit timeline")

            with gr.Accordion("Add independently verified support", open=False):
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
                outputs=[seed_story, seed_json, seed_timeline],
            )
            seed_select.change(
                inspect_seed,
                inputs=[shadow_session, seed_select],
                outputs=[seed_story, seed_json, seed_timeline],
            )
            falsify_button.click(
                falsify_seed,
                inputs=[shadow_session, seed_select],
                outputs=[falsify_result, seed_story, seed_json, seed_timeline],
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
                outputs=[
                    evidence_result,
                    seed_story,
                    seed_json,
                    seed_timeline,
                    evidence_source,
                    evidence_attest,
                ],
            )


        with gr.Tab("Verify"):
            gr.Markdown("## Verify what Shadowseed actually changed")
            gr.Markdown(
                "A textual difference between two model generations is not proof of Shadowseed "
                "influence. This view exposes the paired control and the stored attribution record."
            )
            with gr.Group(elem_id="verify-callout"):
                gr.Markdown(
                    "**How to read this**  \n"
                    "1. Choose a run and turn.  \n"
                    "2. Load the stored SSL-on / SSL-off comparison.  \n"
                    "3. Check whether an authorized seed actually surfaced.  \n"
                    "4. Only then may a difference be attributed to Shadowseed."
                )
            verify_session = gr.Dropdown(choices=initial_choices, label="Run")
            verify_refresh = gr.Button("Refresh runs", variant="secondary")
            verify_turn = gr.Number(value=0, precision=0, label="Turn index")
            with gr.Row():
                verify_blind = gr.Checkbox(label="Blind A/B", value=False)
                verify_reveal = gr.Checkbox(label="Reveal mapping", value=True)
            verify_button = gr.Button("Verify turn", variant="primary")
            verify_result = gr.JSON(label="Verification record")

            verify_refresh.click(
                refresh_session_dropdown,
                inputs=[verify_session],
                outputs=[verify_session],
            )
            verify_button.click(
                advanced_compare,
                inputs=[verify_session, verify_turn, verify_blind, verify_reveal],
                outputs=[verify_result],
            )

        with gr.Tab("Feedback and export"):
            feedback_session = gr.Dropdown(choices=initial_choices, label="Chat")
            feedback_refresh = gr.Button("Refresh chats")
            gr.Markdown(
                "Tester feedback is record-only. It never changes seed weight, promotion, or Gate authority."
            )
            turn_index = gr.Number(value=0, precision=0, label="Turn index")
            overall = gr.Dropdown(
                choices=["better", "neutral", "worse"],
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
