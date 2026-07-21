"""Immutable Gate events: the authority-change audit ledger.

Every Validation Gate invocation produces exactly one ``GateEvent``. The event
is the sole audit record that an authority change (or a refusal to change
authority) happened, and it captures enough typed detail to reconstruct the
decision during replay (ADR-001, "Audit requirements").

The record is immutable. Point-of-use influence decisions (issue #14) reference
a ``GateEvent`` by ``event_id`` and by ``authority_version`` so a stale
authorization can be detected during replay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Sequence

from shadowseed.gate.signals import ValidationSignal


class GateDecision(str, Enum):
    """What the Gate did with the offered signals."""

    PROMOTED = "promoted"
    VALIDATED = "validated"
    DEMOTED = "demoted"
    BLOCKED = "blocked"
    CONTRADICTED = "contradicted"
    CONTRADICTION_RESOLVED = "contradiction_resolved"
    EXPIRED = "expired"
    NO_CHANGE = "no_change"


@dataclass(frozen=True)
class ContradictionState:
    """Snapshot of a seed's blocking-contradiction state at decision time.

    ``open_count`` derives from unresolved contradiction records (issue #13);
    ``score`` is the legacy scalar retained for compatibility. ``blocking`` is
    the single boolean the point-of-use contract consults.
    """

    blocking: bool = False
    open_count: int = 0
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "blocking": self.blocking,
            "open_count": self.open_count,
            "score": self.score,
        }


@dataclass(frozen=True)
class GateEvent:
    """One immutable authority-decision record.

    ``authority_version`` is a monotonically increasing counter the manager
    stamps on a seed's authority state; it lets a later point-of-use decision
    prove it referenced the authority that was current when it was made.
    """

    event_id: str
    seed_id: str
    policy_id: str
    decision: GateDecision
    signals: tuple[ValidationSignal, ...] = ()
    status_before: str = ""
    status_after: str = ""
    weight_before: float = 0.0
    weight_after: float = 0.0
    contradiction_before: ContradictionState = field(default_factory=ContradictionState)
    contradiction_after: ContradictionState = field(default_factory=ContradictionState)
    authority_version: int = 0
    reason: str = ""
    created_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", GateDecision(self.decision))
        object.__setattr__(self, "signals", tuple(self.signals))

    @property
    def weight_delta(self) -> float:
        return self.weight_after - self.weight_before

    @property
    def changed_authority(self) -> bool:
        """Whether this event actually altered authority state."""

        return (
            self.weight_after != self.weight_before
            or self.status_after != self.status_before
            or self.contradiction_after != self.contradiction_before
        )

    def to_dict(self) -> dict[str, Any]:
        """Deterministic, ordered serialization for audit and replay.

        ``created_at`` is included as-is (possibly ``None``); callers that need
        deterministic replay hashing should exclude timestamps or inject a fixed
        clock, rather than relying on wall-clock time being stable.
        """

        return {
            "event_id": self.event_id,
            "seed_id": self.seed_id,
            "policy_id": self.policy_id,
            "decision": self.decision.value,
            "signals": [signal.to_dict() for signal in self.signals],
            "status_before": self.status_before,
            "status_after": self.status_after,
            "weight_before": self.weight_before,
            "weight_after": self.weight_after,
            "weight_delta": self.weight_delta,
            "contradiction_before": self.contradiction_before.to_dict(),
            "contradiction_after": self.contradiction_after.to_dict(),
            "authority_version": self.authority_version,
            "reason": self.reason,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GateEvent":
        def _contradiction(raw: dict[str, Any] | None) -> ContradictionState:
            raw = raw or {}
            return ContradictionState(
                blocking=bool(raw.get("blocking", False)),
                open_count=int(raw.get("open_count", 0)),
                score=float(raw.get("score", 0.0)),
            )

        return cls(
            event_id=data["event_id"],
            seed_id=data["seed_id"],
            policy_id=data["policy_id"],
            decision=GateDecision(data["decision"]),
            signals=tuple(
                ValidationSignal.from_dict(signal) for signal in data.get("signals", [])
            ),
            status_before=data.get("status_before", ""),
            status_after=data.get("status_after", ""),
            weight_before=float(data.get("weight_before", 0.0)),
            weight_after=float(data.get("weight_after", 0.0)),
            contradiction_before=_contradiction(data.get("contradiction_before")),
            contradiction_after=_contradiction(data.get("contradiction_after")),
            authority_version=int(data.get("authority_version", 0)),
            reason=data.get("reason", ""),
            created_at=data.get("created_at"),
        )


def new_event_id(seed_id: str, sequence: int) -> str:
    """Deterministic event id from a seed id and a per-manager sequence number.

    Deterministic (no randomness, no wall-clock) so replay and golden-file tests
    are stable.
    """

    return f"gate::{seed_id}::{sequence:06d}"


def summarize_signals(signals: Sequence[ValidationSignal]) -> dict[str, Any]:
    """Small helper for policy reasons and audit summaries."""

    return {
        "count": len(signals),
        "kinds": sorted({signal.kind.value for signal in signals}),
        "has_external_evidence": any(signal.is_external_evidence for signal in signals),
        "has_recurrence": any(
            signal.kind.value == "recurrence" for signal in signals
        ),
    }
