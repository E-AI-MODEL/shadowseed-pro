"""Measure recurrence recognition on recorded detector candidates.

Replays recorded candidates through the product's ``RecurrenceClusterer`` with
the product embedding backend, for a range of cluster thresholds, without new
model calls. Per conversation it reports how many clusters were observed in two
or more distinct turns (recurrence) and how many in three or more (the default
``min_occurrences_for_gate``). It also writes a stratified sample of cross-turn
candidate pairs for human "same gap?" labelling, so a threshold can be chosen
from labelled data instead of guessed.

Usage:
    python scripts/recurrence_calibration.py \\
        --input benchmarks/seed_calibration/fixed22_candidates.json \\
        --embedding-backend sentence-transformers --embedding-model <path> \\
        --embedding-revision <sha> --output-dir benchmarks/seed_calibration/results
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import numpy as np

from shadowseed.adapters.embedding import make_embedding_fn
from shadowseed.intake import is_atomic_seed
from shadowseed.recurrence_clustering import DEFAULT_CLUSTER_THRESHOLD, RecurrenceClusterer

THRESHOLDS = (0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85)
SIMILARITY_BINS = ((0.0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 1.01))
PAIRS_PER_BIN = 12


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def _conversations(data: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten arms into conversations of admitted candidates per turn."""

    flat = []
    for arm in data["arms"]:
        for conversation in arm["conversations"]:
            turns = []
            for turn in conversation["turns"]:
                admitted = [c["text"] for c in turn["candidates"] if is_atomic_seed(c["text"])]
                turns.append({"turn": turn["turn"], "question": turn["question"], "candidates": admitted})
            flat.append(
                {
                    "id": f"{arm['model']}/{conversation['conversation_id']}",
                    "model": arm["model"],
                    "turns": turns,
                }
            )
    return flat


def _replay(conversation: dict[str, Any], embed, threshold: float) -> dict[str, Any]:
    clusterer = RecurrenceClusterer(threshold=threshold)
    for turn in conversation["turns"]:
        for text in turn["candidates"]:
            clusterer.add(text, embed(text), observation_ref=f"turn:{turn['turn']}")
    counts = [clusterer.recurrence(i) for i in range(len(clusterer.centroids))]
    largest = max((len(members) for members in clusterer.members), default=0)
    return {
        "clusters": len(counts),
        "recurring_2plus": sum(count >= 2 for count in counts),
        "recurring_3plus": sum(count >= 3 for count in counts),
        "largest_cluster_members": largest,
    }


def _pair_sample(conversations: list[dict[str, Any]], embed, seed: int) -> list[dict[str, Any]]:
    pairs_by_bin: dict[int, list[dict[str, Any]]] = {i: [] for i in range(len(SIMILARITY_BINS))}
    for conversation in conversations:
        items = [
            (turn["turn"], text) for turn in conversation["turns"] for text in turn["candidates"]
        ]
        for i, (turn_a, text_a) in enumerate(items):
            for turn_b, text_b in items[i + 1 :]:
                if turn_a == turn_b:
                    continue
                similarity = _cosine(embed(text_a), embed(text_b))
                for index, (low, high) in enumerate(SIMILARITY_BINS):
                    if low <= similarity < high:
                        pairs_by_bin[index].append(
                            {
                                "conversation": conversation["id"],
                                "turn_a": turn_a,
                                "turn_b": turn_b,
                                "text_a": text_a,
                                "text_b": text_b,
                                "similarity": round(similarity, 4),
                            }
                        )
                        break
    rng = random.Random(seed)
    sample = []
    for index, pairs in pairs_by_bin.items():
        rng.shuffle(pairs)
        sample.extend(pairs[:PAIRS_PER_BIN])
    for pair in sample:
        pair["pair_id"] = hashlib.sha256(
            f"{pair['conversation']}|{pair['text_a']}|{pair['text_b']}".encode("utf-8")
        ).hexdigest()[:16]
    rng.shuffle(sample)
    return sample


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--embedding-backend", default="lexical")
    parser.add_argument("--embedding-model", default=None)
    parser.add_argument("--embedding-revision", default=None)
    parser.add_argument("--seed", type=int, default=20261023)
    args = parser.parse_args(argv)

    data = json.loads(args.input.read_text(encoding="utf-8"))
    conversations = _conversations(data)
    embed_fn, _dimensions = make_embedding_fn(
        args.embedding_backend, args.embedding_model, revision=args.embedding_revision
    )
    cache: dict[str, np.ndarray] = {}

    def embed(text: str) -> np.ndarray:
        if text not in cache:
            cache[text] = np.asarray(embed_fn(text), dtype=float)
        return cache[text]

    sweep = []
    for threshold in THRESHOLDS:
        per_conversation = {c["id"]: _replay(c, embed, threshold) for c in conversations}
        sweep.append(
            {
                "threshold": threshold,
                "is_product_default": threshold == DEFAULT_CLUSTER_THRESHOLD,
                "totals": {
                    key: sum(result[key] for result in per_conversation.values())
                    for key in ("clusters", "recurring_2plus", "recurring_3plus")
                },
                "per_conversation": per_conversation,
            }
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": "ssl-recurrence-calibration-v1",
        "input": str(args.input),
        "input_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "embedding": {
            "backend": args.embedding_backend,
            "model": args.embedding_model,
            "revision": args.embedding_revision,
        },
        "admitted_candidates": sum(len(t["candidates"]) for c in conversations for t in c["turns"]),
        "conversations": len(conversations),
        "sweep": sweep,
    }
    (args.output_dir / "recurrence_sweep.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    pairs = _pair_sample(conversations, embed, args.seed)
    (args.output_dir / "pair_sample.json").write_text(
        json.dumps({"schema": "ssl-recurrence-pair-sample-v1", "pairs": pairs}, indent=2) + "\n",
        encoding="utf-8",
    )
    for row in sweep:
        marker = " (default)" if row["is_product_default"] else ""
        print(f"threshold {row['threshold']:.2f}{marker}: {row['totals']}")
    print(f"pairs sampled: {len(pairs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
