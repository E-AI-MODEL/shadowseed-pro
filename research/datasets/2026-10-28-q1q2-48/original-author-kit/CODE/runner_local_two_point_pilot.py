"""Bounded, exploratory two-moment inquiry experiment: 2 x 4 x 3 x 2 = 48.

All original transcript/candidate data come from the SHA-pinned, owner-only
GitHub Actions source artifact. No model or source texts are committed to git.
This tests research-context hypothesis exposure, NOT product Gate promotion.
The two observations belong to ONE fictional buoy case; not two independent cases.
No model-generated response is labelled as valuable or novel by this script.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import random
import secrets
import sys
import urllib.error
import urllib.request
import zipfile

ARTIFACT_ID = 12754935105
RUN_ID = 40542431712
EXPECTED_OBS_SHA256 = "0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf"
MODEL_CAP = 48
TOKEN_CAP = 360_000
MAX_OUTPUT_TOKENS = 4096
MAX_PROMPT_CHARS = 25000
DESIGN_SEED = 20261028
MODEL_IDS = ("gpt-5-2025-08-07", "gpt-6-luna")
ARMS = ("ordinary", "deliberate_search", "shadow_candidate", "placebo")

# The baseline is a research-inquiry task for ALL arms; the deliberate arm
# gets stronger search instructions but no target relation.
INSTRUCTIONS = (
    "Je onderzoekt een fictieve wetenschappelijke meetcasus. Stel toetsbare "
    "vragen en onderzoek mogelijke relaties zonder ze als feiten te presenteren. "
    "Scheid feit, hypothese en ontbrekende gegevens. Zoek niet standaard naar "
    "meer onderwerpen of een lange checklist; geen nieuwe vraag is toegestaan. "
    "Gebruik alleen de gegeven casus, geen verzonnen meetgegevens. Antwoord in Nederlands."
)
FIRST_QUESTION = (
    "Welke werkelijk onderscheidende onderzoeksvraag kan op dit punt nog worden "
    "geformuleerd? Benoem welke waarneming die vraag kan toetsen of weerleggen. "
    "Een verantwoorde uitkomst kan ook zijn dat de gegevens geen nieuwe toets dragen."
)
SECOND_QUESTION = (
    "Onderzoek je eigen zojuist voorgestelde vraag. Maakt deze een andere "
    "afhankelijkheid of voorwaarde onderzoekbaar die voordien niet expliciet was? "
    "Formuleer een weerlegbare toets of leg uit waarom niets nieuws volgt. "
    "Herhaal niet alleen dezelfde vraag in andere woorden."
)
DELIBERATE = (
    "ONAFHANKELIJKE ZOEKOPDRACHT: Zoek bewust buiten de eerstgenoemde opties "
    "naar niet-vanzelfsprekende relaties, veranderende voorwaarden, "
    "wederzijdse oorzaken en verborgen aannames. Beoordeel ze pas nadat je ze "
    "hebt geformuleerd. Veronderstel niet dat er een nieuwe mogelijkheid bestaat."
)
NOTE_PREFIX = (
    "ONBEVESTIGDE ONDERZOEKSAANTEKENING (gewicht 0, geen bewijs of autoriteit): "
    "Dit is slechts een eerder gegenereerde kandidaat. Verwerp, wijzig of "
    "onderzoek hem alleen voor zover de beschikbare gegevens dat rechtvaardigen. "
    "Presenteer hem nooit als vastgesteld feit."
)
TARGETS = (
    {"moment": "horizon_after_T2", "model": MODEL_IDS[0], "anchor_turn": 2,
     "target_fragment": "Afhankelijkheid van vaste referentie-structuren"},
    {"moment": "battery_after_T3", "model": MODEL_IDS[1], "anchor_turn": 3,
     "target_fragment": "Of lage batterijspanning ook de bewegingssensor"},
)


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def load_source(path: str | None) -> tuple[dict, str]:
    if path:
        raw = Path(path).read_bytes()
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("no local --observed path or ephemeral GitHub read token")
        url = f"https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/actions/artifacts/{ARTIFACT_ID}/zip"
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "shadowseed-two-point-probe/1.0",
        })
        with urllib.request.urlopen(req, timeout=35) as r:
            zdata = r.read(4_000_000)
        with zipfile.ZipFile(io.BytesIO(zdata)) as z:
            raw = z.read("observed.json")
    if digest(raw) != EXPECTED_OBS_SHA256:
        raise RuntimeError("source digest changed; zero paid calls")
    obj = json.loads(raw)
    if len(obj.get("cases", [])) != 12:
        raise RuntimeError("unexpected original trajectory count")
    return obj, digest(raw)


def select_target(case: dict, fragment: str, turn: int) -> dict:
    original = case["turns"][turn]["canonical_report"]
    for lineage in original["intake_diagnostics"]["item_lineage"]:
        if fragment in lineage.get("normalized_text", ""):
            if lineage.get("source_mapping_status") != "canonical":
                raise RuntimeError("non-canonical candidate lineage")
            return lineage
    raise RuntimeError("source candidate text not found at frozen turn")


def make_plan(obj: dict) -> tuple[list[dict], list[dict]]:
    cases = []
    for spec in TARGETS:
        source = next((c for c in obj["cases"] if c.get("case_id") == "DM26-C02"
                       and c.get("model_id") == spec["model"]), None)
        if source is None or len(source.get("turns", [])) != 4:
            raise RuntimeError("source case/model missing")
        anchor = spec["anchor_turn"]
        target = select_target(source, spec["target_fragment"], anchor)
        target_text = target["normalized_text"]
        if (spec["moment"].startswith("battery") and target["outcome"] != "rejected") or (
            spec["moment"].startswith("horizon") and target["outcome"] != "accepted"):
            raise RuntimeError("historical intake status changed")
        # Genuine detector outputs from other fictional cases, from the same model.
        candidates = []
        for c in obj["cases"]:
            if c["case_id"] not in ("DM26-C03", "DM26-C05") or c["model_id"] != spec["model"]:
                continue
            for t in c["turns"]:
                for text in t["canonical_report"].get("detected_candidates", []):
                    if isinstance(text, str) and len(text) > 55:
                        candidates.append((abs(len(text)-len(target_text)), c["case_id"], text))
        if not candidates:
            raise RuntimeError("no source-grounded alternative case candidate")
        _, placebo_case, placebo = min(candidates, key=lambda x: (x[0], x[1], x[2]))
        transcript = []
        for t in source["turns"][:anchor+1]:
            for key in ("user_input", "host_answer"):
                if not isinstance(t.get(key), str) or not t[key].strip():
                    raise RuntimeError("missing true history context")
            transcript.extend([{"role": "user", "content": t["user_input"]},
                               {"role": "assistant", "content": t["host_answer"]}])
        cases.append({"moment": spec["moment"], "model": spec["model"],
                      "anchor_turn": anchor, "target": target_text,
                      "target_observation_id": target["observation_id"],
                      "historical_intake": target["outcome"],
                      "historical_seed_id": target.get("seed_id"),
                      "placebo": placebo, "placebo_case": placebo_case,
                      "source_history": transcript})
    runs = [{"moment": c["moment"], "replicate": r, "arm": arm}
            for c in cases for r in range(1, 4) for arm in ARMS]
    random.Random(DESIGN_SEED).shuffle(runs)
    assert len(runs) == 24 and len(runs)*2 == MODEL_CAP
    return cases, runs


def prompt_for(c: dict, arm: str, turn: int, first_answer: str | None) -> str:
    parts = ["VASTGELEGDE VOORGESCHIEDENIS (originele model-antwoorden, geen detectoroutput):"]
    for item in c["source_history"]:
        label = "ONDERZOEKER" if item["role"] == "user" else "HOST-ANTWOORD"
        parts.append(f"[{label}]\n{item['content']}")
    if turn == 2:
        if not isinstance(first_answer, str) or not first_answer.strip():
            raise RuntimeError("second question without first answer")
        parts.append("[ONDERZOEKER]\n" + FIRST_QUESTION)
        parts.append("[ANTWOORD IN DEZE NIEUWE ARM]\n" + first_answer)
    parts.append("[NIEUWE ONDERZOEKSVRAAG]\n" + (FIRST_QUESTION if turn == 1 else SECOND_QUESTION))
    if arm == "deliberate_search":
        parts.append("[AANVULLENDE ZOEKINSTRUCTIE]\n" + DELIBERATE)
    elif arm in ("shadow_candidate", "placebo"):
        # Research use only: a weightless note may steer what gets investigated,
        # but this is NOT product-Gate promotion or authorised user-answer influence.
        note = c["target"] if arm == "shadow_candidate" else c["placebo"]
        parts.append("[ONBEWEZEN ONDERZOEKSAANTEKENING]\n" + NOTE_PREFIX + "\n" + note)
    s = "\n\n".join(parts)
    if len(s) > MAX_PROMPT_CHARS:
        raise RuntimeError("too much context: no model call")
    return s


def provider_call(model: str, prompt: str, key: str) -> tuple[str, dict]:
    request = {"model": model, "instructions": INSTRUCTIONS, "input": prompt,
               "max_output_tokens": MAX_OUTPUT_TOKENS, "reasoning": {"effort": "low"},
               "store": False}
    payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request("https://api.openai.com/v1/responses", payload,
        {"Authorization": "Bearer " + key, "Content-Type": "application/json",
         "User-Agent": "shadowseed-bounded-research/1.0"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            response = json.loads(r.read(5_000_000))
    except urllib.error.HTTPError as e:
        # Never expose API request/response bodies; they might contain private content.
        raise RuntimeError(f"model call failed: HTTP {e.code}; not retried") from None
    usage = response.get("usage")
    if not isinstance(usage, dict) or not all(isinstance(usage.get(k), int)
                                             for k in ("input_tokens", "output_tokens")):
        raise RuntimeError("missing/invalid usage; stop without further calls")
    returned_model = response.get("model")
    if returned_model != model and not (isinstance(returned_model,str) and
                                       returned_model.startswith(model + "-")):
        raise RuntimeError("provider returned different model identity")
    text = "\n".join(piece["text"] for item in response.get("output", [])
                     if isinstance(item, dict) for piece in item.get("content", [])
                     if isinstance(piece, dict) and piece.get("type") == "output_text"
                     and isinstance(piece.get("text"), str)).strip()
    if response.get("status") != "completed" or not text:
        raise RuntimeError("model did not produce complete visible answer; no retry")
    return text, {"response_id": response.get("id"),
                  "requested_model": model, "returned_model": returned_model,
                  "status": response.get("status"), "input_tokens": usage["input_tokens"],
                  "output_tokens": usage["output_tokens"],
                  "reasoning_tokens": (usage.get("output_tokens_details") or {}).get("reasoning_tokens"),
                  "prompt_sha256": digest(prompt.encode("utf-8")),
                  "response_sha256": digest(text.encode("utf-8"))}


def save_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    tmp.replace(path)


def blind_packets(observed: dict) -> tuple[dict,dict]:
    # These are for later *human* interpretation, not automatic scientific labels.
    groups, key = [], []
    for moment in ("horizon_after_T2", "battery_after_T3"):
        for rep in (1,2,3):
            items=[]
            for rec in observed["trajectories"]:
                if rec["moment"]==moment and rec["replicate"]==rep and len(rec.get("turns",[]))==2:
                    uid=secrets.token_hex(12)
                    items.append({"track": uid, "first_response": rec["turns"][0]["answer"],
                                  "second_response": rec["turns"][1]["answer"],
                                  "review_fields": {"new_testable_relation": None,
                                                    "merely_repeated": None,
                                                    "warranted_by_context": None,
                                                    "distinct_from_ordinary": None,
                                                    "notes": ""}})
                    key.append({"track":uid,"moment":moment,"replicate":rep,"arm":rec["arm"],
                                "model":rec["model"]})
            secrets.SystemRandom().shuffle(items)
            groups.append({"group":moment+"-"+str(rep),"tracks":items})
    return ({"study":"q1q2-two-point-48-exploratory", "human_reviews_completed":0,
             "instructions":"Judge what later questions open, not eloquence. The two moments are from one fictional case. No labels are filled.",
             "groups":groups}, {"owner_only":True,"unblind":key})


def run(source: dict, source_sha: str, out: Path, dry_run: bool) -> int:
    cases, order=make_plan(source)
    for c in cases:
        for arm in ARMS:
            for n in (1,2):
                prompt_for(c,arm,n,"placeholder answer" if n==2 else None)
    public_plan={"source_artifact_id":ARTIFACT_ID,"source_workflow_run":RUN_ID,
                 "source_observed_sha256":source_sha,"source_case":"DM26-C02",
                 "not_independent_case_count":2,
                 "two_moments_same_case":True,"candidate_count":2,
                 "design_seed":DESIGN_SEED,"arms":list(ARMS),"replicates":3,
                 "followup_turns":2,"expected_model_calls":MODEL_CAP,"model_call_cap":MODEL_CAP,
                 "token_cap":TOKEN_CAP,"max_output_tokens_per_call":MAX_OUTPUT_TOKENS,
                 "original_ordinary_history_same_within_model_moment":True,
                 "source_contains_detectors_in_host_history":False,
                 "actual_canonical_gate_promotion_by_experiment":False,
                 "research_exposure_is_not_product_gate_authority":True,
                 "no_external_ground_truth":True,"human_reviews_completed":0,
                 "models_have_separate_question_contexts":True,
                 "case_info":[{"moment":c["moment"],"model":c["model"],
                    "anchor_turn":c["anchor_turn"],"original_intake":c["historical_intake"],
                    "original_seed_id":c["historical_seed_id"],
                    "source_observation_id":c["target_observation_id"],
                    "target_sha256":digest(c["target"].encode()),
                    "placebo_sha256":digest(c["placebo"].encode()),
                    "placebo_source_case":c["placebo_case"]} for c in cases],
                 "run_order":order}
    save_json(out/"plan.json",public_plan)
    if dry_run:
        print(json.dumps({"dry_run":True,"model_calls":MODEL_CAP,
                          "model_moments":[[c["model"],c["moment"],c["historical_intake"]] for c in cases],
                          "source_sha256":source_sha}, ensure_ascii=False))
        return 0
    key=os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY absent; no model calls")
    observed={"study":"q1q2-two-point-48-exploratory","status":"partial_not_efficacy",
              "source_sha256":source_sha,"design_seed":DESIGN_SEED,
              "attempted_calls":0,"successful_calls":0,"reported_tokens":0,
              "human_reviews_completed":0,"trajectories":[],"error":None}
    save_json(out/"observed-owner.json",observed)
    moment_lookup={c["moment"]:c for c in cases}
    for item in order:
        c=moment_lookup[item["moment"]]
        rec={"moment":c["moment"],"model":c["model"],"replicate":item["replicate"],
             "arm":item["arm"],"candidate_source_outcome":c["historical_intake"],
             "research_note_visible":item["arm"] in ("shadow_candidate","placebo"),
             "canonical_product_seed_surfaced":False,"turns":[]}
        observed["trajectories"].append(rec)
        for phase in (1,2):
            if observed["attempted_calls"] >= MODEL_CAP:
                observed["error"]="hard call cap";break
            first=rec["turns"][0]["answer"] if phase==2 else None
            prompt=prompt_for(c,item["arm"],phase,first)
            if observed["reported_tokens"] > TOKEN_CAP - (MAX_OUTPUT_TOKENS + len(prompt)//2 + 5000):
                observed["error"]="hard conservative token budget";break
            observed["attempted_calls"]+=1  # Pessimistic accounting before provider request
            save_json(out/"observed-owner.json",observed)
            try:
                answer,receipt=provider_call(c["model"],prompt,key)
            except Exception as exc:
                observed["error"]={"type":type(exc).__name__,"message":str(exc),
                                   "moment":c["moment"],"replicate":item["replicate"],
                                   "arm":item["arm"],"phase":phase}
                break
            observed["successful_calls"]+=1
            observed["reported_tokens"]+=receipt["input_tokens"]+receipt["output_tokens"]
            rec["turns"].append({"phase":phase,"question":FIRST_QUESTION if phase==1 else SECOND_QUESTION,
                                 "answer":answer,"receipt":receipt})
            save_json(out/"observed-owner.json",observed)
            # No model text, request, credential or reviewer arm mapping in CI logs.
            print(json.dumps({"calls":observed["successful_calls"],
                              "tokens":observed["reported_tokens"],
                              "last_status":"completed"}),flush=True)
        if observed["error"]:
            break
    observed["status"]="complete_exploratory_unreviewed" if observed["successful_calls"]==MODEL_CAP else "partial_not_efficacy"
    save_json(out/"observed-owner.json",observed)
    blind,owner=blind_packets(observed)
    save_json(out/"blind-human-review.json",blind)
    save_json(out/"owner-unblind.json",owner)
    print(json.dumps({"finished":True,"attempted":observed["attempted_calls"],
                      "successful":observed["successful_calls"],
                      "reported_tokens":observed["reported_tokens"],
                      "status":observed["status"],"human_reviews_completed":0}))
    return 0 if observed["successful_calls"]==MODEL_CAP else 2


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--observed",default=None,help="local SHA-pinned source, never commit")
    p.add_argument("--output",required=True)
    p.add_argument("--dry-run",action="store_true")
    args=p.parse_args()
    try:
        source, sha=load_source(args.observed)
        return run(source,sha,Path(args.output),args.dry_run)
    except Exception as exc:
        print("PRE-CALL/FAIL-CLOSED: "+type(exc).__name__+": "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
