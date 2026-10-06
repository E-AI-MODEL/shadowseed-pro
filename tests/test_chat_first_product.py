from __future__ import annotations

import json

import pytest

from shadowseed.adapters.embedding import SUPPORTED_EMBEDDING_BACKENDS

from shadowseed.application.comparison import ComparisonService
from shadowseed.application.inspection import InspectionService
from shadowseed.application.models import SessionConfig
from shadowseed.application.scenarios import parse_scenario
from shadowseed.application.sessions import service_for_workspace
from shadowseed.authority_profiles import resolve_authority_runtime
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


def test_workbench_uses_canonical_embedding_backend_registry() -> None:
    assert WorkbenchController.embedding_backends() == SUPPORTED_EMBEDDING_BACKENDS


def test_real_model_product_default_uses_semantic_embedding() -> None:
    assert WorkbenchController.default_embedding_backend("fixture") == "lexical"
    assert WorkbenchController.default_embedding_backend("ollama") == "ollama"
    assert WorkbenchController.default_embedding_model("ollama") == "embeddinggemma"
    assert WorkbenchController.default_embedding_model("sentence-transformers") is None
    assert WorkbenchController.default_embedding_backend("hf-transformers") == "sentence-transformers"
    assert WorkbenchController.default_embedding_backend("openai") == "openai"


def test_optional_provider_availability_is_runtime_scoped(monkeypatch) -> None:
    available = {"openai"}

    monkeypatch.setattr(
        "shadowseed.workbench.controller.find_spec",
        lambda module: object() if module in available else None,
    )

    assert WorkbenchController.backend_available("fixture") is True
    assert WorkbenchController.backend_available("ollama") is True
    assert WorkbenchController.backend_available("openai") is True
    assert WorkbenchController.backend_available("hf-transformers") is False


def test_ollama_workbench_session_persists_resolved_embedding_identity(
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setattr(
        "shadowseed.adapters.ollama_client.OllamaClient.embed",
        lambda self, text: [[1.0, 0.0, 0.0]],
    )
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Ollama embedding provenance",
        profile_id="balanced",
        backend="ollama",
        model_id="qwen3:8b",
        runtime_mode="live",
    )

    stored = controller.sessions.load(session_id)

    assert stored["config"]["embedding_backend"] == "ollama"
    assert stored["config"]["embedding_model"] == "embeddinggemma"


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
    assert report["comparison_kind"] == "same_history_no_ssl_vs_ssl"
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
    assert comparison["comparison_kind"] == "same_history_no_ssl_vs_ssl"
    assert {comparison["candidate_a_label"], comparison["candidate_b_label"]} == {
        "ssl_off",
        "ssl_on",
    }
    assert comparison["control_history_isolated"] is False
    assert comparison["control_state_isolated"] is True
    assert comparison["control_transport"] == "role_structured_chat"
    assert comparison["question"] == "What should I consider next?"


def test_default_live_ab_started_late_does_not_replay_history(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Late same-turn control", profile_id="demo")

    sessions.run_turn(session_id, "First user question")
    sessions.run_turn(session_id, "Second user question")
    report = sessions.run_turn(
        session_id,
        "Third user question",
        compare_without_ssl=True,
    )
    stored = sessions.load(session_id)

    assert report["comparison_kind"] == "same_history_no_ssl_vs_ssl"
    assert report["comparison_control_replayed_turns"] == 0
    assert report["comparison_control_history_turns_before"] == 2
    assert report["comparison_control_transport"] == "role_structured_chat"
    assert stored["state"]["vanilla_history"] == []


def test_live_ab_started_late_replays_only_user_questions_into_vanilla_history(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Late vanilla control", profile_id="demo")

    sessions.run_turn(session_id, "First user question")
    sessions.run_turn(session_id, "Second user question")
    report = sessions.run_turn(
        session_id,
        "Third user question",
        compare_without_ssl=True,
        comparison_mode="longitudinal",
    )
    stored = sessions.load(session_id)
    vanilla_history = stored["state"]["vanilla_history"]

    assert report["comparison_control_history_isolated"] is True
    assert report["comparison_control_transport"] == "role_structured_chat"
    assert report["comparison_control_replayed_turns"] == 2
    assert report["comparison_control_history_turns_before"] == 2
    assert [item["question"] for item in vanilla_history] == [
        "First user question",
        "Second user question",
        "Third user question",
    ]
    assert len(vanilla_history) == 3


def test_live_turn_without_requested_control_does_not_pretend_to_be_comparable(tmp_path) -> None:
    sessions = service_for_workspace(tmp_path / "workspace")
    session_id = sessions.create_session(title="Normal chat", profile_id="demo")
    sessions.run_turn(session_id, "Normal user message")

    with pytest.raises(ValueError, match="no stored no-SSL control"):
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



def test_assisted_exploratory_runtime_does_not_request_proactive_review() -> None:
    runtime = resolve_authority_runtime(
        "assisted",
        runtime_mode="evaluation",
    )

    assert runtime.gate_policy_id == "exploratory"
    assert runtime.proactive_review is False


def test_persisted_assisted_exploratory_gate_does_not_show_review_request() -> None:
    stored = {
        "session_id": "session-exploratory",
        "title": "Assisted exploratory",
        "profile_id": "demo",
        "backend": "fixture",
        "model_id": None,
        "created_at": "2026-01-01T00:00:00",
        "updated_at": "2026-01-01T00:00:00",
        "config": {
            "runtime_mode": "evaluation",
            "authority_profile_id": "assisted",
            "gate_policy_id": "exploratory",
        },
        "state": {
            "session_config": {
                "runtime_mode": "evaluation",
                "authority_profile_id": "assisted",
                "gate_policy_id": "exploratory",
            },
            "manager": {
                "config": {"min_occurrences_for_gate": 3},
                "seeds": [
                    {
                        "id": "ss_001",
                        "text": "Recurring perspective.",
                        "status": "ACTIVE",
                        "occurrence_count": 4,
                    }
                ],
                "contradiction_records": [],
            },
            "turn_reports": [],
            "turn": 0,
        },
    }

    class _Sessions:
        def load(self, _session_id):
            return stored

        def list_feedback(self, _session_id):
            return []

    view = InspectionService(_Sessions()).session_view("session-exploratory")

    assert view["effective_gate_policy_id"] == "exploratory"
    assert view["authority_review_seed_ids"] == []



def test_default_ssl_intensity_keeps_single_seed_surface_cap() -> None:
    assert WorkbenchController.ssl_intensity_settings(50)["surface_top_k"] == 1
    assert WorkbenchController.ssl_intensity_settings(60)["surface_top_k"] == 1
    assert WorkbenchController.ssl_intensity_settings(61)["surface_top_k"] == 2
    assert WorkbenchController.ssl_intensity_settings(90)["surface_top_k"] == 2
    assert WorkbenchController.ssl_intensity_settings(91)["surface_top_k"] == 3


def test_product_sliders_are_independent_and_persisted(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")

    open_id = controller.create_session(
        title="Open gate, no surfacing",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=0,
        gate_strictness=0,
    )
    strict_id = controller.create_session(
        title="Full SSL, strict gate",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=100,
        gate_strictness=100,
    )

    open_stored = controller.sessions.load(open_id)
    strict_stored = controller.sessions.load(strict_id)

    assert open_stored["config"]["ssl_intensity"] == 0
    assert open_stored["config"]["gate_strictness"] == 0
    assert open_stored["config"]["surface_top_k"] == 0
    assert open_stored["config"]["gate_policy_id"] == "exploratory"
    assert open_stored["config"]["min_occurrences_for_gate"] == 1
    assert open_stored["config"]["promotion_threshold"] == 0.2

    assert strict_stored["config"]["ssl_intensity"] == 100
    assert strict_stored["config"]["gate_strictness"] == 100
    assert strict_stored["config"]["surface_top_k"] == 3
    assert strict_stored["config"]["gate_policy_id"] == "evidence_backed"
    assert strict_stored["config"]["authority_profile_id"] == "strict"
    assert strict_stored["config"]["min_occurrences_for_gate"] == 4
    assert strict_stored["config"]["min_evidence_for_gate"] == 3
    assert strict_stored["config"]["promotion_threshold"] == 0.6
    assert strict_stored["config"]["validation_increment"] == 0.2

    open_view = controller.session_view(open_id)
    strict_view = controller.session_view(strict_id)
    assert open_view["ssl_intensity"] == 0
    assert open_view["gate_strictness"] == 0
    assert strict_view["ssl_intensity"] == 100
    assert strict_view["gate_strictness"] == 100


def test_gate_zero_promotes_first_observation_but_ssl_zero_never_surfaces(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Open gate observation only",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=0,
        gate_strictness=0,
    )

    first = controller.send_turn(session_id, "What important perspective could be missing?")
    assert first["report"]["surfaced_seed_ids"] == []
    assert any(seed["status"] == "PROMOTED" for seed in first["session"]["seeds"])

    second = controller.send_turn(session_id, "What important perspective could be missing again?")
    assert second["report"]["surfaced_seed_ids"] == []


def test_gate_hundred_requires_three_verified_sources_without_hidden_recurrence_gate(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Strict Gate",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=100,
        gate_strictness=100,
    )

    controller.ingest_sources(
        session_id,
        pasted_text="Alpha provides a recurring explanatory perspective.",
    )

    view = controller.session_view(session_id)
    seed = max(view["seeds"], key=lambda item: int(item.get("occurrence_count", 0)))
    seed_id = seed["id"]
    recurrence_threshold = int(view["core_config"]["min_occurrences_for_gate"])
    assert recurrence_threshold == 4
    assert int(seed["occurrence_count"]) < recurrence_threshold
    assert seed["status"] != "PROMOTED"

    for index in range(2):
        result = controller.submit_verified_evidence(
            session_id,
            seed_id,
            source_ref=f"reviewer:strict:{index}",
            note="Independent verified source.",
            operator_verified=True,
        )
        assert result["status_after"] != "PROMOTED"

    final = controller.submit_verified_evidence(
        session_id,
        seed_id,
        source_ref="reviewer:strict:2",
        note="Third independent verified source.",
        operator_verified=True,
    )

    assert final["status_after"] == "PROMOTED"
    assert final["evidence_count"] == 3



def test_regie_controls_reconfigure_existing_chat_without_losing_state(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Live Regie",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=100,
        gate_strictness=100,
        allow_self_reinforcement=False,
    )

    controller.send_turn(session_id, "Remember this conversation state.")
    before = controller.sessions.load(session_id)
    history_before = list(before["state"]["history"])
    seeds_before = list(before["state"]["manager"]["seeds"])

    view = controller.update_session_controls(
        session_id,
        ssl_intensity=0,
        gate_strictness=0,
        allow_self_reinforcement=True,
    )
    stored = controller.sessions.load(session_id)

    assert view["ssl_intensity"] == 0
    assert view["gate_strictness"] == 0
    assert view["allow_self_reinforcement"] is True

    assert stored["config"]["ssl_intensity"] == 0
    assert stored["config"]["gate_strictness"] == 0
    assert stored["config"]["allow_self_reinforcement"] is True
    assert stored["config"]["surface_top_k"] == 0
    assert stored["config"]["gate_policy_id"] == "exploratory"
    assert stored["config"]["min_occurrences_for_gate"] == 1

    state_config = stored["state"]["session_config"]
    assert state_config["surface_top_k"] == 0
    assert state_config["gate_policy_id"] == "exploratory"
    assert state_config["authority_profile_id"] == "autonomous"
    assert state_config["allow_self_reinforcement"] is True
    assert stored["state"]["manager"]["config"]["min_occurrences_for_gate"] == 1

    assert stored["state"]["history"] == history_before
    assert stored["state"]["manager"]["seeds"] == seeds_before



def test_regie_reconfiguration_does_not_rehydrate_model_backend() -> None:
    from pathlib import Path

    source = Path("src/shadowseed/application/sessions.py").read_text(encoding="utf-8")
    start = source.index("def update_controls(")
    end = source.index("@staticmethod", start)
    body = source[start:end]

    assert "ShadowChatSession.from_state" not in body
    assert "save_session_configuration" in body



def test_loop_only_update_preserves_legacy_custom_regie(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Legacy-style custom Regie",
        profile_id="balanced",
        backend="fixture",
    )

    before = controller.sessions.load(session_id)
    config_before = dict(before["config"])
    state_config_before = dict(before["state"]["session_config"])
    manager_config_before = dict(before["state"]["manager"]["config"])

    assert config_before["ssl_intensity"] is None
    assert config_before["gate_strictness"] is None

    view = controller.update_session_self_reinforcement(
        session_id,
        allow_self_reinforcement=True,
    )
    after = controller.sessions.load(session_id)

    assert view["allow_self_reinforcement"] is True
    assert after["config"]["ssl_intensity"] is None
    assert after["config"]["gate_strictness"] is None
    assert after["config"]["surface_threshold"] == config_before["surface_threshold"]
    assert after["config"]["surface_top_k"] == config_before["surface_top_k"]
    assert after["config"]["gate_policy_id"] == config_before["gate_policy_id"]
    assert after["state"]["session_config"]["surface_threshold"] == (
        state_config_before["surface_threshold"]
    )
    assert after["state"]["session_config"]["surface_top_k"] == (
        state_config_before["surface_top_k"]
    )
    assert after["state"]["manager"]["config"] == manager_config_before
    assert after["config"]["allow_self_reinforcement"] is True
    assert after["state"]["session_config"]["allow_self_reinforcement"] is True



def test_shadow_pressure_is_rejected_for_evaluation_sessions(tmp_path) -> None:
    import pytest

    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Evaluation comparison",
        profile_id="demo",
        backend="fixture",
        runtime_mode="evaluation",
    )

    before = controller.sessions.load(session_id)
    with pytest.raises(ValueError, match="available only for live sessions"):
        controller.send_turn(
            session_id,
            "Compare this turn.",
            compare_without_ssl=True,
            comparison_mode="shadow_pressure",
        )
    after = controller.sessions.load(session_id)

    assert after["state"]["history"] == before["state"]["history"]
    assert after["state"]["turn"] == before["state"]["turn"]



def test_tightening_gate_revalidates_existing_promotions_at_use_time(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Tighten current Gate",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=100,
        gate_strictness=0,
    )

    first = controller.send_turn(
        session_id,
        "What important perspective could be missing?",
    )
    promoted = [
        seed for seed in first["session"]["seeds"]
        if seed["status"] == "PROMOTED"
    ]
    assert promoted
    assert any(seed["current_gate_authorized"] is True for seed in promoted)

    tightened = controller.update_session_controls(
        session_id,
        ssl_intensity=100,
        gate_strictness=100,
        allow_self_reinforcement=False,
    )
    historical_promotions = [
        seed for seed in tightened["seeds"]
        if seed["status"] == "PROMOTED"
    ]
    assert historical_promotions
    assert all(
        seed["current_gate_authorized"] is False
        for seed in historical_promotions
    )

    second = controller.send_turn(
        session_id,
        "What important perspective could be missing again?",
    )
    assert second["report"]["surfaced_seed_ids"] == []



def test_tightened_assisted_gate_reviews_historical_promotion(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Historical promotion review",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=0,
        gate_strictness=0,
    )

    for _ in range(3):
        controller.ingest_sources(
            session_id,
            pasted_text="Alpha provides a recurring explanatory perspective.",
        )

    permissive = controller.session_view(session_id)
    promoted = [
        seed for seed in permissive["seeds"]
        if seed["status"] == "PROMOTED"
    ]
    assert promoted
    seed_id = promoted[0]["id"]

    tightened = controller.update_session_controls(
        session_id,
        ssl_intensity=100,
        gate_strictness=60,
        allow_self_reinforcement=False,
    )
    seed = next(item for item in tightened["seeds"] if item["id"] == seed_id)

    assert tightened["authority_profile_id"] == "assisted"
    assert tightened["effective_gate_policy_id"] == "evidence_backed"
    assert seed["current_gate_authorized"] is False
    assert int(seed["occurrence_count"]) >= 3
    assert seed_id in tightened["authority_review_seed_ids"]



def test_source_summary_keeps_review_for_blocked_historical_promotion(tmp_path) -> None:
    controller = WorkbenchController(tmp_path / "workspace")
    session_id = controller.create_session(
        title="Runtime review agreement",
        profile_id="balanced",
        backend="fixture",
        ssl_intensity=0,
        gate_strictness=0,
    )

    for _ in range(3):
        controller.ingest_sources(
            session_id,
            pasted_text="Alpha provides a recurring explanatory perspective.",
        )

    permissive = controller.session_view(session_id)
    seed = next(item for item in permissive["seeds"] if item["status"] == "PROMOTED")
    seed_id = seed["id"]

    tightened = controller.update_session_controls(
        session_id,
        ssl_intensity=100,
        gate_strictness=60,
        allow_self_reinforcement=False,
    )
    assert seed_id in tightened["authority_review_seed_ids"]

    summary = controller.ingest_sources(
        session_id,
        pasted_text="Alpha provides a recurring explanatory perspective.",
    )

    assert seed_id in summary["authority_review_seed_ids"]
    assert seed_id in controller.session_view(session_id)["authority_review_seed_ids"]
