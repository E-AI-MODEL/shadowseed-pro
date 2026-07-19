from shadowseed.manager import SSLManager


def test_atomic_seed_passes():
    assert SSLManager.is_atomic_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )


def test_broad_seed_fails():
    assert not SSLManager.is_atomic_seed(
        "Oorzaken, chronologie, arbeid, kapitaal, koloniale verbanden en milieugevolgen."
    )
