"""Optional paper evidence smoke runner.

This runner checks that paper-derived SSOT proposals remain read-only
review candidates and never grant Gate authority.

Important safety rule:
- paper chunks start as llm_proposed;
- llm_proposed chunks do not validate seeds;
- verifying chunks alone does not create a relation review;
- an explicit relation review permits inspection, not Gate authorization.
"""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.text_similarity import lexical_embedding
from shadowseed.manager import SSLManager
from shadowseed.ssot import SSOTManager, SSOTRelation
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import InMemoryVectorStore


PAPER_TEXT = """
Retrieval augmented generation systems can fail when retrieved context contains
conflicting evidence. A model may choose one source without noticing the conflict.
This failure mode suggests that source conflict detection is a missing validation
step in retrieval pipelines.
""".strip()


def run_paper_evidence_smoke(output_path: str = "results/paper_evidence_smoke.json") -> Path:
    constellation = VectorConstellation(InMemoryVectorStore())
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=constellation,
        validation_increment=0.2,
        promotion_threshold=0.5,
    )

    paper_ssot = SSOTManager(InMemoryVectorStore(), manager)

    seed_text = "Bronconflict tussen opgehaalde documenten wordt niet herkend."
    seed_id = manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)

    chunk_ids = paper_ssot.ingest_from_llm_output(
        PAPER_TEXT,
        doc_id="paper_fixture_001",
        source="paper_pipeline_smoke",
        chunk_words=18,
    )

    before = manager.get_seed(seed_id).to_dict()
    blocked_validations = paper_ssot.validate_open_seeds_against_ssot(
        threshold=0.0,
        top_k=8,
        max_evidence_per_seed=4,
    )
    after_blocked = manager.get_seed(seed_id).to_dict()

    for chunk_id in chunk_ids:
        paper_ssot.verify_chunk(chunk_id, verifier="paper_evidence_smoke")

    # Source verification alone cannot establish that a chunk supports a seed.
    unreviewed_candidates = paper_ssot.validate_open_seeds_against_ssot(
        threshold=0.0, top_k=8, max_evidence_per_seed=4
    )
    after_verified = manager.get_seed(seed_id).to_dict()
    paper_ssot.attest_document_relation(
        seed_id,
        "paper_fixture_001",
        relation=SSOTRelation.SUPPORTS,
        reviewer="paper_evidence_smoke_synthetic_operator",
        rationale="Synthetic review exercising read-only inspection, not a factual claim.",
    )
    review_candidates = paper_ssot.validate_open_seeds_against_ssot(
        threshold=0.0, top_k=8, max_evidence_per_seed=4
    )
    after_review = manager.get_seed(seed_id).to_dict()
    gate_events_after = len(manager.gate_events)
    safe_candidates = all(
        not record["gate_authorized"]
        and all(
            not item["gate_authorized"] and item["requires_authorized_submission"]
            for item in record["review_candidates"]
        )
        for record in review_candidates
    )

    payload = {
        "summary": {
            "passed": (
                before["weight"] == 0.0
                and blocked_validations == []
                and after_blocked["weight"] == 0.0
                and unreviewed_candidates == []
                and after_verified["weight"] == 0.0
                and bool(review_candidates)
                and safe_candidates
                and after_review["weight"] == 0.0
                and gate_events_after == 0
            ),
            "seed_id": seed_id,
            "chunk_count": len(chunk_ids),
            "blocked_validations": len(blocked_validations),
            "unreviewed_candidates": len(unreviewed_candidates),
            "review_candidates": len(review_candidates),
            "gate_events_after": gate_events_after,
            "before_weight": before["weight"],
            "after_blocked_weight": after_blocked["weight"],
            "after_verified_weight": after_verified["weight"],
            "after_verified_status": after_verified["status"],
            "after_review_weight": after_review["weight"],
            "interpretation": "Verified source chunks and explicit relation review provide read-only candidates; no Gate authority or weight change.",
        },
        "before": before,
        "blocked_validations": blocked_validations,
        "after_blocked": after_blocked,
        "unreviewed_candidates": unreviewed_candidates,
        "review_candidates": review_candidates,
        "after_review": after_review,
        "after_verified": after_verified,
        "paper_ssot": paper_ssot.to_dict(),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    print(run_paper_evidence_smoke())
