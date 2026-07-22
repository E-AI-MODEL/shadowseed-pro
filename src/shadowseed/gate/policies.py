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
    """Interface implemented by every concrete Gate policy."""

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
    has_resolution = any(
        signal.kind is SignalKind.CONTRADICTION_RESOLUTION
        for signal in signals
    )
    if authority.has_blocking_contradiction and not has_resolution:
        return GateDecisionProposal(
            policy_id,
            ProposedVerdict.BLOCK,
            reason="unresolved blocking contradiction",
            missing=("contradiction_resolution",),
        )
    return None


@dataclass(frozen=True)
class ExploratoryPolicy:
    """Permissive policy: recurrence may raise authority."""

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
        external = any(signal.is_external_evidence for signal in support)
        if recurrent or external:
            basis = "recurrence" if recurrent else "external_support"
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
    """Compatibility policy requiring recurrence and verified evidence.

    It preserves the former boolean Gate behavior while using the same typed
    signal engine as every current policy.
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
        recurrent = any(signal.kind is SignalKind.RECURRENCE for signal in support)
        verified_external = any(
            signal.is_external_evidence and signal.verified for signal in support
        )
        if recurrent and verified_external:
            return GateDecisionProposal(
                self.policy_id,
                ProposedVerdict.PROMOTE_OR_VALIDATE,
                weight_delta=self.weight_increment,
                reason="legacy compatibility requirements satisfied",
                satisfied=True,
            )

        missing: list[str] = []
        if not recurrent:
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
