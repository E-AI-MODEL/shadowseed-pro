"""Tests for the contradiction lifecycle and Gate-controlled recovery (#13)."""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed.gate.contradictions import ContradictionRecord, ContradictionStatus
from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)
from shadowseed.manager import SSLManager, SeedStatus


def fake_embedding(text: str) -> np.ndarray:
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vector = rng.standard_normal(16)
    return vector / np.linalg.norm(vector)


def _contradiction(reason: str = "counterexample") -> ValidationSignal:
    return ValidationSignal(
        kind=SignalKind.CONTRADICTION,
        direction=SignalDirection.OPPOSE,
        reason=reason,
        source_ref="reviewer_a",
    )


def _promote(manager: SSLManager, seed_id: str) -> None:
    manager.seeds[seed_id].occurrence_count = 5
    for _ in range(3):
        manager.submit_signals(seed_id, [recurrence_signal(5, threshold=2)], "exploratory")


# -- record model ------------------------------------------------------------


def test_record_resolution_requires_non_empty_basis():
    record = ContradictionRecord(contradiction_id="c1", seed_id="s1")
    with pytest.raises(ValueError):
        record.resolve("   ")
    record.resolve("new evidence overturns the objection")
    assert record.lifecycle_state is ContradictionStatus.RESOLVED
    assert record.is_blocking is False


def test_record_roundtrip():
    record = ContradictionRecord(
        contradiction_id="c1", seed_id="s1", reason="r", strength=0.5
    )
    assert ContradictionRecord.from_dict(record.to_dict()) == record


@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({}, ContradictionStatus.RESOLVED),
        ({"superseded": True}, ContradictionStatus.SUPERSEDED),
        ({"withdrawn": True}, ContradictionStatus.WITHDRAWN),
    ],
)
def test_terminal_states(kwargs, expected):
    record = ContradictionRecord(contradiction_id="c1", seed_id="s1")
    record.resolve("basis", **kwargs)
    assert record.lifecycle_state is expected


# -- manager integration -----------------------------------------------------


def test_contradiction_creates_open_record_and_blocks():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a contradicted seed")
    _promote(manager, seed_id)
    manager.submit_signals(seed_id, [_contradiction()], "exploratory")
    open_records = manager.open_contradictions(seed_id)
    assert len(open_records) == 1
    assert manager._contradiction_state(manager.seeds[seed_id]).blocking is True


def test_recurrence_alone_cannot_lift_a_contradiction():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a stubborn seed")
    _promote(manager, seed_id)
    manager.submit_signals(seed_id, [_contradiction()], "exploratory")
    # Hammering recurrence must stay blocked while the contradiction is open.
    for _ in range(5):
        event = manager.submit_signals(
            seed_id, [recurrence_signal(9, threshold=2)], "exploratory"
        )
        assert event.decision is GateDecision.BLOCKED
    assert manager.open_contradictions(seed_id)


def test_recovery_requires_resolution_then_revalidation():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a recoverable seed")
    _promote(manager, seed_id)
    manager.submit_signals(seed_id, [_contradiction()], "exploratory")

    # Resolution needs a basis and only unblocks; it does not restore authority.
    with pytest.raises(ValueError):
        manager.resolve_contradiction(seed_id, basis="")
    event = manager.resolve_contradiction(
        seed_id, basis="independent replication overturned the objection"
    )
    assert event.decision is GateDecision.CONTRADICTION_RESOLVED
    assert manager.open_contradictions(seed_id) == []
    assert manager.seeds[seed_id].contradiction_score == 0.0

    # Now revalidation under the policy can promote again.
    manager.seeds[seed_id].occurrence_count = 5
    for _ in range(3):
        manager.submit_signals(seed_id, [recurrence_signal(5, threshold=2)], "exploratory")
    assert manager.seeds[seed_id].status is SeedStatus.PROMOTED


def test_resolved_record_is_retained_for_audit():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("an audited seed")
    _promote(manager, seed_id)
    manager.submit_signals(seed_id, [_contradiction("bad")], "exploratory")
    manager.resolve_contradiction(seed_id, basis="fixed", superseded=True)
    records = manager.contradictions_for(seed_id)
    assert len(records) == 1
    assert records[0].lifecycle_state is ContradictionStatus.SUPERSEDED
    assert records[0].resolution_basis == "fixed"


def test_resolve_without_open_contradiction_raises():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("an uncontradicted seed")
    with pytest.raises(ValueError):
        manager.resolve_contradiction(seed_id, basis="nothing to resolve")


def test_expired_seed_cannot_recover_via_resolution():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a seed that expires")
    _promote(manager, seed_id)
    manager.submit_signals(seed_id, [_contradiction()], "exploratory")
    manager.seeds[seed_id].unsafe_set_authority(status=SeedStatus.EXPIRED)
    with pytest.raises(ValueError):
        manager.resolve_contradiction(seed_id, basis="too late")


def test_migration_creates_records_for_legacy_scalar():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a legacy seed")
    manager.seeds[seed_id].unsafe_set_authority(contradiction_score=0.5)
    created = manager.migrate_legacy_contradictions()
    assert len(created) == 1
    assert created[0].source_ref == "legacy_migration"
    # Idempotent.
    assert manager.migrate_legacy_contradictions() == []


def test_legacy_scalar_without_records_is_treated_as_blocking():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a legacy blocked seed")
    manager.seeds[seed_id].unsafe_set_authority(contradiction_score=0.25)
    assert manager._contradiction_state(manager.seeds[seed_id]).blocking is True
