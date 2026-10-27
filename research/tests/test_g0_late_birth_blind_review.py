"""No-network negative tests for three-arm longitudinal review blinding."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from test_g0_late_birth_real_rf import (
    LateBirthFakeProvider, fixture,
)
from shadowseed_research.benchmark.g0_late_birth_real_rf import run_study
from shadowseed_research.benchmark.g0_late_birth_blind_review import (
    BLIND_SCHEMA, OWNER_SCHEMA, create_blinded_triplets,
)


def sample_study():
    born = {"LB27-C01": 0, "LB27-C03": 1, "LB27-C04": 2}
    return run_study(
        fixture(),
        lambda cid: LateBirthFakeProvider(cid, born_at=born.get(cid)),
        allocation=dict(zip(
            fixture()["case_order"],
            [("A", "B", "C"), ("A", "C", "B"),
             ("B", "A", "C"), ("B", "C", "A"),
             ("C", "A", "B"), ("C", "B", "A")],
        )),
    )


def ids():
    data = iter(f"track-{i:04d}" for i in range(100))
    return lambda: next(data)


def test_seed_hidden_review_preserves_three_full_post_birth_tracks():
    observed = sample_study()
    original = deepcopy(observed)
    blind, owner = create_blinded_triplets(
        observed, shuffle=lambda a: a.reverse(), new_id=ids(),
    )
    assert observed == original
    assert blind["schema"] == BLIND_SCHEMA
    assert owner["schema"] == OWNER_SCHEMA
    assert blind["G0"] == owner["G0"] == "NOT_PASSED"
    assert not blind["human_ratings_received"]
    assert blind["model_text_can_unblind_by_content"]
    assert blind["phase1_reviewable_groups"] == 3
    assert blind["original_case_count_with_failures"] == 6
    assert len(owner["original_case_census_including_failures"]) == 6
    assert len(owner["anonymous_track_to_real_arm"]) == 9
    assert owner["release_only_after_two_independent_phase1_human_reviews"]
    assert owner["no_automatic_human_review_or_release"]
    blind_text = json.dumps(blind, ensure_ascii=False)
    for forbidden in (
        '"seed_text_owner_only"', '"arm_owner_only"',
        '"birth_turn_owner_only"', '"anonymous_track_to_real_arm"',
        '"ordinary_note_owner_only"', '"cohort"',
        '"research_order_first"',
    ):
        assert forbidden not in blind_text
    for group in blind["groups"]:
        tracks = group["three_randomized_longitudinal_tracks"]
        assert len(tracks) == 3
        common = group["common_context_without_seed_or_arm_labels"]
        assert "BEGIN FICTIEVE ONDERZOEKSSITUATIE" in (
            common["initial_context_and_original_T0_input"]
        )
        assert common["no_real_inquiry_action_executed"] is True
        for track in tracks:
            assert len(track["two_post_birth_inquiry_turns"]) == 2
            owner_ref = owner["anonymous_track_to_real_arm"][
                track["anonymous_track"]
            ]
            case = next(c for c in observed["cases"]
                        if c["case_id"] == owner_ref["case_id_owner_only"])
            birth_turn = owner_ref["birth_turn_owner_only"]
            arm = owner_ref["arm_owner_only"]
            expected = [
                case["turns"][t]["research_arms"][arm]["text"]
                for t in (birth_turn + 1, birth_turn + 2)
            ]
            actual = [
                t["model_output_unmodified"]
                for t in track["two_post_birth_inquiry_turns"]
            ]
            assert actual == expected
            assert [t["turn"] for t in track["two_post_birth_inquiry_turns"]] == [
                birth_turn + 1, birth_turn + 2,
            ]
            for t in track["two_post_birth_inquiry_turns"]:
                assert not t["external_action_executed"]
                assert all(x is None for x in t["reviewer_1"].values())
                assert all(x is None for x in t["reviewer_2"].values())
    assert sum(x["included_in_phase1"]
               for x in owner["original_case_census_including_failures"]) == 3


def test_seed_in_common_context_prevents_claim_of_blind_scoring():
    d = sample_study()
    case = next(c for c in d["cases"]
                if c["status"] == "complete_six_inquiry_records")
    case["turns"][0]["user_input"] += " " + case["cohort"]["seed_text_owner_only"]
    blind, owner = create_blinded_triplets(
        d, new_id=ids(), shuffle=lambda a: None,
    )
    row = next(x for x in owner["original_case_census_including_failures"]
               if x["case_id_owner_only"] == case["case_id"])
    assert row["included_in_phase1"] is False
    assert row["exclusion"] == "source_seed_literal_in_common_context"
    assert blind["original_case_count_with_failures"] == 6
    assert blind["phase1_reviewable_groups"] == 2


@pytest.mark.parametrize("tamper", [
    "G0", "q2", "missing_arm", "wrong_census",
    "missing_birth", "duplicate_case", "missing_context",
])
def test_reject_tampered_scientific_claim_or_case_census(tamper):
    d = sample_study()
    case = next(c for c in d["cases"]
                if c["status"] == "complete_six_inquiry_records")
    if tamper == "G0":
        d["G0"] = "PASSED"
    elif tamper == "q2":
        d["Q2_later_world_expansion_proven"] = True
    elif tamper == "missing_arm":
        t = case["cohort"]["selected_birth_turn"] + 1
        case["turns"][t]["research_arms"].pop("B")
    elif tamper == "wrong_census":
        d["counts"]["six_inquiry_record_cases"] += 1
    elif tamper == "missing_birth":
        case["cohort"]["selected_birth_turn"] = None
    elif tamper == "duplicate_case":
        d["cases"][1]["case_id"] = d["cases"][0]["case_id"]
    elif tamper == "missing_context":
        case["turns"][0].pop("user_input")
    with pytest.raises(ValueError):
        create_blinded_triplets(
            d, new_id=ids(), shuffle=lambda a: None,
        )


def test_duplicate_track_pseudonym_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        create_blinded_triplets(
            sample_study(),
            new_id=lambda: "identical",
            shuffle=lambda a: None,
        )
