"""Auditable, raw-first detector-to-intake accounting without model calls.

Source file is SHA-256-pinned. This is not a semantic quality test, and a
max-count parser diagnostic alone is not proof of dropped generated text.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re

ORIGINAL_SHA = "0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf"
NUMBERED_LINE = re.compile(r"^\s*\d+[.)]\s*\S", re.MULTILINE)


def audit(source: dict) -> dict:
    counts = Counter()
    models = defaultdict(Counter)
    observations = []
    for case in source["cases"]:
        model = case["model_id"]
        for turn in case["turns"]:
            report = turn["canonical_report"]
            info = report["intake_diagnostics"]
            detector = report["detector_audit"]
            diag = detector["parse_diagnostics"]
            raw = detector.get("raw_output") or ""
            raw_lines = len(NUMBERED_LINE.findall(raw))
            parsed = report.get("detected_candidates", [])
            normalized = info.get("normalized_candidates", [])
            lineage = info.get("item_lineage", [])
            values = {
                "turns": 1,
                "raw_numbered_candidate_lines": raw_lines,
                "parsed_candidates": len(parsed),
                "normalized_candidates": len(normalized),
                "intake_lineage_items": len(lineage),
                "accepted_candidates": sum(x.get("outcome") == "accepted" for x in lineage),
                "rejected_not_atomic": sum(
                    x.get("outcome") == "rejected" and x.get("reason") == "not_atomic"
                    for x in lineage
                ),
                "explicit_none_turns": int(bool(diag.get("explicit_none"))),
                "cap_flagged_turns": int(bool(diag.get("truncated_after_max_seeds"))),
                "raw_numbered_exceeds_parsed_turns": int(raw_lines > len(parsed)),
                "normalized_count_differs_turns": int(len(parsed) != len(normalized)),
                "lineage_count_differs_turns": int(len(normalized) != len(lineage)),
                "noncanonical_lineage_turns": int(any(
                    x.get("source_mapping_status") != "canonical" for x in lineage
                )),
                "parser_reported_drops": sum(int(diag.get(x, 0)) for x in (
                    "dropped_blank_or_placeholder", "dropped_citation_or_stub",
                    "dropped_fewshot_leak", "dropped_duplicate")),
            }
            counts.update(values)
            models[model].update(values)
            observations.append({
                "case_id": case["case_id"], "model": model,
                "turn": turn["turn"], "raw_numbered_lines": raw_lines,
                "parsed": len(parsed), "normalized": len(normalized),
                "lineage": len(lineage), "parse_diagnostics": diag,
                "normalized_text_matches_parsed": (
                    [str(x).strip().rstrip(" .?") for x in parsed]
                    == [str(x).strip().rstrip(" .?") for x in normalized]
                ),
            })
    # Flag is set when the parser reaches the cap; it may have processed all
    # generated candidates. Never equate a set flag with proven discards.
    return {
        "status": "mechanical_source_boundary_audit",
        "grain": "candidate occurrences within model/case/turn; not independent discoveries",
        "counts": dict(counts),
        "by_model": {k: dict(v) for k, v in sorted(models.items())},
        "all_parsed_texts_survived_normalization": all(
            x["normalized_text_matches_parsed"] for x in observations
        ),
        "parser_flag_is_proof_of_discarded_text": False,
        "unobserved_model_possibilities_excluded_from_claims": True,
        "no_semantic_quality_or_q1q2_proof": True,
        "no_model_calls": True,
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--observed", required=True, type=Path)
    p.add_argument("--source-sha256", default=ORIGINAL_SHA)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args(argv)
    raw = args.observed.read_bytes()
    actual = sha256(raw).hexdigest()
    if actual != args.source_sha256:
        raise SystemExit("source SHA-256 mismatch; no report written")
    result = audit(json.loads(raw))
    result["source_sha256"] = actual
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": result["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
