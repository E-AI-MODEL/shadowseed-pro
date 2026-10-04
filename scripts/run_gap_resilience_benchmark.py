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
import urllib.request
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from shadowseed.adapters.ollama_client import ollama_host
from shadowseed.detection.model_detector import (
    CURRENT_PAIR_PROMPT_META,
    build_detection_prompt,
    make_detector_backend,
    parse_numbered_seeds_with_diagnostics,
)

SCHEMA_VERSION = 1
ARTIFACT = "shadowseed-gap-resilience-v1"
DEFAULT_MATCH_THRESHOLD = 0.35


EXPERIMENTAL_PROMPTS: dict[str, str] = {
    "candidate_v1": """
You analyse one user question, a draft answer, and optional bounded prior context.

Name up to {max_seeds} plausible unresolved information gaps that may still
deserve checking for this specific question.

A candidate gap is only a dimension or information slot to investigate. It is
NOT a claim that the gap is definitely real, important, correct, supported, or
eligible to influence an answer. You may name a relevant dimension even when
the draft does not mention it explicitly, but never invent the missing value or
answer.

Use prior context only to avoid reopening something already established.

Rules:
- Use the same language as CURRENT QUESTION.
- Each candidate names exactly one unresolved dimension.
- Prefer a concrete relation, condition, dependency, criterion, timing,
  ownership, interface, or distinction when relevant to the question.
- Do not invent facts, values, names, numbers, quotations, or sources.
- Do not output a gap that the draft or bounded prior context already answers.
- Do not rank, validate, complete, or explain candidates.
- Return one numbered candidate per line.
- Return exactly NONE only when no plausible unresolved dimension directly
  relevant to the user's current question can be named without inventing its
  answer.

BOUNDED PRIOR CONTEXT:
{conversation_context}

CURRENT QUESTION:
{question}

DRAFT ANSWER:
{answer}

OUTPUT:
""".strip(),
    "candidate_v2": """
Perform a contrastive coverage check of the current exchange.

First use DRAFT ANSWER and BOUNDED PRIOR CONTEXT only to subtract what is
already established. Then output up to {max_seeds} concrete information slots
that remain plausibly unresolved for answering CURRENT QUESTION.

The output is exploratory detector material only. Naming a slot does not prove
that it is missing, useful, true, supported, or authorized. Do not supply the
answer to the slot.

Rules:
- Use the same language as CURRENT QUESTION.
- One candidate = one information slot.
- A candidate may be a noun phrase or concise question-like label.
- Prefer specific conditions, criteria, dependencies, timing, ownership,
  failure behavior, interfaces, or distinctions over generic checklist items.
- Do not invent facts, values, sources, names, or quotations.
- Never repeat a slot already settled by the draft or prior context.
- Return one numbered candidate per line, no commentary.
- Return exactly NONE only when every material slot you can name for this
  specific question is already settled by the draft or bounded prior context.

BOUNDED PRIOR CONTEXT:
{conversation_context}

CURRENT QUESTION:
{question}

DRAFT ANSWER:
{answer}

OUTPUT:
""".strip(),
}


class BenchmarkOllamaDetector:
    """Benchmark-only Ollama arm with explicit thinking capture.

    This never changes the product runtime. It exists so reasoning-model output
    can be measured without mistaking an empty final response for abstention.
    """

    def __init__(
        self,
        model_id: str,
        profile: str,
        max_new_tokens: int,
        *,
        thinking_mode: str = "default",
    ) -> None:
        if profile not in {"runtime_v06", *EXPERIMENTAL_PROMPTS}:
            raise ValueError(f"unknown benchmark prompt profile: {profile}")
        if thinking_mode not in {"default", "on", "off"}:
            raise ValueError(f"unknown thinking mode: {thinking_mode}")
        self.name = f"ollama:{model_id}:{profile}:{thinking_mode}"
        self.model_id = model_id
        self.profile = profile
        self.max_new_tokens = max_new_tokens
        self.thinking_mode = thinking_mode
        self.host = ollama_host()
        self.last_raw_output: str | None = None
        self.last_thinking_output: str | None = None
        self.last_parse_diagnostics: dict[str, int | bool] | None = None
        self.last_prompt_metadata: dict[str, Any] | None = None
        self.last_provider_metadata: dict[str, Any] | None = None

    def _prompt(self, item: dict[str, Any], max_seeds: int) -> tuple[str, str]:
        question = str(item.get("question") or "").strip()
        answer = str(item.get("text") or item.get("input") or "").strip()
        context = str(item.get("conversation_context") or "NONE").strip() or "NONE"
        if self.profile == "runtime_v06":
            prompt = build_detection_prompt(
                answer,
                max_seeds=max_seeds,
                variant="current_pair",
                question=question,
                conversation_context=context,
            )
            self.last_prompt_metadata = dict(CURRENT_PAIR_PROMPT_META)
        else:
            prompt = EXPERIMENTAL_PROMPTS[self.profile].format(
                max_seeds=max_seeds,
                conversation_context=context,
                question=question,
                answer=answer,
            )
            self.last_prompt_metadata = {
                "prompt_id": f"benchmark_gap_resilience_{self.profile}",
                "prompt_profile": self.profile,
                "authority": "benchmark_only",
            }
        return prompt, answer

    def detect_seeds(self, item: dict[str, Any], max_seeds: int = 5) -> list[str]:
        prompt, answer = self._prompt(item, max_seeds)
        if not answer:
            self.last_raw_output = ""
            self.last_thinking_output = ""
            self.last_parse_diagnostics = {
                "explicit_none": False,
                "nonblank_lines": 0,
                "numbered_lines": 0,
                "unnumbered_nonblank_lines": 0,
                "nested_numbering_prefixes_removed": 0,
                "dropped_blank_or_placeholder": 0,
                "dropped_citation_or_stub": 0,
                "dropped_fewshot_leak": 0,
                "dropped_duplicate": 0,
                "accepted_candidates": 0,
                "truncated_after_max_seeds": False,
            }
            return []

        payload: dict[str, Any] = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": self.max_new_tokens,
                "seed": 0,
            },
        }
        if self.thinking_mode != "default":
            payload["think"] = self.thinking_mode == "on"

        request = urllib.request.Request(
            f"{self.host}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=600) as response:
            body = json.loads(response.read().decode("utf-8"))

        raw = str(body.get("response") or "")
        thinking = str(body.get("thinking") or "")
        seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
            raw, max_seeds=max_seeds, source_text=answer
        )
        self.last_raw_output = raw
        self.last_thinking_output = thinking
        self.last_parse_diagnostics = diagnostics
        self.last_provider_metadata = {
            key: body.get(key)
            for key in (
                "done_reason",
                "total_duration",
                "load_duration",
                "prompt_eval_count",
                "eval_count",
            )
            if key in body
        }
        return seeds


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
    run_audits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    expected = _groups(case, "expected_gap_groups")
    resolved = _groups(case, "resolved_gap_groups")
    negative_control = bool(case.get("negative_control", False))

    expected_opportunities = len(expected) * len(runs)
    expected_hits = 0
    resolved_opportunities = len(resolved) * len(runs)
    resolved_reopens = 0
    empty_runs = 0
    explicit_none_runs = 0
    parser_empty_non_none_runs = 0
    run_details: list[dict[str, Any]] = []

    for index, candidates in enumerate(runs, start=1):
        candidates = [str(value).strip() for value in candidates if str(value).strip()]
        audit = (
            run_audits[index - 1]
            if run_audits is not None and index - 1 < len(run_audits)
            else {}
        )
        parse_diagnostics = audit.get("parse_diagnostics") or {}
        if not candidates:
            empty_runs += 1
            if parse_diagnostics.get("explicit_none"):
                explicit_none_runs += 1
            elif audit.get("raw_output"):
                parser_empty_non_none_runs += 1

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
                "detector_raw_output": audit.get("raw_output"),
                "detector_parse_diagnostics": parse_diagnostics or None,
                "detector_prompt_metadata": audit.get("prompt_metadata"),
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
        "explicit_none_runs": explicit_none_runs,
        "parser_empty_non_none_runs": parser_empty_non_none_runs,
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
    explicit_none_runs = sum(int(item.get("explicit_none_runs", 0)) for item in case_reports)
    parser_empty_non_none_runs = sum(
        int(item.get("parser_empty_non_none_runs", 0)) for item in case_reports
    )

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
        "explicit_none_runs": explicit_none_runs,
        "parser_empty_non_none_runs": parser_empty_non_none_runs,
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
            runs.append(
                list(
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
            )
            audits.append(
                {
                    "raw_output": getattr(detector, "last_raw_output", None),
                    "parse_diagnostics": getattr(
                        detector, "last_parse_diagnostics", None
                    ),
                    "prompt_metadata": getattr(detector, "last_prompt_metadata", None),
                }
            )
        reports.append(
            score_case(
                case,
                runs,
                threshold=threshold,
                run_audits=audits,
            )
        )

    return {"summary": summarize(reports), "cases": reports}


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
    parser.add_argument(
        "--prompt-profile",
        choices=("runtime_v06", "candidate_v1", "candidate_v2"),
        default="runtime_v06",
    )
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--max-seeds", type=int, default=5)
    parser.add_argument("--max-new-tokens", type=int, default=400)
    parser.add_argument("--match-threshold", type=float, default=DEFAULT_MATCH_THRESHOLD)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)

    case_payload, cases = _load_cases(args.cases)
    if args.prompt_profile == "runtime_v06":
        detector = make_detector_backend(
            args.backend,
            model_id=args.model_id,
            max_new_tokens=args.max_new_tokens,
            prompt_variant="current_pair",
            model_revision=args.model_revision,
        )
    else:
        if args.backend != "ollama":
            raise ValueError("experimental prompt profiles currently require --backend ollama")
        if not args.model_id:
            raise ValueError("experimental prompt profiles require --model-id")
        detector = ExperimentalOllamaDetector(
            model_id=args.model_id,
            profile=args.prompt_profile,
            max_new_tokens=args.max_new_tokens,
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
        "prompt_profile": args.prompt_profile,
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
