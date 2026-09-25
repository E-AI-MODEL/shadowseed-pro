from shadowseed.cli import build_parser


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
