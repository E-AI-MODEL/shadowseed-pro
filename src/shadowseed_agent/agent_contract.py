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

    def decide(
        self,
        seed: SeedLike,
        action: InfluenceAction | str,
        gate_log: Iterable[Any] = (),
    ) -> InfluenceDecision:
        seed_id = _seed_id(seed)
        action_value = str(getattr(action, "value", action))
        weight = float(_value(seed, "weight", 0.0) or 0.0)

        if not seed_id:
            return InfluenceDecision("", action_value, False, "missing_seed_id")
        if weight <= 0.0:
            return InfluenceDecision(seed_id, action_value, False, "weightless_seed")
        if _status_name(seed) != PROMOTED_STATUS:
            return InfluenceDecision(seed_id, action_value, False, "seed_not_promoted")

        contradiction_score = float(_value(seed, "contradiction_score", 0.0) or 0.0)
        if self.block_contradicted_seed and contradiction_score > 0.0:
            return InfluenceDecision(seed_id, action_value, False, "contradiction_present")

        if self.require_logged_promotion and not has_logged_promotion(seed_id, gate_log):
            return InfluenceDecision(seed_id, action_value, False, "missing_logged_promotion")

        return InfluenceDecision(seed_id, action_value, True, "allowed_promoted_gate_logged")

    def can_influence(
        self,
        seed: SeedLike,
        action: InfluenceAction | str,
        gate_log: Iterable[Any] = (),
    ) -> bool:
        return self.decide(seed, action, gate_log).allowed
