from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


REVIEW_PACKETS = {
    "summary": {"packet_count": 2},
    "packets": [
        {
            "item_id": "OPEN_LAW_001",
            "title": "Consumentenrecht zonder procedurele uitwerking",
            "domain": "recht en jurisdictie",
            "seed_id": "ss_001",
            "seed_text": "Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
            "reviewer_id": "reviewer_a",
            "review_status": "accepted",
            "review_fields": {
                "atomicity": True,
                "relevance": True,
                "testability": True,
                "non_triviality": True,
                "follow_up_utility": True,
            },
            "reject_reason": None,
            "reviewer_notes": "Sterke seed.",
        },
        {
            "item_id": "OPEN_LAW_001",
            "title": "Consumentenrecht zonder procedurele uitwerking",
            "domain": "recht en jurisdictie",
            "seed_id": "ss_001",
            "seed_text": "Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
            "reviewer_id": "reviewer_b",
            "review_status": "accepted",
            "review_fields": {
                "atomicity": True,
                "relevance": True,
                "testability": True,
                "non_triviality": True,
                "follow_up_utility": True,
            },
            "reject_reason": None,
            "reviewer_notes": "Ook akkoord.",
        },
    ],
}


def test_run_absencebench_smoke_default_route_writes_under_result_writer_root(tmp_path: Path) -> None:
    input_file = tmp_path / "absence_input.json"
    input_file.write_text(
        json.dumps(
            {
                "source": "integration-test",
                "scenarios": [
                    {
                        "id": "ABS_001",
                        "original_context": "De overeenkomst noemt privacy, encryptie en logging.",
                        "modified_context": "De overeenkomst noemt privacy en logging.",
                        "omitted_context": ["encryptie"],
                    },
                    {
                        "id": "ABS_002",
                        "original_context": "Het antwoord noemt planning en budget.",
                        "modified_context": "Het antwoord noemt planning en budget.",
                        "omitted_context": [],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "shadowseed.cli",
            "run-absencebench-smoke",
            "--input",
            str(input_file),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    output_file = tmp_path / "benchmarks" / "results" / "absencebench_smoke.json"
    wrong_nested_file = tmp_path / "benchmarks" / "results" / "results" / "absencebench_smoke.json"

    assert result.returncode == 0
    assert output_file.exists()
    assert not wrong_nested_file.exists()

    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["benchmark_name"] == "AbsenceBench"
    assert payload["evaluation"]["shadowseed"]["f1"] >= 0.0


def test_open_set_summary_default_route_flows_into_analyzer(tmp_path: Path) -> None:
    review_packets = tmp_path / "review_packets.json"
    review_packets.write_text(json.dumps(REVIEW_PACKETS), encoding="utf-8")

    summarize = subprocess.run(
        [
            sys.executable,
            "-m",
            "shadowseed.cli",
            "summarize-open-set-seed-review",
            "--input",
            str(review_packets),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    summary_file = tmp_path / "results" / "open_set_seed_review_summary.json"
    legacy_summary_file = tmp_path / "results" / "open_review" / "open_set_review_summary.json"
    disagreements_file = tmp_path / "results" / "open_review" / "open_set_disagreements.json"
    report_file = tmp_path / "results" / "open_review" / "open_set_review_report.md"

    assert summarize.returncode == 0
    assert summary_file.exists()
    assert not legacy_summary_file.exists()
    assert disagreements_file.exists()
    assert report_file.exists()

    analyze = subprocess.run(
        [sys.executable, "-m", "shadowseed.cli", "analyze-results"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    analysis_summary = tmp_path / "results" / "analysis" / "analysis_summary.json"
    analysis_report = tmp_path / "results" / "analysis" / "analysis_report.md"

    assert analyze.returncode == 0
    assert analysis_summary.exists()
    assert analysis_report.exists()

    summary_payload = json.loads(analysis_summary.read_text(encoding="utf-8"))
    assert summary_payload["open_set_review"]["seed_acceptance_rate"] == 1.0
    assert "## Open-set review" in analysis_report.read_text(encoding="utf-8")

    conclusion = summary_payload["conclusion"]
    assert {"verdict", "headline", "body", "supporting_observations", "claim_boundary"} <= set(
        conclusion
    )
    assert isinstance(conclusion["supporting_observations"], list)
    assert conclusion["claim_boundary"]


def test_open_set_legacy_summary_name_is_analyzer_fallback_only(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    legacy_dir = results_dir / "open_review"
    legacy_dir.mkdir(parents=True)
    legacy_summary = legacy_dir / "open_set_review_summary.json"
    legacy_summary.write_text(
        json.dumps(
            {
                "summary": {
                    "packet_count": 1,
                    "unique_seed_count": 1,
                    "seed_acceptance_rate": 1.0,
                    "seed_rejection_rate": 0.0,
                    "agreement_eligible_seed_count": 1,
                    "unanimous_verdict_rate": 1.0,
                    "pairwise_decision_agreement_rate": 1.0,
                }
            }
        ),
        encoding="utf-8",
    )

    analyze = subprocess.run(
        [sys.executable, "-m", "shadowseed.cli", "analyze-results"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    analysis_summary = results_dir / "analysis" / "analysis_summary.json"

    assert analyze.returncode == 0
    assert analysis_summary.exists()

    payload = json.loads(analysis_summary.read_text(encoding="utf-8"))
    assert payload["open_set_review"]["seed_acceptance_rate"] == 1.0
