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
Stable data contracts live in :mod:`shadowseed.models` and are re-exported here
for backward compatibility.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import math
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Iterable, Literal, Mapping

import numpy as np

from shadowseed.contradictions import ContradictionDomain as _ContradictionDomain
from shadowseed import intake as intake_engine
from shadowseed.core_config import SSLCoreConfig
from shadowseed.gate.contradictions import (
    ContradictionRecord,
    ContradictionStatus,  # noqa: F401 - re-exported for compatibility
)
from shadowseed.gate.events import (
    ContradictionState,
    GateDecision,
    GateEvent,
    new_event_id,
)
# The single executable Validation Gate engine. The Gate methods on SSLManager
# delegate to this module; there is no second decision path and nothing is
# installed onto the class at import time.
from shadowseed.gate import runtime_adapter as gate_engine
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
)
from shadowseed.models import (
    AUTHORITY_FIELDS,
    CandidateType,
    Constellation,
    ProbeFeedbackResult,
    ProbeOutcome,
    ProbeType,
    SeedEvent,
    SeedOrigin,
    SeedStatus,
    ShadowSeed,
    ValidationGateFlags,
    ValidationGateResult,
    WEIGHT_MAX,
    WEIGHT_MIN,
    validate_seed_snapshot,
)
from shadowseed.seed_normalization import normalize_detection_candidates

if TYPE_CHECKING:
    from shadowseed.vector_constellation import VectorConstellation


DEFAULT_CONFIG = SSLCoreConfig()


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
        # Canonical contradiction collection and lifecycle workflows. Public
        # manager attributes and methods below remain compatibility facades.
        self._contradictions = _ContradictionDomain()

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
        It is an explicit, unsupported escape hatch, not a normal API.
        """

        self._seeds[seed.id] = seed

    def restore_seed(self, data: dict[str, Any], *, replace_existing: bool = False) -> ShadowSeed:
        """Deserialize a persisted seed and install it, preserving its authority
        snapshot and version. This is the supported migration/deserialization
        path (not an authority decision); it does not run the Gate.

        The snapshot is fully validated and reconstructed *before* any registry
        change, so invalid data never partially mutates the registry. Duplicate
        handling is explicit and never silent:

        - a new seed id is installed;
        - an existing id with ``replace_existing=False`` (the default) raises,
          so a persisted snapshot can never accidentally clobber a live seed;
        - an existing id with ``replace_existing=True`` is replaced deliberately.
        """

        # Validate and build first; a malformed snapshot raises here, before the
        # duplicate check and before the registry is touched.
        seed = ShadowSeed.from_dict(data)
        if seed.id in self._seeds and not replace_existing:
            raise ValueError(
                f"a seed with id {seed.id!r} already exists; pass "
                "replace_existing=True to replace it deliberately"
            )
        self._seeds[seed.id] = seed
        return seed

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

    @property
    def contradiction_records(self) -> list[ContradictionRecord]:
        """Historical mutable record list, backed by the canonical domain."""

        return self._contradictions.records

    @contradiction_records.setter
    def contradiction_records(self, records: Iterable[ContradictionRecord]) -> None:
        self._contradictions.replace_records(records)

    @property
    def _contradiction_sequence(self) -> int:
        """Compatibility view of the domain-owned identifier sequence."""

        return self._contradictions.sequence

    @_contradiction_sequence.setter
    def _contradiction_sequence(self, value: int) -> None:
        self._contradictions.sequence = value

    def open_contradictions(self, seed_id: str) -> list[ContradictionRecord]:
        """Unresolved (blocking) contradiction records for a seed."""

        return self._contradictions.open_for(seed_id)


    def contradictions_for(self, seed_id: str) -> list[ContradictionRecord]:
        """All contradiction records for a seed, in creation order."""

        return self._contradictions.contradictions_for(seed_id)


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

        return self._contradictions.state_for(seed)


    def _open_contradiction_record(
        self,
        seed: ShadowSeed,
        *,
        reason: str,
        source_ref: str | None,
        strength: float,
    ) -> ContradictionRecord:
        return self._contradictions.open(
            seed,
            reason=reason,
            source_ref=source_ref,
            strength=strength,
            created_at=self._now_iso(),
        )


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
        """Resolve contradiction records through the canonical Gate boundary."""

        return gate_engine.resolve_contradiction(
            self,
            seed_id,
            basis=basis,
            contradiction_id=contradiction_id,
            superseded=superseded,
            withdrawn=withdrawn,
            resolver=resolver,
        )


    def migrate_legacy_contradictions(self) -> list[ContradictionRecord]:
        """Create an open record for any seed with a legacy scalar but no records.

        Idempotent: seeds that already have records are left untouched. Returns
        the records created, for logging or tests.
        """

        return self._contradictions.migrate_legacy(
            self._seeds.values(),
            open_record=self._open_contradiction_record,
        )


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

        The decision body lives in :mod:`shadowseed.gate.runtime_adapter`, the
        single Gate engine; this method delegates to it explicitly so there is
        exactly one executable implementation.
        """

        return gate_engine.submit_signals(self, seed_id, signals, policy_id)

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
        """Mirror a Gate decision into ``validation_log``.

        Delegates to the Gate engine's verified-evidence logging: only
        explicitly verified external support may be reported as passed/applied
        evidence, so an unverified observation is never logged as evidence.
        """

        gate_engine.log_validation_from_signals(
            self,
            seed,
            decision,
            signals,
            status_before=status_before,
            weight_before=weight_before,
        )

    def _sync_seed(self, seed_id: str) -> None:
        if self.vector_constellation is not None:
            self.vector_constellation.sync_seed(self._seeds[seed_id])

    def _record_and_sync(self, event_type: str, seed_id: str, **detail: Any) -> None:
        self._record_event(event_type, seed_id, **detail)
        self._sync_seed(seed_id)

    def _load_embedder(self):
        """Compatibility facade for the canonical intake backend loader."""

        return intake_engine.load_embedder(self)

    def get_embedding(self, text: str) -> np.ndarray:
        """Compatibility facade for canonical intake embedding."""

        return intake_engine.get_embedding(self, text)

    @staticmethod
    def _normalize_embedding(embedding: np.ndarray) -> np.ndarray:
        """Compatibility facade for historical callers and tests."""

        return intake_engine.normalize_embedding(embedding)

    @staticmethod
    def is_atomic_seed(text: str, max_seed_words: int | None = None) -> bool:
        """Compatibility facade for the canonical atomicity heuristic."""

        return intake_engine.is_atomic_seed(text, max_seed_words=max_seed_words)

    def normalize_detection_candidates(
        self,
        candidates: Iterable[str],
        expand_short_fragments: bool = True,
        split_broad: bool = True,
    ) -> list[str]:
        """Compatibility facade for detector-candidate normalization."""

        return intake_engine.normalize_detection_candidates(
            candidates,
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
        """Compatibility facade for canonical candidate intake."""

        return intake_engine.ingest_detection_candidates(
            self,
            candidates,
            trigger_keywords=trigger_keywords,
            expand_short_fragments=expand_short_fragments,
            split_broad=split_broad,
            deduplicate=deduplicate,
            min_seed_words=min_seed_words,
            origin=origin,
        )

    def _maybe_deduplicate_seed(
        self, new_embedding: np.ndarray
    ) -> tuple[str, float] | None:
        return intake_engine.maybe_deduplicate_seed(self, new_embedding)

    def _activate_existing_seed(self, seed_id: str, similarity: float) -> str:
        return intake_engine.activate_existing_seed(self, seed_id, similarity)

    def _create_seed(
        self,
        text: str,
        embedding: np.ndarray,
        trigger_keywords: Iterable[str] | None,
        origin: SeedOrigin | None = None,
    ) -> str:
        return intake_engine.create_seed(
            self,
            text,
            embedding,
            trigger_keywords,
            origin=origin,
        )

    def add_or_update_seed(
        self,
        text: str,
        trigger_keywords: Iterable[str] | None = None,
        deduplicate: bool = True,
        origin: SeedOrigin | None = None,
    ) -> str:
        """Compatibility facade for canonical seed intake and deduplication."""

        return intake_engine.add_or_update_seed(
            self,
            text,
            trigger_keywords=trigger_keywords,
            deduplicate=deduplicate,
            origin=origin,
        )

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

    def run_validation_gate_detailed(
        self,
        seed_id: str,
        external_evidence: bool = False,
        contradiction: bool = False,
        signals: Iterable[ValidationSignal] | None = None,
        policy_id: str | None = None,
    ) -> ValidationGateResult:
        """Boolean-compatible Validation Gate (compatibility adapter).

        The ``external_evidence`` / ``contradiction`` booleans are retained for
        backward compatibility; prefer :meth:`submit_signals` for new code. This
        is an input/output adapter only: the arguments are translated into typed
        signals, the single Gate engine decides under the
        ``legacy_evidence_required`` policy, and the resulting event is
        translated back into the legacy result shape. One call still records
        exactly one ``GateEvent``, attributed to the policy that decided it, and
        recurrence is represented as recurrence — never as external evidence.
        """

        return gate_engine.run_validation_gate_detailed(
            self,
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
            signals=signals,
            policy_id=policy_id,
        )

    def _run_validation_gate_core(
        self,
        seed_id: str,
        external_evidence: bool = False,
        contradiction: bool = False,
        signals: Iterable[ValidationSignal] | None = None,
        policy_id: str | None = None,
    ) -> ValidationGateResult:
        """Historical private entry point, kept as an alias of the public
        adapter so no second decision path can exist behind it."""

        return gate_engine.run_validation_gate_detailed(
            self,
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
            signals=signals,
            policy_id=policy_id,
        )

    def run_validation_gate(
        self,
        seed_id: str,
        external_evidence: bool = False,
        contradiction: bool = False,
        signals: Iterable[ValidationSignal] | None = None,
        policy_id: str | None = None,
    ) -> bool | None:
        """Boolean verdict form of :meth:`run_validation_gate_detailed`."""

        return gate_engine.run_validation_gate(
            self,
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
            signals=signals,
            policy_id=policy_id,
        )

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
        feedback_emb = self.get_embedding(f"FEEDBACK: {feedback_text} ON: {context}")
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
                    return f"Cluster around {clean}."
        seed_text = cluster[0].text.strip().rstrip(".")
        return f"Cluster around {seed_text[:48]}."

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
        probe_type: ProbeType
        | Literal["follow_up", "retrieval", "dialectic", "general"] = ProbeType.GENERAL,
    ) -> ProbeFeedbackResult:
        """Apply bounded probe feedback through the canonical Gate boundary."""

        return gate_engine.apply_probe_feedback(self, seed_id, outcome, probe_type)

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.to_dict(),
            "seeds": [seed.to_dict() for seed in self._seeds.values()],
            "constellations": [item.to_dict() for item in self.find_constellations()],
            "validation_log": [item.to_dict() for item in self.validation_log],
            "event_log": [item.to_dict() for item in self.event_log],
            "feedback_log": [item.to_dict() for item in self.feedback_log],
            "gate_events": [item.to_dict() for item in self.gate_events],
            "contradiction_records": [
                item.to_dict() for item in self.contradiction_records
            ],
            "vector_constellation": (
                self.vector_constellation.to_dict()
                if self.vector_constellation is not None
                else None
            ),
        }
