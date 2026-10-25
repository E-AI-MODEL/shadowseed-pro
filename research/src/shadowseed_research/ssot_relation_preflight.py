"""Research-only SSOT relation review preflight for issue #241.

A retrieval similarity score is never a judgment about whether text supports
a seed. This module records externally *asserted* source/seed relationships;
it cannot verify human identity, source truth, or genuine independence.

It never writes product state, creates Gate signals, or promotes a seed.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from hashlib import sha256
from math import isfinite
from typing import Mapping, Sequence


class Relation(str, Enum):
    SUPPORTS = "supports"
    OPPOSES = "opposes"
    TOPICAL = "topical"
    UNDETERMINED = "undetermined"
    NOT_TESTABLE = "not_testable"


def fingerprint(text: str) -> str:
    """Version-bind exact UTF-8 text; a digest never proves source truth."""
    return sha256(text.encode("utf-8")).hexdigest()


def _required(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


@dataclass(frozen=True)
class RetrievedHit:
    seed_id: str
    seed_text: str
    doc_id: str
    chunk_id: str
    chunk_text: str
    status: str
    similarity: float

    def __post_init__(self) -> None:
        for name in ("seed_id", "seed_text", "doc_id", "chunk_id",
                     "chunk_text", "status"):
            _required(getattr(self, name), name)
        if not isfinite(self.similarity) or not -1 <= self.similarity <= 1:
            raise ValueError("similarity must be finite and in [-1, 1]")


@dataclass(frozen=True)
class RelationAttestation:
    """Untrusted until separately verified by a real external process.

    Review refers to one exact seed and chunk version. source_unit_id groups
    distinct chunks/copies of one underlying source, but its asserted value
    does NOT establish the true independence of two source units.
    """

    seed_id: str
    seed_digest: str
    doc_id: str
    chunk_id: str
    chunk_digest: str
    source_unit_id: str
    relation: Relation
    source_checked_by: str
    relation_checked_by: str
    reviewed_at: str
    rationale: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "relation", Relation(self.relation))
        for name in ("seed_id", "seed_digest", "doc_id", "chunk_id",
                     "chunk_digest", "source_unit_id", "source_checked_by",
                     "relation_checked_by", "reviewed_at", "rationale"):
            _required(getattr(self, name), name)
        for name in ("seed_digest", "chunk_digest"):
            value = getattr(self, name)
            if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
                raise ValueError(f"{name} must be a lowercase SHA-256 digest")
        try:
            timestamp = datetime.fromisoformat(self.reviewed_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("reviewed_at must be an ISO 8601 timestamp") from exc
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("reviewed_at must include a timezone")


@dataclass(frozen=True)
class PreflightRecord:
    seed_id: str
    chunk_id: str
    doc_id: str
    relation: Relation | None
    source_unit_id: str | None
    disposition: str
    possible_support_for_external_review: bool
    # Deliberately constant: the preflight can NEVER authorize the product Gate.
    gate_authorized: bool = False


@dataclass(frozen=True)
class BatchPreflight:
    observations: tuple[PreflightRecord, ...]
    support_units_to_review: tuple[tuple[str, str], ...]
    conflicting_source_units: tuple[tuple[str, str], ...]
    gate_authorized: bool = False


def preflight_hit(
    hit: RetrievedHit,
    review: RelationAttestation | None,
) -> PreflightRecord:
    """Fail closed without an exact externally asserted relationship.

    OPPOSES never creates a contradiction or falsifies a question/what-if.
    A 'verified' metadata flag is only a legacy status, not a truth proof.
    """
    base = {"seed_id": hit.seed_id, "chunk_id": hit.chunk_id,
            "doc_id": hit.doc_id}
    if review is None:
        return PreflightRecord(**base, relation=None, source_unit_id=None,
                               disposition="relation_review_missing",
                               possible_support_for_external_review=False)
    matching = (
        hit.seed_id == review.seed_id
        and hit.doc_id == review.doc_id
        and hit.chunk_id == review.chunk_id
        and fingerprint(hit.seed_text) == review.seed_digest
        and fingerprint(hit.chunk_text) == review.chunk_digest
    )
    if not matching:
        return PreflightRecord(**base, relation=None, source_unit_id=None,
                               disposition="stale_or_wrong_identity",
                               possible_support_for_external_review=False)
    if hit.status != "verified":
        return PreflightRecord(**base, relation=review.relation,
                               source_unit_id=review.source_unit_id,
                               disposition="source_not_verified",
                               possible_support_for_external_review=False)
    descriptions = {
        Relation.SUPPORTS: "asserted_support_needs_external_check",
        Relation.OPPOSES: "asserted_opposition_not_auto_contradiction",
        Relation.TOPICAL: "topic_relevance_only",
        Relation.UNDETERMINED: "relation_undetermined",
        Relation.NOT_TESTABLE: "relation_not_testable",
    }
    return PreflightRecord(
        **base,
        relation=review.relation,
        source_unit_id=review.source_unit_id,
        disposition=descriptions[review.relation],
        possible_support_for_external_review=(review.relation is Relation.SUPPORTS),
    )


def preflight_batch(
    hits: Sequence[RetrievedHit],
    reviews: Mapping[tuple[str, str], RelationAttestation],
) -> BatchPreflight:
    """Keep all observations; count at most one possible unit per source.

    Conflicting relations from the same asserted source unit quarantine that
    unit. No run from here can create supporting Gate signals.
    """
    records = [
        preflight_hit(hit, reviews.get((hit.seed_id, hit.chunk_id)))
        for hit in hits
    ]
    relations: dict[tuple[str, str], set[Relation]] = {}
    for record in records:
        if record.source_unit_id and record.relation is not None:
            relations.setdefault((record.seed_id, record.source_unit_id), set()).add(record.relation)
    conflicting = {
        unit for unit, values in relations.items()
        if len(values) > 1
    }
    records = [
        replace(record, disposition="conflicting_relation_same_source",
                possible_support_for_external_review=False)
        if (record.seed_id, record.source_unit_id) in conflicting else record
        for record in records
    ]
    support = sorted({
        (record.seed_id, record.source_unit_id)
        for record in records
        if record.possible_support_for_external_review
        and record.source_unit_id is not None
    })
    return BatchPreflight(
        observations=tuple(records),
        support_units_to_review=tuple(support),
        conflicting_source_units=tuple(sorted(conflicting)),
    )
