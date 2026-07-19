import json
import subprocess
import sys

from shadowseed.cli import build_parser


def test_cli_prepare(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "shadowseed.cli", "prepare-absencebench", "--output", "test.json"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_local(tmp_path):
    data = {"scenarios": [{"detected": True}, {"detected": False}]}
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(data))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "shadowseed.cli",
            "run-local-absencebench",
            "--input",
            str(input_file),
            "--output",
            "local.json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_absencebench_smoke(tmp_path):
    data = {"scenarios": [{"detected": True}, {"detected": False}]}
    input_file = tmp_path / "input.json"
    input_file.write_text(json.dumps(data))

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "shadowseed.cli",
            "run-absencebench-smoke",
            "--input",
            str(input_file),
            "--output",
            "smoke.json",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_cli_fetch_open_set_hf_batch_parser() -> None:
    args = build_parser().parse_args(
        [
            "fetch-open-set-hf-batch",
            "--source-id",
            "ag_news_test",
            "--limit",
            "8",
        ]
    )
    assert args.command == "fetch-open-set-hf-batch"
    assert args.source_id == "ag_news_test"
    assert args.limit == 8


def test_cli_open_set_defaults() -> None:
    args = build_parser().parse_args(["run-open-set-seed-review"])
    assert args.output == "results/open_review/open_set_seed_output.json"
    assert args.review_packets == "results/open_review/open_set_review_packets.json"
    assert args.reviewer_ids is None

    custom_args = build_parser().parse_args(
        [
            "run-open-set-seed-review",
            "--reviewer-id",
            "alpha",
            "--reviewer-id",
            "beta",
        ]
    )
    assert custom_args.reviewer_ids == ["alpha", "beta"]

    summary_args = build_parser().parse_args(["summarize-open-set-seed-review"])
    assert summary_args.input == "results/open_review/open_set_review_packets.json"
    assert summary_args.output == "results/open_set_seed_review_summary.json"
    assert summary_args.disagreements_output == "results/open_review/open_set_disagreements.json"
    assert summary_args.report_output == "results/open_review/open_set_review_report.md"


def test_cli_absencebench_smoke_default_output_matches_result_writer_root() -> None:
    args = build_parser().parse_args(["run-absencebench-smoke"])
    assert args.output == "absencebench_smoke.json"


def test_cli_open_set_review_summary(tmp_path):
    review_packets = {
        "summary": {"packet_count": 1},
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
            }
        ],
    }
    input_file = tmp_path / "review_packets.json"
    output_file = tmp_path / "review_summary.json"
    disagreements_file = tmp_path / "review_disagreements.json"
    report_file = tmp_path / "review_report.md"
    input_file.write_text(json.dumps(review_packets), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "shadowseed.cli",
            "summarize-open-set-seed-review",
            "--input",
            str(input_file),
            "--output",
            str(output_file),
            "--disagreements-output",
            str(disagreements_file),
            "--report-output",
            str(report_file),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert output_file.exists()
    assert disagreements_file.exists()
    assert report_file.exists()
