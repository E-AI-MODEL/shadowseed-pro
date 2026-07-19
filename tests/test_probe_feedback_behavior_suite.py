"""Tests for the probe feedback behavioral suite (Layer E)."""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.probe_feedback_behavior_suite import (
    run_probe_feedback_behavior_suite,
)


FIXTURE = "src/shadowseed/data/probe_feedback_behavior_suite.json"


def _run(tmp_path: Path) -> dict:
    output = tmp_path / "pfb.json"
    casebook = tmp_path / "pfb.md"
    run_probe_feedback_behavior_suite(FIXTURE, str(output), casebook_path=str(casebook))
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["_casebook_text"] = casebook.read_text(encoding="utf-8")
    return payload


def test_suite_passes_end_to_end(tmp_path: Path) -> None:
    payload = _run(tmp_path)
    s = payload["summary"]
    assert s["scenario_count"] >= 8
    assert s["correct_outcome_count"] == s["scenario_count"]
    assert s["correct_outcome_rate"] == 1.0
    assert s["passed"] is True


def test_per_category_covers_full_lifecycle(tmp_path: Path) -> None:
    """The suite must exercise every documented lifecycle behavior."""
    payload = _run(tmp_path)
    categories = set(payload["summary"]["per_category"].keys())
    required = {
        "strengthen",
        "weaken",
        "clamp_upper",
        "clamp_lower",
        "demotion",
        "status_block",
        "neutral",
        "promotion_block",
    }
    missing = required - categories
    assert not missing, f"missing lifecycle categories: {missing}"


def test_every_scenario_reports_correct_outcome(tmp_path: Path) -> None:
    payload = _run(tmp_path)
    for scenario in payload["results"]:
        assert scenario["correct_outcome"] is True, (
            f"{scenario['scenario_id']} ({scenario['category']}) failed: "
            f"{scenario['mismatches']}"
        )


def test_demotion_scenario_sets_demoted_flag(tmp_path: Path) -> None:
    payload = _run(tmp_path)
    demotion_scenarios = [r for r in payload["results"] if r["category"] == "demotion"]
    assert demotion_scenarios, "fixture must include at least one demotion scenario"
    for scenario in demotion_scenarios:
        assert scenario["observed"]["demoted"] is True
        assert scenario["observed"]["status"] == "ACTIVE"


def test_status_block_scenarios_skip_feedback(tmp_path: Path) -> None:
    payload = _run(tmp_path)
    blocked = [r for r in payload["results"] if r["category"] == "status_block"]
    assert blocked, "fixture must include status_block scenarios"
    for scenario in blocked:
        assert scenario["observed"]["skip_count"] > 0
        # weight must not change while status is blocked
        assert scenario["observed"]["weight"] == scenario["initial_state"]["weight"]
        assert scenario["observed"]["status"] == scenario["initial_state"]["status"]


def test_clamp_scenarios_respect_bounds(tmp_path: Path) -> None:
    payload = _run(tmp_path)
    for scenario in payload["results"]:
        if scenario["category"] == "clamp_upper":
            assert scenario["observed"]["weight"] == 1.0
        if scenario["category"] == "clamp_lower":
            assert scenario["observed"]["weight"] == 0.0


def test_promotion_block_does_not_change_status(tmp_path: Path) -> None:
    """Probe rewards must not auto-promote a seed even if weight crosses the
    promotion threshold. Promotion is the Validation Gate's job."""
    payload = _run(tmp_path)
    promo = [r for r in payload["results"] if r["category"] == "promotion_block"]
    assert promo
    for scenario in promo:
        assert scenario["observed"]["status"] == "ACTIVE"
        assert scenario["observed"]["weight"] >= 0.5  # crossed threshold via reward
        assert scenario["observed"]["demoted"] is False


def test_casebook_renders_per_category_breakdown(tmp_path: Path) -> None:
    payload = _run(tmp_path)
    text = payload["_casebook_text"]
    assert "Probe Feedback Behavior Casebook" in text
    assert "Per categorie" in text
    assert "strengthen" in text
    assert "demotion" in text
    assert "status_block" in text


def test_suite_fails_when_expected_state_is_wrong(tmp_path: Path) -> None:
    """Regression guard: if the fixture's expected final weight is wrong, the
    suite must report the mismatch and not silently pass."""
    fixture = json.loads(Path(FIXTURE).read_text(encoding="utf-8"))
    # break exactly one scenario
    broken = json.loads(json.dumps(fixture))
    broken["scenarios"][0]["expected"]["weight"] = 0.99
    broken_path = tmp_path / "broken.json"
    broken_path.write_text(json.dumps(broken), encoding="utf-8")
    output = tmp_path / "out.json"
    run_probe_feedback_behavior_suite(str(broken_path), str(output))
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["summary"]["passed"] is False
    assert payload["summary"]["correct_outcome_count"] == len(broken["scenarios"]) - 1
    first = payload["results"][0]
    assert first["correct_outcome"] is False
    assert any("weight" in m for m in first["mismatches"])


def test_cli_dispatcher_wired() -> None:
    from shadowseed.cli_dispatch import COMMAND_HANDLERS

    assert "run-probe-feedback-behavior-suite" in COMMAND_HANDLERS
