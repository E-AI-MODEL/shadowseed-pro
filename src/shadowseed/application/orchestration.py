"""Read-only human/SSL orchestration derived from canonical runtime state.

This module never mutates seed state and never grants authority. It translates
existing authority, contradiction, profile and Gate state into one small
application contract that Workbench surfaces can render consistently.
"""

from __future__ import annotations

from typing import Any, Mapping


SSL_TURN = "ssl_turn"
OPTIONAL_REVIEW = "optional_review"
HUMAN_TURN = "human_turn"
BLOCKED = "blocked"

ORCHESTRATION_STATES = frozenset(
    {SSL_TURN, OPTIONAL_REVIEW, HUMAN_TURN, BLOCKED}
)


def _result(
    state: str,
    *,
    reason_code: str,
    reason_text: str,
    required_action: str | None = None,
    optional_actions: tuple[str, ...] = (),
    no_action_effect: str,
    component: str,
    seed_id: str | None = None,
) -> dict[str, Any]:
    if state not in ORCHESTRATION_STATES:
        raise ValueError(f"unknown orchestration state: {state}")
    return {
        "state": state,
        "reason_code": reason_code,
        "reason_text": reason_text,
        "required_action": required_action,
        "optional_actions": list(optional_actions),
        "no_action_effect": no_action_effect,
        "component": component,
        "seed_id": seed_id,
    }


def derive_seed_orchestration(
    seed: Mapping[str, Any],
    *,
    authority_profile_id: str,
    gate_policy_id: str,
    recurrence_threshold: int,
) -> dict[str, Any]:
    """Describe who is expected to act next for one seed.

    The result is explanatory application state. All authority facts supplied
    here must already have been derived by the canonical runtime/inspection
    layer.
    """

    seed_id = str(seed.get("id", "")) or None
    status = str(seed.get("status", "")).upper()
    blocking = bool(seed.get("blocking", False))
    current_authorized = bool(seed.get("current_gate_authorized", False))
    occurrences = int(seed.get("occurrence_count", 0))
    evidence = int(seed.get("evidence_count", 0))
    profile = str(authority_profile_id or "strict")
    policy = str(gate_policy_id or "evidence_backed")

    if blocking:
        return _result(
            BLOCKED,
            reason_code="blocking_contradiction",
            reason_text=(
                "An open contradiction blocks influence and must be resolved "
                "explicitly first."
            ),
            required_action="resolve_contradiction",
            no_action_effect="The seed remains blocked and cannot influence an answer.",
            component="contradiction_resolution",
            seed_id=seed_id,
        )

    if status == "EXPIRED":
        return _result(
            BLOCKED,
            reason_code="expired_terminal",
            reason_text="The seed is expired and no longer belongs to active memory.",
            no_action_effect="No action is required; the expired seed remains outside influence.",
            component="lifecycle",
            seed_id=seed_id,
        )

    if status == "PROMOTED" and current_authorized:
        return _result(
            OPTIONAL_REVIEW,
            reason_code="authorized_for_consideration",
            reason_text=(
                "The seed is Gate-authorized. Relevance and point-of-use checks "
                "still decide whether it may be used for a concrete question."
            ),
            optional_actions=("inspect_seed",),
            no_action_effect="Shadowseed may continue autonomously; human review is optional.",
            component="point_of_use_authorization",
            seed_id=seed_id,
        )

    if status == "PROMOTED" and not current_authorized:
        if profile in {"strict", "assisted"} and policy == "evidence_backed":
            return _result(
                HUMAN_TURN,
                reason_code="current_gate_requires_verified_support",
                reason_text=(
                    "The seed was promoted earlier but does not satisfy the "
                    "current evidence-backed authorization."
                ),
                required_action="submit_verified_support",
                optional_actions=("inspect_gate_history",),
                no_action_effect="Historical promotion remains audit history, but influence stays blocked.",
                component="validation_gate",
                seed_id=seed_id,
            )
        return _result(
            SSL_TURN,
            reason_code="current_gate_not_yet_satisfied",
            reason_text=(
                "The seed was historically promoted, but the current Gate basis "
                "is insufficient. The autonomous runtime may collect new "
                "qualifying support."
            ),
            optional_actions=("inspect_gate_history",),
            no_action_effect="Shadowseed keeps observing; the seed is not used while authorization is missing.",
            component="validation_gate",
            seed_id=seed_id,
        )

    mature_recurrence = occurrences >= max(1, int(recurrence_threshold))
    manual_evidence_path = profile in {"strict", "assisted"} and policy == "evidence_backed"

    if mature_recurrence and manual_evidence_path and evidence <= 0:
        return _result(
            HUMAN_TURN,
            reason_code="verified_support_required",
            reason_text=(
                "The seed has recurred enough to require attention, but this "
                "authority route still requires verified support."
            ),
            required_action="submit_verified_support",
            optional_actions=("inspect_seed",),
            no_action_effect="The seed remains in shadow memory without authority to influence.",
            component="human_authority_actions",
            seed_id=seed_id,
        )

    if profile in {"autonomous", "open"}:
        return _result(
            SSL_TURN,
            reason_code="autonomous_observation",
            reason_text="The runtime may continue observing this seed autonomously and submit qualifying support to the Gate.",
            optional_actions=("inspect_seed",),
            no_action_effect="No human action is required; Shadowseed continues observing.",
            component="human_ssl_orchestration",
            seed_id=seed_id,
        )

    return _result(
        SSL_TURN,
        reason_code="awaiting_more_observation",
        reason_text="No human authority action is required yet; more valid observation is needed first.",
        optional_actions=("inspect_seed",),
        no_action_effect="Shadowseed keeps observing until the next decision boundary is reached.",
        component="human_ssl_orchestration",
        seed_id=seed_id,
    )


_STATE_PRIORITY = {
    BLOCKED: 3,
    HUMAN_TURN: 2,
    OPTIONAL_REVIEW: 1,
    SSL_TURN: 0,
}


def aggregate_session_orchestration(
    seed_states: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate seed orchestration deterministically for the session surface."""

    if not seed_states:
        return _result(
            SSL_TURN,
            reason_code="no_seed_action",
            reason_text="No seed currently requires human action.",
            no_action_effect="Shadowseed may continue observing the session normally.",
            component="human_ssl_orchestration",
        )

    selected = max(
        seed_states,
        key=lambda item: (
            _STATE_PRIORITY.get(str(item.get("state")), -1),
            str(item.get("seed_id") or ""),
        ),
    )
    matching = [
        item
        for item in seed_states
        if str(item.get("state")) == str(selected.get("state"))
    ]
    result = dict(selected)
    result["seed_id"] = None
    result["seed_ids"] = sorted(
        str(item.get("seed_id"))
        for item in matching
        if item.get("seed_id")
    )
    result["affected_seed_count"] = len(result["seed_ids"])
    return result


__all__ = [
    "SSL_TURN",
    "OPTIONAL_REVIEW",
    "HUMAN_TURN",
    "BLOCKED",
    "ORCHESTRATION_STATES",
    "derive_seed_orchestration",
    "aggregate_session_orchestration",
]
