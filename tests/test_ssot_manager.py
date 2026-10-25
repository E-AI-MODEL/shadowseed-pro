"""Product SSOT contract: retrieval is not relation support or source truth.

Researcher-authored fictional source relationships in these tests are NOT
human-verification or proof of independent evidence units.
"""

import pytest

from shadowseed.gate.signals import SignalDirection, SignalKind
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.ssot import SSOTManager, SSOTRelation
from shadowseed.text_similarity import lexical_embedding
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore


SEED_TEXT = "Mogelijk beïnvloedt de blauwe klep de druk in kamer B."
AFFIRMING = "De blauwe klep beïnvloedt de druk in kamer B."


def make_manager_and_ssot() -> tuple[SSLManager, SSOTManager, str]:
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
    assert manager.get_seed(seed_id).weight == 0
    return manager, ssot, seed_id


def attest(ssot: SSOTManager, seed_id: str, doc_id: str,
           relation: SSOTRelation, unit: str | None = None) -> None:
    ssot.attest_document_relation(
        seed_id, doc_id, relation=relation, reviewer="researcher-simulated-human",
        rationale="Explicit fictional relation for a mechanics test.",
        evidence_unit_id=unit,
    )


def test_ssot_ingests_document_and_retrieves_context() -> None:
    manager = SSLManager(embedding_fn=lexical_embedding)
    ssot = SSOTManager(InMemoryVectorStore(), manager)
    chunks = ssot.ingest_document(
        "Toepasselijk recht is nodig bij een grensoverschrijdend consumentencontract.",
        doc_id="doc_001", chunk_words=6,
    )
    hits = ssot.retrieve_context("grensoverschrijdend consumentencontract", threshold=0.10)
    assert chunks and hits
    assert ssot.to_dict()["documents"][0]["doc_id"] == "doc_001"


def test_similar_verified_documents_never_raise_weight_without_relation_review() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    for n in range(4):
        ssot.ingest_document(AFFIRMING, doc_id=f"doc_{n}")
    assert ssot.retrieve_context(SEED_TEXT, top_k=5, threshold=0)
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=6) == []
    seed = manager.get_seed(seed_id)
    assert seed.weight == 0 and seed.evidence_count == 0
    assert seed.status is not SeedStatus.PROMOTED
    assert manager.gate_events == []


def test_explicitly_reviewed_support_uses_existing_gate_only() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    # Distinct IDs are *declared* source units, not verified independent studies.
    for n in range(4):
        doc_id = f"fictional_source_{n}"
        ssot.ingest_document(AFFIRMING, doc_id=doc_id)
        attest(ssot, seed_id, doc_id, SSOTRelation.SUPPORTS)
    assert manager.get_seed(seed_id).evidence_count == 0
    outcomes = ssot.validate_open_seeds_against_ssot(
        threshold=0, top_k=8, max_evidence_per_seed=8
    )
    seed = manager.get_seed(seed_id)
    assert len(outcomes) == 1
    assert len(outcomes[0]["applied_evidence"]) == 4
    assert seed.evidence_count == 4
    assert seed.status is SeedStatus.PROMOTED
    assert seed.weight >= 0.5
    assert len(manager.gate_events) == 4
    for event in manager.gate_events:
        ssot_signals = [s for s in event.signals if s.kind is SignalKind.SSOT]
        assert len(ssot_signals) == 1
        assert ssot_signals[0].direction is SignalDirection.SUPPORT
        assert ssot_signals[0].strength == 1.0
        assert ssot_signals[0].independent is False
        assert ssot_signals[0].reason.startswith("relation-attested:ssot:")
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []


def test_many_chunks_of_one_document_are_only_one_evidence_unit() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    ssot.ingest_document(
        "De blauwe klep beïnvloedt de druk in kamer B. "
        "Metingen bevestigen de druk in kamer B. "
        "De blauwe klep beïnvloedt ook de druk. "
        "Alleen ditzelfde document bevat deze fictieve beweringen.",
        doc_id="one_underlying_document", chunk_words=8,
    )
    attest(ssot, seed_id, "one_underlying_document", SSOTRelation.SUPPORTS)
    result = ssot.validate_open_seeds_against_ssot(
        threshold=0, top_k=12, max_evidence_per_seed=12
    )
    assert len(result) == 1
    assert len(result[0]["applied_evidence"]) == 1
    assert manager.get_seed(seed_id).evidence_count == 1
    assert manager.get_seed(seed_id).weight == 0
    assert manager.get_seed(seed_id).status is not SeedStatus.PROMOTED


def test_same_asserted_underlying_source_across_documents_counts_once() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    for n in range(3):
        doc_id = f"copy_{n}"
        ssot.ingest_document(AFFIRMING, doc_id=doc_id)
        attest(ssot, seed_id, doc_id, SSOTRelation.SUPPORTS, unit="one_original")
    result = ssot.validate_open_seeds_against_ssot(
        threshold=0, top_k=8, max_evidence_per_seed=8
    )
    assert len(result[0]["applied_evidence"]) == 1
    assert manager.get_seed(seed_id).evidence_count == 1
    assert manager.get_seed(seed_id).weight == 0


def test_conflicting_relations_same_source_unit_cannot_be_voted_into_support() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    for name, relation in (
        ("support", SSOTRelation.SUPPORTS),
        ("oppose", SSOTRelation.OPPOSES),
    ):
        ssot.ingest_document(AFFIRMING, doc_id=name)
        attest(ssot, seed_id, name, relation, unit="same_source")
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []
    assert manager.gate_events == []
    assert manager.get_seed(seed_id).weight == 0


@pytest.mark.parametrize("relation", [
    SSOTRelation.OPPOSES, SSOTRelation.TOPICAL,
    SSOTRelation.UNDETERMINED, SSOTRelation.NOT_TESTABLE,
])
def test_non_support_remains_investigable_not_authority(relation: SSOTRelation) -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    ssot.ingest_document(AFFIRMING, doc_id="one_source")
    attest(ssot, seed_id, "one_source", relation)
    assert ssot.search(SEED_TEXT)
    assert ssot.validate_open_seeds_against_ssot(threshold=0) == []
    assert manager.get_seed(seed_id).weight == 0
    assert manager.gate_events == []


def test_replacing_document_invalidates_reviews_and_removes_stale_chunks() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    ssot.ingest_document(
        AFFIRMING + " " + AFFIRMING,
        doc_id="evolving", chunk_words=7,
    )
    attest(ssot, seed_id, "evolving", SSOTRelation.SUPPORTS)
    ssot.ingest_document(
        "Een gewijzigde bron is geen ongewijzigde onderbouwing.",
        doc_id="evolving",
    )
    assert ssot.relation_reviews == {}
    assert len(ssot.store.get_all_ids()) == 1
    assert ssot.validate_open_seeds_against_ssot(threshold=0) == []
    assert manager.get_seed(seed_id).evidence_count == 0


def test_partial_document_verification_does_not_grant_document_wide_support() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    chunks = ssot.ingest_from_llm_output(
        AFFIRMING + " " + AFFIRMING + " " + AFFIRMING,
        doc_id="proposed", chunk_words=7,
    )
    assert len(chunks) >= 2
    ssot.verify_chunk(chunks[0], verifier="researcher")
    attest(ssot, seed_id, "proposed", SSOTRelation.SUPPORTS)
    assert ssot.validate_open_seeds_against_ssot(threshold=0, top_k=8) == []
    assert manager.get_seed(seed_id).weight == 0


def test_review_requires_known_identity_and_rationale() -> None:
    manager, ssot, seed_id = make_manager_and_ssot()
    ssot.ingest_document(AFFIRMING, doc_id="known")
    with pytest.raises(KeyError, match="Unknown seed"):
        ssot.attest_document_relation(
            "unknown", "known", relation="supports", reviewer="operator", rationale="x"
        )
    with pytest.raises(ValueError, match="rationale"):
        ssot.attest_document_relation(
            seed_id, "known", relation="supports", reviewer="operator", rationale=""
        )
    with pytest.raises(ValueError, match="reviewer"):
        ssot.attest_document_relation(
            seed_id, "known", relation="supports", reviewer="", rationale="x"
        )
    with pytest.raises(ValueError):
        ssot.attest_document_relation(
            seed_id, "known", relation="made_up", reviewer="operator", rationale="x"
        )
