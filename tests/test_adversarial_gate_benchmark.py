from __future__ import annotations

import json
from pathlib import Path

from shadowseed.analysis.ssl45_result_analyzer import analyze_results
from shadowseed.benchmark.adversarial_gate_benchmark import run_adversarial_gate_benchmark


DATA = "src/shadowseed/data/adversarial_gate_benchmark.json"


def test_adversarial_gate_benchmark_blocks_lures_and_writes_casebook(tmp_path: Path) -> None:
    output = tmp_path / "adversarial_gate.json"
    casebook = tmp_path / "adversarial_gate_casebook.md"
    run_adversarial_gate_benchmark(DATA, str(output), casebook_path=str(casebook))

    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["summary"]
    baseline_summaries = payload["baseline_summaries"]
    false_positive_log = payload["false_positive_log"]
    casebook_text = casebook.read_text(encoding="utf-8")

    # The fixture now contains a mix of negative-control candidates and
    # positive-control candidates (with and without external evidence).
    assert summary["scenario_count"] >= 5
    assert summary["candidate_count"] >= 10
    assert summary["bad_candidate_count"] > 0
    assert summary["good_with_evidence_count"] > 0
    assert summary["promoted_bad_count"] == 0
    assert summary["promoted_good_with_evidence_count"] == summary["good_with_evidence_count"]
    assert summary["missed_good_with_evidence_count"] == 0
    assert summary["correct_outcome_count"] == summary["candidate_count"]
    assert summary["correct_outcome_rate"] == 1.0
    assert summary["current_gate_precision"] == 1.0
    assert summary["current_gate_recall"] == 1.0
    assert summary["current_gate_f1"] == 1.0
    assert summary["trace_only_promoted_count"] > 0
    assert summary["gate_vs_trace_only_delta"] > 0
    assert summary["baseline_only_blocked_count"] > 0
    assert summary["current_gate_false_promotion_rate"] == 0.0
    assert summary["trace_only_false_promotion_rate"] > 0.0
    assert summary["gate_relative_reduction_vs_trace_only"] > 0.0
    assert summary["passed"] is True

    assert baseline_summaries["current_gate"]["promoted_count"] == summary["gate_promoted_count"]
    assert baseline_summaries["trace_only"]["promoted_count"] == summary["trace_only_promoted_count"]
    assert len(false_positive_log) == summary["candidate_count"]
    assert any(row["baseline_only_blocked"] for row in false_positive_log)
    outcomes = {row["outcome"] for row in false_positive_log}
    assert "blocked_true_negative" in outcomes
    assert "promoted_true_positive" in outcomes

    assert "Adversarial Gate Casebook" in casebook_text
    assert "Trace-only promoted" in casebook_text
    assert "Gate reduction versus trace-only" in casebook_text
    assert "Gate precision" in casebook_text


def test_adversarial_gate_benchmark_correctly_refuses_positive_without_evidence(tmp_path: Path) -> None:
    """Positive controls without evidence must be blocked: the Gate is supposed
    to require evidence even when the seed is a legitimate gap."""
    output = tmp_path / "adversarial_gate.json"
    run_adversarial_gate_benchmark(DATA, str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    log = payload["false_positive_log"]

    refused_without_evidence = [
        row for row in log
        if row["candidate_expected_label"] == "gap"
        and not row["evidence_available"]
    ]
    assert refused_without_evidence, "fixture must include positive controls without evidence"
    for row in refused_without_evidence:
        assert not row["current_gate_promoted"], (
            f"positive control without evidence was promoted: {row['candidate']!r}"
        )


def test_adversarial_gate_benchmark_backwards_compatible_with_bare_string_candidates(
    tmp_path: Path,
) -> None:
    """A legacy fixture that still uses bare-string candidates must still run
    and treat them as not_gap candidates without external evidence."""
    legacy_fixture = {
        "version": "adversarial-gate-legacy",
        "description": "Legacy fixture with bare-string candidates",
        "scenarios": [
            {
                "id": "LEGACY_A",
                "title": "Volledig antwoord",
                "domain": "test",
                "scenario_type": "complete-answer",
                "expected_label": "not_gap",
                "input": "Het antwoord behandelt al de centrale punten over alpha, beta en gamma volledig.",
                "adversarial_candidates": [
                    "Alpha als centrale factor in deze redenering.",
                    "Beta als secundaire factor.",
                ],
            }
        ],
    }
    fixture_path = tmp_path / "legacy_fixture.json"
    fixture_path.write_text(json.dumps(legacy_fixture), encoding="utf-8")
    output = tmp_path / "out.json"
    run_adversarial_gate_benchmark(str(fixture_path), str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    log = payload["false_positive_log"]
    assert len(log) == 2
    for row in log:
        assert row["candidate_expected_label"] == "not_gap"
        assert row["evidence_available"] is False
        assert row["candidate_type"] is None


def test_analyze_results_includes_adversarial_gate_metrics(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    output_dir = tmp_path / "analysis"
    results_dir.mkdir()

    adversarial_payload = {
        "summary": {
            "scenario_count": 2,
            "candidate_count": 4,
            "current_gate_false_promotion_rate": 0.0,
            "trace_only_false_promotion_rate": 0.5,
            "trace_without_contradiction_false_promotion_rate": 0.25,
            "gate_relative_reduction_vs_trace_only": 1.0,
            "gate_relative_reduction_vs_trace_without_contradiction": 1.0,
            "gate_vs_trace_only_delta": 2,
        },
        "baseline_summaries": {
            "current_gate": {"promoted_count": 0, "false_promotion_rate": 0.0},
            "trace_only": {"promoted_count": 2, "false_promotion_rate": 0.5},
            "trace_without_contradiction": {"promoted_count": 1, "false_promotion_rate": 0.25},
        },
        "false_positive_log": [],
        "results": [],
    }
    (results_dir / "adversarial_gate_benchmark.json").write_text(
        json.dumps(adversarial_payload, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report_path = analyze_results(str(results_dir), str(output_dir))
    report_text = report_path.read_text(encoding="utf-8")
    summary_payload = json.loads((output_dir / "analysis_summary.json").read_text(encoding="utf-8"))

    assert summary_payload["adversarial_gate"]["current_gate_false_promotion_rate"] == 0.0
    assert summary_payload["conclusion"]["metrics"]["adversarial_trace_only_false_promotion_rate"] == 0.5
    assert "Adversarial Gate current FP rate" in report_text
    assert "Gate reduction versus trace-only" in report_text
    assert "The adversarial Gate layer shows" in report_text


def test_analyze_results_surfaces_adversarial_discrimination_and_probe_behavior(tmp_path: Path) -> None:
    """The analyzer must surface the v0.3-era discrimination metrics
    (precision/recall/F1/correct_outcome_rate) and the probe-feedback
    behavioral suite, so Layer D/E evidence reaches the published summary."""
    results_dir = tmp_path / "results"
    output_dir = tmp_path / "analysis"
    results_dir.mkdir()

    (results_dir / "adversarial_gate_benchmark.json").write_text(
        json.dumps({
            "summary": {
                "candidate_count": 21,
                "current_gate_false_promotion_rate": 0.0,
                "trace_only_false_promotion_rate": 0.5,
                "current_gate_precision": 1.0,
                "current_gate_recall": 1.0,
                "current_gate_f1": 1.0,
                "correct_outcome_rate": 1.0,
            }
        }), encoding="utf-8",
    )
    (results_dir / "probe_feedback_behavior_suite.json").write_text(
        json.dumps({
            "summary": {
                "scenario_count": 10,
                "correct_outcome_count": 10,
                "correct_outcome_rate": 1.0,
                "passed": True,
            }
        }), encoding="utf-8",
    )

    report_path = analyze_results(str(results_dir), str(output_dir))
    report_text = report_path.read_text(encoding="utf-8")
    summary_payload = json.loads((output_dir / "analysis_summary.json").read_text(encoding="utf-8"))

    # top-level passthrough
    assert summary_payload["probe_feedback_behavior"]["correct_outcome_rate"] == 1.0
    assert summary_payload["adversarial_gate"]["current_gate_f1"] == 1.0
    # conclusion metrics
    metrics = summary_payload["conclusion"]["metrics"]
    assert metrics["adversarial_current_gate_f1"] == 1.0
    assert metrics["adversarial_correct_outcome_rate"] == 1.0
    assert metrics["probe_feedback_correct_outcome_rate"] == 1.0
    # report sections
    assert "Gate F1" in report_text
    assert "Probe-feedback behavioral layer" in report_text


def test_analyze_results_includes_open_set_review_metrics(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    output_dir = tmp_path / "analysis"
    results_dir.mkdir()

    open_set_payload = {
        "summary": {
            "packet_count": 6,
            "completed_packet_count": 6,
            "accepted_packet_count": 4,
            "rejected_packet_count": 2,
            "unique_seed_count": 3,
            "accepted_seed_count": 2,
            "rejected_seed_count": 1,
            "mixed_seed_count": 0,
            "pending_seed_count": 0,
            "seed_acceptance_rate": 0.6666666667,
            "seed_rejection_rate": 0.3333333333,
            "agreement_eligible_seed_count": 3,
            "unanimous_seed_count": 2,
            "unanimous_verdict_rate": 0.6666666667,
            "pairwise_decision_agreement_rate": 0.8333333333,
            "status": "review_complete",
        },
        "results": [],
    }
    (results_dir / "open_set_seed_review_summary.json").write_text(
        json.dumps(open_set_payload, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report_path = analyze_results(str(results_dir), str(output_dir))
    report_text = report_path.read_text(encoding="utf-8")
    summary_payload = json.loads((output_dir / "analysis_summary.json").read_text(encoding="utf-8"))

    assert summary_payload["open_set_review"]["seed_acceptance_rate"] == open_set_payload["summary"]["seed_acceptance_rate"]
    assert summary_payload["conclusion"]["metrics"]["open_set_unanimous_verdict_rate"] == open_set_payload["summary"]["unanimous_verdict_rate"]
    assert "Open-set seed acceptance rate" in report_text
    assert "Open-set unanimous verdict rate" in report_text
    assert "## Open-set review" in report_text
    assert "reviewer consensus" in report_text
