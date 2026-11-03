"""Research-specific quality boundary for the MIT / ShadowSeed exploratory replay.

The normal ShadowSeed parser and authority gates are unchanged. This experiment
adds an explicit, rejectable *method fit* check before candidate ingestion.
The check does not certify novelty, scientific merit, or causal value.
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
from sentence_transformers import SentenceTransformer
from huggingface_hub import model_info
from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import parse_numbered_seeds_with_diagnostics
from research.experiments.mit_shadow_memory_20261103.run_replay_v2 import (
    MITChatDetector, MODEL_ID, EMBED_ID, INPUT, parse_turns, extract_observation,
)

OUT = Path("mit-v3-output")
OUT.mkdir(exist_ok=True)
SELECTED_TURNS = (1, 3, 34, 64, 142)
SYSTEM = (
    "You are helping design a controlled mechanistic experiment, not training a model. "
    "Study: a frozen Qwen3.5 0.8B transformer produces repetitive reasoning. "
    "The researchers inspect layer activations, token probabilities and generation results "
    "and can make targeted weight edits. No training, fine-tuning, dropout, learning-rate "
    "changes or architecture changes are allowed. "
    "Given a contemporaneous research observation, identify a genuinely unresolved test "
    "or control. Do not invent measurements or imply existing results were not measured. "
    "Use one or two numbered concise suggestions. Format each:\n"
    "1. Compare [specific intervention or control] versus [specific baseline] "
    "and measure [specific outcome] to test [one mechanism].\n"
    "Do not propose generic generalization studies, correlations without interventions, "
    "or tests that merely restate the observation. If nothing concrete, write exactly NONE. "
    "No examples, explanation, markdown, placeholders or code."
)

OUT_OF_SCOPE = [
    (r"\b(dropout|learning rate|optimizer|optimiser|backpropagation|fine.tun(?:e|ing))\b", "outside_frozen_weight_edit"),
    (r"\b(train(?:ing)? (?:with|on)|retrain(?:ing)?)\b", "outside_frozen_weight_edit"),
    (r"\b(recurrent (?:network|connections|layer))\b", "incorrect_architecture_assumption"),
]
UNSPECIFIC = [
    (r"\b(diverse tasks|diverse domains|downstream tasks|different tasks)\b", "generic_transfer_question"),
    (r"\b(ability to generalize|generalize across diverse)\b", "generic_transfer_question"),
]
CONTRAST = re.compile(r"\b(compar(?:e|ing|ison)|versus|vs\.?|relative to|with and without|baseline|control|ablat(?:e|ion|ing)|edited and original|original and edited)\b", re.I)
MEASURE = re.compile(r"\b(accuracy|correct|cutoff|cut.off|truncat|token|log.?prob|likelihood|repetition|repeat|error|perplexity|failure rate|rescues|regressions|box(?:ed)?|whitespace|latency|generation length)\b", re.I)

def normalize_research_numbered_output(raw: str) -> str:
    """Preserve numbered proposals, joining only labeled measurement continuations.

    This does not reinterpret NONE and does not turn explanatory prose into
    candidate evidence. Raw text is retained separately for review.
    """
    lines = raw.splitlines()
    if lines and lines[0].strip().upper().startswith("NONE"):
        return raw
    numbered = re.compile(r"^\s*(\d+)[.)]\s*(.+?)\s*$")
    continuation = re.compile(
        r"^\s*[-*]?\s*(?:\*\*)?(?:Specific Outcome|Measured Outcome|Outcome|Metric)(?:\*\*)?\s*:\s*(.+?)\s*$",
        re.I,
    )
    result: list[str] = []
    for line in lines:
        match = numbered.match(line)
        if match:
            value = re.sub(r"\*\*(.*?)\*\*", r"\1", match.group(2))
            result.append(f"{match.group(1)}. {value}")
            continue
        extra = continuation.match(line)
        if extra and result:
            value = re.sub(r"\*\*(.*?)\*\*", r"\1", extra.group(1))
            result[-1] += " Measured outcome: " + value
    return "\n".join(result)


def quality_reasons(candidate: str) -> list[str]:
    reasons = []
    for pattern, label in OUT_OF_SCOPE + UNSPECIFIC:
        if re.search(pattern, candidate, re.I):
            reasons.append(label)
    if not CONTRAST.search(candidate):
        reasons.append("missing_explicit_comparison")
    if not MEASURE.search(candidate):
        reasons.append("missing_measurable_outcome")
    if len(candidate.split()) < 9:
        reasons.append("insufficient_test_detail")
    return list(dict.fromkeys(reasons))

class ScopedMITDetector(MITChatDetector):
    name = "mit-chat-method-fit-v3"
    prompt_variant = "mit_method_fit_v3"

    @torch.inference_mode()
    def detect_seeds(self, item: dict, max_seeds: int = 2) -> list[str]:
        note = str(item.get("text") or "").strip()
        request = (
            "ACTUAL RESEARCH OBSERVATION (not a verified general truth):\n"
            + note[:850] + "\n\n"
            + "Propose at most two distinct weight-edit or diagnostic controls, "
            + "each naming a baseline and a measurable outcome."
        )
        inputs = self.tokenizer.apply_chat_template(
            [{"role": "system", "content": SYSTEM}, {"role": "user", "content": request}],
            add_generation_prompt=True, tokenize=True, return_tensors="pt",
        )
        generated = self.model.generate(
            inputs, max_new_tokens=155, do_sample=False,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        raw = self.tokenizer.decode(generated[0, inputs.shape[-1]:], skip_special_tokens=True).strip()
        normalized = normalize_research_numbered_output(raw)
        parsed, diag = parse_numbered_seeds_with_diagnostics(normalized,max_seeds=max_seeds,source_text=note)
        accepted = []
        rejected = []
        for candidate in parsed:
            reasons = quality_reasons(candidate)
            if reasons:
                rejected.append({"text": candidate, "reasons": reasons})
            else:
                accepted.append(candidate)
        self.last_raw_output = raw
        self.last_normalized_output = normalized
        self.last_parse_diagnostics = diag
        self.last_accepted = accepted
        self.last_rejected = rejected
        return accepted

def save(name, obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")

def main():
    torch.manual_seed(20261103)
    torch.set_num_threads(4)
    text = INPUT.read_text(encoding="utf-8")
    turns = parse_turns(text)
    by_number = {n: extract_observation(reply) for n, reply in turns}
    selected = [(n, by_number.get(n)) for n in SELECTED_TURNS]
    if any(not note for _n, note in selected):
        raise RuntimeError("Missing exact source observation for fixed MIT selection")
    detector = ScopedMITDetector(MODEL_ID)
    embedding_model = SentenceTransformer(EMBED_ID,device="cpu")
    cache = {}
    def embed(value):
        key = str(value)
        if key not in cache:
            cache[key] = np.asarray(embedding_model.encode(key,normalize_embeddings=True),dtype=float)
        return cache[key]
    manifest = {
        "mit_commit": "4d09ba6d6a7e891dd8063974dfe81b3d78e3494f",
        "mit_trajectory_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "shadowseed_commit": os.environ.get("GITHUB_SHA"),
        "model": MODEL_ID,"model_commit": model_info(MODEL_ID).sha,
        "embedding": EMBED_ID,"embedding_commit": model_info(EMBED_ID).sha,
        "selected_mit_turns": list(SELECTED_TURNS),
        "selection_rule": "preselected across early and later phases",
        "test_design": "source-grounded candidate-generation and method-fit screen only",
        "novelty_asserted": False, "causal_benefit_asserted": False,
        "authority_policy": "evidence_backed_zero_unless_external_evidence",
    }
    save("manifest.json", manifest)
    detector.detect_seeds({"text": (
        "The selected weight edit improved accuracy on the same 32 math tasks "
        "used to tune it. Its effect on independent held-out tasks is unknown."
    )},max_seeds=2)
    calibration = {
        "raw": detector.last_raw_output,
        "normalized": detector.last_normalized_output,
        "accepted": detector.last_accepted,
        "rejected": detector.last_rejected,
        "parse": detector.last_parse_diagnostics,
    }
    save("preflight.json", calibration)
    print("PREFLIGHT",json.dumps(calibration,ensure_ascii=False),flush=True)
    if not calibration["accepted"]:
        raise RuntimeError("PRECHECK_FAILED: model output did not pass experiment method-fit rules")

    engine = ShadowseedEngine(
        embedding_fn=embed, detector_backend=detector, max_seeds_per_turn=2,
        recurrence_mode="cluster",gate_policy_id="evidence_backed",
    )
    records = []
    start = time.monotonic()
    try:
        for n,note in selected:
            p = engine.prepare_turn("Which specific untested control could evaluate this MIT observation?")
            report = engine.observe_turn(p,note)
            record = {
                "mit_turn":n,"source_observation":note,
                "raw_output":detector.last_raw_output,
                "normalized_output":detector.last_normalized_output,
                "parsed":detector.last_parse_diagnostics,
                "method_fit_candidates":detector.last_accepted,
                "method_fit_rejections":detector.last_rejected,
                "seed_ids_born_weightless":report["seeds_born_weightless"],
                "intake_diagnostics":report.get("intake_diagnostics"),
                "surfaced_seed_ids":report.get("surfaced_seed_ids"),
            }
            records.append(record)
            save("records.json",records)
            print("TURN_RESULT",json.dumps({
                "mit_turn":n, "accepted":record["method_fit_candidates"],
                "rejected":record["method_fit_rejections"],
                "stored":len(record["seed_ids_born_weightless"]),
            },ensure_ascii=False),flush=True)
    except Exception:
        save("records.json",records)
        raise
    seeds = engine.inspect()["seeds"]
    assert engine.turn == len(records)
    assert all(float(s["weight"])==0.0 for s in seeds)
    assert not any(r["surfaced_seed_ids"] for r in records)
    summary = {
        "turns_processed":len(records),
        "accepted_method_fit_candidates":sum(len(r["method_fit_candidates"]) for r in records),
        "rejected_method_fit_candidates":sum(len(r["method_fit_rejections"]) for r in records),
        "born_weightless_seeds":sum(len(r["seed_ids_born_weightless"]) for r in records),
        "stored_seeds":len(seeds),
        "elapsed_seconds":round(time.monotonic()-start,1),
        "scientific_novelty_unreviewed":True,
        "no_authority_or_influence":True,
    }
    save("summary.json",summary)
    save("seeds.json",seeds)
    print("REPLAY_V3_FINAL",json.dumps(summary),flush=True)
    if not summary["accepted_method_fit_candidates"] or not summary["born_weightless_seeds"]:
        raise RuntimeError("NO_USABLE_HYPOTHESES: no proposed candidate passed source-method fit")

if __name__=="__main__":
    main()
