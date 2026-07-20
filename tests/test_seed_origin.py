"""Tests for optional seed-origin observability metadata.

Origin metadata records *why* a candidate absence was proposed. It is purely
descriptive: it must never increase weight, count as evidence, or influence the
Validation Gate. The lifecycle is unchanged; these tests pin that boundary and
the serialization contract.
"""

import json

import numpy as np

from shadowseed.manager import (
    CandidateType,
    SeedOrigin,
    SeedStatus,
    SSLManager,
)

SEED_TEXT = "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."


def fake_embedding(text: str) -> np.ndarray:
    if "Koloniaal kapitaal" in text:
        return np.array([1.0, 0.0, 0.0])
    if "Koloniale katoen" in text:
        return np.array([0.96, -0.28, 0.0])
    return np.array([0.0, 1.0, 0.0])


def _convincing_origin() -> SeedOrigin:
    return SeedOrigin(
        candidate_type=CandidateType.MISSING_DEPENDENCY,
        detection_basis="strong recurring pattern; high detector confidence",
        context_ref="doc:42#p3",
    )


def test_seed_origin_defaults_and_serialization() -> None:
    origin = SeedOrigin()
    assert origin.candidate_type == CandidateType.UNSPECIFIED
    assert origin.to_dict() == {
        "candidate_type": "unspecified",
        "detection_basis": "",
        "context_ref": None,
    }


def test_convincing_origin_must_leave_weight_at_zero() -> None:
    """The load-bearing safety property: a convincing rationale is not evidence."""
    manager = SSLManager(embedding_fn=fake_embedding, promotion_threshold=0.4)
    seed_id = manager.add_or_update_seed(SEED_TEXT, origin=_convincing_origin())
    seed = manager.seeds[seed_id]

    # Origin is recorded but grants no influence.
    assert seed.origin is not None
    assert seed.weight == 0.0
    assert seed.evidence_count == 0
    assert seed.status == SeedStatus.NEW

    # Even with ample internal recurrence, without real external evidence the
    # gate must not promote: the rationale cannot substitute for evidence.
    seed.occurrence_count = 3
    promoted = manager.run_validation_gate(seed_id)
    assert promoted is not True
    assert seed.weight == 0.0
    assert seed.status != SeedStatus.PROMOTED


def test_origin_serializes_and_is_json_safe() -> None:
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(SEED_TEXT, origin=_convincing_origin())

    data = manager.seeds[seed_id].to_dict()
    assert data["origin"] == {
        "candidate_type": "missing_dependency",
        "detection_basis": "strong recurring pattern; high detector confidence",
        "context_ref": "doc:42#p3",
    }
    # Must round-trip through JSON without a custom encoder.
    json.dumps(data)


def test_seed_without_origin_serializes_none() -> None:
    """Backward compatibility: origin is optional and its absence is tolerated."""
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(SEED_TEXT)
    seed = manager.seeds[seed_id]

    assert seed.origin is None
    assert seed.to_dict()["origin"] is None
    json.dumps(seed.to_dict())


def test_created_event_records_origin() -> None:
    manager = SSLManager(embedding_fn=fake_embedding)

    with_origin = manager.add_or_update_seed(
        SEED_TEXT,
        origin=SeedOrigin(candidate_type=CandidateType.UNSTATED_ASSUMPTION),
    )
    created = [
        e
        for e in manager.event_log
        if e.event_type == "created" and e.seed_id == with_origin
    ][-1]
    assert created.detail["origin"]["candidate_type"] == "unstated_assumption"

    without_origin = manager.add_or_update_seed("Ontbrekende rate-limiting op de publieke API.")
    created_none = [
        e
        for e in manager.event_log
        if e.event_type == "created" and e.seed_id == without_origin
    ][-1]
    assert created_none.detail["origin"] is None


def test_dedup_preserves_first_origin() -> None:
    """A near-duplicate re-detection reinforces the seed but keeps its origin."""
    manager = SSLManager(embedding_fn=fake_embedding)
    first_origin = SeedOrigin(
        candidate_type=CandidateType.MISSING_RELATION, detection_basis="first"
    )
    seed_id = manager.add_or_update_seed(SEED_TEXT, origin=first_origin)

    later_origin = SeedOrigin(
        candidate_type=CandidateType.CONTRADICTION, detection_basis="second"
    )
    same_id = manager.add_or_update_seed(SEED_TEXT, origin=later_origin)

    assert same_id == seed_id
    assert manager.seeds[seed_id].origin is first_origin


def test_reactivation_records_basis() -> None:
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Koloniale katoen als grondstof voor de Britse textielindustrie.",
        trigger_keywords=["katoen", "textiel"],
    )
    manager.seeds[seed_id].status = SeedStatus.DORMANT
    manager.seeds[seed_id].trace = 0.01

    reactivated = manager.reactivate_by_text("De katoenhandel voedde de textielindustrie.")
    assert reactivated == [seed_id]

    event = [e for e in manager.event_log if e.event_type == "reactivated"][-1]
    assert event.detail["basis"] == "keyword"
    assert "similarity" in event.detail
    assert event.detail["keyword_hit"] is True
