from __future__ import annotations

from pathlib import Path

from shadowseed.workbench.feature_help import render_feature_help
from shadowseed.workbench.simple_app_vnext import _ollama_note, _ui_error
from shadowseed.workbench.simple_app import (
    _authority_explainer,
    _chat_status,
    _dashboard_summary,
    _embedding_explainer,
    _gate_notice,
    _legacy_control_summary,
    _memory_overview,
    _seed_story,
    _verify_summary,
    _control_preset_values,
    _control_state_summary,
    _recommended_setup,
    _source_summary,
    _ssl_intensity_explainer,
    _gate_strictness_explainer,
)


class _NoLocalModels:
    @staticmethod
    def discover_models(_backend: str) -> list[str]:
        return []


class _LocalModel:
    @staticmethod
    def discover_models(_backend: str) -> list[str]:
        return ["qwen3:8b", "llama3.2:3b"]


def test_default_workbench_is_dutch_chat_first_surface() -> None:
    app_source = Path("src/shadowseed/workbench/app.py").read_text(encoding="utf-8")
    vnext_source = Path("src/shadowseed/workbench/simple_app_vnext.py").read_text(
        encoding="utf-8"
    )

    assert "from shadowseed.workbench.simple_app_vnext import build_vnext_app" in app_source
    assert "return build_vnext_app(workspace, controller=controller)" in app_source

    for label in (
        'with gr.Tab("Chat")',
        'with gr.Tab("Shadow")',
        'with gr.Tab("Bronnen")',
        'with gr.Tab("Onderzoek")',
        'label="Vergelijk dit antwoord zonder SSL"',
        'gr.Button("Versturen"',
        'gr.Button("Start nieuwe chat"',
    ):
        assert label in vnext_source

    for normal_ui_control in (
        'label="SSL-invloed"',
        'label="Validation Gate"',
        'label="Zelfversterking · experimenteel"',
        'label="Wat wil je vergelijken?"',
    ):
        assert normal_ui_control not in vnext_source

    for refresh_label in (
        '"Vernieuwen"',
        '"Gesprekken vernieuwen"',
        '"Geheugen vernieuwen"',
        '"Refresh chats"',
        '"Refresh runs"',
    ):
        assert refresh_label not in vnext_source


def test_vnext_ollama_note_makes_embedding_dependency_explicit() -> None:
    missing = _ollama_note(["qwen3:8b"], "qwen3:8b")
    ready = _ollama_note(["qwen3:8b", "embeddinggemma:latest"], "qwen3:8b")

    assert "ollama pull embeddinggemma" in missing
    assert "Semantisch matchen gebruikt lokaal" in ready
    assert "ollama pull embeddinggemma" not in ready


def test_vnext_error_text_redacts_known_secrets(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret-value-123456")
    rendered = _ui_error(
        RuntimeError("Authorization: Bearer sk-test-secret-value-123456")
    )

    assert "sk-test-secret-value-123456" not in rendered
    assert "<redacted-secret>" in rendered


def test_vnext_callback_failures_preserve_user_input() -> None:
    source = Path("src/shadowseed/workbench/simple_app_vnext.py").read_text(
        encoding="utf-8"
    )

    evidence_start = source.index("    def submit_verified_evidence(")
    ingest_start = source.index("    def ingest(", evidence_start)
    evidence_body = source[evidence_start:ingest_start]
    assert "except Exception as exc:" in evidence_body
    assert "note," in evidence_body
    assert "attested," in evidence_body
    assert '""' in evidence_body
    assert "False" in evidence_body

    ingest_start = source.index("    def ingest(")
    research_start = source.index("    def run_longitudinal_comparison(", ingest_start)
    ingest_body = source[ingest_start:research_start]
    assert "except Exception as exc:" in ingest_body
    assert "pasted," in ingest_body
    assert "sanitized_exception_line(exc)" in ingest_body

    send_start = source.index("    def send(")
    inspect_start = source.index("    def inspect_seed(", send_start)
    send_body = source[send_start:inspect_start]
    assert "except Exception as exc:" in send_body
    assert "question," in send_body


def test_vnext_keeps_longitudinal_ab_in_research_only() -> None:
    source = Path("src/shadowseed/workbench/simple_app_vnext.py").read_text(
        encoding="utf-8"
    )

    send_start = source.index("    def send(")
    inspect_start = source.index("    def inspect_seed(", send_start)
    send_body = source[send_start:inspect_start]
    assert 'comparison_mode="authorized"' in send_body
    assert 'comparison_mode="longitudinal"' not in send_body

    research_start = source.index("    def run_longitudinal_comparison(")
    blocks_start = source.index("    with gr.Blocks(", research_start)
    research_body = source[research_start:blocks_start]
    assert 'comparison_mode="longitudinal"' in research_body
    assert "eerdere userbeurt(en) opnieuw opgebouwd" in research_body

    research_tab = source.index('with gr.Tab("Onderzoek")')
    research_binding = source.index("research_run.click(", research_tab)
    assert research_tab < research_binding
    assert 'label="Onderzoeksvraag"' in source[research_tab:research_binding]
    assert "Voer longitudinale vanilla-vergelijking uit" in source[research_tab:research_binding]


def test_vnext_every_normal_function_has_contextual_info_binding() -> None:
    source = Path("src/shadowseed/workbench/simple_app_vnext.py").read_text(
        encoding="utf-8"
    )

    for feature_id in (
        "conversation",
        "new_chat",
        "model",
        "external_consent",
        "send",
        "compare",
        "shadow",
        "contradiction",
        "verified_support",
        "sources",
        "research",
    ):
        assert f'"{feature_id}"' in source

    assert "render_feature_help" in source
    assert "help_feature = gr.State" in source
    assert 'gr.Button("ⓘ"' in source or 'gr.Button("ⓘ ' in source


def test_feature_help_preserves_ssl_semantics_and_explains_combinations() -> None:
    view = {
        "backend": "ollama",
        "effective_gate_policy_id": "evidence_backed",
        "authority_profile_id": "strict",
        "allow_self_reinforcement": False,
    }
    seed = {
        "blocking": True,
        "current_gate_authorized": True,
    }

    text = render_feature_help(
        "verified_support",
        view=view,
        compare_enabled=True,
        provider="ollama",
        hosted_confirmed=False,
        seed=seed,
    )

    assert "Alsof je 8 bent" in text
    assert "Wat doet dit echt?" in text
    assert "Wat doet dit níet?" in text
    assert "Samen met andere functies" in text
    assert "Huidige combinatie" in text
    assert "versterken" in text.lower()
    assert "niet automatisch waar" in text.lower()
    assert "open contradiction" in text
    assert "geblokkeerd" in text.lower()
    assert "één extra control-generatie" in text


def test_feature_help_distinguishes_self_reinforcement_on_and_off() -> None:
    off = render_feature_help(
        "self_reinforcement",
        view={
            "effective_gate_policy_id": "evidence_backed",
            "authority_profile_id": "strict",
            "allow_self_reinforcement": False,
        },
    )
    on = render_feature_help(
        "self_reinforcement",
        view={
            "effective_gate_policy_id": "evidence_backed",
            "authority_profile_id": "strict",
            "allow_self_reinforcement": True,
        },
    )

    assert "Self-reinforcement staat uit" in off
    assert "niet teruggevoerd" in off
    assert "Self-reinforcement staat aan" in on
    assert "versterken" in on.lower()


def test_simple_start_automatically_prefers_local_model_then_safe_demo() -> None:
    backend, model, note = _recommended_setup(_LocalModel())
    assert backend == "ollama"
    assert model == "qwen3:8b"
    assert "Automatisch gekozen" in note

    backend, model, note = _recommended_setup(_NoLocalModels())
    assert backend == "fixture"
    assert model is None
    assert "offline demomodel" in note


def test_visible_authority_language_is_plain_dutch() -> None:
    safe = _authority_explainer("strict")
    autonomous = _authority_explainer("autonomous")

    assert "**Veilig**" in safe
    assert "observeert automatisch" in safe
    assert "**Zelfstandig**" in autonomous
    assert "terugkerende patronen" in autonomous.lower()


def test_chat_status_shows_simple_slider_state_without_policy_jargon() -> None:
    status = _chat_status(
        {
            "backend": "fixture",
            "authority_profile_id": "assisted",
            "effective_gate_policy_id": "evidence_backed",
            "ssl_intensity": 80,
            "gate_strictness": 70,
            "turn": 4,
            "authority_review_seed_ids": ["ss_2"],
            "seeds": [
                {"status": "PROMOTED", "blocking": False},
                {"status": "ACTIVE", "blocking": False},
            ],
        }
    )

    assert "4 bericht(en)" in status
    assert "SSL **80%**" in status
    assert "Gate **70%**" in status
    assert "2 geheugenpunt(en)" in status
    assert "1 mag later meedenken" in status
    assert "1 vraagt controle" in status
    assert "evidence_backed" not in status


def test_source_summary_explains_result_without_treating_upload_as_truth() -> None:
    text = _source_summary(
        {
            "sources": 2,
            "chunks": 7,
            "new_seed_count": 4,
            "promoted_seed_ids": ["ss_1"],
            "authority_review_seed_ids": ["ss_2"],
            "source_names": ["rapport.md", "data.csv"],
        }
    )

    assert "2** bron(nen)" in text
    assert "7** tekstdeel/delen" in text
    assert "4** nieuwe geheugenpunten" in text
    assert "wordt niet automatisch waarheid of bewijs" in text



def test_dashboard_supports_progressive_disclosure_and_drilldown() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert "def _dashboard_summary" in source
    assert 'label="Geheugenpunt"' in source
    assert 'gr.Button("Open detail"' in source
    assert 'with gr.Accordion("Technische audit van dit punt", open=False)' in source
    assert 'elem_classes=["ss-metric"]' in source
    assert 'elem_classes=["ss-detail"]' in source



def test_sliders_explain_two_independent_dimensions() -> None:
    ssl_off = _ssl_intensity_explainer(0)
    ssl_full = _ssl_intensity_explainer(100)
    gate_open = _gate_strictness_explainer(0)
    gate_strict = _gate_strictness_explainer(100)

    assert "SSL-invloed 0%" in ssl_off
    assert "leert wel" in ssl_off
    assert "SSL-invloed 100%" in ssl_full
    assert "Validation Gate 0%" in gate_open
    assert "eerste waarneming" in gate_open
    assert "Validation Gate 100%" in gate_strict
    assert "vier keer" in gate_strict
    assert "drie onafhankelijke" in gate_strict

    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")
    assert 'label="SSL-invloed"' in source
    assert 'label="Validation Gate"' in source
    assert 'step=10' in source



def test_self_reinforcement_is_explicit_experimental_toggle() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert 'label="Zelfversterking · experimenteel"' in source
    assert "Laat SSL-beïnvloede antwoorden de geheugenlus opnieuw voeden." in source
    assert "feedbacklus" in source.lower()



def test_dashboard_preserves_custom_slider_labels() -> None:
    headline, *_rest = _dashboard_summary(
        {
            "title": "Legacy",
            "backend": "fixture",
            "ssl_intensity": None,
            "gate_strictness": None,
            "allow_self_reinforcement": False,
            "turn": 0,
            "authority_review_seed_ids": [],
            "seeds": [],
            "turn_reports": [],
        }
    )

    assert "SSL **aangepast**" in headline
    assert "Gate **aangepast**" in headline
    assert "SSL **0%**" not in headline
    assert "Gate **0%**" not in headline



def test_modern_workbench_visual_contract() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert "position: sticky" in source
    assert "#ss-composer" in source
    assert ".ss-control-card" in source
    assert ".ss-regie-summary" in source
    assert "@media (max-width: 900px)" in source
    assert "theme=gr.themes.Soft()" in source
    assert 'label="Snelle stand"' in source
    assert 'with gr.Accordion("Model en geavanceerd", open=False)' in source


def test_control_presets_make_complex_regimes_one_click() -> None:
    assert _control_preset_values("observeren") == (0, 100, False)
    assert _control_preset_values("gebalanceerd") == (60, 70, False)
    assert _control_preset_values("vrij") == (100, 0, True)
    assert _control_preset_values("strikt") == (100, 100, False)

    assert "Observeren" in _control_state_summary(0, 100, False)
    assert "Vrij experiment" in _control_state_summary(100, 0, True)
    assert "Strikt" in _control_state_summary(100, 100, False)



def test_markdown_uses_real_line_break_escapes_and_user_only_control_events() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert "\\\\n" not in source
    assert "control_preset.input(" in source
    assert "ssl_intensity.input(" in source
    assert "gate_strictness.input(" in source
    assert "allow_self_reinforcement.input(" in source
    assert "control_preset.change(" not in source
    assert "ssl_intensity.change(" not in source
    assert "gate_strictness.change(" not in source
    assert "allow_self_reinforcement.change(" not in source



def test_regie_controls_are_bound_to_selected_session() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert "ctl.update_session_controls(" in source
    assert "inputs=[session_select, control_preset]" in source
    assert "session_select," in source
    assert "def _control_view_state(" in source
    assert "initial_ssl" in source
    assert "initial_gate" in source
    assert "initial_loop" in source



def test_loop_toggle_uses_loop_only_backend_update() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    start = source.index("def update_loop_control(")
    end = source.index("def create_chat(", start)
    body = source[start:end]

    assert "ctl.update_session_self_reinforcement(" in body
    assert "ctl.update_session_controls(" not in body
    assert "SSL- en Gate-instellingen blijven ongewijzigd" in body



def test_menu_navigation_is_packaged_with_default_workbench() -> None:
    simple = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")
    production = Path("src/shadowseed/workbench/production_local.py").read_text(
        encoding="utf-8"
    )
    standalone = Path("src/shadowseed/workbench/standalone.py").read_text(
        encoding="utf-8"
    )

    assert 'gr.Button("☰ Menu"' in simple
    for elem_id in (
        "ss-tab-overzicht",
        "ss-tab-chat",
        "ss-tab-geheugen",
        "ss-tab-bronnen",
        "ss-tab-controleren",
        "ss-tab-uitleg",
        "ss-tab-meer",
    ):
        assert f'"{elem_id}"' in simple
    assert "{_tab_elem_id}-button" in simple

    # The packaged launcher -> production-local shell -> default build_app chain
    # must keep using the Dutch Workbench rather than a separate legacy UI.
    assert "workbench = build_app(controller=ctl)" in production
    assert "launch_production_local_workbench" in standalone



def test_initial_custom_regie_summary_is_not_strict() -> None:
    summary = _legacy_control_summary(False)

    assert "Aangepaste/legacy-regie" in summary
    assert "feedbacklus **uit**" in summary
    assert "**Strikt**" not in summary

    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")
    assert "initial_control_summary" in source
    assert "control_summary = gr.Markdown(" in source


def test_shadow_pressure_verification_is_explicitly_pre_authority() -> None:
    summary = _verify_summary(
        {
            "comparison_mode": "shadow_pressure",
            "ssl_influence_observed": True,
            "surfaced_seed_ids": ["ss_pre_1", "ss_pre_2"],
            "question": "Wat verandert er?",
        }
    )

    assert "pre-authority" in summary
    assert "nog niet-gepromoveerde" in summary
    assert "geen Gate-geautoriseerde" in summary



def test_shadow_pressure_mode_is_exposed_in_chat_ui() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert '"Shadow pressure · pre-promotie experiment", "shadow_pressure"' in source
    assert 'label="Wat wil je vergelijken?"' in source
    assert "comparison_mode=comparison_mode or \"authorized\"" in source
    assert "comparison_mode," in source


def test_embedding_choices_explain_meaning_and_privacy() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert '("Automatisch · aanbevolen", "auto")' in source
    assert '("Slim lokaal · vergelijkt betekenis", "sentence-transformers")' in source
    assert '("Snel lokaal · vergelijkt woorden", "lexical")' in source
    assert '("Online · OpenAI vergelijkt betekenis", "openai")' in source
    assert "embedding_backend.change(" in source
    assert "outputs=[embedding_help]" in source
    assert "online taalmodel of online " in source

    assert "stuurt geen tekst naar een online provider" in _embedding_explainer(
        "sentence-transformers"
    )
    assert "naar OpenAI gestuurd" in _embedding_explainer("openai")


def test_gate_review_notice_is_actionable_and_wired() -> None:
    view = {
        "authority_review_seed_ids": ["ss_1"],
        "seeds": [{"id": "ss_1", "text": "Een mogelijk ontbrekend perspectief."}],
    }
    notice = _gate_notice(view)

    assert "Validation Gate vraagt jouw beoordeling" in notice
    assert "Een mogelijk ontbrekend perspectief." in notice
    assert "open **Geheugen**" in notice
    assert "niets opnieuw te draaien" in notice

    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")
    assert "gate_alert = gr.Markdown(" in source
    assert "_gate_notice(initial_view)" in source
    assert "source_gate_alert = gr.Markdown(" in source
    assert 'gr.Warning("Validation Gate vraagt jouw beoordeling.")' in source



def test_manual_review_actions_refresh_gate_alerts() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    falsify_start = source.index("def falsify_seed(")
    evidence_start = source.index("def submit_verified_evidence(", falsify_start)
    verify_start = source.index("def verify_turn(", evidence_start)

    falsify_body = source[falsify_start:evidence_start]
    evidence_body = source[evidence_start:verify_start]

    assert "session_view = ctl.session_view(session_id)" in falsify_body
    assert "notice = _gate_notice(session_view)" in falsify_body
    assert "session_view = ctl.session_view(session_id)" in evidence_body
    assert "notice = _gate_notice(session_view)" in evidence_body

    assert "gate_alert," in source
    assert "source_gate_alert," in source



def test_historical_promotion_is_not_presented_as_current_influence() -> None:
    view = {
        "title": "Tightened Gate",
        "backend": "fixture",
        "ssl_intensity": 100,
        "gate_strictness": 100,
        "turn": 2,
        "authority_review_seed_ids": [],
        "turn_reports": [],
        "seeds": [
            {
                "id": "ss_legacy",
                "text": "Historically promoted perspective.",
                "status": "PROMOTED",
                "blocking": False,
                "current_gate_authorized": False,
                "occurrence_count": 1,
                "evidence_count": 0,
            }
        ],
    }

    status = _chat_status(view)
    memory = _memory_overview(view)
    _headline, _conversation, dashboard_memory, _authority, attention = _dashboard_summary(view)

    assert "1 mag later meedenken" not in status
    assert "historisch promoted, nu niet toegelaten" in status
    assert "**0** mag meedenken" in memory
    assert "historisch promoted, nu niet toegelaten" in memory
    assert "0 mag meedenken" in dashboard_memory
    assert "historisch promoted" in dashboard_memory
    assert "Gate is aangescherpt" in attention


def test_seed_detail_labels_historical_promotion_separately() -> None:
    story = _seed_story(
        {
            "id": "ss_legacy",
            "text": "Historically promoted perspective.",
            "status": "PROMOTED",
            "blocking": False,
            "current_gate_authorized": False,
            "review_required": False,
            "occurrence_count": 1,
            "evidence_count": 0,
            "timeline": [],
        }
    )

    assert "Historisch promoted · nu niet toegelaten" in story
    assert "kan nu niet meedenken" in story



def test_regie_updates_refresh_gate_alert_immediately() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    persist_start = source.index("def _persist_controls(")
    preset_start = source.index("def apply_control_preset(", persist_start)
    persist_body = source[persist_start:preset_start]

    assert "notice = _gate_notice(view)" in persist_body
    assert 'gr.Warning("Validation Gate vraagt jouw beoordeling.")' in persist_body
    assert "return _chat_status(view), view, notice" in persist_body

    for callback in (
        "control_preset.input(",
        "ssl_intensity.input(",
        "gate_strictness.input(",
        "allow_self_reinforcement.input(",
    ):
        start = source.index(callback)
        block = source[start : min(len(source), start + 1200)]
        assert "gate_alert," in block


def test_memory_refresh_reloads_seed_choices_and_overview() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    helper_start = source.index("def refresh_memory(")
    inspect_start = source.index("def inspect_seed(", helper_start)
    helper = source[helper_start:inspect_start]

    assert "memory_session_changed(selected)" in helper
    assert "dropdown_update(choices, selected)" in helper

    binding_start = source.index("memory_refresh.click(")
    binding = source[binding_start : binding_start + 500]
    assert "refresh_memory" in binding
    assert "outputs=[memory_session, seed_select, memory_overview]" in binding



def test_review_actions_refresh_memory_summary_and_dropdown() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    falsify_start = source.index("def falsify_seed(")
    evidence_start = source.index("def submit_verified_evidence(", falsify_start)
    verify_start = source.index("def verify_turn(", evidence_start)
    falsify_body = source[falsify_start:evidence_start]
    evidence_body = source[evidence_start:verify_start]

    for body in (falsify_body, evidence_body):
        assert "dropdown_update(ctl.seed_choices(session_view), seed_id)" in body
        assert "_memory_overview(session_view)" in body

    falsify_binding = source[
        source.index("falsify_button.click(") : source.index("evidence_button.click(")
    ]
    evidence_binding = source[
        source.index("evidence_button.click(") : source.index('with gr.Tab("Controleren"')
    ]
    for binding in (falsify_binding, evidence_binding):
        assert "seed_select," in binding
        assert "memory_overview," in binding



def test_review_alerts_are_scoped_and_preserved_on_errors() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    helper_start = source.index("def _notice_for_selected_session(")
    inspect_start = source.index("def inspect_seed(", helper_start)
    helper = source[helper_start:inspect_start]
    assert "selected_session_id == mutated_session_id" in helper
    assert "ctl.session_view(selected_session_id)" in helper
    assert "return gr.update()" in helper

    falsify_start = source.index("def falsify_seed(")
    evidence_start = source.index("def submit_verified_evidence(", falsify_start)
    verify_start = source.index("def verify_turn(", evidence_start)
    falsify_body = source[falsify_start:evidence_start]
    evidence_body = source[evidence_start:verify_start]

    for body in (falsify_body, evidence_body):
        assert "chat_session_id" in body
        assert "source_session_id" in body
        assert "_notice_for_selected_session(" in body
        assert "gr.update()" in body

    falsify_binding = source[
        source.index("falsify_button.click(") : source.index("evidence_button.click(")
    ]
    evidence_binding = source[
        source.index("evidence_button.click(") : source.index('with gr.Tab("Controleren"')
    ]
    for binding in (falsify_binding, evidence_binding):
        assert "session_select," in binding
        assert "source_session," in binding



def test_send_rejections_preserve_existing_gate_notice() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    send_start = source.index("def send_message(")
    ingest_start = source.index("def source_session_changed(", send_start)
    body = source[send_start:ingest_start]

    empty_branch = body[
        body.index('if not str(question or "").strip():') :
        body.index("try:", body.index('if not str(question or "").strip():'))
    ]
    assert "gr.update()," in empty_branch
    assert empty_branch.rstrip().endswith(")")

    exception_start = body.index("except Exception as exc:")
    exception_body = body[exception_start:]
    assert "gr.update()," in exception_body
    assert 'return (' in exception_body

    # The final callback output is gate_alert, so rejected sends must not clear it.
    assert exception_body.count("gr.update()") >= 2


def test_sources_gate_notice_tracks_its_selected_session() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    assert "def source_session_changed(" in source
    assert "return _gate_notice(ctl.session_view(session_id))" in source
    assert "def refresh_source_session(" in source
    assert "source_session_changed(selected)" in source

    component_start = source.index("source_gate_alert = gr.Markdown(")
    component = source[component_start : component_start + 220]
    assert "_gate_notice(initial_view)" in component

    refresh_start = source.index("source_refresh.click(")
    refresh_block = source[refresh_start : refresh_start + 700]
    assert "refresh_source_session" in refresh_block
    assert "outputs=[source_session, source_gate_alert]" in refresh_block
    assert "source_session.change(" in refresh_block
    assert "source_session_changed" in refresh_block
    assert "outputs=[source_gate_alert]" in refresh_block



def test_sources_ingest_errors_preserve_gate_notice() -> None:
    source = Path("src/shadowseed/workbench/simple_app.py").read_text(encoding="utf-8")

    ingest_start = source.index("def ingest_sources(")
    dashboard_start = source.index("def dashboard_session_changed(", ingest_start)
    body = source[ingest_start:dashboard_start]
    exception_start = body.index("except Exception as exc:")
    exception_body = body[exception_start:]

    assert "pasted_text," in exception_body
    assert "gr.update()," in exception_body
    assert not exception_body.rstrip().endswith('""\n            )')
