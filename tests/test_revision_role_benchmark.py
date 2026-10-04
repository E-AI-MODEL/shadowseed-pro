from __future__ import annotations

import importlib.util
from pathlib import Path

_SCRIPT = Path("scripts/run_revision_role_benchmark.py").resolve()
_spec = importlib.util.spec_from_file_location("run_revision_role_benchmark", _SCRIPT)
assert _spec and _spec.loader
bench = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bench)


def _case() -> dict:
    return {
        "case_id": "revision",
        "language": "en",
        "expected_addition_groups": [
            {
                "id": "drift",
                "aliases": ["monitor data drift after deployment"],
            }
        ],
        "baseline_preservation_groups": [
            {
                "id": "test-set",
                "aliases": ["evaluate on a separate test set"],
            }
        ],
    }


def test_token_recall_rewards_expected_terms_without_requiring_verbatim_order() -> None:
    answer = "After deployment, monitor carefully for data drift."
    assert bench.token_recall(answer, "monitor data drift after deployment") >= 0.75


def test_revision_role_contract_passes_complete_clean_final() -> None:
    report = bench.score_case(
        _case(),
        {
            "response": (
                "Evaluate on a separate test set. After deployment, monitor data drift."
            ),
            "done_reason": "stop",
            "total_duration": 4_000_000_000,
            "eval_count": 42,
        },
    )

    assert report["final_response_available"] is True
    assert report["addition_coverage"] == 1.0
    assert report["baseline_preservation"] == 1.0
    assert report["visible_contract_violations"] == []
    assert report["role_contract_pass"] is True


def test_length_truncation_never_counts_as_final_role_success() -> None:
    report = bench.score_case(
        _case(),
        {
            "response": (
                "Evaluate on a separate test set. After deployment, monitor data drift."
            ),
            "done_reason": "length",
            "total_duration": 30_000_000_000,
        },
    )

    assert report["final_response_available"] is False
    assert report["role_contract_pass"] is False


def test_visible_thinking_markup_breaks_revision_contract() -> None:
    report = bench.score_case(
        _case(),
        {
            "response": (
                "<think>reasoning</think> Evaluate on a separate test set. "
                "After deployment, monitor data drift."
            ),
            "done_reason": "stop",
        },
    )

    assert "thinking_markup" in report["visible_contract_violations"]
    assert report["role_contract_pass"] is False


def test_current_product_timeout_is_reported_separately_from_quality() -> None:
    report = bench.score_case(
        _case(),
        {
            "response": (
                "Evaluate on a separate test set. After deployment, monitor data drift."
            ),
            "done_reason": "stop",
            "total_duration": 121_000_000_000,
        },
    )

    assert report["role_contract_pass"] is True
    assert report["within_current_product_timeout"] is False


def test_summary_keeps_quality_and_runtime_dimensions_separate() -> None:
    good = bench.score_case(
        _case(),
        {
            "response": (
                "Evaluate on a separate test set. After deployment, monitor data drift."
            ),
            "done_reason": "stop",
            "total_duration": 10_000_000_000,
        },
    )
    bad = bench.score_case(
        _case(),
        {
            "response": "<think>still reasoning",
            "done_reason": "length",
            "total_duration": 130_000_000_000,
        },
    )

    summary = bench.summarize([good, bad])

    assert summary["final_response_rate"] == 0.5
    assert summary["role_contract_pass_rate"] == 0.5
    assert summary["within_current_product_timeout_rate"] == 0.5
    assert "score" not in summary
    assert "winner" not in summary



def test_language_summary_and_pair_comparison_keep_languages_separate() -> None:
    nl_case = _case()
    nl_case["case_id"] = "same-nl"
    nl_case["pair_id"] = "same"
    nl_case["language"] = "nl"
    en_case = _case()
    en_case["case_id"] = "same-en"
    en_case["pair_id"] = "same"
    en_case["language"] = "en"

    nl = bench.score_case(
        nl_case,
        {
            "response": "Evaluate on a separate test set.",
            "done_reason": "length",
            "total_duration": 150_000_000_000,
            "eval_count": 700,
        },
    )
    en = bench.score_case(
        en_case,
        {
            "response": (
                "Evaluate on a separate test set. After deployment, monitor data drift."
            ),
            "done_reason": "stop",
            "total_duration": 90_000_000_000,
            "eval_count": 400,
        },
    )

    language = bench.summarize_by_language([nl, en])
    pairs = bench.summarize_pairs([nl, en])

    assert language["nl"]["final_response_rate"] == 0.0
    assert language["en"]["final_response_rate"] == 1.0
    assert pairs[0]["pair_id"] == "same"
    assert pairs[0]["nl"]["done_reason"] == "length"
    assert pairs[0]["en"]["done_reason"] == "stop"
    assert pairs[0]["en_minus_nl"]["total_duration_seconds"] == -60.0
