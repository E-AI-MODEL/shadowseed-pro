"""Review dossiers are inspectable snapshots, not Gate repair operations.

All examples are fictional and model-free. No investigator-authored label is
independent verification of a source, its identity or its truth.
"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from shadowseed.application.inspection import InspectionService
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.text_similarity import lexical_embedding
from shadowseed_agent import (
    AgentInfluenceRecord,
    AgentSafetyContract,
    InfluenceAction,
    assert_influence_records_valid,
)
from shadowseed_agent.legacy_ssot_review import (
    DOSSIER_SCHEMA,
    build_legacy_ssot_review_dossier,
)


def _legacy_history():
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        validation_increment=0.2,
        promotion_threshold=0.5,
    )
    seed_id = manager.add_or_update_seed("Kan de blauwe klep druk B veranderen?")
    manager.add_or_update_seed(manager.get_seed(seed_id).text)
    manager.add_or_update_seed(manager.get_seed(seed_id).text)
    for index in range(4):
        doc = f"fictional_doc_{index}::chunk_001"
        manager.run_validation_gate(
            seed_id,
            external_evidence=True,
            signals=[
                ValidationSignal(
                    kind=SignalKind.SSOT,
                    direction=SignalDirection.SUPPORT,
                    source_ref=doc,
                    verified=True,
                    independent=True,
                    strength=0.9,
                    reason=f"verified SSOT chunk {doc}",
                )
            ],
        )
    seed = manager.get_seed(seed_id)
    assert seed.status is SeedStatus.PROMOTED
    promoted = next(
        event for event in reversed(manager.gate_events)
        if event.decision.value == "promoted"
    )
    use = AgentInfluenceRecord(
        seed_id=seed_id,
        action=InfluenceAction.ANSWER_MODIFICATION.value,
        seed_weight=float(seed.weight),
        seed_status=seed.status.value,
        allowed=True,
        reason="historical use, not new authorization",
        gate_event_ref=promoted.event_id,
        authority_version=promoted.authority_version,
        policy_id=promoted.policy_id,
        decided_at="2026-10-20T09:00:00+01:00",
    )
    return manager, seed_id, use


def test_real_gate_history_dossier_is_read_only_and_conservative() -> None:
    manager, seed_id, old_use = _legacy_history()
    gate_before = deepcopy([item.to_dict() for item in manager.gate_events])
    seed_before = deepcopy(manager.get_seed(seed_id).to_dict())
    assert_influence_records_valid([old_use], manager.gate_events)

    report = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id), manager.gate_events, [old_use],
        session_id="synthetic::session",
    )
    assert report["schema"] == DOSSIER_SCHEMA
    assert report["seed_id"] == seed_id
    assert report["known_legacy_producer_detected"] is True
    assert report["legacy_signal_count"] == 4
    assert report["gate_events_inspected"] == 4
    assert report["recorded_prior_use_count"] == 1
    assert report["recorded_prior_allowed_use_count"] == 1
    assert report["review_state"] == "not_requalified"
    assert report["source_to_seed_truth_checked"] is False
    assert report["actor_identity_checked"] is False
    assert report["independence_verified"] is False
    assert report["requalification_performed"] is False
    assert report["source_refs_included"] is False
    assert len(report["dossier_sha256"]) == 64
    assert all(item["verified_flag_claimed"] for item in report["historical_signals"])
    assert all(item["independent_flag_claimed"] for item in report["historical_signals"])
    assert all(
        item["producer_family"] == "historical_similarity_producer"
        for item in report["historical_signals"]
    )
    assert all("source_ref" not in item for item in report["historical_signals"])
    assert "fictional_doc_" not in json.dumps(report)
    assert report["historical_influence"][0]["recorded_allowed"] is True
    assert not any(key in report for key in ("allowed", "authorized", "can_release"))

    # Report generation neither changes old authority nor grants new influence.
    assert [item.to_dict() for item in manager.gate_events] == gate_before
    assert manager.get_seed(seed_id).to_dict() == seed_before
    assert_influence_records_valid([old_use], manager.gate_events)
    current = AgentSafetyContract().decide_and_record(
        manager.get_seed(seed_id),
        InfluenceAction.ANSWER_MODIFICATION,
        gate_events=manager.gate_events,
        ledger=[],
        contradiction_blocking=False,
    )
    assert current.allowed is False
    assert current.reason == "legacy_ssot_requires_review"


def test_dossier_replays_identically_from_serialized_snapshots() -> None:
    manager, seed_id, old_use = _legacy_history()
    original = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id), manager.gate_events, [old_use]
    )
    serialized = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id).to_dict(),
        [event.to_dict() for event in manager.gate_events],
        [vars(old_use).copy()],
    )
    assert original == serialized
    assert original["dossier_sha256"] == serialized["dossier_sha256"]


def test_historical_event_tampering_changes_digest_without_changing_original() -> None:
    manager, seed_id, old_use = _legacy_history()
    source = [event.to_dict() for event in manager.gate_events]
    before = deepcopy(source)
    first = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id).to_dict(), source, [old_use]
    )
    tampered = deepcopy(source)
    tampered[0]["weight_after"] = 0.12345
    changed = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id).to_dict(), tampered, [old_use]
    )
    assert first["dossier_sha256"] != changed["dossier_sha256"]
    assert first["historical_signals"][0]["gate_event_sha256"] != (
        changed["historical_signals"][0]["gate_event_sha256"]
    )
    assert source == before


def test_source_references_are_explicit_opt_in_for_trusted_local_review() -> None:
    manager, seed_id, _ = _legacy_history()
    redacted = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id), manager.gate_events
    )
    local = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id), manager.gate_events,
        include_source_refs=True,
    )
    assert redacted["source_refs_included"] is False
    assert local["source_refs_included"] is True
    assert local["historical_signals"][0]["source_ref"] == (
        "fictional_doc_0::chunk_001"
    )
    assert "recorded_reason" in local["historical_signals"][0]
    assert local["historical_signals"][0]["source_ref_sha256"] == (
        redacted["historical_signals"][0]["source_ref_sha256"]
    )


def test_nonlegacy_research_ssot_support_is_not_falsely_certified() -> None:
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = manager.add_or_update_seed("What if an alternative holds?")
    manager.submit_signals(
        seed_id,
        [ValidationSignal(
            kind=SignalKind.SSOT,
            direction=SignalDirection.SUPPORT,
            verified=True,
            source_ref="fixture://predeclared/one",
            reason="researcher authored signal",
        )],
        policy_id="evidence_backed",
    )
    report = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id), manager.gate_events
    )
    assert report["known_legacy_producer_detected"] is False
    assert report["other_ssot_support_count"] == 1
    assert report["legacy_signal_count"] == 0
    assert report["review_state"] == "not_requalified"
    assert report["source_to_seed_truth_checked"] is False


def test_intermediate_self_attestation_is_identified_without_auth_claim() -> None:
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = manager.add_or_update_seed("Hypothesis under discussion")
    manager.submit_signals(
        seed_id,
        [ValidationSignal(
            kind=SignalKind.SSOT,
            direction=SignalDirection.SUPPORT,
            verified=True,
            source_ref="claimed-source-unit",
            reason="relation-attested:ssot:doc at fake-time",
        )],
        policy_id="evidence_backed",
    )
    report = build_legacy_ssot_review_dossier(
        manager.get_seed(seed_id), manager.gate_events
    )
    assert report["known_legacy_producer_detected"] is True
    assert report["legacy_signal_count"] == 1
    assert report["historical_signals"][0]["producer_family"] == (
        "intermediate_self_attestation"
    )


def test_malformed_history_is_rejected_not_mistaken_for_reviewed() -> None:
    with pytest.raises(ValueError, match="signals"):
        build_legacy_ssot_review_dossier(
            {"id": "one", "status": "PROMOTED"},
            [{"seed_id": "one", "signals": "invalid-history"}],
        )
    with pytest.raises(ValueError, match="nonempty"):
        build_legacy_ssot_review_dossier({"text": "missing id"}, [])
    with pytest.raises(TypeError, match="mapping"):
        build_legacy_ssot_review_dossier({"id": "one"}, [object()])


def test_inspection_service_builds_dossier_from_stored_state_without_mutation() -> None:
    manager, seed_id, old_use = _legacy_history()
    state = {
        "manager": {
            "seeds": [manager.get_seed(seed_id).to_dict()],
            "config": manager.config.to_dict(),
            "gate_events": [event.to_dict() for event in manager.gate_events],
        },
        "influence_records": [vars(old_use).copy()],
    }
    stored = {
        "state": state,
        "session_id": "fixture::legacy",
    }
    before = deepcopy(stored)

    class ReadOnlySessions:
        def load(self, session_id):
            assert session_id == "fixture::legacy"
            return stored

    service = InspectionService(ReadOnlySessions())
    report = service.legacy_ssot_review_dossier("fixture::legacy", seed_id)
    assert report["known_legacy_producer_detected"] is True
    assert report["recorded_prior_allowed_use_count"] == 1
    assert stored == before
    with pytest.raises(KeyError, match="unknown seed"):
        service.legacy_ssot_review_dossier("fixture::legacy", "different")


def test_workbench_controller_exposes_dossier_without_evidence_submission(
    tmp_path, monkeypatch
) -> None:
    from shadowseed.workbench.controller import WorkbenchController

    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Read-only legacy inspection",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(session_id, "What is missing from this privacy plan?")
    seed_id = str(result["session"]["seeds"][0]["id"])
    before = deepcopy(controller.sessions.load(session_id)["state"])

    def forbid_mutation(*_args, **_kwargs):
        raise AssertionError("legacy inspection cannot submit evidence")

    monkeypatch.setattr(controller.sessions, "submit_verified_evidence_authorized", forbid_mutation)
    dossier = controller.legacy_ssot_review_dossier(session_id, seed_id)
    assert dossier["schema"] == DOSSIER_SCHEMA
    assert dossier["known_legacy_producer_detected"] is False
    assert dossier["requalification_performed"] is False
    assert controller.sessions.load(session_id)["state"] == before
