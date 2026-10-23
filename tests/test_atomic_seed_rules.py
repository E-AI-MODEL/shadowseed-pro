from shadowseed.manager import SSLManager


def test_atomic_seed_passes():
    assert SSLManager.is_atomic_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )


def test_atomic_legal_seed_passes():
    assert SSLManager.is_atomic_seed(
        "Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel."
    )


def test_atomic_technical_seed_passes():
    assert SSLManager.is_atomic_seed(
        "Rate-limiting op API's die gezondheidsdata verwerken."
    )


def test_broad_seed_fails():
    assert not SSLManager.is_atomic_seed(
        "Oorzaken, chronologie, arbeid, kapitaal, koloniale verbanden en milieugevolgen."
    )


def test_multi_domain_seed_fails():
    assert not SSLManager.is_atomic_seed(
        "Security, privacy en schaalbaarheid ontbreken."
    )


def test_analysis_framework_seed_fails():
    assert not SSLManager.is_atomic_seed(
        "Een volledig analysekader met oorzaken, gevolgen, contexten en perspectieven ontbreekt."
    )


def test_atomic_seed_is_not_rejected_only_for_exceeding_legacy_word_limit():
    candidate = (
        "De relatie tussen de eerder beschreven bewaartermijn en de concrete "
        "verwijderprocedure voor gegevens van voormalige gebruikers binnen "
        "dezelfde verwerkingsgrondslag en hetzelfde systeem."
    )
    assert len(candidate.split()) > 18
    assert SSLManager.is_atomic_seed(candidate, max_seed_words=18)


def test_english_of_is_not_a_separator():
    # Real candidates from the fixed22 runs that the Dutch " of " (= "or")
    # separator rejected as not atomic.
    for text in (
        "Whether technical reliability or performance is a significant source of user churn.",
        "How invitation-driven growth is measured through invite conversion and retention of referred users.",
    ):
        assert SSLManager.is_atomic_seed(text)


def test_dutch_of_still_separates_dutch_text():
    assert not SSLManager.is_atomic_seed("Kosten of baten en risico's ontbreken.")
