"""Read-only tester inspection views over persisted Workbench sessions.

This module deliberately consumes persisted application state instead of
re-implementing runtime authority. It explains what happened; it never grants
permission, changes seed state, or calls the Validation Gate.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from shadowseed.application.configuration import setting_metadata
from shadowseed.application.orchestration import (
    aggregate_session_orchestration,
    derive_seed_orchestration,
)
from shadowseed.application.sessions import SessionService
from shadowseed.authority_profiles import resolve_authority_runtime
from shadowseed.gate.current_authority import snapshot_meets_current_gate
from shadowseed.storage.integrity import (
    behavior_config_digest,
    behavior_config_epoch,
    behavior_config_projection,
)


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
        configured_gate_policy_id = persisted_config.get("gate_policy_id")
        profile_default_gate_policy_id = resolve_authority_runtime(
            authority_profile_id,
            runtime_mode=runtime_mode,
            configured_gate_policy_id=None,
        ).gate_policy_id
        effective_gate_policy_id = str(
            session_config.get("gate_policy_id")
            or configured_gate_policy_id
            or profile_default_gate_policy_id
        )
        gate_policy_override_active = bool(
            configured_gate_policy_id
            and str(configured_gate_policy_id) != profile_default_gate_policy_id
        )
        blocking_ids = {
            str(item.get("seed_id"))
            for item in manager.get("contradiction_records", [])
            if str(item.get("status", "open")).lower() == "open"
        }
        manager_config = dict(manager.get("config", {}))
        decorated = []
        for seed in seeds:
            seed_id = str(seed.get("id"))
            blocking = seed_id in blocking_ids
            revalidate_current_gate = bool(
                session_config.get(
                    "revalidate_current_gate",
                    persisted_config.get("revalidate_current_gate", False),
                )
            )
            current_gate_authorized = (
                snapshot_meets_current_gate(
                    seed,
                    manager_config,
                    effective_gate_policy_id,
                    blocking=blocking,
                    gate_events=manager.get("gate_events", []),
                )
                if revalidate_current_gate
                else (
                    str(seed.get("status", "")).upper() == "PROMOTED"
                    and not blocking
                )
            )
            plain_explanation = explain_seed(seed, blocking=blocking)
            if (
                str(seed.get("status", "")).upper() == "PROMOTED"
                and not current_gate_authorized
            ):
                plain_explanation += (
                    " It was promoted under an earlier Gate state, but the current "
                    "Gate no longer authorizes point-of-use influence."
                )
            decorated_seed = {
                **seed,
                "blocking": blocking,
                "current_gate_authorized": current_gate_authorized,
                "plain_explanation": plain_explanation,
            }
            decorated_seed["orchestration"] = derive_seed_orchestration(
                decorated_seed,
                authority_profile_id=authority_profile_id,
                gate_policy_id=effective_gate_policy_id,
                recurrence_threshold=int(
                    manager_config.get("min_occurrences_for_gate", 3)
                ),
            )
            decorated.append(decorated_seed)

        review_seed_ids: list[str] = []
        if (
            authority_profile_id == "assisted"
            and effective_gate_policy_id == "evidence_backed"
        ):
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
                    and status != "EXPIRED"
                    and not bool(seed.get("current_gate_authorized", False))
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
            "revision_backend": (
                session_config.get("revision_backend")
                or persisted_config.get("revision_backend")
                or stored["backend"]
            ),
            "revision_model_id": (
                session_config.get("revision_model_id")
                if session_config.get("revision_model_id") is not None
                else persisted_config.get("revision_model_id", stored["model_id"])
            ),
            "runtime_mode": runtime_mode,
            "authority_profile_id": authority_profile_id,
            "profile_default_gate_policy_id": profile_default_gate_policy_id,
            "configured_gate_policy_id": configured_gate_policy_id,
            "effective_gate_policy_id": effective_gate_policy_id,
            "gate_policy_override_active": gate_policy_override_active,
            "embedding_backend": str(
                session_config.get("embedding_backend")
                or persisted_config.get("embedding_backend", "lexical")
            ),
            "recurrence_mode": str(
                session_config.get("recurrence_mode")
                or persisted_config.get("recurrence_mode", "cluster")
            ),
            "surface_top_k": int(
                session_config.get(
                    "surface_top_k",
                    persisted_config.get("surface_top_k", 2),
                )
            ),
            "ssl_intensity": (
                int(persisted_config["ssl_intensity"])
                if persisted_config.get("ssl_intensity") is not None
                else None
            ),
            "gate_strictness": (
                int(persisted_config["gate_strictness"])
                if persisted_config.get("gate_strictness") is not None
                else None
            ),
            "allow_same_turn_revision": bool(
                persisted_config.get(
                    "allow_same_turn_revision",
                    persisted_config.get("allow_self_reinforcement", False),
                )
            ),
            "self_derived_signal_policy": str(
                persisted_config.get("self_derived_signal_policy", "fail_closed")
            ),
            "allow_self_reinforcement": bool(
                persisted_config.get("allow_self_reinforcement", False)
            ),
            "authority_review_seed_ids": review_seed_ids,
            "orchestration": aggregate_session_orchestration(
                [dict(seed["orchestration"]) for seed in decorated]
            ),
            "created_at": stored["created_at"],
            "updated_at": stored["updated_at"],
            "turn": int(state.get("turn", len(state.get("turn_reports", [])))),
            "turn_reports": list(state.get("turn_reports", [])),
            "seeds": decorated,
            "feedback": [item.to_dict() for item in self.sessions.list_feedback(session_id)],
            # Full configuration snapshots are exposed for the local Workbench
            # control and audit surfaces. They are configuration only; no
            # credentials or secrets are stored in these records.
            "persisted_config": persisted_config,
            "session_config": session_config,
            "core_config": manager_config,
            "setting_metadata": setting_metadata(),
            "behavior_config": behavior_config_projection(state),
            "behavior_config_digest": behavior_config_digest(state),
            "behavior_config_epoch": behavior_config_epoch(state),
        }

    def seed_view(self, session_id: str, seed_id: str) -> dict[str, Any]:
        seed = self.sessions.inspect_seed(session_id, seed_id)
        session = self.session_view(session_id)
        review_ids = {str(item) for item in session.get("authority_review_seed_ids", [])}
        decorated = next(
            (
                dict(item)
                for item in session.get("seeds", [])
                if str(item.get("id")) == str(seed_id)
            ),
            {},
        )
        merged = {**seed, **decorated}
        return {
            **merged,
            "authority_profile_id": session.get("authority_profile_id", "strict"),
            "effective_gate_policy_id": session.get("effective_gate_policy_id"),
            "review_required": str(seed_id) in review_ids,
            "plain_explanation": str(
                merged.get("plain_explanation")
                or explain_seed(merged, blocking=bool(merged.get("blocking")))
            ),
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
