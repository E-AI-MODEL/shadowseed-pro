"""Tests for the generative detector variant."""
from __future__ import annotations

from shadowseed.detection.model_detector import (
    PROMPT_VARIANTS,
    build_detection_prompt,
    make_detector_backend,
)


def test_variants_registered():
    assert PROMPT_VARIANTS == ("absence", "generative")


def test_absence_prompt_asks_what_is_missing():
    p = build_detection_prompt("Een korte testtekst.", variant="absence")
    assert "MISSING" in p.upper()
    assert "UNTaken direction".upper() not in p.upper()


def test_generative_prompt_asks_what_could_have_been():
    p = build_detection_prompt("Een korte testtekst.", variant="generative")
    assert "COULD have appeared" in p
    assert "untaken direction" in p
    # doctrine guardrail survives: no invented facts, only a direction
    assert "Do NOT invent concrete facts" in p
    assert "DIRECTION" in p
    # generative few-shot frames, not omission examples
    assert "explanatory frame" in p


def test_unknown_variant_rejected():
    import pytest
    with pytest.raises(ValueError):
        build_detection_prompt("x", variant="bogus")
    with pytest.raises(ValueError):
        make_detector_backend("fixture", prompt_variant="bogus")


def test_fixture_backend_reflects_variant():
    item = {"text": "Manchester en Watt dreven de Industriële Revolutie."}
    absence = make_detector_backend("fixture", prompt_variant="absence").detect_seeds(item)
    generative = make_detector_backend("fixture", prompt_variant="generative").detect_seeds(item)
    assert absence and generative
    assert any("Missing explanation" in s for s in absence)
    assert any("explanatory frame" in s for s in generative)
