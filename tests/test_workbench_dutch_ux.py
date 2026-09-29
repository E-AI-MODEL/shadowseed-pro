from __future__ import annotations

from pathlib import Path

from shadowseed.workbench.simple_app import (
    _authority_explainer,
    _chat_status,
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
    simple_source = Path("src/shadowseed/workbench/simple_app.py").read_text(
        encoding="utf-8"
    )

    assert "from shadowseed.workbench.simple_app import build_simple_app" in app_source
    assert "return build_simple_app(workspace, controller=controller)" in app_source

    for label in (
        'with gr.Tab("Overzicht")',
        'with gr.Tab("Chat")',
        'with gr.Tab("Bronnen")',
        'with gr.Tab("Geheugen")',
        'with gr.Tab("Controleren")',
        'with gr.Tab("Uitleg")',
        'with gr.Tab("Meer")',
        'gr.Button("＋ Nieuwe chat"',
        'gr.Button("Versturen"',
        'gr.Button("Open detail"',
    ):
        assert label in simple_source

    for old_top_level_tab in (
        'with gr.Tab("Sources")',
        'with gr.Tab("Control")',
        'with gr.Tab("About SSL")',
        'with gr.Tab("Shadow")',
        'with gr.Tab("Verify")',
        'with gr.Tab("Feedback and export")',
        'with gr.Tab("Advanced / research")',
    ):
        assert old_top_level_tab not in simple_source


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
