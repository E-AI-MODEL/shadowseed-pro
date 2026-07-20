"""Typed validation signals fed to the Validation Gate.

A ``ValidationSignal`` is an *observation offered to the Gate*, not an authority
change. The Gate (through a policy) decides whether a combination of signals may
change a seed's authority. Collecting or recording a signal never grants
influence on its own (ADR-001, invariants 1 and 2).

Design notes:

- ``kind`` names the support channel. Recurrence is its own kind and is never
  relabeled as external evidence (ADR-001, "Recurrence").
- ``direction`` says whether the signal argues *for* or *against* authority.
- ``strength`` is a bounded, dimensionless magnitude in ``[0.0, 1.0]``. It is a
  relative weight the policy may use; it is deliberately not tied to any
  specific threshold here (issue #10: "avoid embedding arbitrary thresholds
  before their semantics are justified").
- ``verified`` and ``independent`` carry provenance/trust the policy may
  require. Generated model output must not be marked ``verified``; that trust
  boundary is enforced where signals are constructed, mirroring
  ``shadowseed_agent.agent_contract.evidence_can_support_gate``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SignalKind(str, Enum):
    """Which support channel produced an observation.

    Closed vocabulary so audit logs stay legible and so recurrence can never be
    silently reclassified as external evidence.
    """

    RECURRENCE = "recurrence"
    SSOT = "ssot"
    HUMAN_FEEDBACK = "human_feedback"
    RETRIEVAL = "retrieval"
    DIALECTIC = "dialectic"
    PROBE = "probe"
    TASK_OUTCOME = "task_outcome"
    CONTRADICTION = "contradiction"
    CONTRADICTION_RESOLUTION = "contradiction_resolution"


#: Signal kinds that represent externally sourced evidence (as opposed to
#: internally observed recurrence or probe/dialectic outcomes). A policy that
#: requires "external evidence" must look for these kinds; recurrence is
#: deliberately excluded so it can never satisfy an external-evidence
#: requirement by relabeling.
EXTERNAL_EVIDENCE_KINDS: frozenset[SignalKind] = frozenset(
    {SignalKind.SSOT, SignalKind.HUMAN_FEEDBACK, SignalKind.RETRIEVAL}
)


class SignalDirection(str, Enum):
    """Whether a signal supports, opposes, or is neutral toward authority."""

    SUPPORT = "support"
    OPPOSE = "oppose"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class ValidationSignal:
    """One typed observation offered to the Gate.

    Immutable so a recorded signal cannot be edited after the fact. Equality and
    hashing are structural, which makes signals convenient to deduplicate and to
    compare in replay tests.
    """

    kind: SignalKind
    direction: SignalDirection = SignalDirection.SUPPORT
    strength: float = 1.0
    source_ref: str | None = None
    verified: bool = False
    independent: bool = False
    reason: str | None = None

    def __post_init__(self) -> None:
        # Coerce string inputs so callers may pass raw enum values.
        object.__setattr__(self, "kind", SignalKind(self.kind))
        object.__setattr__(self, "direction", SignalDirection(self.direction))
        strength = float(self.strength)
        if not 0.0 <= strength <= 1.0:
            raise ValueError(
                f"ValidationSignal.strength must be in [0.0, 1.0], got {strength!r}"
            )
        object.__setattr__(self, "strength", strength)

    @property
    def is_external_evidence(self) -> bool:
        """Whether this signal counts as external evidence.

        Recurrence, probe, dialectic, and task-outcome signals return ``False``
        even when they support promotion. This is the code-level guarantee that
        recurrence is not external evidence.
        """

        return self.kind in EXTERNAL_EVIDENCE_KINDS

    def to_dict(self) -> dict[str, Any]:
        """Deterministic, ordered serialization for audit and replay."""

        return {
            "kind": self.kind.value,
            "direction": self.direction.value,
            "strength": self.strength,
            "source_ref": self.source_ref,
            "verified": self.verified,
            "independent": self.independent,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ValidationSignal":
        return cls(
            kind=SignalKind(data["kind"]),
            direction=SignalDirection(data.get("direction", SignalDirection.SUPPORT.value)),
            strength=float(data.get("strength", 1.0)),
            source_ref=data.get("source_ref"),
            verified=bool(data.get("verified", False)),
            independent=bool(data.get("independent", False)),
            reason=data.get("reason"),
        )


def recurrence_signal(
    count: int,
    *,
    threshold: int = 2,
    source_ref: str | None = None,
) -> ValidationSignal:
    """Build a recurrence support signal from an occurrence count.

    Strength scales from 0 at ``threshold`` occurrences toward 1 as the count
    grows, saturating at ``threshold * 3``. The signal's kind is always
    ``RECURRENCE`` so it can never be mistaken for external evidence, directly
    replacing the ``external_evidence = occurrence_count >= 2`` relabeling that
    previously lived in the chat runtime.
    """

    if threshold < 1:
        raise ValueError("recurrence threshold must be >= 1")
    span = max(1, threshold * 3 - threshold)
    strength = max(0.0, min(1.0, (count - threshold) / span)) if count >= threshold else 0.0
    return ValidationSignal(
        kind=SignalKind.RECURRENCE,
        direction=SignalDirection.SUPPORT if count >= threshold else SignalDirection.NEUTRAL,
        strength=strength,
        source_ref=source_ref,
        verified=False,
        independent=False,
        reason=f"occurrence_count={count} (threshold={threshold})",
    )
