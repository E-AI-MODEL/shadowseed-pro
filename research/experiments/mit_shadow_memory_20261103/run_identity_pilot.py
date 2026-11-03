"""Research-only pilot of existing model-based recurrence recognition.

Use ShadowSeed's canonical recurrence_recognition.recognize, a native chat-
templated small Qwen model, and verbatim hypotheses from a pinned MIT trajectory.
Manual pair labels are predeclared and non-blind. The aim is to test whether a
recognizer can reject semantically related but DIFFERENT research questions.
No production code, Gate, weight edit or MIT baseline is modified.
"""
from __future__ import annotations

import json
import os
import time
import hashlib
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import model_info

from shadowseed.recurrence_recognition import recognize, OpenQuestion
from research.experiments.mit_shadow_memory_20261103.run_replay_v2 import parse_turns, INPUT
from research.experiments.mit_shadow_memory_20261103.replay_85_source_hypotheses import extract_hypotheses

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
OUT = Path("mit-identity-pilot-output")
OUT.mkdir(exist_ok=True)

# Fixed pair set from the first, post-hoc manual review of 12 embedding clusters.
# "related" is NEGATIVE: the subject is similar but the experimental question
# is not equivalent. This is not an independently annotated benchmark.
CLUSTER_PAIRS = [
    (1, 64, "different", "diagnosis vs MLP intervention transfer"),
    (10, 68, "related", "writer localization vs dose-response mechanism"),
    (17, 60, "different", "MLP direction vs independent attention-head intervention"),
    (18, 29, "same", "multi-layer and dose-response question"),
    (20, 88, "different", "recover earlier run vs random-direction control"),
    (27, 84, "different", "restore experiment state vs dose-response over early closure"),
    (54, 121, "different", "numerical/attention check vs held-out transfer"),
    (58, 83, "related", "alpha3 selectivity vs higher-strength transfer"),
    (66, 108, "related", "alpha1 vs alpha6 intervention"),
    (70, 80, "different", "alpha2 held-out gain vs alpha4 overcorrection"),
    (117, 138, "same", "same frozen-alpha6 transfer claim"),
    (129, 134, "same", "same frozen-edit batch reproducibility claim"),
]
EXACT_POSITIVE_CONTROLS = [
    (81, 82, "same", "verbatim repeated hypothesis"),
    (121, 122, "same", "verbatim repeated hypothesis"),
]


def build_source_rows(text: str) -> dict[int, str]:
    return {
        n: hypothesis
        for n, reply in parse_turns(text)
        for hypothesis in extract_hypotheses(reply)
    }


def save(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    torch.manual_seed(20261103)
    torch.set_num_threads(4)
    source = INPUT.read_text(encoding="utf-8")
    rows = build_source_rows(source)
    if len(rows) != 85:
        raise ValueError(f"Expected 85 hypothesis source rows; got {len(rows)}")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype="auto")
    model.eval()
    manifest = {
        "mit_sha": "4d09ba6d6a7e891dd8063974dfe81b3d78e3494f",
        "mit_trajectory_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "shadowseed_commit": os.environ.get("GITHUB_SHA"),
        "model": MODEL_ID, "model_sha": model_info(MODEL_ID).sha,
        "method": "unmodified shadowseed.recurrence_recognition.recognize()",
        "question_identity_labels": "researcher-created, non-blind, exploratory",
        "strict_related_counts_as": "not same",
        "no_trained_edit_or_output_influence": True,
    }
    save("manifest.json", manifest)
    pairs = CLUSTER_PAIRS + EXACT_POSITIVE_CONTROLS

    @torch.inference_mode()
    def generate(prompt: str) -> str:
        inputs = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            add_generation_prompt=True, tokenize=True, return_tensors="pt",
        )
        output = model.generate(
            inputs,
            max_new_tokens=25,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
        return tokenizer.decode(output[0, inputs.shape[-1]:], skip_special_tokens=True).strip()

    results = []
    start = time.monotonic()
    for earlier, later, label, rationale in pairs:
        verdicts, raw = recognize(
            generate,
            [OpenQuestion(1, 0, rows[earlier])],
            [rows[later]],
        )
        verdict = verdicts.get(0) if verdicts else None
        returned_same = verdict is not None and verdict.open_question == 1
        parsed = verdict is not None
        expected_same = label == "same"
        entry = {
            "earlier_turn": earlier, "later_turn": later,
            "earlier": rows[earlier], "later": rows[later],
            "manual_label": label, "manual_rationale": rationale,
            "expected_same": expected_same,
            "raw_model_output": raw,
            "readable_verdict": (
                "same" if returned_same else ("not_same" if parsed else "unreadable")
            ),
            "parsed": parsed, "returned_same": returned_same,
            "agrees_with_manual_label": parsed and (returned_same == expected_same),
            "in_original_twelve_clusters": (earlier,later,label,rationale) in CLUSTER_PAIRS,
        }
        results.append(entry)
        save("pair_results.json", results)
        print("PAIR_RESULT", json.dumps({
            "pair": [earlier, later], "expected": label,
            "verdict": entry["readable_verdict"], "raw": raw
        }, ensure_ascii=False), flush=True)

    eval_items = results[:len(CLUSTER_PAIRS)]
    exact_controls = results[len(CLUSTER_PAIRS):]
    tp = sum(x["expected_same"] and x["returned_same"] and x["parsed"] for x in eval_items)
    fn = sum(x["expected_same"] and not x["returned_same"] for x in eval_items)
    fp = sum(not x["expected_same"] and x["returned_same"] for x in eval_items)
    tn = sum(not x["expected_same"] and not x["returned_same"] and x["parsed"] for x in eval_items)
    unreadable = sum(not x["parsed"] for x in eval_items)
    summary = {
        "cluster_pair_count":len(eval_items), "exact_control_count":len(exact_controls),
        "pair_TP":tp, "pair_FN":fn, "pair_FP":fp, "pair_TN":tn,
        "unreadable_cluster_pair_answers":unreadable,
        "exact_duplicate_controls_passed":sum(x["returned_same"] and x["parsed"] for x in exact_controls),
        "manual_label_agreements":sum(x["agrees_with_manual_label"] for x in eval_items),
        "manual_labels_nonblind":True,
        "proven_scientific_novelty":False,
        "elapsed_seconds":round(time.monotonic()-start,1),
    }
    save("summary.json",summary)
    print("PILOT_SUMMARY",json.dumps(summary),flush=True)
    # A failed quality pilot must not be marketed as a reliable recognizer.
    if unreadable or fp or summary["exact_duplicate_controls_passed"] != 2:
        raise RuntimeError("RECOGNIZER_NOT_READY: failed critical negative or exact-positive identity controls")

if __name__ == "__main__":
    main()
