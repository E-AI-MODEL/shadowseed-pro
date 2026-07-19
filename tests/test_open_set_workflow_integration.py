"""Integratietest voor de open-set workflow-keten.

Test dat `summarize_open_set_seed_review` een eerlijk, geldig artifact
produceert op all-pending review-packets zoals de workflow dat doet direct
na `run_open_set_seed_review`, zonder menselijke reviewers.
"""
from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.open_set_seed_review import (
    ARTIFACT_CONTRACT_VERSION,
    EVIDENCE_LAYER,
    REVIEW_CRITERIA,
)
from shadowseed.benchmark.open_set_review_summary import summarize_open_set_seed_review


def _pending_packets(n: int = 6) -> dict:
    packets = []
    domains = ["IT en engineering", "recht en jurisdictie", "geschiedenis en economie"]
    seeds = [
        "AVG-compliance bij verwerking van medische hartslagdata.",
        "Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel.",
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.",
    ]
    for i in range(n):
        packets.append(
            {
                "item_id": f"OPEN_{i:03d}",
                "title": f"Testitem {i}",
                "domain": domains[i % len(domains)],
                "seed_id": f"ss_{i:03d}",
                "seed_text": seeds[i % len(seeds)],
                "reviewer_id": None,
                "review_fields": {criterion: None for criterion in REVIEW_CRITERIA},
                "review_status": "pending",
                "reject_reason": None,
                "reviewer_notes": "",
            }
        )
    return {
        "summary": {
            "evidence_layer": EVIDENCE_LAYER,
            "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
            "packet_count": n,
            "criteria": REVIEW_CRITERIA,
            "status": "review_pending",
        },
        "packets": packets,
    }


class TestPendingSummaryHonesty:
    def test_status_is_review_in_progress_not_complete(self, tmp_path: Path):
        packets_path = tmp_path / "packets.json"
        packets_path.write_text(json.dumps(_pending_packets(6)), encoding="utf-8")

        summarize_open_set_seed_review(
            str(packets_path),
            str(tmp_path / "summary.json"),
            disagreements_output_path=str(tmp_path / "disagreements.json"),
            report_output_path=str(tmp_path / "report.md"),
        )

        summary = json.loads((tmp_path / "summary.json").read_text())["summary"]
        assert summary["status"] == "review_in_progress"

    def test_acceptance_rate_is_zero_when_all_pending(self, tmp_path: Path):
        packets_path = tmp_path / "packets.json"
        packets_path.write_text(json.dumps(_pending_packets(4)), encoding="utf-8")

        summarize_open_set_seed_review(str(packets_path), str(tmp_path / "summary.json"))

        summary = json.loads((tmp_path / "summary.json").read_text())["summary"]
        assert summary["seed_acceptance_rate"] == 0.0
        assert summary["accepted_seed_count"] == 0
        assert summary["completed_packet_count"] == 0

    def test_pending_count_matches_input(self, tmp_path: Path):
        n = 8
        packets_path = tmp_path / "packets.json"
        packets_path.write_text(json.dumps(_pending_packets(n)), encoding="utf-8")

        summarize_open_set_seed_review(str(packets_path), str(tmp_path / "summary.json"))

        summary = json.loads((tmp_path / "summary.json").read_text())["summary"]
        assert summary["packet_count"] == n
        assert summary["pending_packet_count"] == n


class TestEvidenceLayerIdentity:
    def test_evidence_layer_field_present_and_correct(self, tmp_path: Path):
        packets_path = tmp_path / "packets.json"
        packets_path.write_text(json.dumps(_pending_packets(3)), encoding="utf-8")

        summarize_open_set_seed_review(str(packets_path), str(tmp_path / "summary.json"))

        summary = json.loads((tmp_path / "summary.json").read_text())["summary"]
        assert summary["evidence_layer"] == "open_set_seed_quality"

    def test_report_contains_evidence_layer_header(self, tmp_path: Path):
        packets_path = tmp_path / "packets.json"
        packets_path.write_text(json.dumps(_pending_packets(3)), encoding="utf-8")

        summarize_open_set_seed_review(
            str(packets_path),
            str(tmp_path / "summary.json"),
            report_output_path=str(tmp_path / "report.md"),
        )

        report = (tmp_path / "report.md").read_text(encoding="utf-8")
        assert "open_set_seed_quality" in report
        assert "# Open-set Seed Review Report" in report


class TestAllFiveArtifactPaths:
    def test_artifacts_dict_contains_summary_disagreements_report(self, tmp_path: Path):
        packets_path = tmp_path / "packets.json"
        summary_path = tmp_path / "summary.json"
        disagreements_path = tmp_path / "disagreements.json"
        report_path = tmp_path / "report.md"
        packets_path.write_text(json.dumps(_pending_packets(4)), encoding="utf-8")

        summarize_open_set_seed_review(
            str(packets_path),
            str(summary_path),
            disagreements_output_path=str(disagreements_path),
            report_output_path=str(report_path),
        )

        artifacts = json.loads(summary_path.read_text())["summary"]["artifacts"]
        assert "summary" in artifacts
        assert "disagreements" in artifacts
        assert "report" in artifacts

    def test_all_three_summary_outputs_exist_on_disk(self, tmp_path: Path):
        packets_path = tmp_path / "packets.json"
        summary_path = tmp_path / "open_set_seed_review_summary.json"
        disagreements_path = tmp_path / "open_set_disagreements.json"
        report_path = tmp_path / "open_set_review_report.md"
        packets_path.write_text(json.dumps(_pending_packets(5)), encoding="utf-8")

        summarize_open_set_seed_review(
            str(packets_path),
            str(summary_path),
            disagreements_output_path=str(disagreements_path),
            report_output_path=str(report_path),
        )

        assert summary_path.exists()
        assert disagreements_path.exists()
        assert report_path.exists()

    def test_disagreements_empty_when_all_pending(self, tmp_path: Path):
        packets_path = tmp_path / "packets.json"
        packets_path.write_text(json.dumps(_pending_packets(4)), encoding="utf-8")

        summarize_open_set_seed_review(
            str(packets_path),
            str(tmp_path / "summary.json"),
            disagreements_output_path=str(tmp_path / "disagreements.json"),
        )

        disagreements = json.loads((tmp_path / "disagreements.json").read_text())
        assert disagreements["summary"]["disagreement_count"] == 0


class TestEdgeCases:
    def test_empty_packets_does_not_crash(self, tmp_path: Path):
        empty = {"summary": {"packet_count": 0, "criteria": REVIEW_CRITERIA}, "packets": []}
        packets_path = tmp_path / "packets.json"
        packets_path.write_text(json.dumps(empty), encoding="utf-8")

        summarize_open_set_seed_review(str(packets_path), str(tmp_path / "summary.json"))

        summary = json.loads((tmp_path / "summary.json").read_text())["summary"]
        assert summary["packet_count"] == 0
        assert summary["unique_seed_count"] == 0
        assert summary["seed_acceptance_rate"] == 0.0
