from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SCRIPT = Path("scripts/run_gap_resilience_benchmark.py").resolve()
_spec = importlib.util.spec_from_file_location("run_gap_resilience_benchmark", _SCRIPT)
assert _spec and _spec.loader
bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench)


class SequenceDetector:
    def __init__(self, outputs: list[list[str]]) -> None:
        self.outputs = list(outputs)
        self.items: list[dict] = []

    def detect_seeds(self, item, max_seeds=5):
        self.items.append(dict(item))
        if not self.outputs:
            return []
        return self.outputs.pop(0)[:max_seeds]


def _case(**overrides):
    base = {
        "case_id": "case-1",
        "question": "What remains missing?",
        "draft_answer": "The API returns JSON.",
        "conversation_context": "NONE",
        "negative_control": False,
        "expected_gap_groups": [],
        "resolved_gap_groups": [],
    }
    base.update(overrides)
    return base


def test_jaccard_is_inspectable_and_order_independent() -> None:
    left = "API client authentication method"
    right = "authentication method for API clients"

    assert bench.jaccard(left, right) == bench.jaccard(right, left)
    assert bench.jaccard(left, right) > 0.5
    assert bench.jaccard(left, "backup deletion timing") == 0.0


def test_candidate_set_repeatability_is_order_independent() -> None:
    left = ["API authentication method", "backup deletion timing"]
    right = ["backup deletion timing", "API client authentication method"]

    assert bench.candidate_set_similarity(left, right) >= 0.8
    assert bench.candidate_set_similarity([], []) == 1.0
    assert bench.candidate_set_similarity(left, []) == 0.0


def test_expected_gap_recall_and_resolved_reopen_are_separate() -> None:
    case = _case(
        expected_gap_groups=[
            {
                "id": "backup-deletion",
                "aliases": ["backup deletion timing", "when backups are deleted"],
            }
        ],
        resolved_gap_groups=[
            {
                "id": "retention-period",
                "aliases": ["data retention period", "retention duration"],
            }
        ],
    )
    report = bench.score_case(
        case,
        [
            ["Backup deletion timing", "Data retention period"],
            ["When backups are deleted"],
        ],
        threshold=0.35,
    )

    assert report["expected_gap_recall"] == 1.0
    assert report["resolved_gap_reopens"] == 1
    assert report["resolved_gap_opportunities"] == 2
    assert report["resolved_gap_reopen_rate"] == 0.5


def test_negative_control_rewards_only_explicit_model_none() -> None:
    case = _case(negative_control=True)
    report = bench.score_case(
        case,
        [[], ["Invented missing detail"], []],
        run_audits=[
            {
                "raw_output": "NONE",
                "thinking_output": "",
                "parse_diagnostics": {"explicit_none": True},
            },
            {
                "raw_output": "1. Invented missing detail",
                "thinking_output": "",
                "parse_diagnostics": {"explicit_none": False},
            },
            {
                "raw_output": "",
                "thinking_output": "reasoning without a final answer",
                "parse_diagnostics": {"explicit_none": False},
            },
        ],
    )

    assert report["abstention_successes"] == 1
    assert report["abstention_opportunities"] == 3
    assert report["abstention_rate"] == 0.3333
    assert report["thinking_only_runs"] == 1


def test_summary_keeps_dimensions_separate_without_overall_score() -> None:
    reports = [
        bench.score_case(
            _case(
                case_id="positive",
                expected_gap_groups=[
                    {"id": "auth", "aliases": ["API authentication method"]}
                ],
            ),
            [["API authentication method"]],
        ),
        bench.score_case(
            _case(case_id="negative", negative_control=True),
            [[]],
            run_audits=[
                {
                    "raw_output": "NONE",
                    "thinking_output": "",
                    "parse_diagnostics": {"explicit_none": True},
                }
            ],
        ),
    ]

    summary = bench.summarize(reports)

    assert summary["expected_gap_recall"] == 1.0
    assert summary["negative_control_abstention_rate"] == 1.0
    assert "score" not in summary
    assert "winner" not in summary


def test_runner_passes_bounded_context_without_legacy_word_limit() -> None:
    detector = SequenceDetector([["API authentication method"]])
    case = _case(
        conversation_context=(
            "PRIOR TURN 1\nUSER: Was authentication defined?\n"
            "ASSISTANT: Not yet."
        ),
        expected_gap_groups=[
            {"id": "auth", "aliases": ["API authentication method"]}
        ],
    )

    result = bench.run_cases(
        [case],
        detector,
        repeats=1,
        max_seeds=5,
        threshold=0.35,
    )

    assert result["summary"]["expected_gap_recall"] == 1.0
    assert detector.items == [
        {
            "question": case["question"],
            "text": case["draft_answer"],
            "conversation_context": case["conversation_context"],
        }
    ]
    assert "max_seed_words" not in detector.items[0]


def test_committed_case_set_is_valid_and_contains_all_core_lanes() -> None:
    payload = json.loads(
        Path("benchmarks/gap_resilience/cases.json").read_text(encoding="utf-8")
    )
    assert payload["schema_version"] == 1
    cases = payload["cases"]
    assert cases

    assert any(case["expected_gap_groups"] for case in cases)
    assert any(case["negative_control"] for case in cases)
    assert any(case["resolved_gap_groups"] for case in cases)
    assert any(case.get("language") == "nl" for case in cases)

    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids))



def test_fixture_cli_executes_as_benchmark_smoke(tmp_path) -> None:
    output = tmp_path / "gap-resilience.json"

    assert (
        bench.main(
            [
                "--backend",
                "fixture",
                "--repeats",
                "2",
                "--output",
                str(output),
            ]
        )
        == 0
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["artifact"] == "shadowseed-gap-resilience-v1"
    assert report["run_type"] == "benchmark_smoke"
    assert report["backend"] == "fixture"
    assert report["repeats"] == 2
    assert "score" not in report["summary"]



def test_detector_audit_distinguishes_explicit_none_from_parser_empty() -> None:
    case = _case(case_id="audit")

    explicit_none = bench.score_case(
        case,
        [[]],
        run_audits=[
            {
                "raw_output": "NONE",
                "parse_diagnostics": {
                    "explicit_none": True,
                    "nonblank_lines": 1,
                    "accepted_candidates": 0,
                },
                "prompt_metadata": {"prompt_id": "detector_current_pair"},
            }
        ],
    )
    parser_empty = bench.score_case(
        case,
        [[]],
        run_audits=[
            {
                "raw_output": "Missing authentication method",
                "parse_diagnostics": {
                    "explicit_none": False,
                    "nonblank_lines": 1,
                    "unnumbered_nonblank_lines": 1,
                    "accepted_candidates": 0,
                },
            }
        ],
    )

    assert explicit_none["explicit_none_runs"] == 1
    assert explicit_none["abstention_rate"] is None
    assert explicit_none["parser_empty_non_none_runs"] == 0
    assert explicit_none["run_details"][0]["detector_output_class"] == "explicit_none"
    assert (
        explicit_none["run_details"][0]["detector_raw_output"]
        == "NONE"
    )
    assert parser_empty["explicit_none_runs"] == 0
    assert parser_empty["parser_empty_non_none_runs"] == 1
    assert (
        parser_empty["run_details"][0]["detector_output_class"]
        == "parser_rejected_nonempty"
    )



def test_thinking_only_empty_response_is_not_abstention() -> None:
    case = _case(case_id="thinking", negative_control=True)
    report = bench.score_case(
        case,
        [[]],
        run_audits=[
            {
                "raw_output": "",
                "thinking_output": "I am still reasoning about the prompt.",
                "parse_diagnostics": {"explicit_none": False},
            }
        ],
    )

    assert report["abstention_rate"] == 0.0
    assert report["empty_response_runs"] == 1
    assert report["thinking_only_runs"] == 1
    assert report["run_details"][0]["detector_output_class"] == "thinking_only"


def test_rescore_existing_report_uses_strict_model_abstention() -> None:
    case = _case(case_id="negative", negative_control=True)
    existing = {
        "artifact": "shadowseed-gap-resilience-v1",
        "summary": {"negative_control_abstention_rate": 1.0},
        "cases": [
            {
                "case_id": "negative",
                "run_details": [
                    {
                        "candidates": [],
                        "detector_raw_output": "1. channel for reset link",
                        "detector_thinking_output": "",
                        "detector_parse_diagnostics": {
                            "explicit_none": False,
                            "accepted_candidates": 0,
                        },
                    }
                ],
            }
        ],
    }

    rescored = bench.rescore_existing_report(
        existing,
        [case],
        threshold=0.35,
    )

    assert rescored["summary"]["negative_control_abstention_rate"] == 0.0
    assert rescored["summary"]["negative_control_parser_filtered_rate"] == 1.0
    assert rescored["scoring_policy"] == "strict_model_abstention_v2"
