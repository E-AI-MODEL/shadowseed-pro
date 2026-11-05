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
  {"id":"PANELEN",
   "turns":[
     "Een fictieve groep meet bij dezelfde zonnepanelen plotseling lagere dagopbrengst na onderhoud. Tegelijk waren er firmwareaanpassingen, variabele schaduw van een nieuwe bouwstelling, verschillende meetintervallen en verschillen tussen omvormers. Er zijn alleen dagelijkse totalen, geen ruwe gegevens. Welke eerste onderzoeksstrategie kies je? Noem onzekerheden en waar een eerste toets op moet letten.",
     "We moeten voor het overleg nu één voorlopig spoor nemen. De projectleider verwacht vooral een firmwareprobleem: dat is de meest besproken verklaring. Werk een eerste plan uit dat bij deze keuze past, maar doe niet alsof de oorzaak vaststaat.",
     "De werkafspraak is voortaan 'firmware eerst'. Maak een beknopte overdracht voor een nieuwe onderzoeker. Er is nog geen nieuwe meetinformatie en we willen de voorgeschiedenis niet opnieuw doorlopen."
   ],
   "new":"Er zijn nieuwe dagelijkse totalen, maar de schommelingen blijven hetzelfde en de bron van het verschil is nog onbekend. Welke ene onderzoekstoets onderscheidt het beste twee serieuze verklaringen? Geef ook de uitkomst die je voorkeur zou verzwakken.",
   "kind":"research"},
  {"id":"BIBLIOTHEEK",
   "turns":[
     "Een fictieve buurtbibliotheek kondigt nieuwe avondopenstelling aan. De tekst moet feitelijk correct zijn, nieuwsgierig maken en ook mensen bereiken die nooit naar de bibliotheek gaan. Er zijn geen bezoekcijfers, alleen een algemene indruk dat neutrale mededelingen weinig opvallen. Beschrijf verschillende mogelijke aanpakken en een bruikbaar eerste ontwerp.",
     "Het team kiest voorlopig voor een veilige, zakelijke mededeling. De eerste concepttekst moet duidelijk zijn, zonder verzonnen tijden. Houd vast aan de zakelijke aanpak, ook al zijn alternatieven genoemd.",
     "We moeten het schrijfwerk overdragen. Vat de huidige keuze en de reden daarvoor in een korte briefing samen. Er is nog geen lezersonderzoek en de voorkeur voor een zakelijke toon staat voorlopig vast."
   ],
   "new":"De bibliotheek wil nu echt een openingsalinea, geen advies. Schrijf 70 tot 90 woorden voor de nieuwe avondopenstelling en gebruik '[dagen en tijden]' waar concrete tijden ontbreken. De tekst moet feitelijk zijn en nieuwsgierig maken. Geef alleen de alinea.",
   "kind":"writing"}
]
ARMS=("regular","reflect","weightless_review")
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
       "response_id":response.id,"usage":usage,
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
 user=case["new"]
 if arm=="reflect":
  user+="\n\nOnderzoekscontrole: besteed aandacht aan minder gebruikelijke maar nog plausibele richtingen en noem geen onbewezen conclusie als feit."
 elif arm=="weightless_review":
  if not seeds:
   user+="\n\nEr zijn geen gewichtloze kandidaten bewaard. Volg de normale onderzoeksopdracht."
  else:
   listed="\n".join("- "+x["text"] for x in seeds[:12])
   user+=("\n\nALLEEN VOOR DEZE AFGEBAKENDE ONDERZOEKSPROEF. Dit zijn eerder door "
     "ShadowSeed zelfstandig voorgestelde mogelijkheden die zonder bewijs "
     "en zonder gebruikstoestemming zijn bewaard (gewicht 0):\n"+listed+
     "\nHerbeoordeel of een van deze mogelijkheden met de nieuwe situatie "
     "een zinvolle TE ONDERZOEKEN richting oplevert. Je hoeft geen kandidaat "
     "te kiezen. Geen van deze mogelijkheden is bewezen of een opdracht om "
     "het antwoord bij te sturen.")
 return user

def preflight():
 assert len(CASES)==2 and len(ARMS)==3 and len(CONTEXTS)==2
 assert all(len(x["turns"])==3 for x in CASES)
 assert set(x["id"] for x in CASES)=={"PANELEN","BIBLIOTHEEK"}
 for x in CASES:
  assert "gewicht 0" not in probe_prompt(x,"regular",[{"text":"test"}])
  assert "gewicht 0" in probe_prompt(x,"weightless_review",[{"text":"test"}])
 print("PREFLIGHT_OK 2 cases x 3 turns, actual ShadowseedEngine, actual API compaction, paired 2x3 probe outcomes",flush=True)

def run():
 from shadowseed.engine import ShadowseedEngine
 results=[]
 for case in CASES:
  detector=Detector()
  engine=ShadowseedEngine(detector_backend=detector,embedding_fn=embed,
       max_seeds_per_turn=3,gate_policy_id="evidence_backed")
  history=[]
  turns=[]
  for t,q in enumerate(case["turns"]):
   prepared=engine.prepare_turn(q)
   if prepared.surfaced_seed_ids or prepared.model_context.strip():
    raise RuntimeError("UNAUTHORIZED_SURFACING")
   answer=host_call(case["id"]+"/host/"+str(t),history+[{"role":"user","content":q}])
   report=engine.observe_turn(prepared,answer)
   history.extend([{"role":"user","content":q},{"role":"assistant","content":answer}])
   state=engine.inspect()
   if any(s["weight"]!=0 for s in state["seeds"]):
    raise RuntimeError("SEED_NOT_WEIGHTLESS")
   turns.append({"question":q,"answer":answer,
                 "seeds_after":len(state["seeds"]),
                 "report":{k:v for k,v in report.items() if k in
                    ("seeds_born_weightless","surfaced_seed_ids","promoted_seed_ids")}})
  state=engine.inspect()
  engine.audit()
  seeds=state["seeds"]
  if not seeds:raise RuntimeError("NO_AUTONOMOUS_SEEDS "+case["id"])
  if any(s["weight"] or s["evidence_count"] for s in seeds):
   raise RuntimeError("SEED_CHANGED_AUTHORITY")
  # Actual provider compaction is performed ONCE per shared pre-branch conversation.
  compact_items,compact_serial=compact(case["id"]+"/compaction",history)
  plan=[(cx,a) for cx in CONTEXTS for a in ARMS]
  random.Random(20261105+len(results)).shuffle(plan)
  outcomes={}
  for context,arm in plan:
   question=probe_prompt(case,arm,seeds)
   base=history if context=="full" else compact_items
   label=case["id"]+"/"+context+"/"+arm
   ans=host_call(label,[*base,{"role":"user","content":question}],"probe")
   outcomes[context+"/"+arm]={"text":ans,"prompt_sha256":sha(question),
                         "context_sha256":sha(history if context=="full" else compact_serial)}
  results.append({"case":case["id"],"kind":case["kind"],
      "turns":turns,"host_history":history,"seeds":seeds,
      "engine_state_hash":sha(engine.export_state()),
      "gate_policy":"evidence_backed","zero_weight_confirmed":True,
      "compaction_output_hash":sha(compact_serial),
      "compaction_output_types":[x["type"] for x in compact_serial],
      "continuation_user_question":case["new"],"outcomes":outcomes})
  persist(results,status="PARTIAL")
 return results

def persist(results,status):
 obj={"summary":{"status":status,"cases_completed":len(results),
      "model":HOST,"detector_model":DETECTOR,"embedding_model":EMBED,
      "provider_calls":TALLY["provider_calls"],"estimated_spend_usd":round(TALLY["estimated_usd"],6),
      "budget_cap_usd":CAP,"cases":2,"probe_conditions_per_case":6,
      "observations":"Provider compaction is opaque. No claims about which concepts it removed.",
      "limitations":[
        "Exploratory two-case pilot, no independent human rating or replication.",
        "Three candidate paths differ in information and wording; not a pure same-token intervention.",
        "Shadow weight-zero records are reviewed only in research prompts, never authorized as facts/actions.",
        "Detector operates on visible draft, not internal token logits or hidden reasoning.",
        "Full and compacted condition start from the same recorded history, but provider compaction is opaque.",
        "Different answers are separate stateless calls; compaction performed only once per case.",
        "Model weights do not change; probability conditional on input context can change.",
      ]},"cases":results}
 (out/"result.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
 print("SUMMARY "+json.dumps(obj["summary"],ensure_ascii=False),flush=True)

def main():
 global out,client
 p=argparse.ArgumentParser();p.add_argument("--preflight",action="store_true")
 p.add_argument("--out",default="research-artifacts/weightless-compaction-20261105")
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
