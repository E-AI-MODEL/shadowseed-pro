"""Author-only read-only reinspection queue for intake-rejected Pro candidates.

No new seeds, quality labels, truth judgements or Gate changes. Full original
host context stays in a *private* output file; never attach this to public CI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from research.scripts.pro_atomicity_fate_audit import ORIGINAL_SHA


def build_queue(observed: dict) -> dict:
    items = []
    for case in observed["cases"]:
        seen_turns = []
        for turn_no, turn in enumerate(case["turns"]):
            seen_turns.append({
                "turn": turn_no,
                "user_input": turn.get("user_input"),
                "host_answer": turn.get("host_answer"),
            })
            for item in turn["canonical_report"]["intake_diagnostics"]["item_lineage"]:
                if item.get("outcome") != "rejected" or item.get("reason") != "not_atomic":
                    continue
                candidate = item.get("normalized_text")
                if not isinstance(candidate, str) or not candidate.strip():
                    continue
                items.append({
                    "case_id": case["case_id"],
                    "model_id": case["model_id"],
                    "turn_index": turn_no,
                    "observation_id": item.get("observation_id"),
                    "raw_candidate_index": item.get("raw_candidate_index"),
                    "source_mapping_status": item.get("source_mapping_status"),
                    "original_candidate": candidate,
                    "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
                    "original_outcome": "rejected",
                    "original_reason": "not_atomic",
                    "seed_born": False,
                    "authority": None,
                    "original_context_through_this_turn": list(seen_turns),
                    "unfilled_review": {
                        "relation_structure": None,
                        "potential_reexpression": None,
                        "review_notes": "",
                    },
                })
    return {
        "status": "owner_only_unjudged_reinspection_queue",
        "no_seed_admission": True,
        "no_gate_or_authority_action": True,
        "no_semantic_value_judgement": True,
        "review_choices": ["one_investigable_dependency", "separate_questions", "unclear"],
        "items": items,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--source-sha256", default=ORIGINAL_SHA)
    parser.add_argument("--private-output", type=Path, required=True)
    args = parser.parse_args(argv)
    blob = args.observed.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != args.source_sha256:
        raise SystemExit("Original source checksum mismatch: no review queue written")
    queue = build_queue(json.loads(blob))
    queue["source_sha256"] = digest
    args.private_output.parent.mkdir(parents=True, exist_ok=True)
    args.private_output.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "status": queue["status"], "items": len(queue["items"]),
        "private_output": True, "source_sha256": digest,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
