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

    def run(self, scenario: ScenarioSpec) -> dict[str, Any]:
        session_id = self.sessions.create_session(
            title=scenario.title,
            profile_id=scenario.profile_id,
            backend=scenario.backend,
            model_id=scenario.model_id,
        )
        reports: list[dict[str, Any]] = []
        for question in scenario.questions:
            reports.append(self.sessions.run_turn(session_id, question))
        return {
            "session_id": session_id,
            "scenario": scenario.to_dict(),
            "turn_reports": reports,
        }
