"""Offline regression tests: plumbing only, never a Q1/Q2 efficacy verdict."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from shadowseed_research.benchmark.compression_retention import (
    OUTPUT_SCHEMA, run_fixtures, validate_fixtures,
)


FIXTURES = Path("research/fixtures/compression_retention_v0.json")


def _document():
    return json.loads(FIXTURES.read_text(encoding="utf-8"))


def _controlled_embedding(text: str) -> np.ndarray:
    """Distinct deterministic topic vectors; NOT a useful semantic model."""
    lower = text.lower()
    if any(s in lower for s in ("battery", "calibration", "thermal", "temperature")):
        return np.array([1.0, 0.0, 0.0, 0.0, 0.0])
    if any(s in lower for s in ("autumn", "registration", "fee")):
        return np.array([0.0, 1.0, 0.0, 0.0, 0.0])
    if any(s in lower for s in ("supplier", "shipping", "delivery delays")):
        return np.array([0.0, 0.0, 1.0, 0.0, 0.0])
    if any(s in lower for s in ("cafeteria", "vegetarian", "lunch")):
        return np.array([0.0, 0.0, 0.0, 1.0, 0.0])
    return np.array([0.0, 0.0, 0.0, 0.0, 1.0])


def _result():
    return run_fixtures(
        _document(), embed=_controlled_embedding,
        embedding_description="test-only-topic-vectors", threshold=0.35,
    )


def test_positive_parity_negative_and_exact_candidate_ablation():
    report = _result()
    assert report["schema"] == OUTPUT_SCHEMA
    assert report["status"] == "offline_plumbing_only_not_efficacy"
    assert report["model_calls"] == report["authority_changes"] == 0
    cases = {item["id"]: item for item in report["results"]}
    assert len(cases) == 4

    sensor = cases["SENSOR_ANCHOR"]["arms"]
    assert sensor["shadowseeds"]["hit_authored_target"] is True
    assert sensor["ordinary_notes"]["hit_authored_target"] is False
    assert sensor["candidate_ablation"]["hit_authored_target"] is False
    assert sensor["sham_notes"]["hit_authored_target"] is False

    # Ordinary notes can do exactly as well: this is required to avoid a fake
    # "unique SSL" result when the same hypothesis is retained in notes.
    parity = cases["NOTE_PARITY"]["arms"]
    assert parity["ordinary_notes"]["hit_authored_target"] is True
    assert parity["shadowseeds"]["hit_authored_target"] is True
    assert parity["candidate_ablation"]["hit_authored_target"] is False

    negative = cases["NO_OPPORTUNITY"]["arms"]
    for arm in ("ordinary_notes", "shadowseeds", "sham_notes", "candidate_ablation"):
        assert negative[arm]["retrieval"] == []
        assert negative[arm]["irrelevant_retrieval_on_negative"] is False

    dependency = cases["DEPENDENCY_REFRAME"]["arms"]
    assert dependency["shadowseeds"]["hit_authored_target"] is True
    assert dependency["candidate_ablation"]["hit_authored_target"] is False

    for item in report["results"]:
        assert item["weightless"] is True
        assert item["gate_events"] == 0
        assert set(item["arms"]) == {
            "compressed_only", "ordinary_notes", "shadowseeds",
            "sham_notes", "candidate_ablation",
        }
        assert item["arms"]["compressed_only"]["model_response"] is None


def test_oracle_labels_do_not_drive_retrieval_selection():
    original = _document()
    changed = copy.deepcopy(original)
    changed["cases"][0]["expected_candidate_id"] = "sampling"
    before = run_fixtures(original, embed=_controlled_embedding)["results"][0]["arms"]
    after = run_fixtures(changed, embed=_controlled_embedding)["results"][0]["arms"]
    for arm in ("ordinary_notes", "shadowseeds", "sham_notes"):
        assert [x["id"] for x in before[arm]["retrieval"]] == [
            x["id"] for x in after[arm]["retrieval"]
        ]
    # The ablation is knowingly label-conditioned, and must not be presented
    # as a blind, prospective causal effect estimate.
    assert before["candidate_ablation"]["retrieval"] != after["candidate_ablation"]["retrieval"]


def test_validation_rejects_duplicate_case_bad_gold_and_overbudget_memory():
    document = _document()
    assert len(validate_fixtures(document)) == 4

    dup = copy.deepcopy(document)
    dup["cases"][1]["id"] = dup["cases"][0]["id"]
    with pytest.raises(ValueError, match="duplicate case"):
        validate_fixtures(dup)

    unknown = copy.deepcopy(document)
    unknown["cases"][0]["expected_candidate_id"] = "invented"
    with pytest.raises(ValueError, match="expected candidate"):
        validate_fixtures(unknown)

    over = copy.deepcopy(document)
    over["cases"][0]["ordinary_notes"][0]["text"] = "over " * 30
    with pytest.raises(ValueError, match="over-budget"):
        validate_fixtures(over)

    negative = copy.deepcopy(document)
    negative["cases"][2]["sham_notes"][0]["candidate_ref"] = "customs"
    with pytest.raises(ValueError, match="sham notes"):
        validate_fixtures(negative)


def test_threshold_and_retrieval_budget_are_validated():
    case = _document()["cases"][0]
    from shadowseed_research.benchmark.compression_retention import run_case

    with pytest.raises(ValueError, match="threshold"):
        run_case(case, _controlled_embedding, threshold=float("nan"))
    with pytest.raises(ValueError, match="top_k"):
        run_case(case, _controlled_embedding, top_k=3, max_items=2)


def test_cli_is_offline_and_reports_fixture_identity(tmp_path: Path):
    output = tmp_path / "result.json"
    result = subprocess.run(
        [
            sys.executable, "-m", "shadowseed_research.benchmark.compression_retention",
            "--fixtures", str(FIXTURES), "--output", str(output),
        ],
        check=True, capture_output=True, text=True,
    )
    record = json.loads(output.read_text(encoding="utf-8"))
    assert record["status"] == "offline_plumbing_only_not_efficacy"
    assert record["model_calls"] == 0
    assert len(record["fixture_sha256"]) == 64
    assert "model_calls" in result.stdout

    # This CLI is *not* an implicit approval for API/remote embedding calls.
    refused = subprocess.run(
        [
            sys.executable, "-m", "shadowseed_research.benchmark.compression_retention",
            "--fixtures", str(FIXTURES), "--output", str(output),
            "--embedding-backend", "openai",
        ],
        capture_output=True, text=True,
    )
    assert refused.returncode != 0
    assert "offline harness only" in refused.stderr
