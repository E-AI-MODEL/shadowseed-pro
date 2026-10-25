"""SSOT negative controls: an authored contradiction is not SUPPORT evidence.

All content and relations in this test are fictional researcher inputs.
"""

from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.ssot import SSOTManager, SSOTRelation
from shadowseed.text_similarity import lexical_embedding
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore


SEED_TEXT = "Mogelijk beïnvloedt de blauwe klep de druk in kamer B."
OPPOSING = "De blauwe klep beïnvloedt de druk in kamer B niet."


def setup():
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=VectorConstellation(InMemoryVectorStore()),
        validation_increment=0.2,
        promotion_threshold=0.5,
    )
    ssot = SSOTManager(InMemoryVectorStore(), manager)
    seed_id = manager.add_or_update_seed(SEED_TEXT)
    manager.add_or_update_seed(SEED_TEXT)
    manager.add_or_update_seed(SEED_TEXT)
    return manager, ssot, seed_id


def test_explicit_opposition_is_retrieved_but_not_promoted():
    manager, ssot, seed_id = setup()
    for i in range(4):
        doc_id = f"synthetic_opposition_{i}"
        ssot.ingest_document(OPPOSING, doc_id=doc_id)
        ssot.attest_document_relation(
            seed_id, doc_id, relation=SSOTRelation.OPPOSES,
            reviewer="synthetic-author", rationale="Author-labelled fictional denial.",
        )
    assert len(ssot.search(SEED_TEXT, top_k=8)) == 4
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []
    seed = manager.get_seed(seed_id)
    assert seed.weight == 0 and seed.evidence_count == 0
    assert seed.status is not SeedStatus.PROMOTED
    # Neither a SUPPORT signal nor an automatic CONTRADICTION was constructed.
    assert manager.gate_events == []


def test_unreviewed_opposition_cannot_be_counted_as_support():
    manager, ssot, seed_id = setup()
    for i in range(4):
        ssot.ingest_document(OPPOSING, doc_id=f"unreviewed_{i}")
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []
    assert manager.get_seed(seed_id).weight == 0
    assert manager.gate_events == []


def test_llm_proposal_needs_both_source_verification_and_relation_review():
    manager, ssot, seed_id = setup()
    chunks = ssot.ingest_from_llm_output(
        "De blauwe klep beïnvloedt de druk in kamer B. " * 3,
        doc_id="llm_proposal", chunk_words=10,
    )
    assert chunks
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []
    for chunk_id in chunks:
        ssot.verify_chunk(chunk_id, verifier="test_human")
    # Source verification alone still does not verify the seed-specific relation.
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []
    ssot.attest_document_relation(
        seed_id, "llm_proposal", relation="supports", reviewer="test_human",
        rationale="Only an asserted relation in a synthetic test.",
    )
    result = ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8)
    assert len(result) == 1
    assert len(result[0]["applied_evidence"]) == 1
    assert manager.get_seed(seed_id).evidence_count == 1
    assert manager.get_seed(seed_id).weight == 0


def test_rejected_chunk_never_qualifies_even_with_support_review():
    manager, ssot, seed_id = setup()
    chunks = ssot.ingest_from_llm_output(OPPOSING, doc_id="rejected")
    assert chunks
    for chunk_id in chunks:
        ssot.reject_chunk(chunk_id, verifier="test_human")
    ssot.attest_document_relation(
        seed_id, "rejected", relation="supports", reviewer="test_human",
        rationale="Intentionally false research attestation to test trust boundary.",
    )
    assert ssot.validate_open_seeds_against_ssot(threshold=0) == []
    assert manager.get_seed(seed_id).weight == 0
    assert manager.gate_events == []


def test_unrelated_ssot_document_does_not_become_evidence():
    manager, ssot, seed_id = setup()
    ssot.ingest_document(
        "De hoofdstad van Frankrijk is Milaan. Dit gaat over aardrijkskunde.",
        doc_id="unrelated",
    )
    assert ssot.validate_open_seeds_against_ssot(threshold=0.9) == []
    assert manager.get_seed(seed_id).weight == 0


def test_old_similarity_only_gate_event_stays_immutable_and_blocks_recertification():
    manager, ssot, seed_id = setup()
    # Represent a historical pre-fix evidence event. No repair may rewrite it.
    manager.run_validation_gate(
        seed_id, external_evidence=True,
        signals=[
            ValidationSignal(
                kind=SignalKind.SSOT, direction=SignalDirection.SUPPORT,
                source_ref="legacy_doc::chunk_001", verified=True,
                independent=True, strength=0.99,
                reason="verified SSOT chunk legacy_doc::chunk_001",
            )
        ],
    )
    old_ledger = tuple(event.to_dict() for event in manager.gate_events)
    for i in range(4):
        doc_id = f"new_doc_{i}"
        ssot.ingest_document("De blauwe klep beïnvloedt de druk in kamer B.", doc_id=doc_id)
        ssot.attest_document_relation(
            seed_id, doc_id, relation="supports", reviewer="test_human",
            rationale="Fictional after-the-fact source review.",
        )
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []
    assert tuple(event.to_dict() for event in manager.gate_events) == old_ledger
    assert manager.get_seed(seed_id).weight == 0
