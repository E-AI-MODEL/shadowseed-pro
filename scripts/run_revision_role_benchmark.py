#!/usr/bin/env python3
"""Benchmark a model only in Shadowseed's same-turn revision role.

The baseline answer and candidate perspectives are fixed human-authored inputs.
The model does not generate the baseline, detect gaps, create seeds, affect Gate
state, or decide authority. This isolates the conditional revision task.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from shadowseed.adapters.ollama_client import (
    DEFAULT_PROVIDER_TIMEOUT_SECONDS,
    ollama_host,
)
from shadowseed.surfacing import REVISION_PROMPT_META, build_revision_prompt

ARTIFACT = "shadowseed-revision-role-screen-v1"
SCHEMA_VERSION = 1
DEFAULT_MATCH_THRESHOLD = 0.60

_STOPWORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "de", "een", "en",
        "for", "from", "het", "in", "is", "of", "on", "or", "the", "to",
        "van", "voor", "with", "wordt", "worden",
    }
)


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zà-ÿ0-9]+", str(text).lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def token_recall(text: str, alias: str) -> float:
    expected = _tokens(alias)
    if not expected:
        return 1.0
    actual = _tokens(text)
    return len(actual & expected) / len(expected)


def group_hit(
    text: str,
    group: dict[str, Any],
    threshold: float,
) -> tuple[bool, float, str | None]:
    aliases = [str(value) for value in group.get("aliases", [])]
    scored = [(token_recall(text, alias), alias) for alias in aliases]
    if not scored:
        return False, 0.0, None
    score, alias = max(scored, key=lambda item: item[0])
    return score >= threshold, score, alias


def score_groups(
    text: str,
    groups: Iterable[dict[str, Any]],
    threshold: float,
) -> tuple[float | None, list[dict[str, Any]]]:
    details: list[dict[str, Any]] = []
    hits = 0
    group_list = list(groups)
    for group in group_list:
        hit, similarity, alias = group_hit(text, group, threshold)
        hits += int(hit)
        details.append(
            {
                "id": str(group["id"]),
                "hit": hit,
                "best_token_recall": round(similarity, 4),
                "best_alias": alias,
            }
        )
    return (
        round(hits / len(group_list), 4) if group_list else None,
        details,
    )


def visible_contract_violations(response: str) -> list[str]:
    lowered = response.lower()
    violations: list[str] = []
    if "<think>" in lowered or "</think>" in lowered:
        violations.append("thinking_markup")
    if "candidate_perspectives" in lowered:
        violations.append("candidate_delimiter")
    if "existing draft:" in lowered or "user question:" in lowered:
        violations.append("prompt_label")
    if "revised answer:" in lowered:
        violations.append("output_label")
    return violations


def _ollama_generate(
    *,
    model_id: str,
    prompt: str,
    max_new_tokens: int,
    timeout: float,
) -> dict[str, Any]:
    payload = {
        "model": model_id,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": max_new_tokens,
            "seed": 0,
        },
    }
    request = urllib.request.Request(
        f"{ollama_host()}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = json.loads(response.read().decode("utf-8"))
    if not isinstance(body, dict):
        raise RuntimeError("Ollama returned an unexpected response shape")
    return body


def score_case(
    case: dict[str, Any],
    body: dict[str, Any],
    *,
    threshold: float = DEFAULT_MATCH_THRESHOLD,
) -> dict[str, Any]:
    response = str(body.get("response") or "").strip()
    thinking = str(body.get("thinking") or "").strip()
    done_reason = str(body.get("done_reason") or "")
    addition_coverage, addition_details = score_groups(
        response,
        case.get("expected_addition_groups", []),
        threshold,
    )
    preservation, preservation_details = score_groups(
        response,
        case.get("baseline_preservation_groups", []),
        threshold,
    )
    violations = visible_contract_violations(response)
    total_duration_ns = int(body.get("total_duration") or 0)
    total_duration_seconds = total_duration_ns / 1_000_000_000 if total_duration_ns else None
    within_product_timeout = (
        None
        if total_duration_seconds is None
        else total_duration_seconds <= DEFAULT_PROVIDER_TIMEOUT_SECONDS
    )
    final_response_available = bool(response) and done_reason != "length"
    role_contract_pass = (
        final_response_available
        and not violations
        and (addition_coverage is None or addition_coverage >= 1.0)
        and (preservation is None or preservation >= 1.0)
    )

    return {
        "case_id": str(case["case_id"]),
        "language": case.get("language"),
        "final_response_available": final_response_available,
        "done_reason": done_reason or None,
        "eval_count": body.get("eval_count"),
        "prompt_eval_count": body.get("prompt_eval_count"),
        "total_duration_seconds": (
            round(total_duration_seconds, 3)
            if total_duration_seconds is not None
            else None
        ),
        "within_current_product_timeout": within_product_timeout,
        "response_word_count": len(re.findall(r"[A-Za-zÀ-ÿ0-9_]+", response)),
        "addition_coverage": addition_coverage,
        "addition_details": addition_details,
        "baseline_preservation": preservation,
        "baseline_preservation_details": preservation_details,
        "visible_contract_violations": violations,
        "role_contract_pass": role_contract_pass,
        "response": response,
        "thinking": thinking,
    }


def summarize(reports: list[dict[str, Any]]) -> dict[str, Any]:
    additions = [
        float(item["addition_coverage"])
        for item in reports
        if item["addition_coverage"] is not None
    ]
    preservation = [
        float(item["baseline_preservation"])
        for item in reports
        if item["baseline_preservation"] is not None
    ]
    durations = [
        float(item["total_duration_seconds"])
        for item in reports
        if item["total_duration_seconds"] is not None
    ]
    return {
        "cases": len(reports),
        "final_response_rate": (
            round(sum(bool(item["final_response_available"]) for item in reports) / len(reports), 4)
            if reports else None
        ),
        "role_contract_pass_rate": (
            round(sum(bool(item["role_contract_pass"]) for item in reports) / len(reports), 4)
            if reports else None
        ),
        "mean_addition_coverage": round(mean(additions), 4) if additions else None,
        "mean_baseline_preservation": (
            round(mean(preservation), 4) if preservation else None
        ),
        "visible_contract_violation_cases": sum(
            bool(item["visible_contract_violations"]) for item in reports
        ),
        "within_current_product_timeout_rate": (
            round(
                sum(item["within_current_product_timeout"] is True for item in reports)
                / len(reports),
                4,
            )
            if reports
            else None
        ),
        "mean_total_duration_seconds": (
            round(mean(durations), 3) if durations else None
        ),
    }


def _load_cases(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if int(payload.get("schema_version", 0)) != SCHEMA_VERSION:
        raise ValueError("unsupported revision-role case schema")
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("revision-role case file must contain non-empty cases")
    return payload, cases


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("benchmarks/revision_role/cases.json"),
    )
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-revision", default=None)
    parser.add_argument("--max-new-tokens", type=int, default=700)
    parser.add_argument("--timeout", type=float, default=300.0)
    parser.add_argument("--match-threshold", type=float, default=DEFAULT_MATCH_THRESHOLD)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)

    case_payload, cases = _load_cases(args.cases)
    reports: list[dict[str, Any]] = []
    for case in cases:
        prompt = build_revision_prompt(
            str(case["question"]),
            str(case["baseline_answer"]),
            [str(value) for value in case.get("points_to_integrate", [])],
            response_language=(
                "Dutch" if case.get("language") == "nl" else "English"
            ),
        )
        body = _ollama_generate(
            model_id=args.model_id,
            prompt=prompt,
            max_new_tokens=args.max_new_tokens,
            timeout=args.timeout,
        )
        reports.append(
            score_case(case, body, threshold=args.match_threshold)
        )

    report = {
        "artifact": ARTIFACT,
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "shadowseed_source_ref": os.environ.get("GITHUB_SHA", "working-tree"),
        "case_set": case_payload.get("case_set"),
        "case_set_version": case_payload.get("case_set_version"),
        "model_id": args.model_id,
        "model_revision": args.model_revision,
        "max_new_tokens": args.max_new_tokens,
        "provider_timeout_seconds_current_product": DEFAULT_PROVIDER_TIMEOUT_SECONDS,
        "benchmark_timeout_seconds": args.timeout,
        "match_threshold": args.match_threshold,
        "prompt_contract": dict(REVISION_PROMPT_META),
        "disclaimer": (
            "This benchmark isolates revision only. Fixed baselines and reviewer-supplied "
            "candidate perspectives are evaluation inputs, not runtime evidence or authority. "
            "GitHub-runner latency is not laptop latency."
        ),
        "summary": summarize(reports),
        "cases": reports,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
