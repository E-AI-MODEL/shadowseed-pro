"""Tests for authority-state encapsulation (issue #11).

These prove that authority fields cannot be assigned directly through the normal
API, that the explicit unsafe hook is the only non-Gate way to set them, and
that the Gate transition path stamps a monotonic authority version.
"""

from __future__ import annotations

import numpy as np
import pytest

from shadowseed.manager import AUTHORITY_FIELDS, SSLManager, SeedStatus, ShadowSeed


def fake_embedding(text: str) -> np.ndarray:
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vector = rng.standard_normal(16)
    return vector / np.linalg.norm(vector)


def _seed() -> ShadowSeed:
    return ShadowSeed(id="ss_001", text="a seed", embedding=fake_embedding("a seed"))


@pytest.mark.parametrize("field_name", sorted(AUTHORITY_FIELDS))
def test_direct_authority_assignment_is_blocked(field_name):
    seed = _seed()
    value = SeedStatus.PROMOTED if field_name == "status" else 0.9
    with pytest.raises(AttributeError, match="authority state"):
        setattr(seed, field_name, value)


def test_non_authority_fields_remain_writable():
    seed = _seed()
    seed.trace = 1.23
    seed.occurrence_count = 5
    seed.turns_dormant = 2
    assert seed.trace == 1.23
    assert seed.occurrence_count == 5


def test_unsafe_set_authority_is_the_explicit_escape_hatch():
    seed = _seed()
    seed.unsafe_set_authority(weight=0.6, status=SeedStatus.PROMOTED, evidence_count=3)
    assert seed.weight == 0.6
    assert seed.status is SeedStatus.PROMOTED
    assert seed.evidence_count == 3


def test_authority_version_bumps_on_weight_change_only():
    seed = _seed()
    start = seed.authority_version
    # Weight change bumps.
    seed.unsafe_set_authority(weight=0.2)
    assert seed.authority_version == start + 1
    # A pure lifecycle status move (no weight, no promotion crossing) does not.
    seed.unsafe_set_authority(status=SeedStatus.DORMANT)
    assert seed.authority_version == start + 1
    # Crossing into PROMOTED bumps.
    seed.unsafe_set_authority(status=SeedStatus.PROMOTED)
    assert seed.authority_version == start + 2


def test_gate_promotion_uses_the_transition_path_and_bumps_version():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a genuinely atomic seed")
    seed = manager.seeds[seed_id]
    seed.unsafe_set_authority(evidence_count=2)
    seed.occurrence_count = 3
    version_before = seed.authority_version
    manager.run_validation_gate(seed_id)
    assert seed.weight > 0.0
    assert seed.authority_version > version_before


def test_to_dict_excludes_seal_and_exposes_version():
    seed = _seed()
    seed.unsafe_set_authority(weight=0.4)
    data = seed.to_dict()
    assert "_authority_sealed" not in data
    assert data["authority_version"] == seed.authority_version
    assert data["weight"] == 0.4


def test_authority_fields_are_readable_everywhere():
    seed = _seed()
    # Reading never raises; only writing is guarded.
    assert seed.weight == 0.0
    assert seed.status is SeedStatus.NEW
    assert seed.evidence_count == 0
    assert seed.contradiction_score == 0.0


def test_constructor_cannot_set_authority():
    # init=False closes the construction bypass: authority kwargs are rejected.
    for kwargs in ({"weight": 1.0}, {"status": SeedStatus.PROMOTED}, {"evidence_count": 9}):
        with pytest.raises(TypeError):
            ShadowSeed(id="x", text="t", embedding=fake_embedding("t"), **kwargs)


def test_authority_version_is_not_directly_writable():
    seed = _seed()
    with pytest.raises(AttributeError):
        seed.authority_version = 999


def test_seed_registry_is_read_only():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a seed")
    # The view cannot be replaced or mutated in place.
    with pytest.raises((TypeError, AttributeError)):
        manager.seeds = {}
    with pytest.raises(TypeError):
        manager.seeds["x"] = manager.seeds[seed_id]
    # But it reads normally.
    assert seed_id in manager.seeds
    assert manager.seeds[seed_id].text == "a seed"


def test_unchanged_authority_rewrite_does_not_bump_version():
    seed = _seed()
    seed.unsafe_set_authority(weight=0.4)
    version = seed.authority_version
    seed.unsafe_set_authority(weight=0.4)  # same value
    assert seed.authority_version == version


def test_evidence_count_change_bumps_version():
    seed = _seed()
    version = seed.authority_version
    seed.unsafe_set_authority(evidence_count=2)
    assert seed.authority_version == version + 1


def test_from_dict_restores_authority_snapshot_and_version_losslessly():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a seed to serialize")
    seed = manager.seeds[seed_id]
    seed.unsafe_set_authority(weight=0.6, status=SeedStatus.PROMOTED, evidence_count=2)
    version = seed.authority_version

    data = seed.to_dict()
    restored = ShadowSeed.from_dict(data)

    assert restored.weight == 0.6
    assert restored.status is SeedStatus.PROMOTED
    assert restored.evidence_count == 2
    # The historical version is restored exactly, not recomputed/incremented.
    assert restored.authority_version == version
    assert restored.to_dict()["authority_version"] == version
    # And it is still guarded after restoration.
    with pytest.raises(AttributeError):
        restored.weight = 0.1


def test_restore_seed_installs_into_registry():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("persisted seed")
    manager.seeds[seed_id].unsafe_set_authority(weight=0.7, status=SeedStatus.PROMOTED)
    data = manager.seeds[seed_id].to_dict()

    fresh = SSLManager(embedding_fn=fake_embedding)
    restored = fresh.restore_seed(data)
    assert restored.id in fresh.seeds
    assert fresh.seeds[restored.id].weight == 0.7
    assert fresh.seeds[restored.id].authority_version == manager.seeds[seed_id].authority_version


def test_vector_only_expiry_resets_weight():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a seed to expire")
    manager.seeds[seed_id].unsafe_set_authority(weight=0.8, status=SeedStatus.PROMOTED)

    class _Store:
        def housekeeping(self, max_age_days):
            return [seed_id]

    manager.vector_constellation = _Store()
    manager.expire_vector_only_open_seeds(max_age_days=1)
    assert manager.seeds[seed_id].status is SeedStatus.EXPIRED
    assert manager.seeds[seed_id].weight == 0.0
