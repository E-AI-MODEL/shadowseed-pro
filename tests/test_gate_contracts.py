"""Tests for the Validation Gate contracts (issue #10).

These cover the data contracts only. They do not exercise the runtime manager,
which is migrated onto these contracts in later issues (#11, #12).
"""

from __future__ import annotations

import pytest

from shadowseed.gate import (
    ContradictionState,
    EvidenceBackedPolicy,
    ExploratoryPolicy,
    GateDecision,
    GateEvent,
    ProposedVerdict,
    SignalDirection,
    SignalKind,
    ValidationSignal,
    default_policy,
    resolve_policy,
)
from shadowseed.gate.events import new_event_id, summarize_signals
from shadowseed.gate.policies import (
    DEFAULT_POLICY_ID,
    EXAMPLE_POLICY_IDS,
    AuthoritySnapshot,
    available_policy_ids,
)
from shadowseed.gate.signals import EXTERNAL_EVIDENCE_KINDS, recurrence_signal


# -- signals -----------------------------------------------------------------


def test_signal_serialization_roundtrip_is_deterministic():
    signal = ValidationSignal(
        kind=SignalKind.SSOT,
        direction=SignalDirection.SUPPORT,
        strength=0.75,
        source_ref="doc::chunk_001",
        verified=True,
        independent=True,
        reason="matched trusted chunk",
    )
    data = signal.to_dict()
    assert list(data.keys()) == [
        "kind", "direction", "strength", "source_ref",
        "verified", "independent", "reason",
    ]
    assert ValidationSignal.from_dict(data) == signal


def test_signal_accepts_raw_string_enum_values():
    signal = ValidationSignal(kind="recurrence", direction="support")
    assert signal.kind is SignalKind.RECURRENCE
    assert signal.direction is SignalDirection.SUPPORT


@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0, -5.0])
def test_signal_rejects_out_of_range_strength(bad):
    with pytest.raises(ValueError):
        ValidationSignal(kind=SignalKind.PROBE, strength=bad)


def test_signal_rejects_invalid_kind_and_direction():
    with pytest.raises(ValueError):
        ValidationSignal(kind="not_a_kind")
    with pytest.raises(ValueError):
        ValidationSignal(kind=SignalKind.PROBE, direction="sideways")


def test_recurrence_is_never_external_evidence():
    # The core anti-double-counting guarantee.
    assert SignalKind.RECURRENCE not in EXTERNAL_EVIDENCE_KINDS
    recurrence = ValidationSignal(kind=SignalKind.RECURRENCE, strength=1.0)
    assert recurrence.is_external_evidence is False
    for kind in (SignalKind.SSOT, SignalKind.HUMAN_FEEDBACK, SignalKind.RETRIEVAL):
        assert ValidationSignal(kind=kind).is_external_evidence is True


def test_recurrence_signal_builder_scales_and_stays_recurrence():
    below = recurrence_signal(1, threshold=2)
    assert below.kind is SignalKind.RECURRENCE
    assert below.direction is SignalDirection.NEUTRAL
    assert below.strength == 0.0
    at = recurrence_signal(2, threshold=2)
    assert at.direction is SignalDirection.SUPPORT
    saturated = recurrence_signal(100, threshold=2)
    assert saturated.strength == 1.0
    assert saturated.is_external_evidence is False


# -- policies ----------------------------------------------------------------


def test_default_policy_is_explicit():
    assert DEFAULT_POLICY_ID == "exploratory"
    assert default_policy().policy_id == DEFAULT_POLICY_ID
    assert resolve_policy(None).policy_id == DEFAULT_POLICY_ID


def test_resolve_policy_known_and_unknown():
    assert isinstance(resolve_policy("exploratory"), ExploratoryPolicy)
    assert isinstance(resolve_policy("evidence_backed"), EvidenceBackedPolicy)
    assert available_policy_ids() == ["evidence_backed", "exploratory"]
    with pytest.raises(ValueError):
        resolve_policy("totally_unknown")


def test_example_profiles_raise_clear_error_not_silent_fallback():
    for policy_id in EXAMPLE_POLICY_IDS:
        with pytest.raises(ValueError, match="not implemented yet"):
            resolve_policy(policy_id)


def test_exploratory_promotes_on_recurrence_alone():
    policy = ExploratoryPolicy()
    proposal = policy.propose(
        [recurrence_signal(3, threshold=2)],
        AuthoritySnapshot(weight=0.0, status="ACTIVE"),
    )
    assert proposal.satisfied is True
    assert proposal.verdict is ProposedVerdict.PROMOTE_OR_VALIDATE
    assert "recurrence" in proposal.reason


def test_evidence_backed_rejects_recurrence_only():
    policy = EvidenceBackedPolicy()
    proposal = policy.propose(
        [recurrence_signal(50, threshold=2)],
        AuthoritySnapshot(weight=0.0, status="ACTIVE"),
    )
    assert proposal.satisfied is False
    assert proposal.verdict is ProposedVerdict.BLOCK
    assert "verified_external_evidence" in proposal.missing


def test_evidence_backed_accepts_verified_external_evidence():
    policy = EvidenceBackedPolicy()
    proposal = policy.propose(
        [ValidationSignal(kind=SignalKind.SSOT, verified=True, strength=0.9)],
        AuthoritySnapshot(weight=0.0, status="ACTIVE"),
    )
    assert proposal.satisfied is True
    assert proposal.verdict is ProposedVerdict.PROMOTE_OR_VALIDATE


def test_unverified_external_signal_does_not_satisfy_evidence_backed():
    policy = EvidenceBackedPolicy()
    proposal = policy.propose(
        [ValidationSignal(kind=SignalKind.SSOT, verified=False)],
        AuthoritySnapshot(),
    )
    assert proposal.satisfied is False


def test_fresh_contradiction_proposes_contradict_under_both_policies():
    contradiction = ValidationSignal(
        kind=SignalKind.CONTRADICTION, direction=SignalDirection.OPPOSE
    )
    for policy in (ExploratoryPolicy(), EvidenceBackedPolicy()):
        proposal = policy.propose([contradiction], AuthoritySnapshot())
        assert proposal.verdict is ProposedVerdict.CONTRADICT


def test_blocking_contradiction_blocks_until_resolution_signal():
    policy = ExploratoryPolicy()
    authority = AuthoritySnapshot(weight=0.4, status="ACTIVE", has_blocking_contradiction=True)
    blocked = policy.propose([recurrence_signal(9, threshold=2)], authority)
    assert blocked.verdict is ProposedVerdict.BLOCK
    assert "contradiction_resolution" in blocked.missing
    # Recurrence alone cannot lift the block; a resolution signal is required.


# -- events ------------------------------------------------------------------


def test_gate_event_serialization_roundtrip_and_deltas():
    event = GateEvent(
        event_id=new_event_id("ss_001", 1),
        seed_id="ss_001",
        policy_id="exploratory",
        decision=GateDecision.PROMOTED,
        signals=(recurrence_signal(4, threshold=2),),
        status_before="ACTIVE",
        status_after="PROMOTED",
        weight_before=0.4,
        weight_after=0.6,
        contradiction_before=ContradictionState(),
        contradiction_after=ContradictionState(),
        authority_version=3,
        reason="exploratory support via recurrence",
        created_at=None,
    )
    assert event.event_id == "gate::ss_001::000001"
    assert round(event.weight_delta, 6) == 0.2
    assert event.changed_authority is True
    restored = GateEvent.from_dict(event.to_dict())
    assert restored == event


def test_gate_event_no_change_reports_no_authority_change():
    event = GateEvent(
        event_id=new_event_id("ss_002", 2),
        seed_id="ss_002",
        policy_id="exploratory",
        decision=GateDecision.NO_CHANGE,
        status_before="ACTIVE",
        status_after="ACTIVE",
        weight_before=0.3,
        weight_after=0.3,
    )
    assert event.changed_authority is False
    assert event.weight_delta == 0.0


def test_event_id_is_deterministic():
    assert new_event_id("ss_010", 7) == new_event_id("ss_010", 7)
    assert new_event_id("ss_010", 7) != new_event_id("ss_010", 8)


def test_summarize_signals_flags_recurrence_and_external_evidence():
    summary = summarize_signals(
        [
            recurrence_signal(3, threshold=2),
            ValidationSignal(kind=SignalKind.SSOT, verified=True),
        ]
    )
    assert summary["count"] == 2
    assert summary["has_recurrence"] is True
    assert summary["has_external_evidence"] is True
    assert summary["kinds"] == ["recurrence", "ssot"]
