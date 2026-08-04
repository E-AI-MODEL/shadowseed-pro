"""Shadow Seed Learning 4.6 core manager.

The manager coordinates lifecycle, Validation Gate, contradiction, probe, and
constellation workflows. Stable data contracts live in :mod:`shadowseed.models`
and are re-exported here for backward compatibility.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import math
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Callable, Iterable, Literal, Mapping

import numpy as np

from shadowseed.core_config import SSLCoreConfig
from shadowseed.gate import runtime_adapter as gate_engine
from shadowseed.gate.contradictions import ContradictionRecord, ContradictionStatus
from shadowseed.gate.events import ContradictionState, GateDecision, GateEvent, new_event_id
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
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
        self.gate_events: list[GateEvent] = []
        self._gate_sequence = 0
        self.contradiction_records: list[ContradictionRecord] = []
        self._contradiction_sequence = 0

    @property
    def seeds(self) -> Mapping[str, ShadowSeed]:
        """Read-only view of the seed registry."""

        return MappingProxyType(self._seeds)

    def unsafe_install_seed(self, seed: ShadowSeed) -> None:
        """Test/benchmark-only insertion hook."""

        self._seeds[seed.id] = seed

    def restore_seed(self, data: dict[str, Any], *, replace_existing: bool = False) -> ShadowSeed:
        """Deserialize and install a persisted seed without a Gate transition."""

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
        """Single production authority-transition path."""

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
        return [
            record
            for record in self.contradiction_records
            if record.seed_id == seed_id and record.is_blocking
        ]

    def contradictions_for(self, seed_id: str) -> list[ContradictionRecord]:
        return [r for r in self.contradiction_records if r.seed_id == seed_id]

    def is_blocking_contradiction(self, seed_id: str) -> bool:
        return self._contradiction_state(self._seeds[seed_id]).blocking

    def _contradiction_state(self, seed: ShadowSeed) -> ContradictionState:
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
        if self._embedder is not None:
            return self._embedder
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise ImportError(
                "Install sentence-transformers to use SSLManager: "
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
        for seed_id, seed in self._seeds.items():
            if seed.status == SeedStatus.EXPIRED:
                continue

            before_trace = seed.trace
            seed.trace *= math.exp(-turns_passed / self.half_life_turns)
            self._set_authority(seed, status=self._status_after_decay(seed))

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
        return gate_engine.run_validation_gate(
            self,
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
            signals=signals,
            policy_id=policy_id,
        )

    def reactivate_by_text(self, text: str, threshold: float = 0.65) -> list[str]:
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
        return self.reactivate_by_text(text, threshold=threshold)

    def find_uncertain_region(
        self,
        text: str,
        threshold: float = 0.85,
        include_promoted: bool = False,
    ) -> list[dict[str, Any]]:
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

        demoted = seed.status == SeedStatus.PROMOTED and new_weight < self.promotion_threshold

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


__all__ = [
    "AUTHORITY_FIELDS",
    "CandidateType",
    "Constellation",
    "ProbeFeedbackResult",
    "ProbeOutcome",
    "ProbeType",
    "SSLManager",
    "SeedEvent",
    "SeedOrigin",
    "SeedStatus",
    "ShadowSeed",
    "ValidationGateFlags",
    "ValidationGateResult",
    "WEIGHT_MAX",
    "WEIGHT_MIN",
    "validate_seed_snapshot",
]
