#!/usr/bin/env python3
"""Model-free before/after SSOT polarity regression against the REAL Gate.

The historical, unfixed result is preserved in PR #240 and its archived
GitHub Actions JSON artifact, not recomputed by installing a fake legacy Gate.
All current cases use the product manager, SSOT and Gate unchanged apart from
the reviewed source-relation producer. Every text and attestation is synthetic.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from shadowseed.manager import SSLManager
from shadowseed.ssot import SSOTManager, SSOTRelation
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

HISTORIC_BUG_RUN = (
    "https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40176388209"
)


def _case(
    name: str,
    texts: tuple[str, ...],
    *,
    relation: SSOTRelation | None = None,
    proposed: bool = False,
) -> dict:
    manager = SSLManager(embedding_fn=lexical_embedding)
    ssot = SSOTManager(InMemoryVectorStore(), manager)
    seed_id = manager.add_or_update_seed(HYPOTHESIS)
    manager.add_or_update_seed(HYPOTHESIS)
    manager.add_or_update_seed(HYPOTHESIS)
    seed_before = manager.get_seed(seed_id)
    assert seed_before.weight == 0 and seed_before.evidence_count == 0

    for index, text in enumerate(texts, start=1):
        doc_id = f"g0_{name}_{index:02d}"
        if proposed:
            ssot.ingest_from_llm_output(
                text, doc_id=doc_id, source="investigator_simulated_unverified"
            )
        else:
            # Verified is intentionally *synthetic metadata*, not a real review.
            ssot.ingest_document(
                text, doc_id=doc_id,
                source="investigator_simulated_verified_metadata",
                trust_level="user_verified",
            )
        if relation is not None:
            # Review is also simulated by the experiment AUTHOR; not a
            # genuine human assessment, independent truth, or provenance proof.
            ssot.attest_document_relation(
                seed_id, doc_id, relation=relation,
                reviewer="synthetic_investigator_not_independent",
                rationale="Authored explicit relationship for falsification test.",
            )

    retrieved = ssot.search(HYPOTHESIS, top_k=10)
    observed = ssot.validate_open_seeds_against_ssot(
        threshold=0.65, top_k=10, max_evidence_per_seed=4
    )
    final_seed = manager.get_seed(seed_id)
    return {
        "case": name,
        "relation_author_label_not_model_judgment": (
            relation.value if relation is not None else "not_reviewed"
        ),
        "source_status_is_test_metadata_not_independent_verification": True,
        "reviewer_is_experiment_author_not_independent": True,
        "retrieval_hits": [
            {
                "chunk_id": chunk_id,
                "similarity": round(float(score), 6),
                "status": meta["status"],
                "chunk_text": meta["text"],
            }
            for chunk_id, score, meta in retrieved
        ],
        "accepted_ssot_signal_count": sum(
            len(record["applied_evidence"]) for record in observed
        ),
        "gate_events": [
            {
                "decision": event.decision.value,
                "policy_id": event.policy_id,
                "signal_kinds": [s.kind.value for s in event.signals],
                "directions": [s.direction.value for s in event.signals],
                "source_refs": [s.source_ref for s in event.signals],
            }
            for event in manager.gate_events
        ],
        "final_seed": {
            "status": final_seed.status.value,
            "weight": final_seed.weight,
            "evidence_count": final_seed.evidence_count,
            "occurrence_count": final_seed.occurrence_count,
        },
    }


def build_result() -> dict:
    cases = {
        "affirmation_without_relation": _case("affirm_unreviewed", AFFIRMING),
        "affirmation_with_author_support": _case(
            "affirm_reviewed", AFFIRMING, relation=SSOTRelation.SUPPORTS
        ),
        "explicit_negation_with_author_opposition": _case(
            "negate_reviewed", NEGATING, relation=SSOTRelation.OPPOSES
        ),
        "unverified_with_author_support": _case(
            "unverified_reviewed", NEGATING,
            relation=SSOTRelation.SUPPORTS, proposed=True
        ),
    }
    for case in cases.values():
        assert len(case["retrieval_hits"]) == 4
        assert min(row["similarity"] for row in case["retrieval_hits"]) > 0.65

    yes = cases["affirmation_with_author_support"]
    for name, case in cases.items():
        if name == "affirmation_with_author_support":
            assert case["accepted_ssot_signal_count"] == 4
            assert case["final_seed"]["weight"] > 0
            assert case["final_seed"]["evidence_count"] == 4
            assert len(case["gate_events"]) == 4
            assert all(
                any(k == "ssot" and d == "support" for k, d in zip(
                    event["signal_kinds"], event["directions"]
                ))
                for event in case["gate_events"]
            )
        else:
            assert case["accepted_ssot_signal_count"] == 0
            assert not case["gate_events"]
            assert case["final_seed"]["weight"] == 0
            assert case["final_seed"]["evidence_count"] == 0
    assert yes["final_seed"]["status"] == "PROMOTED"

    return {
        "schema": "g0-ssot-polarity-before-after-characterization-v1",
        "status": "post_fix_synthetic_mechanics_characterized_not_independently_verified",
        "historic_pre_fix_result": {
            "source": HISTORIC_BUG_RUN,
            "original_git_commit": "4c433c6e95733491e4b4720950bf997f5f1af634",
            "affirmation": {"ssot_support": 4, "final_weight": 0.6},
            "explicit_negation": {"ssot_support": 4, "final_weight": 0.6},
            "unverified_negation": {"ssot_support": 0, "final_weight": 0},
            "note": "Archival observation, not re-executed in this revision.",
        },
        "current_product_code_executed": True,
        "input_provenance": "INVESTIGATOR_AUTHORED_FICTIONAL_POLARITIES",
        "human_verifiers": 0,
        "model_calls": 0,
        "no_research_gate_or_polarity_classifier": True,
        "observations_are_not_independent_truth_labels": True,
        "G0_passed": False,
        "Q1_tested": False,
        "Q2_tested": False,
        "cases": cases,
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
        "SSOT polarity after fix: real Gate, synthetic case reviews. "
        "Unreviewed and opposing sources add no authority. "
        "Historical defect retained as an immutable earlier-run reference. "
        "No independent evidence, G0 or Q1/Q2 finding."
    )


if __name__ == "__main__":
    main()
