from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.open_set_review_summary import summarize_open_set_seed_review


def test_open_set_review_summary_aggregates_packets_and_disagreements(tmp_path: Path) -> None:
    packets_path = tmp_path / "review_packets.json"
    summary_path = tmp_path / "review_summary.json"
    disagreements_path = tmp_path / "review_disagreements.json"
    report_path = tmp_path / "review_report.md"

    packets_payload = {
        "summary": {
            "packet_count": 3,
            "criteria": [
                "atomicity",
                "relevance",
                "testability",
                "non_triviality",
                "follow_up_utility",
            ]
        },
        "packets": [
            {
                "item_id": "OPEN_IT_001",
                "title": "Health app ontwerp zonder veiligheidsuitwerking",
                "domain": "IT en engineering",
                "seed_id": "ss_001",
                "seed_text": "AVG-compliance bij verwerking van medische hartslagdata.",
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
                "item_id": "OPEN_IT_001",
                "title": "Health app ontwerp zonder veiligheidsuitwerking",
                "domain": "IT en engineering",
                "seed_id": "ss_001",
                "seed_text": "AVG-compliance bij verwerking van medische hartslagdata.",
                "reviewer_id": "reviewer_b",
                "review_status": "rejected",
                "review_fields": {
                    "atomicity": True,
                    "relevance": False,
                    "testability": True,
                    "non_triviality": True,
                    "follow_up_utility": False,
                },
                "reject_reason": "not_relevant",
                "reviewer_notes": "Voor deze tekst nog te ver afgeleid.",
            },
            {
                "item_id": "OPEN_LAW_001",
                "title": "Consumentenrecht zonder procedurele uitwerking",
                "domain": "recht en jurisdictie",
                "seed_id": "ss_002",
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
                "reviewer_notes": "Heldere procedurele gap.",
            },
        ],
    }
    packets_path.write_text(json.dumps(packets_payload), encoding="utf-8")

    summarize_open_set_seed_review(
        str(packets_path),
        str(summary_path),
        disagreements_output_path=str(disagreements_path),
        report_output_path=str(report_path),
    )

    summary_payload = json.loads(summary_path.read_text(encoding="utf-8"))
    disagreements_payload = json.loads(disagreements_path.read_text(encoding="utf-8"))
    report_text = report_path.read_text(encoding="utf-8")

    assert summary_payload["summary"]["evidence_layer"] == "open_set_seed_quality"
    assert summary_payload["summary"]["packet_count"] == 3
    assert summary_payload["summary"]["completed_packet_count"] == 3
    assert summary_payload["summary"]["accepted_packet_count"] == 2
    assert summary_payload["summary"]["rejected_packet_count"] == 1
    assert summary_payload["summary"]["unique_seed_count"] == 2
    assert summary_payload["summary"]["accepted_seed_count"] == 1
    assert summary_payload["summary"]["mixed_seed_count"] == 1
    assert summary_payload["summary"]["agreement_eligible_seed_count"] == 1
    assert summary_payload["summary"]["unanimous_seed_count"] == 0
    assert summary_payload["summary"]["unanimous_verdict_rate"] == 0.0
    assert summary_payload["summary"]["pairwise_decision_agreement_rate"] == 0.0
    assert summary_payload["summary"]["reject_reason_counts"]["not_relevant"] == 1
    assert summary_payload["summary"]["reviewer_ids"] == ["reviewer_a", "reviewer_b"]
    assert summary_payload["summary"]["artifacts"]["report"] == str(report_path)
    assert summary_payload["results"][0]["aggregate_verdict"] in {"accepted", "mixed", "rejected", "pending"}
    assert summary_payload["results"][0]["pairwise_decision_agreement"] in {None, 0.0, 1.0}
    assert disagreements_payload["summary"]["disagreement_count"] == 1
    assert disagreements_payload["summary"]["unanimous_verdict_rate"] == 0.0
    assert disagreements_payload["summary"]["pairwise_decision_agreement_rate"] == 0.0
    assert disagreements_payload["disagreements"][0]["seed_text"] == "AVG-compliance bij verwerking van medische hartslagdata."
    assert "# Open-set Seed Review Report" in report_text
    assert "Evidence layer: `open_set_seed_quality`" in report_text



def _accepted_fields() -> dict[str, bool]:
    return {
        "atomicity": True,
        "relevance": True,
        "testability": True,
        "non_triviality": True,
        "follow_up_utility": True,
    }


def test_partial_reviewer_completion_does_not_count_seed_as_accepted(tmp_path: Path) -> None:
    input_file = tmp_path / "review_packets_partial.json"
    output_file = tmp_path / "review_summary_partial.json"
    input_file.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "item_id": "OPEN_001",
                        "title": "Open item",
                        "domain": "nieuws",
                        "seed_id": "ss_001",
                        "seed_text": "Bron van de centrale bewering.",
                        "reviewer_id": "reviewer_a",
                        "review_status": "accepted",
                        "review_fields": _accepted_fields(),
                        "reject_reason": None,
                        "reviewer_notes": "Sterke seed.",
                    },
                    {
                        "item_id": "OPEN_001",
                        "title": "Open item",
                        "domain": "nieuws",
                        "seed_id": "ss_001",
                        "seed_text": "Bron van de centrale bewering.",
                        "reviewer_id": "reviewer_b",
                        "review_status": "pending",
                        "review_fields": {
                            "atomicity": None,
                            "relevance": None,
                            "testability": None,
                            "non_triviality": None,
                            "follow_up_utility": None,
                        },
                        "reject_reason": None,
                        "reviewer_notes": "",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    summarize_open_set_seed_review(str(input_file), str(output_file))
    payload = json.loads(output_file.read_text(encoding="utf-8"))

    assert payload["summary"]["accepted_seed_count"] == 0
    assert payload["summary"]["completed_seed_count"] == 0
    assert payload["summary"]["pending_seed_count"] == 1
    assert payload["summary"]["status"] == "review_in_progress"
    assert payload["results"][0]["aggregate_verdict"] == "pending"


def test_invalid_completed_packet_marks_summary_invalid(tmp_path: Path) -> None:
    input_file = tmp_path / "review_packets_invalid.json"
    output_file = tmp_path / "review_summary_invalid.json"
    input_file.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "item_id": "OPEN_002",
                        "title": "Open item",
                        "domain": "nieuws",
                        "seed_id": "ss_002",
                        "seed_text": "Tijdlijn van de beschreven gebeurtenis.",
                        "reviewer_id": "reviewer_a",
                        "review_status": "accepted",
                        "review_fields": {
                            "atomicity": True,
                            "relevance": True,
                            "testability": None,
                            "non_triviality": True,
                            "follow_up_utility": True,
                        },
                        "reject_reason": None,
                        "reviewer_notes": "Mist nog een veld.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    summarize_open_set_seed_review(str(input_file), str(output_file))
    payload = json.loads(output_file.read_text(encoding="utf-8"))

    assert payload["summary"]["invalid_packet_count"] == 1
    assert payload["summary"]["invalid_seed_count"] == 1
    assert payload["summary"]["status"] == "review_invalid"
    assert payload["results"][0]["aggregate_verdict"] == "invalid"
