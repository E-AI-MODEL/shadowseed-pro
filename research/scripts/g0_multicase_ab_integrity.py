"""Read-only provenance and matched-prompt audit of the six-case RF A/B.

This is a retrospective integrity check of observed.json, not a second model
call, semantic novelty assessor, proof of latent model representations or
human reviewer. A case with no true seed birth cannot count as a negative
A/B effect. A failed checkpoint cannot count as a completed T2 inquiry.

Usage:
    python research/scripts/g0_multicase_ab_integrity.py \
      --observed observed.json \
      --fixture research/fixtures/g0_multicase_real_ab_v1.json
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from shadowseed_research.benchmark.g0_multicase_real_ab import (
    ARMS, CASE_COUNT, CALL_CAP, EMBED_CAP, OUTPUT_SCHEMA, TOKEN_CAP,
    _parse_research, research_prompt, validate_design,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import _hash

SCHEMA = "shadowseed-multicase-ab-integrity-v1"
MAX_TOTAL = CASE_COUNT * CALL_CAP
ALLOWED = {
    "completed_exploratory_pair",
    "completed_no_T0_seed_no_AB_opportunity",
    "failed_incomplete_not_zero_effect",
}


def ensure(ok: Any, message: str) -> None:
    if not ok:
        raise ValueError(message)


def check_checkpoint(checkpoint: dict, label: str) -> None:
    ensure(
        isinstance(checkpoint, dict)
        and checkpoint.get("snapshot_sha256") ==
            _hash({k: v for k, v in checkpoint.items()
                   if k != "snapshot_sha256"}),
        label + " hash missing or modified",
    )


def audit(data: dict, fixture: dict) -> dict:
    cases = validate_design(fixture)
    ensure(
        isinstance(data, dict) and data.get("schema") == OUTPUT_SCHEMA
        and data.get("model") == "gpt-5" and data.get("feedback_regime") == "RF"
        and data.get("G0") == "NOT_PASSED"
        and data.get("independent_semantic_review_completed") is False
        and data.get("q2_new_later_investigability_proven") is False
        and data.get("q1_internal_activation_not_observed") is True
        and data.get("study_fixture_sha256") == _hash(fixture),
        "wrong design, incompatible source, or false scientific claim",
    )
    recorded = data.get("cases")
    ensure(
        isinstance(recorded, list)
        and len(recorded) == CASE_COUNT
        and [x.get("case_id") for x in recorded] ==
            [x["id"] for x in cases],
        "one or more original cases missing, duplicated or reordered",
    )
    allocation = data.get("recorded_allocation", {})
    ensure(
        data.get("allocation_frozen_before_first_provider_call") is True
        and set(allocation) == {x["id"] for x in cases}
        and sorted(v[0] for v in allocation.values()) == ["A"] * 3 + ["B"] * 3
        and all(sorted(v) == list(ARMS) for v in allocation.values()),
        "invalid or unbalanced recorded A/B allocation",
    )
    rows = []
    calls, embeddings, tokens = 0, 0, 0
    complete_pairs = no_birth = failed = 0
    for case, row in zip(cases, recorded):
        cid = case["id"]
        status = row.get("status")
        ensure(status in ALLOWED, cid + " has unrecognized case outcome")
        receipt = row.get("provider")
        ensure(isinstance(receipt, dict), cid + " has no provider receipt")
        mc = receipt.get("model_calls_attempted", -1)
        ec = receipt.get("embedding_calls_attempted", -1)
        tc = receipt.get("reported_tokens", -1)
        ensure(
            all(type(x) is int and x >= 0 for x in (mc, ec, tc))
            and mc <= CALL_CAP and ec <= EMBED_CAP and tc <= TOKEN_CAP,
            cid + " overran per-case call/token budget",
        )
        calls += mc
        embeddings += ec
        tokens += tc
        entry: dict[str, Any] = {
            "case_id": cid, "family": case["family"],
            "status": status, "provider_model_calls": mc,
            "provider_embedding_calls": ec,
            "provider_reported_tokens": tc,
            "valid_model_inquiries": 0,
            "valid_none_inquiries": 0,
            "invalid_model_inquiries": 0,
            "completed_A_B_turn_pairs": 0,
            "source_seed_word_exposed_in_ordinary_note": None,
        }
        if status == "failed_incomplete_not_zero_effect":
            ensure(
                row.get("not_an_independent_negative_finding") is True
                and isinstance(row.get("error_type"), str),
                "failed run silently relabeled as no-effect result",
            )
            failed += 1
            rows.append(entry)
            continue
        turns = row.get("turns")
        ensure(
            isinstance(turns, list)
            and len(turns) == 3
            and [t.get("turn") for t in turns] == [0, 1, 2],
            cid + " lacks full three-turn recorded chronology",
        )
        ensure(
            all(
                t.get("ordinary_control_identical") is True
                and t.get("host_answer") ==
                    t.get("canonical_report", {}).get("answer")
                and not t.get("canonical_report", {}).get("selected_seed_ids")
                and not t.get("canonical_report", {}).get("surfaced_seed_ids")
                and t.get("canonical_report", {}).get("same_turn_revision_applied") is False
                and t.get("canonical_report", {}).get("self_reinforcement_applied") is False
                for t in turns
            ) and row.get("ordinary_answer_seed_influence") is False,
            cid + " ordinary answer touched by untrusted seed",
        )
        if status == "completed_no_T0_seed_no_AB_opportunity":
            ensure(
                row.get("first_seed") is None and row.get("birth") is None
                and all(not t.get("research_arms") for t in turns),
                cid + " missing seed was misrepresented as a completed A/B",
            )
            no_birth += 1
            rows.append(entry)
            continue
        complete_pairs += 1
        seed = row.get("first_seed")
        birth = row.get("birth")
        note = row.get("ordinary_note")
        ensure(
            isinstance(seed, dict) and isinstance(seed.get("text"), str)
            and isinstance(note, str) and note
            and seed.get("birth_turn") == 0 and seed.get("weight") == 0
            and seed.get("evidence_count") == 0
            and seed.get("selection") == "first_T0_canonical_accepted"
            and len(row.get("ordinary_t0_samples", [])) == 2,
            cid + " did not retain real first weightless birth/source samples",
        )
        check_checkpoint(birth, cid + " first birth")
        ensure(
            birth["seed_id"] == seed["id"]
            and birth["snapshot_sha256"] == seed["birth_snapshot_sha256"]
            and sha256(seed["text"].encode("utf-8")).hexdigest() ==
                birth["candidate_text_sha256"]
            and birth.get("raw_detector_item_to_seed_mapping_verified") is True,
            cid + " detector-to-seed lineage mismatch",
        )
        entry["source_seed_word_exposed_in_ordinary_note"] = (
            seed["text"] in note
        )
        earlier = {"A": None, "B": None}
        history = []
        previous = None
        for i, t in enumerate(turns):
            history.append((t["user_input"], t["host_answer"]))
            if i == 0:
                ensure(not t.get("research_arms") and not t.get("followup"),
                       cid + " cannot have T0 experiments")
                continue
            checkpoint = t.get("followup")
            check_checkpoint(checkpoint, f"{cid} T{i} checkpoint")
            ensure(
                checkpoint.get("seed_id") == seed["id"]
                and checkpoint.get("turn") == i
                and checkpoint.get("birth_snapshot_sha256") ==
                    birth["snapshot_sha256"]
                and checkpoint.get("history_sha256") ==
                    _hash([z["canonical_report"] for z in turns[:i+1]])
                and checkpoint.get("seed_state_after_turn", {}).get("weight") == 0
                and checkpoint.get("seed_state_after_turn", {}).get("evidence_count") == 0
                and checkpoint.get("product_answer_seed_influence_observed") is False
                and checkpoint.get("previous_checkpoint_sha256") ==
                    (previous["snapshot_sha256"] if previous else None),
                cid + f" T{i} candidate/history/authority not faithfully recorded",
            )
            previous = checkpoint
            research = t.get("research_arms", {})
            ensure(
                isinstance(research, dict) and set(research) == set(ARMS),
                cid + f" missing paired T{i} inquiry",
            )
            for arm in ARMS:
                v = research[arm]
                prompt = research_prompt(
                    case, history, note,
                    seed["text"] if arm == "B" else None,
                    i, earlier[arm],
                )
                ensure(
                    v.get("prompt_sha256") == _hash(prompt)
                    and v.get("prompt_chars") == len(prompt)
                    and v.get("research_seed_exposure") is (arm == "B")
                    and v.get("previous_own_question_only") is (i == 2)
                    and v.get("external_test_executed") is False
                    and v.get("independent_review_completed") is False,
                    cid + f" T{i} {arm} prompt is contaminated or altered",
                )
                parsed = _parse_research(v.get("text", ""))
                ensure(v.get("parsed") == parsed,
                       cid + f" T{i} {arm} parser record disagrees with raw text")
                if parsed["status"] == "valid_questions":
                    entry["valid_model_inquiries"] += 1
                elif parsed["status"] == "valid_none":
                    entry["valid_none_inquiries"] += 1
                else:
                    entry["invalid_model_inquiries"] += 1
                earlier[arm] = parsed if parsed["status"] in {
                    "valid_questions", "valid_none"
                } else None
            entry["completed_A_B_turn_pairs"] += 1
        ensure(
            entry["completed_A_B_turn_pairs"] == 2,
            cid + " T1/T2 paired trajectory not complete",
        )
        entry["T0_birth_snapshot_sha256"] = birth["snapshot_sha256"]
        entry["T2_followup_snapshot_sha256"] = previous["snapshot_sha256"]
        rows.append(entry)
    counts = data.get("study_counts")
    ensure(
        isinstance(counts, dict)
        and counts.get("cases_attempted") == CASE_COUNT
        and counts.get("case_pairs_completed") == complete_pairs
        and counts.get("no_birth_opportunities") == no_birth
        and counts.get("failed_or_incomplete") == failed
        and counts.get("provider_model_calls") == calls
        and counts.get("provider_embedding_calls") == embeddings
        and counts.get("provider_reported_tokens") == tokens,
        "recorded total/case denominator mismatches the raw records",
    )
    ensure(calls <= MAX_TOTAL, "global model-call budget exceeded")
    return {
        "schema": SCHEMA,
        "G0": "NOT_PASSED",
        "feedback_regime": "RF",
        "design_fixture_sha256": _hash(fixture),
        "independent_case_count": CASE_COUNT,
        "completed_case_pairs": complete_pairs,
        "no_birth_cases_not_effect_nulls": no_birth,
        "failed_cases_not_effect_nulls": failed,
        "full_T1_T2_paired_inquiry_records": complete_pairs * 4,
        "model_calls_attempted": calls,
        "embedding_calls_attempted": embeddings,
        "reported_tokens": tokens,
        "all_recorded_full_pair_prompt_hashes_match": True,
        "candidate_specific_semantic_or_causal_effect_established": False,
        "internal_q1_ability_established": False,
        "real_RI_later_investigability_established": False,
        "no_automatic_novelty_score": True,
        "ordinary_note_contamination_cases": [
            x["case_id"] for x in rows
            if x["source_seed_word_exposed_in_ordinary_note"] is True
        ],
        "cases": rows,
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--observed", type=Path, required=True)
    p.add_argument("--fixture", type=Path, required=True)
    p.add_argument("--expected-observed-sha256")
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    raw = args.observed.read_bytes()
    actual = sha256(raw).hexdigest()
    if args.expected_observed_sha256 and args.expected_observed_sha256 != actual:
        raise ValueError("source artifact SHA-256 mismatch")
    source = json.loads(raw)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    findings = audit(source, fixture)
    findings["source_observed_sha256"] = actual
    output = json.dumps(findings, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
