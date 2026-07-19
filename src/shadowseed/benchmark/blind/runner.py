"""Runner for the Shadow Seed blind benchmark."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from shadowseed.benchmark.blind.detector import detect_blind_candidates, tokenize
from shadowseed.benchmark.blind.loader import load_hidden_labels, load_public_suite
from shadowseed.benchmark.blind.schemas import BlindScenarioResult
from shadowseed.benchmark.blind.scorer import score_blind_result
from shadowseed.hash_utils import stable_bucket_index
from shadowseed.manager import SSLManager, SeedStatus


def lexical_embedding(text: str, dimensions: int = 128) -> np.ndarray:
    """Deterministic no-download embedding for CI-safe blind benchmark runs."""
    vector = np.zeros(dimensions, dtype=float)
    for token in tokenize(text):
        vector[stable_bucket_index(token, dimensions)] += 1.0
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm


def promoted_or_active_seed_texts(manager: SSLManager) -> list[str]:
    """Return candidate texts that survived repeated detection.

    This benchmark keeps labels out of the promotion step. A blind run may use
    active repeated candidates for scoring; true promotion still requires real
    external evidence in production use.
    """
    accepted_statuses = {SeedStatus.ACTIVE, SeedStatus.PROMOTED}
    return [
        seed.text
        for seed in manager.seeds.values()
        if seed.status in accepted_statuses and seed.occurrence_count >= 2
    ]


def run_blind_benchmark(
    input_path: str,
    labels_path: str,
    output_path: str,
    turns: int = 3,
    max_seeds: int = 5,
) -> Path:
    """Run the blind benchmark.

    Public scenario text is loaded before private labels. Labels are used only
    inside the final scoring phase.
    """
    public_version, scenarios = load_public_suite(input_path)
    labels_version, label_by_id = load_hidden_labels(labels_path)
    results: list[BlindScenarioResult] = []

    for scenario in scenarios:
        if scenario.id not in label_by_id:
            raise ValueError(f"Missing hidden label for scenario {scenario.id}.")

        manager = SSLManager(
            embedding_fn=lexical_embedding,
            dedup_threshold=0.85,
            promotion_threshold=0.5,
            validation_increment=0.2,
        )
        text_for_detection = scenario.baseline_answer or scenario.input
        detected_by_turn: list[list[str]] = []

        for _turn in range(turns):
            candidates = detect_blind_candidates(
                scenario.domain,
                text_for_detection,
                max_seeds=max_seeds,
            )
            detected_by_turn.append(candidates)
            for candidate in candidates:
                try:
                    manager.add_or_update_seed(
                        candidate,
                        trigger_keywords=sorted(tokenize(candidate))[:5],
                    )
                except ValueError:
                    continue

        baseline_candidates: list[str] = []
        ssl_candidates = promoted_or_active_seed_texts(manager)
        score = score_blind_result(
            baseline_candidates=baseline_candidates,
            ssl_candidates=ssl_candidates,
            label=label_by_id[scenario.id],
        )

        promoted_seed_count = sum(
            1 for seed in manager.seeds.values() if seed.status == SeedStatus.PROMOTED
        )
        results.append(
            BlindScenarioResult(
                scenario_id=scenario.id,
                domain=scenario.domain,
                detected_by_turn=detected_by_turn,
                candidate_seed_count=len(manager.seeds),
                promoted_seed_count=promoted_seed_count,
                score=score,
                ssl_state=manager.to_dict(),
            )
        )

    summary = {
        "public_suite_version": public_version,
        "labels_version": labels_version,
        "scenario_count": len(results),
        "mean_baseline_gap_coverage": _mean(
            item.score.baseline_gap_coverage for item in results
        ),
        "mean_ssl_gap_coverage": _mean(item.score.ssl_gap_coverage for item in results),
        "mean_coverage_delta": _mean(item.score.coverage_delta for item in results),
        "total_unsupported_additions": sum(
            item.score.unsupported_additions for item in results
        ),
        "total_false_positive_count": sum(
            item.score.false_positive_count for item in results
        ),
        "mean_net_benefit": _mean(item.score.net_benefit for item in results),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "summary": summary,
                "results": [item.to_dict() for item in results],
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def _mean(values) -> float:
    materialized = list(values)
    if not materialized:
        return 0.0
    return sum(materialized) / len(materialized)
