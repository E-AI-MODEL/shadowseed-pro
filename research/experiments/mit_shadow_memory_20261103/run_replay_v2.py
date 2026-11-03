"""Research-only MIT replay v2: real chat-templated detector + real ShadowseedEngine.

Original MIT responses are never edited. Only explicit research-note statements,
not tool JSON/code, are sent to the detector. No candidates gain authority.
This experiment is not evidence of better weight edits or causal benefit.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import time

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from sentence_transformers import SentenceTransformer
from huggingface_hub import model_info

from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import parse_numbered_seeds_with_diagnostics

MIT_COMMIT = "4d09ba6d6a7e891dd8063974dfe81b3d78e3494f"
MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
EMBED_ID = "sentence-transformers/all-MiniLM-L6-v2"
INPUT = Path("mit-data/exp8_math/runs/p50c/readable/trajectory.md")
OUTPUT = Path("mit-v2-output")
OUTPUT.mkdir(exist_ok=True)
MAX_NOTES = int(os.getenv("MAX_NOTES", "5"))

def parse_turns(text: str) -> list[tuple[int, str]]:
    parts = re.split(r"(?m)^## t(\d{3})\s*$", text)
    turns = []
    for i in range(1, len(parts), 2):
        n = int(parts[i])
        body = parts[i + 1].split("### astra", 1)
        if len(body) != 2:
            raise ValueError(f"Missing model reply at MIT turn {n}")
        turns.append((n, body[1]))
    if len(turns) != 158 or [n for n, _ in turns] != list(range(1, 159)):
        raise ValueError(f"Expected exactly 158 ordered MIT turns, got {len(turns)}")
    return turns

def extract_observation(reply: str) -> str | None:
    """Source-preserving extraction: explicit logged hypothesis, not generated paraphrase."""
    hypothesis = re.search(r"(?m)^\s*#\s*Hypothesis:\s*(.+)$", reply)
    if hypothesis:
        return hypothesis.group(1).strip()
    # A substantive narrative is allowed; JSON tool requests and code are not.
    before_code = re.split(r"(?m)^\s*"+chr(96)*3, reply, maxsplit=1)[0].strip()
    if len(before_code) >= 110 and not before_code.startswith(("{", "[")):
        return before_code[:750]
    return None

SYSTEM = (
    "You are an experimental research assistant. Read a research note and propose "
    "an unanswered, TESTABLE research question that is not already resolved by that note. "
    "Do not restate or confirm the given hypothesis. Do not invent measurements, "
    "results, observations, sources, or certainty. "
    "Output one or two numbered short candidate gaps, using only these forms:\n"
    "1. [single testable question or research relation]\n"
    "2. [different single testable question or research relation]\n"
    "If none exists, output exactly NONE. No preface, explanations, code, or markdown."
)

class MITChatDetector:
    name = "mit-qwen-chat-template-v2"
    prompt_variant = "mit_research_note_v2"

    def __init__(self, model_id: str):
        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto")
        self.model.eval()
        self.last_raw_output = None
        self.last_parse_diagnostics = None

    @torch.inference_mode()
    def detect_seeds(self, item: dict, max_seeds: int = 2) -> list[str]:
        note = (item.get("text") or "").strip()
        prompt = (
            "The following note is from a published experiment editing a small "
            "language model's weights. Suggest a genuinely different, specific "
            "follow-up test to investigate, not an invented result.\n\n"
            "RESEARCH NOTE:\n" + note[:850] + "\n\n"
            "Give up to " + str(max_seeds) + " candidates."
        )
        inputs = self.tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
            tokenize=True, add_generation_prompt=True, return_tensors="pt",
        )
        response = self.model.generate(
            inputs, max_new_tokens=112, do_sample=False,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        raw = self.tokenizer.decode(response[0, inputs.shape[-1]:], skip_special_tokens=True).strip()
        candidates, diagnostics = parse_numbered_seeds_with_diagnostics(
            raw, max_seeds=max_seeds, source_text=note,
        )
        self.last_raw_output = raw
        self.last_parse_diagnostics = diagnostics
        return candidates

def write_json(name, data):
    (OUTPUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def main():
    torch.manual_seed(20261103)
    torch.set_num_threads(4)
    text = INPUT.read_text(encoding="utf-8")
    raw_turns = parse_turns(text)
    selected = [(n, note) for n, reply in raw_turns if (note := extract_observation(reply))]
    selected = selected[:MAX_NOTES]
    if not selected:
        raise RuntimeError("The extractor found no substantive MIT research notes")
    print("SOURCE_CHECK", json.dumps({
        "total_mit_turns": len(raw_turns), "notes_selected": len(selected),
        "turns_selected": [x[0] for x in selected],
        "mit_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    }), flush=True)
    detector = MITChatDetector(MODEL_ID)
    embed_model = SentenceTransformer(EMBED_ID, device="cpu")
    cache = {}
    def embed(text):
        text = str(text)
        if text not in cache:
            cache[text] = np.asarray(embed_model.encode(text, normalize_embeddings=True), dtype=float)
        return cache[text]
    manifest = {
        "mit_commit": MIT_COMMIT, "mit_turns": len(raw_turns),
        "original_mit_file_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "shadowseed_commit": os.getenv("GITHUB_SHA"),
        "detector": MODEL_ID, "detector_commit": model_info(MODEL_ID).sha,
        "embeddings": EMBED_ID, "embeddings_commit": model_info(EMBED_ID).sha,
        "selected_turns": [n for n, _ in selected],
        "extraction": "explicit MIT hypotheses or prose before code",
        "chat_template": True, "generation_temperature": "greedy",
        "authority_from_replay": "none; evidence_backed gate",
        "historical_replay": True, "causal_test": False,
    }
    write_json("manifest.json", manifest)
    # Preflight is a separate synthetic example. It cannot be counted as
    # evidence of novelty in the MIT trajectory.
    calibration = (
        "The edited model answered eight of ten questions correctly. "
        "These were the same ten questions used to select the edit."
    )
    preflight_candidates = detector.detect_seeds({"text": calibration}, max_seeds=2)
    write_json("calibration.json", {
        "input": calibration, "raw": detector.last_raw_output,
        "parse": detector.last_parse_diagnostics, "candidates": preflight_candidates,
    })
    if not preflight_candidates:
        raise RuntimeError("Detector calibration failed: no parseable research candidates")
    print("DETECTOR_PREFLIGHT", json.dumps({
        "candidate_count": len(preflight_candidates),
        "candidates": preflight_candidates,
    }), flush=True)
    engine = ShadowseedEngine(
        embedding_fn=embed, detector_backend=detector,
        gate_policy_id="evidence_backed",
        recurrence_mode="cluster", max_seeds_per_turn=2,
    )
    records = []
    start = time.monotonic()
    try:
        for turn, observation in selected:
            question = "What remains worth investigating about this research observation?"
            prepared = engine.prepare_turn(question)
            report = engine.observe_turn(prepared, observation)
            rec = {
                "mit_turn": turn,
                "mit_note_exact": observation,
                "detector_raw": detector.last_raw_output,
                "parse": detector.last_parse_diagnostics,
                "detected_candidates": report.get("detected_candidates", []),
                "born_weightless_seed_ids": report.get("seeds_born_weightless", []),
                "intake_diagnostics": report.get("intake_diagnostics"),
                "surfaced_seed_ids": report.get("surfaced_seed_ids", []),
            }
            records.append(rec)
            write_json("turn_records.json", records)
            print("MODEL_TURN", json.dumps({
                "mit_turn": turn, "raw": detector.last_raw_output,
                "detected_count": len(rec["detected_candidates"]),
                "accepted_count": len(rec["born_weightless_seed_ids"]),
            }, ensure_ascii=False), flush=True)
    except Exception:
        write_json("turn_records.json", records)
        raise
    seeds = engine.inspect().get("seeds", [])
    write_json("seeds.json", seeds)
    detected_total = sum(len(x["detected_candidates"]) for x in records)
    accepted_total = sum(len(x["born_weightless_seed_ids"]) for x in records)
    assert engine.turn == len(records), "Engine missed a research-note turn"
    assert all(float(s["weight"]) == 0.0 for s in seeds), "Unauthorized promotion"
    assert not any(x["surfaced_seed_ids"] for x in records), "Unauthorized historical influence"
    summary = {
        "technical_turns_completed": len(records), "detector_candidates": detected_total,
        "accepted_weightless_seeds": accepted_total, "stored_seeds": len(seeds),
        "model_calibration_candidates": len(preflight_candidates),
        "no_influence_and_no_promotion": True,
        "elapsed_s": round(time.monotonic()-start, 1),
        "novelty_not_proven": True,
    }
    write_json("summary.json", summary)
    print("REPLAY_RESULT", json.dumps(summary), flush=True)
    # A green experiment must have demonstrated its PRIMARY behavior,
    # not merely run a model and upload empty records.
    if not detected_total or not accepted_total:
        raise RuntimeError("NO_RESULT: no research candidate survived detection and intake")

if __name__ == "__main__":
    main()
