"""Probe utility benchmark for SSL 4.5.

This suite treats promoted seeds as instruments for follow-up action and asks a
narrow question: are the seed-guided probes sharper than broad baseline probes?

The benchmark is intentionally local and deterministic. It does not claim human
preference yet; it creates a first measurable layer for:

- Socratic follow-up quality;
- retrieval query sharpness;
- dialectical falsification sharpness.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from shadowseed.benchmark.evidence_layers import PROBE_UTILITY, assert_valid_layer

EVIDENCE_LAYER = assert_valid_layer(PROBE_UTILITY)


BROAD_WORDS = {
    "meer",
    "algemeen",
    "context",
    "extra",
    "analyse",
    "verbeteren",
    "iets",
    "security",
}


def words(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text.lower()))


def count_expected_terms(text: str, expected_terms: list[str]) -> int:
    token_set = words(text)
    total = 0
    for term in expected_terms:
        term_tokens = words(term)
        if term_tokens and term_tokens.issubset(token_set):
            total += 1
    return total


def count_broad_terms(text: str, forbidden_terms: list[str]) -> int:
    token_set = words(text)
    forbidden = set(forbidden_terms) | BROAD_WORDS
    return sum(1 for term in forbidden if term.lower() in token_set)


def specificity_score(text: str, expected_terms: list[str], forbidden_terms: list[str]) -> float:
    expected_hits = count_expected_terms(text, expected_terms)
    broad_hits = count_broad_terms(text, forbidden_terms)
    return float(expected_hits) - 0.5 * float(broad_hits)


def evaluate_probe_pair(scenario: dict) -> dict:
    baseline_follow = specificity_score(
        scenario["baseline_follow_up"],
        scenario["expected_terms"],
        scenario["forbidden_broad_terms"],
    )
    ssl_follow = specificity_score(
        scenario["ssl_follow_up"],
        scenario["expected_terms"],
        scenario["forbidden_broad_terms"],
    )

    baseline_retrieval = specificity_score(
        scenario["baseline_retrieval_query"],
        scenario["expected_terms"],
        scenario["forbidden_broad_terms"],
    )
    ssl_retrieval = specificity_score(
        scenario["ssl_retrieval_query"],
        scenario["expected_terms"],
        scenario["forbidden_broad_terms"],
    )

    baseline_dialectic = specificity_score(
        scenario["baseline_dialectic"],
        scenario["expected_terms"],
        scenario["forbidden_broad_terms"],
    )
    ssl_dialectic = specificity_score(
        scenario["ssl_dialectic"],
        scenario["expected_terms"],
        scenario["forbidden_broad_terms"],
    )

    return {
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "domain": scenario["domain"],
        "seed": scenario["seed"],
        "baseline_follow_up": scenario["baseline_follow_up"],
        "ssl_follow_up": scenario["ssl_follow_up"],
        "baseline_retrieval_query": scenario["baseline_retrieval_query"],
        "ssl_retrieval_query": scenario["ssl_retrieval_query"],
        "baseline_dialectic": scenario["baseline_dialectic"],
        "ssl_dialectic": scenario["ssl_dialectic"],
        "baseline_follow_up_score": baseline_follow,
        "ssl_follow_up_score": ssl_follow,
        "follow_up_delta": ssl_follow - baseline_follow,
        "baseline_retrieval_score": baseline_retrieval,
        "ssl_retrieval_score": ssl_retrieval,
        "retrieval_delta": ssl_retrieval - baseline_retrieval,
        "baseline_dialectic_score": baseline_dialectic,
        "ssl_dialectic_score": ssl_dialectic,
        "dialectic_delta": ssl_dialectic - baseline_dialectic,
    }


def run_ssl45_probe_utility_suite(input_path: str, output_path: str) -> Path:
    suite = json.loads(Path(input_path).read_text(encoding="utf-8"))
    results = [evaluate_probe_pair(scenario) for scenario in suite["scenarios"]]

    count = len(results)
    follow_delta = sum(item["follow_up_delta"] for item in results) / count if count else 0.0
    retrieval_delta = sum(item["retrieval_delta"] for item in results) / count if count else 0.0
    dialectic_delta = sum(item["dialectic_delta"] for item in results) / count if count else 0.0

    summary = {
        "evidence_layer": EVIDENCE_LAYER,
        "suite_version": suite.get("version"),
        "scenario_count": count,
        "mean_follow_up_delta": follow_delta,
        "mean_retrieval_delta": retrieval_delta,
        "mean_dialectic_delta": dialectic_delta,
        "overall_probe_utility_delta": (follow_delta + retrieval_delta + dialectic_delta) / 3.0,
        "passed": follow_delta > 0 and retrieval_delta > 0 and dialectic_delta > 0,
        "interpretation": (
            "Positive deltas mean the seed-guided probes are lexically and structurally sharper than the broad baseline probes in this local scaffold."
        ),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
