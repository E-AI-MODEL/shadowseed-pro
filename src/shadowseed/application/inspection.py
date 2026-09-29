"""Read-only tester inspection views over persisted Workbench sessions.

This module deliberately consumes persisted application state instead of
re-implementing runtime authority. It explains what happened; it never grants
permission, changes seed state, or calls the Validation Gate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shadowseed.application.sessions import SessionService


_STATUS_EXPLANATIONS = {
    "open": "Observed in the shadow layer; not authorized to influence an answer.",
    "dormant": "Retained for possible later reactivation; not currently authorized to influence.",
    "promoted": (
        "Promoted by the Validation Gate. It may influence only when relevance and "
        "the point-of-use safety checks also allow it."
    ),
    "contradicted": "Contradicted and blocked from influence while the contradiction is active.",
    "expired": "Expired from the active lifecycle and unavailable for influence.",
}


def _references_seed(value: Any, seed_id: str) -> bool:
    """Return whether a ledger payload explicitly references ``seed_id``."""

    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"seed_id", "source_seed_id", "target_seed_id"} and str(item) == seed_id:
                return True
            if key in {"seed_ids", "members"} and isinstance(item, (list, tuple, set)):
                if any(str(member) == seed_id for member in item):
                    return True
            if isinstance(item, (dict, list, tuple)) and _references_seed(item, seed_id):
                return True
        return False
    if isinstance(value, (list, tuple)):
        return any(_references_seed(item, seed_id) for item in value)
    return False


def _timestamp_sort_key(value: Any) -> tuple[int, float]:
    """Return a stable chronological key for persisted ISO-8601 timestamps.

    Missing or malformed timestamps sort before timestamped entries. Timestamped
    values are normalized to UTC so different offsets are ordered by the actual
    instant rather than by their textual representation.
    """

    if value in (None, ""):
        return (0, 0.0)
    text = str(value).strip()
    if not text:
        return (0, 0.0)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return (0, 0.0)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return (1, parsed.astimezone(timezone.utc).timestamp())


def explain_seed(seed: dict[str, Any], *, blocking: bool = False) -> str:
    """Give a plain-language, non-authorizing explanation of one seed snapshot."""

    status = str(seed.get("status", "open")).lower()
    explanation = _STATUS_EXPLANATIONS.get(
        status,
        "Stored in the shadow layer. Its current snapshot alone does not authorize influence.",
    )
    if blocking:
        explanation += " An open contradiction currently blocks point-of-use influence."
    return explanation


class InspectionService:
    """Build read-only views for session, seed, and audit inspection."""

    def __init__(self, sessions: SessionService) -> None:
        self.sessions = sessions

    def session_view(self, session_id: str) -> dict[str, Any]:
        stored = self.sessions.load(session_id)
        state = dict(stored["state"])
        session_config = dict(state.get("session_config", {}))
        persisted_config = dict(stored.get("config", {}))
        runtime_mode = session_config.get("runtime_mode") or persisted_config.get(
            "runtime_mode", "evaluation"
        )
        if runtime_mode not in {"evaluation", "live"}:
            runtime_mode = "evaluation"
        manager = dict(state.get("manager", {}))
        seeds = [dict(seed) for seed in manager.get("seeds", [])]
        authority_profile_id = str(
            session_config.get("authority_profile_id")
            or persisted_config.get("authority_profile_id", "strict")
        )
        effective_gate_policy_id = str(
            session_config.get("gate_policy_id")
            or persisted_config.get("gate_policy_id")
            or ("evidence_backed" if runtime_mode == "live" else "exploratory")
        )
        blocking_ids = {
            str(item.get("seed_id"))
            for item in manager.get("contradiction_records", [])
            if str(item.get("status", "open")).lower() == "open"
        }
        decorated = [
            {
                **seed,
                "blocking": str(seed.get("id")) in blocking_ids,
                "plain_explanation": explain_seed(
                    seed, blocking=str(seed.get("id")) in blocking_ids
                ),
            }
            for seed in seeds
        ]

        review_seed_ids: list[str] = []
        if authority_profile_id == "assisted":
            manager_config = dict(manager.get("config", {}))
            recurrence_threshold = int(manager_config.get("min_occurrences_for_gate", 3))
            seed_to_cluster = {
                str(key): int(value)
                for key, value in dict(state.get("seed_to_cluster", {})).items()
            }
            cluster_rep = {
                int(key): str(value)
                for key, value in dict(state.get("cluster_rep", {})).items()
            }
            for seed in decorated:
                seed_id = str(seed.get("id", ""))
                status = str(seed.get("status", "")).upper()
                occurrence_count = int(seed.get("occurrence_count", 0))
                cluster_id = seed_to_cluster.get(seed_id)
                is_representative = (
                    cluster_id is None or cluster_rep.get(cluster_id) == seed_id
                )
                if (
                    seed_id not in blocking_ids
                    and status not in {"PROMOTED", "EXPIRED"}
                    and is_representative
                    and occurrence_count >= recurrence_threshold
                ):
                    review_seed_ids.append(seed_id)

        return {
            "session_id": stored["session_id"],
            "title": stored["title"],
            "profile_id": stored["profile_id"],
            "backend": stored["backend"],
            "model_id": stored["model_id"],
            "runtime_mode": runtime_mode,
            "authority_profile_id": authority_profile_id,
            "effective_gate_policy_id": effective_gate_policy_id,
            "authority_review_seed_ids": review_seed_ids,
            "created_at": stored["created_at"],
            "updated_at": stored["updated_at"],
            "turn": int(state.get("turn", len(state.get("turn_reports", [])))),
            "turn_reports": list(state.get("turn_reports", [])),
            "seeds": decorated,
            "feedback": [item.to_dict() for item in self.sessions.list_feedback(session_id)],
        }

    def seed_view(self, session_id: str, seed_id: str) -> dict[str, Any]:
        seed = self.sessions.inspect_seed(session_id, seed_id)
        session = self.session_view(session_id)
        review_ids = {str(item) for item in session.get("authority_review_seed_ids", [])}
        return {
            **seed,
            "authority_profile_id": session.get("authority_profile_id", "strict"),
            "effective_gate_policy_id": session.get("effective_gate_policy_id"),
            "review_required": str(seed_id) in review_ids,
            "plain_explanation": explain_seed(seed, blocking=bool(seed.get("blocking"))),
            "timeline": self.seed_timeline(session_id, seed_id),
        }

    def seed_timeline(self, session_id: str, seed_id: str) -> list[dict[str, Any]]:
        stored = self.sessions.load(session_id)
        state = dict(stored["state"])
        manager = dict(state.get("manager", {}))
        sources = (
            ("seed_event", manager.get("event_log", [])),
            ("validation", manager.get("validation_log", [])),
            ("gate", manager.get("gate_events", [])),
            ("contradiction", manager.get("contradiction_records", [])),
            ("probe_feedback", manager.get("feedback_log", [])),
            ("influence", state.get("influence_records", [])),
        )
        collected: list[tuple[tuple[int, float], int, int, dict[str, Any]]] = []
        for category_index, (event_type, items) in enumerate(sources):
            for item_index, item in enumerate(items):
                if not isinstance(item, dict) or not _references_seed(item, seed_id):
                    continue
                timestamp = item.get("created_at") or item.get("timestamp") or item.get("at")
                collected.append(
                    (
                        _timestamp_sort_key(timestamp),
                        category_index,
                        item_index,
                        {
                            "type": event_type,
                            "timestamp": timestamp,
                            "payload": dict(item),
                        },
                    )
                )
        collected.sort(key=lambda entry: (entry[0], entry[1], entry[2]))
        return [
            {"sequence": sequence, **entry[3]}
            for sequence, entry in enumerate(collected)
        ]
