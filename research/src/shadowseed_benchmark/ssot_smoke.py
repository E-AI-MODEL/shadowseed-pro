"""Smoke runner for SSOT-backed Shadow Seed validation."""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.text_similarity import lexical_embedding
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.ssot import SSOTManager
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import create_vector_store


SSOT_DOCUMENT = """
Bij een grensoverschrijdend consumentencontract tussen een Nederlandse consument
en een Amerikaanse webwinkel moet eerst de rechtsbevoegdheid worden beoordeeld.
Het toepasselijk recht bepaalt welke consumentenregels de koop beheersen.
De afdwingbaarheid van EU-consumentenrecht tegenover een niet-EU retailer moet
apart worden getoetst. Een forumkeuzebeding in internationale online
koopvoorwaarden kan invloed hebben op waar een geschil wordt behandeld.
""".strip()


def run_ssot_smoke(output_path: str, backend: str = "memory") -> Path:
    seed_constellation = VectorConstellation(create_vector_store(backend=backend, dimensions=128, collection_name="seed_smoke"))
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=seed_constellation,
        dedup_threshold=0.85,
        promotion_threshold=0.5,
        validation_increment=0.2,
    )
    ssot = SSOTManager(create_vector_store(backend=backend, dimensions=128, collection_name="ssot_smoke"), manager)

    seed_text = "Toepasselijk recht bij een grensoverschrijdend consumentencontract."
    seed_id = manager.add_or_update_seed(seed_text, trigger_keywords=["toepasselijk", "recht"])
    manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    seed_before_ssot = manager.get_seed(seed_id).to_dict()

    chunks = ssot.ingest_document(
        SSOT_DOCUMENT,
        doc_id="legal_protocol_001",
        source="test_fixture_upload",
        trust_level="user_verified",
        chunk_words=8,
    )

    threshold = 0.10 if backend != "chroma" else 0.03
    retrieved_context = ssot.retrieve_context(
        "Welke regels gelden voor toepasselijk recht bij een Amerikaanse webwinkel?",
        top_k=3,
        threshold=threshold,
    )
    validations = ssot.validate_open_seeds_against_ssot(
        threshold=threshold,
        top_k=8,
        max_evidence_per_seed=4,
    )
    seed_after_ssot = manager.get_seed(seed_id).to_dict()

    summary = {
        "backend": backend,
        "seed_id": seed_id,
        "doc_count": len(ssot.documents),
        "chunk_count": len(chunks),
        "retrieved_context_count": len(retrieved_context),
        "validations": len(validations),
        "before_status": seed_before_ssot["status"],
        "before_weight": seed_before_ssot["weight"],
        "before_evidence_count": seed_before_ssot["evidence_count"],
        "after_status": seed_after_ssot["status"],
        "after_weight": seed_after_ssot["weight"],
        "after_evidence_count": seed_after_ssot["evidence_count"],
        "passed": (
            len(chunks) >= 4
            and len(retrieved_context) >= 1
            and seed_before_ssot["weight"] == 0.0
            and seed_after_ssot["status"] == SeedStatus.PROMOTED.value
            and seed_after_ssot["weight"] >= 0.5
            and seed_after_ssot["evidence_count"] >= 4
        ),
    }

    payload = {
        "summary": summary,
        "ssot": ssot.to_dict(),
        "seed_before_ssot": seed_before_ssot,
        "retrieved_context": retrieved_context,
        "validations": validations,
        "seed_after_ssot": seed_after_ssot,
        "ssl_state": manager.to_dict(),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output
