"""Tests for the text-grounded v0.2 open-set candidate adapter."""

from __future__ import annotations

import pytest

from shadowseed.benchmark.open_set_candidate_adapter import (
    SUPPORTED_DETECTORS,
    raw_open_set_candidates,
)
from shadowseed.benchmark.open_set_candidate_adapter_v2 import (
    OPEN_SET_ADAPTER_V2_SOURCE,
    detect_open_set_candidates_v2,
)


def _sample_item() -> dict[str, str]:
    return {
        "id": "AG_NEWS_TEST_0",
        "title": "AG News Business #0",
        "domain": "nieuws - Business",
        "text": (
            "Fears for T N pension after talks Unions representing workers at "
            "Turner Newall say they are disappointed after talks with stricken "
            "parent firm Federal Mogul."
        ),
    }


def test_v2_returns_seeds_grounded_in_input_text() -> None:
    item = _sample_item()
    seeds = detect_open_set_candidates_v2(item)

    assert seeds, "expected non-empty seed list"
    assert len(seeds) <= 5
    # every seed must contain a token taken from the actual input text
    text_tokens = set(item["text"].split())
    for seed in seeds:
        assert any(
            token.strip(".,") in seed for token in text_tokens
        ), f"seed {seed!r} contains no input-text token"


def test_v2_drops_generated_ag_news_title_tokens() -> None:
    seeds = detect_open_set_candidates_v2(_sample_item())
    for seed in seeds:
        assert "AG News" not in seed
        assert "Business" not in seed
        assert "Sci/Tech" not in seed


def test_v2_two_items_produce_different_seed_sets() -> None:
    item_a = _sample_item()
    item_b = {
        "id": "AG_NEWS_TEST_1",
        "title": "AG News Sci/Tech #1",
        "domain": "nieuws - Sci/Tech",
        "text": (
            "The Race is On: Second Private Team Sets Launch Date for Human "
            "Spaceflight (SPACE.com) — TORONTO, Canada — A second team of "
            "rocketeers competing for the Ansari X Prize."
        ),
    }
    seeds_a = set(detect_open_set_candidates_v2(item_a))
    seeds_b = set(detect_open_set_candidates_v2(item_b))

    # The v0.1 failure mode was that two items shared 4 of 5 seed strings.
    # v0.2 must avoid that: overlap should be small.
    assert seeds_a, "item A produced no seeds"
    assert seeds_b, "item B produced no seeds"
    assert len(seeds_a & seeds_b) <= 1, (
        f"v0.2 should not reuse seed strings across items; overlap was "
        f"{seeds_a & seeds_b}"
    )


def test_v2_returns_empty_on_empty_input() -> None:
    assert detect_open_set_candidates_v2({"title": "", "text": ""}) == []
    assert detect_open_set_candidates_v2({}) == []


def test_v2_rejects_only_generic_ag_news_title() -> None:
    # title is the generated label; text is empty: nothing to ground in
    seeds = detect_open_set_candidates_v2({"title": "AG News Business #0", "text": ""})
    assert seeds == []


def test_raw_open_set_candidates_routes_to_v2_when_requested() -> None:
    item = _sample_item()
    candidates, source = raw_open_set_candidates(item, detector="adapter_v2")
    assert source == OPEN_SET_ADAPTER_V2_SOURCE
    assert candidates == detect_open_set_candidates_v2(item)


def test_raw_open_set_candidates_default_remains_v1() -> None:
    item = _sample_item()
    _, source = raw_open_set_candidates(item)
    assert source == "open_set_candidate_adapter"


def test_explicit_candidates_win_over_detector_choice() -> None:
    item = dict(_sample_item())
    item["candidate_seeds"] = ["expliciete seed 1", "expliciete seed 2"]
    for detector in SUPPORTED_DETECTORS:
        candidates, source = raw_open_set_candidates(item, detector=detector)
        assert source == "explicit_candidate_seeds"
        assert candidates == ["expliciete seed 1", "expliciete seed 2"]


def test_raw_open_set_candidates_rejects_unknown_detector() -> None:
    with pytest.raises(ValueError):
        raw_open_set_candidates(_sample_item(), detector="adapter_v9")
