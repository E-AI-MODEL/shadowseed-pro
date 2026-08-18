"""Tester-facing session orchestration over the existing ShadowChat runtime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from shadowseed.application.models import SessionConfig, SessionSummary, TesterFeedback
from shadowseed.application.profiles import get_profile
from shadowseed.chat import ShadowChatSession
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository
from shadowseed.surfacing import build_chat_prompt


class SessionService:
    def __init__(self, repository: SQLiteWorkspaceRepository) -> None:
        self.repository = repository
        self.repository.initialize()

    def create_session(
        self,
        *,
        title: str = "Untitled session",
        profile_id: str = "balanced",
        config: SessionConfig | None = None,
        backend: str | None = None,
        model_id: str | None = None,
    ) -> str:
        profile = get_profile(profile_id)
        resolved = profile.apply(config, backend=backend, model_id=model_id)
        session = ShadowChatSession(**resolved.to_dict())
        session_id = f"session::{uuid4()}"
        now = datetime.now().isoformat()
        self.repository.create_session(
            session_id=session_id,
            title=title.strip() or "Untitled session",
            profile_id=profile_id,
            config=resolved.to_dict(),
            state=session.to_state(),
            created_at=now,
        )
        return session_id

    @staticmethod
    def _generate_live_no_ssl_control(
        session: ShadowChatSession,
        question: str,
    ) -> str:
        """Generate a paired control without mutating SSL state.

        The control uses the exact persisted visible conversation history and the
        same model backend, but receives no surfaced Shadow Seeds. It is generated
        before the real live turn so the control cannot observe state changes from
        that turn. Its text is never fed to detection, recurrence, the Gate, or
        later conversation history.
        """

        fixture_answer = f"Fixture echo answer to: {question}"
        return session.model.generate(
            build_chat_prompt(
                session.history,
                question,
                [],
                response_language="English",
            ),
            {
                "question": question,
                "turn": session._turn,
                "baseline_answer": fixture_answer,
            },
            "baseline",
            [],
        )

    def run_turn(
        self,
        session_id: str,
        question: str,
        *,
        compare_without_ssl: bool = False,
    ) -> dict[str, Any]:
        if not question or not question.strip():
            raise ValueError("question must not be empty")
        normalized_question = question.strip()
        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])

        control_answer: str | None = None
        if compare_without_ssl and session.runtime_mode == "live":
            control_answer = self._generate_live_no_ssl_control(
                session,
                normalized_question,
            )

        report = session.turn(normalized_question)

        if compare_without_ssl:
            if session.runtime_mode == "evaluation":
                baseline = report.get("baseline_answer")
                if baseline is None:
                    raise RuntimeError(
                        "evaluation comparison requested but the turn has no baseline answer"
                    )
                control_answer = str(baseline)
            if control_answer is None:
                raise RuntimeError("comparison requested but no no-SSL control was generated")
            comparison_fields = {
                "comparison_requested": True,
                "comparison_kind": (
                    "paired_live_no_ssl_control"
                    if session.runtime_mode == "live"
                    else "evaluation_control"
                ),
                "comparison_control_answer": control_answer,
                "comparison_ssl_answer": str(report.get("answer", "")),
                "comparison_ssl_influence_observed": bool(
                    report.get("surfaced_seed_ids", [])
                ),
                "comparison_interpretation": (
                    "The control used the same pre-turn visible history and model configuration "
                    "without surfaced Shadow Seeds. When no authorized seed surfaced, textual "
                    "differences must not be attributed to SSL."
                ),
            }
            report.update(comparison_fields)
            if session.turn_reports:
                session.turn_reports[-1].update(comparison_fields)

        self.repository.save_session(
            session_id,
            session.to_state(),
            updated_at=datetime.now().isoformat(),
        )
        return report

    def falsify(self, session_id: str, seed_id: str) -> dict[str, Any]:
        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])
        result = session.falsify(seed_id)
        self.repository.save_session(
            session_id,
            session.to_state(),
            updated_at=datetime.now().isoformat(),
        )
        return result

    def submit_verified_evidence(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str = "",
        operator_verified: bool = False,
    ) -> dict[str, Any]:
        """Persist explicit operator-attested support through the runtime Gate."""

        if not operator_verified:
            raise ValueError("operator verification must be explicitly confirmed")
        if not isinstance(source_ref, str):
            raise ValueError("source_ref must be a string")
        normalized_source = source_ref.strip()
        if not normalized_source:
            raise ValueError("source_ref must not be empty")
        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])
        if session.runtime_mode != "live":
            raise ValueError("verified evidence entry is available only for live sessions")
        result = session.submit_evidence(
            seed_id,
            ValidationSignal(
                kind=SignalKind.HUMAN_FEEDBACK,
                direction=SignalDirection.SUPPORT,
                verified=True,
                independent=True,
                source_ref=normalized_source,
                reason=note.strip() or "verified Workbench operator support",
            ),
        )
        self.repository.save_session(
            session_id,
            session.to_state(),
            updated_at=datetime.now().isoformat(),
        )
        return result

    def load(self, session_id: str) -> dict[str, Any]:
        return self.repository.load_session(session_id)

    def list_sessions(self) -> list[SessionSummary]:
        return self.repository.list_sessions()

    def inspect_seed(self, session_id: str, seed_id: str) -> dict[str, Any]:
        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])
        seed = session.manager.get_seed(seed_id)
        open_contradictions = [
            record.to_dict() for record in session.manager.open_contradictions(seed_id)
        ]
        gate_event = next(
            (event for event in reversed(session.manager.gate_events) if event.seed_id == seed_id),
            None,
        )
        return {
            **seed.to_dict(),
            "born_turn": session.born_turn.get(seed_id),
            "last_surfaced_turn": session.last_surfaced.get(seed_id),
            "open_contradictions": open_contradictions,
            "last_gate_event": gate_event.to_dict() if gate_event else None,
            "blocking": session.manager.is_blocking_contradiction(seed_id),
        }

    def record_feedback(self, feedback: TesterFeedback) -> TesterFeedback:
        if feedback.action != "record_only":
            raise ValueError(
                "foundation release supports record_only feedback; authority-changing "
                "feedback remains an explicit later workflow"
            )
        self.repository.load_session(feedback.session_id)
        return self.repository.add_feedback(feedback)

    def list_feedback(self, session_id: str) -> list[TesterFeedback]:
        return self.repository.list_feedback(session_id)

    def delete_session(self, session_id: str) -> None:
        self.repository.delete_session(session_id)


def service_for_workspace(workspace: str | Path | None = None) -> SessionService:
    from shadowseed.application.workspace import WorkspaceService

    workspace_service = WorkspaceService(workspace)
    workspace_service.initialize()
    return SessionService(workspace_service.repository)
