"""Safety contract for agent/RAG integrations around Shadow Seed Learning.

The core SSL runtime already separates trace from weight. This adapter layer
makes that separation explicit at the boundary where an agent might otherwise
let a seed influence retrieval, probes, answer text, tool calls, warnings, or
other decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Protocol

PROMOTED_STATUS = "PROMOTED"
GENERATED_EVIDENCE_KINDS = {
    "completion",
    "generated_completion",
    "llm_output",
    "model_output",
}


class InfluenceAction(str, Enum):
    """Agent actions that must not be driven by weightless seeds."""

    RETRIEVAL = "retrieval"
    PROBE = "probe"
    ANSWER_MODIFICATION = "answer_modification"
    TOOL_CALL = "tool_call"
    WARNING = "warning"
    DECISION = "decision"


class SeedLike(Protocol):
    id: str
    weight: float
    status: Any


@dataclass(frozen=True)
class InfluenceDecision:
    """Decision record for one attempted seed-driven agent action."""

    seed_id: str
    action: str
    allowed: bool
    reason: str
    gate_event_ref: str | None = None


def _value(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _status_name(seed: Any) -> str:
    status = _value(seed, "status", "")
    return str(getattr(status, "value", status))


def _seed_id(seed: Any) -> str:
    return str(_value(seed, "id", _value(seed, "seed_id", "")))


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def has_logged_promotion(seed_id: str, gate_log: Iterable[Any]) -> bool:
    """Return whether the gate log contains a promotion for this seed.

    This accepts either `ValidationGateResult` instances or dict-like exported
    records. The agent layer should require this before a promoted seed can
    steer retrieval or other downstream behavior.
    """

    for entry in gate_log:
        if str(_value(entry, "seed_id", "")) != seed_id:
            continue
        promoted = _as_bool(_value(entry, "promoted", False))
        status_after = str(_value(entry, "status_after", ""))
        verdict = str(_value(entry, "verdict", ""))
        if (promoted or status_after == PROMOTED_STATUS) and verdict != "expired_noop":
            return True
    return False


def evidence_can_support_gate(evidence_ref: Any) -> bool:
    """Return whether an evidence reference is eligible for gate support.

    LLM/generated output is not trusted evidence at the agent boundary. It can
    be stored as a proposal elsewhere, but it must not count as verified support
    for influence.
    """

    kind = str(
        _value(
            evidence_ref,
            "kind",
            _value(
                evidence_ref,
                "evidence_kind",
                _value(evidence_ref, "source_kind", _value(evidence_ref, "source", "")),
            ),
        )
    ).strip().lower()
    if kind in GENERATED_EVIDENCE_KINDS:
        return False
    return _as_bool(_value(evidence_ref, "verified", False))


@dataclass(frozen=True)
class AgentSafetyContract:
    """Policy guard for using SSL seeds inside agents.

    The contract is intentionally conservative:
    - a seed with weight <= 0 can never influence an agent action;
    - a seed must be `PROMOTED`;
    - a promotion must be present in the gate log;
    - an active contradiction score blocks influence by default.
    """

    require_logged_promotion: bool = True
    block_contradicted_seed: bool = True

    def _decide(
        self,
        seed: SeedLike,
        action: InfluenceAction | str,
        gate_log: Iterable[Any] = (),
        *,
        contradiction_blocking: bool | None = None,
    ) -> InfluenceDecision:
        """Internal decision logic. Does not record. Use ``decide_and_record``.

        ``contradiction_blocking``, when provided, is the canonical blocking
        state derived from contradiction records (#13); it takes precedence over
        the legacy scalar.
        """

        seed_id = _seed_id(seed)
        action_value = str(getattr(action, "value", action))
        weight = float(_value(seed, "weight", 0.0) or 0.0)

        if not seed_id:
            return InfluenceDecision("", action_value, False, "missing_seed_id")
        if weight <= 0.0:
            return InfluenceDecision(seed_id, action_value, False, "weightless_seed")
        if _status_name(seed) != PROMOTED_STATUS:
            return InfluenceDecision(seed_id, action_value, False, "seed_not_promoted")

        if contradiction_blocking is None:
            contradiction_blocking = (
                float(_value(seed, "contradiction_score", 0.0) or 0.0) > 0.0
            )
        if self.block_contradicted_seed and contradiction_blocking:
            return InfluenceDecision(seed_id, action_value, False, "contradiction_present")

        if self.require_logged_promotion and not has_logged_promotion(seed_id, gate_log):
            return InfluenceDecision(seed_id, action_value, False, "missing_logged_promotion")

        return InfluenceDecision(seed_id, action_value, True, "allowed_promoted_gate_logged")

    def inspect(
        self,
        seed: SeedLike,
        action: InfluenceAction | str,
        gate_log: Iterable[Any] = (),
        *,
        contradiction_blocking: bool | None = None,
    ) -> InfluenceDecision:
        """Report a seed's current eligibility for status/UX purposes only.

        This is explicitly **not** an authorization: its result must never be
        used to gate an actual influence. To let a seed influence an action, use
        :meth:`decide_and_record`, which records the decision and links it to a
        Gate event. ``inspect`` exists so callers can display "blocked" /
        "eligible" without recording a spurious influence attempt.

        (The former public ``decide``/``can_influence`` methods were removed:
        they returned an allowed verdict that could be used to drive influence
        without recording, which the point-of-use contract forbids.)
        """

        return self._decide(
            seed, action, gate_log, contradiction_blocking=contradiction_blocking
        )

    def decide_and_record(
        self,
        seed: SeedLike,
        action: InfluenceAction | str,
        *,
        gate_events: Iterable[Any],
        ledger: list,
        contradiction_blocking: bool,
        context_ref: str | None = None,
        now: str | None = None,
    ):
        """Decide and record one influence attempt as a single atomic step.

        This is the mandatory point-of-use API (#14): a decision cannot be used
        without being recorded, because the record is produced here and appended
        to ``ledger`` before the decision is returned. Each allowed decision is
        linked to the Gate event that authorized it, and the seed's authority
        version is snapshotted so a stale authorization can be detected on
        replay. ``gate_events`` is consumed both for the promotion check and for
        the event linkage, so it should be the manager's ``gate_events`` ledger.

        Returns the recorded ``AgentInfluenceRecord``.
        """

        from shadowseed_agent.audit_policy import AgentInfluenceRecord

        events = list(gate_events)
        seed_id = _seed_id(seed)
        current_version = _value(seed, "authority_version", None)

        decision = self._decide(
            seed, action, events, contradiction_blocking=contradiction_blocking
        )
        allowed = decision.allowed
        reason = decision.reason

        # Link only to the Gate event that established the seed's *current*
        # authority: same seed, promoted, current authority version, and no
        # blocking contradiction recorded on that event.
        ref, event_version, policy_id = self._link_gate_event(
            seed_id, events, current_version
        )

        # Stale-authorization guard at decision time: an allowed decision must
        # reference a live, current-version promotion — not just any past one.
        if allowed and (ref is None or event_version != current_version):
            allowed = False
            reason = "stale_gate_authorization"

        record = AgentInfluenceRecord(
            seed_id=decision.seed_id,
            action=decision.action,
            seed_weight=float(_value(seed, "weight", 0.0) or 0.0),
            seed_status=_status_name(seed),
            allowed=allowed,
            reason=reason,
            gate_event_ref=ref,
            authority_version=current_version,
            contradiction_blocking=bool(contradiction_blocking),
            policy_id=policy_id,
            context_ref=context_ref,
            decided_at=now,
        )
        ledger.append(record)
        return record

    #: Gate decisions that establish or confirm positive authority. Only these
    #: may act as the authorizing event for an influence decision; a later
    #: BLOCKED/NO_CHANGE/etc. event that happens to leave status_after==PROMOTED
    #: must never be treated as the authorization.
    _AUTHORITY_CONFIRMING_DECISIONS = frozenset({"promoted", "validated"})

    @staticmethod
    def _link_gate_event(
        seed_id: str,
        gate_events: Iterable[Any],
        current_version: int | None = None,
    ) -> tuple[str | None, int | None, str | None]:
        """Return (event_id, authority_version, policy_id) of the latest Gate
        event that represents the seed's current promoted authority.

        Selects the latest event for the same seed that (a) carries an
        authority-confirming decision (promoted/validated), (b) left the seed
        promoted, (c) records a non-blocking contradiction state, and (d) — when
        ``current_version`` is given — matches the seed's current authority
        version. Returns ``(None, None, None)`` if none qualifies, which the
        caller treats as a stale or missing authorization.
        """

        latest = None
        for event in gate_events:
            if str(_value(event, "seed_id", "")) != seed_id:
                continue
            decision = _value(event, "decision", "")
            decision_value = str(getattr(decision, "value", decision))
            if decision_value not in AgentSafetyContract._AUTHORITY_CONFIRMING_DECISIONS:
                continue
            if str(_value(event, "status_after", "")) != PROMOTED_STATUS:
                continue
            contradiction_after = _value(event, "contradiction_after", None)
            if contradiction_after is not None and _value(contradiction_after, "blocking", False):
                continue
            event_version = _value(event, "authority_version", None)
            if current_version is not None and event_version != current_version:
                continue
            latest = event
        if latest is None:
            return None, None, None
        return (
            _value(latest, "event_id", None),
            _value(latest, "authority_version", None),
            _value(latest, "policy_id", None),
        )
