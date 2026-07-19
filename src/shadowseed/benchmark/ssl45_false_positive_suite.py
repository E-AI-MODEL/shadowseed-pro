"""False-positive controls for the SSL 4.5 Gap-Test Suite.

This suite now does two things:

1. keep the original regression check: complete answers should not produce fresh
   gap candidates via the standard detector;
2. stress the Validation Gate with adversarial lure candidates and compare the
   Gate against weaker promotion rules.

That makes the negative controls useful as more than a smoke-test. They now
show whether the current Gate blocks misleading seeds that weaker baselines
would promote.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from shadowseed.benchmark.ssl45_gap_suite import detect_candidate_seeds, lexical_embedding, tokenize
from shadowseed.manager import SSLManager, SeedStatus


ADVERSARIAL_LURES = {
    "geschiedenis en economie": [
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.",
        "Koloniale katoen als grondstof voor de Britse textielindustrie.",
        "Goedkope koloniale grondstoffen als voorwaarde voor schaalvergroting van productie.",
    ],
    "recht en jurisdictie": [
        "Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel.",
        "Toepasselijk recht bij een grensoverschrijdend consumentencontract.",
        "Afdwingbaarheid van EU-consumentenrecht tegenover een niet-EU retailer.",
    ],
    "IT en engineering": [
        "AVG-compliance bij verwerking van medische hartslagdata.",
        "Authenticatiestrategie voor toegang tot gezondheidsdata.",
        "Encryptie van medische data in rust en tijdens transport.",
    ],
}


def contradiction_from_complete_input(candidate: str, input_text: str) -> bool:
    """Heuristic contradiction check for negative controls.

    In these controls the candidate is treated as a false positive when the core
    concept is already explicit in the answer. This approximates the kind of
    contradiction or direct falsification signal the Gate should react to.
    """
    candidate_tokens = tokenize(candidate)
    input_tokens = tokenize(input_text)
    if not candidate_tokens:
        return False
    overlap = len(candidate_tokens & input_tokens) / len(candidate_tokens)
    return overlap >= 0.6


def trace_only_promotes(manager: SSLManager, seed_id: str) -> bool:
    seed = manager.get_seed(seed_id)
    return (
        seed.occurrence_count >= manager.config.min_occurrences_for_gate
        and seed.trace > manager.config.min_trace_for_gate
    )


def trace_without_contradiction_promotes(
    manager: SSLManager,
    seed_id: str,
    contradiction: bool,
) -> bool:
    seed = manager.get_seed(seed_id)
    return (
        seed.occurrence_count >= manager.config.min_occurrences_for_gate
        and seed.trace > manager.config.min_trace_for_gate
        and not contradiction
    )


def _normalize_adversarial_candidate(
    candidate: str | dict,
) -> tuple[str, str, bool, str | None]:
    """Normalize a candidate entry into (text, expected_label, evidence_available, candidate_type).

    Bare strings are treated as legacy negative-control lures: expected_label
    ``not_gap``, no external evidence, no candidate_type. Dict form lets the
    fixture mark a candidate as a positive control or annotate its category
    so discrimination metrics can be computed.
    """
    if isinstance(candidate, dict):
        text = str(candidate.get("text", "")).strip()
        if not text:
            raise ValueError("dict-form candidate must have a non-empty 'text' field")
        expected_label = str(candidate.get("expected_label", "not_gap"))
        if expected_label not in {"gap", "not_gap"}:
            raise ValueError(
                f"expected_label must be 'gap' or 'not_gap', got {expected_label!r}"
            )
        evidence_available = bool(candidate.get("evidence_available", False))
        candidate_type = candidate.get("candidate_type")
        return text, expected_label, evidence_available, candidate_type
    return str(candidate).strip(), "not_gap", False, None


def evaluate_adversarial_candidate(candidate: str | dict, scenario: dict) -> dict:
    text, expected_label, evidence_available, candidate_type = (
        _normalize_adversarial_candidate(candidate)
    )
    manager = SSLManager(embedding_fn=lexical_embedding)
    seed_id = None
    for _ in range(manager.config.min_occurrences_for_gate):
        seed_id = manager.add_or_update_seed(text, trigger_keywords=sorted(tokenize(text))[:5])
    assert seed_id is not None

    contradiction = contradiction_from_complete_input(text, scenario["input"])
    baseline_trace_only = trace_only_promotes(manager, seed_id)
    baseline_trace_without_contradiction = trace_without_contradiction_promotes(
        manager,
        seed_id,
        contradiction,
    )
    # Reaching PROMOTED requires (a) enough evidence calls to clear
    # min_evidence_for_gate and (b) enough successful validations to lift
    # weight to promotion_threshold. The first few Gate calls return
    # verdict="blocked" while evidence accumulates; only afterwards do
    # successful validations begin incrementing weight. The fixture therefore
    # simulates this accumulation by calling the Gate until the seed promotes
    # or a generous safety cap is reached. Negative controls (contradiction
    # or no evidence) never promote because their validation flags fail every
    # iteration.
    weight_steps_needed = max(
        1,
        math.ceil(manager.promotion_threshold / manager.validation_increment),
    )
    max_iterations = manager.config.min_evidence_for_gate + weight_steps_needed + 2
    gate_result = manager.run_validation_gate_detailed(
        seed_id,
        external_evidence=evidence_available,
        contradiction=contradiction,
    )
    if not contradiction and evidence_available and not gate_result.promoted:
        for _ in range(max_iterations - 1):
            gate_result = manager.run_validation_gate_detailed(
                seed_id,
                external_evidence=evidence_available,
                contradiction=False,
            )
            if gate_result.promoted:
                break

    return {
        "candidate": text,
        "expected_label": expected_label,
        "evidence_available": evidence_available,
        "candidate_type": candidate_type,
        "contradiction_detected": contradiction,
        "trace_only_promoted": baseline_trace_only,
        "trace_without_contradiction_promoted": baseline_trace_without_contradiction,
        "current_gate_promoted": gate_result.promoted,
        "current_gate_verdict": gate_result.verdict,
        "weight_after": gate_result.weight_after,
        "status_after": gate_result.status_after,
        "occurrence_count": gate_result.occurrence_count,
        "evidence_count": gate_result.evidence_count,
    }


def run_ssl45_false_positive_suite(input_path: str, output_path: str) -> Path:
    suite = json.loads(Path(input_path).read_text(encoding="utf-8"))
    results = []
    candidate_false_positives = 0
    promoted_false_positives = 0
    adversarial_candidate_count = 0
    baseline_trace_only_promotions = 0
    baseline_trace_without_contradiction_promotions = 0
    gate_promoted_false_positives = 0
    gate_blocked_false_positives = 0

    for scenario in suite["scenarios"]:
        strict_candidates = detect_candidate_seeds(scenario)
        candidate_count = len(strict_candidates)
        candidate_false_positives += candidate_count
        promoted_false_positives += 0

        lure_candidates = scenario.get("adversarial_candidates") or ADVERSARIAL_LURES.get(
            scenario["domain"],
            [],
        )
        adversarial_checks = [
            evaluate_adversarial_candidate(candidate, scenario)
            for candidate in lure_candidates
        ]
        adversarial_candidate_count += len(adversarial_checks)
        baseline_trace_only_promotions += sum(
            1 for row in adversarial_checks if row["trace_only_promoted"]
        )
        baseline_trace_without_contradiction_promotions += sum(
            1 for row in adversarial_checks if row["trace_without_contradiction_promoted"]
        )
        gate_promoted_false_positives += sum(
            1 for row in adversarial_checks if row["current_gate_promoted"]
        )
        gate_blocked_false_positives += sum(
            1 for row in adversarial_checks if not row["current_gate_promoted"]
        )

        results.append(
            {
                "scenario_id": scenario["id"],
                "title": scenario["title"],
                "domain": scenario["domain"],
                "candidate_false_positives": candidate_count,
                "promoted_false_positives": 0,
                "detected_candidates": strict_candidates,
                "adversarial_lure_candidates": lure_candidates,
                "adversarial_gate_checks": adversarial_checks,
                "passed": candidate_count == 0 and all(
                    not row["current_gate_promoted"] for row in adversarial_checks
                ),
            }
        )

    scenario_count = len(suite["scenarios"])
    summary = {
        "suite_version": suite.get("version"),
        "scenario_count": scenario_count,
        "candidate_false_positives": candidate_false_positives,
        "promoted_false_positives": promoted_false_positives,
        "candidate_false_positive_rate": candidate_false_positives / scenario_count,
        "promoted_false_positive_rate": promoted_false_positives / scenario_count,
        "adversarial_candidate_count": adversarial_candidate_count,
        "baseline_trace_only_promotions": baseline_trace_only_promotions,
        "baseline_trace_without_contradiction_promotions": baseline_trace_without_contradiction_promotions,
        "gate_promoted_false_positives": gate_promoted_false_positives,
        "gate_blocked_false_positives": gate_blocked_false_positives,
        "gate_block_rate_on_adversarial_candidates": (
            gate_blocked_false_positives / adversarial_candidate_count
            if adversarial_candidate_count
            else 0.0
        ),
        "gate_vs_trace_only_delta": baseline_trace_only_promotions - gate_promoted_false_positives,
        "gate_vs_trace_without_contradiction_delta": (
            baseline_trace_without_contradiction_promotions - gate_promoted_false_positives
        ),
        "passed": candidate_false_positives == 0 and gate_promoted_false_positives == 0,
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
