"""Tests for the generative detector variant."""
from __future__ import annotations

from shadowseed.detection.model_detector import (
    CURRENT_PAIR_PROMPT_META,
    PROMPT_VARIANTS,
    SOURCE_OBSERVATION_PROMPT_META,
    build_detection_prompt,
    make_detector_backend,
    parse_numbered_seeds_with_diagnostics,
)


def test_variants_registered():
    assert PROMPT_VARIANTS == ("absence", "generative", "current_pair")


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


def test_current_pair_prompt_uses_bounded_context_without_word_limit():
    p = build_detection_prompt(
        "Dit is het draftantwoord.",
        variant="current_pair",
        question="Wat mist er inhoudelijk?",
        max_seed_words=30,
        conversation_context="PRIOR TURN 1\nUSER: Eerder besproken.",
    )
    assert "CURRENT QUESTION:" in p
    assert "Wat mist er inhoudelijk?" in p
    assert "DRAFT ANSWER:" in p
    assert "Dit is het draftantwoord." in p
    assert "PRIOR TURN 1" in p
    assert "30 words" not in p
    assert "word-count limit" in p
    assert "epistemically undetermined" in p
    assert "not evidence" in p
    assert "return exactly: NONE" in p
    assert "Colonial capital" not in p


def test_current_pair_variant_falls_back_to_source_observation_context():
    p = build_detection_prompt(
        "Brontekst over onderwijs.",
        variant="current_pair",
        source_context="source:file-1",
        max_seed_words=24,
    )
    assert "SOURCE OBSERVATION:" in p
    assert "SOURCE CONTEXT:" in p
    assert "source:file-1" in p
    assert "24 words" not in p
    assert "word-count limit" in p


def test_explicit_none_is_a_valid_zero_candidate_result():
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics("NONE")
    assert seeds == []
    assert diagnostics["explicit_none"] is True
    assert diagnostics["accepted_candidates"] == 0


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



def test_prompt_metadata_declares_detector_input_and_output_contracts() -> None:
    assert CURRENT_PAIR_PROMPT_META["input_contract"] == [
        "bounded_clean_conversation_context",
        "current_question",
        "draft_answer",
        "max_seeds",
    ]
    assert SOURCE_OBSERVATION_PROMPT_META["input_contract"] == [
        "source_observation",
        "source_context",
        "max_seeds",
    ]
    assert CURRENT_PAIR_PROMPT_META["output_contract"] == (
        "zero_or_more_numbered_atomic_gap_candidates_or_NONE"
    )
    assert SOURCE_OBSERVATION_PROMPT_META["output_contract"] == (
        "zero_or_more_numbered_atomic_gap_candidates_or_NONE"
    )
    assert CURRENT_PAIR_PROMPT_META["prompt_version"] == "0.6"
    assert SOURCE_OBSERVATION_PROMPT_META["prompt_version"] == "0.6"


def test_fixture_detector_exposes_raw_and_parser_audit() -> None:
    detector = make_detector_backend("fixture", prompt_variant="current_pair")
    seeds = detector.detect_seeds(
        {
            "question": "What matters?",
            "text": "Alpha introduces a perspective.",
            "max_seed_words": 18,
        }
    )

    assert seeds
    assert detector.last_raw_output is not None
    assert "1." in detector.last_raw_output
    assert detector.last_parse_diagnostics["accepted_candidates"] == len(seeds)
    assert detector.last_prompt_metadata["prompt_id"] == "detector_current_pair"


def test_fixture_detector_records_explicit_none_for_empty_input() -> None:
    detector = make_detector_backend("fixture", prompt_variant="current_pair")
    seeds = detector.detect_seeds(
        {
            "question": "What matters?",
            "text": "",
            "max_seed_words": 18,
        }
    )

    assert seeds == []
    assert detector.last_raw_output == "NONE"
    assert detector.last_parse_diagnostics["explicit_none"] is True



def test_parser_preserves_two_word_gap_labels_but_drops_single_token_stubs() -> None:
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        "1. Authentication mechanism\n"
        "2. kanaal resetlink\n"
        "3. availability zones\n"
        "4. Context"
    )

    assert seeds == [
        "Authentication mechanism",
        "kanaal resetlink",
        "availability zones",
    ]
    assert diagnostics["accepted_candidates"] == 3
    assert diagnostics["dropped_citation_or_stub"] == 1


def test_parser_drops_short_copied_proper_name_but_not_title_case_gap_label() -> None:
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        "1. Alice Smith\n"
        "2. Data Drift",
        source_text="Alice Smith deployed the classifier yesterday.",
    )

    assert seeds == ["Data Drift"]
    assert diagnostics["dropped_citation_or_stub"] == 1
