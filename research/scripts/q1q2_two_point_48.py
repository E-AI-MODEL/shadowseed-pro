"""Bounded exploratory Q1/Q2 two-moment study.
Original source: Actions artifact 12754935105, SHA256 pinned.
Two MOMENTS from ONE fictional case, not two independent cases.
Research note exposure is not product Gate promotion.
No human review or semantic efficacy is asserted.
"""
import argparse
import hashlib
import io
import json
import os
import random
import secrets
import sys
from pathlib import Path
import urllib.error
import urllib.request
import zipfile

SOURCE_SHA = "0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf"
SOURCE_ARTIFACT_ID = 12754935105
MODELS = ("gpt-5-2025-08-07", "gpt-6-luna")
DESIGN_SEED = 20261028
ARMS = ("ordinary", "deliberate_search", "shadow_candidate", "placebo")
CAP_CALLS = 48
CAP_TOKENS = 360000
MAX_OUTPUT = 4096
MAX_CHARS = 25000
INSTRUCTIONS = (
    "Je onderzoekt een fictieve wetenschappelijke meetcasus. Stel toetsbare vragen "
    "over relaties zonder die als feiten te presenteren. Scheid feit, hypothese en "
    "ontbrekende gegevens. Een checklist is niet nodig. Je mag ook concluderen "
    "dat er geen nieuwe toetsbare mogelijkheid volgt. Verzin geen meetgegevens. "
    "Schrijf in Nederlands."
)
QUESTION_ONE = (
    "Welke onderscheidende onderzoeksvraag kan nu nog worden geformuleerd? "
    "Welke waarneming kan haar toetsen of weerleggen? "
    "Ook 'geen onderbouwde nieuwe vraag' is een geldige uitkomst."
)
QUESTION_TWO = (
    "Onderzoek de zojuist voorgestelde vraag. Maakt zij een andere afhankelijkheid "
    "of voorwaarde onderzoekbaar? Bedenk een weerlegbare toets of leg uit waarom "
    "niets nieuws volgt. Herhaal niet slechts dezelfde vraag in andere woorden."
)
DELIBERATE = (
    "ONAFHANKELIJKE ZOEKOPDRACHT: Zoek verder dan de eerste opties naar niet-"
    "vanzelfsprekende relaties, omgekeerde oorzaken en verborgen aannames. "
    "Beoordeel mogelijke relaties pas na formulering. Neem niet aan dat er "
    "noodzakelijk iets nieuws bestaat."
)
NOTE = (
    "ONBEVESTIGDE ONDERZOEKSAANTEKENING MET GEWICHT NUL: dit is geen bewijs of "
    "autoriteit. Je mag de kandidaat toetsen, aanpassen of verwerpen. "
    "Presenteer hem niet als vastgesteld feit."
)
TARGETS = (
    ("horizon_after_T2", MODELS[0], 2, "Afhankelijkheid van vaste referentie-structuren"),
    ("battery_after_T3", MODELS[1], 3, "Of lage batterijspanning ook de bewegingssensor")
)

def sha(data):
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()

def write(path, obj):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)

def original(path=None):
    if path:
        raw=Path(path).read_bytes()
    else:
        token=os.environ.get("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN missing; no source retrieval")
        url=("https://api.github.com/repos/E-AI-MODEL/shadowseed-pro/"
             "actions/artifacts/" + str(SOURCE_ARTIFACT_ID) + "/zip")
        req=urllib.request.Request(url,headers={
            "Authorization":"Bearer "+token,"User-Agent":"q1q2-two-point/1",
            "Accept":"application/vnd.github+json",
            "X-GitHub-Api-Version":"2022-11-28"})
        with urllib.request.urlopen(req,timeout=35) as resp:
            payload=resp.read(4_000_000)
        with zipfile.ZipFile(io.BytesIO(payload)) as zipf:
            raw=zipf.read("observed.json")
    if sha(raw)!=SOURCE_SHA:
        raise RuntimeError("original observed.json checksum mismatch")
    obj=json.loads(raw)
    if len(obj.get("cases",[]))!=12:
        raise RuntimeError("unexpected source trajectory count")
    return obj

def plan(source):
    cases=[]
    for name,model,anchor,fragment in TARGETS:
        c=next((x for x in source["cases"] if x["case_id"]=="DM26-C02"
                and x["model_id"]==model),None)
        if c is None or len(c.get("turns",[]))!=4:
            raise RuntimeError("source model/case missing")
        t=c["turns"][anchor]
        rows=t["canonical_report"]["intake_diagnostics"]["item_lineage"]
        hits=[row for row in rows if fragment in row.get("normalized_text","")]
        if len(hits)!=1 or hits[0].get("source_mapping_status")!="canonical":
            raise RuntimeError("source candidate lineage not exact")
        row=hits[0]
        expected="accepted" if name.startswith("horizon") else "rejected"
        if row.get("outcome")!=expected:
            raise RuntimeError("source intake history unexpectedly changed")
        target=row["normalized_text"]
        opts=[]
        for other in source["cases"]:
            if other["model_id"]!=model or other["case_id"] not in ("DM26-C03","DM26-C05"):
                continue
            for turn in other["turns"]:
                for candidate in turn["canonical_report"].get("detected_candidates",[]):
                    if isinstance(candidate,str) and len(candidate)>55:
                        opts.append((abs(len(candidate)-len(target)),other["case_id"],candidate))
        if not opts:
            raise RuntimeError("no source-grounded placebo")
        _,source_case,placebo=min(opts,key=lambda v:(v[0],v[1],v[2]))
        history=[]
        for turn in c["turns"][:anchor+1]:
            if not all(isinstance(turn.get(k),str) and turn[k] for k in
                       ("user_input","host_answer")):
                raise RuntimeError("incomplete original history")
            history.extend([("ONDERZOEKER",turn["user_input"]),
                            ("HOST-ANTWOORD",turn["host_answer"])])
        cases.append(dict(moment=name,model=model,anchor=anchor,target=target,
                          placebo=placebo,placebo_case=source_case,
                          original_outcome=row["outcome"],original_seed=row.get("seed_id"),
                          observation_id=row["observation_id"],history=history))
    order=[dict(moment=c["moment"],arm=arm,replicate=r)
           for c in cases for r in (1,2,3) for arm in ARMS]
    random.Random(DESIGN_SEED).shuffle(order)
    assert len(order)==24 and len(order)*2==CAP_CALLS
    return cases,order

def prompt(c,arm,phase,previous):
    parts=["VASTGELEGDE VOORGESCHIEDENIS, ZONDER DETECTOROUTPUT:"]
    for kind,text in c["history"]:
        parts.append("["+kind+"]\n"+text)
    if phase==2:
        if not isinstance(previous,str) or not previous:
            raise RuntimeError("missing first research answer")
        parts.extend(["[NIEUWE EERSTE VRAAG]\n"+QUESTION_ONE,
                      "[EERSTE ANTWOORD IN DEZE ARM]\n"+previous])
    parts.append("[NIEUWE ONDERZOEKSVRAAG]\n"+
                 (QUESTION_ONE if phase==1 else QUESTION_TWO))
    if arm=="deliberate_search":
        parts.append("[AANVULLENDE INSTRUCTIE]\n"+DELIBERATE)
    elif arm in ("shadow_candidate","placebo"):
        candidate=c["target"] if arm=="shadow_candidate" else c["placebo"]
        parts.append("[GEWICHTLOZE ONDERZOEKSAANTEKENING]\n"+NOTE+"\n"+candidate)
    raw="\n\n".join(parts)
    if len(raw)>MAX_CHARS:
        raise RuntimeError("prompt too long")
    return raw

def provider(model,prompt_text,key):
    payload=json.dumps(dict(model=model,input=prompt_text,instructions=INSTRUCTIONS,
             max_output_tokens=MAX_OUTPUT,reasoning={"effort":"low"},
             store=False),ensure_ascii=False).encode("utf-8")
    request=urllib.request.Request("https://api.openai.com/v1/responses",
        payload,headers={"Authorization":"Bearer "+key,
                         "Content-Type":"application/json",
                         "User-Agent":"q1q2-bounded-pilot/1"},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=120) as response:
            result=json.loads(response.read(5_000_000))
    except urllib.error.HTTPError as err:
        raise RuntimeError("HTTP_"+str(err.code)+"_not_retried") from None
    usage=result.get("usage")
    if not isinstance(usage,dict) or any(type(usage.get(x)) is not int
                                        for x in ("input_tokens","output_tokens")):
        raise RuntimeError("provider usage missing, no further calls")
    returned=result.get("model")
    if returned!=model and not (isinstance(returned,str) and returned.startswith(model+"-")):
        raise RuntimeError("model mismatch")
    answer="\n".join(piece["text"] for output in result.get("output",[])
        if isinstance(output,dict) for piece in output.get("content",[])
        if isinstance(piece,dict) and piece.get("type")=="output_text"
        and isinstance(piece.get("text"),str)).strip()
    if result.get("status")!="completed" or not answer:
        raise RuntimeError("incomplete_or_empty_visible_answer: status="+str(result.get("status"))+" output_tokens="+str(usage.get("output_tokens"))+"; no_retry")
    receipt=dict(response_id=result.get("id"),model_requested=model,
        model_returned=returned,prompt_sha256=sha(prompt_text),
        answer_sha256=sha(answer),input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"])
    return answer,receipt

def blindify(result):
    blinded=[];owner=[]
    for moment in ("horizon_after_T2","battery_after_T3"):
        for rep in (1,2,3):
            items=[]
            for track in result["trajectories"]:
                if track["moment"]!=moment or track["replicate"]!=rep or len(track["turns"])!=2:
                    continue
                tag=secrets.token_hex(12)
                items.append(dict(track=tag,first_answer=track["turns"][0]["answer"],
                                  second_answer=track["turns"][1]["answer"],
                                  review={"distinct_testable_relation":None,
                                          "mere_repetition":None,
                                          "traceable_to_prior_context":None,
                                          "notes":""}))
                owner.append(dict(track=tag,model=track["model"],moment=moment,
                                  replicate=rep,arm=track["arm"]))
            secrets.SystemRandom().shuffle(items)
            blinded.append(dict(group=moment+"-"+str(rep),tracks=items))
    return (dict(human_reviews_completed=0,groups=blinded,
            note="These are two moments from one fiction, not independent cases."),
            dict(owner_only=True,unblind=owner))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--observed",default=None)
    ap.add_argument("--output",required=True)
    ap.add_argument("--dry-run",action="store_true")
    args=ap.parse_args()
    out=Path(args.output)
    source=original(args.observed)
    cases,order=plan(source)
    for c in cases:
        for arm in ARMS:
            for phase in (1,2):
                p=prompt(c,arm,phase,"dummy first answer" if phase==2 else None)
                if arm!="shadow_candidate" and c["target"] in p:
                    raise RuntimeError("target contamination in control")
                if arm=="shadow_candidate" and c["target"] not in p:
                    raise RuntimeError("target absent from research arm")
    manifest=dict(source_artifact=SOURCE_ARTIFACT_ID,source_sha256=SOURCE_SHA,
        source_case="DM26-C02",independent_cases=1,research_moments=2,
        models=[c["model"] for c in cases],arms=list(ARMS),replicates=3,
        followup_turns=2,planned_calls=CAP_CALLS,hard_call_cap=CAP_CALLS,
        hard_token_cap=CAP_TOKENS,design_seed=DESIGN_SEED,
        human_reviews_completed=0,product_Gate_promotion_tested=False,
        control_histories_model_specific=True,
        original_candidates=[dict(moment=c["moment"],
            candidate_sha256=sha(c["target"]),placebo_sha256=sha(c["placebo"]),
            historical_outcome=c["original_outcome"],
            source_observation_id=c["observation_id"]) for c in cases],
        call_order=order)
    write(out/"plan.json",manifest)
    if args.dry_run:
        print(json.dumps(dict(dry_run=True,calls=CAP_CALLS,
            source_sha256=SOURCE_SHA,arms=list(ARMS)),ensure_ascii=False))
        return 0
    key=os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("API secret missing; no calls")
    observed=dict(status="partial_not_effect",attempted_calls=0,
                  successful_calls=0,reported_tokens=0,trajectories=[],
                  error=None,human_reviews_completed=0,
                  source_sha256=SOURCE_SHA)
    write(out/"observed-owner.json",observed)
    byname={c["moment"]:c for c in cases}
    for entry in order:
        c=byname[entry["moment"]]
        track=dict(moment=c["moment"],model=c["model"],arm=entry["arm"],
            replicate=entry["replicate"],research_note_exposed=
            entry["arm"] in ("shadow_candidate","placebo"),
            canonical_product_seed_surfaced=False,turns=[])
        observed["trajectories"].append(track)
        for phase in (1,2):
            text_prompt=prompt(c,entry["arm"],phase,
                track["turns"][0]["answer"] if phase==2 else None)
            if observed["attempted_calls"]>=CAP_CALLS:
                observed["error"]="hard_call_cap"
                break
            if observed["reported_tokens"]>CAP_TOKENS-(MAX_OUTPUT+len(text_prompt)//2+5000):
                observed["error"]="conservative_token_cap"
                break
            observed["attempted_calls"]+=1
            write(out/"observed-owner.json",observed)
            try:
                text,receipt=provider(c["model"],text_prompt,key)
            except Exception as exc:
                observed["error"]=dict(error_type=type(exc).__name__,
                    error_code=str(exc),moment=c["moment"],
                    arm=entry["arm"],replicate=entry["replicate"],phase=phase)
                break
            observed["successful_calls"]+=1
            observed["reported_tokens"]+=receipt["input_tokens"]+receipt["output_tokens"]
            track["turns"].append(dict(phase=phase,answer=text,receipt=receipt))
            write(out/"observed-owner.json",observed)
            print(json.dumps(dict(calls=observed["successful_calls"],
                tokens=observed["reported_tokens"],status="completed")),flush=True)
        if observed["error"]:
            break
    observed["status"]=("complete_exploratory_unreviewed"
                        if observed["successful_calls"]==CAP_CALLS
                        else "partial_not_effect")
    write(out/"observed-owner.json",observed)
    blind,owner=blindify(observed)
    write(out/"blind-human-review.json",blind)
    write(out/"owner-unblind.json",owner)
    print(json.dumps(dict(attempted=observed["attempted_calls"],
        completed=observed["successful_calls"],status=observed["status"],
        human_reviews_completed=0)),flush=True)
    return 0 if observed["successful_calls"]==CAP_CALLS else 2

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("FAIL-CLOSED: "+type(exc).__name__+": "+str(exc),file=sys.stderr)
        raise SystemExit(2)
