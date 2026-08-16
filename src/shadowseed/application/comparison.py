"""Side-by-side and blind comparison of persisted baseline and SSL answers."""

from __future__ import annotations

import hashlib
from typing import Any

from shadowseed.application.sessions import SessionService


class ComparisonService:
    """Compare outputs already produced by one ShadowChat turn.

    The service does not score quality automatically. It presents the clean
    baseline and SSL-visible answer for human comparison and can hide which is
    which until reveal time.
    """

    def __init__(self, sessions: SessionService) -> None:
        self.sessions = sessions

    def compare_turn(
        self,
        session_id: str,
        turn_index: int,
        *,
        blinded: bool = True,
        reveal: bool = False,
    ) -> dict[str, Any]:
        stored = self.sessions.load(session_id)
        state = dict(stored["state"])
        reports = list(state.get("turn_reports", []))
        report = next(
            (
                item
                for index, item in enumerate(reports)
                if int(item.get("turn", index)) == int(turn_index)
            ),
            None,
        )
        if report is None:
            raise ValueError(f"turn {turn_index} does not exist in session {session_id}")
        state_config = dict(state.get("session_config", {}))
        persisted_config = dict(stored.get("config", {}))
        runtime_mode = (
            report.get("runtime_mode")
            or state_config.get("runtime_mode")
            or persisted_config.get("runtime_mode", "evaluation")
        )
        if runtime_mode not in {"evaluation", "live"}:
            runtime_mode = "evaluation"
        if runtime_mode != "evaluation":
            raise ValueError(
                "baseline comparison is available only for evaluation sessions; "
                "live sessions intentionally perform one visible generation"
            )
        baseline_value = report.get("baseline_answer")
        if baseline_value is None:
            raise ValueError("evaluation turn does not contain a baseline answer")
        baseline = str(baseline_value)
        ssl_answer = str(report.get("ssl_answer", report.get("answer", "")))
        # Stable ordering makes a blinded comparison reproducible without
        # persisting additional hidden state.
        digest = hashlib.sha256(f"{session_id}:{turn_index}".encode("utf-8")).digest()
        baseline_first = digest[0] % 2 == 0
        if baseline_first:
            candidate_a, candidate_b = baseline, ssl_answer
            mapping = {"A": "baseline", "B": "shadowseed"}
        else:
            candidate_a, candidate_b = ssl_answer, baseline
            mapping = {"A": "shadowseed", "B": "baseline"}
        result: dict[str, Any] = {
            "session_id": session_id,
            "turn": int(turn_index),
            "question": str(report.get("question", "")),
            "candidate_a": candidate_a,
            "candidate_b": candidate_b,
            "same_output": baseline == ssl_answer,
            "surfaced_seed_ids": list(report.get("surfaced_seed_ids", [])),
            "blinded": bool(blinded),
        }
        if not blinded:
            result["candidate_a_label"] = mapping["A"]
            result["candidate_b_label"] = mapping["B"]
        elif reveal:
            result["revealed_mapping"] = mapping
        return result
