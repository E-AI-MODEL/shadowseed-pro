"""Thin Workbench controller over tester-facing application services.

No Validation Gate, manager, or lifecycle implementation is imported here. The
controller translates UI actions into application-service calls and adds only
product concerns such as external-provider consent and presentation shaping.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from shadowseed.application.comparison import ComparisonService
from shadowseed.application.exports import ExportService, verify_workbench_export
from shadowseed.application.feedback import FeedbackService
from shadowseed.application.inspection import InspectionService
from shadowseed.application.profiles import list_profiles
from shadowseed.application.scenarios import ScenarioService, ScenarioSpec
from shadowseed.application.sessions import SessionService
from shadowseed.application.workspace import WorkspaceService


BACKENDS = ("fixture", "hf-transformers", "ollama", "openai")
_EXTERNAL_PROMPT_BACKENDS = {"openai"}

_BACKEND_NOTES = {
    "fixture": "Deterministic local fixture. Best for onboarding and repeatable smoke tests.",
    "hf-transformers": (
        "Runs the selected Transformers model locally after it is available. Initial model "
        "download may contact Hugging Face; prompts are evaluated locally by this backend."
    ),
    "ollama": "Uses a model served by your local Ollama instance.",
    "openai": (
        "Hosted provider. Prompts and generated context are sent to the OpenAI API; "
        "the API key remains in the process environment and is not stored by the Workbench."
    ),
}


class WorkbenchController:
    """Product-level orchestration for the local tester Workbench."""

    def __init__(self, workspace: str | Path | None = None) -> None:
        self.workspace = WorkspaceService(workspace)
        self.workspace.initialize()
        self.sessions = SessionService(self.workspace.repository)
        self.inspection = InspectionService(self.sessions)
        self.feedback = FeedbackService(self.sessions)
        self.scenarios = ScenarioService(self.sessions)
        self.comparison = ComparisonService(self.sessions)
        self.exports = ExportService(
            self.sessions,
            workspace_root=self.workspace.paths.root,
        )

    @property
    def workspace_root(self) -> str:
        return str(self.workspace.paths.root)

    def profiles(self) -> list[dict[str, Any]]:
        return [
            {
                "profile_id": profile.profile_id,
                "label": profile.label,
                "description": profile.description,
            }
            for profile in list_profiles()
        ]

    def backends(self) -> list[dict[str, str]]:
        return [
            {"backend": backend, "note": _BACKEND_NOTES[backend]}
            for backend in BACKENDS
        ]

    def list_sessions(self) -> list[dict[str, Any]]:
        return [asdict(item) for item in self.sessions.list_sessions()]

    def create_session(
        self,
        *,
        title: str,
        profile_id: str,
        backend: str,
        model_id: str | None = None,
        external_confirmed: bool = False,
    ) -> str:
        self._validate_backend(
            backend,
            model_id=model_id,
            external_confirmed=external_confirmed,
        )
        return self.sessions.create_session(
            title=title,
            profile_id=profile_id,
            backend=backend,
            model_id=model_id or None,
        )

    def send_turn(
        self,
        session_id: str,
        question: str,
        *,
        external_confirmed: bool = False,
    ) -> dict[str, Any]:
        stored = self.sessions.load(session_id)
        self._validate_backend(
            str(stored["backend"]),
            model_id=stored.get("model_id"),
            external_confirmed=external_confirmed,
        )
        report = self.sessions.run_turn(session_id, question)
        return {
            "report": report,
            "session": self.inspection.session_view(session_id),
        }

    def session_view(self, session_id: str) -> dict[str, Any]:
        return self.inspection.session_view(session_id)

    def seed_view(self, session_id: str, seed_id: str) -> dict[str, Any]:
        return self.inspection.seed_view(session_id, seed_id)

    def record_feedback(
        self,
        *,
        session_id: str,
        turn_index: int,
        overall: str,
        seed_effect: str,
        note: str = "",
        seed_id: str | None = None,
    ) -> dict[str, Any]:
        return self.feedback.record(
            session_id=session_id,
            turn_index=int(turn_index),
            overall=overall,
            seed_effect=seed_effect,
            note=note,
            seed_id=seed_id or None,
        ).to_dict()

    def compare_turn(
        self,
        session_id: str,
        turn_index: int,
        *,
        blinded: bool = True,
        reveal: bool = False,
    ) -> dict[str, Any]:
        return self.comparison.compare_turn(
            session_id,
            int(turn_index),
            blinded=blinded,
            reveal=reveal,
        )

    def parse_scenario(self, scenario_json: str) -> dict[str, Any]:
        return self.scenarios.parse(scenario_json).to_dict()

    def run_scenario(
        self,
        scenario_json: str,
        *,
        external_confirmed: bool = False,
    ) -> dict[str, Any]:
        scenario: ScenarioSpec = self.scenarios.parse(scenario_json)
        self._validate_backend(
            scenario.backend,
            model_id=scenario.model_id,
            external_confirmed=external_confirmed,
        )
        result = self.scenarios.run(scenario)
        result["session"] = self.inspection.session_view(result["session_id"])
        return result

    def resume_scenario(
        self,
        scenario_json: str,
        session_id: str,
        *,
        start_at: int | None = None,
        external_confirmed: bool = False,
    ) -> dict[str, Any]:
        scenario = self.scenarios.parse(scenario_json)
        stored = self.sessions.load(session_id)
        if scenario.profile_id != stored["profile_id"]:
            raise ValueError("scenario profile does not match the persisted session")
        if scenario.backend != stored["backend"]:
            raise ValueError("scenario backend does not match the persisted session")
        if (scenario.model_id or None) != (stored.get("model_id") or None):
            raise ValueError("scenario model does not match the persisted session")
        self._validate_backend(
            str(stored["backend"]),
            model_id=stored.get("model_id"),
            external_confirmed=external_confirmed,
        )
        result = self.scenarios.resume(scenario, session_id, start_at=start_at)
        result["session"] = self.inspection.session_view(session_id)
        return result

    def export_report(self, session_id: str, destination: str | Path) -> str:
        return str(self.exports.export_report(session_id, destination))

    def export_support_bundle(self, session_id: str, destination: str | Path) -> str:
        return str(self.exports.export_support_bundle(session_id, destination))

    @staticmethod
    def verify_export(path: str | Path) -> dict[str, Any]:
        return verify_workbench_export(path)

    @staticmethod
    def chat_messages(session_view: dict[str, Any]) -> list[dict[str, str]]:
        messages: list[dict[str, str]] = []
        for report in session_view.get("turn_reports", []):
            messages.append({"role": "user", "content": str(report.get("question", ""))})
            messages.append({"role": "assistant", "content": str(report.get("answer", ""))})
        return messages

    @staticmethod
    def session_choices(summaries: list[dict[str, Any]]) -> list[tuple[str, str]]:
        return [
            (
                f"{item['title']} · {item['backend']} · {item['turn_count']} turns",
                str(item["session_id"]),
            )
            for item in summaries
        ]

    @staticmethod
    def seed_choices(session_view: dict[str, Any]) -> list[tuple[str, str]]:
        choices: list[tuple[str, str]] = []
        for seed in session_view.get("seeds", []):
            seed_id = str(seed.get("id", ""))
            text = str(seed.get("text", "")).replace("\n", " ")
            status = str(seed.get("status", "unknown"))
            choices.append((f"{status} · {text[:72]}", seed_id))
        return choices

    @staticmethod
    def _validate_backend(
        backend: str,
        *,
        model_id: str | None,
        external_confirmed: bool,
    ) -> None:
        if backend not in BACKENDS:
            raise ValueError(f"unsupported Workbench backend: {backend}")
        if backend != "fixture" and not str(model_id or "").strip():
            raise ValueError(f"backend {backend!r} requires a model id")
        if backend in _EXTERNAL_PROMPT_BACKENDS and not external_confirmed:
            raise ValueError(
                "this backend sends prompts to an external provider; check the explicit "
                "external-provider confirmation before continuing"
            )
