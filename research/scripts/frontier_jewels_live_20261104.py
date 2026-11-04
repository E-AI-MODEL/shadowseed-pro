#!/usr/bin/env python3
"""One-time, capped live frontier study. Fictional cases; no real subject data.

Five treatments by two cases, with an actual two-turn model history.
The existing GitHub Actions environment provides OPENAI_API_KEY. Never commit it.
This is an exploratory comparison, not proof that ShadowSeed memory works.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import sys
from datetime import datetime, timezone

MODEL = "gpt-6.1-sol"
ARMS = ("ordinary", "ordinary_note", "candidate_early", "candidate_delayed", "placebo")
OUTPUT_LIMIT = 900
MAX_USD = 0.50
INPUT_USD_PER_M = 2.00
OUTPUT_USD_PER_M = 10.00
SYSTEM = (
    "Je onderzoekt een fictieve casus. Geef een concrete, uitvoerbare "
    "onderzoekstoets. Behandel niet-bevestigde hypotheses niet als feiten. "
    "Noem de waarnemingen die nodig zijn en welke uitkomst de verklaring "
    "zou verzwakken. Verzin geen data. Schrijf helder Nederlands, beknopt."
)
CASES = (
    {
        "id": "F02",
        "domain": "Waterverbruik in een proefkas",
        "initial": (
            "In een proefkas tonen identieke vochtmeters in verschillende "
            "plantenbakken uiteenlopende waarden na hetzelfde sproeischema. "
            "Er is geen onafhankelijke meting van het werkelijke watergehalte. "
            "De software registreert alleen gemiddelden per uur."
        ),
        "early_question": (
            "Welke onzekere verklaringen verdienen behoud als "
            "onderzoeksmogelijkheid, zonder dat je al een oorzaak kiest?"
        ),
        "later_observation": (
            "Nieuwe informatie: tijdens een handmatige controle stonden alle "
            "meters op dezelfde diepte. Een technicus ontdekte dat de "
            "voedingsspanning van een meetgroep tijdelijk lager was. "
            "Onafhankelijke weegmetingen van de bakken ontbreken nog."
        ),
        "later_question": (
            "Welke proef kan meetfout en werkelijk waterverlies uit elkaar "
            "houden? Wat zou de proef onderuit halen?"
        ),
        "candidate": (
            "Misschien ontstaat het verschil doordat vochtmeters op "
            "verschillende diepte zijn geplaatst."
        ),
        "ordinary_note": (
            "Bij de vochtmetingen is de plaatsing van de sensoren nog niet "
            "als mogelijke bron van verschil uitgesloten."
        ),
        "placebo": (
            "De bakken krijgen na de proef een nieuwe nummering; "
            "de huidige codes zijn tijdelijk."
        ),
    },
    {
        "id": "F04",
        "domain": "Reparatie van keramische onderdelen",
        "initial": (
            "Na een wijziging van het droogprogramma scheuren sommige "
            "keramische proefstukken sneller. Van het droogproces zijn alleen "
            "globale luchtvochtigheid en oventemperatuur beschikbaar. "
            "De stukvorm varieert en de metingen van scheuren zijn niet geblindeerd."
        ),
        "early_question": (
            "Noem nog niet vastgestelde verklaringen die later bruikbaar "
            "kunnen zijn, maar laat ze zonder voorkeur naast elkaar staan."
        ),
        "later_observation": (
            "Nieuwe informatie: de scheuren komen vooral voor bij onderdelen "
            "met een brede steunrand, zelfs in dezelfde ovenbatch. Een foto "
            "toont dat de onderste contactvlakken verschillen. "
            "Er zijn geen temperatuurmetingen aan afzonderlijke oppervlakken."
        ),
        "later_question": (
            "Welk nieuw experiment kan contactgeometrie van algemene "
            "droogbelasting onderscheiden? Welke uitkomst zou die "
            "verklaring verzwakken?"
        ),
        "candidate": (
            "De manier waarop elk stuk op de steunplaat rust kan lokaal "
            "een ander droogverloop veroorzaken."
        ),
        "ordinary_note": (
            "Er is nog niet bekeken of de draagconstructie de "
            "droogomstandigheden per stuk verandert."
        ),
        "placebo": (
            "Na de reeks wordt de opstelling opnieuw gefotografeerd "
            "voor de interne catalogus."
        ),
    },
)


def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def trials():
    r = [(c, a) for c in CASES for a in ARMS]
    random.Random(20261104).shuffle(r)
    return r


def messages(case, arm, t1=None):
    first = case["initial"] + "\nVraag: " + case["early_question"]
    if arm == "ordinary_note":
        first += "\nGewone gespreksnotitie: " + case["ordinary_note"]
    if arm == "candidate_early":
        first += "\nOnbewezen onderzoekskandidaat: " + case["candidate"]
    if arm == "placebo":
        first += "\nLosse contextnotitie: " + case["placebo"]
    msgs = [{"role": "developer", "content": SYSTEM}, {"role": "user", "content": first}]
    if t1 is None:
        return msgs
    last = case["later_observation"] + "\nVraag: " + case["later_question"]
    if arm == "candidate_delayed":
        last += "\nEerder bewaarde maar nog onbewezen onderzoekskandidaat: " + case["candidate"]
    return msgs + [{"role": "assistant", "content": t1}, {"role": "user", "content": last}]


def preflight():
    r = trials()
    assert len(r) == 10 and len(set((c["id"], a) for c, a in r)) == 10
    assert {c["id"] for c, a in r} == {"F02", "F04"}
    for c, a in r:
        first = messages(c, a)
        second = messages(c, a, "EERSTE ANTWOORD")
        assert len(first) == 2 and len(second) == 4
        assert c["later_observation"] not in json.dumps(first, ensure_ascii=False)
        assert c["later_observation"] in second[-1]["content"]
        assert second[2]["content"] == "EERSTE ANTWOORD"
        assert (c["candidate"] in first[-1]["content"]) == (a == "candidate_early")
        assert (c["candidate"] in second[-1]["content"]) == (a == "candidate_delayed")
        assert all(len(m["content"]) < 5000 for m in second)
    print("PREFLIGHT_OK cases=2 arms=5 trajectories=10 planned_calls=20", flush=True)


def estimated_cost(usage):
    return (
        usage.get("input_tokens", 0) * INPUT_USD_PER_M
        + usage.get("output_tokens", 0) * OUTPUT_USD_PER_M
    ) / 1_000_000


def reservation(msgs):
    # Deliberately conservative short-text estimate, not a billing guarantee.
    chars = sum(len(m["content"]) for m in msgs)
    if chars > 14000:
        raise RuntimeError("Prompt te groot")
    return 1.35 * (
        chars * INPUT_USD_PER_M + OUTPUT_LIMIT * OUTPUT_USD_PER_M
    ) / 1_000_000


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def record_event(path, obj):
    with path.open("a", encoding="utf-8") as out:
        out.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")
        out.flush()
        os.fsync(out.fileno())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--output", default="research-artifacts/frontier-jewels-live-20261104")
    opts = parser.parse_args()
    preflight()
    if opts.preflight:
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("BLOCKED_NO_PROVIDER_KEY: no model calls")
    from openai import OpenAI
    client = OpenAI(timeout=90.0, max_retries=0)
    outdir = Path(opts.output)
    outdir.mkdir(parents=True, exist_ok=True)
    events_file = outdir / "provider_events.jsonl"
    if events_file.exists():
        raise SystemExit("BLOCKED_ALREADY_STARTED: never auto-repeat potentially paid calls")
    events = []
    spend = 0.0
    stopped = None
    for case, arm in trials():
        first_answer = None
        for phase in (1, 2):
            if phase == 2 and not first_answer:
                stopped = "NO_FIRST_ANSWER"
                break
            msgs = messages(case, arm, first_answer)
            reserve = reservation(msgs)
            if spend + reserve > MAX_USD:
                stopped = "BUDGET_STOP"
                break
            ident = case["id"] + "__" + arm
            request_meta = {
                "case": case["id"], "arm": arm, "phase": phase,
                "model_requested": MODEL, "prompt_sha256": digest(msgs),
                "messages": msgs, "utc": datetime.now(timezone.utc).isoformat(),
            }
            record_event(events_file, {"kind": "request_start", **request_meta})
            try:
                response = client.responses.create(
                    model=MODEL, input=msgs, reasoning={"effort": "low"},
                    max_output_tokens=OUTPUT_LIMIT, store=False,
                )
            except Exception as exc:
                record_event(events_file, {
                    "kind": "request_error", "case": case["id"],
                    "arm": arm, "phase": phase,
                    "exception_type": type(exc).__name__,
                    "note": "No automatic retry; a provider charge cannot be ruled out",
                })
                stopped = "PROVIDER_ERROR"
                break
            result = response.output_text or ""
            usage = response.usage.model_dump() if response.usage else {}
            obj = {
                "kind": "response", **request_meta,
                "model_returned": response.model, "response_id": response.id,
                "response_status": response.status, "usage": usage,
                "text": result, "text_sha256": hashlib.sha256(result.encode()).hexdigest(),
            }
            record_event(events_file, obj)
            events.append(obj)
            spend += estimated_cost(usage)
            print(
                "RECEIVED case=%s arm=%s phase=%d tokens_in=%d tokens_out=%d estimated_spend_usd=%.5f"
                % (case["id"], arm, phase, usage.get("input_tokens", 0),
                   usage.get("output_tokens", 0), spend),
                flush=True,
            )
            if phase == 1:
                first_answer = result
        if stopped:
            break

    answers = [e for e in events if e["kind"] == "response" and e["phase"] == 2]
    random.Random(20261105).shuffle(answers)
    private_map = {f"B{i+1:02d}": {"case": e["case"], "arm": e["arm"]}
                   for i, e in enumerate(answers)}
    with (outdir / "blind_review.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "domain", "later_observation", "later_question",
                         "answer", "executable_test", "falsifier",
                         "tunnel_vision", "comment"])
        byid = {c["id"]: c for c in CASES}
        for i, e in enumerate(answers):
            c = byid[e["case"]]
            writer.writerow([
                f"B{i+1:02d}", c["domain"], c["later_observation"],
                c["later_question"], e["text"], "", "", "", "",
            ])
    atomic_json(outdir / "PRIVATE_MAPPING.json", private_map)
    state = {
        "status": stopped or "PROVIDER_COMPLETED",
        "expected_provider_calls": 20, "received_responses": len(events),
        "t2_answers": len(answers), "model_requested": MODEL,
        "estimated_spend_usd": round(spend, 6), "budget_usd": MAX_USD,
        "cases": ["F02", "F04"], "arms": list(ARMS),
        "independent_human_review_completed": False,
        "causal_shadowseed_memory_effect_established": False,
        "notes": (
            "Researcher-authored hypothetical candidates. The active treatment "
            "is prompt exposure, not validated ShadowSeed memory or Gate activation."
        ),
    }
    atomic_json(outdir / "summary.json", state)
    print("SUMMARY " + json.dumps(state, ensure_ascii=False), flush=True)
    if stopped:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
