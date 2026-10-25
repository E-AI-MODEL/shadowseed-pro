"""Research-contract tests: no similarity-to-SUPPORT shortcut and no Gate writes.

Human relation values are deliberately authored test inputs, not machine
entailment, verified evidence, or independent fact-checking.
"""

from dataclasses import replace

import pytest

from shadowseed_research.ssot_relation_preflight import (
    BatchPreflight,
    Relation,
    RelationAttestation,
    RetrievedHit,
    fingerprint,
    preflight_batch,
    preflight_hit,
)

SEED = "Mogelijk beïnvloedt de blauwe klep de druk in kamer B."
YES = "De blauwe klep beïnvloedt de druk in kamer B."
NO = "De blauwe klep beïnvloedt de druk in kamer B niet."
DATE = "2026-10-25T09:00:00+01:00"


def hit(text: str, *, chunk: str = "source::chunk_1", doc: str = "source",
        seed_id: str = "seed-1", status: str = "verified",
        similarity: float = 0.99) -> RetrievedHit:
    return RetrievedHit(
        seed_id=seed_id, seed_text=SEED, doc_id=doc,
        chunk_id=chunk, chunk_text=text, status=status, similarity=similarity,
    )


def reviewed(
    item: RetrievedHit, relation: Relation, *,
    unit: str = "underlying-study-a",
) -> RelationAttestation:
    return RelationAttestation(
        seed_id=item.seed_id, seed_digest=fingerprint(item.seed_text),
        doc_id=item.doc_id, chunk_id=item.chunk_id,
        chunk_digest=fingerprint(item.chunk_text), source_unit_id=unit,
        relation=relation, source_checked_by="claimed-operator",
        relation_checked_by="claimed-reviewer",
        reviewed_at=DATE, rationale="Researcher-declared test relationship.",
    )


@pytest.mark.parametrize(
    ("text", "asserted_relation", "disposition", "possible"),
    [
        (YES, Relation.SUPPORTS, "asserted_support_needs_external_check", True),
        (NO, Relation.OPPOSES, "asserted_opposition_not_auto_contradiction", False),
        (NO, Relation.TOPICAL, "topic_relevance_only", False),
        (YES, Relation.UNDETERMINED, "relation_undetermined", False),
        (YES, Relation.NOT_TESTABLE, "relation_not_testable", False),
    ],
)
def test_relation_is_explicit_not_from_similarity(
    text: str, asserted_relation: Relation, disposition: str, possible: bool,
) -> None:
    item = hit(text, similarity=0.99)
    result = preflight_hit(item, reviewed(item, asserted_relation))
    assert result.relation is asserted_relation
    assert result.disposition == disposition
    assert result.possible_support_for_external_review is possible
    assert result.gate_authorized is False


def test_unreviewed_source_does_not_become_support_even_with_high_similarity() -> None:
    item = hit(YES, similarity=1.0)
    result = preflight_hit(item, None)
    assert result.disposition == "relation_review_missing"
    assert result.possible_support_for_external_review is False
    assert result.gate_authorized is False


def test_metadata_verified_is_not_relation_verified() -> None:
    item = hit(NO)
    result = preflight_hit(item, None)
    assert result.possible_support_for_external_review is False
    assert result.relation is None


def test_unverified_llm_proposal_remains_unverified_despite_claimed_review() -> None:
    item = hit(YES, status="proposed")
    result = preflight_hit(item, reviewed(item, Relation.SUPPORTS))
    assert result.disposition == "source_not_verified"
    assert not result.possible_support_for_external_review


@pytest.mark.parametrize(
    "change", [
        {"seed_digest": fingerprint("A different seed")},
        {"chunk_digest": fingerprint("Document was revised")},
        {"chunk_id": "source::chunk_changed"},
        {"doc_id": "different_document"},
        {"seed_id": "other_seed"},
    ],
)
def test_wrong_or_stale_attestation_is_rejected(change: dict[str, str]) -> None:
    item = hit(YES)
    claimed = replace(reviewed(item, Relation.SUPPORTS), **change)
    result = preflight_hit(item, claimed)
    assert result.disposition == "stale_or_wrong_identity"
    assert result.relation is None
    assert not result.possible_support_for_external_review


def test_duplicate_chunks_share_one_provisional_source_unit() -> None:
    a = hit(YES, chunk="doc::a")
    b = hit(YES, chunk="doc::b")
    batch = preflight_batch(
        [a, b],
        {
            (a.seed_id, a.chunk_id): reviewed(a, Relation.SUPPORTS, unit="one-study"),
            (b.seed_id, b.chunk_id): reviewed(b, Relation.SUPPORTS, unit="one-study"),
        },
    )
    assert batch.support_units_to_review == (("seed-1", "one-study"),)
    assert len(batch.observations) == 2
    assert batch.gate_authorized is False
    assert all(not obs.gate_authorized for obs in batch.observations)


def test_explicitly_conflicting_relations_quarantine_entire_unit() -> None:
    a = hit(YES, chunk="doc::a")
    b = hit(NO, chunk="doc::b")
    batch = preflight_batch(
        [a, b],
        {
            (a.seed_id, a.chunk_id): reviewed(a, Relation.SUPPORTS, unit="same-study"),
            (b.seed_id, b.chunk_id): reviewed(b, Relation.OPPOSES, unit="same-study"),
        },
    )
    assert batch.conflicting_source_units == (("seed-1", "same-study"),)
    assert batch.support_units_to_review == ()
    assert all(obs.disposition == "conflicting_relation_same_source"
               for obs in batch.observations)


def test_missing_review_does_not_disappear_from_observation_ledger() -> None:
    a = hit(YES, chunk="doc::a")
    b = hit(NO, chunk="doc::b")
    result = preflight_batch(
        [a, b], {(a.seed_id, a.chunk_id): reviewed(a, Relation.SUPPORTS)}
    )
    assert len(result.observations) == 2
    assert result.observations[1].disposition == "relation_review_missing"


@pytest.mark.parametrize("timestamp", ["2026-10-25", "yesterday", "2026-10-25T09:00:00"])
def test_naive_or_invalid_review_timestamp_fails(timestamp: str) -> None:
    item = hit(YES)
    with pytest.raises(ValueError, match="reviewed_at"):
        replace(reviewed(item, Relation.SUPPORTS), reviewed_at=timestamp)


@pytest.mark.parametrize("field", ["seed_digest", "chunk_digest"])
def test_invalid_version_digest_fails(field: str) -> None:
    item = hit(YES)
    with pytest.raises(ValueError, match=field):
        replace(reviewed(item, Relation.SUPPORTS), **{field: "not-a-digest"})


def test_invalid_similarity_is_rejected() -> None:
    with pytest.raises(ValueError, match="similarity"):
        hit(YES, similarity=float("nan"))


def test_not_a_semantic_entailment_classifier() -> None:
    item = hit(NO)
    result = preflight_hit(item, reviewed(item, Relation.SUPPORTS))
    # The function intentionally cannot detect a dishonest label. It is a
    # *review handoff* that requires a real, independent attestation process.
    assert result.disposition == "asserted_support_needs_external_check"
    assert result.gate_authorized is False


def test_same_underlying_source_can_have_opposing_relations_to_different_seeds() -> None:
    first = hit(YES, seed_id="seed-1")
    second = hit(NO, seed_id="seed-2")
    batch = preflight_batch(
        [first, second],
        {
            (first.seed_id, first.chunk_id): reviewed(first, Relation.SUPPORTS, unit="one-source"),
            (second.seed_id, second.chunk_id): reviewed(second, Relation.OPPOSES, unit="one-source"),
        },
    )
    assert batch.conflicting_source_units == ()
    assert batch.support_units_to_review == (("seed-1", "one-source"),)
    assert batch.observations[1].disposition == "asserted_opposition_not_auto_contradiction"
