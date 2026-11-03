"""Full MIT chronological recurrence replay with the real ShadowseedEngine.

This measures whether semantic memory detects recurrence beyond a literal-notes
baseline. It does not modify MIT weights, discover new hypotheses, or prove
value relative to an equally equipped LLM with its own semantic note retrieval.

All 85 source statements are extracted exactly as written, with 158-turn
chronology and a pinned MIT Git blob. The model does not paraphrase the input.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer
from sentence_transformers import SentenceTransformer
from huggingface_hub import model_info
from shadowseed import ShadowseedEngine
from research.experiments.mit_shadow_memory_20261103.run_replay_v2 import parse_turns, INPUT, EMBED_ID

OUT = Path("mit-85-recurrence-output")
OUT.mkdir(exist_ok=True)
MIT_BLOB_SHA = "caa2d040547e81677f98cccb1854769b1057f3b7"
HYPOTHESIS = re.compile(r"(?m)^\s*#\s*Hypothesis:\s*(.+)$")


def extract_hypotheses(reply: str) -> list[str]:
    return [m.group(1).strip() for m in HYPOTHESIS.finditer(reply)]


def normalized_literal(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold().strip(" .;")


def source_records(turns: list[tuple[int, str]]) -> list[dict]:
    return [
        {"mit_turn": n, "text": hypothesis}
        for n, reply in turns
        for hypothesis in extract_hypotheses(reply)
    ]


class ExactSourceNoteDetector:
    """Non-generative, identity-preserving source adapter."""
    name = "mit-exact-observation"
    prompt_variant = "mit_explicit_hypothesis"

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        return extract_hypotheses(str(item.get("text") or ""))[:max_seeds]


def write_json(name: str, obj) -> None:
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def verify_replay_source(text: str) -> list[tuple[int, str]]:
    turns = parse_turns(text)
    records = source_records(turns)
    if len(turns) != 158 or len(records) != 85:
        raise ValueError("Pinned MIT trajectory differs from 158-turn / 85-note source")
    if len({row["mit_turn"] for row in records}) != 85:
        raise ValueError("Unexpected multiple notes per MIT turn")
    return turns


def recurrent_cluster_ids(clusterer) -> list[int]:
    """Include idempotently re-observed seeds even with a single stored member."""
    return [
        i for i in range(len(clusterer.members))
        if clusterer.recurrence(i) >= 2
    ]


def build_lexical_baseline(records: list[dict]) -> list[dict]:
    """No future-dependent fit: hashing vocabulary and weights are stateless."""
    vectorizer = HashingVectorizer(
        analyzer="word", ngram_range=(1, 2), norm="l2",
        alternate_sign=False, n_features=2**17,
    )
    rows = [rec["text"] for rec in records]
    vectors = vectorizer.transform(rows)
    seen = {}
    matches = []
    for index, row in enumerate(records):
        literal = normalized_literal(row["text"])
        earlier = seen.get(literal)
        if earlier is not None:
            matches.append({
                "mit_turn": row["mit_turn"], "earlier_turn": earlier,
                "kind": "exact", "score": 1.0,
            })
        if literal not in seen:
            seen[literal] = row["mit_turn"]
        if index:
            scores = (vectors[:index] @ vectors[index].T).toarray().ravel()
            best_idx = int(np.argmax(scores))
            best_score = float(scores[best_idx])
            if best_score >= 0.6:
                matches.append({
                    "mit_turn": row["mit_turn"],
                    "earlier_turn": records[best_idx]["mit_turn"],
                    "kind": "hashing_ngram_0.6", "score": round(best_score, 4),
                })
    return matches


def run() -> None:
    text = INPUT.read_text(encoding="utf-8")
    turns = verify_replay_source(text)
    records = source_records(turns)
    model = SentenceTransformer(EMBED_ID, device="cpu")
    embeddings = model.encode(
        [row["text"] for row in records],
        normalize_embeddings=True,
        convert_to_numpy=True, batch_size=32,
    )
    embedding_cache = {
        row["text"]: np.asarray(vec, dtype=float)
        for row, vec in zip(records, embeddings)
    }

    @lru_cache(maxsize=1024)
    def embed(value: str) -> np.ndarray:
        value = str(value)
        if value in embedding_cache:
            return embedding_cache[value]
        return np.asarray(model.encode(value, normalize_embeddings=True), dtype=float)

    engine = ShadowseedEngine(
        embedding_fn=embed,
        detector_backend=ExactSourceNoteDetector(),
        recurrence_mode="cluster",
        cluster_threshold=0.6,
        gate_policy_id="evidence_backed",
        max_seeds_per_turn=2,
    )
    semantic_nearest_prior = []
    for i, row in enumerate(records):
        if not i:
            continue
        scores = embeddings[:i] @ embeddings[i]
        nearest_idx = int(np.argmax(scores))
        semantic_nearest_prior.append({
            "mit_turn": row["mit_turn"],
            "earlier_turn": records[nearest_idx]["mit_turn"],
            "semantic_cosine": round(float(scores[nearest_idx]), 4),
        })

    start = time.monotonic()
    turn_audit = []
    for n, reply in turns:
        # Only the verbatim hypothesis marker is transmitted to the engine.
        # This removes JSON/tool commands and prevents prompt/model invention.
        note_text = "\n".join(
            "# Hypothesis: " + note for note in extract_hypotheses(reply)
        )
        prepared = engine.prepare_turn("Read the documented hypothesis for this MIT research turn.")
        report = engine.observe_turn(prepared, note_text)
        turn_audit.append({
            "mit_turn": n,
            "source_notes": extract_hypotheses(reply),
            "engine_detected": report.get("detected_candidates", []),
            "seed_ids_born": report.get("seeds_born_weightless", []),
            "surfaced_seed_ids": report.get("surfaced_seed_ids", []),
            "engine_turn": engine.turn,
        })

    clusterer = engine._session.clusterer
    assert clusterer is not None
    # Source identity: one hypothesis per distinct historical turn.
    for seen in clusterer.seen_observation_refs:
        assert len(seen) == len(set(seen))
    clusters = []
    for i in recurrent_cluster_ids(clusterer):
        members = clusterer.members[i]
        involved = [
            row["mit_turn"]
            for row in records
            if any(row["text"] == member for member in members)
        ]
        clusters.append({
            "cluster_id": i,
            "observations": int(clusterer.recurrence(i)),
            "members": members,
            "source_turns": sorted(set(involved)),
        })

    stored = engine.inspect().get("seeds", [])
    assert engine.turn == 158
    assert all(float(seed["weight"]) == 0 for seed in stored), "Unexpected authority"
    assert not any(a["surfaced_seed_ids"] for a in turn_audit)
    baseline = build_lexical_baseline(records)
    summary = {
        "source_turns": len(turns),
        "explicit_hypothesis_mentions": len(records),
        "distinct_note_turns": len({r["mit_turn"] for r in records}),
        "engine_seeds_stored": len(stored),
        "engine_semantic_clusters_total": len(clusterer.members),
        "engine_semantic_recurrent_clusters": len(clusters),
        "all_engine_recurrence_followups": sum(max(0, clusterer.recurrence(i) - 1) for i in range(len(clusterer.members))),
        "engine_cluster_observations_in_recurrent_clusters": sum(c["observations"] for c in clusters),
        "baseline_exact_repeat_occurrences": sum(a["kind"] == "exact" for a in baseline),
        "baseline_hashing_ngram_0_6_matches": sum(a["kind"] == "hashing_ngram_0.6" for a in baseline),
        "semantic_nearest_prior_cosine_ge_0_6": sum(x["semantic_cosine"] >= 0.6 for x in semantic_nearest_prior),
        "semantic_nearest_prior_cosine_ge_0_75": sum(x["semantic_cosine"] >= 0.75 for x in semantic_nearest_prior),
        "non_authorizing_replay": True,
        "research_novelty_tested": False,
        "causal_weight_edit_tested": False,
        "elapsed_seconds_without_model_download": round(time.monotonic() - start, 1),
    }
    write_json("manifest.json", {
        "MIT_commit": "4d09ba6d6a7e891dd8063974dfe81b3d78e3494f",
        "trajectory_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "model": EMBED_ID, "model_commit": model_info(EMBED_ID).sha,
        "source_file_git_blob": MIT_BLOB_SHA,
        "cluster_threshold": 0.6,
        "lexical_baseline": "HashingVectorizer unigram+bigram, cosine threshold 0.6, no corpus fit",
        "selection": "all exact # Hypothesis: lines from all 158 sequential turns",
        "authority": "evidence_backed, no independent evidence supplied",
    })
    write_json("turn_audit.json", turn_audit)
    write_json("source_hypotheses.json", records)
    write_json("cluster_pairs_for_manual_review.json", clusters)
    write_json("plain_notes_baselines.json", baseline)
    write_json("semantic_nearest_prior.json", semantic_nearest_prior)
    write_json("summary.json", summary)
    print("REPLAY_85_RESULTS", json.dumps(summary, ensure_ascii=False), flush=True)
    print("REPLAY_85_CLUSTER_SAMPLES", json.dumps(clusters[:9], ensure_ascii=False), flush=True)


if __name__ == "__main__":
    run()
