from __future__ import annotations

from copy import deepcopy
import json
import sqlite3

from shadowseed.storage.integrity import (
    behavior_config_digest,
    behavior_config_epoch,
    behavior_config_projection,
)
from shadowseed.workbench.controller import WorkbenchController


def _behavior_state() -> dict:
    return {
        "session_config": {
            "backend": "fixture",
            "model_id": None,
            "revision_backend": "fixture",
            "revision_model_id": None,
            "max_new_tokens": 700,
            "embedding_backend": "lexical",
            "embedding_model": None,
            "surface_threshold": 0.30,
            "surface_top_k": 2,
            "early_turn_margin": 0.10,
            "early_turn_history": 5,
            "resurface_margin": 0.15,
            "max_seeds_per_turn": 5,
            "recurrence_mode": "cluster",
            "cluster_threshold": None,
            "runtime_mode": "live",
            "gate_policy_id": "evidence_backed",
            "authority_profile_id": "strict",
            "allow_toy_embedder": False,
            "revalidate_current_gate": True,
            "allow_same_turn_revision": False,
            "self_derived_signal_policy": "fail_closed",
        },
        "manager": {
            "config": {
                "trace_start": 2.0,
                "half_life_turns": 2.0794415416798357,
                "dedup_threshold": 0.85,
                "promotion_threshold": 0.5,
                "dormant_threshold": 0.05,
                "validation_increment": 0.2,
                "contradiction_penalty": 0.3,
                "reward_step": 0.1,
                "penalty_step": 0.2,
                "max_trace": 3.0,
                "reactivation_increment": 2.0,
                "min_occurrences_for_gate": 3,
                "min_evidence_for_gate": 2,
                "min_trace_for_gate": 0.5,
                "max_seed_words": 18,
                "dormant_ttl_turns": 5,
                "contradiction_trace_penalty": 0.5,
            }
        },
        "behavior_runtime": {
            "model_roles": {
                "generation": {
                    "backend": "fixture",
                    "model_id": None,
                    "runtime_name": "fixture",
                },
                "revision": {
                    "backend": "fixture",
                    "model_id": None,
                    "runtime_name": "fixture",
                },
            },
            "detector_role": {
                "backend": "fixture",
                "model_id": None,
                "runtime_name": "fixture-detector",
            },
            "prompt_contracts": {
                "answer_generation": {
                    "prompt_id": "answer_generation_v1",
                    "prompt_version": "1",
                    "component": "answer_generation",
                    "template_sha256": "a" * 64,
                    "input_contract": ["current_question"],
                    "output_contract": "draft_or_final_answer",
                }
            },
        },
    }


def test_material_behavior_change_produces_new_digest_and_epoch() -> None:
    before = _behavior_state()
    after = deepcopy(before)
    after["session_config"]["surface_top_k"] = 4

    assert behavior_config_projection(before) != behavior_config_projection(after)
    assert behavior_config_digest(before) != behavior_config_digest(after)
    assert behavior_config_epoch(before) != behavior_config_epoch(after)


def test_display_only_change_does_not_change_behavior_digest() -> None:
    before = _behavior_state()
    after = deepcopy(before)
    after["title"] = "A different display title"
    after["selected_tab"] = "audit"
    after["operator_note"] = "not behavior configuration"

    assert behavior_config_projection(before) == behavior_config_projection(after)
    assert behavior_config_digest(before) == behavior_config_digest(after)


def test_turn_keeps_original_behavior_digest_after_reconfigure(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Behavior epoch turns",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )

    controller.send_turn(session_id, "What Privacy Gap Remains?")
    first_view = controller.session_view(session_id)
    first_report = dict(first_view["turn_reports"][0])
    first_digest = first_report["behavior_config_digest"]

    controller.update_session_advanced(
        session_id,
        settings={"surface_top_k": 4},
    )
    controller.send_turn(session_id, "Which boundary matters next?")

    view = controller.session_view(session_id)
    reports = list(view["turn_reports"])
    assert reports[0]["behavior_config_digest"] == first_digest
    assert reports[1]["behavior_config_digest"] != first_digest
    assert reports[1]["behavior_config_digest"] == view["behavior_config_digest"]

    projection = reports[1]["behavior_config"]
    assert projection["projection_version"] == 1
    assert projection["model_roles"]["generation"]["backend"] == "fixture"
    assert projection["model_roles"]["revision"]["backend"] == "fixture"
    assert projection["detector_role"]["backend"] == "fixture"
    assert "detector_current_pair" in projection["prompt_contracts"]
    assert projection["manager_config"]["dedup_threshold"] == 0.85
    assert projection["manager_config"]["max_seed_words"] == 18


def test_reconfigure_ledger_commits_behavior_projection(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Behavior epoch ledger",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )

    controller.update_session_advanced(
        session_id,
        settings={"surface_top_k": 3},
    )
    stored = controller.sessions.load(session_id)
    expected_state = dict(stored["state"])

    with sqlite3.connect(controller.workspace.paths.database) as connection:
        row = connection.execute(
            "SELECT payload_json FROM production_ledger "
            "WHERE session_id = ? AND event_type = 'runtime.session_reconfigure' "
            "ORDER BY sequence_no DESC LIMIT 1",
            (session_id,),
        ).fetchone()

    assert row is not None
    payload = json.loads(row[0])
    assert payload["behavior_config"] == behavior_config_projection(expected_state)
    assert payload["behavior_config_digest"] == behavior_config_digest(expected_state)
    assert payload["behavior_config_epoch"] == behavior_config_epoch(expected_state)
    assert payload["runtime_commit"]["behavior_config_digest"] == payload[
        "behavior_config_digest"
    ]
