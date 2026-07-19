from shadowseed.benchmark.ssl45_gap_suite import lexical_embedding
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.ssot import SSOTManager
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore


def make_manager_and_ssot():
    seed_constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=seed_constellation,
        validation_increment=0.2,
        promotion_threshold=0.5,
    )
    ssot = SSOTManager(InMemoryVectorStore(), manager)
    return manager, ssot


def prepare_open_seed(manager: SSLManager, seed_text: str) -> str:
    seed_id = manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    assert manager.get_seed(seed_id).occurrence_count >= 3
    assert manager.get_seed(seed_id).weight == 0.0
    return seed_id


def test_bad_ssot_document_does_not_promote_unrelated_seed():
    manager, ssot = make_manager_and_ssot()
    seed_id = prepare_open_seed(
        manager,
        "Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
    )

    ssot.ingest_document(
        "De hoofdstad van Frankrijk is Milaan. "
        "Deze tekst gaat over aardrijkskunde en bevat geen juridische onderbouwing. "
        "Er staat niets over toepasselijk recht of consumentencontracten.",
        doc_id="bad_doc_001",
        chunk_words=12,
    )

    validations = ssot.validate_open_seeds_against_ssot(
        threshold=0.70,
        top_k=5,
        max_evidence_per_seed=4,
    )

    seed = manager.get_seed(seed_id)
    assert validations == []
    assert seed.status != SeedStatus.PROMOTED
    assert seed.weight == 0.0
    assert seed.evidence_count == 0


def test_llm_proposed_chunks_do_not_validate_until_verified():
    manager, ssot = make_manager_and_ssot()
    seed_id = prepare_open_seed(
        manager,
        "Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
    )

    chunk_ids = ssot.ingest_from_llm_output(
        "Bij een grensoverschrijdend consumentencontract moet het toepasselijk recht worden vastgesteld. "
        "Het toepasselijk recht bepaalt welke consumentenregels gelden.",
        doc_id="llm_proposal_001",
        chunk_words=8,
    )

    validations_before_verification = ssot.validate_open_seeds_against_ssot(
        threshold=0.0,
        top_k=5,
        max_evidence_per_seed=4,
    )
    seed_before = manager.get_seed(seed_id)

    assert chunk_ids
    assert validations_before_verification == []
    assert seed_before.status != SeedStatus.PROMOTED
    assert seed_before.weight == 0.0
    assert seed_before.evidence_count == 0

    for chunk_id in chunk_ids:
        ssot.verify_chunk(chunk_id, verifier="test_human")

    validations_after_verification = ssot.validate_open_seeds_against_ssot(
        threshold=0.0,
        top_k=5,
        max_evidence_per_seed=4,
    )
    seed_after = manager.get_seed(seed_id)

    assert validations_after_verification
    assert seed_after.evidence_count > 0
    assert seed_after.weight > 0.0
    assert seed_after.status in {SeedStatus.ACTIVE, SeedStatus.PROMOTED}


def test_rejected_llm_chunk_never_validates_seed():
    manager, ssot = make_manager_and_ssot()
    seed_id = prepare_open_seed(
        manager,
        "Afdwingbaarheid van EU-consumentenrecht tegenover een niet-EU retailer.",
    )

    chunk_ids = ssot.ingest_from_llm_output(
        "EU-consumentenrecht is altijd automatisch afdwingbaar tegenover iedere niet-EU retailer.",
        doc_id="llm_bad_claim_001",
        chunk_words=10,
    )
    for chunk_id in chunk_ids:
        ssot.reject_chunk(chunk_id, verifier="test_human")

    validations = ssot.validate_open_seeds_against_ssot(
        threshold=0.0,
        top_k=5,
        max_evidence_per_seed=4,
    )

    seed = manager.get_seed(seed_id)
    assert validations == []
    assert seed.status != SeedStatus.PROMOTED
    assert seed.weight == 0.0
    assert seed.evidence_count == 0
