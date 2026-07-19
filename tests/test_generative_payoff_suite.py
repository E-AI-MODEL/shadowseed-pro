"""Tests for the generative-payoff suite (W5), fixture backend, no network."""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.benchmark.generative_payoff_suite import (
    build_generative_ssl_prompt,
    run_generative_payoff_suite,
)


def test_ssl_prompt_weaves_frames_without_jargon():
    p = build_generative_ssl_prompt("Why X?", ["Power as an explanatory frame."])
    assert "Power as an explanatory frame." in p
    assert "Why X?" in p


def test_generative_suite_runs_on_fixture(tmp_path: Path):
    out = tmp_path / "gen.json"
    run_generative_payoff_suite(
        "src/shadowseed/data/generative_payoff_suite.json",
        str(out),
        backend="fixture",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    s = payload["summary"]
    assert s["artifact"] == "generative_payoff_suite"
    assert s["item_count"] == len(payload["results"]) == 8
    # The fixture generative detector emits "[FIXTURE] ... as an explanatory frame"
    # frames, so every item should carry detected frames + a blind pair
    assert all(r["detected_frames"] for r in payload["results"])
    assert len(payload["blind_review_items"]) == 8
    for r in payload["results"]:
        assert all("explanatory frame" in f.lower() for f in r["detected_frames"])
