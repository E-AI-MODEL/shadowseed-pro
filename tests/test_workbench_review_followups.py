"""Regression tests for the two late P2 review threads on PR #42."""

from __future__ import annotations

import pytest

from shadowseed.application.inspection import InspectionService
from shadowseed.application.scenarios import ScenarioService, ScenarioSpec


class _InspectionSessions:
    def __init__(self, manager: dict, influence: list | None = None) -> None:
        self._manager = manager
        self._influence = influence or []

    def load(self, _session_id: str) -> dict:
        return {"state": {"manager": self._manager, "influence_records": self._influence}}


def _inspection(manager: dict) -> InspectionService:
    service = InspectionService.__new__(InspectionService)
    service.sessions = _InspectionSessions(manager)
    return service


def test_seed_timeline_interleaves_ledgers_by_actual_instant() -> None:
    service = _inspection(
        {
            "event_log": [
                {
                    "seed_id": "s1",
                    "event_type": "created",
                    "created_at": "2026-01-01T00:30:00+02:00",
                },
                {
                    "seed_id": "s1",
                    "event_type": "reactivated",
                    "created_at": "2026-01-01T02:00:00+00:00",
                },
            ],
            "validation_log": [],
            "gate_events": [
                {
                    "seed_id": "s1",
                    "decision": "promoted",
                    "created_at": "2025-12-31T23:00:00Z",
                }
            ],
            "contradiction_records": [],
            "feedback_log": [],
        }
    )

    timeline = service.seed_timeline("sess", "s1")

    # 00:30+02:00 is 22:30Z on the previous day, so lexical ISO ordering
    # would be wrong here. The audit view must order the actual instants.
    assert [entry["type"] for entry in timeline] == ["seed_event", "gate", "seed_event"]
    assert [entry["sequence"] for entry in timeline] == [0, 1, 2]


def test_seed_timeline_is_deterministic_without_valid_timestamps() -> None:
    manager = {
        "event_log": [{"seed_id": "s1", "event_type": "created"}],
        "validation_log": [{"seed_id": "s1", "created_at": "not-a-time"}],
        "gate_events": [{"seed_id": "s1", "decision": "blocked"}],
        "contradiction_records": [],
        "feedback_log": [],
    }

    first = _inspection(manager).seed_timeline("sess", "s1")
    second = _inspection(manager).seed_timeline("sess", "s1")

    assert first == second
    assert [entry["sequence"] for entry in first] == list(range(len(first)))


class _FailingSessions:
    def __init__(self, fail_on: str = "never") -> None:
        self.fail_on = fail_on
        self.asked: list[str] = []
        self.persisted: list[dict] = []

    def create_session(self, **_kwargs) -> str:
        self.persisted = []
        return "sess-1"

    def run_turn(self, _session_id: str, question: str) -> dict:
        self.asked.append(question)
        if question == self.fail_on:
            raise RuntimeError("backend timeout")
        report = {"turn": len(self.persisted), "question": question}
        self.persisted.append(report)
        return report

    def load(self, _session_id: str) -> dict:
        return {"state": {"turn_reports": list(self.persisted)}}


def _spec(*questions: str) -> ScenarioSpec:
    return ScenarioSpec(
        title="batch",
        questions=tuple(questions),
        profile_id="demo",
        backend="fixture",
    )


def test_scenario_batch_preserves_partial_progress_on_failure() -> None:
    sessions = _FailingSessions(fail_on="q3")
    service = ScenarioService(sessions)

    result = service.run(_spec("q1", "q2", "q3", "q4"))

    assert result["session_id"] == "sess-1"
    assert result["complete"] is False
    assert result["completed"] == result["next_at"] == 2
    assert result["total"] == 4
    assert result["failed_at"] == 2
    assert "backend timeout" in result["error"]
    assert [item["question"] for item in sessions.persisted] == ["q1", "q2"]
    assert sessions.asked == ["q1", "q2", "q3"]


def test_scenario_resume_retries_failure_without_replaying_completed_calls() -> None:
    sessions = _FailingSessions(fail_on="q3")
    service = ScenarioService(sessions)
    scenario = _spec("q1", "q2", "q3", "q4")
    first = service.run(scenario)
    asked_before_resume = len(sessions.asked)

    sessions.fail_on = "never"
    resumed = service.resume(scenario, first["session_id"], start_at=first["next_at"])

    assert resumed["complete"] is True
    assert resumed["completed"] == resumed["total"] == 4
    assert sessions.asked[asked_before_resume:] == ["q3", "q4"]
    assert [item["question"] for item in sessions.persisted] == ["q1", "q2", "q3", "q4"]


def test_scenario_resume_rejects_stale_position() -> None:
    sessions = _FailingSessions(fail_on="q3")
    service = ScenarioService(sessions)
    scenario = _spec("q1", "q2", "q3")
    service.run(scenario)

    with pytest.raises(ValueError, match="persisted progress"):
        service.resume(scenario, "sess-1", start_at=1)

    assert sessions.asked == ["q1", "q2", "q3"]


def test_scenario_resume_rejects_different_scenario_prefix() -> None:
    sessions = _FailingSessions(fail_on="q3")
    service = ScenarioService(sessions)
    service.run(_spec("q1", "q2", "q3"))

    with pytest.raises(ValueError, match="questions do not match"):
        service.resume(_spec("q1", "different", "q3"), "sess-1", start_at=2)


def test_successful_scenario_batch_reports_completion() -> None:
    sessions = _FailingSessions()
    result = ScenarioService(sessions).run(_spec("q1", "q2"))

    assert result["complete"] is True
    assert result["completed"] == result["next_at"] == result["total"] == 2
    assert result["failed_at"] is None
    assert result["error"] is None
