"""Optional benchmark runner for paper-derived scenarios.

This does not modify or merge with the core SSL benchmark suites. It reads
scenarios created by the paper pipeline and evaluates whether they are usable as
separate candidate benchmark cases.
"""

from __future__ import annotations

import json
from pathlib import Path


PAPER_INGEST_DIR = Path("results/paper_ingest")


def load_paper_scenarios(input_dir: str = str(PAPER_INGEST_DIR)) -> list[dict]:
    root = Path(input_dir)
    scenarios: list[dict] = []
    if not root.exists():
        return scenarios
    for path in sorted(root.glob("*/scenarios.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        paper_id = path.parent.name
        for index, scenario in enumerate(data, start=1):
            scenarios.append(
                {
                    "paper_id": paper_id,
                    "scenario_id": f"{paper_id}_scenario_{index:03d}",
                    "question": scenario.get("question", ""),
                    "expected_additions": scenario.get("expected_additions", []),
                    "status": "candidate",
                    "source": "paper_pipeline",
                }
            )
    return scenarios


def score_candidate_scenario(scenario: dict) -> dict:
    question = scenario.get("question", "")
    expected = scenario.get("expected_additions", [])
    usable = bool(question.strip()) and isinstance(expected, list) and len(expected) >= 1
    return {
        "scenario_id": scenario["scenario_id"],
        "paper_id": scenario["paper_id"],
        "usable": usable,
        "question_length": len(question.split()),
        "expected_count": len(expected),
        "status": "candidate" if usable else "needs_review",
    }


def run_paper_scenario_smoke(
    input_dir: str = str(PAPER_INGEST_DIR),
    output_path: str = "results/paper_scenario_smoke.json",
) -> Path:
    scenarios = load_paper_scenarios(input_dir)
    scored = [score_candidate_scenario(scenario) for scenario in scenarios]
    usable_count = sum(1 for item in scored if item["usable"])

    payload = {
        "summary": {
            "passed": len(scenarios) == 0 or usable_count > 0,
            "scenario_count": len(scenarios),
            "usable_count": usable_count,
            "needs_review_count": len(scored) - usable_count,
            "interpretation": "Paper scenarios are optional candidate benchmarks and are not merged into core suites automatically.",
        },
        "scenarios": scenarios,
        "scored": scored,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(run_paper_scenario_smoke())
