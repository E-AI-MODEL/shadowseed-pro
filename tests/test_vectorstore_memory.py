from datetime import datetime, timedelta

from shadowseed.benchmark.ssl45_gap_suite import lexical_embedding
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore


def test_in_memory_vectorstore_search_and_metadata_update():
    store = InMemoryVectorStore()
    emb = lexical_embedding("toepasselijk recht consumentencontract")
    store.add("seed-1", emb, {"weight": 0.0, "label": "open"})

    results = store.search(lexical_embedding("recht consumentencontract"), top_k=1)

    assert results[0][0] == "seed-1"
    assert results[0][1] > 0.0

    store.update_metadata("seed-1", {"weight": 0.2})
    assert store.get_metadata("seed-1")["weight"] == 0.2


def test_ssl_manager_indexes_weightless_seed_in_vector_constellation():
    constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=constellation,
    )

    seed_id = manager.add_or_update_seed("Toepasselijk recht bij een grensoverschrijdend consumentencontract.")

    assert seed_id in constellation.store.get_all_ids()
    metadata = constellation.store.get_metadata(seed_id)
    assert metadata["weight"] == 0.0
    assert metadata["status"] == SeedStatus.NEW.value


def test_uncertain_region_and_feedback_flow_uses_validation_gate():
    constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=constellation,
        validation_increment=0.2,
        promotion_threshold=0.5,
    )
    seed_text = "Toepasselijk recht bij een grensoverschrijdend consumentencontract."
    seed_id = manager.add_or_update_seed(seed_text)

    matches = manager.find_uncertain_region(
        "Welke regels gelden voor toepasselijk recht bij een grensoverschrijdend consumentencontract?",
        threshold=0.20,
    )
    assert matches
    assert matches[0]["seed_id"] == seed_id
    assert manager.get_seed(seed_id).weight == 0.0

    manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    for _ in range(4):
        manager.apply_external_feedback(
            "Toepasselijk recht ontbreekt in deze grensoverschrijdende consumentenkoop.",
            context="Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
            positive=True,
            threshold=0.10,
        )

    assert manager.get_seed(seed_id).status == SeedStatus.PROMOTED
    assert manager.get_seed(seed_id).weight >= 0.5
    assert constellation.store.get_metadata(seed_id)["status"] == SeedStatus.PROMOTED.value

    manager.apply_external_feedback(
        "Deze gap is tegengesproken door externe beoordeling.",
        context="Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
        positive=False,
        threshold=0.10,
    )
    assert manager.get_seed(seed_id).weight < 0.5


def test_vector_constellation_housekeeping_expires_old_open_seed():
    constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=constellation,
    )
    seed_id = manager.add_or_update_seed("Afdwingbaarheid van EU-consumentenrecht tegenover een niet-EU retailer.")
    old_date = (datetime.now() - timedelta(days=60)).isoformat()
    manager.seeds[seed_id].created_at = old_date
    constellation.sync_seed(manager.seeds[seed_id])

    expired = manager.expire_vector_only_open_seeds(max_age_days=30)

    assert expired == [seed_id]
    assert manager.get_seed(seed_id).status == SeedStatus.EXPIRED
    assert seed_id not in constellation.store.get_all_ids()
