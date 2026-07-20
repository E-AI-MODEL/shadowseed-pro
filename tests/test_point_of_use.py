"""Tests for atomic, replayable point-of-use decisions (issue #14)."""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.gate.signals import recurrence_signal
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed_agent import (
    AgentInfluenceRecord,
    AgentSafetyContract,
    InfluenceAction,
    InfluenceReplayError,
    assert_influence_records_valid,
    can_seed_trigger_retrieval,
)


def _promotion_event(seed_id: str, version: int, *, event_id: str = "e1", policy_id: str = "exploratory") -> GateEvent:
    return GateEvent(
        event_id=event_id,
        seed_id=seed_id,
        policy_id=policy_id,
        decision=GateDecision.PROMOTED,
        status_after="PROMOTED",
        authority_version=version,
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
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
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
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
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
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
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
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
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
            authority_version=1, policy_id="exploratory",
        )
    ]
    with pytest.raises(InfluenceReplayError, match="unknown Gate event"):
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


def test_strict_replay_rejects_missing_authority_version():
    bad = [
        AgentInfluenceRecord(
            seed_id="ss_001", action="answer_modification", seed_weight=0.6,
            seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
            authority_version=None,
        )
    ]
    with pytest.raises(InfluenceReplayError):
        assert_influence_records_valid(bad, [])


def test_strict_replay_rejects_stale_authority_version():
    record = AgentInfluenceRecord(
        seed_id="ss_001", action="answer_modification", seed_weight=0.6,
        seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
        authority_version=5, policy_id="exploratory",
    )
    event = _promotion_event("ss_001", version=3)  # record says 5, event says 3
    with pytest.raises(InfluenceReplayError, match="stale authority version"):
        assert_influence_records_valid([record], [event])


def test_strict_replay_rejects_foreign_seed_event():
    record = AgentInfluenceRecord(
        seed_id="ss_001", action="answer_modification", seed_weight=0.6,
        seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
        authority_version=1, policy_id="exploratory",
    )
    event = _promotion_event("ss_999", version=1)  # different seed
    with pytest.raises(InfluenceReplayError, match="different seed"):
        assert_influence_records_valid([record], [event])


def test_strict_replay_rejects_non_promoting_event():
    record = AgentInfluenceRecord(
        seed_id="ss_001", action="answer_modification", seed_weight=0.6,
        seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
        authority_version=1, policy_id="exploratory",
    )
    # A confirming decision (validated) that nonetheless did not leave the seed
    # promoted must be rejected by the status_after check.
    event = GateEvent(
        event_id="e1", seed_id="ss_001", policy_id="exploratory",
        decision=GateDecision.VALIDATED, status_after="ACTIVE", authority_version=1,
    )
    with pytest.raises(InfluenceReplayError, match="did not leave"):
        assert_influence_records_valid([record], [event])


def test_strict_replay_rejects_blocked_event_as_authorization():
    # A later BLOCKED event that still shows status_after=PROMOTED and the same
    # version must not count as the authorizing event.
    record = AgentInfluenceRecord(
        seed_id="ss_001", action="answer_modification", seed_weight=0.6,
        seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
        authority_version=3, policy_id="exploratory",
    )
    blocked_event = GateEvent(
        event_id="e1", seed_id="ss_001", policy_id="exploratory",
        decision=GateDecision.BLOCKED, status_after="PROMOTED", authority_version=3,
    )
    with pytest.raises(InfluenceReplayError, match="authority-confirming"):
        assert_influence_records_valid([record], [blocked_event])


def test_link_gate_event_ignores_blocked_event_at_decision_time():
    manager, seed_id = _promoted_manager()
    # A later BLOCKED submission leaves the promoted seed unchanged.
    manager.submit_signals(seed_id, [], "exploratory")  # no signals -> BLOCKED, no change
    contract = AgentSafetyContract()
    ledger: list = []
    record = contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )
    # It must still link to the promoting event, not the blocked one.
    assert record.allowed is True
    linked = [e for e in manager.gate_events if e.event_id == record.gate_event_ref]
    assert linked and linked[0].decision is GateDecision.PROMOTED
    assert_influence_records_valid(ledger, manager.gate_events)


def test_strict_replay_requires_policy_id_for_allowed():
    record = AgentInfluenceRecord(
        seed_id="ss_001", action="answer_modification", seed_weight=0.6,
        seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
        authority_version=1, policy_id=None,
    )
    event = _promotion_event("ss_001", version=1)
    with pytest.raises(InfluenceReplayError, match="no policy id"):
        assert_influence_records_valid([record], [event])


def test_influence_record_json_roundtrip_replays():
    import json
    from dataclasses import asdict

    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract()
    ledger: list = []
    contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
        now="2026-07-20T00:00:00",
    )
    payload = json.loads(json.dumps(asdict(ledger[0])))
    restored = AgentInfluenceRecord(**payload)
    assert restored == ledger[0]
    # And the deserialized record still replays cleanly against the ledger.
    events = [GateEvent.from_dict(json.loads(json.dumps(e.to_dict()))) for e in manager.gate_events]
    assert_influence_records_valid([restored], events)


def test_strict_replay_rejects_policy_mismatch():
    record = AgentInfluenceRecord(
        seed_id="ss_001", action="answer_modification", seed_weight=0.6,
        seed_status="PROMOTED", allowed=True, reason="x", gate_event_ref="e1",
        authority_version=1, policy_id="evidence_backed",
    )
    event = _promotion_event("ss_001", version=1, policy_id="exploratory")
    with pytest.raises(InfluenceReplayError, match="policy mismatch"):
        assert_influence_records_valid([record], [event])


def test_decide_time_stale_authorization_is_denied():
    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract()
    ledger: list = []
    # Only a stale promotion event exists (version does not match current).
    stale_events = [_promotion_event(seed_id, version=manager.seeds[seed_id].authority_version - 1)]
    record = contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=stale_events,
        ledger=ledger,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )
    assert record.allowed is False
    assert record.reason == "stale_gate_authorization"


def test_no_public_nonrecording_allow_decision():
    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract()
    # The former public allow-returning APIs are gone: there is no public
    # method that returns an allowed verdict without recording.
    assert not hasattr(contract, "decide")
    assert not hasattr(contract, "can_influence")
    # inspect() exists for status/UX only and is documented as non-authorizing;
    # it returns an InfluenceDecision but records nothing to any ledger.
    decision = contract.inspect(
        manager.seeds[seed_id],
        InfluenceAction.RETRIEVAL,
        manager.gate_events,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )
    assert decision.allowed is True


def test_retrieval_helper_records_and_replays():
    manager, seed_id = _promoted_manager()
    ledger: list = []
    allowed = can_seed_trigger_retrieval(
        manager.seeds[seed_id],
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )
    assert allowed is True
    assert len(ledger) == 1 and ledger[0].action == "retrieval"
    assert_influence_records_valid(ledger, manager.gate_events)


def test_contradiction_blocking_uses_canonical_state():
    manager, seed_id = _promoted_manager()
    # Open a contradiction via the Gate; canonical blocking becomes True.
    from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal

    manager.submit_signals(
        seed_id,
        [ValidationSignal(kind=SignalKind.CONTRADICTION, direction=SignalDirection.OPPOSE)],
        "exploratory",
    )
    contract = AgentSafetyContract()
    ledger: list = []
    record = contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
    )
    assert record.allowed is False


def test_influence_record_is_serializable():
    from dataclasses import asdict

    manager, seed_id = _promoted_manager()
    contract = AgentSafetyContract()
    ledger: list = []
    contract.decide_and_record(
        manager.seeds[seed_id],
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=manager.is_blocking_contradiction(seed_id),
        now="2026-07-20T00:00:00",
    )
    data = asdict(ledger[0])
    assert data["gate_event_ref"] is not None
    assert data["authority_version"] == manager.seeds[seed_id].authority_version
    assert data["decided_at"] == "2026-07-20T00:00:00"
