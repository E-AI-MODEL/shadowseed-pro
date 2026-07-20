"""
Shadow Seed Learning 4.6 core manager.

This manager is the canonical Niveau-1 core for SSL. The mechanical kernel is
unchanged across 4.5 and 4.6 — see `docs/00_shadow_seed_learning_4_6.md` for
the current canonical source. It keeps four ideas explicit:

- a seed is atomic;
- trace measures presence;
- weight measures influence;
- promotion requires the Validation Gate.

The manager now also keeps explicit configuration, normalization results and
validation-event logs so benchmark runs can be reconstructed more honestly.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from enum import Enum
import math
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Iterable, Literal, Mapping

import numpy as np

from shadowseed.core_config import SSLCoreConfig
from shadowseed.gate.contradictions import ContradictionRecord, ContradictionStatus
from shadowseed.gate.events import (
    ContradictionState,
    GateDecision,
    GateEvent,
    new_event_id,
)
from shadowseed.gate.policies import AuthoritySnapshot, ProposedVerdict, resolve_policy
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)
from shadowseed.seed_normalization import normalize_detection_candidates

if TYPE_CHECKING:
    from shadowseed.vector_constellation import VectorConstellation


DEFAULT_CONFIG = SSLCoreConfig()


class SeedStatus(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    DECAYING = "DECAYING"
    DORMANT = "DORMANT"
    PROMOTED = "PROMOTED"
    EXPIRED = "EXPIRED"


class CandidateType(str, Enum):
    """Why a candidate absence was proposed.

    This is observability metadata only. It records what kind of gap the
    detector believed it found; it never affects trace, weight, evidence, or
    the Validation Gate. Closed vocabulary so audit logs stay legible.
    """

    MISSING_RELATION = "missing_relation"
    MISSING_BOUNDARY = "missing_boundary"
    UNSTATED_ASSUMPTION = "unstated_assumption"
    CONTRADICTION = "contradiction"
    ALTERNATIVE_HYPOTHESIS = "alternative_hypothesis"
    MISSING_DEPENDENCY = "missing_dependency"
    POSSIBLE_COMPLETION = "possible_completion"
    UNSPECIFIED = "unspecified"


@dataclass
class SeedOrigin:
    """Optional, audit-only record of *why* a seed was generated.

    Purely descriptive provenance. It makes the conceptual origin of a seed
    visible in the created-event and export, but carries no epistemic force:
    a convincing rationale here must still leave ``weight`` at ``0.0``. Weight
    can rise only through the Validation Gate, never from this metadata.
    """

    candidate_type: CandidateType = CandidateType.UNSPECIFIED
    detection_basis: str = ""
    context_ref: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_type": self.candidate_type.value,
            "detection_basis": self.detection_basis,
            "context_ref": self.context_ref,
        }


# Authority fields: only the Validation Gate transition path (SSLManager) may
# change these. They determine whether a seed can eventually influence behavior.
# trace, occurrence_count, and turns_dormant are observation/lifecycle-support
# fields and stay freely writable. authority_version is included so it cannot be
# assigned externally; it is managed automatically by _write_authority.
AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {"weight", "status", "evidence_count", "contradiction_score", "authority_version"}
)

# The subset whose value actually changing marks an authority change (and bumps
# the version). Status is handled separately: only crossing the PROMOTED
# boundary counts, so ordinary lifecycle moves (ACTIVE/DORMANT/NEW) do not churn
# the authority version.
_VERSIONED_AUTHORITY_FIELDS: frozenset[str] = frozenset(
    {"weight", "contradiction_score", "evidence_count"}
)


@dataclass
class ShadowSeed:
    id: str
    text: str
    embedding: np.ndarray
    trigger_keywords: list[str] = field(default_factory=list)
    trace: float = 2.0
    occurrence_count: int = 1
    turns_dormant: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    origin: SeedOrigin | None = None
    # Authority fields are init=False: they cannot be set through the
    # constructor, closing the construction bypass. A seed is always born
    # weightless; authority is reached only through the Gate, and tests use
    # unsafe_set_authority(...).
    weight: float = field(default=0.0, init=False)
    evidence_count: int = field(default=0, init=False)
    contradiction_score: float = field(default=0.0, init=False)
    status: SeedStatus = field(default=SeedStatus.NEW, init=False)
    # Monotonic counter stamped whenever authority (weight, evidence,
    # contradiction, or promotion state) changes. A point-of-use decision
    # references it so a stale authorization can be detected on replay.
    authority_version: int = field(default=0, init=False)
    _authority_sealed: bool = field(default=False, repr=False, compare=False, init=False)

    def __post_init__(self) -> None:
        # Seal after construction so field defaults can be set during init, but
        # later direct assignments are guarded.
        object.__setattr__(self, "_authority_sealed", True)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in AUTHORITY_FIELDS and getattr(self, "_authority_sealed", False):
            raise AttributeError(
                f"'{name}' is authority state and cannot be assigned directly. "
                "Authority changes only through the SSLManager Validation Gate "
                "transition path. In tests or benchmarks, use "
                "ShadowSeed.unsafe_set_authority(...)."
            )
        object.__setattr__(self, name, value)

    def _write_authority(self, changes: dict[str, Any]) -> None:
        """Apply an authority change and bump the version when it matters.

        This is the single low-level writer. It bypasses the ``__setattr__``
        guard on purpose; callers are the manager's transition path and the
        explicit unsafe test hook. The version bumps only when an
        authority-determining value actually changes (weight, evidence, or
        contradiction score) or when the PROMOTED boundary is crossed — not on
        an unchanged rewrite, and not on a pure lifecycle status move.
        """

        promoted_before = self.status == SeedStatus.PROMOTED
        value_changed = False
        for name, value in changes.items():
            if name == "authority_version":
                raise KeyError("authority_version is managed automatically")
            if name not in AUTHORITY_FIELDS:
                raise KeyError(f"'{name}' is not an authority field")
            if name in _VERSIONED_AUTHORITY_FIELDS and value != getattr(self, name):
                value_changed = True
            object.__setattr__(self, name, value)
        promoted_after = self.status == SeedStatus.PROMOTED
        if value_changed or promoted_before != promoted_after:
            object.__setattr__(self, "authority_version", self.authority_version + 1)

    def unsafe_set_authority(
        self,
        *,
        weight: float | None = None,
        status: "SeedStatus | None" = None,
        evidence_count: int | None = None,
        contradiction_score: float | None = None,
    ) -> None:
        """Explicitly unsafe authority setter for tests and benchmark fixtures.

        Production code must never call this. It exists so tests can construct
        edge-case authority states without a full Gate run, while direct field
        assignment stays blocked.
        """

        changes: dict[str, Any] = {}
        if weight is not None:
            changes["weight"] = weight
        if status is not None:
            changes["status"] = status
        if evidence_count is not None:
            changes["evidence_count"] = evidence_count
        if contradiction_score is not None:
            changes["contradiction_score"] = contradiction_score
        self._write_authority(changes)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("_authority_sealed", None)
        data["embedding"] = self.embedding.tolist()
        data["status"] = self.status.value
        data["origin"] = self.origin.to_dict() if self.origin is not None else None
        return data


@dataclass
class Constellation:
    members: list[str]
    centroid: list[float]
    combined_weight: float
    id: str = ""
    label: str = ""
    probe_type: str = "socratic"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["member_ids"] = list(self.members)
        return data


@dataclass
class SeedEvent:
    event_type: str
    seed_id: str
    detail: dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationGateResult:
    seed_id: str
    status_before: str
    status_after: str
    weight_before: float
    weight_after: float
    occurrence_count: int
    evidence_count: int
    internal_recognition_passed: bool
    external_evidence_passed: bool
    contradiction_free: bool
    external_evidence_applied: bool
    contradiction_applied: bool
    promoted: bool
    verdict: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationGateFlags:
    internal_recognition_passed: bool
    external_evidence_passed: bool
    contradiction_free: bool


class ProbeType(str, Enum):
    """Which probe instrument produced the outcome."""

    FOLLOW_UP = "follow_up"
    RETRIEVAL = "retrieval"
    DIALECTIC = "dialectic"
    GENERAL = "general"


class ProbeOutcome(str, Enum):
    """Outcome of a probe evaluation.

    Probe feedback is deliberately weaker than the Validation Gate. A probe may
    nudge a seed's weight up or down, but it cannot promote a seed on its own.
    It can demote a promoted seed back to ACTIVE when repeated poor outcomes
    drive the weight back below the promotion threshold.
    """

    REWARD = "reward"
    PENALTY = "penalty"
    NEUTRAL = "neutral"


@dataclass
class ProbeFeedbackResult:
    """Structured record of a single probe-feedback event."""

    seed_id: str
    probe_type: str
    outcome: str
    weight_before: float
    weight_after: float
    delta_applied: float
    status_before: str
    status_after: str
    demoted: bool
    skipped: bool
    skip_reason: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SSLManager:
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        half_life_turns: float | None = None,
        dedup_threshold: float | None = None,
        promotion_threshold: float | None = None,
        dormant_threshold: float | None = None,
        validation_increment: float | None = None,
        contradiction_penalty: float | None = None,
        max_trace: float | None = None,
        reactivation_increment: float | None = None,
        embedding_fn: Callable[[str], np.ndarray] | None = None,
        vector_constellation: VectorConstellation | None = None,
        config: SSLCoreConfig | None = None,
    ):
        base_config = config or DEFAULT_CONFIG
        self._embedding_fn = embedding_fn
        self.model_name = model_name
        self._embedder = None
        self._seeds: dict[str, ShadowSeed] = {}
        self.config = replace(
            base_config,
            half_life_turns=base_config.half_life_turns if half_life_turns is None else half_life_turns,
            dedup_threshold=base_config.dedup_threshold if dedup_threshold is None else dedup_threshold,
            promotion_threshold=base_config.promotion_threshold
            if promotion_threshold is None
            else promotion_threshold,
            dormant_threshold=base_config.dormant_threshold if dormant_threshold is None else dormant_threshold,
            validation_increment=base_config.validation_increment
            if validation_increment is None
            else validation_increment,
            contradiction_penalty=base_config.contradiction_penalty
            if contradiction_penalty is None
            else contradiction_penalty,
            max_trace=base_config.max_trace if max_trace is None else max_trace,
            reactivation_increment=base_config.reactivation_increment
            if reactivation_increment is None
            else reactivation_increment,
        )
        self.half_life_turns = self.config.half_life_turns
        self.dedup_threshold = self.config.dedup_threshold
        self.promotion_threshold = self.config.promotion_threshold
        self.dormant_threshold = self.config.dormant_threshold
        self.validation_increment = self.config.validation_increment
        self.contradiction_penalty = self.config.contradiction_penalty
        self.max_trace = self.config.max_trace
        self.reactivation_increment = self.config.reactivation_increment
        self.reward_step = self.config.reward_step
        self.penalty_step = self.config.penalty_step
        self.dormant_ttl_turns = self.config.dormant_ttl_turns
        self.contradiction_trace_penalty = self.config.contradiction_trace_penalty
        self.vector_constellation = vector_constellation
        self.validation_log: list[ValidationGateResult] = []
        self.event_log: list[SeedEvent] = []
        self.feedback_log: list[ProbeFeedbackResult] = []
        # Immutable authority-decision ledger (#10/#12). Every Gate invocation
        # appends one GateEvent recording the typed signals, the policy, and the
        # before/after authority state.
        self.gate_events: list[GateEvent] = []
        self._gate_sequence = 0
        # Explicit contradiction records (#13). Blocking state is derived from
        # unresolved records; contradiction_score is kept for compatibility.
        self.contradiction_records: list[ContradictionRecord] = []
        self._contradiction_sequence = 0

    @property
    def seeds(self) -> "Mapping[str, ShadowSeed]":
        """Read-only view of the seed registry.

        The mapping itself cannot be replaced or have entries inserted/removed
        through this view — seed creation goes through ``add_or_update_seed`` and
        the Gate owns authority. Individual ``ShadowSeed`` objects are returned
        directly, so their non-authority observation fields remain writable while
        authority fields stay guarded.
        """

        return MappingProxyType(self._seeds)

    def unsafe_install_seed(self, seed: ShadowSeed) -> None:
        """Test/benchmark-only: insert a pre-built seed into the registry.

        Production code creates seeds through ``add_or_update_seed``. This hook
        exists so tests can install hand-constructed seeds (paired with
        ``ShadowSeed.unsafe_set_authority``) without a public mutable registry.
        """

        self._seeds[seed.id] = seed

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat()

    def _record_event(self, event_type: str, seed_id: str, **detail: Any) -> None:
        self.event_log.append(SeedEvent(event_type=event_type, seed_id=seed_id, detail=detail))

    def _touch_seed(self, seed: ShadowSeed) -> None:
        seed.updated_at = self._now_iso()

    def _set_authority(
        self,
        seed: ShadowSeed,
        *,
        weight: float | None = None,
        status: SeedStatus | None = None,
        evidence_count: int | None = None,
        contradiction_score: float | None = None,
    ) -> None:
        """The single production authority-transition path.

        Every runtime authority change (validation, contradiction, probe
        feedback, decay/expiry, lifecycle status moves) goes through here. #12
        migrates the callers to feed this from typed signals and a named policy;
        #11 establishes that no runtime code writes authority fields directly.
        """

        changes: dict[str, Any] = {}
        if weight is not None:
            changes["weight"] = weight
        if status is not None:
            changes["status"] = status
        if evidence_count is not None:
            changes["evidence_count"] = evidence_count
        if contradiction_score is not None:
            changes["contradiction_score"] = contradiction_score
        if changes:
            seed._write_authority(changes)

    def open_contradictions(self, seed_id: str) -> list[ContradictionRecord]:
        """Unresolved (blocking) contradiction records for a seed."""

        return [
            record
            for record in self.contradiction_records
            if record.seed_id == seed_id and record.is_blocking
        ]

    def contradictions_for(self, seed_id: str) -> list[ContradictionRecord]:
        """All contradiction records for a seed, in creation order."""

        return [r for r in self.contradiction_records if r.seed_id == seed_id]

    def is_blocking_contradiction(self, seed_id: str) -> bool:
        """Canonical blocking state for a seed (derived from records, with the
        legacy scalar as fallback). This is the value point-of-use decisions
        should consult rather than reading contradiction_score directly."""

        return self._contradiction_state(self._seeds[seed_id]).blocking

    def _contradiction_state(self, seed: ShadowSeed) -> ContradictionState:
        """Derive the blocking-contradiction snapshot.

        Blocking state comes from unresolved records. Seeds that predate the
        record model (a positive scalar but no records) are treated as carrying
        one legacy open contradiction, so migration is lossless.
        """

        records = self.contradictions_for(seed.id)
        if records:
            open_count = sum(1 for r in records if r.is_blocking)
            return ContradictionState(
                blocking=open_count > 0,
                open_count=open_count,
                score=seed.contradiction_score,
            )
        legacy_blocking = seed.contradiction_score > 0.0
        return ContradictionState(
            blocking=legacy_blocking,
            open_count=1 if legacy_blocking else 0,
            score=seed.contradiction_score,
        )

    def _open_contradiction_record(
        self,
        seed: ShadowSeed,
        *,
        reason: str,
        source_ref: str | None,
        strength: float,
    ) -> ContradictionRecord:
        self._contradiction_sequence += 1
        record = ContradictionRecord(
            contradiction_id=f"contra::{seed.id}::{self._contradiction_sequence:06d}",
            seed_id=seed.id,
            reason=reason,
            source_ref=source_ref,
            strength=max(0.0, min(1.0, strength)),
            lifecycle_state=ContradictionStatus.OPEN,
            created_at=self._now_iso(),
        )
        self.contradiction_records.append(record)
        return record

    def resolve_contradiction(
        self,
        seed_id: str,
        *,
        basis: str,
        contradiction_id: str | None = None,
        superseded: bool = False,
        withdrawn: bool = False,
        resolver: str = "human",
    ) -> GateEvent:
        """Gate-controlled contradiction recovery.

        Marks the seed's open contradiction record(s) as resolved (or superseded
        / withdrawn) with a recorded ``basis``, then — if no blocking record
        remains — clears the blocking scalar through the authority path. This
        only *unblocks* the seed; authority is not restored here. Recovery still
        requires revalidation (a subsequent signal submission) under the active
        policy, which is what actually raises weight again.

        Recurrence alone can never reach this method: resolution is an explicit,
        separately-recorded action with a mandatory basis.
        """

        seed = self._seeds[seed_id]
        if seed.status == SeedStatus.EXPIRED:
            raise ValueError("expired seeds cannot recover through contradiction resolution")
        open_records = self.open_contradictions(seed_id)
        if contradiction_id is not None:
            open_records = [r for r in open_records if r.contradiction_id == contradiction_id]
        if not open_records:
            raise ValueError(f"no open contradiction to resolve for seed '{seed_id}'")

        status_before = seed.status.value
        weight_before = seed.weight
        contradiction_before = self._contradiction_state(seed)
        for record in open_records:
            record.resolve(
                basis,
                superseded=superseded,
                withdrawn=withdrawn,
                resolved_at=self._now_iso(),
            )
        # If nothing blocking remains, clear the scalar so the point-of-use
        # contract and the policies stop treating the seed as contradicted.
        if not self.open_contradictions(seed_id):
            self._set_authority(seed, contradiction_score=0.0)
        self._touch_seed(seed)
        signal = ValidationSignal(
            kind=SignalKind.CONTRADICTION_RESOLUTION,
            direction=SignalDirection.SUPPORT,
            strength=1.0,
            source_ref=resolver,
            reason=basis,
        )
        return self._record_gate_event(
            seed,
            GateDecision.CONTRADICTION_RESOLVED,
            [signal],
            policy_id="contradiction_resolution",
            status_before=status_before,
            weight_before=weight_before,
            contradiction_before=contradiction_before,
            reason=f"resolved by {resolver}: {basis}",
        )

    def migrate_legacy_contradictions(self) -> list[ContradictionRecord]:
        """Create an open record for any seed with a legacy scalar but no records.

        Idempotent: seeds that already have records are left untouched. Returns
        the records created, for logging or tests.
        """

        created: list[ContradictionRecord] = []
        for seed in self._seeds.values():
            if seed.contradiction_score > 0.0 and not self.contradictions_for(seed.id):
                created.append(
                    self._open_contradiction_record(
                        seed,
                        reason="migrated from legacy contradiction_score",
                        source_ref="legacy_migration",
                        strength=min(1.0, seed.contradiction_score),
                    )
                )
        return created

    def _record_gate_event(
        self,
        seed: ShadowSeed,
        decision: GateDecision,
        signals: Iterable[ValidationSignal],
        *,
        policy_id: str,
        status_before: str,
        weight_before: float,
        contradiction_before: ContradictionState,
        reason: str,
    ) -> GateEvent:
        self._gate_sequence += 1
        event = GateEvent(
            event_id=new_event_id(seed.id, self._gate_sequence),
            seed_id=seed.id,
            policy_id=policy_id,
            decision=decision,
            signals=tuple(signals),
            status_before=status_before,
            status_after=seed.status.value,
            weight_before=weight_before,
            weight_after=seed.weight,
            contradiction_before=contradiction_before,
            contradiction_after=self._contradiction_state(seed),
            authority_version=seed.authority_version,
            reason=reason,
            created_at=self._now_iso(),
        )
        self.gate_events.append(event)
        return event

    def submit_signals(
        self,
        seed_id: str,
        signals: Iterable[ValidationSignal],
        policy_id: str | None = None,
    ) -> GateEvent:
        """Route typed signals through a named policy and apply the Gate decision.

        This is the signal-native Gate entry point. Helpers (recurrence, probes,
        feedback, SSOT, dialectic) build ``ValidationSignal`` objects and call
        here; only this method applies the resulting authority change, and only
        through ``_set_authority``. The policy proposes; the Gate applies.

        Recurrence signals contribute to promotion under the exploratory policy
        without ever incrementing ``evidence_count`` — external evidence and
        recurrence stay distinct.
        """

        seed = self._seeds[seed_id]
        policy = resolve_policy(policy_id)
        signal_list = list(signals)
        status_before = seed.status.value
        weight_before = seed.weight
        contradiction_before = self._contradiction_state(seed)

        if seed.status == SeedStatus.EXPIRED:
            # Terminal: an expired seed cannot regain authority.
            return self._record_gate_event(
                seed, GateDecision.EXPIRED, signal_list,
                policy_id=policy.policy_id, status_before=status_before,
                weight_before=weight_before, contradiction_before=contradiction_before,
                reason="expired seed is terminal",
            )

        snapshot = AuthoritySnapshot(
            weight=seed.weight,
            status=seed.status.value,
            has_blocking_contradiction=contradiction_before.blocking,
        )
        proposal = policy.propose(signal_list, snapshot)

        if proposal.verdict is ProposedVerdict.CONTRADICT:
            contradiction_signal = next(
                (s for s in signal_list if s.kind is SignalKind.CONTRADICTION), None
            )
            self._open_contradiction_record(
                seed,
                reason=(contradiction_signal.reason if contradiction_signal else "") or "contradiction signal",
                source_ref=contradiction_signal.source_ref if contradiction_signal else None,
                strength=contradiction_signal.strength if contradiction_signal else 1.0,
            )
            self._set_authority(
                seed,
                weight=max(0.0, seed.weight - self.contradiction_penalty),
                contradiction_score=min(1.0, seed.contradiction_score + 0.25),
                status=SeedStatus.NEW,
            )
            seed.occurrence_count = 1
            if self.contradiction_trace_penalty:
                seed.trace = max(0.0, seed.trace - self.contradiction_trace_penalty)
            seed.turns_dormant = 0
            self._touch_seed(seed)
            decision = GateDecision.CONTRADICTED
        elif proposal.verdict is ProposedVerdict.PROMOTE_OR_VALIDATE and proposal.satisfied:
            new_weight = min(1.0, seed.weight + proposal.weight_delta)
            new_status = (
                SeedStatus.PROMOTED
                if new_weight >= self.promotion_threshold
                else SeedStatus.ACTIVE
            )
            external_support = sum(
                1
                for s in signal_list
                if s.is_external_evidence and s.direction is SignalDirection.SUPPORT
            )
            self._set_authority(
                seed,
                weight=new_weight,
                status=new_status,
                evidence_count=(
                    seed.evidence_count + external_support if external_support else None
                ),
            )
            self._touch_seed(seed)
            decision = (
                GateDecision.PROMOTED
                if new_status is SeedStatus.PROMOTED
                else GateDecision.VALIDATED
            )
        else:
            decision = GateDecision.BLOCKED

        # Mirror the decision into validation_log so the existing point-of-use
        # contract (which inspects validation_log for a logged promotion) stays
        # consistent with the signal-native path. #14 links point-of-use
        # decisions to gate_events directly.
        self._log_validation_from_signals(
            seed, decision, signal_list,
            status_before=status_before, weight_before=weight_before,
        )
        event = self._record_gate_event(
            seed, decision, signal_list,
            policy_id=policy.policy_id, status_before=status_before,
            weight_before=weight_before, contradiction_before=contradiction_before,
            reason=proposal.reason,
        )
        self._sync_seed(seed_id)
        return event

    _DECISION_TO_VERDICT = {
        GateDecision.PROMOTED: "promoted",
        GateDecision.VALIDATED: "validated",
        GateDecision.BLOCKED: "blocked",
        GateDecision.CONTRADICTED: "contradicted",
        GateDecision.EXPIRED: "expired",
    }

    def _log_validation_from_signals(
        self,
        seed: ShadowSeed,
        decision: GateDecision,
        signals: list[ValidationSignal],
        *,
        status_before: str,
        weight_before: float,
    ) -> None:
        has_recurrence_support = any(
            s.kind is SignalKind.RECURRENCE and s.direction is SignalDirection.SUPPORT
            for s in signals
        )
        has_external_support = any(
            s.is_external_evidence and s.direction is SignalDirection.SUPPORT
            for s in signals
        )
        result = ValidationGateResult(
            seed_id=seed.id,
            status_before=status_before,
            status_after=seed.status.value,
            weight_before=weight_before,
            weight_after=seed.weight,
            occurrence_count=seed.occurrence_count,
            evidence_count=seed.evidence_count,
            internal_recognition_passed=has_recurrence_support,
            external_evidence_passed=has_external_support,
            contradiction_free=decision is not GateDecision.CONTRADICTED,
            external_evidence_applied=has_external_support,
            contradiction_applied=decision is GateDecision.CONTRADICTED,
            promoted=decision is GateDecision.PROMOTED,
            verdict=self._DECISION_TO_VERDICT.get(decision, "blocked"),
        )
        self.validation_log.append(result)

    def _sync_seed(self, seed_id: str) -> None:
        if self.vector_constellation is not None:
            self.vector_constellation.sync_seed(self._seeds[seed_id])

    def _record_and_sync(self, event_type: str, seed_id: str, **detail: Any) -> None:
        self._record_event(event_type, seed_id, **detail)
        self._sync_seed(seed_id)

    def _load_embedder(self):
        if self._embedder is not None:
            return self._embedder
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "Installeer sentence-transformers om SSLManager te gebruiken: "
                "pip install sentence-transformers"
            ) from exc
        self._embedder = SentenceTransformer(self.model_name)
        return self._embedder

    def get_embedding(self, text: str) -> np.ndarray:
        if self._embedding_fn is not None:
            return self._normalize_embedding(self._embedding_fn(text))
        embedder = self._load_embedder()
        return embedder.encode(text, normalize_embeddings=True)

    @staticmethod
    def _normalize_embedding(embedding: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm

    @staticmethod
    def is_atomic_seed(text: str, max_seed_words: int | None = None) -> bool:
        """Heuristic filter. Human review is still needed."""
        lowered = text.lower().strip()
        separators = [",", ";", " en ", " of ", "zoals", "bijvoorbeeld"]
        broad_terms = [
            "analysekader",
            "complete",
            "oorzaken",
            "gevolgen",
            "contexten",
            "perspectieven",
            "meerdere",
        ]
        generic_category_terms = {
            "security",
            "privacy",
            "schaalbaarheid",
            "kolonialisme",
            "context",
        }
        word_limit = DEFAULT_CONFIG.max_seed_words if max_seed_words is None else max_seed_words
        has_many_separators = sum(sep in lowered for sep in separators) >= 2
        has_broad_terms = any(term in lowered for term in broad_terms)
        word_count = len(re.findall(r"\w+", text))
        if word_count <= 3 and any(term in lowered for term in generic_category_terms) and (
            "ontbreekt" in lowered or "ontbreken" in lowered
        ):
            return False
        return not has_many_separators and not has_broad_terms and word_count <= word_limit

    def normalize_detection_candidates(
        self,
        candidates: Iterable[str],
        expand_short_fragments: bool = True,
        split_broad: bool = True,
    ) -> list[str]:
        return normalize_detection_candidates(
            list(candidates),
            expand_short_fragments=expand_short_fragments,
            split_broad=split_broad,
        )

    def ingest_detection_candidates(
        self,
        candidates: Iterable[str],
        trigger_keywords: Iterable[str] | None = None,
        expand_short_fragments: bool = True,
        split_broad: bool = True,
        deduplicate: bool = True,
        min_seed_words: int = 0,
        origin: SeedOrigin | None = None,
    ) -> dict[str, Any]:
        raw_candidates = list(candidates)
        normalized = self.normalize_detection_candidates(
            raw_candidates,
            expand_short_fragments=expand_short_fragments,
            split_broad=split_broad,
        )
        accepted: list[dict[str, str]] = []
        rejected: list[dict[str, str]] = []
        seen_texts: set[str] = set()
        accepted_ids: set[str] = set()
        for candidate in normalized:
            if min_seed_words and len(re.findall(r"\w+", candidate)) < min_seed_words:
                rejected.append({"text": candidate, "reason": "too_vague"})
                continue
            key = candidate.strip().lower()
            if key in seen_texts:
                rejected.append({"text": candidate, "reason": "duplicate"})
                continue
            try:
                seed_id = self.add_or_update_seed(
                    candidate,
                    trigger_keywords=trigger_keywords,
                    deduplicate=deduplicate,
                    origin=origin,
                )
            except ValueError:
                rejected.append({"text": candidate, "reason": "not_atomic"})
                continue
            if seed_id in accepted_ids:
                # Deduplication merged this candidate into a seed that was
                # already accepted in this batch; emitting it again would
                # produce a duplicate seed_id row. Record it as a duplicate
                # instead of a second accepted seed under the same id.
                rejected.append({"text": candidate, "reason": "duplicate"})
                continue
            accepted.append({"seed_id": seed_id, "text": candidate})
            accepted_ids.add(seed_id)
            seen_texts.add(key)
        return {
            "input_count": len(raw_candidates),
            "normalized_candidates": normalized,
            "accepted": accepted,
            "rejected": rejected,
        }

    def _maybe_deduplicate_seed(self, new_embedding: np.ndarray) -> tuple[str, float] | None:
        for seed_id, seed in self._seeds.items():
            # EXPIRED is terminal (removed from shadow memory): a degraded
            # seed must not be resurrected by a near-duplicate re-detection. Skip
            # it so a new seed is created instead of reviving the dead one.
            if seed.status == SeedStatus.EXPIRED:
                continue
            similarity = float(np.dot(new_embedding, seed.embedding))
            if similarity >= self.dedup_threshold:
                return seed_id, similarity
        return None

    def _activate_existing_seed(self, seed_id: str, similarity: float) -> str:
        seed = self._seeds[seed_id]
        seed.occurrence_count += 1
        seed.trace = min(seed.trace + 0.5, self.max_trace)
        seed.turns_dormant = 0
        if seed.status != SeedStatus.PROMOTED:
            self._set_authority(seed, status=SeedStatus.ACTIVE)
        self._touch_seed(seed)
        self._record_and_sync(
            "deduplicated",
            seed_id,
            similarity=similarity,
            occurrence_count=seed.occurrence_count,
            trace=seed.trace,
        )
        return seed_id

    def _create_seed(
        self,
        text: str,
        embedding: np.ndarray,
        trigger_keywords: Iterable[str] | None,
        origin: SeedOrigin | None = None,
    ) -> str:
        seed_id = f"ss_{len(self._seeds) + 1:03d}"
        self._seeds[seed_id] = ShadowSeed(
            id=seed_id,
            text=text,
            embedding=embedding,
            trigger_keywords=list(trigger_keywords or []),
            trace=self.config.trace_start,
            origin=origin,
        )
        self._record_and_sync(
            "created",
            seed_id,
            text=text,
            origin=origin.to_dict() if origin is not None else None,
        )
        return seed_id

    def add_or_update_seed(
        self,
        text: str,
        trigger_keywords: Iterable[str] | None = None,
        deduplicate: bool = True,
        origin: SeedOrigin | None = None,
    ) -> str:
        if not self.is_atomic_seed(text, max_seed_words=self.config.max_seed_words):
            raise ValueError("Seed appears too broad. Split it into atomic seeds first.")

        new_embedding = self.get_embedding(text)
        if deduplicate:
            deduplicated = self._maybe_deduplicate_seed(new_embedding)
            if deduplicated is not None:
                # Origin records the first detection of a seed; a later
                # near-duplicate re-detection reinforces the existing seed and
                # does not overwrite its recorded origin.
                seed_id, similarity = deduplicated
                return self._activate_existing_seed(seed_id, similarity)

        return self._create_seed(text, new_embedding, trigger_keywords, origin=origin)

    def _status_after_decay(self, seed: ShadowSeed) -> SeedStatus:
        if seed.trace < self.dormant_threshold and seed.weight == 0.0:
            return SeedStatus.DORMANT
        if seed.trace < self.config.min_trace_for_gate and seed.status not in {
            SeedStatus.PROMOTED,
            SeedStatus.DORMANT,
        }:
            return SeedStatus.DECAYING
        return seed.status

    def decay_traces(self, turns_passed: int = 1) -> None:
        """TTL (Time-to-Live): decay every seed's trace and run the disappearance
        clock. Trace fades exponentially without recognition; a seed that stays
        DORMANT for ``dormant_ttl_turns`` without a TrTL trigger becomes EXPIRED.
        This is the mirror of ``reactivate_by_text`` (TrTL), which keeps seeds
        alive. EXPIRED seeds are terminal and skipped."""
        for seed_id, seed in self._seeds.items():
            if seed.status == SeedStatus.EXPIRED:
                continue

            before_trace = seed.trace
            seed.trace *= math.exp(-turns_passed / self.half_life_turns)
            self._set_authority(seed, status=self._status_after_decay(seed))

            # TTL to disappearance (4.5 §10): count consecutive dormant turns; a
            # seed that stays DORMANT without a re-recognising trigger for
            # dormant_ttl_turns becomes EXPIRED (dormant too long without a
            # trigger). Expiry is a lifecycle-driven authority reset: it clears
            # weight, so it is routed through the single authority path.
            expired = False
            if seed.status == SeedStatus.DORMANT:
                seed.turns_dormant += turns_passed
                if self.dormant_ttl_turns > 0 and seed.turns_dormant >= self.dormant_ttl_turns:
                    self._set_authority(seed, status=SeedStatus.EXPIRED, weight=0.0)
                    expired = True
            else:
                seed.turns_dormant = 0

            self._touch_seed(seed)
            self._record_and_sync(
                "trace_decayed",
                seed_id,
                turns_passed=turns_passed,
                trace_before=before_trace,
                trace_after=seed.trace,
                status=seed.status.value,
                turns_dormant=seed.turns_dormant,
            )
            if expired:
                self._record_event(
                    "expired", seed_id, reason="dormant_ttl", turns_dormant=seed.turns_dormant
                )

    def _validation_flags(self, seed: ShadowSeed, contradiction: bool) -> ValidationGateFlags:
        return ValidationGateFlags(
            internal_recognition_passed=(
                seed.occurrence_count >= self.config.min_occurrences_for_gate
                and seed.trace > self.config.min_trace_for_gate
            ),
            external_evidence_passed=seed.evidence_count >= self.config.min_evidence_for_gate,
            contradiction_free=not contradiction,
        )

    def _build_validation_result(
        self,
        *,
        seed_id: str,
        seed: ShadowSeed,
        status_before: str,
        weight_before: float,
        flags: ValidationGateFlags,
        external_evidence: bool,
        contradiction: bool,
        promoted: bool,
        verdict: str,
    ) -> ValidationGateResult:
        return ValidationGateResult(
            seed_id=seed_id,
            status_before=status_before,
            status_after=seed.status.value,
            weight_before=weight_before,
            weight_after=seed.weight,
            occurrence_count=seed.occurrence_count,
            evidence_count=seed.evidence_count,
            internal_recognition_passed=flags.internal_recognition_passed,
            external_evidence_passed=flags.external_evidence_passed,
            contradiction_free=flags.contradiction_free,
            external_evidence_applied=external_evidence,
            contradiction_applied=contradiction,
            promoted=promoted,
            verdict=verdict,
        )

    def _finalize_validation_result(
        self,
        result: ValidationGateResult,
        *,
        event_type: str | None = None,
        event_detail: dict[str, Any] | None = None,
    ) -> ValidationGateResult:
        self.validation_log.append(result)
        if event_type is not None:
            self._record_and_sync(event_type, result.seed_id, **(event_detail or {}))
        else:
            self._sync_seed(result.seed_id)
        return result

    def _apply_contradiction(
        self,
        *,
        seed_id: str,
        seed: ShadowSeed,
        status_before: str,
        weight_before: float,
        flags: ValidationGateFlags,
        external_evidence: bool,
    ) -> ValidationGateResult:
        self._open_contradiction_record(
            seed,
            reason="validation gate contradiction",
            source_ref=None,
            strength=1.0,
        )
        self._set_authority(
            seed,
            weight=max(0.0, seed.weight - self.contradiction_penalty),
            contradiction_score=min(1.0, seed.contradiction_score + 0.25),
            status=SeedStatus.NEW,
        )
        seed.occurrence_count = 1
        # Doctrine: falsified → weight 0, back to NEW. But also start the
        # disappearance clock: lower trace so a degraded seed decays toward
        # DORMANT/EXPIRED faster unless genuinely re-recognized (weight decreases and
        # TTL continues until the seed disappears).
        if self.contradiction_trace_penalty:
            seed.trace = max(0.0, seed.trace - self.contradiction_trace_penalty)
        seed.turns_dormant = 0
        self._touch_seed(seed)
        result = self._build_validation_result(
            seed_id=seed_id,
            seed=seed,
            status_before=status_before,
            weight_before=weight_before,
            flags=flags,
            external_evidence=external_evidence,
            contradiction=True,
            promoted=False,
            verdict="contradicted",
        )
        return self._finalize_validation_result(
            result,
            event_type="contradicted",
            event_detail={"weight_after": seed.weight},
        )

    def _apply_successful_validation(self, *, seed: ShadowSeed) -> tuple[bool, str]:
        new_weight = min(1.0, seed.weight + self.validation_increment)
        new_status = (
            SeedStatus.PROMOTED
            if new_weight >= self.promotion_threshold
            else SeedStatus.ACTIVE
        )
        self._set_authority(seed, weight=new_weight, status=new_status)
        self._touch_seed(seed)
        promoted = seed.status == SeedStatus.PROMOTED
        verdict = "promoted" if promoted else "validated"
        return promoted, verdict

    _VERDICT_TO_DECISION = {
        "expired": GateDecision.EXPIRED,
        "contradicted": GateDecision.CONTRADICTED,
        "promoted": GateDecision.PROMOTED,
        "validated": GateDecision.VALIDATED,
        "blocked": GateDecision.BLOCKED,
    }

    def _signals_for_boolean_gate(
        self,
        seed: ShadowSeed,
        external_evidence: bool,
        contradiction: bool,
        extra_signals: Iterable[ValidationSignal] | None,
    ) -> list[ValidationSignal]:
        """Represent a boolean-API Gate call as typed signals for the ledger.

        Recurrence is always recorded as a recurrence signal from the occurrence
        count — never as external evidence. External evidence is a separate,
        verified SSOT-kind signal only when the caller actually passed one.
        """

        if extra_signals is not None:
            return list(extra_signals)
        signals: list[ValidationSignal] = [
            recurrence_signal(seed.occurrence_count, threshold=self.config.min_occurrences_for_gate)
        ]
        if external_evidence:
            signals.append(
                ValidationSignal(
                    kind=SignalKind.SSOT,
                    direction=SignalDirection.SUPPORT,
                    strength=1.0,
                    verified=True,
                    reason="legacy external_evidence=True",
                )
            )
        if contradiction:
            signals.append(
                ValidationSignal(
                    kind=SignalKind.CONTRADICTION,
                    direction=SignalDirection.OPPOSE,
                    strength=1.0,
                    reason="legacy contradiction=True",
                )
            )
        return signals

    def run_validation_gate_detailed(
        self,
        seed_id: str,
        external_evidence: bool = False,
        contradiction: bool = False,
        signals: Iterable[ValidationSignal] | None = None,
        policy_id: str | None = None,
    ) -> ValidationGateResult:
        """Boolean-compatible Validation Gate.

        The ``external_evidence`` / ``contradiction`` booleans are retained for
        backward compatibility; they are the "evidence-required" mechanics that
        the existing suite depends on. Prefer :meth:`submit_signals` for new
        code. Either way, one immutable ``GateEvent`` is recorded, and recurrence
        is represented as recurrence — never relabeled as external evidence.
        ``signals`` (when given) are recorded verbatim on the event.
        """

        seed = self._seeds[seed_id]
        weight_before = seed.weight
        contradiction_before = self._contradiction_state(seed)
        recorded_signals = self._signals_for_boolean_gate(
            seed, external_evidence, contradiction, signals
        )
        status_before_event = seed.status.value
        result = self._run_validation_gate_core(
            seed_id, external_evidence=external_evidence, contradiction=contradiction
        )
        self._record_gate_event(
            seed,
            self._VERDICT_TO_DECISION.get(result.verdict, GateDecision.NO_CHANGE),
            recorded_signals,
            policy_id=policy_id or "legacy_boolean_gate",
            status_before=status_before_event,
            weight_before=weight_before,
            contradiction_before=contradiction_before,
            reason=f"verdict={result.verdict}",
        )
        return result

    def _run_validation_gate_core(
        self,
        seed_id: str,
        external_evidence: bool = False,
        contradiction: bool = False,
    ) -> ValidationGateResult:
        seed = self._seeds[seed_id]
        status_before = seed.status.value
        weight_before = seed.weight

        # EXPIRED is terminal: a degraded/disappeared seed cannot be re-validated
        # or re-promoted. No-op so it never climbs back from the dead.
        if seed.status == SeedStatus.EXPIRED:
            result = self._build_validation_result(
                seed_id=seed_id,
                seed=seed,
                status_before=status_before,
                weight_before=weight_before,
                flags=ValidationGateFlags(False, False, not contradiction),
                external_evidence=False,
                contradiction=contradiction,
                promoted=False,
                verdict="expired",
            )
            return self._finalize_validation_result(result)

        if external_evidence:
            self._set_authority(seed, evidence_count=seed.evidence_count + 1)

        flags = self._validation_flags(seed, contradiction)

        if contradiction:
            return self._apply_contradiction(
                seed_id=seed_id,
                seed=seed,
                status_before=status_before,
                weight_before=weight_before,
                flags=flags,
                external_evidence=external_evidence,
            )

        if (
            flags.internal_recognition_passed
            and flags.external_evidence_passed
            and flags.contradiction_free
        ):
            promoted, verdict = self._apply_successful_validation(seed=seed)
            result = self._build_validation_result(
                seed_id=seed_id,
                seed=seed,
                status_before=status_before,
                weight_before=weight_before,
                flags=flags,
                external_evidence=external_evidence,
                contradiction=False,
                promoted=promoted,
                verdict=verdict,
            )
            return self._finalize_validation_result(
                result,
                event_type="validated",
                event_detail={
                    "promoted": promoted,
                    "weight_after": seed.weight,
                    "evidence_count": seed.evidence_count,
                },
            )

        result = self._build_validation_result(
            seed_id=seed_id,
            seed=seed,
            status_before=status_before,
            weight_before=weight_before,
            flags=flags,
            external_evidence=external_evidence,
            contradiction=False,
            promoted=False,
            verdict="blocked",
        )
        return self._finalize_validation_result(
            result,
            event_type="validation_blocked",
            event_detail={
                "internal_recognition_passed": flags.internal_recognition_passed,
                "external_evidence_passed": flags.external_evidence_passed,
                "contradiction_free": flags.contradiction_free,
            },
        )

    def run_validation_gate(
        self,
        seed_id: str,
        external_evidence: bool = False,
        contradiction: bool = False,
        signals: Iterable[ValidationSignal] | None = None,
        policy_id: str | None = None,
    ) -> bool | None:
        result = self.run_validation_gate_detailed(
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
            signals=signals,
            policy_id=policy_id,
        )
        if result.verdict == "contradicted":
            return False
        if result.verdict in {"validated", "promoted"}:
            return True
        return None

    def reactivate_by_text(self, text: str, threshold: float = 0.65) -> list[str]:
        """TrTL (Trigger-to-Live): scan new input for triggers of DORMANT seeds
        and revive the matches. A dormant seed survives by contextual
        recognition — cosine similarity above ``threshold`` or a trigger-keyword
        hit — which bumps its trace, returns it to NEW and resets the dormancy
        (TTL) clock. This is the mirror of ``decay_traces`` (TTL): recognition
        keeps a seed alive, neglect lets it expire. EXPIRED seeds are terminal
        and are never reactivated."""
        query_emb = self.get_embedding(text)
        reactivated: list[str] = []

        for seed_id, seed in self._seeds.items():
            if seed.status != SeedStatus.DORMANT:
                continue

            similarity = float(np.dot(query_emb, seed.embedding))
            keyword_hit = any(
                keyword.lower() in text.lower() for keyword in seed.trigger_keywords
            )

            if similarity >= threshold or keyword_hit:
                seed.trace = min(seed.trace + self.reactivation_increment, self.max_trace)
                self._set_authority(seed, status=SeedStatus.NEW)
                seed.turns_dormant = 0
                self._touch_seed(seed)
                semantic_hit = similarity >= threshold
                if semantic_hit and keyword_hit:
                    basis = "semantic+keyword"
                elif semantic_hit:
                    basis = "semantic"
                else:
                    basis = "keyword"
                self._record_and_sync(
                    "reactivated",
                    seed_id,
                    similarity=similarity,
                    keyword_hit=keyword_hit,
                    basis=basis,
                    trace=seed.trace,
                )
                reactivated.append(seed_id)

        return reactivated

    def scan_trtl_triggers(self, text: str, threshold: float = 0.65) -> list[str]:
        """Canonical TrTL name for ``reactivate_by_text`` (4.5 §12.3
        Trigger-matching). Same behaviour; kept so call sites can use the
        doctrinal term."""
        return self.reactivate_by_text(text, threshold=threshold)

    def find_uncertain_region(
        self,
        text: str,
        threshold: float = 0.85,
        include_promoted: bool = False,
    ) -> list[dict[str, Any]]:
        """Find vector-near seeds for a new prompt or context."""
        if self.vector_constellation is None:
            return []
        query_emb = self.get_embedding(text)
        matches = self.vector_constellation.search_similar_seeds(query_emb, threshold=threshold)
        uncertain = []
        for seed_id, score, metadata in matches:
            seed = self._seeds.get(seed_id)
            if seed is None:
                continue
            if not include_promoted and seed.status == SeedStatus.PROMOTED:
                continue
            if seed.weight == 0.0:
                uncertain.append(
                    {
                        "seed_id": seed_id,
                        "similarity": score,
                        "text": seed.text,
                        "status": seed.status.value,
                        "weight": seed.weight,
                        "metadata": metadata,
                    }
                )
        return uncertain

    def apply_external_feedback(
        self,
        feedback_text: str,
        context: str,
        positive: bool = True,
        threshold: float = 0.75,
    ) -> list[dict[str, Any]]:
        if self.vector_constellation is None:
            return []
        feedback_emb = self.get_embedding(f"FEEDBACK: {feedback_text} OP: {context}")
        matches = self.vector_constellation.search_similar_seeds(feedback_emb, threshold=threshold)
        updates = []
        for seed_id, score, _metadata in matches:
            if seed_id not in self._seeds:
                continue
            if positive:
                result = self.run_validation_gate(
                    seed_id,
                    external_evidence=True,
                    signals=[
                        ValidationSignal(
                            kind=SignalKind.HUMAN_FEEDBACK,
                            direction=SignalDirection.SUPPORT,
                            strength=float(score),
                            source_ref=context,
                            verified=True,
                            reason="external feedback (positive)",
                        )
                    ],
                )
            else:
                result = self.run_validation_gate(
                    seed_id,
                    contradiction=True,
                    signals=[
                        ValidationSignal(
                            kind=SignalKind.CONTRADICTION,
                            direction=SignalDirection.OPPOSE,
                            strength=float(score),
                            source_ref=context,
                            reason="external feedback (negative)",
                        )
                    ],
                )
            self.vector_constellation.record_feedback(
                seed_id=seed_id,
                feedback=feedback_text,
                is_correction=positive,
                similarity=score,
            )
            updates.append(
                {
                    "seed_id": seed_id,
                    "similarity": score,
                    "gate_result": result,
                    "seed": self._seeds[seed_id].to_dict(),
                }
            )
        return updates

    def expire_vector_only_open_seeds(self, max_age_days: int = 30) -> list[str]:
        if self.vector_constellation is None:
            return []
        expired = self.vector_constellation.housekeeping(max_age_days=max_age_days)
        for seed_id in expired:
            if seed_id in self._seeds:
                # Expiry is a terminal authority reset: clear weight too, matching
                # TTL expiry, so an expired seed carries no residual authority.
                self._set_authority(
                    self._seeds[seed_id], status=SeedStatus.EXPIRED, weight=0.0
                )
                self._touch_seed(self._seeds[seed_id])
                self._record_event("expired", seed_id, max_age_days=max_age_days)
        return expired

    @staticmethod
    def _constellation_label(cluster: list[ShadowSeed]) -> str:
        for seed in cluster:
            for keyword in seed.trigger_keywords:
                clean = keyword.strip()
                if clean:
                    return f"Cluster rond {clean}."
        seed_text = cluster[0].text.strip().rstrip(".")
        return f"Cluster rond {seed_text[:48]}."

    def find_constellations(
        self, threshold: float = 0.70, min_members: int = 3
    ) -> list[Constellation]:
        promoted = [
            seed for seed in self._seeds.values() if seed.status == SeedStatus.PROMOTED
        ]
        constellations: list[Constellation] = []
        seen: set[tuple[str, ...]] = set()

        for index, seed in enumerate(promoted):
            cluster = [seed]
            for other in promoted[index + 1 :]:
                similarity = float(np.dot(seed.embedding, other.embedding))
                if similarity >= threshold:
                    cluster.append(other)

            if len(cluster) >= min_members:
                member_ids = tuple(sorted(item.id for item in cluster))
                if member_ids in seen:
                    continue
                seen.add(member_ids)
                centroid = np.mean([item.embedding for item in cluster], axis=0)
                constellations.append(
                    Constellation(
                        members=list(member_ids),
                        centroid=centroid.tolist(),
                        combined_weight=float(np.mean([item.weight for item in cluster])),
                        id=f"const_{len(constellations) + 1:03d}",
                        label=self._constellation_label(cluster),
                        probe_type="retrieval" if len(cluster) >= 5 else "socratic",
                    )
                )

        return constellations

    def get_seed(self, seed_id: str) -> ShadowSeed:
        return self._seeds[seed_id]

    def apply_probe_feedback(
        self,
        seed_id: str,
        outcome: ProbeOutcome | Literal["reward", "penalty", "neutral"],
        probe_type: ProbeType | Literal["follow_up", "retrieval", "dialectic", "general"] = ProbeType.GENERAL,
    ) -> ProbeFeedbackResult:
        """Apply bounded probe feedback to an existing seed.

        Probe feedback is a weaker signal than the Validation Gate. It can only
        adjust weight for ACTIVE or PROMOTED seeds. It cannot promote a seed on
        its own, but it can demote a PROMOTED seed back to ACTIVE when repeated
        penalties push weight below the promotion threshold.
        """
        if seed_id not in self._seeds:
            raise KeyError(f"Seed '{seed_id}' does not exist.")

        seed = self._seeds[seed_id]
        outcome_enum = ProbeOutcome(outcome)
        probe_type_enum = ProbeType(probe_type)

        status_before = seed.status.value
        weight_before = seed.weight

        feedbackable = {SeedStatus.ACTIVE, SeedStatus.PROMOTED}
        if seed.status not in feedbackable:
            result = ProbeFeedbackResult(
                seed_id=seed_id,
                probe_type=probe_type_enum.value,
                outcome=outcome_enum.value,
                weight_before=weight_before,
                weight_after=weight_before,
                delta_applied=0.0,
                status_before=status_before,
                status_after=status_before,
                demoted=False,
                skipped=True,
                skip_reason=f"status '{seed.status.value}' does not accept feedback",
            )
            self.feedback_log.append(result)
            return result

        delta_map: dict[ProbeOutcome, float] = {
            ProbeOutcome.REWARD: self.reward_step,
            ProbeOutcome.PENALTY: -self.penalty_step,
            ProbeOutcome.NEUTRAL: 0.0,
        }
        delta_requested = delta_map[outcome_enum]
        new_weight = max(0.0, min(1.0, seed.weight + delta_requested))

        demoted = (
            seed.status == SeedStatus.PROMOTED
            and new_weight < self.promotion_threshold
        )

        self._set_authority(
            seed,
            weight=new_weight,
            status=SeedStatus.ACTIVE if demoted else None,
        )
        self._touch_seed(seed)

        delta_applied = seed.weight - weight_before
        result = ProbeFeedbackResult(
            seed_id=seed_id,
            probe_type=probe_type_enum.value,
            outcome=outcome_enum.value,
            weight_before=weight_before,
            weight_after=seed.weight,
            delta_applied=delta_applied,
            status_before=status_before,
            status_after=seed.status.value,
            demoted=demoted,
            skipped=False,
            skip_reason="",
        )
        self.feedback_log.append(result)
        # Record the probe effect as a typed probe signal on the Gate ledger, so
        # the authority change is attributable even though probe feedback is a
        # bounded nudge rather than a full promotion policy.
        probe_direction = {
            ProbeOutcome.REWARD: SignalDirection.SUPPORT,
            ProbeOutcome.PENALTY: SignalDirection.OPPOSE,
            ProbeOutcome.NEUTRAL: SignalDirection.NEUTRAL,
        }[outcome_enum]
        if demoted:
            probe_decision = GateDecision.DEMOTED
        elif delta_applied != 0.0:
            probe_decision = GateDecision.VALIDATED
        else:
            probe_decision = GateDecision.NO_CHANGE
        self._record_gate_event(
            seed,
            probe_decision,
            [
                ValidationSignal(
                    kind=SignalKind.PROBE,
                    direction=probe_direction,
                    strength=min(1.0, abs(delta_requested)),
                    source_ref=probe_type_enum.value,
                    reason=f"probe {outcome_enum.value} ({probe_type_enum.value})",
                )
            ],
            policy_id="probe_feedback",
            status_before=status_before,
            weight_before=weight_before,
            contradiction_before=self._contradiction_state(seed),
            reason=f"probe {outcome_enum.value}",
        )
        self._record_and_sync(
            "probe_feedback",
            seed_id,
            probe_type=probe_type_enum.value,
            outcome=outcome_enum.value,
            weight_before=weight_before,
            weight_after=seed.weight,
            delta_requested=delta_requested,
            delta_applied=delta_applied,
            demoted=demoted,
        )
        return result

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "seeds": [seed.to_dict() for seed in self._seeds.values()],
            "constellations": [item.to_dict() for item in self.find_constellations()],
            "validation_log": [item.to_dict() for item in self.validation_log],
            "event_log": [item.to_dict() for item in self.event_log],
            "feedback_log": [item.to_dict() for item in self.feedback_log],
            "gate_events": [item.to_dict() for item in self.gate_events],
            "contradiction_records": [item.to_dict() for item in self.contradiction_records],
            "vector_constellation": (
                self.vector_constellation.to_dict()
                if self.vector_constellation is not None
                else None
            ),
        }
