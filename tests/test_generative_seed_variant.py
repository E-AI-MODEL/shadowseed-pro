"""Tests for the generative detector variant."""
from __future__ import annotations

import pytest

from shadowseed.detection.model_detector import (
    CURRENT_PAIR_PROMPT_META,
    PROMPT_VARIANTS,
    SOURCE_OBSERVATION_PROMPT_META,
    build_detection_prompt,
    make_detector_backend,
    parse_numbered_seeds_with_diagnostics,
)


@pytest.mark.parametrize("wrapper", ["**", "__", "`", "*", "_", "**`", "`**"])
def test_parser_removes_whole_candidate_markdown(wrapper):
    text = "The relation between LLM memory and human memory"
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        f"1. {wrapper}{text}{wrapper[::-1]}\n2. {text}"
    )
    assert seeds == [text]
    assert diagnostics["markdown_wrappers_removed"] >= 1
    assert diagnostics["dropped_duplicate"] == 1


@pytest.mark.parametrize("text", [
    "**LLM memory** compared with **human memory**",
    "`context_window` compared with `working_memory`",
    "*LLM memory* compared with *human memory*",
    "_left_boundary and right_boundary_ within a graph",
    "**Unclosed formatting around a gap",
])
def test_parser_preserves_internal_or_unclosed_markdown(text):
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(f"1. {text}")
    assert seeds == [text]
    assert diagnostics["markdown_wrappers_removed"] == 0


def test_markdown_cleanup_cannot_bypass_placeholder_and_copied_text_filters():
    text = "The relation between LLM memory and human memory"
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        f"1. **[seed]**\n2. `{text}`",
        source_text=text,
    )
    assert seeds == []
    assert diagnostics["dropped_blank_or_placeholder"] == 1
    assert diagnostics["dropped_citation_or_stub"] == 1


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





def test_default_chat_detector_preserves_curiosity_without_inventing_an_error() -> None:
    prompt = build_detection_prompt(
        "De conclusie is verantwoord en het antwoord is volledig.",
        variant="current_pair",
        question="Hoe helpen leerlingen elkaar om iets te begrijpen?",
    )
    assert "This is NOT a completeness checklist" in prompt
    assert "A clear, correct answer may still invite" in prompt
    for term in ("uncertainty", "doubt", "curiosity", "alternative interpretation"):
        assert term in prompt
    assert "Do not claim that something is missing merely to create a candidate" in prompt
    assert "The model is not said to *feel* curiosity or doubt" in prompt
    assert "Never invent facts" in prompt
    assert "return exactly: NONE" in prompt


def test_source_observation_detector_allows_an_open_question() -> None:
    prompt = build_detection_prompt(
        "Twee groepen leerlingen geven verschillende redenen.",
        variant="current_pair",
        source_context="classroom-observation-1",
    )
    assert "A source does not have to be incomplete" in prompt
    assert "uncertainty, doubt, an alternative explanation" in prompt
    assert "A concise phrase or a naturally phrased open question is acceptable" in prompt
    assert "do not produce generic questions".lower() in prompt.lower()


def test_inquiry_question_and_tentative_frame_survive_parser_without_becoming_facts() -> None:
    question = "Could the same feedback mean something different in another classroom?"
    frame = "Feedback timing as a possible factor in learner independence"
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        f"1. {question}\n2. {frame}",
        source_text="Pupils compared two examples of feedback.",
    )
    assert seeds == [question, frame]
    assert diagnostics["accepted_candidates"] == 2


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
        "zero_or_more_numbered_bounded_inquiry_candidates_or_NONE"
    )
    assert SOURCE_OBSERVATION_PROMPT_META["output_contract"] == (
        "zero_or_more_numbered_bounded_inquiry_candidates_or_NONE"
    )
    assert CURRENT_PAIR_PROMPT_META["prompt_version"] == "0.7"
    assert SOURCE_OBSERVATION_PROMPT_META["prompt_version"] == "0.7"


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


def test_parser_drops_bare_two_word_proper_names() -> None:
    seeds, diagnostics = parse_numbered_seeds_with_diagnostics(
        "1. Alice Smith\n"
        "2. Data Drift"
    )

    assert seeds == []
    assert diagnostics["dropped_citation_or_stub"] == 2
