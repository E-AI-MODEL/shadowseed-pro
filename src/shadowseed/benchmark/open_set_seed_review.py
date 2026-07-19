"""Open-set seed quality review scaffold for SSL 4.5.

This route prepares candidate seeds for human review on unknown inputs. It does
not use the fixed regression-suite detector, fixed scenario priors, expected gaps
or ground-truth seeds. Candidate text is passed through SSLManager so existing
normalization, atomicity checks, deduplication and zero-weight seed storage stay
in force.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

import numpy as np

from shadowseed.benchmark.evidence_layers import (
    OPEN_SET_SEED_QUALITY,
    assert_valid_layer,
)
from shadowseed.benchmark.open_set_candidate_adapter import (
    OPEN_SET_CANDIDATE_ADAPTER_ID,
    SUPPORTED_DETECTORS,
    raw_open_set_candidates,
)
from shadowseed.hash_utils import stable_bucket_index
from shadowseed.manager import SSLManager


REVIEW_CRITERIA = [
    "atomicity",
    "relevance",
    "testability",
    "non_triviality",
    "follow_up_utility",
]
REJECT_CODES = [
    "too_broad",
    "too_vague",
    "trivial",
    "not_relevant",
    "not_testable",
    "duplicate",
    "style_not_gap",
]
DEFAULT_REVIEWER_IDS = ["reviewer_a", "reviewer_b"]
EVIDENCE_LAYER = assert_valid_layer(OPEN_SET_SEED_QUALITY)
ARTIFACT_CONTRACT_VERSION = "open-review-0.2"


def _normalize_reviewer_ids(reviewer_ids: list[str] | tuple[str, ...] | None) -> list[str]:
    ids = reviewer_ids or DEFAULT_REVIEWER_IDS
    normalized: list[str] = []
    seen: set[str] = set()
    for reviewer_id in ids:
        clean = str(reviewer_id).strip()
        if clean and clean not in seen:
            normalized.append(clean)
            seen.add(clean)
    if not normalized:
        raise ValueError("At least one reviewer id is required for open-set review packets.")
    return normalized


def _item_excerpt(item: dict[str, Any]) -> str:
    excerpt = (item.get("text") or item.get("input") or "").strip()
    excerpt = excerpt[:400] + ("..." if len(excerpt) > 400 else "")
    return excerpt


def _review_entry(
    item: dict[str, Any],
    seed_row: dict[str, Any],
    reviewer_id: str,
    reviewer_slot: int,
) -> dict[str, Any]:
    return {
        "item_id": item.get("id"),
        "title": item.get("title"),
        "domain": item.get("domain"),
        "source_excerpt": _item_excerpt(item),
        "seed_id": seed_row.get("seed_id"),
        "seed_text": seed_row.get("text"),
        "reviewer_id": reviewer_id,
        "reviewer_slot": reviewer_slot,
        "review_fields": {criterion: None for criterion in REVIEW_CRITERIA},
        "review_status": "pending",
        "reject_reason": None,
        "reviewer_notes": "",
    }


def _open_set_contract_metadata() -> dict[str, Any]:
    return {
        "candidate_adapter": OPEN_SET_CANDIDATE_ADAPTER_ID,
        "fixed_scenario_priors_used": False,
        "expected_gaps_used": False,
        "ground_truth_seeds_used": False,
        "regression_gap_detector_used": False,
        "candidate_quality_requires_human_review": True,
        "seed_verdict_rule": (
            "A seed counts as accepted or rejected only after every generated "
            "reviewer row for that seed is completed and valid."
        ),
    }


def run_open_set_seed_review(
    input_path: str,
    output_path: str,
    review_packet_path: str | None = None,
    reviewer_ids: list[str] | tuple[str, ...] | None = None,
    detector: str = "adapter_v1",
    model_backend: str = "fixture",
    model_id: str | None = None,
    max_new_tokens: int = 400,
    prompt_variant: str = "absence",
) -> Path:
    if detector not in SUPPORTED_DETECTORS:
        raise ValueError(
            f"Unknown detector {detector!r}. Allowed: {SUPPORTED_DETECTORS}."
        )

    model_backend_obj: Any = None
    model_backend_name: str | None = None
    if detector == "model":
        from shadowseed.detection.model_detector import make_detector_backend

        model_backend_obj = make_detector_backend(
            backend=model_backend,
            model_id=model_id,
            max_new_tokens=max_new_tokens,
            prompt_variant=prompt_variant,
        )
        model_backend_name = model_backend_obj.name

    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    items = payload.get("items", [])
    source_metadata = payload.get("source", {})
    reviewer_ids_normalized = _normalize_reviewer_ids(reviewer_ids)
    results = []
    review_packets = []
    raw_candidate_count = 0
    normalized_candidate_count = 0
    accepted_count = 0
    rejected_count = 0
    domain_accept_counts: dict[str, int] = {}
    domain_item_counts: dict[str, int] = {}
    candidate_source_counts: dict[str, int] = {}

    for item in items:
        manager = SSLManager(embedding_fn=detect_embedding)
        raw_candidates, candidate_source = raw_open_set_candidates(
            item, detector=detector, model_backend=model_backend_obj
        )
        candidate_source_counts[candidate_source] = candidate_source_counts.get(candidate_source, 0) + 1
        # A real taalmodel emits one whole-sentence gap per line. For that
        # path: keep each line intact (no comma/"en" splitting that shreds
        # sentences into fragments), do not auto-"ontbreekt"-expand, do not
        # collapse near-paraphrases via the lexical dedup embedding (let the
        # human "duplicate" reject code decide), and drop sub-4-word stubs.
        is_model = detector == "model"
        ingest = manager.ingest_detection_candidates(
            raw_candidates,
            expand_short_fragments=not is_model,
            split_broad=not is_model,
            deduplicate=not is_model,
            min_seed_words=4 if is_model else 0,
        )
        raw_candidate_count += ingest["input_count"]
        normalized_candidate_count += len(ingest["normalized_candidates"])
        accepted_count += len(ingest["accepted"])
        rejected_count += len(ingest["rejected"])
        domain = item.get("domain", "unknown")
        domain_item_counts[domain] = domain_item_counts.get(domain, 0) + 1
        domain_accept_counts[domain] = domain_accept_counts.get(domain, 0) + len(ingest["accepted"])

        for accepted in ingest["accepted"]:
            for reviewer_slot, reviewer_id in enumerate(reviewer_ids_normalized, start=1):
                review_packets.append(_review_entry(item, accepted, reviewer_id, reviewer_slot))

        results.append(
            {
                "item_id": item.get("id"),
                "title": item.get("title"),
                "domain": domain,
                "candidate_source": candidate_source,
                "raw_candidates": raw_candidates,
                "normalized_candidates": ingest["normalized_candidates"],
                "accepted": ingest["accepted"],
                "rejected": ingest["rejected"],
            }
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    review_packet_file = Path(review_packet_path) if review_packet_path else output.with_name(output.stem + "_review_packets.json")
    review_packet_file.parent.mkdir(parents=True, exist_ok=True)
    contract = _open_set_contract_metadata()

    summary = {
        "evidence_layer": EVIDENCE_LAYER,
        "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
        "corpus_version": payload.get("version"),
        "source": source_metadata,
        "item_count": len(items),
        "raw_candidate_count": raw_candidate_count,
        "normalized_candidate_count": normalized_candidate_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "acceptance_rate": (accepted_count / normalized_candidate_count) if normalized_candidate_count else 0.0,
        "domain_item_counts": domain_item_counts,
        "domain_accept_counts": domain_accept_counts,
        "candidate_source_counts": candidate_source_counts,
        "detector": detector,
        "model_backend": model_backend_name,
        "prompt_variant": prompt_variant if detector == "model" else None,
        **contract,
        "reviewer_ids": reviewer_ids_normalized,
        "reviewer_count": len(reviewer_ids_normalized),
        "review_packet_count": len(review_packets),
        "review_criteria": REVIEW_CRITERIA,
        "reject_codes": REJECT_CODES,
        "status": "review_pending",
        "next_step": "Fill review packets and run summarize-open-set-seed-review.",
        "artifacts": {
            "seed_output": str(output),
            "review_packets": str(review_packet_file),
        },
    }

    output.write_text(json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    review_packet_file.write_text(
        json.dumps(
            {
                "summary": {
                    "evidence_layer": EVIDENCE_LAYER,
                    "artifact_contract_version": ARTIFACT_CONTRACT_VERSION,
                    "corpus_version": payload.get("version"),
                    "source": source_metadata,
                    "item_count": len(items),
                    "seed_count": accepted_count,
                    "reviewer_ids": reviewer_ids_normalized,
                    "reviewer_count": len(reviewer_ids_normalized),
                    "packet_count": len(review_packets),
                    "criteria": REVIEW_CRITERIA,
                    "reject_codes": REJECT_CODES,
                    "candidate_source_counts": candidate_source_counts,
                    **contract,
                    "instructions": (
                        "One packet row is generated per reviewer per seed. "
                        "Do not edit a single row sequentially for multiple reviewers. "
                        "A seed only counts as accepted or rejected after every generated "
                        "reviewer row is completed and valid. Score each seed on atomicity, "
                        "relevance, testability, non-triviality and follow-up utility."
                    ),
                    "status": "review_pending",
                    "expected_summary_artifacts": [
                        "open_set_seed_review_summary.json",
                        "open_set_disagreements.json",
                        "open_set_review_report.md",
                    ],
                },
                "packets": review_packets,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return output


def detect_embedding(text: str) -> np.ndarray:
    """Cheap deterministic lexical embedding for review scaffolding."""
    dims = 128
    vector = np.zeros(dims, dtype=float)
    for token in re.findall(r"\w+", text.lower(), flags=re.UNICODE):
        vector[stable_bucket_index(token, dims)] += 1.0
    norm = np.linalg.norm(vector)
    if norm == 0:
        return vector
    return vector / norm
