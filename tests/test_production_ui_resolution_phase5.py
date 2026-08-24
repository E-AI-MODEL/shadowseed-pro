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
