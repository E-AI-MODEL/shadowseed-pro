"""Offline tests for prospective late real-seed birth and TWO later inquiry turns.

All fake detector/host outputs are only software contract tests, NEVER model
evidence or successful Q1/Q2 results.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest

from test_g0_multicase_real_ab import FakeProvider, RAW_CANDIDATE
from shadowseed_research.benchmark.g0_late_birth_real_rf import (
    ARMS, CASE_COUNT, EMBED_CAP, MODEL_CAP, OUTPUT_CAP, TOKEN_CAP,
    OUTPUT_SCHEMA, INQUIRY_INSTRUCTIONS_V2,
    neutral_placebo, prepare_inquiry_triplet,
    run_case, run_study, validate_design,
)
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    DETECTOR_INSTRUCTIONS, MAX_PROMPT_CHARS,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import _user_input

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "g0_late_birth_rf_v2.json"


def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class LateBirthFakeProvider(FakeProvider):
    def __init__(self, cid, *, born_at=None, malformed=False, fail_at=None):
        super().__init__(
            cid, no_birth=True, malformed=malformed, fail_at=fail_at,
        )
        self.born_at = born_at
        self.model_call_cap = MODEL_CAP
        self.embedding_call_cap = EMBED_CAP
        self.all_token_cap = TOKEN_CAP
        self.output_token_cap = OUTPUT_CAP

    def _post(self, endpoint, payload):
        response = super()._post(endpoint, payload)
        if (
            endpoint == "responses"
            and payload["instructions"] == DETECTOR_INSTRUCTIONS
            and response["status"] == "completed"
        ):
            detected_turn = self.detector_calls - 1
            response["output"][0]["content"][0]["text"] = (
                RAW_CANDIDATE if detected_turn == self.born_at else "NONE"
            )
        return response


def provider(cid, *, born_at=None, malformed=False, fail_at=None):
    return LateBirthFakeProvider(
        cid, born_at=born_at, malformed=malformed, fail_at=fail_at,
    )


def test_new_fixture_is_fixed_public_calibration_and_can_fail():
    d = fixture()
    cases = validate_design(d)
    assert len(cases) == CASE_COUNT == 6
    assert len({x["family"] for x in cases}) == 4
    assert sum(x["selection_window"] == "T0_ONLY" for x in cases) == 2
    assert sum(x["selection_window"] == "T1_T2_ONLY" for x in cases) == 4
    assert all(len(x["turns"]) == 5 for x in cases)
    assert d["outcome"] == "NOT_RUN"
    assert "G0_PASS" in d["prohibited_claims"]
    assert d["status"] == "EXPLORATORY_NOT_G0_APPROVED"


@pytest.mark.parametrize("birth_turn,inquiry_turns", [
    (0, [1, 2]), (1, [2, 3]), (2, [3, 4]),
])
def test_real_engine_birth_at_different_turns_gets_two_later_inquiries(
    birth_turn, inquiry_turns,
):
    cases = validate_design(fixture())
    case = cases[0] if birth_turn == 0 else cases[2]
    p = provider(case["id"], born_at=birth_turn)
    data = run_case(case, p, order=("C", "A", "B"))
    assert data["status"] == "complete_six_inquiry_records"
    assert data["G0"] == "NOT_PASSED"
    assert data["cohort"]["selected_birth_turn"] == birth_turn
    assert data["cohort"]["status"] == "TWO_CANONICAL_FOLLOWUPS_NO_Q2_CLAIM"
    assert data["cohort"]["first_birth"]["raw_detector_item_to_seed_mapping_verified"]
    assert data["cohort"]["first_birth"]["authority_at_birth"]["weight"] == 0
    assert data["cohort"]["first_birth"]["authority_at_birth"]["evidence_count"] == 0
    assert data["cohort"]["selected_seed_id"]
    assert len(data["turns"]) == 5
    assert [x["turn"] for x in data["turns"] if x["research_arms"]] == inquiry_turns
    for idx in inquiry_turns:
        track = data["turns"][idx]["research_arms"]
        assert set(track) == set(ARMS)
        assert all(x["parsed"]["status"] == "valid_questions"
                   for x in track.values())
        assert track["B"]["seed_exposed"] is True
        assert track["C"]["placebo_exposed"] is True
        assert track["A"]["seed_exposed"] is False
        assert all(x["external_test_executed"] is False for x in track.values())
    assert all(x["ordinary_control_identical"] for x in data["turns"])
    assert all(x["seed_state_after_turn"]["weight"] == 0
               for x in data["cohort"]["canonical_followups"])
    assert all(x["product_answer_seed_influence_observed"] is False
               for x in data["cohort"]["canonical_followups"])
    assert not data["real_external_action_performed"]
    assert p.model_calls == 17
    assert 0 < p.embedding_calls <= EMBED_CAP


def test_predeclared_late_window_does_not_relabel_real_T0_birth_as_T1():
    case = validate_design(fixture())[2]
    p = provider(case["id"], born_at=0)
    result = run_case(case, p, order=("A", "B", "C"))
    assert result["status"] == "no_eligible_birth_not_zero_effect"
    assert result["cohort"]["selected_seed_id"] is None
    assert result["cohort"]["all_births_including_ineligible"][0][
        "all_canonical_new_birth_ids"
    ]
    assert result["cohort"]["status"] == "NO_ELIGIBLE_BIRTH_NOT_Q2_ZERO"
    assert not any(x["research_arms"] for x in result["turns"])
    assert p.model_calls == 10


def test_negative_no_birth_is_not_a_zero_Q2_effect():
    case = validate_design(fixture())[-1]
    p = provider(case["id"])
    result = run_case(case, p, order=("B", "A", "C"))
    assert result["status"] == "no_eligible_birth_not_zero_effect"
    assert result["cohort"]["selected_seed_id"] is None
    assert result["cohort"]["status"] == "NO_ELIGIBLE_BIRTH_NOT_Q2_ZERO"
    assert all(x["cohort_turn"] is not None for x in result["turns"])
    assert p.model_calls == 10


def test_arm_isolation_and_own_prior_questions_on_second_round():
    case = validate_design(fixture())[2]
    prior = [
        (_user_input(case, turn), f"Compleet normaal antwoord {i}")
        for i, turn in enumerate(case["turns"][:4])
    ]
    seed = RAW_CANDIDATE
    first = prepare_inquiry_triplet(
        case, prior[:3], "Een neutrale eerdere notitie.", seed, 2,
        birth_turn=1, own_earlier={"A": None, "B": None, "C": None},
    )
    assert len(first["prompts"]) == 3
    a, b, c = [first["prompts"][arm]["prompt"] for arm in ARMS]
    assert seed not in a and seed in b and seed not in c
    assert len(neutral_placebo(seed)) == len(seed)
    assert len(a) < MAX_PROMPT_CHARS
    assert first["placebo_content_or_tokens_not_matched"] is True
    for arm in ARMS:
        assert case["turns"][3]["new_observation"] not in first["prompts"][arm]["prompt"]
        assert case["turns"][2]["new_observation"] in first["prompts"][arm]["prompt"]
    previous = {
        "A": {"status": "valid_none", "tag": "A_QUESTION_ONLY"},
        "B": {"status": "valid_questions", "tag": "B_QUESTION_ONLY"},
        "C": {"status": "valid_questions", "tag": "C_QUESTION_ONLY"},
    }
    second = prepare_inquiry_triplet(
        case, prior, "Een neutrale eerdere notitie.", seed, 3,
        birth_turn=1, own_earlier=previous,
    )
    for arm in ARMS:
        text = second["prompts"][arm]["prompt"]
        assert f"{arm}_QUESTION_ONLY" in text
        assert not any(
            f"{other}_QUESTION_ONLY" in text
            for other in ARMS if other != arm
        )
        assert second["prompts"][arm]["own_prior_questions_only"]
    assert second["G0"] == "NOT_PASSED"


def test_all_original_case_slots_and_actual_calls_retained_with_failure():
    d = fixture()
    born = {"LB27-C01": 0, "LB27-C03": 1, "LB27-C04": 2}
    def factory(cid):
        return provider(
            cid, born_at=born.get(cid),
            fail_at=4 if cid == "LB27-C02" else None,
        )
    snapshots = []
    result = run_study(
        d, factory, on_change=lambda x: snapshots.append(deepcopy(x)),
        allocation={
            cid: order for cid, order in zip(
                d["case_order"],
                [("A", "B", "C"), ("A", "C", "B"),
                 ("B", "A", "C"), ("B", "C", "A"),
                 ("C", "A", "B"), ("C", "B", "A")],
            )
        },
    )
    assert result["G0"] == "NOT_PASSED"
    assert result["status"] == "incomplete_observational_pilot"
    counts = result["counts"]
    assert counts["case_slots_attempted"] == 6
    assert counts["six_inquiry_record_cases"] == 3
    assert counts["no_eligible_birth"] == 2
    assert counts["failed_or_incomplete"] == 1
    assert counts["raw_inquiry_records"] == 18
    assert counts["valid_inquiry_records"] == 18
    assert len(result["cases"]) == 6
    assert result["cases"][1]["error_class"] == "RuntimeError"
    assert result["cases"][1]["no_inference_from_failure"]
    assert result["allocation_frozen_before_first_provider_call"]
    assert len(snapshots) > 60
    assert not result["Q2_later_world_expansion_proven"]


def test_strict_validation_denies_scripted_birth_and_budget_drift():
    d = fixture()
    d["cases"][0]["expected_seed"] = "secret predicted winner"
    with pytest.raises(ValueError):
        validate_design(d)
    d = fixture()
    d["cases"][0]["turns"][0]["new_observation"] = "future contamination"
    with pytest.raises(ValueError):
        validate_design(d)
    d = fixture()
    d["limits"]["max_model_calls_per_case"] = 48
    with pytest.raises(ValueError):
        validate_design(d)
    d = fixture()
    d["case_order"].reverse()
    with pytest.raises(ValueError):
        validate_design(d)


def test_no_previous_question_can_appear_before_real_birth():
    case = validate_design(fixture())[2]
    prior = [
        (_user_input(case, t), "An ordinary response.")
        for t in case["turns"][:3]
    ]
    seed = RAW_CANDIDATE
    with pytest.raises(ValueError):
        prepare_inquiry_triplet(
            case, prior, "shared ordinary note", seed, 2,
            birth_turn=1,
            own_earlier={
                "A": {"tag": "invalid earlier"}, "B": None, "C": None,
            },
        )


def test_parser_failures_are_records_not_scientific_zeroes():
    case = validate_design(fixture())[2]
    p = provider(case["id"], born_at=1, malformed=True)
    result = run_case(case, p, order=("A", "B", "C"))
    assert result["status"] == "complete_six_inquiry_records"
    assert all(item["parsed"]["status"] == "invalid"
               for turn in result["turns"]
               for item in turn["research_arms"].values())
    assert result["cohort"]["status"] == "TWO_CANONICAL_FOLLOWUPS_NO_Q2_CLAIM"
