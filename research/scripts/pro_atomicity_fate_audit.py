"""Read-only, SHA-pinned audit of detector output and Pro intake decisions.

This measures form dependence, NOT value, truth or semantic atomicity. It
does not create seeds, call a model, change the Gate, or inject an answer.
Aggregate output contains no raw candidate text. --private-items is owner-only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

from shadowseed.intake import is_atomic_seed

ORIGINAL_SHA = "0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf"
SEPARATORS = (",", ";", " and ", " or ", " en ", " of ", "zoals", "bijvoorbeeld")
MULTI_SENTENCE = re.compile(r"[.!?]\s+[A-ZÀ-Ý]")


def classify_lineage(raw: dict) -> tuple[dict, list[dict]]:
    counts, reasons, transitions, models = Counter(), Counter(), Counter(), Counter()
    rows = []
    for case in raw["cases"]:
        for turn_index, turn in enumerate(case["turns"]):
            lineage = turn["canonical_report"]["intake_diagnostics"]["item_lineage"]
            for item in lineage:
                text = item.get("normalized_text")
                if not isinstance(text, str) or not text.strip():
                    continue
                status = str(item.get("outcome", "unknown"))
                counts[status] += 1
                reasons[str(item.get("reason"))] += 1
                if item.get("seed_transition"):
                    transitions[str(item["seed_transition"])] += 1
                models[str(case.get("model_id", "unknown"))] += 1
                rows.append({
                    "case_id": case.get("case_id"),
                    "model": case.get("model_id"),
                    "turn": turn_index,
                    "outcome": status,
                    "reason": item.get("reason"),
                    "seed_transition": item.get("seed_transition"),
                    "observation_id": item.get("observation_id"),
                    "raw_candidate_index": item.get("raw_candidate_index"),
                    "original_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "current_function_pass": is_atomic_seed(text),
                    "punctuation_counterfactual_pass": is_atomic_seed(
                        text.rstrip(". ") + "?"
                    ),
                    "separator_kinds": [t for t in SEPARATORS if t in text.lower()],
                    "multiple_visible_sentences": bool(MULTI_SENTENCE.search(text)),
                    "original_text": text,
                })
    rejected = [r for r in rows
                if r["outcome"] == "rejected" and r["reason"] == "not_atomic"]
    report = {
        "status": "mechanical_fate_audit_only",
        "independent_cases": "not established; fictitious repeated model turns",
        "cases": len(raw["cases"]),
        "candidate_occurrences": len(rows),
        "recorded_outcomes": dict(counts),
        "recorded_reasons": dict(reasons),
        "seed_transitions": dict(transitions),
        "candidates_per_model": dict(models),
        "not_atomic_rejections": len(rejected),
        "rejected_with_2plus_separator_kinds": sum(
            len(r["separator_kinds"]) >= 2 for r in rejected
        ),
        "rejected_with_multiple_visible_sentences": sum(
            r["multiple_visible_sentences"] for r in rejected
        ),
        "rejected_that_pass_question_punctuation_counterfactual": sum(
            r["punctuation_counterfactual_pass"] for r in rejected
        ),
        "replay_disagreements": sum(
            (r["outcome"] == "accepted") != r["current_function_pass"] for r in rows
        ),
        "counterfactual_is_not_semantic_atomicity": True,
        "no_value_or_truth_judgment": True,
        "no_gate_action_or_model_calls": True,
        "caveats": [
            "Punctuation change tests the current form heuristic, not meaning.",
            "Some rejected items may contain multiple distinct uncertainties.",
            "Rejected original observations remain in records, not in live seed memory.",
        ],
    }
    return report, rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", type=Path, required=True)
    parser.add_argument("--source-sha256", default=ORIGINAL_SHA)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--private-items", type=Path)
    args = parser.parse_args(argv)
    blob = args.observed.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != args.source_sha256:
        raise SystemExit("Source checksum mismatch: refusing to analyse or write.")
    report, rows = classify_lineage(json.loads(blob))
    report["source_sha256"] = digest
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    if args.private_items:
        args.private_items.parent.mkdir(parents=True, exist_ok=True)
        args.private_items.write_text(
            json.dumps(rows, indent=2, ensure_ascii=False) + "\n"
        )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
