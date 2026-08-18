from __future__ import annotations

import json

import pytest

from shadowseed.application.comparison import ComparisonService
from shadowseed.application.models import SessionConfig
from shadowseed.application.scenarios import parse_scenario
from shadowseed.application.sessions import service_for_workspace
from shadowseed.workbench.controller import WorkbenchController


def test_new_application_sessions_default_to_live_ssl(tmp_path) -> None:
    assert SessionConfig().runtime_mode == "live"

    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Normal product chat",
        profile_id="demo",
        backend="fixture",
    )
    stored = controller.sessions.load(session_id)

    assert stored["config"]["runtime_mode"] == "live"
    assert stored["config"]["gate_policy_id"] is None
    assert controller.session_view(session_id)["runtime_mode"] == "live"


def test_real_model_product_default_uses_semantic_embedding() -> None:
    assert WorkbenchController.default_embedding_backend("fixture") == "lexical"
    for backend in ("ollama", "hf-transformers", "openai"):
        assert WorkbenchController.default_embedding_backend(backend) == "sentence-transformers"


def _seed_state(stored: dict) -> list[tuple[str, int, float, float, str]]:
    return sorted(
        (
            str(seed["text"]),
            int(seed["occurrence_count"]),
            float(seed["trace"]),
            float(seed["weight"]),
            str(seed["status"]),
        )
        for seed in stored["state"]["manager"]["seeds"]
    )


def test_live_chat_can_generate_no_ssl_control_without_authored_baseline(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    paired_id = sessions.create_session(title="Paired control", profile_id="demo")
    ordinary_id = sessions.create_session(title="Ordinary control", profile_id="demo")
    question = "What important perspective could be missing?"

    report = sessions.run_turn(
        paired_id,
        question,
        compare_without_ssl=True,
    )
    sessions.run_turn(ordinary_id, question, compare_without_ssl=False)
    paired = sessions.load(paired_id)
    ordinary = sessions.load(ordinary_id)
    persisted_report = paired["state"]["turn_reports"][0]

    assert report["runtime_mode"] == "live"
    assert report["comparison_requested"] is True
    assert report["comparison_kind"] == "paired_live_no_ssl_control"
    assert report["comparison_control_answer"]
    assert report["comparison_ssl_answer"] == report["answer"]
    assert persisted_report["comparison_control_answer"] == report["comparison_control_answer"]
    assert paired["state"]["turn"] == ordinary["state"]["turn"] == 1

    # The extra control generation is presentation-only. Running it must leave
    # exactly the same seed/trace/weight state as an otherwise identical live turn
    # that did not request a control. Cluster recurrence has a separate issue #69.
    assert _seed_state(paired) == _seed_state(ordinary)


def test_controller_returns_ready_to_render_ssl_on_off_comparison(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Compare in chat",
        profile_id="demo",
        backend="fixture",
    )

    result = controller.send_turn(
        session_id,
        "What should I consider next?",
        compare_without_ssl=True,
    )

    comparison = result["comparison"]
    assert comparison is not None
    assert comparison["runtime_mode"] == "live"
    assert comparison["comparison_kind"] == "paired_live_no_ssl_control"
    assert {comparison["candidate_a_label"], comparison["candidate_b_label"]} == {
        "ssl_off",
        "ssl_on",
    }
    assert comparison["question"] == "What should I consider next?"


def test_live_turn_without_requested_control_does_not_pretend_to_be_comparable(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Normal chat", profile_id="demo")
    sessions.run_turn(session_id, "Normal user message")

    with pytest.raises(ValueError, match="no paired no-SSL control"):
        ComparisonService(sessions).compare_turn(session_id, 0)


def test_research_evaluation_still_generates_its_own_control(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(
        title="Research comparison",
        profile_id="demo",
        config=SessionConfig(runtime_mode="evaluation"),
    )

    report = sessions.run_turn(
        session_id,
        "The tester supplies only this question, not a baseline answer.",
        compare_without_ssl=True,
    )
    comparison = ComparisonService(sessions).compare_turn(
        session_id,
        0,
        blinded=False,
    )

    assert report["baseline_answer"]
    assert report["comparison_control_answer"] == report["baseline_answer"]
    assert {comparison["candidate_a_label"], comparison["candidate_b_label"]} == {
        "baseline",
        "shadowseed",
    }


def test_scenario_format_remains_research_legacy_default_evaluation() -> None:
    scenario = parse_scenario(
        json.dumps(
            {
                "title": "Legacy research batch",
                "questions": ["Question one"],
            }
        )
    )
    assert scenario.runtime_mode == "evaluation"
    assert scenario.embedding_backend == "lexical"
