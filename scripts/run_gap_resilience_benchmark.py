#!/usr/bin/env python3
"""Shadowseed gap-resilience benchmark.

This is a benchmark/evaluation harness, not runtime logic. It measures four
properties of detector output without granting evidence, authority, promotion,
or point-of-use permission:

- expected-gap recall against human-authored alias groups;
- abstention on negative-control items where no candidate should be emitted;
- resolved-gap reopen rate when bounded prior context already establishes a
  point that the detector should not call missing again;
- repeatability across repeated detector runs on the same item.

The text matcher is deliberately simple and inspectable. It is a scoring aid,
not semantic truth and not Layer-C evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from shadowseed.detection.model_detector import make_detector_backend

SCHEMA_VERSION = 1
ARTIFACT = "shadowseed-gap-resilience-v1"
DEFAULT_MATCH_THRESHOLD = 0.35

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "de",
        "een",
        "en",
        "for",
        "from",
        "het",
        "in",
        "is",
        "of",
        "on",
        "or",
        "the",
        "to",
        "van",
        "voor",
        "with",
        "wordt",
        "worden",
    }
)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zà-ÿ0-9]+", str(text).lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def jaccard(left: str, right: str) -> float:
    a, b = _tokens(left), _tokens(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def alias_similarity(candidate: str, aliases: Iterable[str]) -> float:
    values = [jaccard(candidate, alias) for alias in aliases]
    return max(values, default=0.0)


def candidate_set_similarity(left: list[str], right: list[str]) -> float:
    """Order-insensitive symmetric best-match similarity between two runs."""

    if not left and not right:
        return 1.0
    if not left or not right:
        return 0.0

    def directed(source: list[str], target: list[str]) -> float:
        return mean(
            max((jaccard(candidate, other) for other in target), default=0.0)
            for candidate in source
        )

    return (directed(left, right) + directed(right, left)) / 2.0


def _groups(case: dict[str, Any], key: str) -> list[dict[str, Any]]:
    groups = case.get(key, [])
    if not isinstance(groups, list):
        raise ValueError(f"{key} must be a list")
    for group in groups:
        if not isinstance(group, dict) or not group.get("id") or not group.get("aliases"):
            raise ValueError(f"Every {key} entry needs id and aliases")
    return groups


def _group_hit(
    candidates: list[str],
    group: dict[str, Any],
    threshold: float,
) -> tuple[bool, float, str | None]:
    best_score = 0.0
    best_candidate: str | None = None
    aliases = [str(value) for value in group["aliases"]]
    for candidate in candidates:
        score = alias_similarity(candidate, aliases)
        if score > best_score:
            best_score = score
            best_candidate = candidate
    return best_score >= threshold, best_score, best_candidate


def score_case(
    case: dict[str, Any],
    runs: list[list[str]],
    *,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> dict[str, Any]:
    expected = _groups(case, "expected_gap_groups")
    resolved = _groups(case, "resolved_gap_groups")
    negative_control = bool(case.get("negative_control", False))

    expected_opportunities = len(expected) * len(runs)
    expected_hits = 0
    resolved_opportunities = len(resolved) * len(runs)
    resolved_reopens = 0
    empty_runs = 0
    run_details: list[dict[str, Any]] = []

    for index, candidates in enumerate(runs, start=1):
        candidates = [str(value).strip() for value in candidates if str(value).strip()]
        if not candidates:
            empty_runs += 1

        expected_detail: list[dict[str, Any]] = []
        for group in expected:
            hit, similarity, candidate = _group_hit(candidates, group, threshold)
            expected_hits += int(hit)
            expected_detail.append(
                {
                    "gap_id": group["id"],
                    "hit": hit,
                    "best_similarity": round(similarity, 4),
                    "best_candidate": candidate,
                }
            )

        resolved_detail: list[dict[str, Any]] = []
        for group in resolved:
            hit, similarity, candidate = _group_hit(candidates, group, threshold)
            resolved_reopens += int(hit)
            resolved_detail.append(
                {
                    "gap_id": group["id"],
                    "reopened": hit,
                    "best_similarity": round(similarity, 4),
                    "best_candidate": candidate,
                }
            )

        run_details.append(
            {
                "run": index,
                "candidate_count": len(candidates),
                "candidates": candidates,
                "expected": expected_detail,
                "resolved": resolved_detail,
            }
        )

    pairwise = [
        candidate_set_similarity(runs[left], runs[right])
        for left, right in combinations(range(len(runs)), 2)
    ]
    repeatability = mean(pairwise) if pairwise else 1.0

    return {
        "case_id": str(case["case_id"]),
        "negative_control": negative_control,
        "runs": len(runs),
        "mean_candidates_per_run": round(
            mean([len(run) for run in runs]) if runs else 0.0, 4
        ),
        "expected_gap_hits": expected_hits,
        "expected_gap_opportunities": expected_opportunities,
        "expected_gap_recall": (
            round(expected_hits / expected_opportunities, 4)
            if expected_opportunities
            else None
        ),
        "resolved_gap_reopens": resolved_reopens,
        "resolved_gap_opportunities": resolved_opportunities,
        "resolved_gap_reopen_rate": (
            round(resolved_reopens / resolved_opportunities, 4)
            if resolved_opportunities
            else None
        ),
        "abstention_successes": empty_runs if negative_control else None,
        "abstention_opportunities": len(runs) if negative_control else None,
        "abstention_rate": (
            round(empty_runs / len(runs), 4)
            if negative_control and runs
            else None
        ),
        "repeatability": round(repeatability, 4),
        "run_details": run_details,
    }


def summarize(case_reports: list[dict[str, Any]]) -> dict[str, Any]:
    expected_hits = sum(item["expected_gap_hits"] for item in case_reports)
    expected_opportunities = sum(
        item["expected_gap_opportunities"] for item in case_reports
    )
    resolved_reopens = sum(item["resolved_gap_reopens"] for item in case_reports)
    resolved_opportunities = sum(
        item["resolved_gap_opportunities"] for item in case_reports
    )
    abstention_successes = sum(
        int(item["abstention_successes"] or 0) for item in case_reports
    )
    abstention_opportunities = sum(
        int(item["abstention_opportunities"] or 0) for item in case_reports
    )
    repeatability = [float(item["repeatability"]) for item in case_reports]

    return {
        "cases": len(case_reports),
        "expected_gap_recall": (
            round(expected_hits / expected_opportunities, 4)
            if expected_opportunities
            else None
        ),
        "expected_gap_hits": expected_hits,
        "expected_gap_opportunities": expected_opportunities,
        "negative_control_abstention_rate": (
            round(abstention_successes / abstention_opportunities, 4)
            if abstention_opportunities
            else None
        ),
        "negative_control_abstention_successes": abstention_successes,
        "negative_control_abstention_opportunities": abstention_opportunities,
        "resolved_gap_reopen_rate": (
            round(resolved_reopens / resolved_opportunities, 4)
            if resolved_opportunities
            else None
        ),
        "resolved_gap_reopens": resolved_reopens,
        "resolved_gap_opportunities": resolved_opportunities,
        "repeatability_mean": (
            round(mean(repeatability), 4) if repeatability else None
        ),
    }


def run_cases(
    cases: list[dict[str, Any]],
    detector: Any,
    *,
    repeats: int,
    max_seeds: int,
    threshold: float,
) -> dict[str, Any]:
    if repeats < 1:
        raise ValueError("repeats must be >= 1")

    reports: list[dict[str, Any]] = []
    for case in cases:
        runs: list[list[str]] = []
        audits: list[dict[str, Any]] = []
        for _ in range(repeats):
            candidates = list(
                detector.detect_seeds(
                    {
                        "question": str(case["question"]),
                        "text": str(case["draft_answer"]),
                        "conversation_context": str(
                            case.get("conversation_context") or "NONE"
                        ),
                    },
                    max_seeds=max_seeds,
                )
            )
            runs.append(candidates)
            raw_output = getattr(detector, "last_raw_output", None)
            parse_diagnostics = getattr(detector, "last_parse_diagnostics", None)
            prompt_metadata = getattr(detector, "last_prompt_metadata", None)
            audits.append(
                {
                    "raw_output": None if raw_output is None else str(raw_output),
                    "parse_diagnostics": (
                        dict(parse_diagnostics)
                        if isinstance(parse_diagnostics, dict)
                        else None
                    ),
                    "prompt_contract": (
                        dict(prompt_metadata)
                        if isinstance(prompt_metadata, dict)
                        else None
                    ),
                }
            )
        report = score_case(case, runs, threshold=threshold)
        explicit_none_runs = 0
        parser_empty_nonblank_runs = 0
        for detail, audit in zip(report["run_details"], audits, strict=True):
            detail["detector_audit"] = audit
            diagnostics = audit.get("parse_diagnostics") or {}
            if diagnostics.get("explicit_none"):
                explicit_none_runs += 1
            if (
                diagnostics
                and not diagnostics.get("explicit_none")
                and int(diagnostics.get("nonblank_lines", 0)) > 0
                and int(diagnostics.get("accepted_candidates", 0)) == 0
            ):
                parser_empty_nonblank_runs += 1
        report["explicit_none_runs"] = explicit_none_runs
        report["parser_empty_nonblank_runs"] = parser_empty_nonblank_runs
        reports.append(report)

    scored = {"summary": summarize(reports), "cases": reports}
    total_runs = sum(item["runs"] for item in reports)
    scored["summary"]["explicit_none_rate"] = (
        round(sum(item["explicit_none_runs"] for item in reports) / total_runs, 4)
        if total_runs
        else None
    )
    scored["summary"]["parser_empty_nonblank_rate"] = (
        round(
            sum(item["parser_empty_nonblank_runs"] for item in reports) / total_runs,
            4,
        )
        if total_runs
        else None
    )
    return scored


def _load_cases(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload.get("schema_version", 0)) != SCHEMA_VERSION:
        raise ValueError("unsupported gap-resilience case schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("benchmark case file must contain non-empty cases")
    return payload, cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("benchmarks/gap_resilience/cases.json"),
    )
    parser.add_argument(
        "--backend",
        choices=("fixture", "hf-transformers", "ollama", "openai"),
        default="fixture",
    )
    parser.add_argument("--model-id", default=None)
    parser.add_argument("--model-revision", default=None)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-seeds", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=400)
    parser.add_argument("--match-threshold", type=float, default=DEFAULT_MATCH_THRESHOLD)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    case_payload, cases = _load_cases(args.cases)
    detector = make_detector_backend(
        args.backend,
        model_id=args.model_id,
        max_new_tokens=args.max_new_tokens,
        prompt_variant="current_pair",
        model_revision=args.model_revision,
    )
    scored = run_cases(
        cases,
        detector,
        repeats=args.repeats,
        max_seeds=args.max_seeds,
        threshold=args.match_threshold,
    )
    live = args.backend != "fixture"
    report = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "run_type": "live_benchmark" if live else "benchmark_smoke",
        "disclaimer": (
            "Benchmark measurements are diagnostic, not evidence or authority. "
            "The fixture backend is a harness smoke test only. No aggregate "
            "metric is an overall Shadowseed quality score."
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "shadowseed_source_ref": os.environ.get("GITHUB_SHA", "working-tree"),
        "case_set": case_payload.get("case_set", args.cases.name),
        "case_set_version": case_payload.get("case_set_version", "unknown"),
        "backend": args.backend,
        "model_id": args.model_id,
        "model_revision": args.model_revision,
        "prompt_variant": "current_pair",
        "repeats": args.repeats,
        "max_seeds": args.max_seeds,
        "match_threshold": args.match_threshold,
        **scored,
    }

    rendered = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
