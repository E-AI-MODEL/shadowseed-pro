"""Named Gate policies.

A policy reads the typed signals offered for a seed plus a small snapshot of the
seed's current authority state and *proposes* a decision. Policies never mutate
anything; the Gate applies (or rejects) the proposal (ADR-001, "Typed signals
and policy profiles"; issue #10).

Amendment (accepted second opinion, §1/§7): the ADR listed five illustrative
profiles. This module ships the two whose semantics are concrete today —
``exploratory`` and ``evidence_backed`` — plus an explicit, named default. The
remaining profiles (``research``, ``creative``, ``high_impact``) are documented
as examples in ``EXAMPLE_POLICY_IDS`` and are intentionally not implemented
until their required signal combinations are justified. The default policy is
never implicit: :func:`default_policy` and :data:`DEFAULT_POLICY_ID` name it
explicitly and :func:`resolve_policy` raises on an unknown id.

Thresholds here are explicit, documented constructor arguments with provisional
defaults, not magic numbers scattered through the code.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, Sequence, runtime_checkable

from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal


class ProposedVerdict(str, Enum):
    """What a policy proposes the Gate should do."""

    PROMOTE_OR_VALIDATE = "promote_or_validate"
    BLOCK = "block"
    CONTRADICT = "contradict"
    RESOLVE_CONTRADICTION = "resolve_contradiction"
    NO_CHANGE = "no_change"


@dataclass(frozen=True)
class AuthoritySnapshot:
    """Read-only view of the authority state a policy is allowed to consider.

    Deliberately minimal: a policy sees enough to reason about the transition
    but cannot reach in and change anything.
    """

    weight: float = 0.0
    status: str = "NEW"
    has_blocking_contradiction: bool = False


@dataclass(frozen=True)
class GateDecisionProposal:
    """A policy's proposal. Advisory only; the Gate decides whether to apply it."""

    policy_id: str
    verdict: ProposedVerdict
    weight_delta: float = 0.0
    reason: str = ""
    satisfied: bool = False
    missing: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_id": self.policy_id,
            "verdict": self.verdict.value,
            "weight_delta": self.weight_delta,
            "reason": self.reason,
            "satisfied": self.satisfied,
            "missing": list(self.missing),
        }


@runtime_checkable
class GatePolicy(Protocol):
    """Interface every Gate policy implements."""

    policy_id: str

    def propose(
        self,
        signals: Sequence[ValidationSignal],
        authority: AuthoritySnapshot,
    ) -> GateDecisionProposal:
        ...


def _supporting(signals: Sequence[ValidationSignal]) -> list[ValidationSignal]:
    return [s for s in signals if s.direction == SignalDirection.SUPPORT]


def _has_open_contradiction(
    signals: Sequence[ValidationSignal],
    authority: AuthoritySnapshot,
) -> bool:
    """A contradiction is in force if the seed already carries a blocking one and
    no resolution signal is offered, or if a fresh contradiction signal arrives."""

    fresh_contradiction = any(
        s.kind == SignalKind.CONTRADICTION and s.direction == SignalDirection.OPPOSE
        for s in signals
    )
    resolution = any(s.kind == SignalKind.CONTRADICTION_RESOLUTION for s in signals)
    if fresh_contradiction:
        return True
    if authority.has_blocking_contradiction and not resolution:
        return True
    return False


@dataclass(frozen=True)
class ExploratoryPolicy:
    """Permissive policy: recurrence alone may promote, if uncontradicted.

    This is what keeps SSL exploratory. Strong recurrence (or any external
    support) with no unresolved contradiction proposes a positive authority
    change. Recurrence is used *as recurrence* — the proposal reason records
    that explicitly and never calls it external evidence.
    """

    policy_id: str = "exploratory"
    min_recurrence_strength: float = 0.0
    weight_increment: float = 0.2

    def propose(
        self,
        signals: Sequence[ValidationSignal],
        authority: AuthoritySnapshot,
    ) -> GateDecisionProposal:
        if any(s.kind == SignalKind.CONTRADICTION and s.direction == SignalDirection.OPPOSE for s in signals):
            return GateDecisionProposal(
                self.policy_id, ProposedVerdict.CONTRADICT,
                reason="contradiction signal present",
            )
        if _has_open_contradiction(signals, authority):
            return GateDecisionProposal(
                self.policy_id, ProposedVerdict.BLOCK,
                reason="unresolved blocking contradiction",
                missing=("contradiction_resolution",),
            )
        support = _supporting(signals)
        recurrence = [s for s in support if s.kind == SignalKind.RECURRENCE]
        strong_recurrence = [s for s in recurrence if s.strength >= self.min_recurrence_strength]
        if strong_recurrence or any(s.is_external_evidence for s in support):
            basis = "recurrence" if strong_recurrence else "external_support"
            return GateDecisionProposal(
                self.policy_id, ProposedVerdict.PROMOTE_OR_VALIDATE,
                weight_delta=self.weight_increment,
                reason=f"exploratory support via {basis}",
                satisfied=True,
            )
        return GateDecisionProposal(
            self.policy_id, ProposedVerdict.BLOCK,
            reason="no qualifying support signal",
            missing=("recurrence_or_external_support",),
        )


@dataclass(frozen=True)
class EvidenceBackedPolicy:
    """Strict policy: requires verified external evidence; recurrence is not enough.

    A verified external-evidence signal (SSOT, human feedback, or retrieval,
    with ``verified=True``) and no unresolved contradiction proposes a positive
    change. Recurrence may accompany the evidence but can never satisfy the
    requirement on its own — the guarantee that recurrence is not double-counted
    as external evidence.
    """

    policy_id: str = "evidence_backed"
    weight_increment: float = 0.2

    def propose(
        self,
        signals: Sequence[ValidationSignal],
        authority: AuthoritySnapshot,
    ) -> GateDecisionProposal:
        if any(s.kind == SignalKind.CONTRADICTION and s.direction == SignalDirection.OPPOSE for s in signals):
            return GateDecisionProposal(
                self.policy_id, ProposedVerdict.CONTRADICT,
                reason="contradiction signal present",
            )
        if _has_open_contradiction(signals, authority):
            return GateDecisionProposal(
                self.policy_id, ProposedVerdict.BLOCK,
                reason="unresolved blocking contradiction",
                missing=("contradiction_resolution",),
            )
        support = _supporting(signals)
        verified_external = [
            s for s in support if s.is_external_evidence and s.verified
        ]
        if verified_external:
            return GateDecisionProposal(
                self.policy_id, ProposedVerdict.PROMOTE_OR_VALIDATE,
                weight_delta=self.weight_increment,
                reason="verified external evidence present",
                satisfied=True,
            )
        return GateDecisionProposal(
            self.policy_id, ProposedVerdict.BLOCK,
            reason="no verified external evidence",
            missing=("verified_external_evidence",),
        )


#: The default policy id. Never implicit: callers that do not name a policy get
#: this one, and it is documented here and in the architecture docs.
DEFAULT_POLICY_ID = "exploratory"

#: Documented-but-unimplemented profiles from ADR-001. Naming them keeps the
#: examples discoverable while making it explicit that they are not yet real
#: policies. ``resolve_policy`` raises a clear error if one is requested.
EXAMPLE_POLICY_IDS: tuple[str, ...] = ("research", "creative", "high_impact")


_REGISTRY: dict[str, GatePolicy] = {
    ExploratoryPolicy().policy_id: ExploratoryPolicy(),
    EvidenceBackedPolicy().policy_id: EvidenceBackedPolicy(),
}


def default_policy() -> GatePolicy:
    """Return the explicit default policy instance."""

    return _REGISTRY[DEFAULT_POLICY_ID]


def resolve_policy(policy_id: str | None) -> GatePolicy:
    """Resolve a policy by id.

    ``None`` resolves to the explicit default. An id listed in
    ``EXAMPLE_POLICY_IDS`` raises a distinct, actionable error so a caller does
    not silently fall back to a different policy. Any other unknown id also
    raises.
    """

    if policy_id is None:
        return default_policy()
    if policy_id in _REGISTRY:
        return _REGISTRY[policy_id]
    if policy_id in EXAMPLE_POLICY_IDS:
        raise ValueError(
            f"Gate policy '{policy_id}' is a documented example profile that is "
            "not implemented yet. Use 'exploratory' or 'evidence_backed', or "
            "register a concrete policy."
        )
    raise ValueError(
        f"Unknown Gate policy '{policy_id}'. "
        f"Known policies: {sorted(_REGISTRY)}."
    )


def available_policy_ids() -> list[str]:
    """Ids of the concrete, registered policies."""

    return sorted(_REGISTRY)
