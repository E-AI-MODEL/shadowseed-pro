#!/usr/bin/env python3
"""Model-free characterization of real SSOT evidence polarity in the product.

This experiment is a *synthetic falsification probe*, not a scientific truth
assessment, production policy change, EAI score, Q1/Q2 result, or independent
source-verification run. It uses the canonical SSLManager, SSOTManager, VectorStore
and Validation Gate. The experiment author supplies both opposite statements;
the product's similarity search receives no external polarity verdict.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shadowseed.manager import SSLManager
from shadowseed.ssot import SSOTManager
from shadowseed.text_similarity import lexical_embedding
from shadowseed.vectorstore import InMemoryVectorStore


HYPOTHESIS = "Mogelijk beïnvloedt de blauwe klep de druk in kamer B."
AFFIRMING = (
    "De blauwe klep beïnvloedt de druk in kamer B.",
    "In kamer B beïnvloedt de blauwe klep de druk.",
    "Metingen bevestigen dat de blauwe klep de druk in kamer B beïnvloedt.",
    "De blauwe klep beïnvloedt volgens proefmetingen de druk in kamer B.",
)
NEGATING = (
    "De blauwe klep beïnvloedt de druk in kamer B niet.",
    "In kamer B beïnvloedt de blauwe klep de druk niet.",
    "Metingen bevestigen dat de blauwe klep de druk in kamer B niet beïnvloedt.",
    "De blauwe klep beïnvloedt volgens proefmetingen de druk in kamer B niet.",
)


def _case(name: str, texts: tuple[str, ...], *, proposed: bool = False) -> dict:
    manager = SSLManager(embedding_fn=lexical_embedding)
    ssot = SSOTManager(InMemoryVectorStore(), manager)
    # Repetition here is intentional frozen *researcher input*. It is NOT
    # independently observed model recurrence or verified external evidence.
    seed_id = manager.add_or_update_seed(HYPOTHESIS)
    manager.add_or_update_seed(HYPOTHESIS)
    manager.add_or_update_seed(HYPOTHESIS)
    seed = manager.get_seed(seed_id)
    assert seed.weight == 0.0 and seed.evidence_count == 0
    assert seed.occurrence_count == 3

    for index, text in enumerate(texts, start=1):
        doc_id = f"g0_{name}_{index:02d}"
        if proposed:
            ssot.ingest_from_llm_output(text, doc_id=doc_id, source="investigator_simulated_unverified")
        else:
            # Only the *metadata* is marked user_verified: there is NO
            # independent human fact-check. This is precisely the trust
            # assumption we seek to separate from semantic entailment.
            ssot.ingest_document(
                text,
                doc_id=doc_id,
                source="investigator_simulated_verified_metadata",
                trust_level="user_verified",
            )

    hits = ssot.search(HYPOTHESIS, top_k=10)
    hit_rows = [
        {
            "chunk_id": chunk_id,
            "similarity": round(float(score), 6),
            "chunk_text": str(metadata["text"]),
            "status": metadata["status"],
            "trust_level": metadata["trust_level"],
        }
        for chunk_id, score, metadata in hits
    ]
    actual = ssot.validate_open_seeds_against_ssot(
        threshold=0.65, top_k=10, max_evidence_per_seed=4
    )
    seed = manager.get_seed(seed_id)
    events = [
        {
            "decision": event.decision.value,
            "policy_id": event.policy_id,
            "source_refs": [s.source_ref for s in event.signals],
            "directions": [s.direction.value for s in event.signals],
            "signal_kinds": [s.kind.value for s in event.signals],
            "verified_flags": [s.verified for s in event.signals],
        }
        for event in manager.gate_events
    ]
    return {
        "name": name,
        "input_polarity_author_label_not_model_judgment": (
            "proposed_unverified" if proposed else name
        ),
        "simulated_verified_metadata_only": not proposed,
        "retrieval_hits": hit_rows,
        "similarity_cutoff": 0.65,
        "accepted_evidence_count": sum(len(x["applied_evidence"]) for x in actual),
        "gate_decisions": events,
        "final_seed": {
            "text": seed.text,
            "status": seed.status.value,
            "weight": seed.weight,
            "evidence_count": seed.evidence_count,
            "occurrence_count": seed.occurrence_count,
            "trace": seed.trace,
        },
    }


def build_result() -> dict:
    confirming = _case("author_affirms", AFFIRMING)
    denying = _case("author_negates", NEGATING)
    unverified = _case("author_negates_unverified", NEGATING, proposed=True)
    assert len(confirming["retrieval_hits"]) == 4
    assert len(denying["retrieval_hits"]) == 4
    assert len(unverified["retrieval_hits"]) == 4
    assert min(x["similarity"] for x in confirming["retrieval_hits"]) > 0.65
    assert min(x["similarity"] for x in denying["retrieval_hits"]) > 0.65

    # Characterize what the existing code ACTUALLY does, not what it ought
    # to do. Any failure indicates an upstream change and needs re-auditing.
    assert confirming["accepted_evidence_count"] == 4
    assert denying["accepted_evidence_count"] == 4
    assert unverified["accepted_evidence_count"] == 0
    assert all(
        event["directions"] == ["support"]
        for record in (confirming, denying)
        for event in record["gate_decisions"]
    )
    assert not unverified["gate_decisions"]
    assert confirming["final_seed"]["weight"] > 0
    assert denying["final_seed"]["weight"] > 0
    assert unverified["final_seed"]["weight"] == 0
    assert denying["final_seed"]["evidence_count"] == 4

    return {
        "schema": "g0-ssot-polarity-mechanical-characterization-v0",
        "status": "existing_product_code_characterized_not_repaired",
        "input_provenance": "INVESTIGATOR_AUTHORED_FICTIONAL_POLARITIES",
        "observations_are_not_independent_truth_labels": True,
        "model_calls": 0,
        "human_verifiers": 0,
        "product_code_changed": False,
        "experimental_policy_changed": False,
        "gate_logic_changed": False,
        "Q1_tested": False,
        "Q2_tested": False,
        "G0_passed": False,
        "hypothesis": HYPOTHESIS,
        "finding_scope": (
            "SSOT similarity and 'verified' metadata drive SUPPORT signals "
            "without textual polarity/entailment evaluation; negating statements "
            "in this frozen synthetic contrast are treated as positive evidence."
        ),
        "cases": {
            "affirmation": confirming,
            "explicit_negation": denying,
            "unverified_negation": unverified,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_result()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "G0 SSOT polarity: canonical product characterized. "
        "Opposite author-polarity statements both generated SUPPORT and weight; "
        "unverified proposals did not. No LLM or independent assessment."
    )


if __name__ == "__main__":
    main()
