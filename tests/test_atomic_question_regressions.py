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


# Post-merge review on PR #206: one relation can compare several values.
@pytest.mark.parametrize("question", [
    "How does latency vary across Android, iOS, and web clients?",
    "How does pressure change at 10, 20, and 30 degrees?",
    "Hoe verschilt de latency tussen Android, iOS en web clients?",
    "Hoe veranderen resultaten per leerjaar in havo 4, havo 5 en vwo 4?",
    "Hoe hangt de druk bij 10, 20 en 30 graden samen met de temperatuur?",
])
def test_measured_levels_do_not_become_category_lists(question):
    assert SSLManager.is_atomic_seed(question)


@pytest.mark.parametrize("question", [
    "Is the API reachable and does the retry succeed?",
    "Is de API bereikbaar en lukt het opnieuw proberen?",
    "Is de API bereikbaar, en werkt de volgende poging?",
    "Can we reproduce the failure, and is the log format stable?",
    "Does this result hold, and was the sample selected randomly?",
])
def test_conjoined_independent_yes_no_questions_are_not_one_seed(question):
    assert not SSLManager.is_atomic_seed(question)


def test_long_single_question_does_not_fail_on_arbitrary_word_ceiling():
    question = (
        "Does the reduction in failed logins after the restart persist "
        + (
            "with the same network load and the same client versions "
            "and the same logging interval "
        ) * 7
        + "in an independently repeated measurement?"
    )
    assert len(question.split()) > 60
    assert SSLManager.is_atomic_seed(question)


@pytest.mark.parametrize("candidate", [
    "What about security, privacy, and scalability?",
    "Welke rol spelen motivatie, thuissituatie en schooltype?",
    "Hoe hangen oorzaken, gevolgen, contexten, perspectieven samen?",
    "Wat weten we over de klas, de docent, de toets en de AI-tool?",
])
def test_broad_checklists_remain_blocked_after_measured_list_exemption(candidate):
    assert not SSLManager.is_atomic_seed(candidate)


def test_binary_alternative_still_counts_as_one_question():
    assert SSLManager.is_atomic_seed(
        "Is it a measurement error, or is the underlying process changing?"
    )
    assert SSLManager.is_atomic_seed(
        "Is het een meetfout of verandert het echte proces?"
    )


@pytest.mark.parametrize("candidate", [
    "How does the system change at night, considering security, privacy, and scalability?",
    "How does the system change at night, looking at security, privacy, and scalability?",
    "Hoe verandert het systeem 's nachts, gezien beveiliging, privacy en betrouwbaarheid?",
])
def test_unrelated_late_checklist_cannot_inherit_measurement_exemption(candidate):
    assert not SSLManager.is_atomic_seed(candidate)


@pytest.mark.parametrize("question", [
    "How does latency vary across Android, iOS, Linux, and web clients?",
    "How does latency vary across Android, iOS, Linux and web clients?",
])
def test_actual_four_level_measurement_still_passes(question):
    assert SSLManager.is_atomic_seed(question)


@pytest.mark.parametrize("candidate", [
    "Does the result remain stable when the sample is large and is the same size across groups?",
    "How does latency increase across Android, iOS, and web clients?",
    "How does latency decrease across Android, iOS, and web clients?",
])
def test_shared_predicates_and_unlisted_measurement_verbs_are_admitted(candidate):
    assert SSLManager.is_atomic_seed(candidate)


def test_descriptive_measurement_level_does_not_have_hidden_character_limit():
    long_level = (
        "Android clients with extended telemetry settings and a very "
        "descriptive build configuration used for the repeated load test"
    )
    assert len(long_level) > 100
    question = f"How does latency vary across {long_level}, iOS, and web clients?"
    assert SSLManager.is_atomic_seed(question)


@pytest.mark.parametrize("candidate", [
    "Is the API reachable and has the retry succeeded?",
    "Has the sample been collected and had the control group been selected?",
    "Is de API bereikbaar en heeft de tweede poging gewerkt?",
])
def test_conjoined_perfect_tense_questions_are_split_at_intake(candidate):
    assert not SSLManager.is_atomic_seed(candidate)
