"""Production-local UI reachability contract for contradiction resolution."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_supported_production_ui_exposes_distinct_contradiction_resolution_action() -> None:
    production_ui = _text("src/shadowseed/workbench/production_local.py")
    standalone = _text("src/shadowseed/workbench/standalone.py")

    assert "def build_production_local_app(" in production_ui
    assert "ctl.resolve_contradiction(" in production_ui
    assert 'gr.Button("Resolve contradiction"' in production_ui
    assert '"This is an authority-bearing production action.' in production_ui
    assert 'gr.TabbedInterface(' in production_ui
    assert '["Workbench", "Resolve contradiction"]' in production_ui
    assert "build_production_local_app(controller=controller)" in standalone
    assert '"production_resolution_ui": True' in standalone


def test_production_resolution_initializes_and_refreshes_seed_choices() -> None:
    production_ui = _text("src/shadowseed/workbench/production_local.py")

    assert "def seed_choices_for_session(session_id: str | None)" in production_ui
    assert "initial_session = initial_sessions[0][1] if initial_sessions else None" in production_ui
    assert "initial_seed_choices = seed_choices_for_session(initial_session)" in production_ui
    assert "choices=initial_seed_choices" in production_ui
    assert "value=initial_seed_choices[0][1] if initial_seed_choices else None" in production_ui
    assert "seed_choices = seed_choices_for_session(selected)" in production_ui
    assert "outputs=[resolution_session, resolution_seed]" in production_ui
