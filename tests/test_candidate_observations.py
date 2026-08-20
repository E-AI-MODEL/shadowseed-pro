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
