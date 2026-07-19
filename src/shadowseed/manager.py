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
from typing import TYPE_CHECKING, Any, Callable, Iterable, Literal

import numpy as np

from shadowseed.core_config import SSLCoreConfig
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


@dataclass
class ShadowSeed:
    id: str
    text: str
    embedding: np.ndarray
    trigger_keywords: list[str] = field(default_factory=list)
    trace: float = 2.0
    weight: float = 0.0
    occurrence_count: int = 1
    evidence_count: int = 0
    contradiction_score: float = 0.0
    turns_dormant: int = 0
    status: SeedStatus = SeedStatus.NEW
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["embedding"] = self.embedding.tolist()
        data["status"] = self.status.value
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
        self.seeds: dict[str, ShadowSeed] = {}
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

    @staticmethod
    def _now_iso() -> str:
        return datetime.now().isoformat()

    def _record_event(self, event_type: str, seed_id: str, **detail: Any) -> None:
        self.event_log.append(SeedEvent(event_type=event_type, seed_id=seed_id, detail=detail))

    def _touch_seed(self, seed: ShadowSeed) -> None:
        seed.updated_at = self._now_iso()

    def _sync_seed(self, seed_id: str) -> None:
        if self.vector_constellation is not None:
            self.vector_constellation.sync_seed(self.seeds[seed_id])

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
                    candidate, trigger_keywords=trigger_keywords, deduplicate=deduplicate
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
        for seed_id, seed in self.seeds.items():
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
        seed = self.seeds[seed_id]
        seed.occurrence_count += 1
        seed.trace = min(seed.trace + 0.5, self.max_trace)
        seed.turns_dormant = 0
        if seed.status != SeedStatus.PROMOTED:
            seed.status = SeedStatus.ACTIVE
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
    ) -> str:
        seed_id = f"ss_{len(self.seeds) + 1:03d}"
        self.seeds[seed_id] = ShadowSeed(
            id=seed_id,
            text=text,
            embedding=embedding,
            trigger_keywords=list(trigger_keywords or []),
            trace=self.config.trace_start,
        )
        self._record_and_sync("created", seed_id, text=text)
        return seed_id

    def add_or_update_seed(
        self,
        text: str,
        trigger_keywords: Iterable[str] | None = None,
        deduplicate: bool = True,
    ) -> str:
        if not self.is_atomic_seed(text, max_seed_words=self.config.max_seed_words):
            raise ValueError("Seed appears too broad. Split it into atomic seeds first.")

        new_embedding = self.get_embedding(text)
        if deduplicate:
            deduplicated = self._maybe_deduplicate_seed(new_embedding)
            if deduplicated is not None:
                seed_id, similarity = deduplicated
                return self._activate_existing_seed(seed_id, similarity)

        return self._create_seed(text, new_embedding, trigger_keywords)

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
        for seed_id, seed in self.seeds.items():
            if seed.status == SeedStatus.EXPIRED:
                continue

            before_trace = seed.trace
            seed.trace *= math.exp(-turns_passed / self.half_life_turns)
            seed.status = self._status_after_decay(seed)

            # TTL to disappearance (4.5 §10): count consecutive dormant turns; a
            # seed that stays DORMANT without a re-recognising trigger for
            # dormant_ttl_turns becomes EXPIRED ("te lang dormant zonder trigger").
            expired = False
            if seed.status == SeedStatus.DORMANT:
                seed.turns_dormant += turns_passed
                if self.dormant_ttl_turns > 0 and seed.turns_dormant >= self.dormant_ttl_turns:
                    seed.status = SeedStatus.EXPIRED
                    seed.weight = 0.0
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
        seed.weight = max(0.0, seed.weight - self.contradiction_penalty)
        seed.contradiction_score = min(1.0, seed.contradiction_score + 0.25)
        seed.occurrence_count = 1
        # Doctrine: falsified → weight 0, back to NEW. But also start the
        # disappearance clock: lower trace so a degraded seed decays toward
        # DORMANT/EXPIRED faster unless genuinely re-recognized (weight decreases and
        # TTL continues until the seed disappears).
        if self.contradiction_trace_penalty:
            seed.trace = max(0.0, seed.trace - self.contradiction_trace_penalty)
        seed.turns_dormant = 0
        seed.status = SeedStatus.NEW
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
        seed.weight = min(1.0, seed.weight + self.validation_increment)
        seed.status = (
            SeedStatus.PROMOTED
            if seed.weight >= self.promotion_threshold
            else SeedStatus.ACTIVE
        )
        self._touch_seed(seed)
        promoted = seed.status == SeedStatus.PROMOTED
        verdict = "promoted" if promoted else "validated"
        return promoted, verdict

    def run_validation_gate_detailed(
        self,
        seed_id: str,
        external_evidence: bool = False,
        contradiction: bool = False,
    ) -> ValidationGateResult:
        seed = self.seeds[seed_id]
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
            seed.evidence_count += 1

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
    ) -> bool | None:
        result = self.run_validation_gate_detailed(
            seed_id,
            external_evidence=external_evidence,
            contradiction=contradiction,
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

        for seed_id, seed in self.seeds.items():
            if seed.status != SeedStatus.DORMANT:
                continue

            similarity = float(np.dot(query_emb, seed.embedding))
            keyword_hit = any(
                keyword.lower() in text.lower() for keyword in seed.trigger_keywords
            )

            if similarity >= threshold or keyword_hit:
                seed.trace = min(seed.trace + self.reactivation_increment, self.max_trace)
                seed.status = SeedStatus.NEW
                seed.turns_dormant = 0
                self._touch_seed(seed)
                self._record_and_sync(
                    "reactivated",
                    seed_id,
                    similarity=similarity,
                    keyword_hit=keyword_hit,
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
            seed = self.seeds.get(seed_id)
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
            if seed_id not in self.seeds:
                continue
            if positive:
                result = self.run_validation_gate(seed_id, external_evidence=True)
            else:
                result = self.run_validation_gate(seed_id, contradiction=True)
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
                    "seed": self.seeds[seed_id].to_dict(),
                }
            )
        return updates

    def expire_vector_only_open_seeds(self, max_age_days: int = 30) -> list[str]:
        if self.vector_constellation is None:
            return []
        expired = self.vector_constellation.housekeeping(max_age_days=max_age_days)
        for seed_id in expired:
            if seed_id in self.seeds:
                self.seeds[seed_id].status = SeedStatus.EXPIRED
                self._touch_seed(self.seeds[seed_id])
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
            seed for seed in self.seeds.values() if seed.status == SeedStatus.PROMOTED
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
        return self.seeds[seed_id]

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
        if seed_id not in self.seeds:
            raise KeyError(f"Seed '{seed_id}' does not exist.")

        seed = self.seeds[seed_id]
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

        seed.weight = new_weight
        if demoted:
            seed.status = SeedStatus.ACTIVE
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
            "seeds": [seed.to_dict() for seed in self.seeds.values()],
            "constellations": [item.to_dict() for item in self.find_constellations()],
            "validation_log": [item.to_dict() for item in self.validation_log],
            "event_log": [item.to_dict() for item in self.event_log],
            "feedback_log": [item.to_dict() for item in self.feedback_log],
            "vector_constellation": (
                self.vector_constellation.to_dict()
                if self.vector_constellation is not None
                else None
            ),
        }
