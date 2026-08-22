"""Tester-facing session orchestration over the existing ShadowChat runtime."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from shadowseed.application.auth import (
    CONTRADICTION_SUBMIT,
    EVIDENCE_VERIFY,
    ActorContext,
    require_capability,
)
from shadowseed.application.models import SessionConfig, SessionSummary, TesterFeedback
from shadowseed.application.profiles import get_profile
from shadowseed.chat import ShadowChatSession
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError
from shadowseed.surfacing import build_chat_prompt


class SessionService:
    def __init__(
        self,
        repository: SQLiteWorkspaceRepository,
        *,
        scope_id: str | None = None,
    ) -> None:
        self.repository = repository
        self.scope_id = scope_id
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
        """Generate a paired control without mutating SSL state."""

        fixture_answer = f"Fixture echo answer to: {question}"
        return session.model.generate(
            build_chat_prompt(
                session.history,
                question,
                [],
                response_language="the same language as the user's current question",
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
            control_answer = self._generate_live_no_ssl_control(session, normalized_question)

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
                "comparison_ssl_influence_observed": bool(report.get("surfaced_seed_ids", [])),
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
        """Research compatibility path; not production authorization."""

        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])
        result = session.falsify(seed_id)
        self.repository.save_session(
            session_id,
            session.to_state(),
            updated_at=datetime.now().isoformat(),
        )
        return result

    def falsify_authorized(
        self,
        session_id: str,
        seed_id: str,
        *,
        actor: ActorContext,
    ) -> dict[str, Any]:
        """Production contradiction submission guarded before runtime mutation."""

        authz = self._authorize(actor, CONTRADICTION_SUBMIT)
        replay = self.repository.authorized_request_result(
            actor.request_id,
            event_type=CONTRADICTION_SUBMIT,
            session_id=session_id,
            seed_id=seed_id,
        )
        if replay is not None:
            return {**replay, "authorization": authz}

        stored = self.repository.load_session(session_id)
        session = ShadowChatSession.from_state(stored["state"])
        result = session.falsify(seed_id)
        persisted = self.repository.save_authorized_session(
            session_id,
            session.to_state(),
            updated_at=datetime.now().isoformat(),
            authorization=authz,
            event_type=CONTRADICTION_SUBMIT,
            seed_id=seed_id,
            operation_result=result,
            event_metadata={"action": "operator_falsification"},
        )
        return {**persisted, "authorization": authz}

    def submit_verified_evidence(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str = "",
        operator_verified: bool = False,
    ) -> dict[str, Any]:
        """Research compatibility path; a bare boolean is not production authorization."""

        if not operator_verified:
            raise ValueError("operator verification must be explicitly confirmed")
        return self._submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=source_ref,
            note=note,
        )

    @staticmethod
    def _evidence_request_fingerprint(
        session_id: str,
        seed_id: str,
        source_ref: str,
        note: str,
    ) -> str:
        material = "\x1f".join(
            (
                EVIDENCE_VERIFY,
                session_id,
                seed_id,
                source_ref,
                note.strip(),
            )
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    @staticmethod
    def _validated_replay(
        replay: dict[str, Any],
        *,
        expected_fingerprint: str,
    ) -> dict[str, Any]:
        stored_fingerprint = replay.pop("_request_fingerprint", None)
        if stored_fingerprint != expected_fingerprint:
            raise WorkspaceStorageError(
                "request_id was replayed with different authority-operation input"
            )
        return replay

    def submit_verified_evidence_authorized(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str = "",
        actor: ActorContext,
    ) -> dict[str, Any]:
        """Production evidence submission requiring trusted attributable authorization."""

        authz = self._authorize(actor, EVIDENCE_VERIFY)
        normalized_source = self._normalize_source_ref(source_ref)
        request_fingerprint = self._evidence_request_fingerprint(
            session_id,
            seed_id,
            normalized_source,
            note,
        )
        replay = self.repository.authorized_request_result(
            actor.request_id,
            event_type=EVIDENCE_VERIFY,
            session_id=session_id,
            seed_id=seed_id,
        )
        if replay is not None:
            replay = self._validated_replay(
                replay, expected_fingerprint=request_fingerprint
            )
            return {**replay, "authorization": authz}

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
        persisted = self.repository.save_authorized_session(
            session_id,
            session.to_state(),
            updated_at=datetime.now().isoformat(),
            authorization=authz,
            event_type=EVIDENCE_VERIFY,
            seed_id=seed_id,
            operation_result={**result, "_request_fingerprint": request_fingerprint},
            event_metadata={
                "source_ref_sha256": hashlib.sha256(
                    normalized_source.encode("utf-8")
                ).hexdigest(),
                "note_sha256": hashlib.sha256(note.strip().encode("utf-8")).hexdigest(),
                "verified": True,
                "independent": True,
            },
        )
        persisted = self._validated_replay(
            persisted, expected_fingerprint=request_fingerprint
        )
        return {**persisted, "authorization": authz}

    @staticmethod
    def _normalize_source_ref(source_ref: str) -> str:
        if not isinstance(source_ref, str):
            raise ValueError("source_ref must be a string")
        normalized_source = source_ref.strip()
        if not normalized_source:
            raise ValueError("source_ref must not be empty")
        return normalized_source

    def _submit_verified_evidence(
        self,
        session_id: str,
        seed_id: str,
        *,
        source_ref: str,
        note: str,
    ) -> dict[str, Any]:
        normalized_source = self._normalize_source_ref(source_ref)
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

    def _authorize(self, actor: ActorContext, capability: str) -> dict[str, object]:
        if not self.scope_id:
            raise RuntimeError("production authorization requires a stable workspace scope")
        return require_capability(actor, scope_id=self.scope_id, capability=capability)

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
    return SessionService(
        workspace_service.repository,
        scope_id=workspace_service.workspace_id,
    )
