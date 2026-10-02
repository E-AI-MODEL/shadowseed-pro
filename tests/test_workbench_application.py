from __future__ import annotations

import json

import pytest

from shadowseed.application.comparison import ComparisonService
from shadowseed.application.configuration import REBUILD_REQUIRED, setting_metadata
from shadowseed.application.feedback import FeedbackService
from shadowseed.application.inspection import InspectionService
from shadowseed.application.models import SessionConfig
from shadowseed.application.orchestration import (
    BLOCKED,
    HUMAN_TURN,
    OPTIONAL_REVIEW,
    SSL_TURN,
    derive_seed_orchestration,
)
from shadowseed.application.scenarios import parse_scenario
from shadowseed.application.sessions import service_for_workspace
from shadowseed.core_config import SSLCoreConfig
from shadowseed.workbench.controller import WorkbenchController


def test_controller_runs_and_resumes_fixture_session(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Round 2 smoke",
        profile_id="demo",
        backend="fixture",
    )

    first = controller.send_turn(session_id, "What uncertainty remains?")
    assert first["report"]["turn"] == 0
    assert first["session"]["turn"] == 1

    restored = WorkbenchController(tmp_path / "workspace")
    second = restored.send_turn(session_id, "What evidence would change the answer?")
    assert second["report"]["turn"] == 1
    assert second["session"]["turn"] == 2
    assert len(second["session"]["turn_reports"]) == 2


def test_hosted_backend_requires_fresh_explicit_confirmation(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    with pytest.raises(ValueError, match="external provider"):
        controller.create_session(
            title="Hosted",
            profile_id="balanced",
            backend="openai",
            model_id="example-model",
            external_confirmed=False,
        )


def test_hosted_revision_backend_requires_explicit_confirmation(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")

    with pytest.raises(ValueError, match="external provider"):
        controller.create_session(
            title="Hosted revision",
            profile_id="demo",
            backend="fixture",
            revision_backend="openai",
            revision_model_id="example-revision-model",
            runtime_mode="live",
            embedding_backend="lexical",
            external_confirmed=False,
        )


def test_advanced_revision_backend_change_requires_explicit_confirmation(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Revision provider boundary",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )

    with pytest.raises(ValueError, match="external provider"):
        controller.update_session_advanced(
            session_id,
            settings={
                "revision_backend": "openai",
                "revision_model_id": "example-revision-model",
            },
            external_confirmed=False,
        )

    stored = controller.sessions.load(session_id)
    assert stored["config"]["revision_backend"] is None
    assert stored["config"]["revision_model_id"] is None


def test_controller_creates_and_lists_explicit_live_session(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Live fixture",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
        embedding_backend="lexical",
    )

    stored = controller.sessions.load(session_id)
    view = controller.session_view(session_id)
    choices = controller.session_choices(controller.list_sessions())

    assert stored["config"]["runtime_mode"] == "live"
    assert stored["config"]["embedding_backend"] == "lexical"
    assert view["runtime_mode"] == "live"
    assert choices[0][0] == "Live fixture · SSL chat · fixture · 0 turns"


def test_live_non_fixture_requires_semantic_embeddings_or_explicit_override(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")

    with pytest.raises(ValueError, match="require sentence-transformers or openai"):
        controller.create_session(
            title="Unsafe live",
            profile_id="balanced",
            backend="ollama",
            model_id="local-model",
            runtime_mode="live",
            embedding_backend="lexical",
        )

    session_id = controller.create_session(
        title="Explicit toy live",
        profile_id="balanced",
        backend="ollama",
        model_id="local-model",
        runtime_mode="live",
        embedding_backend="lexical",
        allow_toy_embedder=True,
    )
    assert controller.sessions.load(session_id)["config"]["allow_toy_embedder"] is True


def test_hosted_embedding_requires_explicit_confirmation(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")

    with pytest.raises(ValueError, match="external provider"):
        controller.create_session(
            title="Hosted embedding",
            profile_id="demo",
            backend="fixture",
            runtime_mode="live",
            embedding_backend="openai",
            external_confirmed=False,
        )


def test_feedback_is_record_only_and_validates_turn(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Feedback", profile_id="demo")
    sessions.run_turn(session_id, "Question")
    service = FeedbackService(sessions)

    feedback = service.record(
        session_id=session_id,
        turn_index=0,
        overall="better",
        seed_effect="no_visible_effect",
        note="Clearer answer",
    )
    assert feedback.action == "record_only"
    assert service.list(session_id) == [feedback]

    with pytest.raises(ValueError, match="does not exist"):
        service.record(session_id=session_id, turn_index=99)


def test_inspection_is_read_only_and_explains_seed_state(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Inspect", profile_id="demo")
    sessions.run_turn(session_id, "Question")
    before = sessions.load(session_id)["state"]

    view = InspectionService(sessions).session_view(session_id)
    after = sessions.load(session_id)["state"]

    assert view["turn"] == 1
    assert view["runtime_mode"] == "live"
    assert before == after
    for seed in view["seeds"]:
        assert seed["plain_explanation"]


@pytest.mark.parametrize("runtime_mode", ["evaluation", "live"])
def test_inspection_exposes_persisted_runtime_mode(tmp_path, runtime_mode: str) -> None:
    sessions = service_for_workspace(tmp_path / runtime_mode)
    session_id = sessions.create_session(
        title=f"Inspect {runtime_mode}",
        profile_id="demo",
        config=SessionConfig(runtime_mode=runtime_mode),
    )

    view = InspectionService(sessions).session_view(session_id)

    assert view["runtime_mode"] == runtime_mode


def test_inspection_defaults_legacy_session_view_to_evaluation(tmp_path, monkeypatch) -> None:
    sessions = service_for_workspace(tmp_path / "legacy")
    session_id = sessions.create_session(title="Legacy inspect", profile_id="demo")
    stored = sessions.load(session_id)
    state = dict(stored["state"])
    state["session_config"] = dict(state["session_config"])
    state["session_config"].pop("runtime_mode")
    persisted_config = dict(stored["config"])
    persisted_config.pop("runtime_mode")
    stored = {**stored, "state": state, "config": persisted_config}
    monkeypatch.setattr(sessions, "load", lambda _session_id: stored)

    view = InspectionService(sessions).session_view(session_id)

    assert view["runtime_mode"] == "evaluation"


def test_inspection_normalizes_invalid_persisted_runtime_mode(tmp_path, monkeypatch) -> None:
    sessions = service_for_workspace(tmp_path / "invalid-mode")
    session_id = sessions.create_session(title="Invalid mode", profile_id="demo")
    stored = sessions.load(session_id)
    state = {**stored["state"], "session_config": {"runtime_mode": None}}
    stored = {**stored, "state": state, "config": {"runtime_mode": None}}
    monkeypatch.setattr(sessions, "load", lambda _session_id: stored)

    view = InspectionService(sessions).session_view(session_id)

    assert view["runtime_mode"] == "evaluation"


def test_scenario_parser_and_run_create_resumable_session(tmp_path) -> None:
    payload = json.dumps(
        {
            "title": "Scenario smoke",
            "questions": ["First?", "Second?"],
            "profile_id": "demo",
            "backend": "fixture",
            "runtime_mode": "live",
            "embedding_backend": "lexical",
        }
    )
    spec = parse_scenario(payload)
    assert spec.questions == ("First?", "Second?")
    assert spec.runtime_mode == "live"
    assert spec.embedding_backend == "lexical"

    controller = WorkbenchController(tmp_path / "workspace")
    result = controller.run_scenario(payload)
    assert len(result["turn_reports"]) == 2
    assert result["session"]["turn"] == 2
    assert result["session"]["runtime_mode"] == "live"
    assert controller.session_view(result["session_id"])["turn"] == 2


def test_scenario_rejects_non_boolean_toy_override() -> None:
    with pytest.raises(ValueError, match="must be a boolean"):
        parse_scenario(
            {
                "title": "Invalid",
                "questions": ["Question?"],
                "allow_toy_embedder": "false",
            }
        )


def test_blind_comparison_is_stable_and_revealable(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(
        title="Compare",
        profile_id="demo",
        config=SessionConfig(runtime_mode="evaluation"),
    )
    sessions.run_turn(session_id, "Question")
    service = ComparisonService(sessions)

    first = service.compare_turn(session_id, 0, blinded=True)
    again = service.compare_turn(session_id, 0, blinded=True)
    revealed = service.compare_turn(session_id, 0, blinded=True, reveal=True)

    assert first == again
    assert "candidate_a_label" not in first
    assert set(revealed["revealed_mapping"].values()) == {"baseline", "shadowseed"}


def test_live_session_requires_requested_paired_control_for_comparison(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(
        title="Live compare",
        profile_id="demo",
        config=SessionConfig(runtime_mode="live"),
    )
    sessions.run_turn(session_id, "Question")

    with pytest.raises(ValueError, match="no stored no-SSL control"):
        ComparisonService(sessions).compare_turn(session_id, 0)


@pytest.mark.parametrize("malformed_mode", [None, "unknown"])
def test_legacy_comparison_normalizes_malformed_runtime_mode(
    tmp_path, monkeypatch, malformed_mode
) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(
        title="Legacy compare",
        profile_id="demo",
        config=SessionConfig(runtime_mode="evaluation"),
    )
    sessions.run_turn(session_id, "Question")
    stored = sessions.load(session_id)
    state = dict(stored["state"])
    reports = [dict(report) for report in state["turn_reports"]]
    reports[0].pop("runtime_mode", None)
    state["turn_reports"] = reports
    state_config = dict(state.get("session_config", {}))
    state_config["runtime_mode"] = malformed_mode
    state["session_config"] = state_config
    persisted_config = dict(stored.get("config", {}))
    persisted_config["runtime_mode"] = malformed_mode
    legacy_stored = {
        **stored,
        "state": state,
        "config": persisted_config,
    }
    monkeypatch.setattr(sessions, "load", lambda requested_id: legacy_stored)

    result = ComparisonService(sessions).compare_turn(session_id, 0)

    assert result["turn"] == 0
    assert result["candidate_a"]
    assert result["candidate_b"]


def test_live_verified_evidence_persists_and_enables_later_use(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Live evidence",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    first = controller.send_turn(session_id, "What is missing from this privacy plan?")
    seed = first["session"]["seeds"][0]
    seed_id = seed["id"]

    with pytest.raises(ValueError, match="explicitly confirmed"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="reviewer:0",
        )
    with pytest.raises(ValueError, match="must not be empty"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="  ",
            operator_verified=True,
        )

    decisions = []
    for index in range(3):
        result = controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=f"reviewer:{index}",
            note="Checked against an independent source.",
            operator_verified=True,
        )
        decisions.append(result["decision"])
    duplicate = controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="reviewer:2",
        operator_verified=True,
    )

    restored = WorkbenchController(tmp_path / "workspace")
    promoted = next(
        item for item in restored.session_view(session_id)["seeds"] if item["id"] == seed_id
    )
    later = restored.send_turn(session_id, seed["text"])

    assert decisions == ["validated", "validated", "promoted"]
    assert duplicate["decision"] == "blocked"
    assert duplicate["evidence_count"] == 3
    assert promoted["status"] == "PROMOTED"
    assert promoted["evidence_count"] == 3
    assert seed_id in later["report"]["surfaced_seed_ids"]


def test_evaluation_session_rejects_live_evidence_entry(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Evaluation evidence",
        profile_id="demo",
        backend="fixture",
        runtime_mode="evaluation",
    )
    result = controller.send_turn(session_id, "What is missing?")
    seed_id = result["session"]["seeds"][0]["id"]

    with pytest.raises(ValueError, match="only for live sessions"):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref="reviewer:1",
            operator_verified=True,
        )


def test_scenario_resume_rejects_runtime_configuration_change(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    live_payload = {
        "title": "Live scenario",
        "questions": ["Question?"],
        "profile_id": "demo",
        "backend": "fixture",
        "runtime_mode": "live",
        "embedding_backend": "lexical",
    }
    result = controller.run_scenario(json.dumps(live_payload))
    changed_payload = {**live_payload, "runtime_mode": "evaluation"}

    with pytest.raises(ValueError, match="runtime_mode does not match"):
        controller.resume_scenario(
            json.dumps(changed_payload),
            result["session_id"],
            start_at=1,
        )


def test_inspection_exposes_full_runtime_configuration_snapshots(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Config inspect",
        profile_id="balanced",
        backend="fixture",
        runtime_mode="live",
    )

    view = controller.session_view(session_id)

    assert view["persisted_config"]["surface_top_k"] == 2
    assert view["session_config"]["runtime_mode"] == "live"
    assert view["core_config"]["min_occurrences_for_gate"] == 3


def test_advanced_controls_update_canonical_session_and_core_config(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Advanced controls",
        profile_id="balanced",
        backend="fixture",
        runtime_mode="live",
    )

    view = controller.update_session_advanced(
        session_id,
        settings={
            "surface_threshold": 0.18,
            "surface_top_k": 4,
            "authority_profile_id": "autonomous",
            "gate_policy_id": "exploratory",
            "min_occurrences_for_gate": 2,
            "promotion_threshold": 0.4,
            "allow_self_reinforcement": True,
        },
    )
    stored = controller.sessions.load(session_id)

    assert view["session_config"]["surface_threshold"] == 0.18
    assert view["session_config"]["surface_top_k"] == 4
    assert view["session_config"]["authority_profile_id"] == "autonomous"
    assert view["session_config"]["gate_policy_id"] == "exploratory"
    assert view["session_config"]["allow_self_reinforcement"] is True
    assert view["core_config"]["min_occurrences_for_gate"] == 2
    assert view["core_config"]["promotion_threshold"] == 0.4
    assert stored["config"]["ssl_intensity"] is None
    assert stored["config"]["gate_strictness"] is None


def test_advanced_controls_keep_backend_metadata_in_sync(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Backend control",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )

    controller.update_session_advanced(
        session_id,
        settings={"model_id": None, "max_new_tokens": 512},
    )
    stored = controller.sessions.load(session_id)

    assert stored["backend"] == "fixture"
    assert stored["model_id"] is None
    assert stored["config"]["max_new_tokens"] == 512
    assert stored["state"]["session_config"]["max_new_tokens"] == 512


def test_advanced_controls_reject_unknown_keys(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Unknown control",
        profile_id="demo",
        backend="fixture",
    )

    with pytest.raises(ValueError, match="unknown Shadowseed setting"):
        controller.update_session_advanced(
            session_id,
            settings={"magic_hidden_switch": True},
        )


def test_structural_advanced_controls_are_allowed_before_seed_state_exists(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Structural before seeds",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )

    view = controller.update_session_advanced(
        session_id,
        settings={
            "recurrence_mode": "pairwise",
            "cluster_threshold": 0.72,
        },
    )

    assert view["session_config"]["recurrence_mode"] == "pairwise"
    assert view["session_config"]["cluster_threshold"] == 0.72


def test_structural_advanced_controls_fail_closed_after_seeds_exist(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Structural after seeds",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    controller.send_turn(session_id, "What Privacy Gap Remains?")
    assert controller.session_view(session_id)["seeds"]

    with pytest.raises(ValueError, match="structural setting"):
        controller.update_session_advanced(
            session_id,
            settings={"recurrence_mode": "pairwise"},
        )

    with pytest.raises(ValueError, match="force cannot bypass"):
        controller.update_session_advanced(
            session_id,
            settings={"cluster_threshold": 0.72},
            force=True,
        )


def test_maximum_gate_strictness_uses_canonical_evidence_backed_policy() -> None:
    settings = WorkbenchController.gate_strictness_settings(100)

    assert settings["authority_profile_id"] == "strict"
    assert settings["gate_policy_id"] == "evidence_backed"
    assert settings["promotion_threshold"] == 0.6
    assert settings["validation_increment"] == 0.2
    assert settings["gate_policy_id"] != "legacy_evidence_required"


def test_normal_gate_strictness_mapping_never_selects_legacy_policy() -> None:
    for percent in range(0, 101):
        settings = WorkbenchController.gate_strictness_settings(percent)
        assert settings["gate_policy_id"] != "legacy_evidence_required"


def test_setting_metadata_covers_full_runtime_configuration() -> None:
    metadata = setting_metadata()
    expected = set(SessionConfig.__dataclass_fields__) | set(SSLCoreConfig.__dataclass_fields__)

    assert expected <= set(metadata)
    assert metadata["embedding_backend"]["apply_mode"] == REBUILD_REQUIRED
    assert metadata["embedding_model"]["apply_mode"] == REBUILD_REQUIRED
    assert metadata["recurrence_mode"]["apply_mode"] == REBUILD_REQUIRED
    assert metadata["cluster_threshold"]["apply_mode"] == REBUILD_REQUIRED


def test_inspection_exposes_setting_owner_and_apply_mode(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Config semantics",
        profile_id="balanced",
        backend="fixture",
        runtime_mode="live",
    )

    view = controller.session_view(session_id)

    recurrence = view["setting_metadata"]["recurrence_mode"]
    assert recurrence["component"] == "recurrence"
    assert recurrence["apply_mode"] == REBUILD_REQUIRED


def test_orchestration_is_read_only_and_defaults_to_ssl_turn(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Orchestration empty",
        profile_id="balanced",
        backend="fixture",
        runtime_mode="live",
        authority_profile_id="autonomous",
    )
    before = controller.sessions.load(session_id)["state"]

    view = controller.session_view(session_id)
    after = controller.sessions.load(session_id)["state"]

    assert view["orchestration"]["state"] == SSL_TURN
    assert before == after


def test_assisted_mature_seed_maps_to_human_turn(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Assisted handoff",
        profile_id="balanced",
        backend="fixture",
        runtime_mode="live",
        authority_profile_id="assisted",
    )
    controller.send_turn(session_id, "What Privacy Gap Remains?")
    controller.send_turn(session_id, "What Privacy Gap Remains?")
    controller.send_turn(session_id, "What Privacy Gap Remains?")

    view = controller.session_view(session_id)
    mature = [
        seed for seed in view["seeds"]
        if int(seed.get("occurrence_count", 0))
        >= int(view["core_config"].get("min_occurrences_for_gate", 3))
    ]
    assert mature
    assert any(seed["orchestration"]["state"] == HUMAN_TURN for seed in mature)
    assert view["orchestration"]["state"] == HUMAN_TURN


def test_promoted_authorized_seed_maps_to_optional_review() -> None:
    orchestration = derive_seed_orchestration(
        {
            "id": "ss_authorized",
            "status": "PROMOTED",
            "blocking": False,
            "current_gate_authorized": True,
            "occurrence_count": 3,
            "evidence_count": 0,
        },
        authority_profile_id="autonomous",
        gate_policy_id="exploratory",
        recurrence_threshold=3,
    )

    assert orchestration["state"] == OPTIONAL_REVIEW
    assert orchestration["required_action"] is None
    assert orchestration["component"] == "point_of_use_authorization"


def test_blocking_contradiction_maps_to_blocked(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Blocked orchestration",
        profile_id="balanced",
        backend="fixture",
        runtime_mode="live",
    )
    controller.send_turn(session_id, "What Privacy Gap Remains?")
    view = controller.session_view(session_id)
    seed_id = str(view["seeds"][0]["id"])
    controller.falsify_seed(session_id, seed_id)

    blocked_view = controller.session_view(session_id)
    blocked = next(seed for seed in blocked_view["seeds"] if str(seed["id"]) == seed_id)
    assert blocked["orchestration"]["state"] == BLOCKED
    assert blocked["orchestration"]["required_action"] == "resolve_contradiction"
    assert blocked_view["orchestration"]["state"] == BLOCKED


def test_legacy_self_reinforcement_control_maps_to_revision_only(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Legacy revision adapter",
        profile_id="balanced",
        backend="fixture",
        runtime_mode="live",
    )

    view = controller.update_session_self_reinforcement(
        session_id,
        allow_self_reinforcement=True,
    )
    stored = controller.sessions.load(session_id)

    assert view["allow_same_turn_revision"] is True
    assert view["self_derived_signal_policy"] == "fail_closed"
    assert stored["config"]["allow_same_turn_revision"] is True
    assert stored["config"]["self_derived_signal_policy"] == "fail_closed"
    assert stored["state"]["session_config"]["allow_same_turn_revision"] is True
    assert stored["state"]["session_config"]["self_derived_signal_policy"] == "fail_closed"



def test_revision_model_settings_have_separate_component_metadata() -> None:
    metadata = setting_metadata()

    assert metadata["revision_backend"]["component"] == "same_turn_revision"
    assert metadata["revision_model_id"]["component"] == "same_turn_revision"
