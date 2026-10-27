"""No-network tests: blind phase one never receives treatment keys."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from test_g0_multicase_real_ab import FakeProvider, fixture
from shadowseed_research.benchmark.g0_multicase_real_ab import run_study
from shadowseed_research.benchmark.g0_next_seed_hidden_review import (
    BLIND_SCHEMA, OWNER_SCHEMA, create_seed_hidden_review,
)


def observed():
    return run_study(
        fixture(),
        lambda cid: FakeProvider(
            cid, no_birth=cid.endswith("06"),
            fail_at=8 if cid.endswith("02") else None,
        ),
    )


def stable_ids():
    counter = iter(f"pseudonym-{i:03d}" for i in range(200))
    return lambda: next(counter)


def test_seed_hidden_first_phase_retains_longitudinal_questions_and_census():
    d = observed()
    blind, owner = create_seed_hidden_review(
        d, shuffle=lambda items: items.reverse(), new_id=stable_ids(),
    )
    assert blind["schema"] == BLIND_SCHEMA
    assert owner["schema"] == OWNER_SCHEMA
    assert blind["G0"] == owner["G0"] == "NOT_PASSED"
    assert not blind["human_review_received"]
    assert blind["semantic_output_can_still_hint_at_arm"]
    assert blind["phase1_case_count"] == 4
    assert blind["study_cases_total_including_failures"] == 6
    assert len(owner["case_census_including_failures"]) == 6
    assert sum(x["included_in_first_phase"]
               for x in owner["case_census_including_failures"]) == 4
    assert {x["original_status"]
            for x in owner["case_census_including_failures"]} == {
                "completed_exploratory_pair",
                "completed_no_T0_seed_no_AB_opportunity",
                "failed_incomplete_not_zero_effect",
            }
    assert owner["release_only_after_independent_phase1_reviews"]
    all_source_seeds = [
        x["first_seed"]["text"] for x in d["cases"]
        if x.get("first_seed") is not None
    ]
    blind_text = json.dumps(blind, ensure_ascii=False)
    for seed in all_source_seeds:
        assert seed not in blind_text
    for name in (
        "first_seed_text_owner_only", "source_t0_first_seed",
        "ordinary_note", "real_arm", "research_seed_exposure",
        "parser_status", "owner_track_mapping",
    ):
        assert name not in blind_text
    for group in blind["phase1_groups"]:
        assert "BEGIN FICTIEVE ONDERZOEKSSITUATIE" in group[
            "common_case_without_seed_or_ordinary_note"
        ]["canonical_T0_user_input_verbatim"]
        assert len(group["randomly_pseudonymized_tracks"]) == 2
        for track in group["randomly_pseudonymized_tracks"]:
            assert track["track_id"] in owner["owner_track_mapping"]
            assert [x["turn"] for x in track["two_turn_chain"]] == [1, 2]
            assert all(x["external_research_action_executed"] is False
                       for x in track["two_turn_chain"])
            assert all(
                all(value is None for value in x["reviewer_1"].values())
                and all(value is None for value in x["reviewer_2"].values())
                for x in track["two_turn_chain"]
            )
    assert len(owner["owner_track_mapping"]) == 8


def test_blind_does_not_change_any_original_model_output():
    d = observed()
    before = deepcopy(d)
    blind, owner = create_seed_hidden_review(
        d, shuffle=lambda items: None, new_id=stable_ids(),
    )
    assert d == before
    for track_id, reference in owner["owner_track_mapping"].items():
        src = next(x for x in d["cases"]
                   if x["case_id"] == reference["case_id"])
        ref_text = [
            turn["research_arms"][reference["real_arm"]]["text"]
            for turn in src["turns"][1:]
        ]
        review_track = next(t for g in blind["phase1_groups"]
                            for t in g["randomly_pseudonymized_tracks"]
                            if t["track_id"] == track_id)
        assert [z["model_output_unedited"]
                for z in review_track["two_turn_chain"]] == ref_text


def test_literal_seed_leak_in_common_context_kept_in_census_not_achieved_blind():
    d = observed()
    case = next(c for c in d["cases"]
                if c["status"] == "completed_exploratory_pair")
    case["turns"][0]["user_input"] += " " + case["first_seed"]["text"]
    blind, owner = create_seed_hidden_review(
        d, shuffle=lambda items: None, new_id=stable_ids(),
    )
    row = next(c for c in owner["case_census_including_failures"]
               if c["case_id"] == case["case_id"])
    assert row["included_in_first_phase"] is False
    assert row["first_phase_exclusion_reason"] == (
        "source_candidate_literal_already_in_common_context"
    )
    assert blind["study_cases_total_including_failures"] == 6
    assert blind["phase1_case_count"] == 3


@pytest.mark.parametrize("tamper", [
    "false_g0", "missing_arm", "duplicate_case", "wrong_census",
    "missing_seed", "missing_raw_T0",
])
def test_reject_fabricated_or_incomplete_blind_evidence(tamper):
    d = observed()
    case = next(c for c in d["cases"]
                if c["status"] == "completed_exploratory_pair")
    if tamper == "false_g0":
        d["G0"] = "PASSED"
    elif tamper == "missing_arm":
        case["turns"][2]["research_arms"].pop("B")
    elif tamper == "duplicate_case":
        d["cases"][1]["case_id"] = d["cases"][0]["case_id"]
    elif tamper == "wrong_census":
        d["study_counts"]["case_pairs_completed"] += 1
    elif tamper == "missing_seed":
        case["first_seed"] = None
    elif tamper == "missing_raw_T0":
        case["turns"][0].pop("user_input")
    with pytest.raises(ValueError):
        create_seed_hidden_review(
            d, shuffle=lambda items: None, new_id=stable_ids(),
        )


def test_duplicate_pseudonym_fails_closed():
    with pytest.raises(ValueError, match="duplicated"):
        create_seed_hidden_review(
            observed(),
            new_id=lambda: "same",
            shuffle=lambda items: None,
        )
