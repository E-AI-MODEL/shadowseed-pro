"""Regression tests for the contradiction-domain extraction."""

from __future__ import annotations

import numpy as np
import pytest

import shadowseed.contradictions as contradiction_module
from shadowseed import manager as manager_module
from shadowseed.gate.contradictions import ContradictionRecord, ContradictionStatus
from shadowseed.gate.events import ContradictionState
from shadowseed.manager import SSLManager
from shadowseed.models import ShadowSeed


def _embedding(_text: str) -> np.ndarray:
    return np.array([1.0, 0.0, 0.0])


def test_new_module_reexports_the_canonical_record_contract() -> None:
    assert contradiction_module.ContradictionRecord is ContradictionRecord
    assert contradiction_module.ContradictionStatus is ContradictionStatus
    assert manager_module.ContradictionRecord is ContradictionRecord
    assert manager_module.ContradictionStatus is ContradictionStatus


def test_manager_blocking_query_preserves_the_state_facade() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("a seed")
    manager._open_contradiction_record(
        manager.seeds[seed_id],
        reason="counterexample",
        source_ref=None,
        strength=1.0,
    )
    manager._contradiction_state = lambda _seed: ContradictionState(
        blocking=False,
        open_count=0,
        score=0.0,
    )

    assert manager.is_blocking_contradiction(seed_id) is False


def test_manager_resolution_preserves_the_open_query_facade() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("a seed")
    record = manager._open_contradiction_record(
        manager.seeds[seed_id],
        reason="counterexample",
        source_ref=None,
        strength=1.0,
    )
    manager.open_contradictions = lambda _seed_id: []

    with pytest.raises(
        ValueError,
        match=f"no open contradiction to resolve for seed '{seed_id}'",
    ):
        manager.resolve_contradiction(seed_id, basis="independent replication")

    assert record.lifecycle_state is ContradictionStatus.OPEN


def test_legacy_migration_preserves_the_open_record_facade() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("a seed")
    manager.seeds[seed_id].unsafe_set_authority(contradiction_score=0.5)

    opened: list[str] = []
    original_open = manager._open_contradiction_record

    def tracked_open(
        seed: ShadowSeed,
        *,
        reason: str,
        source_ref: str | None,
        strength: float,
    ) -> ContradictionRecord:
        opened.append(seed.id)
        return original_open(
            seed,
            reason=reason,
            source_ref=source_ref,
            strength=strength,
        )

    manager._open_contradiction_record = tracked_open
    created = manager.migrate_legacy_contradictions()

    assert opened == [seed_id]
    assert created == manager.open_contradictions(seed_id)


def test_manager_facade_uses_one_canonical_record_collection() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("a seed")
    record = manager._open_contradiction_record(
        manager.seeds[seed_id],
        reason="counterexample",
        source_ref="reviewer-a",
        strength=0.5,
    )

    assert manager.contradiction_records is manager._contradictions.records
    assert manager.open_contradictions(seed_id) == [record]
    assert manager.contradictions_for(seed_id) == [record]
    assert manager.is_blocking_contradiction(seed_id) is True

    event = manager.resolve_contradiction(seed_id, basis="independent replication")
    assert event.decision.value == "contradiction_resolved"
    assert manager.open_contradictions(seed_id) == []
    assert record.lifecycle_state is ContradictionStatus.RESOLVED


def test_assigning_legacy_manager_record_list_restores_domain_sequence() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("a seed")
    restored = ContradictionRecord(
        contradiction_id=f"contra::{seed_id}::000004",
        seed_id=seed_id,
        reason="restored",
    )

    manager.contradiction_records = [restored]
    created = manager._open_contradiction_record(
        manager.seeds[seed_id],
        reason="new",
        source_ref=None,
        strength=1.0,
    )

    assert manager.contradiction_records[0] is restored
    assert created.contradiction_id.endswith("000005")
    assert manager._contradiction_sequence == 5


def test_manager_export_keeps_exact_contradiction_record_shape() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("a seed")
    record = manager._open_contradiction_record(
        manager.seeds[seed_id],
        reason="counterexample",
        source_ref="source-1",
        strength=0.4,
    )

    assert manager.to_dict()["contradiction_records"] == [record.to_dict()]
    assert list(record.to_dict()) == [
        "contradiction_id",
        "seed_id",
        "reason",
        "source_ref",
        "strength",
        "status",
        "created_at",
        "resolved_at",
        "resolution_basis",
    ]


def test_manager_wildcard_import_compatibility_is_preserved() -> None:
    namespace: dict[str, object] = {}
    exec("from shadowseed.manager import *", namespace)

    assert namespace["ContradictionRecord"] is ContradictionRecord
    assert namespace["ContradictionStatus"] is ContradictionStatus
    assert namespace["GateDecision"] is manager_module.GateDecision
    assert "ContradictionDomain" not in namespace
