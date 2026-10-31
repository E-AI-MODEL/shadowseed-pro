#!/usr/bin/env python3
"""Model-free SSOT relation handoff on the real product manager.

PR #240 keeps the original, now-fixed product defect in an archived Actions
trace. PR #243 initially let fabricated 'reviewer' labels reach the real Gate;
this revision makes ALL relation inspection read-only. The true product
evidence.verify boundary is separate. All test texts/reviews are researcher
authored; this is not G0 or a new model result.
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
        "review_candidate_count": sum(
            len(record["review_candidates"]) for record in observed
        ),
        "gate_authorized": any(
            record["gate_authorized"] for record in observed
        ),
        "candidate_review_required": all(
            not candidate["gate_authorized"]
            and candidate["requires_authorized_submission"]
            for record in observed
            for candidate in record["review_candidates"]
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

    affirmative = cases["affirmation_with_author_support"]
    assert affirmative["review_candidate_count"] == 4
    for name, case in cases.items():
        assert case["gate_authorized"] is False
        assert case["candidate_review_required"] is True
        assert case["gate_events"] == []
        assert case["final_seed"]["weight"] == 0.0
        assert case["final_seed"]["evidence_count"] == 0
        assert case["final_seed"]["status"] != "PROMOTED"
        if name != "affirmation_with_author_support":
            assert case["review_candidate_count"] == 0

    return {
        "schema": "g0-ssot-polarity-read-only-handoff-v2",
        "status": "researcher_asserted_relations_read_only_no_gate_authority",
        "historic_pre_fix_result": {
            "source": HISTORIC_BUG_RUN,
            "original_git_commit": "4c433c6e95733491e4b4720950bf997f5f1af634",
            "affirmation": {"ssot_support": 4, "final_weight": 0.6},
            "explicit_negation": {"ssot_support": 4, "final_weight": 0.6},
            "unverified_negation": {"ssot_support": 0, "final_weight": 0},
            "note": "Archival observation, not re-executed in this revision.",
        },
        "current_product_code_executed": True,
        "authorized_actor_submissions": 0,
        "intermediate_unsafe_attestation_run": (
            "https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40182789691"
        ),
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
        "SSOT polarity read-only handoff: real product SSOT, no Gate event. "
        "Researcher-asserted support produces review candidates, never authority. "
        "Historical defect and intermediate regression remain cited, not rerun. "
        "No independent evidence, G0 or Q1/Q2 finding."
    )


if __name__ == "__main__":
    main()
