"""Probe feedback behavioral suite for Layer E.

The existing `ssl45_probe_utility_suite` measures whether SSL-guided follow-up
prompts are more specific than baseline prompts. That is one half of Layer E
("leveren promoted seeds echt betere vervolgstappen op?"). This suite covers
the other half: the doc question "**expliciete behavioral metrics**" — does
the feedback loop in `SSLManager.apply_probe_feedback` actually change weight,
status and lifecycle in the way the 4.6 spec claims?

Each scenario forces a seed into a known initial state (weight, status,
occurrence_count, trace, evidence_count), applies a sequence of probe outcomes
and asserts the expected final state. The suite reports per-category pass
rates and a single behavioral_outcome_rate, so a regression that silently
disables reward/penalty/clamp/demotion would fail loudly.

The suite does not assert that probe feedback is *useful* — that is what the
prompt-quality side of Layer E and the human-reviewed open-set rounds are
for. It only asserts that the mechanism works as documented.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from shadowseed.benchmark.evidence_layers import PROBE_UTILITY, assert_valid_layer
from shadowseed.text_similarity import lexical_embedding
from shadowseed.manager import ProbeOutcome, ProbeType, SSLManager, SeedStatus

EVIDENCE_LAYER = assert_valid_layer(PROBE_UTILITY)


WEIGHT_TOLERANCE = 1e-6


def _force_seed_state(manager: SSLManager, text: str, state: dict[str, Any]) -> str:
    """Seed the manager with one seed and force it into the requested state."""
    seed_id = manager.add_or_update_seed(text, trigger_keywords=["probe", "behavior"])
    seed = manager.seeds[seed_id]
    # Benchmark fixture: force an edge-case authority state without a full Gate
    # run. Authority fields are otherwise read-only outside the Gate.
    seed.unsafe_set_authority(
        weight=float(state.get("weight", 0.0)),
        status=SeedStatus(state.get("status", "ACTIVE")),
        evidence_count=int(state.get("evidence_count", 0)),
    )
    seed.occurrence_count = int(state.get("occurrence_count", 1))
    seed.trace = float(state.get("trace", 1.0))
    return seed_id


def _weights_match(observed: float, expected: float) -> bool:
    return math.isclose(observed, expected, abs_tol=WEIGHT_TOLERANCE)


def _evaluate_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = _force_seed_state(
        manager,
        text=f"Probe behavior seed for {scenario['id']}",
        state=scenario["initial_state"],
    )

    feedback_results: list[dict[str, Any]] = []
    skip_count = 0
    demotion_count = 0
    for step in scenario.get("feedback_sequence", []):
        result = manager.apply_probe_feedback(
            seed_id=seed_id,
            outcome=ProbeOutcome(step["outcome"]),
            probe_type=ProbeType(step.get("probe_type", "general")),
        )
        if result.skipped:
            skip_count += 1
        if result.demoted:
            demotion_count += 1
        feedback_results.append(
            {
                "outcome": result.outcome,
                "probe_type": result.probe_type,
                "weight_before": result.weight_before,
                "weight_after": result.weight_after,
                "delta_applied": result.delta_applied,
                "status_before": result.status_before,
                "status_after": result.status_after,
                "demoted": result.demoted,
                "skipped": result.skipped,
                "skip_reason": result.skip_reason,
            }
        )

    seed = manager.seeds[seed_id]
    expected = scenario["expected"]
    observed = {
        "weight": seed.weight,
        "status": seed.status.value,
        "demoted": demotion_count > 0,
        "skip_count": skip_count,
    }
    mismatches: list[str] = []
    if not _weights_match(observed["weight"], float(expected["weight"])):
        mismatches.append(
            f"weight: expected {expected['weight']:.4f}, observed {observed['weight']:.4f}"
        )
    if observed["status"] != expected["status"]:
        mismatches.append(
            f"status: expected {expected['status']}, observed {observed['status']}"
        )
    if bool(observed["demoted"]) != bool(expected.get("demoted", False)):
        mismatches.append(
            f"demoted: expected {expected.get('demoted', False)}, observed {observed['demoted']}"
        )
    if int(observed["skip_count"]) != int(expected.get("skip_count", 0)):
        mismatches.append(
            f"skip_count: expected {expected.get('skip_count', 0)}, observed {observed['skip_count']}"
        )

    return {
        "scenario_id": scenario["id"],
        "title": scenario["title"],
        "category": scenario.get("category", "uncategorized"),
        "initial_state": scenario["initial_state"],
        "feedback_sequence": scenario.get("feedback_sequence", []),
        "expected": expected,
        "observed": observed,
        "feedback_results": feedback_results,
        "correct_outcome": not mismatches,
        "mismatches": mismatches,
    }


def _safe_rate(num: int, denom: int) -> float:
    return (num / denom) if denom else 0.0


def _casebook_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        "# Probe Feedback Behavior Casebook",
        "",
        "This casebook checks whether the probe-feedback lifecycle, including reward, penalty, clamping, demotion, and status blocking, behaves as specified.",
        "",
        "## Samenvatting",
        "",
        f"- Scenarios: {s['scenario_count']}",
        f"- Correct outcomes: {s['correct_outcome_count']} van {s['scenario_count']} ({s['correct_outcome_rate']:.2f})",
        "",
        "### Per categorie",
        "",
    ]
    for category, stats in sorted(s["per_category"].items()):
        lines.append(
            f"- {category}: {stats['correct']} / {stats['total']} correct"
        )
    lines.append("")

    for scenario in payload["results"]:
        verdict = "PASS" if scenario["correct_outcome"] else "FAIL"
        lines.extend(
            [
                f"## {scenario['scenario_id']} - {scenario['title']}  [{scenario['category']}, {verdict}]",
                "",
                f"- Initial: weight={scenario['initial_state']['weight']}, status={scenario['initial_state']['status']}",
                f"- Feedback: {len(scenario['feedback_sequence'])} steps",
                f"- Expected: weight={scenario['expected']['weight']}, status={scenario['expected']['status']}, demoted={scenario['expected'].get('demoted', False)}, skip_count={scenario['expected'].get('skip_count', 0)}",
                f"- Observed: weight={scenario['observed']['weight']:.4f}, status={scenario['observed']['status']}, demoted={scenario['observed']['demoted']}, skip_count={scenario['observed']['skip_count']}",
                "",
            ]
        )
        if scenario["mismatches"]:
            lines.append("Mismatches:")
            for m in scenario["mismatches"]:
                lines.append(f"  - {m}")
            lines.append("")
    return "\n".join(lines) + "\n"


def run_probe_feedback_behavior_suite(
    input_path: str,
    output_path: str,
    casebook_path: str | None = None,
) -> Path:
    suite = json.loads(Path(input_path).read_text(encoding="utf-8"))
    results = [_evaluate_scenario(scenario) for scenario in suite["scenarios"]]

    correct = sum(1 for r in results if r["correct_outcome"])
    per_category: dict[str, dict[str, int]] = {}
    for r in results:
        bucket = per_category.setdefault(
            r["category"], {"total": 0, "correct": 0}
        )
        bucket["total"] += 1
        if r["correct_outcome"]:
            bucket["correct"] += 1

    summary = {
        "evidence_layer": EVIDENCE_LAYER,
        "suite_version": suite.get("version"),
        "scenario_count": len(results),
        "correct_outcome_count": correct,
        "correct_outcome_rate": _safe_rate(correct, len(results)),
        "per_category": per_category,
        "passed": correct == len(results) and len(results) > 0,
        "interpretation": (
            "Each scenario forces a seed into a known state and applies a "
            "sequence of probe outcomes. Correct outcome means the resulting "
            "weight, status, demotion flag and skip count match the expected "
            "lifecycle behavior per docs/00_shadow_seed_learning_4_6.md."
        ),
    }

    payload = {"summary": summary, "results": results}
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    casebook_file = (
        Path(casebook_path)
        if casebook_path
        else output.with_name("probe_feedback_behavior_casebook.md")
    )
    casebook_file.parent.mkdir(parents=True, exist_ok=True)
    casebook_file.write_text(_casebook_markdown(payload), encoding="utf-8")
    return output
