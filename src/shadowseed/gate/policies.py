"""Named Gate policies.

A policy reads the typed signals offered for a seed plus a small snapshot of the
seed's current authority state and *proposes* a decision. Policies never mutate
anything; the Gate applies (or rejects) the proposal (ADR-001, "Typed signals
and policy profiles"; issue #10).

The module ships the concrete exploratory and evidence-backed policies plus a
legacy compatibility policy. The compatibility policy preserves the former
boolean Gate requirement of recurrence plus verified external evidence while
routing the decision through the same signal-native Gate as every other policy.

The remaining profiles (``research``, ``creative``, ``high_impact``) are
documented examples and are intentionally not implemented until their required
signal combinations are justified. The default policy is never implicit:
:func:`default_policy` and :data:`DEFAULT_POLICY_ID` name it explicitly and
:func:`resolve_policy` raises on an unknown id.
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
    """Read-only view of the authority state a policy may consider."""

    weight: float = 0.0
    status: str = "NEW"
    has_blocking_contradiction: bool = False


@dataclass(frozen=True)
class GateDecisionProposal:
    """A policy proposal. Advisory only; the Gate applies the transition."""

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
    return [signal for signal in signals if signal.direction == SignalDirection.SUPPORT]


def _has_fresh_contradiction(signals: Sequence[ValidationSignal]) -> bool:
    return any(
        signal.kind == SignalKind.CONTRADICTION
        and signal.direction == SignalDirection.OPPOSE
        for signal in signals
    )


def _has_open_contradiction(
    signals: Sequence[ValidationSignal],
    authority: AuthoritySnapshot,
) -> bool:
    """Return whether a blocking contradiction remains in force."""

    if _has_fresh_contradiction(signals):
        return True
    resolution = any(
        signal.kind == SignalKind.CONTRADICTION_RESOLUTION for signal in signals
    )
    return authority.has_blocking_contradiction and not resolution


def _contradiction_proposal(
    policy_id: str,
    signals: Sequence[ValidationSignal],
    authority: AuthoritySnapshot,
) -> GateDecisionProposal | None:
    if _has_fresh_contradiction(signals):
        return GateDecisionProposal(
            policy_id,
            ProposedVerdict.CONTRADICT,
            reason="contradiction signal present",
        )
    if _has_open_contradiction(signals, authority):
        return GateDecisionProposal(
            policy_id,
            ProposedVerdict.BLOCK,
            reason="unresolved blocking contradiction",
            missing=("contradiction_resolution",),
        )
    return None


@dataclass(frozen=True)
class ExploratoryPolicy:
    """Permissive policy: recurrence may promote if uncontradicted."""

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
        recurrence = [
            signal for signal in support if signal.kind == SignalKind.RECURRENCE
        ]
        strong_recurrence = [
            signal
            for signal in recurrence
            if signal.strength >= self.min_recurrence_strength
        ]
        if strong_recurrence or any(signal.is_external_evidence for signal in support):
            basis = "recurrence" if strong_recurrence else "external_support"
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
            reason="no qualifying support signal",
            missing=("recurrence_or_external_support",),
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

        verified_external = [
            signal
            for signal in _supporting(signals)
            if signal.is_external_evidence and signal.verified
        ]
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
    """Compatibility policy requiring recurrence and verified evidence.

    This policy captures the former boolean Gate semantics without maintaining a
    separate decision engine. It is selected by the compatibility adapter when a
    caller uses ``run_validation_gate`` without naming another policy.
    """

    policy_id: str = "legacy_evidence_required"
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
        recurrence = any(
            signal.kind == SignalKind.RECURRENCE for signal in support
        )
        verified_external = any(
            signal.is_external_evidence and signal.verified for signal in support
        )
        if recurrence and verified_external:
            return GateDecisionProposal(
                self.policy_id,
                ProposedVerdict.PROMOTE_OR_VALIDATE,
                weight_delta=self.weight_increment,
                reason="legacy compatibility requirements satisfied",
                satisfied=True,
            )

        missing: list[str] = []
        if not recurrence:
            missing.append("recurrence")
        if not verified_external:
            missing.append("verified_external_evidence")
        return GateDecisionProposal(
            self.policy_id,
            ProposedVerdict.BLOCK,
            reason="legacy compatibility requirements not satisfied",
            missing=tuple(missing),
        )


DEFAULT_POLICY_ID = "exploratory"
EXAMPLE_POLICY_IDS: tuple[str, ...] = ("research", "creative", "high_impact")

_REGISTRY: dict[str, GatePolicy] = {
    ExploratoryPolicy().policy_id: ExploratoryPolicy(),
    EvidenceBackedPolicy().policy_id: EvidenceBackedPolicy(),
    LegacyEvidenceRequiredPolicy().policy_id: LegacyEvidenceRequiredPolicy(),
}


def default_policy() -> GatePolicy:
    """Return the explicit default policy instance."""

    return _REGISTRY[DEFAULT_POLICY_ID]


def resolve_policy(policy_id: str | None) -> GatePolicy:
    """Resolve a concrete policy or fail clearly for examples and unknown ids."""

    if policy_id is None:
        return default_policy()
    if policy_id in _REGISTRY:
        return _REGISTRY[policy_id]
    if policy_id in EXAMPLE_POLICY_IDS:
        raise ValueError(
            f"Gate policy '{policy_id}' is a documented example profile that is "
            "not implemented yet. Use a registered policy or add concrete semantics."
        )
    raise ValueError(
        f"Unknown Gate policy '{policy_id}'. Known policies: {sorted(_REGISTRY)}."
    )


def available_policy_ids() -> list[str]:
    """Return ids of the concrete registered policies."""

    return sorted(_REGISTRY)
