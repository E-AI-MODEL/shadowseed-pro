#!/usr/bin/env python3
"""Audit blinded relation reviews without scoring novelty or unblinding cases.

This is a research-only artifact check. It never reads a model, seed store,
Gate, owner mapping, or hidden answer key. A reviewer's statements are not
independent evidence merely because a CSV has been filled out.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

FIELDS = (
    "case_id",
    "relation",
    "usefulness_0_to_3",
    "specific_new_test_if_any",
    "evidence_for_relation",
    "reason_for_rating",
    "reviewer_id",
)
RELATIONS = {"SAME_CLAIM", "RELATED_DISTINCT", "BROAD_ONLY", "UNCERTAIN"}
CASE_ID = re.compile(r"R[0-9]{2,}")
SCHEMA = "shadowseed-relational-review-audit-v1"


def read_review(path: str | Path) -> dict:
    """Validate a complete single-rater CSV and keep the source unmodified."""
    path = Path(path)
    raw = path.read_bytes()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("review CSV has missing, duplicate or unexpected columns")
        rows = list(reader)
    if not rows:
        raise ValueError("review CSV has no cases")

    seen = set()
    reviewers = set()
    normalized = {}
    for row in rows:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("review CSV has too many or too few values")
        case_id = row["case_id"].strip()
        if not CASE_ID.fullmatch(case_id) or case_id in seen:
            raise ValueError("invalid or repeated case_id")
        seen.add(case_id)
        relation = row["relation"].strip()
        if relation not in RELATIONS:
            raise ValueError(f"invalid relation for {case_id}")
        value = row["usefulness_0_to_3"].strip()
        if value not in {"0", "1", "2", "3"}:
            raise ValueError(f"invalid usefulness for {case_id}")
        for field in ("evidence_for_relation", "reason_for_rating", "reviewer_id"):
            if not row[field].strip():
                raise ValueError(f"empty {field} for {case_id}")
        reviewer_id = row["reviewer_id"].strip()
        reviewers.add(reviewer_id)
        normalized[case_id] = {
            "relation": relation,
            "usefulness": int(value),
            "test_proposed": row["specific_new_test_if_any"].strip().casefold() not in {"", "none", "n/a", "na"},
        }
    if len(reviewers) != 1:
        raise ValueError("one CSV must contain exactly one reviewer_id")
    return {
        "reviewer_id": reviewers.pop(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "cases": dict(sorted(normalized.items())),
    }


def make_audit(first: dict, second: dict | None = None) -> dict:
    """Describe annotations and disagreement; never infer scientific success."""
    cases = first["cases"]
    relation_count = Counter(row["relation"] for row in cases.values())
    usefulness_count = Counter(str(row["usefulness"]) for row in cases.values())
    report = {
        "schema": SCHEMA,
        "review_status": "single_rater_draft" if second is None else "two_raters_unverified",
        "source_pair_text_inspected": False,
        "source_pair_mapping_inspected": False,
        "reviewer_independence_verified": False,
        "g0_status": "NOT_PASSED",
        "shadowseed_incremental_benefit_established": False,
        "limitations": [
            "Annotations were not checked against the original blinded pair texts.",
            "The form does not establish a new executable research question or causal benefit.",
            "Reviewer identity and independence cannot be established from a CSV field.",
        ],
        "first_review": {
            "reviewer_id": first["reviewer_id"],
            "sha256": first["sha256"],
            "case_count": len(cases),
            "relations": {key: relation_count[key] for key in sorted(RELATIONS)},
            "usefulness": {str(i): usefulness_count[str(i)] for i in range(4)},
            "test_proposal_case_ids": [
                case_id for case_id, row in cases.items() if row["test_proposed"]
            ],
        },
    }
    if second is not None:
        if second["reviewer_id"] == first["reviewer_id"]:
            raise ValueError("two review files cannot share a reviewer_id")
        if cases.keys() != second["cases"].keys():
            raise ValueError("review files have different case_id sets")
        differences = []
        for case_id, first_row in cases.items():
            other_row = second["cases"][case_id]
            if first_row != other_row:
                differences.append({
                    "case_id": case_id,
                    "relation_disagrees": first_row["relation"] != other_row["relation"],
                    "usefulness_disagrees": first_row["usefulness"] != other_row["usefulness"],
                    "test_proposal_disagrees": first_row["test_proposed"] != other_row["test_proposed"],
                })
        second_relation_count = Counter(row["relation"] for row in second["cases"].values())
        second_usefulness_count = Counter(str(row["usefulness"]) for row in second["cases"].values())
        report["second_review"] = {
            "reviewer_id": second["reviewer_id"],
            "sha256": second["sha256"],
            "case_count": len(second["cases"]),
            "relations": {key: second_relation_count[key] for key in sorted(RELATIONS)},
            "usefulness": {str(i): second_usefulness_count[str(i)] for i in range(4)},
            "test_proposal_case_ids": [
                case_id for case_id, row in second["cases"].items() if row["test_proposed"]
            ],
        }
        report["comparison"] = {
            "same_annotations": len(cases) - len(differences),
            "different_annotations": len(differences),
            "same_relation": sum(
                cases[case_id]["relation"] == second["cases"][case_id]["relation"]
                for case_id in cases
            ),
            "same_usefulness": sum(
                cases[case_id]["usefulness"] == second["cases"][case_id]["usefulness"]
                for case_id in cases
            ),
            "same_test_proposal": sum(
                cases[case_id]["test_proposed"] == second["cases"][case_id]["test_proposed"]
                for case_id in cases
            ),
            "differences": differences,
            "independent_review_completed": False,
        }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", required=True, type=Path)
    parser.add_argument("--second-review", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    input_paths = [args.review.resolve()]
    if args.second_review:
        input_paths.append(args.second_review.resolve())
    if output in input_paths:
        parser.error("output path may not overwrite a review source")
    first = read_review(args.review)
    second = read_review(args.second_review) if args.second_review else None
    report = make_audit(first, second)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
    print(f"Wrote {args.output}; status: {report['review_status']}; G0: NOT_PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
