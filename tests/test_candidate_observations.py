from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from shadowseed.observations import CandidateObservationLedger


def test_contaminated_observation_is_immutable_and_never_recurrence_eligible() -> None:
    ledger = CandidateObservationLedger()
    created = ledger.record_batch(
        ["A downstream fairness implication."],
        context_ref="turn:4:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance="generative:v1",
        candidate_type="possible_completion",
        ssl_exposed=True,
        surfaced_seed_ids=["seed_privacy"],
        created_at="2026-08-19T20:00:00+00:00",
    )

    assert len(created) == 1
    observation = created[0]
    assert observation.ssl_exposed is True
    assert observation.recurrence_eligible is False
    assert observation.surfaced_seed_ids == ("seed_privacy",)
    with pytest.raises(FrozenInstanceError):
        observation.recurrence_eligible = True  # type: ignore[misc]


def test_recording_observation_has_no_seed_or_authority_state() -> None:
    ledger = CandidateObservationLedger()
    ledger.record_batch(
        ["A possible missing boundary."],
        context_ref="turn:1:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance=None,
        candidate_type="possible_completion",
        ssl_exposed=False,
        created_at="2026-08-19T20:00:00+00:00",
    )

    payload = ledger.to_dict()
    text = repr(payload).lower()
    for forbidden in ("weight", "evidence_count", "authority_version", "gate_decision"):
        assert forbidden not in text
    assert payload["observations"][0]["recurrence_eligible"] is True


def test_later_clean_exact_match_appends_link_without_mutating_old_observation() -> None:
    ledger = CandidateObservationLedger()
    contaminated = ledger.record_batch(
        ["Privacy needs a retention boundary."],
        context_ref="turn:2:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance=None,
        candidate_type="possible_completion",
        ssl_exposed=True,
        surfaced_seed_ids=["seed_1"],
        created_at="2026-08-19T20:00:00+00:00",
    )[0]
    old_snapshot = contaminated.to_dict()

    clean = ledger.record_batch(
        ["  Privacy needs a retention boundary.  "],
        context_ref="turn:5:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance=None,
        candidate_type="possible_completion",
        ssl_exposed=False,
        created_at="2026-08-19T20:05:00+00:00",
    )[0]

    assert contaminated.to_dict() == old_snapshot
    assert clean.recurrence_eligible is True
    assert len(ledger.links) == 1
    link = ledger.links[0]
    assert link.contaminated_observation_id == contaminated.observation_id
    assert link.clean_observation_id == clean.observation_id


def test_semantically_different_clean_observation_is_not_claimed_independent_match() -> None:
    ledger = CandidateObservationLedger()
    ledger.record_batch(
        ["Privacy needs a retention boundary."],
        context_ref="turn:2:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance=None,
        candidate_type="possible_completion",
        ssl_exposed=True,
        surfaced_seed_ids=["seed_1"],
        created_at="2026-08-19T20:00:00+00:00",
    )
    ledger.record_batch(
        ["Fairness may depend on cohort composition."],
        context_ref="turn:5:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance=None,
        candidate_type="possible_completion",
        ssl_exposed=False,
        created_at="2026-08-19T20:05:00+00:00",
    )

    assert ledger.links == ()


def test_roundtrip_preserves_observation_and_link_provenance() -> None:
    ledger = CandidateObservationLedger()
    ledger.record_batch(
        ["Privacy needs a retention boundary."],
        context_ref="turn:2:visible_answer",
        detector_backend="ollama:qwen",
        detector_prompt_provenance="generative:sha256:abc",
        candidate_type="possible_completion",
        ssl_exposed=True,
        surfaced_seed_ids=["seed_1"],
        created_at="2026-08-19T20:00:00+00:00",
    )
    ledger.record_batch(
        ["Privacy needs a retention boundary."],
        context_ref="turn:5:visible_answer",
        detector_backend="ollama:qwen",
        detector_prompt_provenance="generative:sha256:abc",
        candidate_type="possible_completion",
        ssl_exposed=False,
        created_at="2026-08-19T20:05:00+00:00",
    )

    restored = CandidateObservationLedger.from_dict(ledger.to_dict())
    assert restored.to_dict() == ledger.to_dict()


def test_legacy_projection_preserves_suppressed_candidates_without_recurrence() -> None:
    ledger = CandidateObservationLedger.project_legacy_turn_reports(
        [
            {
                "turn": 7,
                "surfaced_seed_ids": ["seed_old"],
                "suppressed_self_attributed_candidates": ["A deferred candidate."],
            }
        ]
    )

    assert len(ledger.observations) == 1
    observation = ledger.observations[0]
    assert observation.legacy_projection is True
    assert observation.ssl_exposed is True
    assert observation.recurrence_eligible is False
    assert observation.context_ref == "turn:7:legacy_suppressed_candidate"



def test_v2_self_reinforcement_roundtrip_is_explicit() -> None:
    payload = {
        "schema_version": 2,
        "observations": [
            {
                "observation_id": "obs_v2",
                "raw_text": "A feedback-loop candidate.",
                "normalized_text": "a feedback-loop candidate.",
                "context_ref": "turn:8:visible_answer",
                "detector_backend": "fixture-detector",
                "detector_prompt_provenance": "generative:v2",
                "candidate_type": "possible_completion",
                "ssl_exposed": True,
                "surfaced_seed_ids": ["seed_feedback"],
                "recurrence_eligible": True,
                "created_at": "2026-09-30T00:00:00+00:00",
                "self_reinforcement_allowed": True,
                "legacy_projection": False,
                "schema_version": 2,
            }
        ],
        "links": [],
    }

    restored = CandidateObservationLedger.from_dict(payload)
    observation = restored.observations[0]

    assert observation.schema_version == 2
    assert observation.ssl_exposed is True
    assert observation.recurrence_eligible is True
    assert observation.self_reinforcement_allowed is True
    assert observation.self_derived_policy_id is None
    assert restored.to_dict()["observations"][0]["schema_version"] == 2


def test_v3_self_derived_policy_is_separate_from_revision() -> None:
    ledger = CandidateObservationLedger()
    created = ledger.record_batch(
        ["A model-derived candidate."],
        context_ref="turn:9:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance="current_pair:v0.5",
        candidate_type="possible_completion",
        ssl_exposed=True,
        surfaced_seed_ids=["seed_feedback"],
        created_at="2026-10-02T00:00:00+00:00",
        self_derived_policy_id="fail_closed",
    )

    observation = created[0]
    assert observation.schema_version == 3
    assert observation.ssl_exposed is True
    assert observation.recurrence_eligible is False
    assert observation.self_reinforcement_allowed is False
    assert observation.self_derived_policy_id == "fail_closed"


def test_v3_bounded_self_derived_observation_can_be_retained_explicitly() -> None:
    ledger = CandidateObservationLedger()
    observation = ledger.record_batch(
        ["A bounded experimental candidate."],
        context_ref="turn:10:visible_answer",
        detector_backend="fixture-detector",
        detector_prompt_provenance="current_pair:v0.5",
        candidate_type="possible_completion",
        ssl_exposed=True,
        surfaced_seed_ids=["seed_feedback"],
        created_at="2026-10-02T00:01:00+00:00",
        self_derived_policy_id="bounded_experimental",
    )[0]

    assert observation.recurrence_eligible is True
    assert observation.self_derived_policy_id == "bounded_experimental"
    assert observation.self_reinforcement_allowed is False


def test_packaged_observation_contract_keeps_v1_v2_and_adds_v3() -> None:
    from pathlib import Path
    import json

    data_dir = Path("src/shadowseed/data")
    v1 = json.loads(
        (data_dir / "candidate_observation_schema_v1.json").read_text(encoding="utf-8")
    )
    v2 = json.loads(
        (data_dir / "candidate_observation_schema_v2.json").read_text(encoding="utf-8")
    )
    v3 = json.loads(
        (data_dir / "candidate_observation_schema_v3.json").read_text(encoding="utf-8")
    )

    assert v1["schema_version"] == 1
    assert "ssl_exposed observations are never recurrence-eligible" in v1["observation"]["invariants"]
    assert v2["schema_version"] == 2
    assert "self_reinforcement_allowed" in v2["observation"]["required"]
    assert v2["record_schema_versions_supported"] == [1, 2]
    assert v3["schema_version"] == 3
    assert "self_derived_policy_id" in v3["observation"]["required"]
    assert v3["record_schema_versions_supported"] == [1, 2, 3]
