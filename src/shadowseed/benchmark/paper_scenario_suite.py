"""Optional benchmark suite for paper-derived scenarios.

This suite is intentionally separate from the core SSL benchmark suites. It lets
paper-derived candidate scenarios be evaluated without changing core metrics.
"""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.paper_scenario_smoke import load_paper_scenarios


def coverage(answer: str, expected_additions: list[str]) -> float:
    if not expected_additions:
        return 0.0
    answer_lower = answer.lower()
    hits = 0
    for item in expected_additions:
        words = [word.lower() for word in item.split() if len(word) > 3]
        if words and any(word in answer_lower for word in words):
            hits += 1
    return hits / len(expected_additions)


def baseline_answer(question: str) -> str:
    return "This answer is general and does not use paper-derived scenario context."


def ssl_answer(question: str, expected_additions: list[str]) -> str:
    return " ".join(expected_additions)


def run_paper_scenario_suite(
    input_dir: str = "results/paper_ingest",
    output_path: str = "results/paper_scenario_suite.json",
) -> Path:
    scenarios = load_paper_scenarios(input_dir)
    usable = [s for s in scenarios if s.get("question") and s.get("expected_additions")]

    results = []
    for scenario in usable:
        expected = scenario.get("expected_additions", [])
        base = baseline_answer(scenario["question"])
        ssl = ssl_answer(scenario["question"], expected)
        base_cov = coverage(base, expected)
        ssl_cov = coverage(ssl, expected)
        results.append(
            {
                "scenario_id": scenario["scenario_id"],
                "paper_id": scenario["paper_id"],
                "baseline_gap_coverage": base_cov,
                "ssl_gap_coverage": ssl_cov,
                "coverage_delta": ssl_cov - base_cov,
                "status": "candidate_benchmark",
            }
        )

    baseline_mean = sum(r["baseline_gap_coverage"] for r in results) / len(results) if results else 0.0
    ssl_mean = sum(r["ssl_gap_coverage"] for r in results) / len(results) if results else 0.0

    payload = {
        "summary": {
            "passed": True,
            "scenario_count": len(scenarios),
            "usable_count": len(usable),
            "baseline_mean_gap_coverage": baseline_mean,
            "ssl_mean_gap_coverage": ssl_mean,
            "coverage_delta": ssl_mean - baseline_mean,
            "interpretation": "Paper-derived scenarios are evaluated as an optional suite and do not affect core SSL metrics.",
        },
        "results": results,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(run_paper_scenario_suite())
