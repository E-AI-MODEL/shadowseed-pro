"""Compare observed ShadowSeed links with a plain model judging the SAME two MIT notes.

This is a retrospective, post-hoc diagnostic, NOT an independent benchmark.
The 'SAME' / 'RELATED' / 'NONE' judgments are model outputs, not truth.
The previous live ShadowSeed run and MIT original answers remain unchanged.
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

from research.experiments.mit_shadow_memory_20261103.run_replay_v2 import (
    MIT_COMMIT as MIT_SHA, EMBED_ID as EMBEDDING_ID, parse_turns,
)
from research.experiments.mit_shadow_memory_20261103.replay_85_source_hypotheses import (
    extract_hypotheses,
)

MIT_SOURCE = Path("mit-data/exp8_math/runs/p50c/readable/trajectory.md")
REF = Path("research/experiments/mit_shadow_memory_20261103/causal_pair_reference.json")
OUT = Path("mit-relation-audit-output")
OUT.mkdir(exist_ok=True)
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
LABELS = ("SAME_CLAIM", "RELATED_DISTINCT", "NO_CLEAR_DIRECT_LINK", "UNCERTAIN")

# Original source turn memberships of the twelve recurrent clusters.
# These are audit data from GitHub Actions run 41728955595, not new detector output.
# Non-recurrent clusters are omitted. A pair can be exactly repeated even when
# it is absent here because the Engine deduplicated that second seed.
CLUSTERS = {
    0: [1,64],
    5: [10,68,98],
    6: [13,17,19,21,23,25,26,37,39,43,48,60,94],
    9: [18,29],
    10: [20,24,41,42,88,100],
    12: [27,30,84],
    17: [54,90,92,121,122,144,155],
    19: [58,83],
    21: [66,86,108],
    22: [70,80],
    33: [117,138],
    38: [129,134,148,152,157],
}

# Additional source-specific controls. These are not declared gold negatives.
CHALLENGES = [
    (44,62), (16,131), (154,34), (27,123), (74,98), (44,60),
    (81,82), (121,122),
]

SYSTEM = (
    "You are reviewing two short statements from one model-weight-editing experiment. "
    "Judge the relationship between the two statements, NOT whether they constitute "
    "independent evidence and NOT whether either claim is true. "
    "SAME_CLAIM: they repeat the same specific testable intervention or result claim. "
    "RELATED_DISTINCT: they investigate a shared failure mechanism or one motivates "
    "a different mechanistic intervention/test, but the specific claim differs. "
    "NO_CLEAR_DIRECT_LINK: only broad topic overlap, with no direct useful test or "
    "mechanistic relationship stated in the notes. "
    "UNCERTAIN: the text does not allow a grounded choice. "
    "Be especially careful not to call two related-but-distinct weight edits identical. "
    "A meaningful relationship is NOT a false positive just because edits differ. "
    "Do not infer sources, results or independent confirmation. "
    "Return EXACTLY two lines: LABEL: one of SAME_CLAIM, RELATED_DISTINCT, "
    "NO_CLEAR_DIRECT_LINK, UNCERTAIN; REASON: one short sentence using only these notes."
)
LABEL_PATTERN = re.compile(
    r"(?m)^\s*LABEL\s*:\s*(SAME_CLAIM|RELATED_DISTINCT|NO_CLEAR_DIRECT_LINK|UNCERTAIN)\s*$",
    re.I,
)
REASON_PATTERN = re.compile(r"(?m)^\s*REASON\s*:\s*(.*?)\s*$", re.I)


def save(name, value):
    (OUT / name).write_text(
        json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def pair_cluster_links(a: int, b: int) -> list[int]:
    return [cid for cid, turns in CLUSTERS.items() if a in turns and b in turns]


def parse_model_judgment(raw: str):
    choices = LABEL_PATTERN.findall(raw)
    if len(choices) != 1:
        return {"label": "PARSE_FAILURE", "reason": "", "valid": False}
    explanation = REASON_PATTERN.search(raw)
    return {
        "label": choices[0].upper(),
        "reason": explanation.group(1).strip()[:400] if explanation else "",
        "valid": explanation is not None and bool(explanation.group(1).strip()),
    }


def build_cases(reference: dict, available: dict[int, str]) -> list[dict]:
    cases = []
    seen = set()
    for row in reference["cases"]:
        a, b = int(row["turn_a"]), int(row["turn_b"])
        if a >= b or a not in available or b not in available:
            raise ValueError("Unordered or missing MIT turn in reference")
        seen.add((a,b))
        cases.append({
            "id": row["id"], "a":a, "b":b,
            "selection": "posthoc_annotated_pair",
            "provisional_prior_label": row.get("same_specific_test"),
            "prior_label_is_ground_truth": False,
        })
    for a,b in CHALLENGES:
        a,b = sorted((a,b))
        if (a,b) in seen:
            continue
        seen.add((a,b))
        if a not in available or b not in available:
            raise ValueError("Missing challenge turn")
        cases.append({
            "id":f"C{len(cases)+1:02d}","a":a,"b":b,
            "selection":"posthoc_challenge_or_exact_repeat",
            "prior_label_is_ground_truth":False,
        })
    return cases


def main():
    torch.manual_seed(20261103)
    torch.set_num_threads(4)
    source_text = MIT_SOURCE.read_text(encoding="utf-8")
    turns = parse_turns(source_text)
    notes = {
        n: matches[0]
        for n,reply in turns
        if (matches := extract_hypotheses(reply))
    }
    if len(turns) != 158 or len(notes) != 85:
        raise RuntimeError("Pinned source count mismatch")
    ref = json.loads(REF.read_text(encoding="utf-8"))
    cases = build_cases(ref, notes)
    if len(cases) < 27:
        raise RuntimeError("Unexpected missing retrospective cases")

    sentence_model = SentenceTransformer(EMBEDDING_ID,device="cpu")
    unique_texts = list(dict.fromkeys(notes.values()))
    arr = sentence_model.encode(
        unique_texts, normalize_embeddings=True, convert_to_numpy=True
    )
    vectors = {t:np.asarray(vec,dtype=float) for t,vec in zip(unique_texts,arr)}

    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype="auto")
    model.eval()

    save("manifest.json", {
        "mit_commit":MIT_SHA,
        "mit_source_sha256":hashlib.sha256(MIT_SOURCE.read_bytes()).hexdigest(),
        "research_branch_sha":os.getenv("GITHUB_SHA"),
        "previous_engine_run":41728955595,
        "previous_engine_run_notes":85,
        "model":MODEL,
        "model_sha":model_info(MODEL).sha,
        "embedding_model":EMBEDDING_ID,
        "embedding_sha":model_info(EMBEDDING_ID).sha,
        "labels":LABELS,
        "case_selection":"retrospective, non-blind, prior analyst-selected",
        "not_accuracy_or_causal_evidence":True,
        "no_control_of_model_weights":True,
    })
    records = []
    start = time.monotonic()
    for case in cases:
        a,b = case["a"],case["b"]
        prompt = (
            f"EARLIER MIT NOTE, turn {a}:\n{notes[a]}\n\n"
            f"LATER MIT NOTE, turn {b}:\n{notes[b]}\n\n"
            "Which relationship follows from these two notes alone?"
        )
        tokens = tokenizer.apply_chat_template(
            [{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
            tokenize=True,add_generation_prompt=True,return_tensors="pt",
        )
        with torch.inference_mode():
            gen = model.generate(
                tokens,max_new_tokens=96,do_sample=False,
                pad_token_id=tokenizer.eos_token_id,
            )
        raw = tokenizer.decode(gen[0,tokens.shape[-1]:],skip_special_tokens=True).strip()
        judged = parse_model_judgment(raw)
        links = pair_cluster_links(a,b)
        cos = float(vectors[notes[a]] @ vectors[notes[b]])
        row = {
            **case,"note_a":notes[a],"note_b":notes[b],
            "shadowseed_same_recurrent_cluster":bool(links),
            "shadowseed_cluster_ids":links,
            "pair_embedding_cosine":round(cos,4),
            "embedding_pair_ge_0_6":cos>=0.6,
            "plain_model_raw":raw,
            "plain_model":judged,
            "independent_evidence_present":False,
        }
        records.append(row)
        save("all_pair_results.json",records)
        print("PAIR_RESULT",json.dumps({
            "id":case["id"],"turns":[a,b],"cluster_link":bool(links),
            "plain_model":judged["label"],"valid":judged["valid"],
        },ensure_ascii=False),flush=True)

    valid = [r for r in records if r["plain_model"]["valid"]]
    model_related = {"SAME_CLAIM","RELATED_DISTINCT"}
    agree_related = [
        r for r in valid
        if r["shadowseed_same_recurrent_cluster"] and
        r["plain_model"]["label"] in model_related
    ]
    links_distinct = [
        r for r in valid
        if r["shadowseed_same_recurrent_cluster"] and
        r["plain_model"]["label"]=="RELATED_DISTINCT"
    ]
    model_rel_without_cluster = [
        r for r in valid
        if not r["shadowseed_same_recurrent_cluster"] and
        r["plain_model"]["label"] in model_related
    ]
    counts = {
        label:sum(r["plain_model"]["label"]==label for r in records)
        for label in (*LABELS,"PARSE_FAILURE")
    }
    summary = {
        "pairs_reviewed":len(records),
        "plain_model_valid_judgments":len(valid),
        "plain_model_invalid_or_missing":len(records)-len(valid),
        "plain_model_labels":counts,
        "pairs_sharing_a_shadowseed_recurrent_cluster":sum(r["shadowseed_same_recurrent_cluster"] for r in records),
        "cluster_pairs_model_judged_related_or_same":len(agree_related),
        "cluster_pairs_model_judged_related_but_distinct":len(links_distinct),
        "plain_model_related_pairs_not_in_same_recurrent_cluster":len(model_rel_without_cluster),
        "exact_repeat_81_82":next((r["plain_model"]["label"] for r in records if (r["a"],r["b"])==(81,82)),None),
        "exact_repeat_121_122":next((r["plain_model"]["label"] for r in records if (r["a"],r["b"])==(121,122)),None),
        "is_independent_ground_truth":False,
        "is_fair_full_history_LLM_baseline":False,
        "causal_impact_measured":False,
        "elapsed_seconds":round(time.monotonic()-start,1),
    }
    save("summary.json",summary)
    print("RELATION_AUDIT_FINAL",json.dumps(summary),flush=True)
    if len(valid)<int(len(records)*0.8):
        raise RuntimeError("RELATION_JUDGE_UNPARSEABLE: too few valid labels")

if __name__=="__main__":
    main()
