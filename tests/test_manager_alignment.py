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
    manager.seeds = {
        "ss_001": ShadowSeed(
            id="ss_001",
            text="AVG-compliance bij medische data.",
            embedding=np.array([1.0, 0.0]),
            trigger_keywords=["AVG"],
            weight=0.8,
            status=SeedStatus.PROMOTED,
        ),
        "ss_002": ShadowSeed(
            id="ss_002",
            text="Encryptie van medische data.",
            embedding=np.array([0.99, 0.01]),
            trigger_keywords=["Encryptie"],
            weight=0.7,
            status=SeedStatus.PROMOTED,
        ),
        "ss_003": ShadowSeed(
            id="ss_003",
            text="Toegangscontrole voor medische data.",
            embedding=np.array([0.98, 0.02]),
            trigger_keywords=["Toegang"],
            weight=0.9,
            status=SeedStatus.PROMOTED,
        ),
    }

    constellations = manager.find_constellations(threshold=0.95, min_members=3)

    assert len(constellations) == 1
    payload = constellations[0].to_dict()
    assert payload["id"] == "const_001"
    assert payload["member_ids"] == ["ss_001", "ss_002", "ss_003"]
    assert payload["label"]
    assert payload["probe_type"] == "socratic"
