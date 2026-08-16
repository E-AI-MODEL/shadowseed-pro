from __future__ import annotations

import json

import pytest

from shadowseed.application.comparison import ComparisonService
from shadowseed.application.feedback import FeedbackService
from shadowseed.application.inspection import InspectionService
from shadowseed.application.models import SessionConfig
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


def test_controller_creates_and_lists_explicit_live_session(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Live fixture",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
    )

    stored = controller.sessions.load(session_id)
    view = controller.session_view(session_id)
    choices = controller.session_choices(controller.list_sessions())

    assert stored["config"]["runtime_mode"] == "live"
    assert stored["config"]["embedding_backend"] == "lexical"
    assert view["runtime_mode"] == "live"
    assert choices[0][0] == "Live fixture · live · fixture · 0 turns"


def test_live_non_fixture_requires_semantic_embeddings_or_explicit_override(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")

    with pytest.raises(ValueError, match="require sentence-transformers or openai"):
        controller.create_session(
            title="Unsafe live",
            profile_id="balanced",
            backend="ollama",
            model_id="local-model",
            runtime_mode="live",
            embedding_backend="lexical",
        )

    session_id = controller.create_session(
        title="Explicit toy live",
        profile_id="balanced",
        backend="ollama",
        model_id="local-model",
        runtime_mode="live",
        embedding_backend="lexical",
        allow_toy_embedder=True,
    )
    assert controller.sessions.load(session_id)["config"]["allow_toy_embedder"] is True


def test_hosted_embedding_requires_explicit_confirmation(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")

    with pytest.raises(ValueError, match="external provider"):
        controller.create_session(
            title="Hosted embedding",
            profile_id="demo",
            backend="fixture",
            runtime_mode="live",
            embedding_backend="openai",
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
    assert view["runtime_mode"] == "evaluation"
    assert before == after
    for seed in view["seeds"]:
        assert seed["plain_explanation"]


@pytest.mark.parametrize("runtime_mode", ["evaluation", "live"])
def test_inspection_exposes_persisted_runtime_mode(tmp_path, runtime_mode: str) -> None:
    sessions = service_for_workspace(tmp_path / runtime_mode)
    session_id = sessions.create_session(
        title=f"Inspect {runtime_mode}",
        profile_id="demo",
        config=SessionConfig(runtime_mode=runtime_mode),
    )

    view = InspectionService(sessions).session_view(session_id)

    assert view["runtime_mode"] == runtime_mode


def test_inspection_defaults_legacy_session_view_to_evaluation(tmp_path, monkeypatch) -> None:
    sessions = service_for_workspace(tmp_path / "legacy")
    session_id = sessions.create_session(title="Legacy inspect", profile_id="demo")
    stored = sessions.load(session_id)
    state = dict(stored["state"])
    state["session_config"] = dict(state["session_config"])
    state["session_config"].pop("runtime_mode")
    persisted_config = dict(stored["config"])
    persisted_config.pop("runtime_mode")
    stored = {**stored, "state": state, "config": persisted_config}
    monkeypatch.setattr(sessions, "load", lambda _session_id: stored)

    view = InspectionService(sessions).session_view(session_id)

    assert view["runtime_mode"] == "evaluation"


def test_inspection_normalizes_invalid_persisted_runtime_mode(tmp_path, monkeypatch) -> None:
    sessions = service_for_workspace(tmp_path / "invalid-mode")
    session_id = sessions.create_session(title="Invalid mode", profile_id="demo")
    stored = sessions.load(session_id)
    state = {**stored["state"], "session_config": {"runtime_mode": None}}
    stored = {**stored, "state": state, "config": {"runtime_mode": None}}
    monkeypatch.setattr(sessions, "load", lambda _session_id: stored)

    view = InspectionService(sessions).session_view(session_id)

    assert view["runtime_mode"] == "evaluation"


def test_scenario_parser_and_run_create_resumable_session(tmp_path) -> None:
    payload = json.dumps(
        {
            "title": "Scenario smoke",
            "questions": ["First?", "Second?"],
            "profile_id": "demo",
            "backend": "fixture",
            "runtime_mode": "live",
            "embedding_backend": "lexical",
        }
    )
    spec = parse_scenario(payload)
    assert spec.questions == ("First?", "Second?")
    assert spec.runtime_mode == "live"
    assert spec.embedding_backend == "lexical"

    controller = WorkbenchController(tmp_path / "workspace")
    result = controller.run_scenario(payload)
    assert len(result["turn_reports"]) == 2
    assert result["session"]["turn"] == 2
    assert result["session"]["runtime_mode"] == "live"
    assert controller.session_view(result["session_id"])["turn"] == 2


def test_scenario_rejects_non_boolean_toy_override() -> None:
    with pytest.raises(ValueError, match="must be a boolean"):
        parse_scenario(
            {
                "title": "Invalid",
                "questions": ["Question?"],
                "allow_toy_embedder": "false",
            }
        )


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


def test_live_session_rejects_baseline_comparison(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(
        title="Live compare",
        profile_id="demo",
        config=SessionConfig(runtime_mode="live"),
    )
    sessions.run_turn(session_id, "Question")

    with pytest.raises(ValueError, match="only for evaluation sessions"):
        ComparisonService(sessions).compare_turn(session_id, 0)


def test_live_verified_evidence_persists_and_enables_later_use(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Live evidence",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    first = controller.send_turn(session_id, "What is missing from this privacy plan?")
    seed = first["session"]["seeds"][0]
    seed_id = seed["id"]

    with pytest.raises(ValueError, match="explicitly confirmed"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="reviewer:0",
        )
    with pytest.raises(ValueError, match="must not be empty"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="  ",
            operator_verified=True,
        )

    decisions = []
    for index in range(3):
        result = controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=f"reviewer:{index}",
            note="Checked against an independent source.",
            operator_verified=True,
        )
        decisions.append(result["decision"])
    duplicate = controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="reviewer:2",
        operator_verified=True,
    )

    restored = WorkbenchController(tmp_path / "workspace")
    promoted = next(
        item for item in restored.session_view(session_id)["seeds"] if item["id"] == seed_id
    )
    later = restored.send_turn(session_id, seed["text"])

    assert decisions == ["validated", "validated", "promoted"]
    assert duplicate["decision"] == "blocked"
    assert duplicate["evidence_count"] == 3
    assert promoted["status"] == "PROMOTED"
    assert promoted["evidence_count"] == 3
    assert seed_id in later["report"]["surfaced_seed_ids"]


def test_evaluation_session_rejects_live_evidence_entry(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Evaluation evidence",
        profile_id="demo",
        backend="fixture",
    )
    result = controller.send_turn(session_id, "What is missing?")
    seed_id = result["session"]["seeds"][0]["id"]

    with pytest.raises(ValueError, match="only for live sessions"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="reviewer:1",
            operator_verified=True,
        )


def test_scenario_resume_rejects_runtime_configuration_change(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    live_payload = {
        "title": "Live scenario",
        "questions": ["Question?"],
        "profile_id": "demo",
        "backend": "fixture",
        "runtime_mode": "live",
        "embedding_backend": "lexical",
    }
    result = controller.run_scenario(json.dumps(live_payload))
    changed_payload = {**live_payload, "runtime_mode": "evaluation"}

    with pytest.raises(ValueError, match="runtime_mode does not match"):
        controller.resume_scenario(
            json.dumps(changed_payload),
            result["session_id"],
            start_at=1,
        )
