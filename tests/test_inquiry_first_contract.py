"""Inquiry-first regression tests for the real memory intake boundary.

These protect semantic scope and punctuation, not model-generated candidate
quality. A fixture cannot prove that an actual model asks worthwhile questions.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.seed_normalization import normalize_detection_candidates


@pytest.mark.parametrize("candidate", [
    "Hoe hangen oorzaken en gevolgen samen?",
    "Waarom zouden verschillende perspectieven tot een ander oordeel leiden?",
    "In hoeverre verandert deze uitleg bij een ander voorbeeld?",
    "What if another interpretation changes this conclusion?",
])
def test_single_grounded_inquiry_is_atomic_despite_historical_broad_terms(candidate):
    assert SSLManager.is_atomic_seed(candidate)


@pytest.mark.parametrize("candidate", [
    "Oorzaken, gevolgen, contexten en perspectieven ontbreken.",
    "Hoe hangen oorzaken, gevolgen, contexten en perspectieven samen?",
    "Welke oorzaken en gevolgen?",
])
def test_category_stacks_are_not_automatically_accepted_as_one_inquiry(candidate):
    assert not SSLManager.is_atomic_seed(candidate)


def test_model_question_remains_a_question_during_intake_and_export():
    question = "Hoe hangen oorzaken en gevolgen samen?"
    normalized = normalize_detection_candidates(
        [question],
        expand_short_fragments=False,
        split_broad=False,
    )
    assert normalized == [question]
    manager = SSLManager(embedding_fn=lambda _text: np.array([1.0, 0.0, 0.0]))
    result = manager.ingest_detection_candidates(
        normalized,
        expand_short_fragments=False,
        split_broad=False,
    )
    assert len(result["accepted"]) == 1
    seed_id = result["accepted"][0]["seed_id"]
    seed = manager.seeds[seed_id]
    assert seed.text == question
    assert seed.to_dict()["text"] == question
    assert seed.trace > 0
    assert seed.weight == 0.0
    assert seed.evidence_count == 0
    assert seed.status is SeedStatus.NEW
    assert manager.run_validation_gate(seed_id) is not True
    assert seed.weight == 0.0


def test_short_interrogative_is_never_rewritten_to_an_absence():
    question = "Waarom nu?"
    for expand in (True, False):
        assert normalize_detection_candidates(
            [question], expand_short_fragments=expand, split_broad=False,
        ) == [question]


def test_user_interface_keeps_unresolved_questions_visible_without_authorizing_them():
    source = Path("apps/web/components/shadowseed-app.tsx").read_text("utf-8")
    assert 'rank(a) - rank(b)' in source
    assert 'seed.current_gate_authorized ? 1 : 0' in source
    assert "Wat blijft open?" in source
    assert "Nieuwe geheugenpunten hebben geen gezag" in source
    assert "De engine bewaakt de regels" in source


def test_canonical_ui_help_does_not_call_every_unanswered_question_an_error():
    source = Path("src/shadowseed/workbench/feature_help.py").read_text("utf-8")
    assert "een open vraag, twijfel of mogelijke nieuwe richting" in source
    assert "Dwingt geen nieuwe vraag af" in source
    assert "Het onthouden van zo'n mogelijkheid maakt er geen feit" in source



def test_inquiry_comparison_cases_are_reproducible_and_not_claimed_as_results():
    path = Path("benchmarks/inquiry_first/cases.json")
    material = json.loads(path.read_text(encoding="utf-8"))
    assert material["version"] == 1
    assert material["status"] == "test_design_only_no_live_results"
    assert material["baseline"]["detector_prompt_version"] == "0.6"
    assert material["candidate"]["detector_prompt_version"] == "0.7"
    cases = material["cases"]
    assert len(cases) >= 10
    assert len({case["id"] for case in cases}) == len(cases)
    assert {"nl", "en"} <= {case["language"] for case in cases}
    assert {"current_pair", "source_observation"} <= {
        case["mode"] for case in cases
    }
    assert "forced_curiosity" in {case["risk"] for case in cases}
    assert "anthropomorphism" in {case["risk"] for case in cases}
    assert "prompt_injection" in {case["risk"] for case in cases}
