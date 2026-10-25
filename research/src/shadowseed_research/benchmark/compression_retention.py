"""Offline, non-efficacy test of candidate retention after a supplied compression.

Uses canonical SSLManager for candidate birth, the configured embedding adapter,
and the canonical in-memory vector store for retrieval. It NEVER generates text,
compresses a conversation, calls a model, submits evidence, or grants Gate authority.

A mechanically retrieved candidate is NOT an independent discovery, an answer
improvement, or evidence that the conceptual possibility space expanded.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Callable

import numpy as np

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.manager import CandidateType, SSLManager, SeedOrigin
from shadowseed.vectorstore import create_vector_store

SCHEMA = "shadowseed-compression-retention-fixtures-v0"
OUTPUT_SCHEMA = "shadowseed-compression-retention-mechanics-v0"
ARMS = ("compressed_only", "ordinary_notes", "shadowseeds", "sham_notes", "candidate_ablation")
EmbedFn = Callable[[str], np.ndarray]


def _word_count(text: str) -> int:
    return len(text.split())


def _validate_memory_items(items: Any, *, case_id: str, arm: str, max_items: int, max_words: int) -> None:
    if not isinstance(items, list) or len(items) != max_items:
        raise ValueError(f"{case_id}/{arm}: require exactly {max_items} memory slots")
    ids: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{case_id}/{arm}: memory item must be an object")
        item_id = item.get("id")
        text = item.get("text")
        if not isinstance(item_id, str) or not item_id.strip() or item_id in ids:
            raise ValueError(f"{case_id}/{arm}: missing or duplicate item id")
        if not isinstance(text, str) or not text.strip() or _word_count(text) > max_words:
            raise ValueError(f"{case_id}/{arm}: missing or over-budget memory text")
        ids.add(item_id)


def validate_fixtures(document: dict[str, Any]) -> list[dict[str, Any]]:
    if document.get("schema") != SCHEMA:
        raise ValueError("unsupported compression-retention fixture schema")
    budget = document.get("budget")
    if not isinstance(budget, dict):
        raise ValueError("missing budget")
    max_items = budget.get("memory_slots")
    max_words = budget.get("max_words_per_slot")
    if type(max_items) is not int or not 1 <= max_items <= 8:
        raise ValueError("memory_slots must be an integer in [1, 8]")
    if type(max_words) is not int or not 3 <= max_words <= 64:
        raise ValueError("max_words_per_slot must be an integer in [3, 64]")
    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("fixture must contain cases")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen:
            raise ValueError("missing or duplicate case id")
        seen.add(case_id)
        for field in ("compressed_summary", "later_cue"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                raise ValueError(f"{case_id}: missing {field}")
        for arm in ("candidates", "ordinary_notes", "sham_notes"):
            _validate_memory_items(case.get(arm), case_id=case_id, arm=arm,
                                   max_items=max_items, max_words=max_words)
        candidate_ids = {item["id"] for item in case["candidates"]}
        expected = case.get("expected_candidate_id")
        if expected is not None and expected not in candidate_ids:
            raise ValueError(f"{case_id}: expected candidate id is not in candidates")
        for candidate in case["candidates"]:
            if not isinstance(candidate.get("origin_ref"), str) or not candidate["origin_ref"].strip():
                raise ValueError(f"{case_id}: candidates require a nonempty origin_ref")
        for note in case["ordinary_notes"]:
            match = note.get("candidate_ref")
            if match is not None and match not in candidate_ids:
                raise ValueError(f"{case_id}: unknown ordinary-note candidate_ref")
        for note in case["sham_notes"]:
            if note.get("candidate_ref") is not None:
                raise ValueError(f"{case_id}: sham notes cannot carry positive candidate labels")
    return cases


def _search(items: list[dict[str, Any]], embed: EmbedFn,
            cue: str, threshold: float, top_k: int) -> list[dict[str, Any]]:
    """Run the same vector retrieval for notes, sham notes, and seeds."""
    store = create_vector_store(backend="memory")
    for item in items:
        store.add(item["id"], embed(item["text"]), {
            "candidate_ref": item.get("candidate_ref"),
            "text": item["text"],
        })
    hits = store.search(embed(cue), top_k=top_k)
    return [
        {
            "id": item_id,
            "score": round(float(score), 7),
            "candidate_ref": metadata.get("candidate_ref"),
            "text": metadata["text"],
        }
        for item_id, score, metadata in hits
        if math.isfinite(float(score)) and float(score) >= threshold
    ]


def _is_hit(hits: list[dict[str, Any]], expected_id: str | None) -> bool | None:
    if expected_id is None:
        return None
    return any(hit["candidate_ref"] == expected_id for hit in hits)


def run_case(case: dict[str, Any], embed: EmbedFn, *, threshold: float = 0.35,
             top_k: int = 1, max_items: int = 2) -> dict[str, Any]:
    """Return mechanical observations; never use the answer key for selection."""
    if not -1.0 <= threshold <= 1.0 or not math.isfinite(threshold):
        raise ValueError("threshold must be finite in [-1, 1]")
    if type(top_k) is not int or not 1 <= top_k <= max_items:
        raise ValueError("top_k must be between 1 and memory_slots")

    # Canonical product candidate birth; this manager is disposable research state.
    manager = SSLManager(embedding_fn=embed)
    candidates = []
    for authored in case["candidates"]:
        seed_id = manager.add_or_update_seed(
            authored["text"],
            deduplicate=False,
            origin=SeedOrigin(
                candidate_type=CandidateType.ALTERNATIVE_HYPOTHESIS,
                detection_basis="investigator_authored_offline_fixture",
                context_ref=authored["origin_ref"],
            ),
        )
        seed = manager.get_seed(seed_id)
        if seed.weight != 0.0 or seed.evidence_count != 0:
            raise AssertionError("research candidate unexpectedly acquired authority")
        candidates.append({
            "id": seed_id,
            "text": seed.text,
            "candidate_ref": authored["id"],
        })
    if manager.gate_events:
        raise AssertionError("offline retention test must never invoke the Gate")

    expected = case.get("expected_candidate_id")
    # The one-candidate ablation is frozen from fixture metadata solely for
    # diagnostic mechanics. It is NOT a blind causal effect estimate.
    ablated = [dict(item) for item in candidates]
    if expected is not None:
        target = next(item for item in ablated if item["candidate_ref"] == expected)
        target["text"] = case.get(
            "neutral_replacement",
            "Review the formatting and administrative record before filing.",
        )
        target["candidate_ref"] = None

    observations: dict[str, Any] = {
        "compressed_only": {
            "context": case["compressed_summary"],
            "retrieval": [],
            "model_response": None,
            "not_evaluated": "no model or source summarizer was invoked",
        }
    }
    for arm, items in (
        ("ordinary_notes", case["ordinary_notes"]),
        ("shadowseeds", candidates),
        ("sham_notes", case["sham_notes"]),
        ("candidate_ablation", ablated),
    ):
        hits = _search(items, embed, case["later_cue"], threshold, top_k)
        observations[arm] = {
            "retrieval": hits,
            "hit_authored_target": _is_hit(hits, expected),
            "irrelevant_retrieval_on_negative": expected is None and bool(hits),
            "memory_slots": len(items),
            "memory_words": sum(_word_count(item["text"]) for item in items),
        }
    return {
        "id": case["id"],
        "later_cue": case["later_cue"],
        "authored_expected_candidate_id": expected,
        "status": "fixture_mechanics_only",
        "candidate_count": len(candidates),
        "weightless": all(
            seed.weight == 0.0 and seed.evidence_count == 0
            for seed in manager.seeds.values()
        ),
        "gate_events": len(manager.gate_events),
        "arms": observations,
    }


def run_fixtures(document: dict[str, Any], *, embed: EmbedFn,
                 embedding_description: str = "injected", top_k: int = 1,
                 threshold: float = 0.35) -> dict[str, Any]:
    cases = validate_fixtures(document)
    if not isinstance(embedding_description, str) or not embedding_description:
        raise ValueError("embedding description required")
    max_items = document["budget"]["memory_slots"]
    return {
        "schema": OUTPUT_SCHEMA,
        "status": "offline_plumbing_only_not_efficacy",
        "research_question": "candidate retention under a supplied compression boundary",
        "not_tested": [
            "actual model selection or non-selection",
            "model-generated candidates",
            "actual context compression quality",
            "anchoring, downstream answer quality, and new investigable questions",
            "Q1/Q2 causal efficacy or external validation",
        ],
        "model_calls": 0,
        "authority_changes": 0,
        "embedding": embedding_description,
        "memory_budget": document["budget"],
        "retrieval_top_k": top_k,
        "retrieval_threshold": threshold,
        "authored_case_count": len(cases),
        "results": [
            run_case(case, embed, threshold=threshold,
                     top_k=top_k, max_items=max_items)
            for case in cases
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline SSL compression-retention mechanics; not an efficacy test"
    )
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--embedding-backend", choices=["lexical", "sentence-transformers",
                                                         "ollama", "openai"], default="lexical")
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--top-k", type=int, default=1)
    args = parser.parse_args()
    if args.embedding_backend != "lexical":
        raise SystemExit(
            "offline harness only: use lexical; inject a preauthorized embedder "
            "programmatically for a separate controlled study"
        )
    raw = args.fixtures.read_bytes()
    document = json.loads(raw)
    embed, dimension = make_embedding_fn("lexical")
    result = run_fixtures(
        document, embed=embed,
        embedding_description=f"lexical-fixture-{dimension}d",
        threshold=args.threshold, top_k=args.top_k,
    )
    result["fixture_sha256"] = hashlib.sha256(raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"], "cases": len(result["results"]),
        "model_calls": result["model_calls"], "output": str(args.output)
    }))


if __name__ == "__main__":
    main()
