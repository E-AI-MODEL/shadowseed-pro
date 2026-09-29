from __future__ import annotations

from pathlib import Path

from shadowseed.workbench.simple_app import (
    _authority_explainer,
    _chat_status,
    _recommended_setup,
    _source_summary,
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
        'with gr.Tab("Chat")',
        'with gr.Tab("Bronnen")',
        'with gr.Tab("Geheugen")',
        'with gr.Tab("Controleren")',
        'with gr.Tab("Uitleg")',
        'with gr.Tab("Meer")',
        'gr.Button("＋ Nieuwe chat"',
        'gr.Button("Versturen"',
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


def test_chat_status_hides_gate_jargon_from_normal_user() -> None:
    status = _chat_status(
        {
            "backend": "fixture",
            "authority_profile_id": "assisted",
            "effective_gate_policy_id": "evidence_backed",
            "turn": 4,
            "authority_review_seed_ids": ["ss_2"],
            "seeds": [
                {"status": "PROMOTED", "blocking": False},
                {"status": "ACTIVE", "blocking": False},
            ],
        }
    )

    assert "4 bericht(en)" in status
    assert "Meedenkend" in status
    assert "2 geheugenpunt(en)" in status
    assert "1 mag later meedenken" in status
    assert "1 vraagt controle" in status
    assert "evidence_backed" not in status
    assert "Gate" not in status


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
