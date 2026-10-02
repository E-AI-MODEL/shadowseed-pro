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
                "Een open tegenspraak blokkeert invloed. Die tegenspraak moet "
                "eerst expliciet worden afgehandeld."
            ),
            required_action="resolve_contradiction",
            no_action_effect="De seed blijft geblokkeerd en kan geen antwoord beïnvloeden.",
            component="contradiction_resolution",
            seed_id=seed_id,
        )

    if status == "EXPIRED":
        return _result(
            BLOCKED,
            reason_code="expired_terminal",
            reason_text="De seed is verlopen en hoort niet meer bij de actieve memory.",
            no_action_effect="Er is geen actie nodig; de verlopen seed blijft buiten invloed.",
            component="lifecycle",
            seed_id=seed_id,
        )

    if status == "PROMOTED" and current_authorized:
        return _result(
            OPTIONAL_REVIEW,
            reason_code="authorized_for_consideration",
            reason_text=(
                "De seed is Gate-geautoriseerd. Relevantie en de point-of-use "
                "controle bepalen pas bij een concrete vraag of hij wordt gebruikt."
            ),
            optional_actions=("inspect_seed",),
            no_action_effect="Shadowseed kan zelfstandig doorgaan; menselijke review is optioneel.",
            component="point_of_use_authorization",
            seed_id=seed_id,
        )

    if status == "PROMOTED" and not current_authorized:
        if profile in {"strict", "assisted"} and policy == "evidence_backed":
            return _result(
                HUMAN_TURN,
                reason_code="current_gate_requires_verified_support",
                reason_text=(
                    "De seed was eerder gepromoveerd, maar voldoet niet aan de "
                    "huidige evidence-backed autorisatie."
                ),
                required_action="submit_verified_support",
                optional_actions=("inspect_gate_history",),
                no_action_effect="De historische promotie blijft auditgeschiedenis, maar invloed blijft geblokkeerd.",
                component="validation_gate",
                seed_id=seed_id,
            )
        return _result(
            SSL_TURN,
            reason_code="current_gate_not_yet_satisfied",
            reason_text=(
                "De seed is historisch gepromoveerd, maar de huidige Gate-basis "
                "is niet toereikend. De autonome runtime kan nieuwe kwalificerende "
                "ondersteuning verzamelen."
            ),
            optional_actions=("inspect_gate_history",),
            no_action_effect="Shadowseed blijft observeren; de seed wordt niet gebruikt zolang autorisatie ontbreekt.",
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
                "De seed is vaak genoeg teruggekomen om aandacht te verdienen, "
                "maar deze authority-route vereist nog geverifieerde ondersteuning."
            ),
            required_action="submit_verified_support",
            optional_actions=("inspect_seed",),
            no_action_effect="De seed blijft in shadow memory zonder authority voor invloed.",
            component="human_authority_actions",
            seed_id=seed_id,
        )

    if profile in {"autonomous", "open"}:
        return _result(
            SSL_TURN,
            reason_code="autonomous_observation",
            reason_text="De runtime kan deze seed zelfstandig verder observeren en via de Gate laten beoordelen.",
            optional_actions=("inspect_seed",),
            no_action_effect="Geen menselijke actie nodig; Shadowseed gaat verder met observeren.",
            component="human_ssl_orchestration",
            seed_id=seed_id,
        )

    return _result(
        SSL_TURN,
        reason_code="awaiting_more_observation",
        reason_text="Er is nog geen menselijke authority-actie nodig; eerst is meer geldige observatie nodig.",
        optional_actions=("inspect_seed",),
        no_action_effect="Shadowseed blijft observeren totdat een volgende beslisgrens wordt bereikt.",
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
            reason_text="Er is op dit moment geen seed waarvoor menselijke actie nodig is.",
            no_action_effect="Shadowseed kan de sessie normaal blijven observeren.",
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
