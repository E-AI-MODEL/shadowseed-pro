"""Reconstruct and verify exact T1 RF inquiry prompts, without model calls.

Sources: original run 40224494313, source code pin
7677f8e145c4766ff3fea5451c95acea21edaacb, fixture and archived
visible history. The original source's _inquiry_prompt implementation
matches the method on this research branch. Verifies the hashes recorded
BEFORE model generation, detects cross-arm literal candidate leakage,
and reports prompt/note length imbalances.

CANNOT establish model use, causal effects, semantic novelty or G0 approval.
Does not claim the reconstructed prompt is a secured prompt from the
provider: it verifies the research runner's own source-time audit hash.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    ARMS, _hash, _inquiry_prompt, _user_input, validate,
)

SOURCE_RUN = 40224494313
SOURCE_SHA = "7677f8e145c4766ff3fea5451c95acea21edaacb"
SOURCE_RAW_SHA = "62f778fb53547f2c0532795ccb31f02f09381500a2eb67b7598bf86ae597820f"
SCHEMA = "shadowseed-rf-t1-prompt-lineage-v1"


def verify_t1_prompt_lineage(observed: dict, fixture: dict) -> dict[str, Any]:
    case = validate(fixture)
    if (
        observed.get("schema") != "ssl-rf-real-seed-observations-v1"
        or observed.get("case_id") != case["id"]
        or observed.get("G0") != "NOT_PASSED"
        or observed.get("status") != "incomplete_exploratory_not_a_null_result"
        or observed.get("fixture_sha256") != _hash(fixture)
    ):
        raise ValueError("source fixture or restricted run metadata mismatch")
    turns = observed.get("turns")
    if not isinstance(turns, list) or len(turns) != 3:
        raise ValueError("partial real RF source must contain exactly three turns")
    if [t.get("turn") for t in turns] != [0, 1, 2]:
        raise ValueError("turn chronology mismatch")
    if turns[2].get("arms"):
        raise ValueError("no model inquiry arms should exist at T2")
    record = observed.get("first_seed")
    if not isinstance(record, dict) or not isinstance(record.get("text"), str):
        raise ValueError("no original real first seed")
    seed_text = record["text"]
    if sha256(seed_text.encode("utf-8")).hexdigest() != (
        turns[0].get("birth") or {}
    ).get("candidate_text_sha256"):
        raise ValueError("original frozen seed differs from first-birth checkpoint")
    source0 = turns[0]["canonical_report"].get("detected_candidates", [])
    possible = [
        x for x in source0
        if isinstance(x, str) and x.strip() and x.strip() != seed_text.strip()
    ]
    sham = possible[0] if possible else case["sham_note"]
    sham_origin = (
        "different_real_T0_detector_item_not_first_seed"
        if possible else "investigator_authored_negative_fallback"
    )
    if record.get("sham_source") != sham_origin:
        raise ValueError("original sham provenance mismatch")
    if record.get("sham_text_sha256") != _hash(sham):
        raise ValueError("source first alternative text hash mismatch")
    note = observed.get("ordinary_note")
    if not isinstance(note, str):
        raise ValueError("ordinary T0 note is unavailable")
    prior = [
        (_user_input(case, case["turns"][i]), turns[i]["host_answer"])
        for i in (0, 1)
    ]
    variants = {"A": "NONE", "B": "NONE", "C": note,
                "D": seed_text, "E": sham}
    audited = turns[1].get("arms", {})
    if not isinstance(audited, dict) or set(audited) != set(ARMS):
        raise ValueError("T1 must have exactly the five original arms")
    rows = {}
    for arm in ARMS:
        inquiry = _inquiry_prompt(
            case, prior,
            case["turns"][1]["new_observation"],
            case["turns"][1]["question"],
            arm=arm, note=variants[arm], earlier_question=None,
        )
        source = audited[arm]
        if (
            source.get("prompt_sha256") != _hash(inquiry)
            or source.get("prompt_chars") != len(inquiry)
            or source.get("note_sha256") != _hash(variants[arm])
            or source.get("note_chars") != len(variants[arm])
        ):
            raise ValueError(f"T1 arm {arm} prompt/note cannot be reconstructed")
        seen = seed_text in inquiry
        if seen != (arm == "D"):
            raise ValueError(f"T1 arm {arm} has incorrect literal seed exposure")
        if arm in ("A", "B") and variants[arm] != "NONE":
            raise ValueError("ordinary controls cannot contain a candidate note")
        rows[arm] = {
            "prompt_sha256": source["prompt_sha256"],
            "prompt_chars": source["prompt_chars"],
            "note_chars": source["note_chars"],
            "literal_first_seed_present": seen,
            "model_question_recorded": source.get("parse_status") == "valid_json",
        }
    return {
        "schema": SCHEMA,
        "source_run": SOURCE_RUN,
        "source_code_commit": SOURCE_SHA,
        "G0": "NOT_PASSED",
        "t1_prompt_reconstruction_hashes_match": True,
        "candidate_exposed_only_in_research_arm_D": True,
        "ordinary_product_answer_seed_influence": False,
        "all_t1_model_arms": rows,
        "t1_prompt_length_span_chars": (
            max(v["prompt_chars"] for v in rows.values())
            - min(v["prompt_chars"] for v in rows.values())
        ),
        "t1_observational_unit_count": 1,
        "t2_inquiry_observational_unit_count": 0,
        "q1_internal_absence_proven": False,
        "q2_seed_causal_effect_proven": False,
        "independent_semantic_review_completed": False,
        "note": (
            "The source runner logged hashes and lengths, not its full prompts. "
            "Exact reconstruction is consistent with frozen code and fixture, "
            "but does not prove the model attended to the seed. Different "
            "arm prompts and note lengths also confound causal attribution."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--expected-raw-sha", default=SOURCE_RAW_SHA)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    if sha256(raw).hexdigest() != args.expected_raw_sha:
        raise ValueError("source observed.json SHA256 mismatch")
    actual = json.loads(raw)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    print(json.dumps(verify_t1_prompt_lineage(actual, fixture),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
