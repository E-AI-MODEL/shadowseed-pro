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
