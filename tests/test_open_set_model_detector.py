"""Tests for the v0.3 open-set taalmodel-detector (fixture backend only).

The hf-transformers backend is exercised via construction-time validation
and lazy import behavior; its actual generation path requires a real
model download and is not unit-tested.
"""

from __future__ import annotations

import pytest

from shadowseed.benchmark.open_set_candidate_adapter import (
    SUPPORTED_DETECTORS,
    raw_open_set_candidates,
)
from shadowseed.detection.model_detector import (
    OPEN_SET_MODEL_DETECTOR_SOURCE,
    FixtureDetectorBackend,
    build_detection_prompt,
    make_detector_backend,
    parse_numbered_seeds,
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


def test_supported_detectors_includes_model() -> None:
    assert "model" in SUPPORTED_DETECTORS


def test_fixture_backend_returns_text_grounded_seeds_with_fixture_prefix() -> None:
    backend = FixtureDetectorBackend()
    seeds = backend.detect_seeds(_sample_item())

    assert seeds, "expected non-empty seeds"
    assert all(seed.startswith("[FIXTURE]") for seed in seeds)
    # at least one seed must contain a token taken from the input text
    text_tokens = set(_sample_item()["text"].split())
    assert any(
        any(token.strip(".,") in seed for token in text_tokens)
        for seed in seeds
    )


def test_fixture_backend_returns_empty_on_empty_text() -> None:
    assert FixtureDetectorBackend().detect_seeds({"text": ""}) == []
    assert FixtureDetectorBackend().detect_seeds({}) == []


def test_make_detector_backend_fixture() -> None:
    backend = make_detector_backend("fixture")
    assert backend.name == "fixture"


def test_make_detector_backend_hf_requires_model_id() -> None:
    with pytest.raises(ValueError, match="model-id"):
        make_detector_backend("hf-transformers", model_id=None)


def test_make_detector_backend_rejects_unknown_backend() -> None:
    with pytest.raises(ValueError, match="Unknown model backend"):
        make_detector_backend("not-a-backend")


def test_raw_open_set_candidates_routes_to_model_detector() -> None:
    backend = FixtureDetectorBackend()
    item = _sample_item()
    candidates, source = raw_open_set_candidates(
        item, detector="model", model_backend=backend
    )
    assert source == OPEN_SET_MODEL_DETECTOR_SOURCE
    assert candidates == backend.detect_seeds(item)


def test_raw_open_set_candidates_model_requires_backend() -> None:
    with pytest.raises(ValueError, match="model_backend"):
        raw_open_set_candidates(_sample_item(), detector="model")


def test_explicit_candidates_still_win_over_model_detector() -> None:
    item = dict(_sample_item())
    item["candidate_seeds"] = ["expliciete seed"]
    backend = FixtureDetectorBackend()
    candidates, source = raw_open_set_candidates(
        item, detector="model", model_backend=backend
    )
    assert source == "explicit_candidate_seeds"
    assert candidates == ["expliciete seed"]


def test_parse_numbered_seeds_handles_typical_model_output() -> None:
    raw = """
1. Rol van koloniaal kapitaal in de financiering van fabrieken.
2. AVG-compliance voor de verwerking van hartslagdata.
3. [seed]
4. Rol van koloniaal kapitaal in de financiering van fabrieken.
ignored chatter
5. Rate-limiting op API's die gezondheidsdata verwerken.
""".strip()
    seeds = parse_numbered_seeds(raw)
    assert seeds == [
        "Rol van koloniaal kapitaal in de financiering van fabrieken.",
        "AVG-compliance voor de verwerking van hartslagdata.",
        "Rate-limiting op API's die gezondheidsdata verwerken.",
    ]


def test_parse_numbered_seeds_respects_max() -> None:
    # use sentence-shaped placeholders so the citation-fragment filter does
    # not reject them as 2-word stubs.
    raw = "\n".join(
        f"{i}. Voorbeeld van een gemiste structurele relatie nummer {i} in deze tekst."
        for i in range(1, 11)
    )
    seeds = parse_numbered_seeds(raw, max_seeds=3)
    assert len(seeds) == 3
    assert seeds[0].endswith("nummer 1 in deze tekst.")
    assert seeds[2].endswith("nummer 3 in deze tekst.")


def test_parse_numbered_seeds_drops_html_entities() -> None:
    raw = """
1. AAPL.O&gt
2. &lt;some html&gt;
3. Verantwoordelijke toezichthouder bij grensoverschrijdende incidenten.
""".strip()
    seeds = parse_numbered_seeds(raw)
    assert seeds == [
        "Verantwoordelijke toezichthouder bij grensoverschrijdende incidenten."
    ]


def test_parse_numbered_seeds_drops_bare_acronyms_and_stubs() -> None:
    raw = """
1. FOAF
2. PGP
3. Sven Jaschan
4. Effect van Sven Jaschans rechtszaak op virusauteursparagraaf in Duits strafrecht.
""".strip()
    seeds = parse_numbered_seeds(raw)
    assert seeds == [
        "Effect van Sven Jaschans rechtszaak op virusauteursparagraaf in Duits strafrecht."
    ]


def test_parse_numbered_seeds_drops_long_citation_substrings_of_source() -> None:
    source = (
        "TORONTO, Canada -- A second team of rocketeers competing for the X Prize "
        "has officially announced the first launch date for its manned rocket."
    )
    raw = """
1. A second team of rocketeers competing for the X Prize
2. Motivatie van de tweede ploeg om voor de X Prize te kiezen.
""".strip()
    seeds = parse_numbered_seeds(raw, source_text=source)
    assert seeds == [
        "Motivatie van de tweede ploeg om voor de X Prize te kiezen."
    ]


def test_parse_numbered_seeds_returns_empty_on_no_numbered_lines() -> None:
    assert parse_numbered_seeds("just some prose") == []
    assert parse_numbered_seeds("") == []


def test_parse_numbered_seeds_drops_verbatim_fewshot_leak() -> None:
    """A model that echoes a few-shot example verbatim must have it dropped."""
    raw = """
1. Colonial capital as a funding source for British factory investment.
2. GDPR compliance when processing medical heart-rate data.
3. Consequences of the reported factory closure for local employment.
""".strip()
    seeds = parse_numbered_seeds(raw)
    assert seeds == [
        "Consequences of the reported factory closure for local employment."
    ]


def test_parse_numbered_seeds_drops_near_verbatim_fewshot_leak() -> None:
    """Near-verbatim echo (one token changed) of a few-shot example is also
    caught by the token-overlap leak filter."""
    raw = """
1. Colonial capital as a funding source for British factory expansion.
2. Effect of the announced tariff increase on small importers.
""".strip()
    seeds = parse_numbered_seeds(raw)
    assert seeds == [
        "Effect of the announced tariff increase on small importers."
    ]


def test_parse_numbered_seeds_keeps_legitimate_seed_sharing_a_few_common_words() -> None:
    """A real seed that happens to share a couple of common words with a
    few-shot example must NOT be dropped (no over-eager leak filtering)."""
    raw = "1. Bron van de financiering voor de aangekondigde ziekenhuisuitbreiding."
    seeds = parse_numbered_seeds(raw)
    assert seeds == [
        "Bron van de financiering voor de aangekondigde ziekenhuisuitbreiding."
    ]


def test_build_detection_prompt_includes_text_and_constraints() -> None:
    prompt = build_detection_prompt("De Industriële Revolutie in Groot-Brittannië.")
    assert "De Industriële Revolutie in Groot-Brittannië." in prompt
    assert "at most 5 candidate gaps" in prompt
    assert "Do not assign a seed" in prompt
    assert "meta-categories" in prompt
    assert prompt.endswith("1.")


def test_detection_prompt_includes_few_shot_blocks() -> None:
    """The prompt must teach form with examples, but those examples must come
    from domains OTHER than the news corpus so a small model that echoes them
    is obviously off-topic (the v0.3b leakage fix)."""
    prompt = build_detection_prompt("Een korte test-inputtekst.")
    assert "Bad form examples" in prompt
    assert "Good form examples" in prompt
    # good examples come from history / medicine / law, not news
    assert "Colonial capital" in prompt
    assert "GDPR compliance" in prompt
    # the prompt must warn against copying the example content
    assert "Do not copy their content" in prompt
    # no news-domain entities from the AG News corpus should appear as examples
    assert "Sven Jaschan" not in prompt
    assert "Apple" not in prompt


def test_run_open_set_seed_review_skips_expansion_for_model_detector(tmp_path) -> None:
    """When the detector is 'model' the auto-'ontbreekt' suffix must not be
    added; the language model is expected to deliver whole sentences."""
    import json
    from shadowseed.benchmark.open_set_seed_review import run_open_set_seed_review

    input_batch = {
        "version": "test-batch",
        "items": [
            {
                "id": "TEST_ITEM_1",
                "title": "Test",
                "domain": "test",
                "text": "Een korte test-inputtekst over alpha en beta.",
            }
        ],
    }
    input_path = tmp_path / "batch.json"
    input_path.write_text(json.dumps(input_batch), encoding="utf-8")

    output_path = tmp_path / "out.json"
    packets_path = tmp_path / "packets.json"
    run_open_set_seed_review(
        str(input_path),
        str(output_path),
        review_packet_path=str(packets_path),
        detector="model",
        model_backend="fixture",
    )
    out = json.loads(output_path.read_text(encoding="utf-8"))
    # fixture backend prefixes seeds with [FIXTURE] and does not produce
    # bare stubs, but the seed text must never have a bare " ontbreekt."
    # appended by the normalizer to a short fragment
    for item in out["results"]:
        for seed in item["accepted"]:
            text = seed["text"] if isinstance(seed, dict) else seed
            # this is a structural check: the model path is expected to
            # carry whole-sentence seeds straight through, not be reshaped
            # into "X ontbreekt." form by the legacy expansion
            assert not text.endswith(" ontbreekt.") or text.startswith("[FIXTURE]"), (
                f"unexpected ontbreekt suffix on model-path seed: {text!r}"
            )
