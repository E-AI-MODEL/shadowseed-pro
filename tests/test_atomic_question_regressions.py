"""Weightless question intake: avoid losing ideas to grammar heuristics.

One visible question is admissible even if it compares many factors or contains
several clauses. That is NOT a verdict that it is useful, singular in meaning,
true, safe to prompt with, or entitled to Gate authority.
"""
import numpy as np
import pytest

from shadowseed.manager import SSLManager


@pytest.mark.parametrize("question", [
    "Blijft het verschil van 1,2 °C bestaan wanneer de thermometers worden omgewisseld?",
    "Blijft ruimte B warmer lijken, of volgt het verschil de thermometer?",
    "How does latency vary across Android, iOS, and web clients?",
    "How does retention vary over one day, one week, and one month?",
    "How does pressure change at 10, 20, and 30 degrees?",
    "Wat weten we over de klas, de docent, de toets en de AI-tool?",
    "Welke rol spelen motivatie, thuissituatie en schooltype?",
    "Hoe hangen oorzaken, gevolgen, contexten en perspectieven samen?",
    "Welke oorzaken en gevolgen?",
    "Is the API reachable and does the retry succeed?",
    "Is the API reachable and has Alice received a response?",
    "Is the API reachable and is it returning data?",
    "Was the deployment complete and were they notified?",
    "Is de API bereikbaar en heeft zij een antwoord ontvangen?",
    "How long was the intervention, and which students did not attend?",
    "Does the result remain stable when the sample is large and is the same size across groups?",
    "How does the system change at night, considering security, privacy, and scalability?",
])
def test_one_visible_question_is_admitted_without_semantic_guesswork(question):
    assert SSLManager.is_atomic_seed(question)


def test_long_question_and_descriptive_measurement_levels_are_admitted():
    long_level = "Android clients with telemetry flags and lengthy deployment configuration notes "
    question = (
        "How does latency vary across "
        + (long_level * 4)
        + ", iOS, Linux, and web clients?"
    )
    assert len(question.split()) > 60
    assert SSLManager.is_atomic_seed(question)


@pytest.mark.parametrize("candidate", [
    "Was it random? Was it large enough?",
    "Is de toets valide? Is hij betrouwbaar?",
    "What is the cause? Who is responsible?",
    "Was it random? And was it large enough?",
    "The first part is unrelated. Is the API reachable?",
    "First question? Second question?",
])
def test_multiple_visible_questions_or_sentences_are_rejected(candidate):
    assert not SSLManager.is_atomic_seed(candidate)


def test_single_question_is_not_rejected_just_for_semicolon_or_conjunction():
    assert SSLManager.is_atomic_seed(
        "Welke verklaring weegt het zwaarst; motivatie, voorkennis of feedback?"
    )
    assert SSLManager.is_atomic_seed(
        "Is het een meetfout, en wat betekent dat voor de conclusie?"
    )


@pytest.mark.parametrize("candidate", [
    "Hoe hangen oorzaken, gevolgen, contexten en perspectieven samen?",
    "Is the API reachable and does the retry succeed?",
    "What do we know about security, privacy, and reliability?",
])
def test_structurally_admitted_question_is_born_weightless(candidate):
    manager = SSLManager(embedding_fn=lambda _text: np.array([1.0, 0.0]))
    result = manager.ingest_detection_candidates(
        [candidate], expand_short_fragments=False, split_broad=False,
    )
    assert len(result["accepted"]) == 1
    seed_id = result["accepted"][0]["seed_id"]
    seed = manager.seeds[seed_id]
    assert seed.weight == 0.0
    assert seed.evidence_count == 0
    assert manager.gate_events == []


def test_nonquestion_legacy_declarative_rejection_is_unchanged():
    assert not SSLManager.is_atomic_seed(
        "Oorzaken, chronologie, arbeid, kapitaal, koloniale verbanden en milieugevolgen."
    )
    assert SSLManager.is_atomic_seed(
        "Rate-limiting op API's die gezondheidsdata verwerken."
    )
