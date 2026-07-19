"""Dedicated adversarial Gate benchmark for SSL 4.5.

This benchmark isolates one question that used to be hidden inside the broader
false-positive controls: does the current Validation Gate block misleading seed
promotion better than weaker baseline promotion rules?

The suite is intentionally still deterministic and local. It is not yet a full
human-reviewed adversarial layer, but it does make three things explicit:

- contradiction-heavy cases where a lure candidate is already covered by the
  answer and therefore should not survive promotion;
- tempting but unsupported lure candidates that weaker baselines would still
  promote;
- casebook artifacts that make the blocked-vs-baseline contrast readable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shadowseed.benchmark.evidence_layers import (
    ADVERSARIAL_NOISE_CONTROL,
    assert_valid_layer,
)
from shadowseed.benchmark.ssl45_false_positive_suite import evaluate_adversarial_candidate

EVIDENCE_LAYER = assert_valid_layer(ADVERSARIAL_NOISE_CONTROL)


def _safe_rate(numerator: int, denominator: int) -> float:
    return (numerator / denominator) if denominator else 0.0


def _relative_reduction(baseline_count: int, gate_count: int) -> float:
    if baseline_count <= 0:
        return 0.0
    return (baseline_count - gate_count) / baseline_count


def _casebook_markdown(payload: dict[str, Any]) -> str:
    s = payload["summary"]
    lines = [
        "# Adversarial Gate Casebook",
        "",
        "This casebook shows where weaker promotion rules would allow a lure seed that the current Gate blocks, and how the Gate handles legitimate gaps that should pass.",
        "",
        "## Samenvatting",
        "",
        f"- Scenario's: {s['scenario_count']}",
        f"- Adversarial candidates: {s['candidate_count']}  (negatief: {s['bad_candidate_count']}, positief met evidence: {s['good_with_evidence_count']}, positief zonder evidence: {s['good_without_evidence_count']})",
        f"- Trace-only promoties: {s['trace_only_promoted_count']}",
        f"- Trace without contradiction checks promoted: {s['trace_without_contradiction_promoted_count']}",
        f"- Gate-promoties totaal: {s['gate_promoted_count']}  (terecht: {s['promoted_good_count']}, false positives: {s['promoted_bad_count']})",
        f"- Geblokkeerd bad: {s['blocked_bad_count']} van {s['bad_candidate_count']}",
        f"- Gemist good met evidence: {s['missed_good_with_evidence_count']} van {s['good_with_evidence_count']}",
        f"- Correct outcomes: {s['correct_outcome_count']} van {s['candidate_count']}  ({s['correct_outcome_rate']:.2f})",
        f"- Baseline-only blokkades: {s['baseline_only_blocked_count']}",
        f"- Gate reduction versus trace-only: {s['gate_relative_reduction_vs_trace_only']:.2f}",
        f"- Gate reduction versus trace without contradiction checks: {s['gate_relative_reduction_vs_trace_without_contradiction']:.2f}",
        f"- Gate precision: {s['current_gate_precision']:.2f}, recall (op cases met evidence): {s['current_gate_recall']:.2f}, F1: {s['current_gate_f1']:.2f}",
        "",
    ]

    for scenario in payload["results"]:
        lines.extend(
            [
                f"## {scenario['scenario_id']} - {scenario['title']}",
                "",
                f"- Domein: {scenario['domain']}",
                f"- Type: {scenario['scenario_type']}",
                f"- Verwachte label: {scenario['expected_label']}",
                "",
            ]
        )
        for check in scenario["candidate_checks"]:
            label = check.get("expected_label", "not_gap")
            outcome = (
                "terecht gepromoteerd"
                if check["current_gate_promoted"] and label == "gap"
                else "false positive"
                if check["current_gate_promoted"]
                else "terecht geblokkeerd"
                if label == "not_gap"
                else "gemist (false negative)"
            )
            lines.extend(
                [
                    f"### {check['candidate']}  [{label}, {outcome}]",
                    "",
                    f"- Contradiction detected: {check['contradiction_detected']}",
                    f"- Evidence available: {check.get('evidence_available', False)}",
                    f"- Trace-only promoted: {check['trace_only_promoted']}",
                    f"- Trace without contradiction checks promoted: {check['trace_without_contradiction_promoted']}",
                    f"- Current gate promoted: {check['current_gate_promoted']}",
                    f"- Current gate verdict: {check['current_gate_verdict']}",
                    "",
                ]
            )
    return "\n".join(lines) + "\n"


def _build_false_positive_log(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scenario in results:
        for check in scenario["candidate_checks"]:
            candidate_label = check.get("expected_label", scenario["expected_label"])
            rows.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "title": scenario["title"],
                    "domain": scenario["domain"],
                    "scenario_type": scenario["scenario_type"],
                    "scenario_expected_label": scenario["expected_label"],
                    "candidate_expected_label": candidate_label,
                    "candidate_type": check.get("candidate_type"),
                    "evidence_available": check.get("evidence_available", False),
                    "candidate": check["candidate"],
                    "contradiction_detected": check["contradiction_detected"],
                    "trace_only_promoted": check["trace_only_promoted"],
                    "trace_without_contradiction_promoted": check["trace_without_contradiction_promoted"],
                    "current_gate_promoted": check["current_gate_promoted"],
                    "current_gate_verdict": check["current_gate_verdict"],
                    "baseline_only_blocked": (
                        (check["trace_only_promoted"] or check["trace_without_contradiction_promoted"])
                        and not check["current_gate_promoted"]
                    ),
                    "outcome": (
                        "promoted_true_positive"
                        if check["current_gate_promoted"] and candidate_label == "gap"
                        else "promoted_false_positive"
                        if check["current_gate_promoted"]
                        else "blocked_true_negative"
                        if candidate_label == "not_gap"
                        else "missed_false_negative"
                    ),
                }
            )
    return rows


def run_adversarial_gate_benchmark(
    input_path: str,
    output_path: str,
    casebook_path: str | None = None,
) -> Path:
    suite = json.loads(Path(input_path).read_text(encoding="utf-8"))
    results = []
    candidate_count = 0
    trace_only_promoted_count = 0
    trace_without_contradiction_promoted_count = 0
    gate_promoted_count = 0
    gate_blocked_count = 0
    contradiction_case_count = 0
    no_contradiction_case_count = 0
    baseline_only_blocked_count = 0

    bad_candidate_count = 0
    good_candidate_count = 0
    good_with_evidence_count = 0
    good_without_evidence_count = 0
    promoted_bad_count = 0
    promoted_good_count = 0
    promoted_good_with_evidence_count = 0
    blocked_bad_count = 0
    missed_good_with_evidence_count = 0
    correct_outcome_count = 0

    def _is_correct_outcome(check: dict[str, Any]) -> bool:
        """The Gate's decision is correct when:
        - a negative-control candidate is blocked, OR
        - a positive-control candidate with evidence is promoted, OR
        - a positive-control candidate without evidence is blocked (the Gate is
          supposed to require evidence even for legitimate gaps).
        """
        if check["expected_label"] == "not_gap":
            return not check["current_gate_promoted"]
        if check.get("evidence_available"):
            return check["current_gate_promoted"]
        return not check["current_gate_promoted"]

    for scenario in suite["scenarios"]:
        candidate_checks = []
        for candidate in scenario["adversarial_candidates"]:
            check = evaluate_adversarial_candidate(candidate, scenario)
            candidate_count += 1
            trace_only_promoted_count += int(check["trace_only_promoted"])
            trace_without_contradiction_promoted_count += int(
                check["trace_without_contradiction_promoted"]
            )
            gate_promoted_count += int(check["current_gate_promoted"])
            gate_blocked_count += int(not check["current_gate_promoted"])
            contradiction_case_count += int(check["contradiction_detected"])
            no_contradiction_case_count += int(not check["contradiction_detected"])
            baseline_only_blocked_count += int(
                (check["trace_only_promoted"] or check["trace_without_contradiction_promoted"])
                and not check["current_gate_promoted"]
            )

            is_good = check["expected_label"] == "gap"
            has_evidence = bool(check.get("evidence_available"))
            if is_good:
                good_candidate_count += 1
                if has_evidence:
                    good_with_evidence_count += 1
                    if check["current_gate_promoted"]:
                        promoted_good_with_evidence_count += 1
                    else:
                        missed_good_with_evidence_count += 1
                else:
                    good_without_evidence_count += 1
                if check["current_gate_promoted"]:
                    promoted_good_count += 1
            else:
                bad_candidate_count += 1
                if check["current_gate_promoted"]:
                    promoted_bad_count += 1
                else:
                    blocked_bad_count += 1

            if _is_correct_outcome(check):
                correct_outcome_count += 1

            candidate_checks.append(check)

        results.append(
            {
                "scenario_id": scenario["id"],
                "title": scenario["title"],
                "domain": scenario["domain"],
                "scenario_type": scenario["scenario_type"],
                "expected_label": scenario.get("expected_label", "not_gap"),
                "candidate_checks": candidate_checks,
                "passed": all(_is_correct_outcome(check) for check in candidate_checks),
            }
        )

    false_positive_log = _build_false_positive_log(results)
    # Discrimination metrics. Precision is computed against all promotions
    # (good vs bad). Recall is restricted to positive controls that come with
    # evidence_available=True: positives without evidence are designed to be
    # blocked by the Gate, so counting them as missed would conflate the Gate
    # working-as-designed with a recall failure.
    current_gate_precision = (
        promoted_good_count / (promoted_good_count + promoted_bad_count)
        if (promoted_good_count + promoted_bad_count) > 0
        else 0.0
    )
    current_gate_recall = (
        promoted_good_with_evidence_count / good_with_evidence_count
        if good_with_evidence_count > 0
        else 0.0
    )
    current_gate_f1 = (
        (2 * current_gate_precision * current_gate_recall)
        / (current_gate_precision + current_gate_recall)
        if (current_gate_precision + current_gate_recall) > 0
        else 0.0
    )

    summary = {
        "evidence_layer": EVIDENCE_LAYER,
        "suite_version": suite.get("version"),
        "scenario_count": len(suite["scenarios"]),
        "candidate_count": candidate_count,
        "trace_only_promoted_count": trace_only_promoted_count,
        "trace_without_contradiction_promoted_count": trace_without_contradiction_promoted_count,
        "gate_promoted_count": gate_promoted_count,
        "gate_blocked_count": gate_blocked_count,
        "contradiction_case_count": contradiction_case_count,
        "no_contradiction_case_count": no_contradiction_case_count,
        "baseline_only_blocked_count": baseline_only_blocked_count,
        # False-promotion rates are computed over negative-control candidates only
        # so adding positive-control candidates does not artificially lower them.
        "trace_only_false_promotion_rate": _safe_rate(
            sum(
                1
                for scenario in results
                for check in scenario["candidate_checks"]
                if check["expected_label"] == "not_gap" and check["trace_only_promoted"]
            ),
            bad_candidate_count,
        ),
        "trace_without_contradiction_false_promotion_rate": _safe_rate(
            sum(
                1
                for scenario in results
                for check in scenario["candidate_checks"]
                if check["expected_label"] == "not_gap"
                and check["trace_without_contradiction_promoted"]
            ),
            bad_candidate_count,
        ),
        "current_gate_false_promotion_rate": _safe_rate(promoted_bad_count, bad_candidate_count),
        "gate_block_rate": _safe_rate(gate_blocked_count, candidate_count),
        "gate_vs_trace_only_delta": trace_only_promoted_count - gate_promoted_count,
        "gate_vs_trace_without_contradiction_delta": (
            trace_without_contradiction_promoted_count - gate_promoted_count
        ),
        "gate_relative_reduction_vs_trace_only": _relative_reduction(
            trace_only_promoted_count,
            gate_promoted_count,
        ),
        "gate_relative_reduction_vs_trace_without_contradiction": _relative_reduction(
            trace_without_contradiction_promoted_count,
            gate_promoted_count,
        ),
        # Discrimination metrics treat the suite as a labelled set with
        # positive-control candidates (real gaps) and negative-control candidates
        # (lures). A high-precision Gate that misses every legitimate seed gets
        # a low recall and a low F1, which a refusal-only Gate cannot hide.
        "bad_candidate_count": bad_candidate_count,
        "good_candidate_count": good_candidate_count,
        "good_with_evidence_count": good_with_evidence_count,
        "good_without_evidence_count": good_without_evidence_count,
        "promoted_bad_count": promoted_bad_count,
        "promoted_good_count": promoted_good_count,
        "promoted_good_with_evidence_count": promoted_good_with_evidence_count,
        "blocked_bad_count": blocked_bad_count,
        "missed_good_with_evidence_count": missed_good_with_evidence_count,
        "correct_outcome_count": correct_outcome_count,
        "correct_outcome_rate": _safe_rate(correct_outcome_count, candidate_count),
        "current_gate_precision": current_gate_precision,
        "current_gate_recall": current_gate_recall,
        "current_gate_f1": current_gate_f1,
        "passed": (
            promoted_bad_count == 0
            and baseline_only_blocked_count > 0
            and correct_outcome_count == candidate_count
        ),
        "interpretation": (
            "Positive deltas and reduction rates mean weaker baselines would promote lure seeds "
            "that the current Gate blocks in this deterministic scaffold. Precision and recall "
            "treat candidates as a labelled set so a refusal-only Gate cannot pass by blocking "
            "everything."
        ),
    }
    baseline_summaries = {
        "current_gate": {
            "promoted_count": gate_promoted_count,
            "false_promotion_rate": summary["current_gate_false_promotion_rate"],
        },
        "trace_only": {
            "promoted_count": trace_only_promoted_count,
            "false_promotion_rate": summary["trace_only_false_promotion_rate"],
        },
        "trace_without_contradiction": {
            "promoted_count": trace_without_contradiction_promoted_count,
            "false_promotion_rate": summary["trace_without_contradiction_false_promotion_rate"],
        },
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary,
        "baseline_summaries": baseline_summaries,
        "false_positive_log": false_positive_log,
        "results": results,
    }
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    casebook_file = Path(casebook_path) if casebook_path else output.with_name("adversarial_gate_casebook.md")
    casebook_file.parent.mkdir(parents=True, exist_ok=True)
    casebook_file.write_text(_casebook_markdown(payload), encoding="utf-8")
    return output
