from __future__ import annotations

import numpy as np

from shadowseed.manager import SSLManager, SeedStatus, ShadowSeed


def _embedding(text: str) -> np.ndarray:
    values = np.array(
        [
            float((len(text) % 7) + 1),
            float((sum(ord(char) for char in text) % 11) + 1),
        ],
        dtype=float,
    )
    norm = np.linalg.norm(values)
    return values / norm


def _manager() -> SSLManager:
    return SSLManager(embedding_fn=_embedding)


def test_contradiction_score_starts_at_zero() -> None:
    manager = _manager()
    seed_id = manager.add_or_update_seed("AVG-compliance bij verwerking van medische data.")
    assert manager.get_seed(seed_id).contradiction_score == 0.0


def test_contradiction_score_accumulates_across_rounds() -> None:
    manager = _manager()
    seed_id = manager.add_or_update_seed("Encryptie van medische data tijdens transport.")

    manager.run_validation_gate_detailed(seed_id, contradiction=True)
    manager.run_validation_gate_detailed(seed_id, contradiction=True)

    assert manager.get_seed(seed_id).contradiction_score == 0.5


def test_contradiction_score_caps_at_one() -> None:
    manager = _manager()
    seed_id = manager.add_or_update_seed("Rechtsbevoegdheid bij grensoverschrijdend consumentencontract.")

    for _ in range(6):
        manager.run_validation_gate_detailed(seed_id, contradiction=True)

    assert manager.get_seed(seed_id).contradiction_score == 1.0


def test_contradiction_score_persists_in_to_dict() -> None:
    manager = _manager()
    seed_id = manager.add_or_update_seed("Bron van de centrale bewering.")
    manager.run_validation_gate_detailed(seed_id, contradiction=True)

    payload = manager.get_seed(seed_id).to_dict()

    assert payload["contradiction_score"] == 0.25


def test_constellation_exports_alignment_fields() -> None:
    manager = _manager()
    specs = [
        ("ss_001", "AVG-compliance bij medische data.", np.array([1.0, 0.0]), ["AVG"], 0.8),
        ("ss_002", "Encryptie van medische data.", np.array([0.99, 0.01]), ["Encryptie"], 0.7),
        ("ss_003", "Toegangscontrole voor medische data.", np.array([0.98, 0.02]), ["Toegang"], 0.9),
    ]
    for seed_id, text, embedding, keywords, weight in specs:
        seed = ShadowSeed(id=seed_id, text=text, embedding=embedding, trigger_keywords=keywords)
        seed.unsafe_set_authority(weight=weight, status=SeedStatus.PROMOTED)
        manager.unsafe_install_seed(seed)

    constellations = manager.find_constellations(threshold=0.95, min_members=3)

    assert len(constellations) == 1
    payload = constellations[0].to_dict()
    assert payload["id"] == "const_001"
    assert payload["member_ids"] == ["ss_001", "ss_002", "ss_003"]
    assert payload["label"]
    assert payload["probe_type"] == "socratic"
