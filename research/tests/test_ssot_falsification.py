"""Research regression: SSOT retrieval alone cannot authorise seed evidence."""

from shadowseed_research.benchmark.ssl45_gap_suite import lexical_embedding
from shadowseed.manager import SSLManager
from shadowseed.ssot import SSOTManager, SSOTRelation
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore


def make_manager_and_ssot():
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=VectorConstellation(InMemoryVectorStore()),
        validation_increment=0.2,
        promotion_threshold=0.5,
    )
    ssot = SSOTManager(InMemoryVectorStore(), manager)
    seed_text = "Mogelijk beïnvloedt de blauwe klep de druk in kamer B."
    seed_id = manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    return manager, ssot, seed_id, seed_text


def test_retrieved_trusted_document_does_not_claim_relation_without_review():
    manager, ssot, seed_id, seed_text = make_manager_and_ssot()
    ssot.ingest_document(
        "De blauwe klep beïnvloedt de druk in kamer B niet.", doc_id="contrary"
    )
    assert ssot.retrieve_context(seed_text, threshold=0, top_k=5)
    assert ssot.validate_open_seeds_against_ssot(threshold=0) == []
    assert manager.get_seed(seed_id).weight == 0
    assert manager.gate_events == []


def test_reviewed_opposition_never_becomes_support_or_auto_contradiction():
    manager, ssot, seed_id, seed_text = make_manager_and_ssot()
    for index in range(4):
        doc_id = f"fictional_negative_{index}"
        ssot.ingest_document(
            "De blauwe klep beïnvloedt de druk in kamer B niet.", doc_id=doc_id
        )
        ssot.attest_document_relation(
            seed_id, doc_id, relation=SSOTRelation.OPPOSES,
            reviewer="investigator-not-independent",
            rationale="The research author wrote this opposition, not a fact-check.",
        )
    assert ssot.search(seed_text, top_k=5)
    assert ssot.validate_open_seeds_against_ssot(
        threshold=0, top_k=8, max_evidence_per_seed=4
    ) == []
    assert manager.get_seed(seed_id).evidence_count == 0
    assert manager.gate_events == []


def test_unverified_llm_proposal_cannot_pass_with_fake_support_attestation():
    manager, ssot, seed_id, _ = make_manager_and_ssot()
    chunks = ssot.ingest_from_llm_output(
        "De blauwe klep beïnvloedt de druk in kamer B.", doc_id="unverified"
    )
    assert chunks
    ssot.attest_document_relation(
        seed_id, "unverified", relation="supports", reviewer="investigator",
        rationale="Synthetic claim, deliberately not verified.",
    )
    assert ssot.validate_open_seeds_against_ssot(threshold=0) == []
    assert manager.get_seed(seed_id).weight == 0
