"""Named Validation Gate policies.

Policies inspect typed signals and propose authority changes. They never mutate
seed state; the Gate applies every transition and records the resulting event.
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
    """Read-only authority state available to a policy."""

    weight: float = 0.0
    status: str = "NEW"
    has_blocking_contradiction: bool = False
    # Accumulated seed facts a policy may reason about. They carry no thresholds
    # of their own: a policy owns its thresholds and applies them to these facts,
    # so the policy stays the single place where a verdict is decided.
    evidence_count: int = 0
    occurrence_count: int = 0
    trace: float = 0.0


@dataclass(frozen=True)
class GateDecisionProposal:
    """A policy proposal. The Gate remains the only transition writer."""

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
    """Interface implemented by every concrete Gate policy.

    A policy receives both inputs and may weigh either or both:

    - ``signals`` — the typed observations offered in *this* call;
    - ``authority`` — the seed's accumulated authority facts (weight, status,
      blocking contradiction, evidence count, occurrence count, trace).

    Policies legitimately differ in which of the two they read.
    ``exploratory`` and ``evidence_backed`` decide from the offered signals,
    while ``legacy_evidence_required`` reproduces historical thresholds and
    therefore decides from the accumulated facts. Both are valid: every policy
    gets the same two arguments, and none of them mutates anything — the Gate
    applies the proposal.
    """

    policy_id: str

    def propose(
        self,
        signals: Sequence[ValidationSignal],
        authority: AuthoritySnapshot,
    ) -> GateDecisionProposal:
        ...


def _supporting(signals: Sequence[ValidationSignal]) -> list[ValidationSignal]:
    return [signal for signal in signals if signal.direction is SignalDirection.SUPPORT]


def _fresh_contradiction(signals: Sequence[ValidationSignal]) -> bool:
    return any(
        signal.kind is SignalKind.CONTRADICTION
        and signal.direction is SignalDirection.OPPOSE
        for signal in signals
    )


def _contradiction_proposal(
    policy_id: str,
    signals: Sequence[ValidationSignal],
    authority: AuthoritySnapshot,
) -> GateDecisionProposal | None:
    if _fresh_contradiction(signals):
        return GateDecisionProposal(
            policy_id,
            ProposedVerdict.CONTRADICT,
            reason="contradiction signal present",
        )
    # A blocking contradiction is lifted only by the authority snapshot, never
    # by a signal offered in this call. Resolution is a separate, deliberate
    # action (``SSLManager.resolve_contradiction``) that requires a recorded
    # basis, closes the records, and produces its own Gate event; once it has
    # run, ``has_blocking_contradiction`` is already False here. Accepting a
    # bare CONTRADICTION_RESOLUTION signal instead would let a caller restore
    # weight while the records are still open.
    if authority.has_blocking_contradiction:
        return GateDecisionProposal(
            policy_id,
            ProposedVerdict.BLOCK,
            reason="unresolved blocking contradiction",
            missing=("contradiction_resolution",),
        )
    return None


@dataclass(frozen=True)
class ExploratoryPolicy:
    """Permissive policy: recurrence may raise authority.

    External support remains visible to the Gate but qualifies only when it is
    explicitly verified. This keeps recurrence exploratory without treating an
    unverified retrieval, SSOT proposal, or feedback signal as evidence.
    """

    policy_id: str = "exploratory"
    min_recurrence_strength: float = 0.0
    weight_increment: float = 0.2

    def propose(
        self,
        signals: Sequence[ValidationSignal],
        authority: AuthoritySnapshot,
    ) -> GateDecisionProposal:
        contradiction = _contradiction_proposal(self.policy_id, signals, authority)
        if contradiction is not None:
            return contradiction

        support = _supporting(signals)
        recurrent = any(
            signal.kind is SignalKind.RECURRENCE
            and signal.strength >= self.min_recurrence_strength
            for signal in support
        )
        verified_external = any(
            signal.is_external_evidence and signal.verified for signal in support
        )
        if recurrent or verified_external:
            basis = "recurrence" if recurrent else "verified_external_support"
            return GateDecisionProposal(
                self.policy_id,
                ProposedVerdict.PROMOTE_OR_VALIDATE,
                weight_delta=self.weight_increment,
                reason=f"exploratory support via {basis}",
                satisfied=True,
            )
        return GateDecisionProposal(
            self.policy_id,
            ProposedVerdict.BLOCK,
            reason="no qualifying recurrence or verified external support",
            missing=("recurrence_or_verified_external_support",),
        )


@dataclass(frozen=True)
class EvidenceBackedPolicy:
    """Strict policy: verified external evidence is required."""

    policy_id: str = "evidence_backed"
    weight_increment: float = 0.2

    def propose(
        self,
        signals: Sequence[ValidationSignal],
        authority: AuthoritySnapshot,
    ) -> GateDecisionProposal:
        contradiction = _contradiction_proposal(self.policy_id, signals, authority)
        if contradiction is not None:
            return contradiction

        verified_external = any(
            signal.is_external_evidence and signal.verified
            for signal in _supporting(signals)
        )
        if verified_external:
            return GateDecisionProposal(
                self.policy_id,
                ProposedVerdict.PROMOTE_OR_VALIDATE,
                weight_delta=self.weight_increment,
                reason="verified external evidence present",
                satisfied=True,
            )
        return GateDecisionProposal(
            self.policy_id,
            ProposedVerdict.BLOCK,
            reason="no verified external evidence",
            missing=("verified_external_evidence",),
        )


@dataclass(frozen=True)
class LegacyEvidenceRequiredPolicy:
    """Compatibility policy reproducing the historical boolean Gate thresholds.

    This is the *only* implementation of the legacy semantics: internal
    recognition (recurrence above the occurrence threshold with live trace) plus
    accumulated verified evidence, with no unresolved contradiction. The
    compatibility adapter resolves this policy and asks it for the proposal, so
    an event attributed to ``legacy_evidence_required`` really was decided here.

    The thresholds are fields rather than constants because they are
    manager-configurable; the adapter rebuilds this policy from the manager's
    config for each call via :func:`dataclasses.replace`, which keeps the class
    (and therefore the decision logic) the single source.
    """

    policy_id: str = "legacy_evidence_required"
    weight_increment: float = 0.2
    min_occurrences: int = 3
    min_trace: float = 0.5
    min_evidence: int = 2

    def internal_recognition(self, authority: AuthoritySnapshot) -> bool:
        """Historical 'internal recognition' rule: enough recurrence, still alive."""

        return (
            authority.occurrence_count >= self.min_occurrences
            and authority.trace > self.min_trace
        )

    def evidence_satisfied(self, authority: AuthoritySnapshot) -> bool:
        """Historical accumulated-evidence rule (verified evidence only)."""

        return authority.evidence_count >= self.min_evidence

    def propose(
        self,
        signals: Sequence[ValidationSignal],
        authority: AuthoritySnapshot,
    ) -> GateDecisionProposal:
        contradiction = _contradiction_proposal(self.policy_id, signals, authority)
        if contradiction is not None:
            return contradiction

        recognized = self.internal_recognition(authority)
        evidenced = self.evidence_satisfied(authority)
        if recognized and evidenced:
            return GateDecisionProposal(
                self.policy_id,
                ProposedVerdict.PROMOTE_OR_VALIDATE,
                weight_delta=self.weight_increment,
                reason="legacy compatibility requirements satisfied",
                satisfied=True,
            )

        missing: list[str] = []
        if not recognized:
            missing.append("internal_recognition")
        if not evidenced:
            missing.append("accumulated_verified_evidence")
        return GateDecisionProposal(
            self.policy_id,
            ProposedVerdict.BLOCK,
            reason="legacy compatibility requirements not satisfied",
            missing=tuple(missing),
        )


DEFAULT_POLICY_ID = "exploratory"
EXAMPLE_POLICY_IDS: tuple[str, ...] = ("research", "creative", "high_impact")

_PUBLIC_REGISTRY: dict[str, GatePolicy] = {
    ExploratoryPolicy().policy_id: ExploratoryPolicy(),
    EvidenceBackedPolicy().policy_id: EvidenceBackedPolicy(),
}
_COMPATIBILITY_REGISTRY: dict[str, GatePolicy] = {
    LegacyEvidenceRequiredPolicy().policy_id: LegacyEvidenceRequiredPolicy(),
}


def default_policy() -> GatePolicy:
    """Return the explicit default policy."""

    return _PUBLIC_REGISTRY[DEFAULT_POLICY_ID]


def resolve_policy(policy_id: str | None) -> GatePolicy:
    """Resolve public and compatibility policies with explicit failures."""

    if policy_id is None:
        return default_policy()
    if policy_id in _PUBLIC_REGISTRY:
        return _PUBLIC_REGISTRY[policy_id]
    if policy_id in _COMPATIBILITY_REGISTRY:
        return _COMPATIBILITY_REGISTRY[policy_id]
    if policy_id in EXAMPLE_POLICY_IDS:
        raise ValueError(
            f"Gate policy '{policy_id}' is a documented example profile that is "
            "not implemented yet. Use 'exploratory' or 'evidence_backed', or "
            "register a concrete policy."
        )
    known = sorted({*_PUBLIC_REGISTRY, *_COMPATIBILITY_REGISTRY})
    raise ValueError(f"Unknown Gate policy '{policy_id}'. Known policies: {known}.")


def available_policy_ids() -> list[str]:
    """Return user-selectable policy ids, excluding compatibility adapters."""

    return sorted(_PUBLIC_REGISTRY)
