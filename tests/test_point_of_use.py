"""Tests for atomic, replayable point-of-use decisions (issue #14)."""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed.gate.signals import recurrence_signal
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed_agent import (
    AgentInfluenceRecord,
    AgentSafetyContract,
    InfluenceAction,
    InfluenceReplayError,
    assert_influence_records_valid,
)


def fake_embedding(text: str) -> np.ndarray:
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vector = rng.standard_normal(16)
    return vector / np.linalg.norm(vector)


def _promoted_manager() -> tuple[SSLManager, str]:
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a promotable seed")
    manager.seeds[seed_id].occurrence_count = 5
    for _ in range(3):
        manager.submit_signals(seed_id, [recurrence_signal(5, threshold=2)], "exploratory")
    assert manager.seeds[seed_id].status is SeedStatus.PROMOTED
    return manager, seed_id


def test_decide_and_record_is_atomic():
    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract()
    ledger: list = []
    record = contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
        context_ref="turn:3",
    )
    # The decision was recorded as part of the same call.
    assert ledger == [record]
    assert record.allowed is True


def test_allowed_decision_links_to_a_gate_event():
    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract()
    ledger: list = []
    record = contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
    )
    assert record.gate_event_ref is not None
    referenced = [e for e in manager.gate_events if e.event_id == record.gate_event_ref]
    assert referenced and referenced[0].seed_id == seed_id
    assert referenced[0].status_after == "PROMOTED"
    assert record.authority_version == manager.seeds[seed_id].authority_version


def test_denied_decision_is_also_recorded():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("an unpromoted seed")
    contract = AgentSafetyContract()
    ledger: list = []
    record = contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
    )
    assert record.allowed is False
    assert ledger == [record]
    assert record.gate_event_ref is None


def test_strict_replay_passes_for_valid_records():
    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract()
    ledger: list = []
    contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
    )
    assert_influence_records_valid(ledger, manager.gate_events)


def test_strict_replay_rejects_weightless_allowed():
    bad = [
        AgentInfluenceRecord(
            seed_id="ss_001", action="answer_modification", seed_weight=0.0,
            seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
        )
    ]
    with pytest.raises(Exception):
        assert_influence_records_valid(bad, [])


def test_strict_replay_rejects_missing_gate_event_link():
    bad = [
        AgentInfluenceRecord(
            seed_id="ss_001", action="answer_modification", seed_weight=0.6,
            seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref=None,
        )
    ]
    with pytest.raises(InfluenceReplayError):
        assert_influence_records_valid(bad, [])


def test_strict_replay_rejects_unknown_gate_event_ref():
    bad = [
        AgentInfluenceRecord(
            seed_id="ss_001", action="answer_modification", seed_weight=0.6,
            seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="nope",
        )
    ]
    with pytest.raises(InfluenceReplayError):
        assert_influence_records_valid(bad, [])


def test_strict_replay_rejects_contradicted_allowed():
    bad = [
        AgentInfluenceRecord(
            seed_id="ss_001", action="answer_modification", seed_weight=0.6,
            seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
            contradiction_blocking=True,
        )
    ]
    with pytest.raises(InfluenceReplayError):
        assert_influence_records_valid(bad, [])
