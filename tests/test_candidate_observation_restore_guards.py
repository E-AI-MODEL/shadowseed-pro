from __future__ import annotations

import pytest

from shadowseed.observations import CandidateObservation, CandidateObservationLedger


def test_ssl_exposed_observation_cannot_be_constructed_as_recurrence_eligible() -> None:
    with pytest.raises(ValueError, match="cannot be recurrence-eligible"):
        CandidateObservation(
            observation_id="obs_invalid",
            raw_text="A contaminated candidate.",
            normalized_text="a contaminated candidate.",
            context_ref="turn:1:visible_answer",
            detector_backend="fixture",
            detector_prompt_provenance=None,
            candidate_type="possible_completion",
            ssl_exposed=True,
            surfaced_seed_ids=("seed_1",),
            recurrence_eligible=True,
            created_at="2026-08-19T22:00:00+00:00",
        )


def test_tampered_persisted_contaminated_observation_fails_closed() -> None:
    payload = {
        "schema_version": 1,
        "observations": [
            {
                "observation_id": "obs_tampered",
                "raw_text": "A contaminated candidate.",
                "normalized_text": "a contaminated candidate.",
                "context_ref": "turn:1:visible_answer",
                "detector_backend": "fixture",
                "detector_prompt_provenance": None,
                "candidate_type": "possible_completion",
                "ssl_exposed": True,
                "surfaced_seed_ids": ["seed_1"],
                "recurrence_eligible": True,
                "created_at": "2026-08-19T22:00:00+00:00",
                "legacy_projection": False,
                "schema_version": 1,
            }
        ],
        "links": [],
    }

    with pytest.raises(ValueError, match="cannot be recurrence-eligible"):
        CandidateObservationLedger.from_dict(payload)


def test_unknown_observation_schema_fails_closed() -> None:
    payload = {
        "schema_version": 1,
        "observations": [
            {
                "observation_id": "obs_future",
                "raw_text": "Future record.",
                "normalized_text": "future record.",
                "context_ref": "turn:1:visible_answer",
                "detector_backend": "fixture",
                "detector_prompt_provenance": None,
                "candidate_type": "possible_completion",
                "ssl_exposed": False,
                "surfaced_seed_ids": [],
                "recurrence_eligible": True,
                "created_at": "2026-08-19T22:00:00+00:00",
                "legacy_projection": False,
                "schema_version": 99,
            }
        ],
        "links": [],
    }

    with pytest.raises(ValueError, match="unsupported candidate-observation schema"):
        CandidateObservationLedger.from_dict(payload)
