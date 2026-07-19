import json
from pathlib import Path

import pytest

from shadowseed.benchmark.blind.detector import detect_blind_candidates
from shadowseed.benchmark.blind.loader import BlindBenchmarkInputError, load_public_suite
from shadowseed.benchmark.blind.runner import run_blind_benchmark


def test_public_suite_rejects_private_labels(tmp_path: Path):
    public = tmp_path / "public.json"
    public.write_text(
        json.dumps(
            {
                "version": "bad",
                "scenarios": [
                    {
                        "id": "S1",
                        "domain": "recht",
                        "input": "Publieke tekst.",
                        "expected_gaps": ["Dit hoort niet in publieke data."],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(BlindBenchmarkInputError):
        load_public_suite(public)


def test_detector_uses_public_text_only():
    candidates = detect_blind_candidates(
        "recht",
        "Een Nederlandse klant koopt online iets bij een buitenlandse aanbieder.",
    )

    assert "Rechtsbevoegdheid bij partijen uit verschillende landen." in candidates


def test_blind_benchmark_runs_with_private_labels(tmp_path: Path):
    public = tmp_path / "public.json"
    labels = tmp_path / "labels.json"
    output = tmp_path / "blind_result.json"

    public.write_text(
        json.dumps(
            {
                "version": "test-public",
                "scenarios": [
                    {
                        "id": "S1",
                        "domain": "recht",
                        "input": "Een Nederlandse klant koopt online iets bij een buitenlandse aanbieder. Het antwoord noemt retourrecht maar niet welk recht geldt.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    labels.write_text(
        json.dumps(
            {
                "version": "test-labels",
                "labels": [
                    {
                        "id": "S1",
                        "expected_gaps": [
                            "Rechtsbevoegdheid bij partijen uit verschillende landen.",
                            "Toepasselijk recht bij grensoverschrijdende afspraken.",
                        ],
                        "must_not_add": [
                            "Onbewezen directe fraude door de buitenlandse aanbieder."
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result_path = run_blind_benchmark(
        str(public),
        str(labels),
        str(output),
        turns=3,
    )

    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["summary"]["scenario_count"] == 1
    assert result["summary"]["mean_ssl_gap_coverage"] > 0
    assert result["summary"]["total_unsupported_additions"] == 0


def test_blind_detector_does_not_reference_private_label_fields():
    source = Path("src/shadowseed/benchmark/blind/detector.py").read_text(encoding="utf-8")

    assert "expected_gaps" not in source
    assert "must_not_add" not in source
    assert "ground_truth_seeds" not in source
    assert "benchmarks/private" not in source
