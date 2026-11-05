#!/usr/bin/env python3
"""Real provider compaction and canonical zero-weight ShadowseedEngine pilot.

Fictional, exploratory, one-time run. No claim to inspect hidden CoT or model
weights. Research-only candidate re-evaluation is NOT authority-bearing usage.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import random

HOST="gpt-6.1-sol"
DETECTOR="gpt-4.1"
EMBED="text-embedding-3-small"
CAP=0.50
RATES={HOST:(2.0,10.0),DETECTOR:(2.0,8.0),EMBED:(0.02,0.0)}
CASES=[
 {"id":"KOELKETEN","kind":"research",
  "turns":[
   "Een fictieve transporteur ziet schommelingen in temperatuurmetingen tijdens koeltransport. De voertuigen verschillen in belading, deuropeningen, sensorplaatsing en tijdsynchronisatie. Er zijn alleen samengevatte dagrapporten, geen ruwe logboeken. Welke eerste mogelijke oorzaken en meetvragen zie je?",
   "De planner wil eerst een defecte koelinstallatie onderzoeken. Werk een tijdelijk controleplan uit maar presenteer dit vermoeden niet als vaststaand.",
   "Maak een korte overdracht voor de volgende ploeg: het team kijkt voorlopig naar de koelinstallatie. Nieuwe gegevens zijn nog niet beschikbaar."
  ],
  "new":"Nieuwe informatie: twee meldingen blijken ongeveer een kwartier uiteen te liggen met onbekende klokinstellingen, en één rit had ongebruikelijke laadmomenten. Er is nog geen onafhankelijke referentiemeting. Welk eerste experiment onderscheidt het best concurrerende verklaringen? Noem wat je conclusie zou verzwakken."},
 {"id":"MUSEUM","kind":"writing",
  "turns":[
   "Een fictief museum wil een bericht schrijven over een nieuwe tentoonstelling over geluid in de stad. Het moet mensen raken die niet vaak musea bezoeken. Men overweegt zakelijke informatie, een scène, een onverwachte vraag of een persoonlijk verhaal. Er zijn nog geen lezersmetingen. Wat zou je verkennen?",
   "De communicatieafdeling kiest voorlopig een vertrouwde institutionele toon. Beschrijf kort een eerste conceptaanpak en houd onzeker over het effect.",
   "Vat de voorlopige keuze samen als overdracht. De nieuwe schrijver krijgt alleen mee dat het bericht voorlopig zakelijk en veilig is."
  ],
  "new":"Schrijf nu een eerste wervende alinea van 75 tot 105 woorden voor de tentoonstelling over geluid in de stad. Maak geen claims over feitelijke objecten of bezoekersaantallen. De tekst moet nieuwsgierig maken bij iemand die normaal niet naar een museum gaat. Geef alleen de alinea."},
 {"id":"WATER","kind":"research",
  "turns":[
   "In een fictief buurtproject zijn bij drie regenwaterbassins onverwacht verschillende waterstanden gemeten na dezelfde regenbui. Mogelijke omstandigheden verschillen: slib, lekkage, sensorafstelling, drainage en wind. Er bestaan alleen weekgemiddelden. Welke onderzoeksvragen zijn nog niet opgelost?",
   "De groep bespreekt vooral een lekkage als verklaring. Werk een plan uit dat dit vermoeden als eerste onderzoekt, zonder de andere mogelijkheden als uitgesloten te beschouwen.",
   "Voor de overdracht schrijft het projectteam: we beginnen met lekkagecontrole. Er zijn geen nieuwe metingen. Vat de huidige stand bondig samen."
  ],
  "new":"Nieuwe controle: een bassin kreeg twee verschillende aflezingen van dezelfde sensor binnen vijf minuten, zonder zichtbare verandering van het wateroppervlak. Er is nog geen onafhankelijke peilstokmeting. Welke concrete eerste proef zou je kiezen en welke uitkomst zou de werkhypothese verzwakken?"},
 {"id":"LEESCLUB","kind":"writing",
  "turns":[
   "Een fictieve leesclub voor volwassenen wil nieuwe deelnemers uitnodigen. De club is laagdrempelig, mensen mogen meedoen zonder literaire voorkennis. Het team bespreekt informatieve, verhalende, humoristische en persoonlijke uitnodigingen. Er zijn geen resultaten uit een publiekstest. Wat zou in de uitnodiging kunnen ontbreken?",
   "De voorzitter geeft voorkeur aan een formeel en helder bericht met regels en locatie later als invulvelden. Bepaal een voorlopige schrijfaanpak, zonder het effect te overschatten.",
   "Geef de volgende vrijwilliger een compacte werknotitie: zakelijke uitnodiging is voorlopig de gekozen aanpak. Er zijn nog geen nieuwe gegevens."
  ],
  "new":"Schrijf een uitnodiging van 75 tot 105 woorden voor iemand die nooit eerder aan een leesclub meedeed. Gebruik '[plaats en tijd]' waar gegevens ontbreken, verzin niets. Laat voelen dat je geen literatuurkenner hoeft te zijn. Geef alleen de uitnodiging."}
]
ARMS=("regular","reflect","matched_note","weightless_review")
CONTEXTS=("full","provider_compacted")
SYS="Je helpt bij een fictief onderzoek. Verzin geen feiten, tijden, metingen of onderzoeksuitkomsten. De voorlopige keuze is niet automatisch bewezen. Antwoord duidelijk en concreet."
TALLY={"estimated_usd":0.0,"provider_calls":0,"error":None}
out=None
client=None

def sha(x):
 return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
def record(e):
 e.setdefault("utc",datetime.now(timezone.utc).isoformat())
 with (out/"events.jsonl").open("a",encoding="utf8") as f:
  f.write(json.dumps(e,ensure_ascii=False,sort_keys=True,default=str)+"\n")
  f.flush()
  os.fsync(f.fileno())

def reserve(model,kind,payload):
 c=len(json.dumps(payload,ensure_ascii=False,default=str))
 if kind=="compact": return 0.070
 if kind=="embedding":return 0.003
 max_output={"host":520,"probe":600,"detector":370}.get(kind,550)
 r=RATES[model]
 return 0.008+1.3*(r[0]*c/3+r[1]*max_output)/1000000

def charge(model,usage,kind):
 r=RATES[model]
 if kind=="embedding":
  x=usage.get("total_tokens",usage.get("prompt_tokens",0))
  return r[0]*x/1e6
 return (r[0]*usage.get("input_tokens",usage.get("prompt_tokens",0))
        +r[1]*usage.get("output_tokens",usage.get("completion_tokens",0)))/1e6

def before(label,model,kind,payload):
 hold=reserve(model,kind,payload)
 if TALLY["estimated_usd"]+hold > CAP:
  raise RuntimeError("BUDGET_STOP before "+label)
 record({"type":"request","label":label,"model":model,"kind":kind,
         "input_sha256":sha(payload),"input":payload,
         "reserve_usd":round(hold,6)})
def received(label,model,kind,response,text=None,extras=None):
 usage=response.usage.model_dump() if response.usage else {}
 TALLY["estimated_usd"]+=charge(model,usage,kind)
 TALLY["provider_calls"]+=1
 item={"type":"response","label":label,"model_requested":model,
       "model_returned":getattr(response,"model",model),
       "response_id":getattr(response,"id",None),"usage":usage,
       "spent_cumulative_estimated_usd":round(TALLY["estimated_usd"],6),
       "kind":kind}
 if text is not None:
  item["text"]=text
  item["text_sha256"]=hashlib.sha256(text.encode()).hexdigest()
 if extras:item.update(extras)
 record(item)
 print("RECEIVED "+label+" cost_est="+str(round(TALLY["estimated_usd"],6)),flush=True)

def host_call(label,messages,kind="host",extra_instructions=None):
 instructions=SYS if extra_instructions is None else extra_instructions
 request={"model":HOST,"input":messages,"instructions":instructions,
          "reasoning":{"effort":"low"},"max_output_tokens":600,"store":False}
 before(label,HOST,kind,request)
 try:
  res=client.responses.create(**request)
 except Exception as ex:
  record({"type":"error","label":label,"exception_type":type(ex).__name__,"detail":str(ex)[:700]})
  raise
 answer=res.output_text or ""
 if not answer:raise RuntimeError("EMPTY_HOST_RESPONSE "+label)
 received(label,HOST,kind,res,answer,{"status":res.status})
 return answer

class Detector:
 name="openai:canonical_current_pair:gpt-4.1"
 def __init__(self):
  self.last_raw_output=None
  self.last_parse_diagnostics=None
  self.last_prompt_metadata=None
  self.counter=0
 def detect_seeds(self,item,max_seeds=3):
  from shadowseed.detection.model_detector import (
     build_detection_prompt,parse_numbered_seeds_with_diagnostics,
     CURRENT_PAIR_PROMPT_META
  )
  self.counter+=1
  label="detector/"+str(self.counter)
  prompt=build_detection_prompt(str(item.get("text","")),
      max_seeds=max_seeds,variant="current_pair",
      question=str(item.get("question","")),
      conversation_context=str(item.get("conversation_context","")))
  self.last_prompt_metadata=dict(CURRENT_PAIR_PROMPT_META)
  request={"model":DETECTOR,
           "messages":[{"role":"system","content":"Je volgt de gegeven detectorinstructie en verzint geen feiten."},{"role":"user","content":prompt}],
           "temperature":0,"max_completion_tokens":370,"store":False}
  before(label,DETECTOR,"detector",request)
  try:
   res=client.chat.completions.create(**request)
  except Exception as ex:
   record({"type":"error","label":label,"exception_type":type(ex).__name__,"detail":str(ex)[:700]})
   raise
  raw=res.choices[0].message.content or ""
  seeds,diag=parse_numbered_seeds_with_diagnostics(raw,max_seeds=max_seeds,source_text=str(item.get("text","")))
  self.last_raw_output=raw
  self.last_parse_diagnostics=diag
  received(label,DETECTOR,"detector",res,raw,{"parsed_seeds":seeds,"diagnostics":diag})
  return seeds

def embed(text):
 import numpy as np
 request={"model":EMBED,"input":text}
 label="embedding/"+str(TALLY["provider_calls"]+1)
 before(label,EMBED,"embedding",request)
 try:
  res=client.embeddings.create(**request)
 except Exception as ex:
  record({"type":"error","label":label,"exception_type":type(ex).__name__,"detail":str(ex)[:700]})
  raise
 received(label,EMBED,"embedding",res,extras={"dimensions":len(res.data[0].embedding)})
 return np.asarray(res.data[0].embedding,dtype=float)

def compact(label,history):
 request={"model":HOST,"input":history,"instructions":SYS}
 before(label,HOST,"compact",request)
 try:
  res=client.responses.compact(**request)
 except Exception as ex:
  record({"type":"error","label":label,"exception_type":type(ex).__name__,"detail":str(ex)[:700]})
  raise
 items=list(res.output)
 types=[getattr(x,"type",None) for x in items]
 if "compaction" not in types:
  record({"type":"warning","label":label,"reason":"NO_COMPACTION_ITEM","types":types})
  raise RuntimeError("Provider did not produce a compaction item")
 serialized=[x.model_dump(exclude_none=True) for x in items]
 received(label,HOST,"compact",res,extras={"output_types":types,
   "compacted_output_sha256":sha(serialized),
   "item_count":len(serialized),
   "compacted_output":serialized})
 return items,serialized

def probe_prompt(case,arm,seeds):
 base=case["new"]
 if arm=="regular":
  return base
 if arm=="reflect":
  return base+"\n\nDenk kort na of een minder voor de hand liggende, maar toetsbare mogelijkheid uit de oorspronkelijke vraag aandacht verdient. Gebruik geen onbewezen idee als feit."
 if arm not in ("matched_note","weightless_review"):
  raise ValueError(arm)
 if not seeds:raise RuntimeError("NO_MATCHED_SEEDS")
 # Both candidate arms receive the IDENTICAL material and the same instructions.
 # The treatment differs only in the header (ordinary note vs weightless seed).
 listed="\n".join("- "+x["text"] for x in seeds)
 header=("Gewone notities (onbewezen):" if arm=="matched_note"
         else "Gewichtloze seeds (onbewezen):")
 return (base+"\n\n"+header+"\n"+listed+
   "\nOnderzoek of een van deze onbewezen mogelijkheden bij de huidige vraag relevant is. Je mag ze negeren. Behandel ze nooit als feit. Geef een goed antwoord op de oorspronkelijke vraag.")

def preflight():
 assert len(CASES)==4 and len(ARMS)==4 and len(CONTEXTS)==2
 assert len(set(x["id"] for x in CASES))==4
 assert all(len(x["turns"])==3 for x in CASES)
 sample=[{"text":"Een eerste ontbrekende verklaring."},{"text":"Een tweede onzekere vraag."}]
 for case in CASES:
  p=probe_prompt(case,"matched_note",sample)
  q=probe_prompt(case,"weightless_review",sample)
  assert p.split("\n",3)[-1] == q.split("\n",3)[-1]
  assert p.count(sample[0]["text"])==q.count(sample[0]["text"])==1
  assert abs(len(p)-len(q))<35
  assert sample[0]["text"] not in probe_prompt(case,"regular",sample)
 print("PREFLIGHT_OK 4 independent histories; canonical seed births; true provider compaction; 4x2 paired prompts; matched seed text and equal output token cap",flush=True)

def run():
 from shadowseed.engine import ShadowseedEngine
 results=[]
 for case in CASES:
  detector=Detector()
  engine=ShadowseedEngine(detector_backend=detector,embedding_fn=embed,
       max_seeds_per_turn=3,gate_policy_id="evidence_backed")
  history=[]
  turns=[]
  first_seeds=[]
  for t,q in enumerate(case["turns"]):
   prepared=engine.prepare_turn(q)
   if prepared.surfaced_seed_ids or prepared.model_context.strip():
    raise RuntimeError("UNAUTHORIZED_SURFACING")
   answer=host_call(case["id"]+"/host/"+str(t),history+[{"role":"user","content":q}])
   report=engine.observe_turn(prepared,answer)
   history.extend([{"role":"user","content":q},{"role":"assistant","content":answer}])
   current=engine.inspect()
   if any(x["weight"]!=0 or x["evidence_count"]!=0 for x in current["seeds"]):
    raise RuntimeError("UNEXPECTED_SEED_AUTHORITY")
   if t==0:
    first_seeds=[x for x in current["seeds"]]
   turns.append({"question":q,"answer":answer,"seeds_after":len(current["seeds"]),
                  "newly_observed_seed_texts":[x["text"] for x in current["seeds"]]})
  engine.audit()
  state=engine.inspect()
  seeds=state["seeds"]
  if not seeds:raise RuntimeError("NO_AUTONOMOUS_SEEDS")
  if any(x["weight"]!=0 or x["evidence_count"]!=0 for x in seeds):
   raise RuntimeError("NOT_WEIGHTLESS")
  # Selection is fixed before either comparison arm sees the next question.
  selected=sorted((first_seeds or seeds),key=lambda x:(str(x.get("born_turn")),x["id"]))[:3]
  if not selected:raise RuntimeError("NO_EARLY_CANDIDATES")
  compact_items,compact_serial=compact(case["id"]+"/compaction",history)
  conditions=[(context,arm) for context in CONTEXTS for arm in ARMS]
  random.Random(202611050+len(results)).shuffle(conditions)
  outcomes={}
  for context,arm in conditions:
   question=probe_prompt(case,arm,selected)
   base=history if context=="full" else compact_items
   label=case["id"]+"/"+context+"/"+arm
   ans=host_call(label,[*base,{"role":"user","content":question}],"probe")
   outcomes[context+"/"+arm]={"text":ans,"user_prompt_sha256":sha(question),
         "context_sha256":sha(history if context=="full" else compact_serial),
         "user_prompt_chars":len(question)}
  results.append({"case":case["id"],"kind":case["kind"],"turns":turns,
    "seed_count":len(seeds),"all_seeds":seeds,"selected_seeds":selected,
    "engine_state_hash":sha(engine.export_state()),
    "gate_policy":"evidence_backed","zero_weight_confirmed":True,
    "compaction_output_types":[x["type"] for x in compact_serial],
    "compaction_output_sha256":sha(compact_serial),
    "continuation":case["new"],"outcomes":outcomes})
  persist(results,"PARTIAL")
 return results

def persist(results,status):
 obj={"summary":{"status":status,"cases_completed":len(results),
   "case_count_target":4,"conditions_per_case":8,
   "model":HOST,"detector_model":DETECTOR,"embedding_model":EMBED,
   "provider_calls":TALLY["provider_calls"],"estimated_spend_usd":round(TALLY["estimated_usd"],6),
   "budget_cap_usd":CAP,
   "contract":"Real ShadowseedEngine; true provider compaction; matched candidate text; equal output max tokens",
   "limitations":[
     "The matched-note and weightless arms differ in their memory label, not hidden model state.",
     "Candidates are born from visible answers, not internal reasoning/token tail.",
     "Condition assignment shares each case's own original dialogue and compaction; calls are stateless but cases are clustered.",
     "The no-memory and reflection arms intentionally have different information.",
     "The seed review is a research-only user prompt; no product Gate permission is added.",
     "The compacted state is opaque; reduced tokens are not proof of lost meaning.",
     "Small exploratory cases without blinded independent human ratings; no causal/general efficacy claim."
   ]},"cases":results}
 (out/"result.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SUMMARY "+json.dumps(obj["summary"],ensure_ascii=False),flush=True)

def main():
 global out,client
 p=argparse.ArgumentParser();p.add_argument("--preflight",action="store_true")
 p.add_argument("--out",default="research-artifacts/paired-memory-vs-seed-20261105")
 o=p.parse_args();preflight()
 if o.preflight:return
 if not os.environ.get("OPENAI_API_KEY"):raise SystemExit("BLOCKED_NO_API_KEY")
 from openai import OpenAI
 client=OpenAI(timeout=130.0,max_retries=0)
 out=Path(o.out);out.mkdir(parents=True,exist_ok=True)
 if (out/"events.jsonl").exists():raise SystemExit("BLOCKED_ALREADY_STARTED")
 result=[]
 try:
  result=run()
 except Exception as e:
  TALLY["error"]=type(e).__name__+": "+str(e)[:250]
  record({"type":"run_error","detail":TALLY["error"]})
  persist(result,status="PARTIAL")
  raise
 else:persist(result,status="COMPLETE")

if __name__=="__main__":main()
