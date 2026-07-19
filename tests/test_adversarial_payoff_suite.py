"""Tests for the adversarial payoff suite (fixture backend, no network)."""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.adversarial_payoff_suite import (
    _asserts_falsehood,
    run_adversarial_payoff_suite,
)


def test_asserts_falsehood_requires_all_markers():
    assert _asserts_falsehood("levert 's nachts evenveel stroom", ["nachts", "evenveel"]) is True
    assert _asserts_falsehood("levert overdag stroom", ["nachts", "evenveel"]) is False
    assert _asserts_falsehood("anything", []) is False


def test_adversarial_suite_runs_and_shapes(tmp_path: Path):
    out = tmp_path / "adv.json"
    run_adversarial_payoff_suite(
        "src/shadowseed/data/adversarial_payoff_suite.json",
        str(out),
        backend="fixture",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    s = payload["summary"]
    assert s["artifact"] == "adversarial_payoff_suite"
    assert s["scenario_count"] == len(payload["results"]) == 9
    # three flavours present
    assert set(s["seed_type_counts"]) == {"false_fact", "irrelevant", "redundant"}
    # blind pairs + key align
    assert len(payload["blind_review_items"]) == 9
    assert len(payload["blind_answer_key"]) == 9
    for k in payload["blind_answer_key"]:
        assert k["desired_verdict"] == "baseline_or_tie"
    # the FixtureBackend echoes the seed into the ssl answer, so a false_fact
    # scenario's markers will be present -> the flag wiring is exercised.
    ff = [r for r in payload["results"] if r["seed_type"] == "false_fact"]
    assert ff and all("incorporated_falsehood" in r for r in ff)
