"""Tester feedback capture without implicit runtime authority changes."""

from __future__ import annotations

from shadowseed.application.models import TesterFeedback
from shadowseed.application.sessions import SessionService


OVERALL_CHOICES = ("better", "neutral", "worse", "unclear")
SEED_EFFECT_CHOICES = (
    "helpful",
    "harmful",
    "no_visible_effect",
    "unclear",
)


class FeedbackService:
    """Validate and persist tester observations as audit-only records."""

    def __init__(self, sessions: SessionService) -> None:
        self.sessions = sessions

    def record(
        self,
        *,
        session_id: str,
        turn_index: int,
        overall: str = "neutral",
        seed_effect: str = "no_visible_effect",
        note: str = "",
        seed_id: str | None = None,
    ) -> TesterFeedback:
        if overall not in OVERALL_CHOICES:
            raise ValueError(f"unknown overall rating: {overall}")
        if seed_effect not in SEED_EFFECT_CHOICES:
            raise ValueError(f"unknown seed effect: {seed_effect}")
        stored = self.sessions.load(session_id)
        reports = list(stored["state"].get("turn_reports", []))
        valid_turns = {int(item.get("turn", index)) for index, item in enumerate(reports)}
        if int(turn_index) not in valid_turns:
            raise ValueError(f"turn {turn_index} does not exist in session {session_id}")
        if seed_id:
            seed_ids = {
                str(seed.get("id"))
                for seed in stored["state"].get("manager", {}).get("seeds", [])
            }
            if seed_id not in seed_ids:
                raise ValueError(f"seed {seed_id!r} does not exist in session {session_id}")
        feedback = TesterFeedback(
            session_id=session_id,
            turn_index=int(turn_index),
            overall=overall,
            seed_effect=seed_effect,
            note=note.strip(),
            action="record_only",
            seed_id=seed_id or None,
        )
        return self.sessions.record_feedback(feedback)

    def list(self, session_id: str) -> list[TesterFeedback]:
        return self.sessions.list_feedback(session_id)
