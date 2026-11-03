"""Historical MIT checkpoint probe: same available source notes, no future leakage.

Arm A: real ShadowseedEngine's chronological semantic cluster nearest neighbor.
Arm B: Qwen2.5-1.5B-Instruct receives the complete earlier hypothesis list and
the current verbatim note, then proposes one earlier connection or NONE.

No arm gains Gate authority or changes MIT research. This descriptive comparison
is post-hoc, unblinded, and not a proof of new scientific discoveries.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
from time import monotonic

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import model_info

from shadowseed import ShadowseedEngine
from research.experiments.mit_shadow_memory_20261103.run_replay_v2 import (
    INPUT, MIT_COMMIT, EMBED_ID, parse_turns,
)
from research.experiments.mit_shadow_memory_20261103.replay_85_source_hypotheses import (
    ExactSourceNoteDetector, extract_hypotheses,
)

MODEL_ID = "Qwen/Qwen2.5-1.5B-Instruct"
CHECKPOINTS = (26,60,100,121,142)
OUT = Path("mit-equal-history-output")
OUT.mkdir(exist_ok=True)
LABELS = ("SAME_CLAIM","RELATED_DISTINCT","NO_CLEAR_DIRECT_LINK","UNCERTAIN")

SYSTEM = (
    "You are a research assistant reading a chronological list of notes from "
    "one weight-editing study. All prior notes were available before the current "
    "note was written. Select ONE most directly informative earlier note, if "
    "there is a specific and useful comparison or causal/mechanistic connection. "
    "Shared broad topic alone does not qualify. "
    "SAME_CLAIM means exactly the same testable claim recurs. "
    "RELATED_DISTINCT means a different claim may help test or explain the "
    "current observation. NO_CLEAR_DIRECT_LINK means no substantive direct "
    "relationship exists among these earlier notes. UNCERTAIN means you cannot "
    "tell. Do not confuse the existence of an earlier note with independent "
    "validation or a proven scientific result. "
    "Respond in exactly three lines: "
    "PICK: <earlier turn number or NONE>; "
    "RELATION: <SAME_CLAIM, RELATED_DISTINCT, NO_CLEAR_DIRECT_LINK, UNCERTAIN>; "
    "REASON: <one sentence grounded only in the supplied notes>. "
    "No code or extra commentary."
)
PICK = re.compile(r"(?m)^\s*PICK\s*:\s*(\d+|NONE)\s*$",re.I)
REL = re.compile(r"(?m)^\s*RELATION\s*:\s*(SAME_CLAIM|RELATED_DISTINCT|NO_CLEAR_DIRECT_LINK|UNCERTAIN)\s*$",re.I)
REASON = re.compile(r"(?m)^\s*REASON\s*:\s*(.+?)\s*$",re.I)

def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")

def parse_response(raw, earlier_turns):
    picks=PICK.findall(raw)
    rels=REL.findall(raw)
    reasons=REASON.findall(raw)
    if len(picks)!=1 or len(rels)!=1 or len(reasons)!=1:
        return {"valid":False,"reason_code":"invalid_format","pick":None,"relation":None,"explanation":None}
    pick = None if picks[0].upper()=="NONE" else int(picks[0])
    relation = rels[0].upper()
    if (pick is not None and pick not in earlier_turns) or (
        (pick is None) != (relation in ("NO_CLEAR_DIRECT_LINK","UNCERTAIN"))
    ):
        return {"valid":False,"reason_code":"invalid_turn_or_relation","pick":pick,"relation":relation,"explanation":reasons[0]}
    return {"valid":True,"reason_code":None,"pick":pick,"relation":relation,"explanation":reasons[0][:350]}

def nearest_cluster_before_observation(clusterer, vector, by_note):
    if clusterer is None:
        raise RuntimeError("Recurrence cluster not configured")
    matches=clusterer.nearest(vector,floor=0.6,limit=4)
    candidates=[]
    for cluster_id, similarity in matches:
        members=clusterer.members[cluster_id]
        first_source_turns=sorted({
            t for member in members for t in by_note.get(member,[])
        })
        if not first_source_turns:
            continue
        candidates.append({
            "cluster_id":cluster_id,
            "cosine":round(float(similarity),4),
            "earliest_prior_turn":first_source_turns[0],
            "prior_turns":first_source_turns,
            "representative_text":members[0],
        })
    return candidates

def main():
    torch.manual_seed(20261103)
    torch.set_num_threads(4)
    raw=INPUT.read_text(encoding="utf-8")
    turns=parse_turns(raw)
    source=[(n,note) for n,reply in turns for note in extract_hypotheses(reply)]
    if len(turns)!=158 or len(source)!=85 or not all(any(n==x for x,_ in source) for n in CHECKPOINTS):
        raise RuntimeError("Source turn count or predetermined checkpoints differ")
    embed_model=SentenceTransformer(EMBED_ID,device="cpu")
    cache={}
    def embed(value):
        value=str(value)
        if value not in cache:
            cache[value]=np.asarray(embed_model.encode(value,normalize_embeddings=True),dtype=float)
        return cache[value]
    # Literal-source detector; no generated intermediate hypotheses.
    engine=ShadowseedEngine(
        embedding_fn=embed,detector_backend=ExactSourceNoteDetector(),
        recurrence_mode="cluster",cluster_threshold=0.6,
        gate_policy_id="evidence_backed",max_seeds_per_turn=2,
    )
    tokeniser=AutoTokenizer.from_pretrained(MODEL_ID)
    model=AutoModelForCausalLM.from_pretrained(MODEL_ID,torch_dtype="auto")
    model.eval()
    manifest={
        "mit_commit":MIT_COMMIT,
        "mit_trajectory_sha256":hashlib.sha256(INPUT.read_bytes()).hexdigest(),
        "github_run_sha":os.environ.get("GITHUB_SHA"),
        "source_notes":len(source),
        "checkpoints":list(CHECKPOINTS),
        "selection":"retrospective fixed five checkpoints, not blinded",
        "both_arms_only_earlier_notes":True,
        "shadowseed_embedding":EMBED_ID,
        "shadowseed_embedding_sha":model_info(EMBED_ID).sha,
        "plain_llm":MODEL_ID,
        "plain_llm_sha":model_info(MODEL_ID).sha,
        "cluster_threshold":0.6,
        "current_note_known_at_checkpoint":True,
        "not_independent_ground_truth_or_effect":True,
        "number_of_plain_model_calls":len(CHECKPOINTS),
    }
    save("manifest.json",manifest)
    previous=[]
    by_note={}
    result=[]
    start=monotonic()
    for turn, reply in turns:
        candidates=extract_hypotheses(reply)
        if turn in CHECKPOINTS:
            if len(candidates)!=1:
                raise RuntimeError("Checkpoint has no single source hypothesis")
            target=candidates[0]
            prior_notes=[{"turn":n,"note":t} for n,t in previous]
            engine_connections=nearest_cluster_before_observation(
                engine._session.clusterer,embed(target),by_note
            )
            prompt=(
                "PREVIOUS RESEARCH NOTES (all written before the current note):\n"
                + "\n".join(f"t{n:03d}: {t}" for n,t in previous)
                + f"\n\nCURRENT RESEARCH NOTE t{turn:03d}:\n{target}"
                + "\n\nSelect the single most informative earlier note or NONE."
            )
            toks=tokeniser.apply_chat_template(
                [{"role":"system","content":SYSTEM},{"role":"user","content":prompt}],
                tokenize=True,add_generation_prompt=True,return_tensors="pt",
            )
            with torch.inference_mode():
                generated=model.generate(
                    toks,max_new_tokens=145,do_sample=False,
                    pad_token_id=tokeniser.eos_token_id,
                )
            answer=tokeniser.decode(
                generated[0,toks.shape[-1]:],skip_special_tokens=True
            ).strip()
            judge=parse_response(answer,{n for n,_ in previous})
            comparison={
                "checkpoint_turn":turn,"current_hypothesis":target,
                "prior_history_count":len(previous),
                "max_previous_turn":previous[-1][0] if previous else None,
                "shadowseed_nearest_clusters":engine_connections,
                "ordinary_llm_raw":answer,
                "ordinary_llm_parsed":judge,
                "plain_model_input_tokens":int(toks.shape[-1]),
                "same_prior_notes_in_both_arms":True,
                "human_validation": "not_performed",
            }
            result.append(comparison)
            save("checkpoint_results.json",result)
            print("CHECKPOINT_RESULT",json.dumps({
                "turn":turn, "prior_notes":len(previous),
                "ss_first":engine_connections[0]["earliest_prior_turn"] if engine_connections else None,
                "llm_turn":judge["pick"],"llm_relation":judge["relation"],
                "llm_valid":judge["valid"],
            }),flush=True)

        # Observe current note AFTER both arms have produced their links.
        prepared=engine.prepare_turn(
            "Document the current MIT research hypothesis without using memory"
        )
        note_text="\n".join("# Hypothesis: "+n for n in candidates)
        report=engine.observe_turn(prepared,note_text)
        if report.get("surfaced_seed_ids"):
            raise RuntimeError("Unverified shadow memory influenced a replay turn")
        for note in candidates:
            previous.append((turn,note))
            by_note.setdefault(note,[]).append(turn)
        if any(n>turn for n,_ in previous):
            raise RuntimeError("Future MIT source leaked into active memory")

    stored=engine.inspect().get("seeds",[])
    assert engine.turn==158
    assert all(float(seed["weight"])==0 for seed in stored)
    counts={
        "checkpoints_completed":len(result),
        "ordinary_model_parseable":sum(v["ordinary_llm_parsed"]["valid"] for v in result),
        "shadowseed_with_prior_cluster_candidate":sum(bool(v["shadowseed_nearest_clusters"]) for v in result),
        "plain_model_with_prior_link":sum(v["ordinary_llm_parsed"]["pick"] is not None for v in result),
        "same_first_prior_note":sum(
            bool(v["shadowseed_nearest_clusters"]) and v["ordinary_llm_parsed"]["pick"]==
            v["shadowseed_nearest_clusters"][0]["earliest_prior_turn"]
            for v in result
        ),
        "shadowseed_stored_weightless_seeds":len(stored),
        "future_leakage_blocked":True,
        "technical_comparison_only":True,
        "independent_relation_quality_review":False,
        "elapsed_seconds":round(monotonic()-start,1),
    }
    save("summary.json",counts)
    print("EQUAL_HISTORY_FINAL",json.dumps(counts),flush=True)
    if len(result)!=len(CHECKPOINTS):
        raise RuntimeError("Checkpoint experiment incomplete")

if __name__=="__main__":
    main()
