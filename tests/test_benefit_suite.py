import json
from pathlib import Path

from shadowseed.benchmark.ssl45_benefit_suite import run_ssl45_benefit_suite


def test_benefit_suite_improves_gap_coverage(tmp_path: Path):
    output = tmp_path / "benefit_results.json"

    run_ssl45_benefit_suite(
        "src/shadowseed/data/ssl45_benefit_suite.json",
        str(output),
        turns=3,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    summary = payload["summary"]

    assert summary["baseline_mean_gap_coverage"] == 0.0
    assert summary["ssl_mean_gap_coverage"] == 1.0
    assert summary["coverage_delta"] == 1.0
    assert summary["coverage_delta_raw"] == summary["coverage_delta"]
    assert summary["mean_answer_length_delta_words"] > 0
    assert summary["coverage_delta_per_100_added_words"] > 0
    assert summary["penalized_coverage_delta"] == summary["coverage_delta"]
    assert summary["unsupported_ssl_additions"] == 0

    first = payload["results"][0]
    assert first["ssl_word_count"] >= first["baseline_word_count"]
    assert first["answer_length_delta_words"] == first["ssl_word_count"] - first["baseline_word_count"]
    assert first["coverage_delta_raw"] == first["coverage_delta"]
    assert "coverage_delta_per_100_added_words" in first
    assert "penalized_coverage_delta" in first
