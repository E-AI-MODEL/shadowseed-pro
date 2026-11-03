"""Strict no-few-shot prompt evaluation of the same frozen MIT identity pairs.

This is an exploratory post-hoc *prompt ablation*, not an independent model
validation. The canonical ShadowSeed recognizer parser is used unchanged.
The model, exact MIT texts, manual labels and decoding settings match v1.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import model_info
from shadowseed.recurrence_recognition import recognize, OpenQuestion

from research.experiments.mit_shadow_memory_20261103.run_identity_pilot import (
    MODEL_ID, CLUSTER_PAIRS, EXACT_POSITIVE_CONTROLS, build_source_rows
)
from research.experiments.mit_shadow_memory_20261103.run_replay_v2 import INPUT

OUT = Path("mit-strict-identity-output")
OUT.mkdir(exist_ok=True)


def strip_fewshot_and_require_single_answer(prompt: str) -> str:
    marker = "Answer with one line per new note, in this form:"
    if marker not in prompt:
        raise ValueError("Unexpected canonical prompt; refusing untraced rewrite")
    prefix = prompt.split(marker, 1)[0].strip()
    return (
        prefix
        + "\n\nDecide only whether the latest note repeats exactly the same "
        "specific unresolved research question or experimental test as open question 1. "
        "Topic overlap or a different intervention, comparison, dose, or outcome "
        "does not qualify. Do not treat follow-up work as an identical question "
        "without matching the actual question being tested.\n"
        "Write exactly ONE line, either 'a: 1' (same specific question) "
        "or 'a: NONE' (different question). No explanations, examples, lists "
        "of options, additional letters or numbering.\n"
    )


def save(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    torch.manual_seed(20261103)
    torch.set_num_threads(4)
    rows = build_source_rows(INPUT.read_text(encoding="utf-8"))
    if len(rows) != 85:
        raise ValueError("Source mismatch: expected exactly 85 MIT hypotheses")
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, torch_dtype="auto")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model.eval()

    save("manifest.json", {
        "MIT_commit": "4d09ba6d6a7e891dd8063974dfe81b3d78e3494f",
        "source_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "model_id": MODEL_ID,
        "model_sha": model_info(MODEL_ID).sha,
        "shadowseed_research_sha": os.environ.get("GITHUB_SHA"),
        "comparison": "same 12 pre-labeled pairs + 2 exact-positive controls as initial run",
        "intervention": "prompt removes canonical example answer and constrains single-pair reply",
        "decoding": "do_sample=False, max_new_tokens=25",
        "evaluation_status": "posthoc exploratory, non-blind labels, not a validated improvement",
        "production_code_modified": False,
    })

    @torch.inference_mode()
    def generate(original_prompt: str) -> str:
        prompt = strip_fewshot_and_require_single_answer(original_prompt)
        inputs = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}],
            tokenize=True, add_generation_prompt=True, return_tensors="pt",
        )
        generated = model.generate(
            inputs, max_new_tokens=25, do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
        return tokenizer.decode(generated[0, inputs.shape[-1]:], skip_special_tokens=True).strip()

    pairs = CLUSTER_PAIRS + EXACT_POSITIVE_CONTROLS
    results = []
    started = time.monotonic()
    for earlier, later, manual_label, rationale in pairs:
        mapping, raw = recognize(
            generate,
            [OpenQuestion(1, 0, rows[earlier])],
            [rows[later]],
        )
        verdict = mapping.get(0) if mapping else None
        parsed = verdict is not None
        predicted_same = bool(parsed and verdict.open_question == 1)
        expected_same = manual_label == "same"
        result = {
            "earlier_turn":earlier, "later_turn":later,
            "earlier_text":rows[earlier], "later_text":rows[later],
            "manual_label":manual_label, "manual_rationale":rationale,
            "raw_model_output":raw, "parsed":parsed,
            "predicted_same":predicted_same, "expected_same":expected_same,
            "agrees":parsed and predicted_same==expected_same,
        }
        results.append(result)
        save("pair_results.json",results)
        print("STRICT_PAIR",json.dumps({
            "pair":[earlier,later],"manual_label":manual_label,
            "raw":raw,"parsed":parsed,"predicted_same":predicted_same
        },ensure_ascii=False),flush=True)

    eval_cases = results[:len(CLUSTER_PAIRS)]
    positive_controls = results[len(CLUSTER_PAIRS):]
    summary = {
        "cluster_pairs":len(eval_cases),
        "same_question_pairs":sum(x["expected_same"] for x in eval_cases),
        "different_or_related_pairs":sum(not x["expected_same"] for x in eval_cases),
        "true_positive":sum(x["parsed"] and x["expected_same"] and x["predicted_same"] for x in eval_cases),
        "false_negative":sum(x["expected_same"] and not x["predicted_same"] for x in eval_cases),
        "false_positive":sum(not x["expected_same"] and x["predicted_same"] for x in eval_cases),
        "true_negative":sum(x["parsed"] and not x["expected_same"] and not x["predicted_same"] for x in eval_cases),
        "unreadable":sum(not x["parsed"] for x in eval_cases),
        "exact_positive_controls_passed":sum(x["parsed"] and x["predicted_same"] for x in positive_controls),
        "elapsed_seconds":round(time.monotonic()-started,1),
        "nonblind_posthoc":True,
        "scientific_novelty_proven":False,
    }
    save("summary.json",summary)
    print("STRICT_IDENTITY_SUMMARY",json.dumps(summary),flush=True)
    if (
        summary["false_positive"]
        or summary["unreadable"]
        or summary["exact_positive_controls_passed"] != len(EXACT_POSITIVE_CONTROLS)
    ):
        raise RuntimeError("STRICT_IDENTITY_UNRELIABLE: key negative/duplicate controls failed")

if __name__ == "__main__":
    main()
