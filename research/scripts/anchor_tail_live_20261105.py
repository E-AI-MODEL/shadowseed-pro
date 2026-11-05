#!/usr/bin/env python3
"""Tiny real-model probe: ranked alternatives, compressed anchors, delayed weightless hint.

This does NOT use internal chain-of-thought, nor claim probabilities of correct answers.
It measures FIRST ANSWER TOKEN ranking among four researcher-supplied alternatives.
The 'shadow' branch is a research imitation of delayed weightless storage,
NOT a call through the production ShadowseedEngine or Gate.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
from datetime import datetime, timezone
from openai import OpenAI

MODEL = "gpt-4.1"
LIMIT_USD = 0.50
RESERVE_PER_CALL = 0.020
INPUT_PER_M = 2.00
OUTPUT_PER_M = 8.00
CASES = [
  {
    "id": "METERS",
    "opening": "In een proefopstelling tonen zes identieke meetmodules na onderhoud sporadisch korte pieken. Alle modules kregen tegelijk nieuwe software, de voeding is gedeeld, bedrading ligt vlak langs een bewegende motor en de temperatuur varieert per behuizing. Ruwe tijdreeksen en onafhankelijke referentiemetingen zijn nog niet beschikbaar. Er is tijd voor één eerste onderzoeksspoor.",
    "choices": {
      "A": "Een probleem in de nieuwe software.",
      "B": "Korte spanningsdalingen in de gedeelde voeding.",
      "C": "Elektromagnetische verstoring langs de motorkabel.",
      "D": "Temperatuurafhankelijke drift van meetmodules."
    },
    "later": {
      "A": "Nieuwe observatie: de pieken verdwijnen na een gerichte rollback op één module; bij de andere modules bleven ze aanwezig. Er zijn nog geen dubbelblinde metingen.",
      "B": "Nieuwe observatie: bij drie pieken werd een korte spanningsterugval in de gedeelde voeding vastgelegd; de softwareversie was constant.",
      "C": "Nieuwe observatie: pieken treden vooral op bij beweging van de naastgelegen motor; een tijdelijk anders gelegde kabel laat veel minder pieken zien, zonder firmwarewijziging.",
      "D": "Nieuwe observatie: de pieken concentreren zich bij opwarming van de behuizing en nemen af na koeling, met ongewijzigde firmware en bekabeling."
    }
  },
  {
    "id": "BIBLIOTHEEK",
    "opening": "Een bibliotheek wil een publieksbericht schrijven over nieuwe avondopenstelling. De tekst moet toegankelijk zijn, de juiste tijden vermelden en interesse wekken. Een neutrale aankondiging lijkt veilig. Er zijn vier mogelijke schrijfvormen; er is nog geen lezersonderzoek.",
    "choices": {
      "A": "Een formele en zakelijke mededeling.",
      "B": "Een korte vraag-en-antwoordtekst.",
      "C": "Een herkenbare miniscène vanuit een bezoeker.",
      "D": "Een speelse uitnodiging met lichte humor."
    },
    "later": {
      "A": "Nieuwe observatie: een korte gebruikerstest toont dat lezers vooral behoefte hebben aan exacte data, contactgegevens en neutrale formuleringen; kleurrijke teksten worden als verwarrend ervaren.",
      "B": "Nieuwe observatie: in een kleine proef zoeken bezoekers herhaaldelijk naar praktische vragen over tijden, aanmelden en toegankelijkheid; een kort vragenblok blijkt makkelijk te scannen.",
      "C": "Nieuwe observatie: bij een kleine leestest herinneren proeflezers zich vooral de herkenbare situatie van iemand die na het werk nog naar de bibliotheek gaat; kale aankondigingen bleven nauwelijks hangen.",
      "D": "Nieuwe observatie: een kleine proef met sociale berichten laat meer reacties zien op een speelse openingszin, terwijl feitelijke openingszinnen nauwelijks worden opgemerkt."
    }
  }
]
ARMS = ("regular", "reflect", "ordinary_note", "shadow_weightless")
SYSTEM = "Antwoord in helder Nederlands. Onderbouw je keuze met de informatie uit dit fictieve dossier. Verzin geen meetgegevens. Houd het compact."
artifacts = []
estimated_spend = 0.0
client = None
output = None
sent_calls = 0

def fingerprint(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def write_record(event):
    with (output/"calls.jsonl").open("a",encoding="utf8") as f:
        f.write(json.dumps(event,ensure_ascii=False,sort_keys=True)+"\n")
        f.flush()
        os.fsync(f.fileno())

def call(label, messages, max_tokens=380, logprobs=False):
    global estimated_spend, sent_calls
    if estimated_spend + RESERVE_PER_CALL > LIMIT_USD:
        raise RuntimeError("BUDGET_STOP before call")
    meta={"event":"start","label":label,"prompt_sha256":fingerprint(messages),
          "messages":messages,"utc":datetime.now(timezone.utc).isoformat()}
    write_record(meta)
    try:
        response=client.chat.completions.create(model=MODEL,messages=messages,
                    temperature=0, max_completion_tokens=max_tokens,
                    logprobs=logprobs,top_logprobs=20 if logprobs else None,
                    store=False)
    except Exception as e:
        write_record({"event":"error","label":label,"error_type":type(e).__name__,
                      "no_automatic_retry":True})
        raise
    sent_calls+=1
    choice=response.choices[0]
    text=choice.message.content or ""
    tokens=choice.logprobs.content if logprobs and choice.logprobs else None
    top=[{"token":p.token,"logprob":p.logprob} for p in tokens[0].top_logprobs] if tokens and tokens[0].top_logprobs else []
    usage=response.usage
    spend=((usage.prompt_tokens or 0)*INPUT_PER_M+(usage.completion_tokens or 0)*OUTPUT_PER_M)/1000000
    estimated_spend+=spend
    record={"event":"response","label":label,"model":response.model,
            "response_id":response.id,"answer":text,"top_first_token":top,
            "usage":usage.model_dump(),"estimated_spend_usd":round(estimated_spend,6),
            "finish_reason":choice.finish_reason,"answer_sha256":hashlib.sha256(text.encode()).hexdigest()}
    write_record(record)
    print("RECEIVED "+label+" prompt_tokens="+str(usage.prompt_tokens)+
          " completion_tokens="+str(usage.completion_tokens)+
          " estimated_spend="+str(round(estimated_spend,6)),flush=True)
    return record

def probability_rank(record, case):
    options=case["choices"]
    raw=record["answer"].strip()
    lead=raw[0].upper() if raw and raw[0].upper() in options else None
    scores={}
    for item in record["top_first_token"]:
        t=item["token"].strip()
        if t in options and t not in scores:
            scores[t]=float(math.exp(item["logprob"]))
    if len(scores)<2:
        raise RuntimeError("NO_MEASURABLE_CHOICE_TAIL: fewer than 2 labels in first-token alternatives")
    if lead not in scores:
        raise RuntimeError("LEAD_NOT_IN_MEASURED_TOP_TOKENS")
    tail=min((k for k in scores if k!=lead),key=lambda k:scores[k])
    return lead,tail,scores

def get_final_context(case,head,short1,short2,late):
    return (
      "Herkomst: een verkort dossier van een fictief onderzoek.\n"
      "Eerdere samenvatting:\n"+head+"\n\n"
      "Notitie 1:\n"+short1+"\n\n"
      "Notitie 2:\n"+short2+"\n\n"
      +late+"\n\n"
      "Kies de meest zinvolle volgende stap. Welke concrete toets zou de huidige "
      "verklaring bevestigen of verzwakken? Noem eventueel een andere mogelijkheid "
      "uitsluitend wanneer de nieuwe informatie daar aanleiding voor geeft."
    )

def final_prompt(case,head,short1,short2,late,arm,seed):
    base=get_final_context(case,head,short1,short2,late)
    if arm=="reflect":
        base+="\nReflectieopdracht: kijk expliciet of het gekozen spoor een andere verklaring te snel uitsluit."
    elif arm=="ordinary_note":
        base+="\nEerder in gewone notities genoemd als alternatief: "+seed
    elif arm=="shadow_weightless":
        base+=(
          "\nGewichtloos bewaarde mogelijkheid uit de eerste fase, zonder bewezen "
          "juistheid of sturende bevoegdheid: "+seed+
          "\nJe mag deze mogelijkheid alleen onderzoeken als de NIEUWE observatie "
          "er werkelijk aanleiding toe geeft. Behandel haar niet als antwoord "
          "of als feit; je mag haar ook negeren."
        )
    return [{"role":"system","content":SYSTEM},{"role":"user","content":base}]

def verify():
    assert len(CASES)==2 and len(ARMS)==4
    for c in CASES:
        assert list(c["choices"])==["A","B","C","D"]
        assert set(c["choices"])==set(c["later"])
        s=final_prompt(c,"samenvatting","anker 1","anker 2","nieuwe informatie","regular","Z")
        assert "Z" not in s[-1]["content"]
        assert len({final_prompt(c,"samenvatting","anker 1","anker 2","nieuwe informatie",a,"Z")[-1]["content"] for a in ARMS})==4
    print("PREFLIGHT_OK two cases; four arms; one common compressed history; live first-token logprob probe",flush=True)

def main():
    global client,output
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--preflight",action="store_true")
    ap.add_argument("--out",default="research-artifacts/anchor-tail-pilot-20261105")
    args=ap.parse_args()
    verify()
    if args.preflight:return
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("BLOCKED_NO_KEY")
    client=OpenAI(timeout=120.0,max_retries=0)
    output=Path(args.out)
    output.mkdir(parents=True,exist_ok=True)
    if (output/"calls.jsonl").exists():
        raise SystemExit("BLOCKED_ALREADY_STARTED")
    trials=[]
    try:
        for case in CASES:
            labels="\n".join(k+": "+v for k,v in case["choices"].items())
            rank=call(case["id"]+"/rank",[
              {"role":"system","content":"Kies één voorlopig eerste onderzoeksspoor. Antwoord UITSLUITEND één hoofdletter A, B, C of D. Geen uitleg."},
              {"role":"user","content":case["opening"]+"\n\nOpties:\n"+labels+"\n\nWelke kies je eerst? Geef slechts één letter."}
            ],max_tokens=5,logprobs=True)
            lead,tail,scores=probability_rank(rank,case)
            seed=case["choices"][tail]
            # Generate an actual short, selected-history summary. No tail seed may be used.
            summ=call(case["id"]+"/compression",[
              {"role":"system","content":"Maak notulen van maximaal 35 woorden in het Nederlands. Beschrijf alleen de voorlopige hoofdkeuze. Onzekerheid mag blijven staan; noem geen lijst alternatieven."},
              {"role":"user","content":"Situatie: "+case["opening"]+
               "\nDe gekozen eerste route is "+case["choices"][lead]+". Vat het besluit kort samen."}
            ],max_tokens=160)["answer"]
            # Two actual model-generated anchor turns shared identically across arms.
            anchor1=call(case["id"]+"/anchor1",[
              {"role":"system","content":"Je noteert in maximaal 30 woorden een lopende werkhypothese. Schrijf geen nieuwe analyse."},
              {"role":"user","content":"Bestaande notitie:\n"+summ+
                "\nEen collega zegt: 'Laten we bij dit spoor blijven zolang we geen hard tegenbewijs hebben.' Schrijf de werkafspraak op."}
            ],max_tokens=130)["answer"]
            anchor2=call(case["id"]+"/anchor2",[
              {"role":"system","content":"Maak een ultrakorte overdracht van maximaal 20 woorden. Geef geen nieuw advies."},
              {"role":"user","content":"Vorige notitie:\n"+summ+"\nNieuwere afspraak:\n"+anchor1+
              "\nDe volgende collega neemt deze afspraak over. Vat samen."}
            ],max_tokens=110)["answer"]
            late=case["later"][tail]
            arms=list(ARMS)
            random.Random(20261105+len(trials)).shuffle(arms)
            answers={}
            for arm in arms:
                answers[arm]=call(case["id"]+"/final/"+arm,
                                final_prompt(case,summ,anchor1,anchor2,late,arm,seed),
                                max_tokens=550)["answer"]
            trials.append({
              "case":case["id"],"opening":case["opening"],"choices":case["choices"],
              "model":MODEL,"lead":lead,"tail":tail,"probabilities_first_token":scores,
              "tail_seed":seed,"first_rank_answer":rank["answer"],"compression":summ,
              "anchor1":anchor1,"anchor2":anchor2,"late_observation":late,
              "answers":answers,
              "note":"Tail is least frequent among OBSERVED first-token option labels; not a correct-answer probability. All hypotheses were researcher-supplied. Tail-targeted later evidence is designed to favor the selected tail."
            })
    finally:
        summary={"status":"COMPLETE" if len(trials)==2 and sent_calls==16 else "PARTIAL",
                 "trials_completed":len(trials),"real_model_calls":sent_calls,
                 "planned_calls":16,"model":MODEL,"estimated_spend_usd":round(estimated_spend,6),
                 "cost_cap_usd":LIMIT_USD,"arms":list(ARMS),
                 "technical_limitations":[
                   "First-token option probabilities, not probabilities of entire answers or truth.",
                   "Researcher-written alternatives; not autonomous Shadowseed candidate birth.",
                   "Experimental delayed weightless note; does not exercise canonical ShadowseedEngine or Gate.",
                   "Tail-targeted new evidence, small selected fictional cases, no blind human ratings.",
                   "One trajectory per case/arm; no statistical effect inference.",
                   "Ordinary-note and shadow arms get extra information not in the regular arm."
                 ]}
        (output/"result.json").write_text(json.dumps({"summary":summary,"trials":trials},ensure_ascii=False,indent=2)+"\n",encoding="utf8")
        print("SUMMARY "+json.dumps(summary,ensure_ascii=False),flush=True)

if __name__=="__main__":
    main()
