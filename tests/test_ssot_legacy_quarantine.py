"""Historical SSOT-Gate events remain immutable but cannot grant NEW influence.

The synthetic legacy evidence simulates the original similarity-only producer
in PR #240. No real source truth, human review or research efficacy is claimed.
"""

from dataclasses import asdict

from shadowseed.gate.events import GateDecision, GateEvent
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.text_similarity import lexical_embedding
from shadowseed_agent import (
    AgentInfluenceRecord,
    AgentSafetyContract,
    InfluenceAction,
    assert_influence_records_valid,
    can_seed_trigger_retrieval,
)
from shadowseed_agent.agent_contract import has_unreviewed_ssot_support


def _legacy_promoted_manager() -> tuple[SSLManager, str]:
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        validation_increment=0.2,
        promotion_threshold=0.5,
    )
    seed_id = manager.add_or_update_seed(
        "Mogelijk beïnvloedt de blauwe klep de druk in kamer B."
    )
    manager.add_or_update_seed(manager.get_seed(seed_id).text)
    manager.add_or_update_seed(manager.get_seed(seed_id).text)
    for n in range(4):
        manager.run_validation_gate(
            seed_id,
            external_evidence=True,
            signals=[
                ValidationSignal(
                    kind=SignalKind.SSOT,
                    direction=SignalDirection.SUPPORT,
                    verified=True,
                    source_ref=f"old_doc_{n}::chunk_001",
                    strength=0.85,
                    independent=True,
                    reason=f"verified SSOT chunk old_doc_{n}::chunk_001",
                )
            ],
        )
    seed = manager.get_seed(seed_id)
    assert seed.status is SeedStatus.PROMOTED
    assert seed.weight > 0
    return manager, seed_id


def test_legacy_ssot_promotion_is_not_authority_for_new_answers_or_retrieval() -> None:
    manager, seed_id = _legacy_promoted_manager()
    original_history = [event.to_dict() for event in manager.gate_events]
    original_seed = manager.get_seed(seed_id).to_dict()
    assert has_unreviewed_ssot_support(seed_id, manager.gate_events) is True

    contract = AgentSafetyContract()
    inspection = contract.inspect(
        manager.get_seed(seed_id),
        InfluenceAction.ANSWER_MODIFICATION,
        manager.gate_events,
        contradiction_blocking=False,
    )
    assert inspection.is_blocked is True
    assert inspection.blocking_reasons == ("legacy_ssot_requires_review",)

    ledger: list[AgentInfluenceRecord] = []
    answer_record = contract.decide_and_record(
        manager.get_seed(seed_id),
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=False,
    )
    assert answer_record.allowed is False
    assert answer_record.reason == "legacy_ssot_requires_review"
    assert can_seed_trigger_retrieval(
        manager.get_seed(seed_id),
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=False,
        contract=contract,
    ) is False
    assert ledger[-1].reason == "legacy_ssot_requires_review"
    assert len(ledger) == 2
    assert [event.to_dict() for event in manager.gate_events] == original_history
    assert manager.get_seed(seed_id).to_dict() == original_seed


def test_serialized_gate_events_remain_detectable() -> None:
    manager, seed_id = _legacy_promoted_manager()
    serialized = [event.to_dict() for event in manager.gate_events]
    restored = [GateEvent.from_dict(event) for event in serialized]
    assert has_unreviewed_ssot_support(seed_id, restored)
    assert has_unreviewed_ssot_support(seed_id, serialized)
    assert not has_unreviewed_ssot_support("different-seed", serialized)


def test_untrusted_new_relation_label_cannot_remove_quarantine() -> None:
    manager, seed_id = _legacy_promoted_manager()
    manager.submit_signals(
        seed_id,
        [
            ValidationSignal(
                kind=SignalKind.HUMAN_FEEDBACK,
                direction=SignalDirection.SUPPORT,
                verified=True,
                source_ref="new_operator_claim",
                reason="claimed operator verified",
            )
        ],
        policy_id="evidence_backed",
    )
    assert has_unreviewed_ssot_support(seed_id, manager.gate_events)
    ledger: list = []
    result = AgentSafetyContract().decide_and_record(
        manager.get_seed(seed_id),
        InfluenceAction.DECISION,
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=False,
    )
    assert not result.allowed
    assert result.reason == "legacy_ssot_requires_review"


def test_ordinary_recurrence_promotion_is_not_falsely_quarantined() -> None:
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = manager.add_or_update_seed("Another atomic uncertain candidate")
    for count in (3, 4, 5):
        manager.seeds[seed_id].occurrence_count = count
        manager.submit_signals(
            seed_id, [recurrence_signal(count, threshold=2)], policy_id="exploratory"
        )
    seed = manager.get_seed(seed_id)
    assert seed.status is SeedStatus.PROMOTED
    assert has_unreviewed_ssot_support(seed_id, manager.gate_events) is False
    ledger: list = []
    result = AgentSafetyContract().decide_and_record(
        seed,
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=ledger,
        contradiction_blocking=False,
    )
    assert result.allowed is True
    assert_influence_records_valid(ledger, manager.gate_events)


def test_historical_allowed_record_replays_without_rewriting_past() -> None:
    manager, seed_id = _legacy_promoted_manager()
    seed = manager.get_seed(seed_id)
    event = next(
        event for event in reversed(manager.gate_events)
        if event.decision is GateDecision.PROMOTED
    )
    historical = AgentInfluenceRecord(
        seed_id=seed_id,
        action=InfluenceAction.ANSWER_MODIFICATION.value,
        seed_weight=seed.weight,
        seed_status=seed.status.value,
        allowed=True,
        reason="historical pre-fix use",
        gate_event_ref=event.event_id,
        authority_version=event.authority_version,
        contradiction_blocking=False,
        policy_id=event.policy_id,
        decided_at="2026-10-20T09:00:00+01:00",
    )
    assert_influence_records_valid([historical], manager.gate_events)
    assert asdict(historical)["allowed"] is True
    # This is audit replay of an old action, NOT permission for a new action.
    current = AgentSafetyContract().decide_and_record(
        seed,
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=[],
        contradiction_blocking=False,
    )
    assert current.allowed is False


def test_read_only_inspection_labels_quarantined_legacy_seed() -> None:
    from shadowseed.application.inspection import InspectionService

    manager, seed_id = _legacy_promoted_manager()
    seed = manager.get_seed(seed_id)

    class StoredFixture:
        def load(self, _session_id):
            return {
                "session_id": "session::legacy",
                "title": "Archived SSOT session",
                "profile_id": "demo",
                "backend": "fixture",
                "model_id": "",
                "created_at": "2026-10-24T00:00:00+00:00",
                "updated_at": "2026-10-24T00:00:00+00:00",
                "config": {"runtime_mode": "live", "authority_profile_id": "strict"},
                "state": {
                    "manager": {
                        "seeds": [seed.to_dict()],
                        "config": manager.config.to_dict(),
                        "gate_events": [event.to_dict() for event in manager.gate_events],
                    },
                    "session_config": {
                        "runtime_mode": "live",
                        "authority_profile_id": "strict",
                    },
                    "turn_reports": [],
                    "influence_records": [],
                },
            }

        def list_feedback(self, _session_id):
            return []

    displayed = InspectionService(StoredFixture()).session_view("session::legacy")
    assert len(displayed["seeds"]) == 1
    seed_view = displayed["seeds"][0]
    assert seed_view["legacy_ssot_requires_review"] is True
    assert seed_view["current_gate_authorized"] is False
    assert "Historical SSOT support" in seed_view["plain_explanation"]
    assert seed_view["weight"] == seed.weight
    assert len(manager.gate_events) == 4


def test_research_ssot_attestation_without_actor_cannot_authorize_live_agent() -> None:
    # Researcher-submitted Gate SSOT signals can remain in the immutable
    # experimental trace, but their provenance does not establish the actor
    # authorization required by the product boundary.
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = manager.add_or_update_seed("An atomic alternative worth testing")
    for i in range(3):
        manager.submit_signals(
            seed_id,
            [
                ValidationSignal(
                    kind=SignalKind.SSOT,
                    direction=SignalDirection.SUPPORT,
                    verified=True,
                    source_ref=f"fixture://predeclared-research-source/{i}",
                    reason="researcher attestation, no product actor ledger",
                )
            ],
            policy_id="evidence_backed",
        )
    seed = manager.get_seed(seed_id)
    assert seed.status is SeedStatus.PROMOTED
    assert has_unreviewed_ssot_support(seed_id, manager.gate_events)
    history_before = [event.to_dict() for event in manager.gate_events]
    ledger: list = []
    outcome = AgentSafetyContract().decide_and_record(
        seed, InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events, ledger=ledger,
        contradiction_blocking=False,
    )
    assert outcome.allowed is False
    assert outcome.reason == "legacy_ssot_requires_review"
    assert [event.to_dict() for event in manager.gate_events] == history_before


def test_unknown_legacy_ssot_support_is_quarantined_without_string_matching() -> None:
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = manager.add_or_update_seed("A measurable uncertainty")
    for i in range(3):
        manager.submit_signals(
            seed_id,
            [
                ValidationSignal(
                    kind=SignalKind.SSOT,
                    direction=SignalDirection.SUPPORT,
                    verified=True,
                    source_ref=f"unknown-old-source-{i}",
                    reason="archived-import-variant",
                )
            ],
            policy_id="evidence_backed",
        )
    assert manager.get_seed(seed_id).status is SeedStatus.PROMOTED
    restored = [GateEvent.from_dict(e.to_dict()) for e in manager.gate_events]
    assert has_unreviewed_ssot_support(seed_id, restored)
    record = AgentSafetyContract().decide_and_record(
        manager.get_seed(seed_id),
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=restored, ledger=[], contradiction_blocking=False,
    )
    assert record.allowed is False
    assert record.reason == "legacy_ssot_requires_review"


def test_unverified_ssot_support_does_not_gain_point_of_use_authority() -> None:
    # Any SSOT support in the old Gate-event schema lacks an authenticated
    # product ledger binding, even if metadata says unverified.
    manager, seed_id = _legacy_promoted_manager()
    gate_log = [e.to_dict() for e in manager.gate_events]
    for event in gate_log:
        for signal in event["signals"]:
            if signal["kind"] == SignalKind.SSOT.value:
                signal["verified"] = False
                signal["reason"] = None
                signal["source_ref"] = "nonstandard-import"
    assert has_unreviewed_ssot_support(seed_id, gate_log)
    assert not has_unreviewed_ssot_support("unrelated-seed", gate_log)


def test_intermediate_relation_attested_ssot_signal_is_not_product_auth() -> None:
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = manager.add_or_update_seed("One epistemic hypothesis")
    for i in range(3):
        manager.submit_signals(
            seed_id,
            [
                ValidationSignal(
                    kind=SignalKind.SSOT,
                    direction=SignalDirection.SUPPORT,
                    verified=True,
                    source_ref=f"research-unit-{i}",
                    reason="relation-attested:ssot:source at fake-review-time",
                )
            ],
            policy_id="evidence_backed",
        )
    assert manager.get_seed(seed_id).status is SeedStatus.PROMOTED
    assert has_unreviewed_ssot_support(seed_id, manager.gate_events)
    assert not AgentSafetyContract().decide_and_record(
        manager.get_seed(seed_id), InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events, ledger=[], contradiction_blocking=False,
    ).allowed


def test_real_live_prepare_turn_denies_legacy_promoted_seed_before_model_context() -> None:
    from shadowseed.chat import ShadowChatSession

    session = ShadowChatSession(
        backend="fixture",
        embedding_backend="lexical",
        runtime_mode="live",
        recurrence_mode="pairwise",
    )
    text = "Privacy as a missing decision boundary."
    seed_id = session.manager.add_or_update_seed(text)
    session.manager.add_or_update_seed(text)
    session.manager.add_or_update_seed(text)
    session.born_turn[seed_id] = -1
    for index in range(4):
        session.manager.run_validation_gate(
            seed_id,
            external_evidence=True,
            signals=[
                ValidationSignal(
                    kind=SignalKind.SSOT,
                    direction=SignalDirection.SUPPORT,
                    source_ref=f"archived_doc_{index}::chunk_001",
                    verified=True,
                    strength=0.85,
                    independent=True,
                    reason=f"verified SSOT chunk archived_doc_{index}::chunk_001",
                )
            ],
        )
    assert session.manager.get_seed(seed_id).status is SeedStatus.PROMOTED
    history_before = [event.to_dict() for event in session.manager.gate_events]
    seed_before = session.manager.get_seed(seed_id).to_dict()

    prepared = session.prepare_turn(text)
    assert seed_id in prepared.selected_seed_ids
    assert prepared.model_context == ""
    assert prepared.surfaced_seeds == ()
    assert prepared.surfaced_seed_ids == ()
    assert any(
        item["seed_id"] == seed_id
        and item["allowed"] is False
        and item["reason"] == "legacy_ssot_requires_review"
        for item in prepared.influence_decisions
    )
    # Denial is recorded before the model ever receives candidate context.
    assert session.influence_records[-1].reason == "legacy_ssot_requires_review"
    session.abort_turn(prepared)
    assert session.manager.get_seed(seed_id).to_dict() == seed_before
    assert [event.to_dict() for event in session.manager.gate_events] == history_before
