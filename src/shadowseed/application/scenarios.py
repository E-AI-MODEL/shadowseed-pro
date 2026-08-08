"""Import and execute practical tester scenarios as persisted sessions."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from shadowseed.application.sessions import SessionService
from shadowseed.application.profiles import get_profile


@dataclass(frozen=True)
class ScenarioSpec:
    title: str
    questions: tuple[str, ...]
    profile_id: str = "balanced"
    backend: str = "fixture"
    model_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["questions"] = list(self.questions)
        return data


def parse_scenario(value: str | dict[str, Any]) -> ScenarioSpec:
    """Parse a small, explicit JSON scenario contract.

    Accepted shape::

        {
          "title": "My scenario",
          "questions": ["First prompt", "Second prompt"],
          "profile_id": "balanced",
          "backend": "fixture",
          "model_id": null
        }
    """

    if isinstance(value, str):
        try:
            data = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError(f"scenario is not valid JSON: {exc.msg}") from exc
    else:
        data = dict(value)
    if not isinstance(data, dict):
        raise ValueError("scenario must be a JSON object")
    questions_raw = data.get("questions")
    if not isinstance(questions_raw, list):
        raise ValueError("scenario.questions must be a JSON array")
    questions = tuple(str(item).strip() for item in questions_raw if str(item).strip())
    if not questions:
        raise ValueError("scenario must contain at least one non-empty question")
    if len(questions) > 100:
        raise ValueError("scenario may contain at most 100 questions")
    profile_id = str(data.get("profile_id", "balanced"))
    get_profile(profile_id)
    backend = str(data.get("backend", "fixture"))
    if backend not in {"fixture", "hf-transformers", "ollama", "openai"}:
        raise ValueError(f"unsupported scenario backend: {backend}")
    model_id_raw = data.get("model_id")
    model_id = str(model_id_raw).strip() if model_id_raw not in (None, "") else None
    if backend != "fixture" and not model_id:
        raise ValueError(f"backend {backend!r} requires model_id")
    return ScenarioSpec(
        title=str(data.get("title", "Imported scenario")).strip() or "Imported scenario",
        questions=questions,
        profile_id=profile_id,
        backend=backend,
        model_id=model_id,
    )


class ScenarioService:
    """Run imported scenarios through the same SessionService used by the UI."""

    def __init__(self, sessions: SessionService) -> None:
        self.sessions = sessions

    def parse(self, value: str | dict[str, Any]) -> ScenarioSpec:
        return parse_scenario(value)

    @staticmethod
    def _result(
        *,
        scenario: ScenarioSpec,
        session_id: str,
        reports: list[dict[str, Any]],
        completed: int,
        error: str | None,
    ) -> dict[str, Any]:
        return {
            "session_id": session_id,
            "scenario": scenario.to_dict(),
            "turn_reports": reports,
            "completed": completed,
            "total": len(scenario.questions),
            "complete": error is None and completed == len(scenario.questions),
            "failed_at": None if error is None else completed,
            "next_at": completed,
            "error": error,
        }

    def _continue(
        self,
        scenario: ScenarioSpec,
        session_id: str,
        *,
        start_at: int,
    ) -> dict[str, Any]:
        reports: list[dict[str, Any]] = []
        completed = start_at
        error: str | None = None
        for position, question in enumerate(scenario.questions[start_at:], start=start_at):
            try:
                reports.append(self.sessions.run_turn(session_id, question))
            except Exception as exc:  # backend/runtime failure becomes resumable batch state
                error = f"{type(exc).__name__}: {exc}"
                break
            completed = position + 1
        return self._result(
            scenario=scenario,
            session_id=session_id,
            reports=reports,
            completed=completed,
            error=error,
        )

    def run(self, scenario: ScenarioSpec) -> dict[str, Any]:
        session_id = self.sessions.create_session(
            title=scenario.title,
            profile_id=scenario.profile_id,
            backend=scenario.backend,
            model_id=scenario.model_id,
        )
        return self._continue(scenario, session_id, start_at=0)

    def resume(
        self,
        scenario: ScenarioSpec,
        session_id: str,
        start_at: int | None = None,
    ) -> dict[str, Any]:
        """Continue a partial scenario without replaying persisted turns.

        The persisted turn count is the authority for the next position. A caller
        supplied position must match it, preventing stale UI state from replaying
        already completed hosted-model calls or skipping questions.
        """

        stored = self.sessions.load(session_id)
        persisted_reports = list(stored["state"].get("turn_reports", []))
        persisted_position = len(persisted_reports)
        if start_at is None:
            start_at = persisted_position
        if start_at < 0 or start_at > len(scenario.questions):
            raise ValueError("scenario resume position is outside the scenario")
        if start_at != persisted_position:
            raise ValueError(
                "scenario resume position does not match persisted progress: "
                f"requested {start_at}, persisted {persisted_position}"
            )
        return self._continue(scenario, session_id, start_at=start_at)
