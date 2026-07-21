from __future__ import annotations

import numpy as np
import pytest

from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.manager import SeedStatus, ShadowSeed, ValidationGateResult
from shadowseed_agent import (
    AgentInfluenceRecord,
    AgentSafetyContract,
    InfluenceAction,
    WeightlessInfluenceError,
    assert_no_weightless_influence,
    can_seed_trigger_retrieval,
    evidence_can_support_gate,
    has_logged_promotion,
)


def make_seed(
    *,
    seed_id: str = "seed-1",
    status: SeedStatus = SeedStatus.NEW,
    weight: float = 0.0,
    contradiction_score: float = 0.0,
) -> ShadowSeed:
    seed = ShadowSeed(
        id=seed_id,
        text="The owner of this action item is not explicitly named.",
        embedding=np.array([1.0, 0.0]),
    )
    seed.unsafe_set_authority(
        status=status, weight=weight, contradiction_score=contradiction_score
    )
    return seed


def promotion_gate(seed_id: str = "seed-1") -> ValidationGateResult:
    return ValidationGateResult(
        seed_id=seed_id,
        status_before="ACTIVE",
        status_after="PROMOTED",
        weight_before=0.4,
        weight_after=0.6,
        occurrence_count=3,
        evidence_count=2,
        internal_recognition_passed=True,
        external_evidence_passed=True,
        contradiction_free=True,
        external_evidence_applied=True,
        contradiction_applied=False,
        promoted=True,
        verdict="promoted",
    )


def test_shadowseed_agent_public_exports_import() -> None:
    import shadowseed_agent

    assert shadowseed_agent.AgentSafetyContract is AgentSafetyContract
    assert shadowseed_agent.can_seed_trigger_retrieval is can_seed_trigger_retrieval
    assert shadowseed_agent.evidence_can_support_gate is evidence_can_support_gate


def test_weightless_seed_cannot_trigger_retrieval() -> None:
    seed = make_seed(status=SeedStatus.PROMOTED, weight=0.0)

    decision = AgentSafetyContract().inspect(
        seed,
        InfluenceAction.RETRIEVAL,
        gate_log=[promotion_gate()],
    )

    assert decision.is_blocked
    assert "weightless_seed" in decision.blocking_reasons


def test_promoted_seed_requires_logged_gate() -> None:
    seed = make_seed(status=SeedStatus.PROMOTED, weight=0.6)

    decision = AgentSafetyContract().inspect(seed, InfluenceAction.PROBE, gate_log=[])

    assert decision.is_blocked
    assert "missing_logged_promotion" in decision.blocking_reasons


def test_promoted_seed_with_logged_gate_can_trigger_retrieval() -> None:
    seed = make_seed(status=SeedStatus.PROMOTED, weight=0.6)

    decision = AgentSafetyContract().inspect(
        seed,
        InfluenceAction.RETRIEVAL,
        gate_log=[promotion_gate()],
    )

    assert not decision.is_blocked
    assert decision.blocking_reasons == ()

    # The retrieval helper now records the decision and links it to a
    # current-version Gate event.
    event = GateEvent(
        event_id="e1",
        seed_id="seed-1",
        policy_id="exploratory",
        decision=GateDecision.PROMOTED,
        status_after="PROMOTED",
        authority_version=seed.authority_version,
    )
    ledger: list = []
    assert can_seed_trigger_retrieval(
        seed, gate_events=[event], ledger=ledger, contradiction_blocking=False
    )
    assert ledger and ledger[0].allowed and ledger[0].gate_event_ref == "e1"


def test_gate_log_accepts_exported_dict_records() -> None:
    exported_gate = promotion_gate().to_dict()

    assert has_logged_promotion("seed-1", [exported_gate])


def test_llm_output_does_not_count_as_verified_evidence() -> None:
    assert not evidence_can_support_gate(
        {"kind": "llm_output", "verified": True, "source": "draft answer"}
    )
    assert not evidence_can_support_gate(
        {"source_kind": "generated_completion", "verified": True}
    )


def test_verified_ssot_evidence_can_support_gate() -> None:
    assert evidence_can_support_gate(
        {"kind": "ssot_chunk", "verified": True, "source": "policy/doc-1"}
    )


def test_contradiction_blocks_promoted_seed_by_default() -> None:
    seed = make_seed(
        status=SeedStatus.PROMOTED,
        weight=0.6,
        contradiction_score=0.4,
    )

    decision = AgentSafetyContract().inspect(
        seed,
        InfluenceAction.WARNING,
        gate_log=[promotion_gate()],
    )

    assert decision.is_blocked
    assert "contradiction_present" in decision.blocking_reasons


def test_audit_replay_rejects_weightless_influence() -> None:
    records = [
        AgentInfluenceRecord(
            seed_id="seed-1",
            action="retrieval",
            seed_weight=0.0,
            seed_status="NEW",
            allowed=True,
            reason="buggy_adapter_allowed_it",
        )
    ]

    with pytest.raises(WeightlessInfluenceError):
        assert_no_weightless_influence(records)


def test_audit_replay_accepts_blocked_weightless_seed() -> None:
    records = [
        AgentInfluenceRecord(
            seed_id="seed-1",
            action="retrieval",
            seed_weight=0.0,
            seed_status="NEW",
            allowed=False,
            reason="weightless_seed",
        )
    ]

    assert_no_weightless_influence(records)
