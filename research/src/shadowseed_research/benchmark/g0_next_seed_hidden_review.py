"""Prepare a seed-hidden first-phase review for a FUTURE G0 RF trial.

This cannot retroactively blind the public, already exposed six-case 2026-10-26
experiment. It does not grant G0, authenticate humans, evaluate novelty or
alter observed facts. The owner key must remain separate until both human
reviewers have independently committed their first-phase assessments.
"""
from __future__ import annotations

from copy import deepcopy
import secrets
from typing import Any, Callable

from shadowseed_research.benchmark.g0_multicase_real_ab import (
    OUTPUT_SCHEMA,
)

BLIND_SCHEMA = "shadowseed-g0-seed-hidden-longitudinal-review-v2"
OWNER_SCHEMA = "shadowseed-g0-owner-only-unblind-map-v2"
_STATUSES = {
    "completed_exploratory_pair",
    "completed_no_T0_seed_no_AB_opportunity",
    "failed_incomplete_not_zero_effect",
}

_REVIEW_FIELDS = (
    "different_inquiry_family",
    "independently_testable_action",
    "T2_depends_on_T1_inquiry",
    "actually_executed_external_result",
    "inconclusive_or_not_scorable",
    "reason",
)


def _empty_review() -> dict[str, Any]:
    # No automatic judgement, including on "none" or a seemingly good test.
    return {field: None for field in _REVIEW_FIELDS}


def create_seed_hidden_review(
    observed: dict[str, Any],
    *,
    shuffle: Callable[[list], None] | None = None,
    new_id: Callable[[], str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Give reviewers arm-hidden longitudinal text, owners an isolated map.

    Groups do NOT contain source seed text, ordinary notes, arm identity,
    parser quality label or the research prompt that contained the seed.
    Original outputs are not redacted; they may themselves reveal a relation,
    so arm blinding remains imperfect. Public historic cases cannot be
    credibly described as a new prospective independent blind test.
    """
    if (
        not isinstance(observed, dict)
        or observed.get("schema") != OUTPUT_SCHEMA
        or observed.get("G0") != "NOT_PASSED"
        or observed.get("independent_semantic_review_completed") is not False
        or observed.get("q2_new_later_investigability_proven") is not False
    ):
        raise ValueError("not an unreviewed exploratory G0 observation")
    cases = observed.get("cases")
    counts = observed.get("study_counts")
    if (
        not isinstance(cases, list)
        or not isinstance(counts, dict)
        or len(cases) != counts.get("cases_attempted")
        or len(cases) != len({x.get("case_id") for x in cases})
        or any(x.get("status") not in _STATUSES for x in cases)
    ):
        raise ValueError("not a complete and unique recorded case census")
    if (
        counts.get("case_pairs_completed") != sum(
            c["status"] == "completed_exploratory_pair" for c in cases
        )
        or counts.get("no_birth_opportunities") != sum(
            c["status"] == "completed_no_T0_seed_no_AB_opportunity" for c in cases
        )
        or counts.get("failed_or_incomplete") != sum(
            c["status"] == "failed_incomplete_not_zero_effect" for c in cases
        )
    ):
        raise ValueError("case census disagrees with recorded study counts")
    shuffle_fn = shuffle if shuffle is not None else secrets.SystemRandom().shuffle
    id_fn = new_id if new_id is not None else lambda: secrets.token_hex(12)
    used_ids: set[str] = set()

    def fresh() -> str:
        token = id_fn()
        if not isinstance(token, str) or not token or token in used_ids:
            raise ValueError("reviewer pseudonym missing or duplicated")
        used_ids.add(token)
        return token

    blind_groups = []
    owner_groups = {}
    census = []
    for case in cases:
        cid = case["case_id"]
        status = case["status"]
        census_row = {
            "case_id": cid,
            "original_status": status,
            "included_in_first_phase": False,
            "first_phase_exclusion_reason": None,
            "not_a_negative_Q2_effect": status != "completed_exploratory_pair",
        }
        census.append(census_row)
        if status != "completed_exploratory_pair":
            census_row["first_phase_exclusion_reason"] = status
            continue
        seed = case.get("first_seed")
        turns = case.get("turns")
        if (
            not isinstance(seed, dict)
            or not isinstance(seed.get("text"), str)
            or not seed["text"].strip()
            or not isinstance(turns, list)
            or len(turns) != 3
            or [t.get("turn") for t in turns] != [0, 1, 2]
        ):
            raise ValueError("incomplete alleged complete-pair provenance")
        for turn in turns[1:]:
            arms = turn.get("research_arms")
            if not isinstance(arms, dict) or set(arms) != {"A", "B"}:
                raise ValueError("a complete case has no exact A/B outputs")
            for arm in ("A", "B"):
                sample = arms[arm]
                if (
                    not isinstance(sample, dict)
                    or not isinstance(sample.get("text"), str)
                    or not sample["text"].strip()
                    or not isinstance(sample.get("prompt_sha256"), str)
                ):
                    raise ValueError("recorded paired output missing")

        # The source candidate must never appear in the common reviewer
        # context as a literal text. If it does, keep the case in the owner
        # census but do NOT pretend it can be blind-scored.
        common = {
            "initial_context": case.get("source_context", None),
            "chronological_ordinary_dialogue": [{
                "turn": t["turn"],
                "question": t["question"],
                "external_observation": t["new_observation"],
                "ordinary_host_answer": t["host_answer"],
            } for t in turns],
        }
        # The v1 result does not include source_context as its own field.
        # The canonical user's T0 question includes it; reconstructing it
        # from raw strings is forbidden here. Caller may supply a verifiable
        # source_context in future study snapshots.
        common_text = str(common)
        if seed["text"] in common_text:
            census_row["first_phase_exclusion_reason"] = (
                "source_candidate_literal_already_in_common_context"
            )
            continue
        group_id = fresh()
        tracks = []
        for arm in ("A", "B"):
            tid = fresh()
            tracks.append({
                "track_id": tid,
                "two_turn_chain": [{
                    "turn": t["turn"],
                    "model_output_unedited": t["research_arms"][arm]["text"],
                    "reviewer_1": _empty_review(),
                    "reviewer_2": _empty_review(),
                } for t in turns[1:]],
            })
            owner_groups[tid] = {
                "case_id": cid,
                "group_id": group_id,
                "real_arm": arm,
                "first_seed_text_owner_only": seed["text"],
                "birth_snapshot_sha256": seed.get("birth_snapshot_sha256"),
                "prompt_hashes": [
                    t["research_arms"][arm]["prompt_sha256"]
                    for t in turns[1:]
                ],
            }
        shuffle_fn(tracks)
        blind_groups.append({
            "group_id": group_id,
            "common_case_without_seed_or_ordinary_note": common,
            "randomly_pseudonymized_tracks": tracks,
        })
        census_row["included_in_first_phase"] = True
    shuffle_fn(blind_groups)
    blind = {
        "schema": BLIND_SCHEMA,
        "G0": "NOT_PASSED",
        "human_review_received": False,
        "human_review_authenticated": False,
        "seed_reference_withheld_from_first_phase": True,
        "arm_identity_withheld_from_first_phase": True,
        "semantic_output_can_still_hint_at_arm": True,
        "public_old_cases_cannot_be_reblind_as_fresh_confirmation": True,
        "not_an_external_RI_execution": True,
        "not_evidence_of_Q2_expansion": True,
        "rating_fields_all_unfilled": True,
        "study_cases_total_including_failures": len(cases),
        "phase1_groups": blind_groups,
        "phase1_case_count": len(blind_groups),
    }
    owner = {
        "schema": OWNER_SCHEMA,
        "G0": "NOT_PASSED",
        "do_not_distribute_to_first_phase_reviewers": True,
        "release_only_after_independent_phase1_reviews": True,
        "phase1_reviewer_authentication_not_automated": True,
        "case_census_including_failures": census,
        "owner_track_mapping": owner_groups,
        "no_human_conclusions_inserted": True,
    }
    return blind, owner
