"""Tester-facing session orchestration over the existing ShadowChat runtime."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from shadowseed.application.models import SessionConfig, SessionSummary, TesterFeedback
from shadowseed.application.profiles import get_profile
from shadowseed.chat import ShadowChatSession
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository


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

    def run_turn(self, session_id: str, question: str) -> dict[str, Any]:
        if not question or not question.strip():
            raise ValueError("question must not be empty")
        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])
        report = session.turn(question.strip())
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
