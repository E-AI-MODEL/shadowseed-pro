"""Production-local UI reachability contract for contradiction resolution."""

from __future__ import annotations

from pathlib import Path

from shadowseed.workbench.production_local import (
    _blocking_seed_choices,
    _live_session_choices,
)


ROOT = Path(__file__).resolve().parents[1]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class _FakeResolutionController:
    def list_sessions(self) -> list[dict]:
        return [
            {
                "session_id": "research",
                "title": "Research comparison",
                "runtime_mode": "evaluation",
                "backend": "fixture",
                "turn_count": 2,
            },
            {
                "session_id": "live",
                "title": "Production chat",
                "runtime_mode": "live",
                "backend": "fixture",
                "turn_count": 1,
            },
        ]

    @staticmethod
    def session_choices(summaries: list[dict]) -> list[tuple[str, str]]:
        return [(item["title"], item["session_id"]) for item in summaries]

    def session_view(self, session_id: str) -> dict:
        assert session_id == "session"
        return {
            "seeds": [
                {"id": "open", "status": "open"},
                {"id": "blocked", "status": "contradicted"},
            ]
        }

    @staticmethod
    def seed_choices(_session_view: dict) -> list[tuple[str, str]]:
        return [
            ("open · first seed", "open"),
            ("contradicted · blocked seed", "blocked"),
        ]

    def seed_view(self, session_id: str, seed_id: str) -> dict:
        assert session_id == "session"
        return {"blocking": seed_id == "blocked"}


def test_supported_production_ui_exposes_distinct_contradiction_resolution_action() -> None:
    production_ui = _text("src/shadowseed/workbench/production_local.py")
    vnext_ui = _text("src/shadowseed/workbench/simple_app_vnext.py")
    standalone = _text("src/shadowseed/workbench/standalone.py")

    assert "def build_production_local_app(" in production_ui
    assert "return build_app(controller=ctl)" in production_ui
    assert "gr.TabbedInterface(" not in production_ui
    assert "can_resolve_contradiction" in vnext_ui
    assert "ctl.resolve_contradiction(" in vnext_ui
    assert "Blokkade formeel oplossen" in vnext_ui
    assert "Alleen gebruiken nadat de blokkade onafhankelijk is gecontroleerd." in vnext_ui
    assert "build_production_local_app(controller=controller)" in standalone
    assert '"production_resolution_ui": True' in standalone

def test_production_resolution_is_bound_to_the_selected_shadow_seed() -> None:
    vnext_ui = _text("src/shadowseed/workbench/simple_app_vnext.py")

    assert "def resolve_contradiction_shell(" in vnext_ui
    assert "seed_before = ctl.seed_view(session_id, seed_id)" in vnext_ui
    assert 'if not bool(seed_before.get("blocking", False))' in vnext_ui
    assert "inputs=[" in vnext_ui
    assert "active_session," in vnext_ui
    assert "seed_select," in vnext_ui
    assert "resolution_basis," in vnext_ui
    assert "resolution_contradiction_id," in vnext_ui
    assert 'api_name="resolve_contradiction"' in vnext_ui

def test_resolution_selector_filters_to_currently_blocking_seeds() -> None:
    controller = _FakeResolutionController()

    assert _blocking_seed_choices(controller, "session") == [
        ("contradicted · blocked seed", "blocked")
    ]


def test_resolution_selector_excludes_research_sessions() -> None:
    controller = _FakeResolutionController()

    assert _live_session_choices(controller) == [("Production chat", "live")]
