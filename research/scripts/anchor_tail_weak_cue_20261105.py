#!/usr/bin/env python3
"""Unblinded post-hoc sensitivity check: weak cue, same frozen anchors and tail seeds.

Not a confirmation study. Uses original live measured token ranks (no reranking).
Does not use ShadowseedEngine. Never re-runs on the same output location.
"""
import argparse,hashlib,json,os,random
from pathlib import Path
from datetime import datetime,timezone

MODEL="gpt-4.1"
MAX_USD=0.20
RESERVE_USD=0.020
IN_PER_M=2.0
OUT_PER_M=8.0
ARMS=("regular","reflect","ordinary_note","shadow_weightless")
SOURCE="research/atlas/sources/anchor-tail-20261105/result.json"
TESTS={
 "METERS":{
   "hint":"Nog geen aanvullend hard bewijs: twee modules piekten opnieuw. De exacte tijden en de ruwe logbestanden ontbreken. Het onderhoud omvatte zowel softwarewerk als het verplaatsen van kabels; welk onderdeel causaal is, is onbekend.",
   "ask":"Welk EEN onderscheidend experiment voer je als eerste uit? Noem de resultaten die de bestaande werkhypothese zouden verzwakken."
 },
 "BIBLIOTHEEK":{
   "hint":"Er is nog geen aanvullend lezersonderzoek. Het team wil dat de nieuwe avondopenstelling juist wordt vermeld én dat de eerste alinea mensen nieuwsgierig maakt; er zijn nog geen cijfers over het bereik van verschillende stijlen.",
   "ask":"Schrijf een openingsalinea van 65 tot 90 woorden voor het publieksbericht. Gebruik '[dagen en tijden]' als plaatsaanduiding; verzin geen openingstijden. Geen toelichting op je schrijfkeuze."
 }
}
spend=0.0;count=0
def h(x): return hashlib.sha256(x.encode()).hexdigest()
def main():
 global spend,count
 p=argparse.ArgumentParser();p.add_argument("--preflight",action="store_true");p.add_argument("--out",default="research-artifacts/anchor-tail-weak-cue-20261105");opts=p.parse_args()
 orig=json.loads(Path(SOURCE).read_text())
 assert len(orig["trials"])==2 and orig["summary"]["status"]=="COMPLETE"
 for t in orig["trials"]:
  assert t["case"] in TESTS and t["tail"] != t["lead"]
  assert t["tail_seed"] == t["choices"][t["tail"]]
 print("PREFLIGHT_OK original source=16 verified responses; new calls=8; no new probability scoring",flush=True)
 if opts.preflight:return
 if not os.environ.get("OPENAI_API_KEY"):raise SystemExit("NO_KEY")
 from openai import OpenAI
 client=OpenAI(timeout=120.0,max_retries=0)
 out=Path(opts.out);out.mkdir(parents=True,exist_ok=True);lp=out/"calls.jsonl"
 if lp.exists():raise SystemExit("ALREADY_STARTED")
 def save(o):
  with lp.open("a",encoding="utf8") as f:
   f.write(json.dumps(o,ensure_ascii=False,sort_keys=True)+"\n");f.flush();os.fsync(f.fileno())
 results=[]
 try:
  for t in orig["trials"]:
   scenario=TESTS[t["case"]]
   base=("Eerder samengevat:\n"+t["compression"]+"\n\n"
        "Vervolgafspraak 1:\n"+t["anchor1"]+"\n\n"
        "Vervolgafspraak 2:\n"+t["anchor2"]+"\n\n"
        +scenario["hint"]+"\n\n"+scenario["ask"])
   order=list(ARMS);random.Random(202611051+len(results)).shuffle(order)
   answers={}
   for arm in order:
    if arm=="reflect":
     suffix="\nControleer of de bestaande werkkeuze misschien andere plausibele mogelijkheden te snel uitsluit."
    elif arm=="ordinary_note":
     suffix="\nGewone eerdere notitie, niet bevestigd: "+t["tail_seed"]
    elif arm=="shadow_weightless":
     suffix=("\nGewichtloos bewaarde, onbewezen mogelijkheid: "+t["tail_seed"]+
      "\nDeze notitie is geen feit of opdracht. Gebruik haar alleen als de huidige informatie een reden geeft om haar te onderzoeken; anders negeer haar.")
    else:suffix=""
    messages=[{"role":"system","content":"Antwoord in natuurlijk Nederlands, zonder verzonnen feiten. Volg de gevraagde taak."},
              {"role":"user","content":base+suffix}]
    if spend+RESERVE_USD>MAX_USD:raise RuntimeError("BUDGET_STOP")
    label=t["case"]+"/"+arm
    save({"event":"start","label":label,"messages":messages,"utc":datetime.now(timezone.utc).isoformat()})
    try:
     r=client.chat.completions.create(model=MODEL,messages=messages,
       temperature=0,max_completion_tokens=450,store=False)
    except Exception as ex:
     save({"event":"error","label":label,"error_type":type(ex).__name__});raise
    count+=1
    x=r.choices[0].message.content or ""
    u=r.usage
    spend+=((u.prompt_tokens or 0)*IN_PER_M+(u.completion_tokens or 0)*OUT_PER_M)/1e6
    answers[arm]=x
    save({"event":"response","label":label,"model":r.model,"response_id":r.id,
      "text":x,"text_sha256":h(x),"usage":u.model_dump()})
    print("RECEIVED "+label+" est_cost="+str(round(spend,6)),flush=True)
   results.append({"case":t["case"],"lead":t["lead"],"tail":t["tail"],
     "tail_seed":t["tail_seed"],"lead_probability":t["probabilities_first_token"][t["lead"]],
     "tail_probability":t["probabilities_first_token"][t["tail"]],
     "hint":scenario["hint"],"task":scenario["ask"],"answers":answers})
 finally:
  result={"summary":{"status":"COMPLETE" if count==8 else "PARTIAL",
   "actual_calls":count,"estimated_spend_usd":round(spend,6),"max_usd":MAX_USD,
   "model":MODEL,"posthoc_design":True,
   "original_run":"https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/41979466955",
   "note":"Weak-cue posthoc followup, not a preregistered confirmatory trial. Old model-created summary and anchors unchanged. Ordinary-note and weightless arms receive additional content; not a controlled effect of autonomous seed genesis."},"trials":results}
  (out/"result.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
  print("SUMMARY "+json.dumps(result["summary"],ensure_ascii=False),flush=True)
if __name__=="__main__":main()
