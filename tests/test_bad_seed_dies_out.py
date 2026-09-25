"""Product lifecycle regression: recurring signal does not expire."""

from __future__ import annotations

import numpy as np

from shadowseed.manager import SSLManager, SeedStatus


def _embedding(text: str) -> np.ndarray:
    vector = np.array(
        [float((len(text) % 7) + 1), float((sum(map(ord, text)) % 11) + 1)],
        dtype=float,
    )
    return vector / np.linalg.norm(vector)


def test_recurring_relevant_seed_survives_the_same_pressure():
    manager = SSLManager(embedding_fn=_embedding)
    text = "Concentratierisico in marktgewogen indexfondsen."
    seed_id = manager.add_or_update_seed(text)
    manager.seeds[seed_id].unsafe_set_authority(status=SeedStatus.DORMANT)

    for _ in range(20):
        manager.decay_traces(turns_passed=1)
        manager.scan_trtl_triggers(text)
        assert manager.seeds[seed_id].status != SeedStatus.EXPIRED

    assert manager.seeds[seed_id].status != SeedStatus.EXPIRED
