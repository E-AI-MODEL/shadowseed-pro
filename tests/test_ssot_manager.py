from shadowseed.benchmark.ssl45_gap_suite import lexical_embedding
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.ssot import SSOTManager
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore


def test_ssot_ingests_document_and_retrieves_context():
    manager = SSLManager(embedding_fn=lexical_embedding)
    ssot = SSOTManager(InMemoryVectorStore(), manager)

    chunk_ids = ssot.ingest_document(
        "Toepasselijk recht is nodig bij een grensoverschrijdend consumentencontract.",
        doc_id="doc_001",
        chunk_words=6,
    )
    hits = ssot.retrieve_context("grensoverschrijdend consumentencontract", threshold=0.10)

    assert chunk_ids
    assert hits
    assert ssot.to_dict()["documents"][0]["doc_id"] == "doc_001"


def test_ssot_validates_open_seed_through_validation_gate():
    seed_constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=seed_constellation,
        validation_increment=0.2,
        promotion_threshold=0.5,
    )
    ssot = SSOTManager(InMemoryVectorStore(), manager)

    seed_text = "Toepasselijk recht bij een grensoverschrijdend consumentencontract."
    seed_id = manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)

    assert manager.get_seed(seed_id).weight == 0.0

    ssot.ingest_document(
        "Bij een grensoverschrijdend consumentencontract moet het toepasselijk recht worden vastgesteld. "
        "Het toepasselijk recht bepaalt welke consumentenregels gelden. "
        "Het toepasselijk recht is cruciaal bij internationale online koop. "
        "Dit is relevant bij een Nederlandse consument en een Amerikaanse webwinkel.",
        doc_id="doc_002",
        chunk_words=8,
    )
    validations = ssot.validate_open_seeds_against_ssot(
        threshold=0.0,
        top_k=8,
        max_evidence_per_seed=4,
    )

    seed = manager.get_seed(seed_id)
    assert validations
    assert seed.evidence_count >= 2
    assert seed.status == SeedStatus.PROMOTED
    assert seed.weight >= 0.5
