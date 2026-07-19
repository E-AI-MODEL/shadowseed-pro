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
