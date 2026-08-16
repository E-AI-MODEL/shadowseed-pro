import math

import numpy as np

from shadowseed.manager import SSLManager, SeedStatus


def fake_embedding(text: str) -> np.ndarray:
    if "Colonial capital" in text:
        return np.array([1.0, 0.0, 0.0])
    return np.array([0.0, 1.0, 0.0])


def test_seed_starts_with_trace_and_zero_weight():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Colonial capital as a funding source for British factory investment."
    )

    seed = manager.get_seed(seed_id)
    assert seed.trace == 2.0
    assert seed.weight == 0.0
    assert seed.status == SeedStatus.NEW


def test_trace_decay_formula():
    manager = SSLManager(embedding_fn=fake_embedding, half_life_turns=3)
    seed_id = manager.add_or_update_seed(
        "Colonial capital as a funding source for British factory investment."
    )

    manager.decay_traces(turns_passed=1)

    expected = 2.0 * math.exp(-math.log(2.0) / 3)
    assert math.isclose(manager.get_seed(seed_id).trace, expected)

    manager.decay_traces(turns_passed=2)
    assert math.isclose(manager.get_seed(seed_id).trace, 1.0)


def test_default_decay_horizon_is_preserved_after_half_life_semantics_fix():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Colonial capital as a funding source for British factory investment."
    )

    dormant_turn = None
    expired_turn = None
    for turn in range(1, 25):
        manager.decay_traces(turns_passed=1)
        status = manager.get_seed(seed_id).status
        if status is SeedStatus.DORMANT and dormant_turn is None:
            dormant_turn = turn
        if status is SeedStatus.EXPIRED:
            expired_turn = turn
            break

    assert dormant_turn == 12
    assert expired_turn == 16


def test_weight_does_not_increase_without_external_evidence():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Colonial capital as a funding source for British factory investment."
    )
    manager.seeds[seed_id].occurrence_count = 3

    result = manager.run_validation_gate(seed_id)

    assert result is None
    assert manager.get_seed(seed_id).weight == 0.0
    assert manager.get_seed(seed_id).status == SeedStatus.NEW


def test_weight_only_increases_after_all_gate_checks_pass():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Colonial capital as a funding source for British factory investment."
    )
    manager.seeds[seed_id].occurrence_count = 3
    manager.seeds[seed_id].unsafe_set_authority(evidence_count=2)

    result = manager.run_validation_gate(seed_id)

    assert result is True
    assert manager.get_seed(seed_id).weight == 0.2
    assert manager.get_seed(seed_id).status == SeedStatus.ACTIVE


def test_promotion_threshold_requires_repeated_gate_passes():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Colonial capital as a funding source for British factory investment."
    )
    manager.seeds[seed_id].occurrence_count = 3
    manager.seeds[seed_id].unsafe_set_authority(evidence_count=2)

    for count in (3, 4, 5):
        manager.seeds[seed_id].occurrence_count = count
        manager.run_validation_gate(seed_id)

    assert manager.get_seed(seed_id).weight == 0.6000000000000001
    assert manager.get_seed(seed_id).status == SeedStatus.PROMOTED


def test_contradiction_reduces_weight_and_resets_seed():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Colonial capital as a funding source for British factory investment."
    )
    manager.seeds[seed_id].unsafe_set_authority(weight=0.6)
    manager.seeds[seed_id].occurrence_count = 3

    result = manager.run_validation_gate(seed_id, contradiction=True)

    assert result is False
    assert manager.get_seed(seed_id).weight == 0.3
    assert manager.get_seed(seed_id).occurrence_count == 1
    assert manager.get_seed(seed_id).status == SeedStatus.NEW
