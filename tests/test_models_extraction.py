"""Regression tests for extracting manager data contracts into models.py."""

from __future__ import annotations

from dataclasses import fields

import numpy as np

import shadowseed
from shadowseed import manager, models


MODEL_NAMES = (
    "CandidateType",
    "Constellation",
    "ProbeFeedbackResult",
    "ProbeOutcome",
    "ProbeType",
    "SeedEvent",
    "SeedOrigin",
    "SeedStatus",
    "ShadowSeed",
    "ValidationGateFlags",
    "ValidationGateResult",
)


def _embedding(_text: str) -> np.ndarray:
    return np.array([1.0, 0.0, 0.0])


def test_manager_reexports_the_canonical_model_objects():
    for name in MODEL_NAMES:
        assert getattr(manager, name) is getattr(models, name)

    assert manager.AUTHORITY_FIELDS is models.AUTHORITY_FIELDS
    assert manager.validate_seed_snapshot is models.validate_seed_snapshot
    assert manager.WEIGHT_MIN == models.WEIGHT_MIN
    assert manager.WEIGHT_MAX == models.WEIGHT_MAX


def test_package_exports_still_resolve_to_the_same_objects():
    assert shadowseed.ShadowSeed is models.ShadowSeed
    assert shadowseed.SeedStatus is models.SeedStatus
    assert shadowseed.SeedOrigin is models.SeedOrigin
    assert shadowseed.CandidateType is models.CandidateType
    assert shadowseed.Constellation is models.Constellation
    assert shadowseed.SSLManager is manager.SSLManager


def test_models_own_the_extracted_class_definitions():
    for name in MODEL_NAMES:
        assert getattr(models, name).__module__ == "shadowseed.models"


def test_shadow_seed_field_order_and_serialization_contract_are_preserved():
    expected_fields = [
        "id",
        "text",
        "embedding",
        "trigger_keywords",
        "trace",
        "occurrence_count",
        "turns_dormant",
        "created_at",
        "updated_at",
        "origin",
        "weight",
        "evidence_count",
        "contradiction_score",
        "status",
        "authority_version",
        "_authority_sealed",
    ]
    assert [item.name for item in fields(models.ShadowSeed)] == expected_fields

    seed = models.ShadowSeed(
        id="ss_001",
        text="an atomic seed",
        embedding=np.array([0.25, 0.75]),
        trigger_keywords=["atomic"],
        trace=1.5,
        occurrence_count=3,
        turns_dormant=2,
        created_at="2026-01-01T00:00:00",
        updated_at="2026-01-02T00:00:00",
        origin=models.SeedOrigin(
            candidate_type=models.CandidateType.MISSING_RELATION,
            detection_basis="test basis",
            context_ref="test-context",
        ),
    )
    seed.unsafe_set_authority(
        weight=0.6,
        status=models.SeedStatus.PROMOTED,
        evidence_count=2,
        contradiction_score=0.1,
    )

    snapshot = seed.to_dict()
    restored = models.ShadowSeed.from_dict(snapshot)

    assert restored.to_dict() == snapshot
    assert list(snapshot) == [
        "id",
        "text",
        "embedding",
        "trigger_keywords",
        "trace",
        "occurrence_count",
        "turns_dormant",
        "created_at",
        "updated_at",
        "origin",
        "weight",
        "evidence_count",
        "contradiction_score",
        "status",
        "authority_version",
    ]


def test_manager_creates_and_restores_the_canonical_shadow_seed_type():
    ssl_manager = manager.SSLManager(embedding_fn=_embedding)
    seed_id = ssl_manager.add_or_update_seed("an atomic seed", deduplicate=False)
    created = ssl_manager.get_seed(seed_id)

    assert type(created) is models.ShadowSeed

    restored_manager = manager.SSLManager(embedding_fn=_embedding)
    restored = restored_manager.restore_seed(created.to_dict())
    assert type(restored) is models.ShadowSeed
    assert restored.to_dict() == created.to_dict()


def test_enum_values_and_result_defaults_remain_stable():
    assert [status.value for status in models.SeedStatus] == [
        "NEW",
        "ACTIVE",
        "DECAYING",
        "DORMANT",
        "PROMOTED",
        "EXPIRED",
    ]
    assert [outcome.value for outcome in models.ProbeOutcome] == [
        "reward",
        "penalty",
        "neutral",
    ]
    assert [probe.value for probe in models.ProbeType] == [
        "follow_up",
        "retrieval",
        "dialectic",
        "general",
    ]


def test_manager_wildcard_import_surface_remains_backward_compatible():
    namespace: dict[str, object] = {}
    exec("from shadowseed.manager import *", namespace)

    assert namespace["GateDecision"] is manager.GateDecision
    assert namespace["ValidationSignal"] is manager.ValidationSignal
    assert namespace["ContradictionRecord"] is manager.ContradictionRecord
    assert namespace["DEFAULT_CONFIG"] is manager.DEFAULT_CONFIG

