"""Smoke runner for weightless shadow seeds in vector space."""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.text_similarity import lexical_embedding
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.vector_constellation import VectorConstellation
from shadowseed.vectorstore import create_vector_store


def run_vectorstore_smoke(output_path: str, backend: str = "memory") -> Path:
    constellation = VectorConstellation(create_vector_store(backend=backend, dimensions=128))
    manager = SSLManager(
        embedding_fn=lexical_embedding,
        vector_constellation=constellation,
        dedup_threshold=0.85,
        promotion_threshold=0.5,
        validation_increment=0.2,
    )

    seed_text = "Toepasselijk recht bij een grensoverschrijdend consumentencontract."
    seed_id = manager.add_or_update_seed(
        seed_text,
        trigger_keywords=["toepasselijk", "recht", "consumentencontract"],
    )
    seed_after_creation = manager.get_seed(seed_id).to_dict()

    # The query must share lexical tokens with the seed: the lexical embedding is
    # token-based, so a paraphrase with zero shared tokens scores 0.0 against the
    # seed and the smoke silently reports passed=false (the old query did exactly
    # that). The smoke is a mechanical chain check, not a paraphrase benchmark.
    uncertainty_matches = manager.find_uncertain_region(
        "Welk recht is van toepassing op dit grensoverschrijdend consumentencontract?",
        threshold=0.20 if backend != "chroma" else 0.05,
    )

    # Repeat detection until occurrence_count can satisfy the Validation Gate.
    manager.add_or_update_seed(seed_text)
    manager.add_or_update_seed(seed_text)

    # Four rounds, not three: the Gate requires min_evidence_for_gate=2, so the
    # first positive round only banks evidence (blocked, no weight gain). Rounds
    # 2-4 then validate at +0.2 each -> 0.6 >= promotion_threshold 0.5.
    feedback_threshold = 0.20 if backend != "chroma" else 0.05
    feedback_rounds = []
    for _ in range(4):
        feedback_rounds.append(
            manager.apply_external_feedback(
                "De casus mist toepasselijk recht voor een grensoverschrijdend consumentencontract.",
                context="Nederlandse consument koopt defecte laptop bij Amerikaanse webwinkel.",
                positive=True,
                threshold=feedback_threshold,
            )
        )

    promoted_seed = manager.get_seed(seed_id).to_dict()

    # Same lexical-overlap requirement for the falsification arm.
    contradiction_updates = manager.apply_external_feedback(
        "Het toepasselijk recht bij dit grensoverschrijdend consumentencontract is hier niet relevant.",
        context="Nederlandse consument koopt defecte laptop bij Amerikaanse webwinkel.",
        positive=False,
        threshold=feedback_threshold,
    )
    contradicted_seed = manager.get_seed(seed_id).to_dict()

    summary = {
        "backend": backend,
        "seed_id": seed_id,
        "vector_ids": constellation.store.get_all_ids(),
        "feedback_events": len(constellation.feedback_log),
        "created_weight": seed_after_creation["weight"],
        "created_status": seed_after_creation["status"],
        "uncertain_matches": len(uncertainty_matches),
        "promoted_status": promoted_seed["status"],
        "promoted_weight": promoted_seed["weight"],
        "contradicted_status": contradicted_seed["status"],
        "contradicted_weight": contradicted_seed["weight"],
        "passed": (
            seed_after_creation["weight"] == 0.0
            and len(uncertainty_matches) >= 1
            and promoted_seed["status"] == SeedStatus.PROMOTED.value
            and promoted_seed["weight"] >= 0.5
            and contradicted_seed["weight"] < promoted_seed["weight"]
        ),
    }

    payload = {
        "summary": summary,
        "seed_after_creation": seed_after_creation,
        "uncertainty_matches": uncertainty_matches,
        "feedback_rounds": feedback_rounds,
        "promoted_seed": promoted_seed,
        "contradiction_updates": contradiction_updates,
        "contradicted_seed": contradicted_seed,
        "constellation": constellation.to_dict(),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output
