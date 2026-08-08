from __future__ import annotations

import json

import pytest

from shadowseed.application.comparison import ComparisonService
from shadowseed.application.feedback import FeedbackService
from shadowseed.application.inspection import InspectionService
from shadowseed.application.scenarios import parse_scenario
from shadowseed.application.sessions import service_for_workspace
from shadowseed.workbench.controller import WorkbenchController


def test_controller_runs_and_resumes_fixture_session(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Round 2 smoke",
        profile_id="demo",
        backend="fixture",
    )

    first = controller.send_turn(session_id, "What uncertainty remains?")
    assert first["report"]["turn"] == 0
    assert first["session"]["turn"] == 1

    restored = WorkbenchController(tmp_path / "workspace")
    second = restored.send_turn(session_id, "What evidence would change the answer?")
    assert second["report"]["turn"] == 1
    assert second["session"]["turn"] == 2
    assert len(second["session"]["turn_reports"]) == 2


def test_hosted_backend_requires_fresh_explicit_confirmation(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    with pytest.raises(ValueError, match="external provider"):
        controller.create_session(
            title="Hosted",
            profile_id="balanced",
            backend="openai",
            model_id="example-model",
            external_confirmed=False,
        )


def test_feedback_is_record_only_and_validates_turn(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Feedback", profile_id="demo")
    sessions.run_turn(session_id, "Question")
    service = FeedbackService(sessions)

    feedback = service.record(
        session_id=session_id,
        turn_index=0,
        overall="better",
        seed_effect="no_visible_effect",
        note="Clearer answer",
    )
    assert feedback.action == "record_only"
    assert service.list(session_id) == [feedback]

    with pytest.raises(ValueError, match="does not exist"):
        service.record(session_id=session_id, turn_index=99)


def test_inspection_is_read_only_and_explains_seed_state(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Inspect", profile_id="demo")
    sessions.run_turn(session_id, "Question")
    before = sessions.load(session_id)["state"]

    view = InspectionService(sessions).session_view(session_id)
    after = sessions.load(session_id)["state"]

    assert view["turn"] == 1
    assert before == after
    for seed in view["seeds"]:
        assert seed["plain_explanation"]


def test_scenario_parser_and_run_create_resumable_session(tmp_path) -> None:
    payload = json.dumps(
        {
            "title": "Scenario smoke",
            "questions": ["First?", "Second?"],
            "profile_id": "demo",
            "backend": "fixture",
        }
    )
    spec = parse_scenario(payload)
    assert spec.questions == ("First?", "Second?")

    controller = WorkbenchController(tmp_path / "workspace")
    result = controller.run_scenario(payload)
    assert len(result["turn_reports"]) == 2
    assert result["session"]["turn"] == 2
    assert controller.session_view(result["session_id"])["turn"] == 2


def test_blind_comparison_is_stable_and_revealable(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Compare", profile_id="demo")
    sessions.run_turn(session_id, "Question")
    service = ComparisonService(sessions)

    first = service.compare_turn(session_id, 0, blinded=True)
    again = service.compare_turn(session_id, 0, blinded=True)
    revealed = service.compare_turn(session_id, 0, blinded=True, reveal=True)

    assert first == again
    assert "candidate_a_label" not in first
    assert set(revealed["revealed_mapping"].values()) == {"baseline", "shadowseed"}
