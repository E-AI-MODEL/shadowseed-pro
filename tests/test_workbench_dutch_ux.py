from __future__ import annotations

from pathlib import Path

from shadowseed.workbench.feature_help import render_feature_help
from shadowseed.workbench.simple_app_vnext import (
    _audit_summary,
    _authority_gate_summary,
    _orchestration_panel,
    _ollama_note,
    _seed_action_flags,
    _seed_story as _vnext_seed_story,
    _statefulness_summary,
    _ui_error,
)


def test_default_workbench_is_dutch_chat_first_surface() -> None:
    app_source = Path("src/shadowseed/workbench/app.py").read_text(encoding="utf-8")
    vnext_source = Path("src/shadowseed/workbench/simple_app_vnext.py").read_text(
        encoding="utf-8"
    )

    assert "from shadowseed.workbench.simple_app_vnext import build_vnext_app" in app_source
    assert "return build_vnext_app(workspace, controller=controller)" in app_source

    assert 'gr.Markdown("Versie **0.10.1**"' not in vnext_source
    assert 'f"Versie **{update_service.current_version}**"' in vnext_source
    assert "Geen nieuwere release beschikbaar" in vnext_source

    for contract in (
        'elem_id="ss-left"',
        'elem_id="ss-center"',
        'elem_id="ss-right"',
        'elem_id="ss-panel-new-chat"',
        'elem_id="ss-panel-source"',
        'elem_id="ss-panel-shadow"',
        'elem_id="ss-panel-research"',
        'elem_id="ss-panel-audit"',
        'label="Vergelijk deze beurt zonder SSL"',
        'gr.Button("Versturen"',
        'gr.Button("Chat starten"',
        'gr.Button("＋  Nieuwe chat"',
        'gr.Button("＋  Bron toevoegen"',
        'gr.Button("Bekijk Shadow"',
    ):
        assert contract in vnext_source

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
    note = _ollama_note(["qwen3:8b"], "qwen3:8b")

    assert "Lokaal chatmodel geselecteerd" in note
    assert "Semantisch matchen gebruikt lokaal `embeddinggemma`" in note
    assert "ollama pull embeddinggemma" in note


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

    evidence_start = source.index("    def _submit_verified_evidence_action(")
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

    research_panel = source.index('elem_id="ss-panel-research"')
    research_binding = source.index("research_run.click(", research_panel)
    assert research_panel < research_binding
    assert 'label="Onderzoeksvraag"' in source[research_panel:research_binding]
    assert "Voer longitudinale vergelijking uit" in source[research_panel:research_binding]

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

def test_feature_help_separates_same_turn_revision_from_self_derived_authority() -> None:
    off = render_feature_help(
        "same_turn_revision",
        view={
            "effective_gate_policy_id": "evidence_backed",
            "authority_profile_id": "strict",
            "allow_same_turn_revision": False,
            "self_derived_signal_policy": "fail_closed",
        },
    )
    on = render_feature_help(
        "same_turn_revision",
        view={
            "effective_gate_policy_id": "evidence_backed",
            "authority_profile_id": "strict",
            "allow_same_turn_revision": True,
            "self_derived_signal_policy": "bounded_experimental",
        },
    )

    assert "Herziening in dezelfde beurt staat uit" in off
    assert "Self-derived authority staat fail-closed" in off
    assert "Herziening in dezelfde beurt staat aan" in on
    assert "maximaal één keer" in on
    assert "verhogen geen canonical recurrence" in on
    assert "geen authority" in on

def test_vnext_exposes_profile_gate_relation_and_rebuild_metadata() -> None:
    view = {
        "authority_profile_id": "autonomous",
        "profile_default_gate_policy_id": "exploratory",
        "configured_gate_policy_id": "evidence_backed",
        "effective_gate_policy_id": "evidence_backed",
        "gate_policy_override_active": True,
        "setting_metadata": {
            "recurrence_mode": {"apply_mode": "rebuild_required"},
            "cluster_threshold": {"apply_mode": "rebuild_required"},
            "surface_top_k": {"apply_mode": "immediate"},
        },
    }

    relation = _authority_gate_summary(view)
    statefulness = _statefulness_summary(view)

    assert "autonomous" in relation
    assert "exploratory" in relation
    assert "override" in relation.lower()
    assert "evidence_backed" in relation
    assert "recurrence_mode" in statefulness
    assert "cluster_threshold" in statefulness
    assert "surface_top_k" not in statefulness

def test_vnext_renders_session_orchestration_without_inventing_ui_rules() -> None:
    view = {
        "orchestration": {
            "state": "human_turn",
            "reason_code": "verified_support_required",
            "required_action": "submit_verified_support",
        },
        "turn_reports": [],
    }

    rendered = _orchestration_panel(view)

    assert "Wie is aan zet?" in rendered
    assert "Jij bent aan zet" in rendered
    assert "geverifieerde ondersteuning" in rendered
    assert "Voeg geverifieerde ondersteuning toe" in rendered

def test_vnext_seed_actions_follow_required_action_only() -> None:
    evidence = _seed_action_flags(
        {
            "blocking": False,
            "orchestration": {
                "required_action": "submit_verified_support",
            },
        }
    )
    blocked = _seed_action_flags(
        {
            "blocking": True,
            "orchestration": {
                "required_action": "resolve_contradiction",
            },
        }
    )

    assert evidence == {
        "contradict": True,
        "verified_support": True,
        "resolve_contradiction": False,
    }
    assert blocked == {
        "contradict": False,
        "verified_support": False,
        "resolve_contradiction": True,
    }

def test_vnext_seed_story_explains_who_is_next_and_why() -> None:
    rendered = _vnext_seed_story(
        {
            "text": "Privacy boundary",
            "blocking": True,
            "current_gate_authorized": False,
            "occurrence_count": 4,
            "evidence_count": 1,
            "orchestration": {
                "state": "blocked",
                "reason_code": "blocking_contradiction",
                "required_action": "resolve_contradiction",
            },
        }
    )

    assert "Wie is aan zet" in rendered
    assert "Eerst een blokkade oplossen" in rendered
    assert "tegenspraak" in rendered.lower()
    assert "Leg vast waarom de tegenspraak is opgelost" in rendered

def test_live_audit_shows_behavior_epoch() -> None:
    rendered = _audit_summary(
        {
            "turn": 2,
            "seeds": [],
            "turn_reports": [],
            "authority_profile_id": "strict",
            "effective_gate_policy_id": "evidence_backed",
            "recurrence_mode": "cluster",
            "surface_top_k": 2,
            "behavior_config_epoch": "behavior-sha256::0123456789abcdef01234567",
        }
    )

    assert "Behavior epoch" in rendered
    assert "behavior-sha256::0123456789abcdef01234567" in rendered
