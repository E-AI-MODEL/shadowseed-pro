"""Three-track seed-hidden review packet for the NEW five-turn RF pilot.

This is presentation and identity separation, NOT automated human review,
scientific novelty assessment, G0 approval, or a hidden confirmation set.
The generated text itself can hint at A/B/C, even without arm labels.
Original public case content cannot be retroactively made independent.
"""
from __future__ import annotations

import secrets
from typing import Any, Callable

from shadowseed_research.benchmark.g0_late_birth_real_rf import (
    ARMS, CASE_COUNT, OUTPUT_SCHEMA,
)

BLIND_SCHEMA = "shadowseed-g0-late-birth-three-arm-blind-v1"
OWNER_SCHEMA = "shadowseed-g0-late-birth-owner-unblind-v1"


def _review_blank() -> dict[str, Any]:
    return {
        "different_inquiry_family": None,
        "independent_test_described": None,
        "second_inquiry_depends_on_first": None,
        "repetition_without_new_test": None,
        "not_judgeable": None,
        "concrete_evidence_for_decision": None,
    }


def create_blinded_triplets(
    study: dict[str, Any],
    *,
    shuffle: Callable[[list], None] | None = None,
    new_id: Callable[[], str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if (
        not isinstance(study, dict)
        or study.get("schema") != OUTPUT_SCHEMA
        or study.get("G0") != "NOT_PASSED"
        or study.get("independent_semantic_review_completed") is not False
        or study.get("Q2_later_world_expansion_proven") is not False
        or study.get("real_RI_actions_executed") is not False
    ):
        raise ValueError("not a valid unreviewed RF observation")
    cases, counts = study.get("cases"), study.get("counts")
    if (
        not isinstance(cases, list) or len(cases) != CASE_COUNT
        or not isinstance(counts, dict)
        or counts.get("case_slots_attempted") != CASE_COUNT
        or len({x.get("case_id") for x in cases}) != CASE_COUNT
    ):
        raise ValueError("wrong original case census")
    if (
        sum(c.get("status") == "complete_six_inquiry_records" for c in cases)
        != counts.get("six_inquiry_record_cases")
        or sum(c.get("status") == "no_eligible_birth_not_zero_effect" for c in cases)
        != counts.get("no_eligible_birth")
        or sum(c.get("status") == "failed_incomplete_not_zero_effect" for c in cases)
        != counts.get("failed_or_incomplete")
    ):
        raise ValueError("case census cannot be silently reduced")
    shuffle_fn = shuffle if shuffle is not None else secrets.SystemRandom().shuffle
    id_fn = new_id if new_id is not None else lambda: secrets.token_hex(12)
    tokens: set[str] = set()

    def token() -> str:
        t = id_fn()
        if not isinstance(t, str) or not t or t in tokens:
            raise ValueError("missing or duplicate review pseudonym")
        tokens.add(t)
        return t

    groups = []
    census = []
    mapping = {}
    for case in cases:
        cid = case["case_id"]
        status = case["status"]
        row = {
            "case_id_owner_only": cid,
            "status": status,
            "included_in_phase1": False,
            "not_a_measured_zero_effect": status != "complete_six_inquiry_records",
            "exclusion": None,
        }
        census.append(row)
        if status != "complete_six_inquiry_records":
            row["exclusion"] = status
            continue
        cohort, turns = case.get("cohort"), case.get("turns")
        if not isinstance(cohort, dict) or not isinstance(turns, list):
            raise ValueError("complete case lacks canonical birth or dialogue")
        first_seed = cohort.get("seed_text_owner_only")
        birth = cohort.get("selected_birth_turn")
        if (
            not isinstance(first_seed, str) or not first_seed.strip()
            or type(birth) is not int or birth not in (0, 1, 2)
            or len(turns) != 5
            or [x.get("turn") for x in turns] != list(range(5))
            or cohort.get("status") != "TWO_CANONICAL_FOLLOWUPS_NO_Q2_CLAIM"
            or len(cohort.get("canonical_followups", [])) < 2
        ):
            raise ValueError("wrong claimed complete longitudinal cohort")
        inquiry_indices = (birth + 1, birth + 2)
        for t in inquiry_indices:
            if set(turns[t].get("research_arms", {})) != set(ARMS):
                raise ValueError("missing arm of declared full inquiry")
        common = {
            "initial_context_and_original_T0_input": turns[0].get("user_input"),
            "ordinary_dialogue_unaltered": [{
                "turn": t["turn"],
                "user_input": t.get("user_input"),
                "ordinary_host_answer": t.get("host_answer"),
            } for t in turns[:inquiry_indices[-1] + 1]],
            "inquiry_turn_indices": list(inquiry_indices),
            "feedback_regime": "RF",
            "no_real_inquiry_action_executed": True,
        }
        if not isinstance(common["initial_context_and_original_T0_input"], str):
            raise ValueError("missing complete initial case")
        if first_seed in str(common):
            row["exclusion"] = "source_seed_literal_in_common_context"
            continue
        group_id = token()
        tracks = []
        for arm in ARMS:
            track_id = token()
            own = []
            for t in inquiry_indices:
                item = turns[t]["research_arms"][arm]
                if (
                    not isinstance(item.get("text"), str)
                    or not item["text"].strip()
                    or not isinstance(item.get("prompt_sha256"), str)
                ):
                    raise ValueError("empty or untraceable research output")
                own.append({
                    "turn": t, "model_output_unmodified": item["text"],
                    "external_action_executed": False,
                    "reviewer_1": _review_blank(),
                    "reviewer_2": _review_blank(),
                })
            tracks.append({"anonymous_track": track_id, "two_post_birth_inquiry_turns": own})
            mapping[track_id] = {
                "case_id_owner_only": cid, "group_id": group_id,
                "arm_owner_only": arm, "seed_text_owner_only": first_seed,
                "birth_turn_owner_only": birth,
                "prompt_sha256_by_turn": [
                    turns[t]["research_arms"][arm]["prompt_sha256"]
                    for t in inquiry_indices
                ],
            }
        shuffle_fn(tracks)
        groups.append({
            "anonymous_group": group_id,
            "common_context_without_seed_or_arm_labels": common,
            "three_randomized_longitudinal_tracks": tracks,
        })
        row["included_in_phase1"] = True
    shuffle_fn(groups)
    blind = {
        "schema": BLIND_SCHEMA,
        "G0": "NOT_PASSED",
        "public_cases_not_independent_holdout": True,
        "arm_label_and_seed_reference_hidden": True,
        "model_text_can_unblind_by_content": True,
        "human_ratings_received": False,
        "human_identity_authenticated": False,
        "original_case_count_with_failures": len(cases),
        "phase1_reviewable_groups": len(groups),
        "groups": groups,
        "no_Q2_or_RI_effect_proven": True,
    }
    owner = {
        "schema": OWNER_SCHEMA,
        "G0": "NOT_PASSED",
        "release_only_after_two_independent_phase1_human_reviews": True,
        "no_automatic_human_review_or_release": True,
        "original_case_census_including_failures": census,
        "anonymous_track_to_real_arm": mapping,
        "independent_semantic_review_completed": False,
    }
    return blind, owner
