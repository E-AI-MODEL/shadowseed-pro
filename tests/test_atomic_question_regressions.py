"""Regressions from an independently created adversarial sample.

No model-quality claim; the synthetic text and expected structural dispositions
only test atomic intake. Human labels for semantic atomicity remain separate.
"""
import pytest

from shadowseed.manager import SSLManager


@pytest.mark.parametrize("question", [
    "Blijft het gemeten verschil van 1,2 °C bestaan wanneer de thermometers tussen Ruimte A en Ruimte B worden omgewisseld?",
    "Blijft ruimte B warmer lijken wanneer de thermometers tussen de ruimtes worden verwisseld, of volgt het gemeten verschil de thermometer?",
    "Hoe hangen oorzaken en gevolgen samen?",
    "Wanneer leerlingen dezelfde opdracht zonder hulpmiddel maken, behouden ze dan het niveau dat ze met AI haalden?",
    "Does the 3.5% error rate on Android drop when we pin the app to version 2.1, or does it stay the same?",
    "Hoe is de 80% correctheid verdeeld over de 24 leerlingen: liggen hun individuele percentages dicht bij elkaar of verhult het klaspercentage verschillen tussen leerlingen?",
])
def test_single_bounded_question_survives(question):
    assert SSLManager.is_atomic_seed(question)


@pytest.mark.parametrize("candidate", [
    "Was it random? Was it large enough?",
    "Is de toets valide? Is hij betrouwbaar?",
    "Hoe lang duurde de interventie, en welke leerlingen deden er niet aan mee?",
    "What was the sample size, and how were participants recruited?",
    "Welke rol spelen motivatie, thuissituatie en schooltype?",
    "How do safety, reliability, fairness, transparency, robustness relate?",
    "Wat zijn betrouwbaarheid, veiligheid, bereikbaarheid, onderhoudbaarheid?",
    "Hoe hangen oorzaken, gevolgen, contexten, perspectieven samen?",
    "Welke relatie is er tussen oorzaak en gevolg, en hoe toets je die?",
])
def test_question_stacks_are_blocked(candidate):
    assert not SSLManager.is_atomic_seed(candidate)


def test_existing_declarative_filter_contract_is_kept():
    assert SSLManager.is_atomic_seed(
        "Rate-limiting op API's die gezondheidsdata verwerken."
    )
    assert not SSLManager.is_atomic_seed(
        "Oorzaken, chronologie, arbeid, kapitaal, koloniale verbanden en milieugevolgen."
    )


@pytest.mark.parametrize("candidate", [
    "Ontbrekende context: kolonialisme, privacy, schaalbaarheid",
    "Consider latency, throughput and cost.",
    "What about security, privacy, and scalability?",
    "Welke oorzaken en gevolgen?",
    (
        "The host may provide up to 4 prior conversation turns. "
        "Each user or assistant message is clipped to at most 800 characters. "
        "Use this bounded context only to interpret references and avoid repeating "
        "what was settled earlier. Conversation context is not evidence, validation, "
        "authority, or permission to influence. Rules: Write every candidate in the "
        "same language as the current question."
    ),
])
def test_declarative_checklists_and_prompt_copy_are_not_atomic(candidate):
    assert not SSLManager.is_atomic_seed(candidate)


def test_clean_question_can_use_a_comma_and_two_alternatives():
    assert SSLManager.is_atomic_seed(
        "Is het verschil een meetfout, of ontstaat het alleen bij hoge belasting?"
    )
    assert SSLManager.is_atomic_seed(
        "How does existing knowledge relate to performance on a new task?"
    )
