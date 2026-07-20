"""Contradiction records and their lifecycle (issue #13).

The legacy model was a single monotonic scalar (``contradiction_score``) that
only ever increased and a point-of-use guard that blocked any seed with a
positive score. In practice that made every contradiction a silent, permanent
influence ban — the over-restrictive failure mode the second opinion flagged.

This module replaces that with explicit, auditable records. Blocking state is
*derived* from unresolved records; the scalar is kept for backward compatibility
and migration. Recovery is possible but never silent: it requires a recorded
resolution basis, a Gate decision, and revalidation under the active policy
before authority can be restored (ADR-001, "Contradictions").
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ContradictionStatus(str, Enum):
    """Lifecycle states of a contradiction record."""

    OPEN = "open"
    RESOLVED = "resolved"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"


#: Only OPEN records block influence. Resolved/superseded/withdrawn records are
#: retained for audit but no longer block.
BLOCKING_STATUSES: frozenset[ContradictionStatus] = frozenset({ContradictionStatus.OPEN})


@dataclass
class ContradictionRecord:
    """One recorded contradiction against a seed.

    Mutable only through the lifecycle transitions on this class, which stamp
    the resolution metadata. The manager owns creation and resolution.
    """

    contradiction_id: str
    seed_id: str
    reason: str = ""
    source_ref: str | None = None
    strength: float = 1.0
    # Named lifecycle_state (not `status`) so the domain is explicit: this is the
    # contradiction record's own lifecycle, never a seed's authority `status`.
    # The static authority-mutation guard relies on that separation.
    lifecycle_state: ContradictionStatus = ContradictionStatus.OPEN
    created_at: str | None = None
    resolved_at: str | None = None
    resolution_basis: str | None = None

    def __post_init__(self) -> None:
        self.lifecycle_state = ContradictionStatus(self.lifecycle_state)
        strength = float(self.strength)
        if not 0.0 <= strength <= 1.0:
            raise ValueError(
                f"ContradictionRecord.strength must be in [0.0, 1.0], got {strength!r}"
            )
        self.strength = strength

    @property
    def is_blocking(self) -> bool:
        return self.lifecycle_state in BLOCKING_STATUSES

    def resolve(
        self,
        basis: str,
        *,
        superseded: bool = False,
        withdrawn: bool = False,
        resolved_at: str | None = None,
    ) -> None:
        """Move an open record to a terminal state with a recorded basis.

        ``basis`` is mandatory and must be non-empty: a contradiction is never
        cleared silently. ``superseded`` and ``withdrawn`` select the terminal
        state; the default is ``resolved``.
        """

        if self.lifecycle_state is not ContradictionStatus.OPEN:
            raise ValueError(
                f"contradiction {self.contradiction_id} is not open "
                f"(lifecycle_state={self.lifecycle_state.value})"
            )
        if not basis or not basis.strip():
            raise ValueError("contradiction resolution requires a non-empty basis")
        if superseded and withdrawn:
            raise ValueError("a contradiction cannot be both superseded and withdrawn")
        if superseded:
            self.lifecycle_state = ContradictionStatus.SUPERSEDED
        elif withdrawn:
            self.lifecycle_state = ContradictionStatus.WITHDRAWN
        else:
            self.lifecycle_state = ContradictionStatus.RESOLVED
        self.resolution_basis = basis
        self.resolved_at = resolved_at

    def to_dict(self) -> dict[str, Any]:
        # The serialized key stays "status" for backward compatibility, even
        # though the in-memory attribute is lifecycle_state.
        return {
            "contradiction_id": self.contradiction_id,
            "seed_id": self.seed_id,
            "reason": self.reason,
            "source_ref": self.source_ref,
            "strength": self.strength,
            "status": self.lifecycle_state.value,
            "created_at": self.created_at,
            "resolved_at": self.resolved_at,
            "resolution_basis": self.resolution_basis,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ContradictionRecord":
        return cls(
            contradiction_id=data["contradiction_id"],
            seed_id=data["seed_id"],
            reason=data.get("reason", ""),
            source_ref=data.get("source_ref"),
            strength=float(data.get("strength", 1.0)),
            lifecycle_state=ContradictionStatus(
                data.get("status", ContradictionStatus.OPEN.value)
            ),
            created_at=data.get("created_at"),
            resolved_at=data.get("resolved_at"),
            resolution_basis=data.get("resolution_basis"),
        )
