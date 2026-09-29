from __future__ import annotations

import json

import pytest

from shadowseed.application.comparison import ComparisonService
from shadowseed.application.inspection import InspectionService
from shadowseed.application.models import SessionConfig
from shadowseed.application.scenarios import parse_scenario
from shadowseed.application.sessions import service_for_workspace
from shadowseed.workbench.controller import WorkbenchController


def test_new_application_sessions_default_to_live_ssl(tmp_path) -> None:
    assert SessionConfig().runtime_mode == "live"

    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Normal product chat",
        profile_id="demo",
        backend="fixture",
    )
    stored = controller.sessions.load(session_id)

    assert stored["config"]["runtime_mode"] == "live"
    assert stored["config"]["gate_policy_id"] is None
    assert controller.session_view(session_id)["runtime_mode"] == "live"


def test_real_model_product_default_uses_semantic_embedding() -> None:
    assert WorkbenchController.default_embedding_backend("fixture") == "lexical"
    for backend in ("ollama", "hf-transformers", "openai"):
        assert WorkbenchController.default_embedding_backend(backend) == "sentence-transformers"


def _seed_state(stored: dict) -> list[tuple[str, int, float, float, str]]:
    return sorted(
        (
            str(seed["text"]),
            int(seed["occurrence_count"]),
            float(seed["trace"]),
            float(seed["weight"]),
            str(seed["status"]),
        )
        for seed in stored["state"]["manager"]["seeds"]
    )


def test_live_chat_can_generate_no_ssl_control_without_authored_baseline(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    paired_id = sessions.create_session(title="Paired control", profile_id="demo")
    ordinary_id = sessions.create_session(title="Ordinary control", profile_id="demo")
    question = "What important perspective could be missing?"

    report = sessions.run_turn(
        paired_id,
        question,
        compare_without_ssl=True,
    )
    sessions.run_turn(ordinary_id, question, compare_without_ssl=False)
    paired = sessions.load(paired_id)
    ordinary = sessions.load(ordinary_id)
    persisted_report = paired["state"]["turn_reports"][0]

    assert report["runtime_mode"] == "live"
    assert report["comparison_requested"] is True
    assert report["comparison_kind"] == "paired_live_no_ssl_control"
    assert report["comparison_control_answer"]
    assert report["comparison_ssl_answer"] == report["answer"]
    assert persisted_report["comparison_control_answer"] == report["comparison_control_answer"]
    assert paired["state"]["turn"] == ordinary["state"]["turn"] == 1

    # The extra control generation is presentation-only. Running it must leave
    # exactly the same seed/trace/weight state as an otherwise identical live turn
    # that did not request a control. Cluster recurrence has a separate issue #69.
    assert _seed_state(paired) == _seed_state(ordinary)


def test_controller_returns_ready_to_render_ssl_on_off_comparison(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Compare in chat",
        profile_id="demo",
        backend="fixture",
    )

    result = controller.send_turn(
        session_id,
        "What should I consider next?",
        compare_without_ssl=True,
    )

    comparison = result["comparison"]
    assert comparison is not None
    assert comparison["runtime_mode"] == "live"
    assert comparison["comparison_kind"] == "paired_live_no_ssl_control"
    assert {comparison["candidate_a_label"], comparison["candidate_b_label"]} == {
        "ssl_off",
        "ssl_on",
    }
    assert comparison["question"] == "What should I consider next?"


def test_live_turn_without_requested_control_does_not_pretend_to_be_comparable(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Normal chat", profile_id="demo")
    sessions.run_turn(session_id, "Normal user message")

    with pytest.raises(ValueError, match="no paired no-SSL control"):
        ComparisonService(sessions).compare_turn(session_id, 0)


def test_research_evaluation_still_generates_its_own_control(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(
        title="Research comparison",
        profile_id="demo",
        config=SessionConfig(runtime_mode="evaluation"),
    )

    report = sessions.run_turn(
        session_id,
        "The tester supplies only this question, not a baseline answer.",
        compare_without_ssl=True,
    )
    comparison = ComparisonService(sessions).compare_turn(
        session_id,
        0,
        blinded=False,
    )

    assert report["baseline_answer"]
    assert report["comparison_control_answer"] == report["baseline_answer"]
    assert {comparison["candidate_a_label"], comparison["candidate_b_label"]} == {
        "baseline",
        "shadowseed",
    }


def test_scenario_format_remains_research_legacy_default_evaluation() -> None:
    scenario = parse_scenario(
        json.dumps(
            {
                "title": "Legacy research batch",
                "questions": ["Question one"],
            }
        )
    )
    assert scenario.runtime_mode == "evaluation"
    assert scenario.embedding_backend == "lexical"


def test_authority_profile_is_persisted_without_changing_default_runtime(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Authority profile",
        profile_id="demo",
        authority_profile_id="autonomous",
        backend="fixture",
    )
    stored = controller.sessions.load(session_id)

    assert stored["config"]["runtime_mode"] == "live"
    assert stored["config"]["authority_profile_id"] == "autonomous"


def test_default_authority_profile_is_strict(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Default authority profile",
        profile_id="demo",
        backend="fixture",
    )
    stored = controller.sessions.load(session_id)

    assert stored["config"]["authority_profile_id"] == "strict"



def test_assisted_session_view_exposes_review_requests(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Assisted review",
        profile_id="demo",
        authority_profile_id="assisted",
        backend="fixture",
    )
    chunks = [
        {
            "source_name": "recurrence.txt",
            "context_ref": f"source:recurrence.txt:instance:{index:05d}:chunk:00000",
            "text": "Alpha provides a recurring explanatory perspective.",
        }
        for index in range(6)
    ]

    ingest = controller.sessions.ingest_source_chunks(session_id, chunks)
    view = controller.session_view(session_id)

    assert ingest["authority_runtime"]["gate_policy_id"] == "evidence_backed"
    assert ingest["authority_review_seed_ids"]
    assert view["authority_profile_id"] == "assisted"
    assert view["effective_gate_policy_id"] == "evidence_backed"
    assert set(view["authority_review_seed_ids"]) == set(ingest["authority_review_seed_ids"])

    seed = controller.inspection.seed_view(
        session_id,
        view["authority_review_seed_ids"][0],
    )
    assert seed["review_required"] is True
    assert seed["effective_gate_policy_id"] == "evidence_backed"



def test_assisted_promoted_seed_does_not_return_to_review(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Assisted promoted seed",
        profile_id="demo",
        authority_profile_id="assisted",
        backend="fixture",
    )

    for _ in range(3):
        controller.ingest_sources(
            session_id,
            pasted_text="Alpha provides a recurring explanatory perspective.",
        )

    view = controller.session_view(session_id)
    seed_id = view["authority_review_seed_ids"][0]

    for index in range(2):
        controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=f"reviewer:independent:{index}",
            note="Independently checked.",
            operator_verified=True,
        )
        partial = controller.seed_view(session_id, seed_id)
        assert partial["status"] != "PROMOTED"
        assert partial["review_required"] is True
        assert seed_id in controller.session_view(session_id)["authority_review_seed_ids"]

    controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="reviewer:independent:2",
        note="Independently checked.",
        operator_verified=True,
    )

    promoted = controller.seed_view(session_id, seed_id)
    assert promoted["status"] == "PROMOTED"
    assert promoted["review_required"] is False

    controller.ingest_sources(
        session_id,
        pasted_text="Alpha provides a recurring explanatory perspective.",
    )
    refreshed = controller.session_view(session_id)

    assert seed_id not in refreshed["authority_review_seed_ids"]
    assert controller.seed_view(session_id, seed_id)["review_required"] is False



def test_session_view_exposes_blocking_contradiction_state(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Blocking state",
        profile_id="demo",
        backend="fixture",
        runtime_mode="live",
    )
    result = controller.send_turn(
        session_id,
        "What important perspective could be missing?",
    )
    seed_id = result["session"]["seeds"][0]["id"]

    controller.falsify_seed(session_id, seed_id)
    view = controller.session_view(session_id)
    seed = next(item for item in view["seeds"] if item["id"] == seed_id)

    assert seed["blocking"] is True
    assert "blocks point-of-use influence" in seed["plain_explanation"]



def test_assisted_ingest_summary_preserves_existing_review_request(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Assisted outstanding review",
        profile_id="demo",
        authority_profile_id="assisted",
        backend="fixture",
    )
    recurring = [
        {
            "source_name": "recurrence.txt",
            "context_ref": f"source:recurrence.txt:instance:{index:05d}:chunk:00000",
            "text": "Alpha provides a recurring explanatory perspective.",
        }
        for index in range(6)
    ]

    first = controller.sessions.ingest_source_chunks(session_id, recurring)
    outstanding = set(first["authority_review_seed_ids"])
    assert outstanding

    second = controller.sessions.ingest_source_chunks(
        session_id,
        [
            {
                "source_name": "unrelated.txt",
                "context_ref": "source:unrelated.txt:instance:second:chunk:00000",
                "text": "Omega describes a completely separate operational topic.",
            }
        ],
    )

    assert outstanding.issubset(set(second["authority_review_seed_ids"]))
    assert outstanding.issubset(
        set(controller.session_view(session_id)["authority_review_seed_ids"])
    )



def test_assisted_ingest_summary_keeps_review_after_partial_validation(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Assisted partial validation",
        profile_id="demo",
        authority_profile_id="assisted",
        backend="fixture",
    )

    for _ in range(3):
        controller.ingest_sources(
            session_id,
            pasted_text="Alpha provides a recurring explanatory perspective.",
        )

    view = controller.session_view(session_id)
    seed_id = view["authority_review_seed_ids"][0]

    controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="reviewer:partial:one",
        note="One independent check.",
        operator_verified=True,
    )
    partial = controller.seed_view(session_id, seed_id)
    assert partial["status"] != "PROMOTED"
    assert partial["review_required"] is True

    summary = controller.ingest_sources(
        session_id,
        pasted_text="Omega describes an unrelated operational topic.",
    )
    assert seed_id in summary["authority_review_seed_ids"]



def test_persisted_assisted_review_excludes_cluster_nonrepresentatives() -> None:
    stored = {
        "session_id": "session-1",
        "title": "Persisted cluster review",
        "profile_id": "demo",
        "backend": "fixture",
        "model_id": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "config": {
            "runtime_mode": "live",
            "authority_profile_id": "assisted",
            "gate_policy_id": "evidence_backed",
        },
        "state": {
            "session_config": {
                "runtime_mode": "live",
                "authority_profile_id": "assisted",
                "gate_policy_id": "evidence_backed",
            },
            "manager": {
                "config": {"min_occurrences_for_gate": 3},
                "seeds": [
                    {
                        "id": "ss_001",
                        "text": "Representative perspective.",
                        "status": "ACTIVE",
                        "occurrence_count": 3,
                    },
                    {
                        "id": "ss_002",
                        "text": "Cluster nonrepresentative perspective.",
                        "status": "ACTIVE",
                        "occurrence_count": 3,
                    },
                ],
                "contradiction_records": [],
            },
            "seed_to_cluster": {"ss_001": 0, "ss_002": 0},
            "cluster_rep": {"0": "ss_001"},
            "turn_reports": [],
            "turn": 0,
        },
    }

    class _Sessions:
        def load(self, _session_id):
            return stored

        def list_feedback(self, _session_id):
            return []

    view = InspectionService(_Sessions()).session_view("session-1")

    assert view["authority_review_seed_ids"] == ["ss_001"]
