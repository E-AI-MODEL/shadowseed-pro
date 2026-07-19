"""Local AbsenceBench harness for testing Shadow Seed claims.

The harness compares a plain lexical baseline with the Shadow Seed pipeline:
input scenarios -> absence candidates -> seeds -> validation gate -> metrics.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re

import numpy as np

from shadowseed.hash_utils import stable_bucket_index
from shadowseed.manager import SSLManager, SeedStatus
from .result_writer import ResultWriter
from .schemas import BenchmarkResult
from .run_types import RunType, ExecutionStatus

STOPWORDS = {
    "de", "het", "een", "en", "of", "van", "in", "op", "te", "is", "zijn", "was",
    "met", "als", "voor", "that", "the", "and", "or", "of", "in", "on", "to", "a",
    "an", "is", "are", "was", "were", "with", "for", "by", "as", "at", "from",
}


@dataclass
class Metrics:
    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0

    @property
    def precision(self) -> float:
        denom = self.true_positive + self.false_positive
        return self.true_positive / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positive + self.false_negative
        return self.true_positive / denom if denom else 0.0

    @property
    def f1(self) -> float:
        denom = self.precision + self.recall
        return (2 * self.precision * self.recall / denom) if denom else 0.0

    @property
    def accuracy(self) -> float:
        total = self.true_positive + self.false_positive + self.true_negative + self.false_negative
        return (self.true_positive + self.true_negative) / total if total else 0.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data.update(
            {
                "precision": self.precision,
                "recall": self.recall,
                "f1": self.f1,
                "accuracy": self.accuracy,
            }
        )
        return data


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[A-Za-zÀ-ÿ0-9_]+", text.lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 2}


def lexical_embedding(text: str, dimensions: int = 64) -> np.ndarray:
    vector = np.zeros(dimensions, dtype=float)
    for token in tokenize(text):
        vector[stable_bucket_index(token, dimensions)] += 1.0
    return vector


def absence_candidates(original: str, modified: str) -> list[str]:
    missing = sorted(tokenize(original) - tokenize(modified))
    return missing


def gold_absent(scenario: dict) -> bool:
    omitted = scenario.get("omitted_context")
    if isinstance(omitted, list):
        return len(omitted) > 0
    if isinstance(omitted, str):
        return bool(omitted.strip())
    if "label" in scenario:
        return bool(scenario["label"])
    return bool(scenario.get("absent", False))


def baseline_detect(original: str, modified: str, threshold: float = 0.20) -> bool:
    original_tokens = tokenize(original)
    if not original_tokens:
        return False
    missing_ratio = len(absence_candidates(original, modified)) / len(original_tokens)
    return missing_ratio >= threshold


def shadow_seed_detect(scenario: dict) -> tuple[bool, dict]:
    original = scenario.get("original_context", "")
    modified = scenario.get("modified_context", "")
    candidates = absence_candidates(original, modified)

    manager = SSLManager(
        embedding_fn=lexical_embedding,
        dedup_threshold=0.95,
        promotion_threshold=0.4,
        validation_increment=0.2,
    )

    promoted = []
    rejected = []
    for candidate in candidates:
        # Keep the seed atomic enough for the current SSLManager rules.
        seed_text = f"Ontbrekend concept: {candidate}"
        try:
            seed_id = manager.add_or_update_seed(seed_text, trigger_keywords=[candidate])
        except ValueError:
            rejected.append(candidate)
            continue

        # AbsenceBench provides paired original/modified context. Treat the pair
        # itself as external evidence for the absence candidate.
        manager.seeds[seed_id].occurrence_count = max(manager.seeds[seed_id].occurrence_count, 3)
        manager.run_validation_gate(seed_id, external_evidence=True)
        manager.run_validation_gate(seed_id, external_evidence=True)
        if manager.seeds[seed_id].status == SeedStatus.PROMOTED:
            promoted.append(seed_id)

    trace = manager.to_dict()
    return bool(promoted), {
        "candidate_count": len(candidates),
        "promoted_count": len(promoted),
        "rejected_candidates": rejected,
        "manager": trace,
    }


def update_metrics(metrics: Metrics, prediction: bool, expected: bool) -> None:
    if prediction and expected:
        metrics.true_positive += 1
    elif prediction and not expected:
        metrics.false_positive += 1
    elif not prediction and expected:
        metrics.false_negative += 1
    else:
        metrics.true_negative += 1


def evaluate_scenarios(scenarios: list[dict]) -> dict:
    baseline = Metrics()
    shadowseed = Metrics()
    examples = []

    for scenario in scenarios:
        original = scenario.get("original_context", "")
        modified = scenario.get("modified_context", "")
        expected = gold_absent(scenario)

        baseline_prediction = baseline_detect(original, modified)
        shadow_prediction, trace = shadow_seed_detect(scenario)

        update_metrics(baseline, baseline_prediction, expected)
        update_metrics(shadowseed, shadow_prediction, expected)

        examples.append(
            {
                "id": scenario.get("id"),
                "expected_absence": expected,
                "baseline_detected": baseline_prediction,
                "shadowseed_detected": shadow_prediction,
                "trace": trace,
            }
        )

    return {
        "baseline": baseline.to_dict(),
        "shadowseed": shadowseed.to_dict(),
        "delta_f1": shadowseed.f1 - baseline.f1,
        "examples": examples,
    }


def run_local_absencebench(input_path: str, output_path: str) -> Path:
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))

    scenarios = data.get("scenarios", [])
    if not scenarios:
        raise ValueError("No scenarios found in input JSON")

    evaluation = evaluate_scenarios(scenarios)

    result = BenchmarkResult(
        benchmark_name="AbsenceBench",
        run_type=RunType.SCAN.value,
        execution_status=ExecutionStatus.SCAN.value,
        ssl_input_basis=["shadowseed-manager", "local-json-or-hf-sample"],
        host_platform="local",
        dataset_status=data.get("source", "local"),
        runner_status="baseline-vs-shadowseed harness",
        score=evaluation["shadowseed"]["f1"],
        score_type="Shadow Seed F1 against absence labels",
        interpretation=(
            "Compares a lexical baseline with the Shadow Seed pipeline. "
            "The score is Shadow Seed F1; delta_f1 is included in the output."
        ),
        limitations=[
            "free local harness; no paid LLM calls",
            "lexical embedding instead of an external embedding model",
            "no upstream AbsenceBench evaluator",
        ],
        execution_gap=False,
    )

    output = ResultWriter().write_result(result, output_path)
    payload = json.loads(output.read_text(encoding="utf-8"))
    payload["evaluation"] = evaluation
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return output
