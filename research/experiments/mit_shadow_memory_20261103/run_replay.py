"""Read-only MIT replay with the real ShadowseedEngine and local open models."""
import hashlib
import json
import os
from pathlib import Path
import re
import time
from functools import lru_cache

import numpy as np
import torch
from huggingface_hub import model_info
from sentence_transformers import SentenceTransformer
from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import HFTransformersDetectorBackend

MIT_SHA = "4d09ba6d6a7e891dd8063974dfe81b3d78e3494f"
BASE = Path("mit-data/exp8_math/runs/p50c")
OUT = Path("mit-replay-output")
OUT.mkdir(exist_ok=True)
DETECTOR_ID = "Qwen/Qwen2.5-0.5B-Instruct"
EMBEDDING_ID = "sentence-transformers/all-MiniLM-L6-v2"
LIMIT = int(os.environ.get("LIMIT", "158"))

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def parse_turns(path):
    text = Path(path).read_text(encoding="utf-8")
    blocks = re.split(r"(?m)^## t(\d{3})\s*$", text)
    turns = []
    for index in range(1, len(blocks), 2):
        num = int(blocks[index])
        body = blocks[index + 1]
        segments = body.split("### astra", 1)
        if len(segments) != 2:
            raise ValueError(f"Missing Astra answer at turn {num}")
        received = segments[0].replace("### received", "", 1).strip()
        reply = segments[1].strip()
        hypotheses = re.findall(r"(?m)^\s*#\s*Hypothesis:\s*(.+)$", reply)
        turns.append((num, received, reply, hypotheses))
    if len(turns) != 158 or [t[0] for t in turns] != list(range(1, 159)):
        raise ValueError(f"Unexpected trajectory: {len(turns)} turns")
    return turns

def visible_excerpt(reply):
    prose = reply.split(chr(96) * 3, 1)[0].strip()
    comments = re.findall(r"(?m)^\s*#\s*(?:Hypothesis:|Next:|Test:|Control:|Check:).+", reply)
    if len(prose) >= 70:
        return prose[:1200]
    if comments:
        return "\n".join(comments[:7])[:1200]
    return reply[:1200]

torch.manual_seed(20261103)
torch.set_num_threads(2)
print("REPLAY_START", json.dumps({"limit": LIMIT, "mit_commit": MIT_SHA, "shadowseed_commit": os.environ.get("GITHUB_SHA")}), flush=True)
source = BASE / "readable/trajectory.md"
turns = parse_turns(source)[:LIMIT]
embedding_model = SentenceTransformer(EMBEDDING_ID, device="cpu")

@lru_cache(maxsize=5000)
def embedding(text):
    vector = embedding_model.encode(str(text), normalize_embeddings=True, convert_to_numpy=True)
    return np.asarray(vector, dtype=float)

detector = HFTransformersDetectorBackend(
    model_id=DETECTOR_ID, max_new_tokens=72, prompt_variant="current_pair"
)
engine = ShadowseedEngine(
    embedding_fn=embedding,
    detector_backend=detector,
    recurrence_mode="cluster",
    gate_policy_id="evidence_backed",
    max_seeds_per_turn=2,
)
manifest = {
    "mit_commit": MIT_SHA,
    "shadowseed_commit": os.environ.get("GITHUB_SHA"),
    "mit_trajectory_sha256": sha256(source),
    "detector_model": DETECTOR_ID,
    "detector_model_commit": model_info(DETECTOR_ID).sha,
    "embedding_model": EMBEDDING_ID,
    "embedding_model_commit": model_info(EMBEDDING_ID).sha,
    "prompt_variant": "current_pair",
    "max_seed_candidates_per_turn": 2,
    "max_new_tokens": 72,
    "turns_available": 158,
    "turns_requested": LIMIT,
    "reference_replay_not_generation": True,
    "no_verified_evidence_or_promotion": True,
    "visible_answer_excerpts_limited_to": 1200,
    "question_feedback_excerpts_limited_to": 500,
}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
all_hypotheses, events, candidates = [], [], []
begin = time.monotonic()

def write_checkpoint():
    (OUT / "turn_records.json").write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "candidate_records.json").write_text(json.dumps(candidates, indent=2, ensure_ascii=False), encoding="utf-8")

for turn, received, answer_raw, hypotheses in turns:
    answer = visible_excerpt(answer_raw)
    question = f"Qwen3.5-0.8B weight investigation, turn {turn}. Experimental feedback: {received[-500:]}"
    prepared = engine.prepare_turn(question)
    try:
        report = engine.observe_turn(prepared, answer)
    except Exception:
        write_checkpoint()
        raise
    seeds = engine.inspect().get("seeds", [])
    by_id = {s["id"]: s for s in seeds}
    born = list(report.get("seeds_born_weightless", []))
    for seed_id in born:
        seed = by_id[seed_id]
        candidate_text = seed["text"]
        if all_hypotheses:
            scores = [float(np.dot(embedding(candidate_text), embedding(h))) for h in all_hypotheses]
            similarity = max(scores)
            nearest = all_hypotheses[int(np.argmax(scores))]
        else:
            similarity, nearest = None, None
        candidates.append({
            "turn": turn, "seed_id": seed_id, "text": candidate_text,
            "similarity_to_prior_explicit_MIT_hypothesis": similarity,
            "nearest_prior_MIT_hypothesis": nearest,
            "status": seed["status"], "weight": seed["weight"],
        })
    events.append({
        "turn": turn, "answer_chars": len(answer),
        "mit_explicit_hypotheses": hypotheses,
        "detector_raw": detector.last_raw_output,
        "detector_parse": detector.last_parse_diagnostics,
        "born_seed_ids": born,
        "surfaced_seed_ids": report.get("surfaced_seed_ids", []),
    })
    all_hypotheses.extend(hypotheses)
    write_checkpoint()
    if turn % 10 == 0 or turn == LIMIT:
        print("REPLAY_PROGRESS", json.dumps({"turn": turn, "born": len(candidates), "elapsed_s": round(time.monotonic()-begin, 1)}), flush=True)

seeds = engine.inspect().get("seeds", [])
assert engine.turn == len(events), (engine.turn, len(events))
assert all(float(s["weight"]) == 0.0 for s in seeds), "Unexpected authority"
assert not any(e["surfaced_seed_ids"] for e in events), "Unexpected influence"
summary = {
    "turns_completed": len(events), "seeds_born": len(candidates),
    "seeds_in_inspection": len(seeds),
    "mit_explicit_hypothesis_mentions": len(all_hypotheses),
    "surfaced_influence_records": sum(len(e["surfaced_seed_ids"]) for e in events),
    "promoted_seeds": sum(float(s["weight"]) > 0 for s in seeds),
    "raw_detector_nonempty": sum(bool(e["detector_raw"] and e["detector_raw"].strip() not in {"NONE", "1."}) for e in events),
    "elapsed_s": round(time.monotonic()-begin, 1),
    "screening_only_not_discovery": True,
}
shortlist = sorted(candidates, key=lambda c: c["similarity_to_prior_explicit_MIT_hypothesis"] if c["similarity_to_prior_explicit_MIT_hypothesis"] is not None else -1)[:12]
(OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "shortlist.json").write_text(json.dumps(shortlist, ensure_ascii=False, indent=2), encoding="utf-8")
write_checkpoint()
print("REPLAY_FINAL", json.dumps(summary), flush=True)
print("REPLAY_SHORTLIST", json.dumps(shortlist[:7], ensure_ascii=False), flush=True)
