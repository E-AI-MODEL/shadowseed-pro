"""End-to-end SSL authority invariants (issue #17).

These tie the components together and assert the core invariants hold across the
manager, the Gate, contradiction records, and the point-of-use contract.
"""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed_agent import (
    AgentSafetyContract,
    InfluenceAction,
    assert_influence_records_valid,
)


def fake_embedding(text: str) -> np.ndarray:
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vector = rng.standard_normal(16)
    return vector / np.linalg.norm(vector)


def _manager() -> SSLManager:
    return SSLManager(embedding_fn=fake_embedding)


def _recur(manager, seed_id, policy="exploratory", n=3, count=5):
    manager.seeds[seed_id].occurrence_count = count
    for _ in range(n):
        manager.submit_signals(seed_id, [recurrence_signal(count, threshold=2)], policy)


# Invariant 1: detection never grants authority.
def test_detection_never_grants_authority():
    manager = _manager()
    ingest = manager.ingest_detection_candidates(["a novel atomic gap"])
    for accepted in ingest["accepted"]:
        seed = manager.seeds[accepted["seed_id"]]
        assert seed.weight == 0.0
        assert seed.status is SeedStatus.NEW


# Invariant 2: observations outside the Gate do not change authority.
def test_observations_do_not_change_authority():
    manager = _manager()
    seed_id = manager.add_or_update_seed("an observed gap")
    version = manager.seeds[seed_id].authority_version
    manager.seeds[seed_id].occurrence_count = 9  # observation
    manager.seeds[seed_id].trace = 3.0            # observation
    manager.decay_traces(turns_passed=1)          # lifecycle/observation
    assert manager.seeds[seed_id].weight == 0.0
    assert manager.seeds[seed_id].authority_version == version


# Invariant 4: every Gate authority change references typed signals and a policy.
def test_every_gate_event_has_policy_and_signals():
    manager = _manager()
    seed_id = manager.add_or_update_seed("a recurring gap")
    _recur(manager, seed_id)
    changing = [e for e in manager.gate_events if e.changed_authority]
    assert changing, "expected at least one authority-changing event"
    for event in changing:
        assert event.policy_id
        assert event.signals  # typed inputs recorded


# Invariant 7: recurrence is never relabeled or double-counted as evidence.
def test_recurrence_promotes_without_becoming_evidence():
    manager = _manager()
    seed_id = manager.add_or_update_seed("recurring but unverified")
    _recur(manager, seed_id)
    seed = manager.seeds[seed_id]
    assert seed.status is SeedStatus.PROMOTED
    assert seed.evidence_count == 0


# Invariant 8: SSOT is optional — exploratory promotes without any external evidence.
def test_ssot_is_optional_under_exploratory_policy():
    manager = _manager()
    seed_id = manager.add_or_update_seed("no external support needed")
    _recur(manager, seed_id)
    assert manager.seeds[seed_id].status is SeedStatus.PROMOTED
    # But the evidence-backed policy would refuse the same recurrence.
    other = manager.add_or_update_seed("evidence hungry")
    manager.seeds[other].occurrence_count = 9
    event = manager.submit_signals(other, [recurrence_signal(9, threshold=2)], "evidence_backed")
    assert event.decision is GateDecision.BLOCKED


# Invariant 6 + 5: contradiction blocks influence, recovery needs resolution +
# revalidation, and every allowed influence replays cleanly.
def test_contradiction_block_recovery_and_point_of_use_replay():
    manager = _manager()
    contract = AgentSafetyContract()
    seed_id = manager.add_or_update_seed("a claim under test")
    _recur(manager, seed_id)
    assert manager.seeds[seed_id].status is SeedStatus.PROMOTED

    ledger: list = []

    def decide():
        return contract.decide_and_record(
            manager.seeds[seed_id], InfluenceAction.ANSWER_MODIFICATION,
            gate_events=manager.gate_events, ledger=ledger,
            contradiction_blocking=manager.is_blocking_contradiction(seed_id),
        )

    assert decide().allowed is True

    # Contradict: influence is blocked.
    manager.submit_signals(
        seed_id,
        [ValidationSignal(kind=SignalKind.CONTRADICTION, direction=SignalDirection.OPPOSE)],
        "exploratory",
    )
    assert decide().allowed is False
    assert manager.is_blocking_contradiction(seed_id) is True

    # Resolve with a basis, then revalidate — only then may it influence again.
    manager.resolve_contradiction(seed_id, basis="independent replication")
    assert decide().allowed is False  # resolved but not yet re-promoted
    _recur(manager, seed_id)
    assert decide().allowed is True

    # All allowed records replay cleanly against the Gate ledger.
    assert_influence_records_valid(ledger, manager.gate_events)


# Invariant 3 (spot check): expired seeds cannot regain authority.
def test_expired_seed_is_terminal():
    manager = _manager()
    seed_id = manager.add_or_update_seed("a seed that will expire")
    _recur(manager, seed_id)
    manager.seeds[seed_id].unsafe_set_authority(status=SeedStatus.EXPIRED, weight=0.0)
    event = manager.submit_signals(seed_id, [recurrence_signal(9, threshold=2)], "exploratory")
    assert event.decision is GateDecision.EXPIRED
    assert manager.seeds[seed_id].weight == 0.0


# Serialization round-trip preserves the full authority model.
def test_manager_export_includes_gate_events_and_contradictions():
    manager = _manager()
    seed_id = manager.add_or_update_seed("exported seed")
    _recur(manager, seed_id)
    manager.submit_signals(
        seed_id,
        [ValidationSignal(kind=SignalKind.CONTRADICTION, direction=SignalDirection.OPPOSE)],
        "exploratory",
    )
    data = manager.to_dict()
    assert data["gate_events"], "gate events must be exported"
    assert data["contradiction_records"], "contradiction records must be exported"
