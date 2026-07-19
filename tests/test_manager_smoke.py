import numpy as np
import pytest

from shadowseed.core_config import SSLCoreConfig
from shadowseed.manager import SSLManager, SeedStatus


def fake_embedding(text: str) -> np.ndarray:
    if "Koloniaal kapitaal" in text:
        return np.array([1.0, 0.0, 0.0])
    if "Winsten uit trans-Atlantische slavenhandel" in text:
        return np.array([0.96, 0.28, 0.0])
    if "Koloniale katoen" in text:
        return np.array([0.96, -0.28, 0.0])
    return np.array([0.0, 1.0, 0.0])


def test_add_update_and_validation_gate_smoke():
    manager = SSLManager(embedding_fn=fake_embedding, promotion_threshold=0.4)

    seed_id = manager.add_or_update_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.",
        trigger_keywords=["kapitaal", "fabrieksinvesteringen"],
    )
    assert seed_id == "ss_001"
    assert manager.seeds[seed_id].weight == 0.0

    duplicate_seed_id = manager.add_or_update_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )
    assert duplicate_seed_id == seed_id

    manager.seeds[seed_id].occurrence_count = 3
    manager.run_validation_gate(seed_id, external_evidence=True)
    manager.run_validation_gate(seed_id, external_evidence=True)
    result = manager.run_validation_gate(seed_id, external_evidence=True)

    assert result is True
    assert manager.seeds[seed_id].status == SeedStatus.PROMOTED
    assert manager.seeds[seed_id].weight >= 0.4


def test_atomic_seed_respects_custom_word_limit():
    manager = SSLManager(
        embedding_fn=fake_embedding,
        config=SSLCoreConfig(max_seed_words=4),
    )

    text = "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."

    assert SSLManager.is_atomic_seed(text)
    assert not manager.is_atomic_seed(text, max_seed_words=manager.config.max_seed_words)

    with pytest.raises(ValueError, match="Seed appears too broad"):
        manager.add_or_update_seed(text)


def test_detailed_validation_gate_records_reasoning():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )
    manager.seeds[seed_id].occurrence_count = 3

    first = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    second = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    third = manager.run_validation_gate_detailed(seed_id, external_evidence=True)
    fourth = manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    assert first.verdict == "blocked"
    assert first.external_evidence_passed is False
    assert second.verdict == "validated"
    assert third.verdict == "validated"
    assert fourth.verdict == "promoted"
    assert manager.validation_log[-1].promoted is True
    assert manager.event_log[-1].event_type == "validated"


def test_blocked_validation_records_block_event():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )
    manager.seeds[seed_id].occurrence_count = 3

    result = manager.run_validation_gate_detailed(seed_id, external_evidence=True)

    assert result.verdict == "blocked"
    assert result.status_before == SeedStatus.NEW.value
    assert result.status_after == SeedStatus.NEW.value
    assert manager.event_log[-1].event_type == "validation_blocked"


def test_reactivate_dormant_seed_by_keyword():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Koloniale katoen als grondstof voor de Britse textielindustrie.",
        trigger_keywords=["katoen", "textiel"],
    )
    manager.seeds[seed_id].status = SeedStatus.DORMANT
    manager.seeds[seed_id].trace = 0.01

    reactivated = manager.reactivate_by_text("De katoenhandel voedde de textielindustrie.")
    assert reactivated == [seed_id]
    assert manager.seeds[seed_id].status == SeedStatus.NEW
    assert manager.seeds[seed_id].trace > 2.0


def test_contradiction_resets_weight_and_status():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )
    manager.seeds[seed_id].weight = 0.6
    manager.seeds[seed_id].occurrence_count = 4

    result = manager.run_validation_gate(seed_id, contradiction=True)
    assert result is False
    assert manager.seeds[seed_id].status == SeedStatus.NEW
    assert manager.seeds[seed_id].occurrence_count == 1
    assert manager.seeds[seed_id].weight < 0.6


def test_contradiction_detailed_result_records_reset():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )
    manager.seeds[seed_id].weight = 0.6
    manager.seeds[seed_id].occurrence_count = 4

    result = manager.run_validation_gate_detailed(seed_id, contradiction=True)

    assert result.verdict == "contradicted"
    assert result.contradiction_applied is True
    assert result.status_after == SeedStatus.NEW.value
    assert manager.event_log[-1].event_type == "contradicted"


def test_constellations_group_promoted_seeds():
    manager = SSLManager(embedding_fn=fake_embedding, dedup_threshold=0.999)
    first = manager.add_or_update_seed(
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen."
    )
    second = manager.add_or_update_seed(
        "Winsten uit trans-Atlantische slavenhandel als investeringskapitaal voor industrialisatie."
    )
    third = manager.add_or_update_seed(
        "Koloniale katoen als grondstof voor de Britse textielindustrie."
    )

    for seed_id in [first, second, third]:
        manager.seeds[seed_id].status = SeedStatus.PROMOTED
        manager.seeds[seed_id].weight = 0.6

    constellations = manager.find_constellations(threshold=0.95, min_members=3)
    assert len(constellations) == 1
    assert constellations[0].members == [first, second, third]
