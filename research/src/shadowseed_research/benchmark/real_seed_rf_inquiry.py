"""Research-only RF: real first seed, five controls, two later model questions.

This is a feasibility pilot, not independent verification or G0-PASS.
The ordinary host NEVER sees weightless seed text. Model-generated inquiries
are separate, untrusted research outputs, not production answers or Gate signals.
Externally authored T1/T2 observations are frozen and are NOT results of any
arm's question. The same true ShadowseedEngine follows the same seed across turns.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any, Callable, Mapping

from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import OpenAIDetectorBackend
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider, DetectorClientBridge, NoneDetector,
    HOST_INSTRUCTIONS, DETECTOR_INSTRUCTIONS,
    _host_prompt,
)
from shadowseed_research.benchmark.weightless_birth_handoff import (
    freeze_canonical_weightless_birth,
)
from shadowseed_research.benchmark.weightless_longitudinal_handoff import (
    freeze_weightless_followup,
)

SCHEMA = "ssl-rf-real-seed-five-arm-one-case-v1"
OUTPUT_SCHEMA = "ssl-rf-real-seed-observations-v1"
ARMS = ("A", "B", "C", "D", "E")
MAX_CALLS = 24
MAX_EMBEDDINGS = 48
MAX_TOKENS = 110000
OUTPUT_CAP = 4096
TURN_COUNT = 3
INQUIRY_INSTRUCTIONS = (
    "Je doet uitsluitend verkennend onderzoek naar een fictieve situatie. "
    "Je mag een nieuwe vraag voorstellen, maar je mag geen uitkomst of "
    "bronbewijs verzinnen. Formuleer maximaal een concrete, toetsbare "
    "vervolgvraag. Geef precies JSON met drie velden: "
    '{"question":"...","test":"...","uncertainty":"..."}. '
    "Geef exact NONE indien een zinvolle vervolgvraag ontbreekt. "
    "Maximaal 90 woorden totaal."
)
NOTES_INSTRUCTIONS = (
    "Leg neutrale, gewone gespreksnotities vast op basis van de tot nu "
    "beschikbare fictieve context en het zichtbare antwoord. Voeg geen "
    "nieuwe hypotheses of onderzoeksvragen toe. Maximaal 55 woorden."
)


def _hash(value: Any) -> str:
    return sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()


def validate(data: Any) -> dict:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("wrong RF exploratory schema")
    if data.get("feedback_regime") != "RF":
        raise ValueError("fixed-feedback RF regime must be declared")
    case = data.get("case")
    if not isinstance(case, dict) or case.get("id") != "MEASUREMENT":
        raise ValueError("one pinned MEASUREMENT case required")
    if not isinstance(case.get("context"), str) or not 100 < len(case["context"]) < 2500:
        raise ValueError("invalid initial context")
    turns = case.get("turns")
    if not isinstance(turns, list) or len(turns) != TURN_COUNT:
        raise ValueError("exactly three consecutive turns")
    if not isinstance(case.get("sham_note"), str) or not 25 < len(case["sham_note"]) < 500:
        raise ValueError("explicit irrelevant sham control required")
    for i, t in enumerate(turns):
        if not isinstance(t, dict) or set(t) != {"question", "new_observation"}:
            raise ValueError("only approved question and observation fields")
        if not isinstance(t["question"], str) or not 20 <= len(t["question"]) <= 700:
            raise ValueError("question invalid")
        if not isinstance(t["new_observation"], str) or len(t["new_observation"]) > 1200:
            raise ValueError("new observation invalid")
        if (i == 0 and t["new_observation"]) or (i > 0 and not t["new_observation"]):
            raise ValueError("future observations may enter only later turns")
    if "answer_key" in data or "target_question" in data:
        raise ValueError("model-facing target hints forbidden")
    if data.get("model") != "gpt-5":
        raise ValueError("model pin changed")
    return case


def _user_input(case: dict, t: dict) -> str:
    # The original case is available to the HOST at every turn and must
    # also be available to the canonical current-pair detector. This is the
    # research adapter, not a change to the detector or product prompt.
    parts = ["BEGIN FICTIEVE ONDERZOEKSSITUATIE", case["context"]]
    if t["new_observation"]:
        parts += ["NIEUWE EXTERNE WAARNEMING:", t["new_observation"]]
    parts += ["VRAAG:", t["question"]]
    return "\n".join(parts)


def _inquiry_prompt(
    case: dict, prior: list[tuple[str, str]], observation: str, question: str,
    *, arm: str, note: str, earlier_question: str | None,
) -> str:
    parts = [
        "BEGIN FICTIEVE ONDERZOEKSSITUATIE", case["context"],
        "TOEGESTANE VRAAG: Ontwerp hoogstens een nieuwe onderzoeksvraag,",
        "niet het antwoord op de gewone gebruikersvraag.",
    ]
    for j, (q, a) in enumerate(prior):
        parts += [f"ZICHTBARE GESPREKSBEURT {j} VRAAG:", q,
                  f"ZICHTBARE GESPREKSBEURT {j} ANTWOORD:", a]
    if observation:
        parts += ["NIEUWE EXTERNE WAARNEMING NU:", observation]
    parts += ["HUIDIGE VRAAG:", question]
    # All arms receive the same question task. Only the declared control
    # mechanism varies. Neither A nor B gets a free seed.
    if arm == "B":
        parts += ["ZOEKWIJZE:",
                  "Overweeg verschillende alternatieve oorzaken, "
                  "tegenvoorbeelden en onderscheidende testen voordat je "
                  "één mogelijke onderzoeksvraag kiest."]
    else:
        parts += ["ZOEKWIJZE:", "Formuleer één onderzoekbare vervolgvraag indien zinvol."]
    if arm in ("C", "D", "E"):
        parts += ["EERDERE ONBEWEZEN ONDERZOEKSNOTITIE:", note]
    else:
        parts += ["EERDERE ONBEWEZEN ONDERZOEKSNOTITIE:", "NONE"]
    if earlier_question is not None:
        parts += [
            "EERDERE DOOR JOU GEFORMULEERDE ONDERZOEKSVRAAG:",
            earlier_question,
            "Er is geen onafhankelijk resultaat van die vraag beschikbaar. "
            "De nieuwe externe waarneming staat daar los van."
        ]
    parts += [
        "VRAAG VOOR DEZE ONDERZOEKSSTAP:",
        "Welke specifieke vraag zou je nu zelfstandig willen onderzoeken? "
        "Zeg welke observatie de vraag zou kunnen toetsen en wat onbewezen is.",
        "EINDE BESCHIKBARE INFORMATIE",
    ]
    return "\n".join(parts)


def _parse_inquiry(text: str) -> dict[str, str] | None:
    if text.strip().upper() == "NONE":
        return None
    try:
        value = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(value, dict) or set(value) != {"question", "test", "uncertainty"}:
        return None
    if not all(isinstance(v, str) and 2 <= len(v.strip()) <= 1000 for v in value.values()):
        return None
    return {k: v.strip() for k, v in value.items()}


def _seed_text(engine: ShadowseedEngine, sid: str) -> str:
    candidates = [
        s for s in engine.export_state()["manager"]["seeds"]
        if s.get("id") == sid
    ]
    if len(candidates) != 1:
        raise RuntimeError("canonical first seed disappeared")
    item = candidates[0]
    if item["weight"] != 0 or item["evidence_count"] != 0:
        raise RuntimeError("research seed carries unearned authority")
    return str(item["text"])


def _report_questions(cases: list[dict]) -> dict:
    # No automatic semantic or novelty labels. This is material for
    # human review; arm identities are OWNER-ONLY, not a blind packet.
    return {
        "schema": "ssl-rf-question-review-handoff-v1",
        "independent_review_complete": False,
        "blinding_complete": False,
        "question_quality_or_causal_effect_established": False,
        "episodes": [{
            "case_id": x["case_id"],
            "arm": arm,
            "questions": [
                {"turn": t["turn"], "question": t["arms"].get(arm, {}).get("parsed")}
                for t in x["turns"] if t["turn"] > 0
            ],
        } for x in cases for arm in ARMS],
    }


def run(
    data: dict, provider: BoundedProvider,
    checkpoint: Callable[[dict], None] | None = None,
) -> dict:
    case = validate(data)
    if (
        provider.model_call_cap > MAX_CALLS
        or provider.embedding_call_cap > MAX_EMBEDDINGS
        or provider.all_token_cap > MAX_TOKENS
        or provider.output_token_cap > OUTPUT_CAP
    ):
        raise ValueError("provider caps exceed RF study limits")
    detector = OpenAIDetectorBackend(
        model_id="gpt-5", prompt_variant="current_pair",
    )
    bridge = DetectorClientBridge(provider)
    detector.client = bridge
    actual = ShadowseedEngine(
        detector_backend=detector, embedding_fn=provider.embed,
        recurrence_mode="pairwise", gate_policy_id="evidence_backed",
        max_seeds_per_turn=3,
    )
    none = ShadowseedEngine(
        detector_backend=NoneDetector(), embedding_backend="lexical",
        allow_toy_embedder=True, recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    results = {
        "schema": OUTPUT_SCHEMA,
        "feedback_regime": "RF",
        "model": "gpt-5", "G0": "NOT_PASSED",
        "status": "running_exploratory_not_efficacy",
        "q1_internal_absence_established": False,
        "q2_causal_novel_inquiry_established": False,
        "no_independent_evaluator": True,
        "public_research_fixture": True,
        "no_closed_loop_feedback": True,
        "case_id": case["id"],
        "fixture_sha256": _hash(data),
        "first_seed": None,
        "ordinary_t0_samples": [],
        "ordinary_note": None,
        "turns": [],
        "provider_audit": {},
    }

    def persist() -> None:
        results["provider_audit"] = {
            "model_calls": provider.model_calls,
            "embedding_calls": provider.embedding_calls,
            "recorded_tokens": provider.total_tokens,
            "model_call_cap": provider.model_call_cap,
            "embedding_call_cap": provider.embedding_call_cap,
            "all_token_cap": provider.all_token_cap,
            "output_token_cap": provider.output_token_cap,
            "events": list(provider.events),
        }
        if checkpoint:
            checkpoint(results)

    ordinary_history: list[tuple[str, str]] = []
    prior_inquiry: dict[str, str | None] = {a: None for a in ARMS}
    birth = None
    previous_checkpoint = None
    frozen_seed = None
    sham_note = case["sham_note"]
    sham_origin = "investigator_authored_negative_fallback"
    for i, turn in enumerate(case["turns"]):
        user_input = _user_input(case, turn)
        prompt = _host_prompt(
            case, ordinary_history, turn["question"], turn["new_observation"],
        )
        if i == 0:
            for replicate in (1, 2):
                answer = provider.generate(
                    stage=f"q1_t0_ordinary_{replicate}",
                    case_id=case["id"], prompt=prompt,
                    instructions=HOST_INSTRUCTIONS,
                )
                results["ordinary_t0_samples"].append(answer)
                persist()
        prepared = actual.prepare_turn(user_input)
        ctl_prepared = none.prepare_turn(user_input)
        if (prepared.model_context or prepared.selected_seed_ids
                or prepared.surfaced_seed_ids or ctl_prepared.model_context):
            raise RuntimeError("ordinary host was exposed to unverified seed")
        host_answer = provider.generate(
            stage=f"host_t{i}", case_id=case["id"],
            prompt=prompt, instructions=HOST_INSTRUCTIONS,
        )
        bridge.case_id, bridge.turn = case["id"], i
        observed = actual.observe_turn(prepared, host_answer)
        ctl = none.observe_turn(ctl_prepared, host_answer)
        if ctl["answer"] != host_answer or none.inspect()["seeds"]:
            raise RuntimeError("NONE mechanical control invalid")
        row = {
            "turn": i,
            "question": turn["question"],
            "new_observation": turn["new_observation"],
            "host_answer": host_answer,
            "detector_raw_output": detector.last_raw_output,
            "canonical_report": observed,
            "none_control_answer_identical": True,
            "birth": None,
            "followup": None,
            "arms": {},
        }
        # Persist partial results before any optional notes or research calls.
        # A failed provider stage must not erase completed canonical turns.
        results["turns"].append(row)
        persist()
        if i == 0:
            ids = [
                sid for sid in observed.get("seeds_born_weightless", [])
                if actual.export_state().get("born_turn", {}).get(sid) == 0
            ]
            if ids:
                # First accepted canonical seed; never a chosen best example.
                birth = freeze_canonical_weightless_birth(actual, observed, ids[0])
                frozen_seed = _seed_text(actual, ids[0])
                if sha256(frozen_seed.encode("utf-8")).hexdigest() != birth["candidate_text_sha256"]:
                    raise RuntimeError("raw-to-seed birth identity invalid")
                row["birth"] = birth
                # Prefer an alternative REAL detector output from this exact
                # first source response for the E candidate ablation. Its
                # intake rejection remains in the canonical raw trace.
                alternatives = [
                    candidate for candidate in observed.get("detected_candidates", [])
                    if isinstance(candidate, str) and candidate.strip()
                    and candidate.strip() != frozen_seed.strip()
                ]
                if alternatives:
                    sham_note = alternatives[0]
                    sham_origin = "different_real_T0_detector_item_not_first_seed"
                results["first_seed"] = {
                    "id": ids[0], "text": frozen_seed,
                    "birth_snapshot_sha256": birth["snapshot_sha256"],
                    "first_seed_predeclared_selection": "first_accepted_newborn",
                    "weight": 0, "evidence_count": 0,
                    "sham_source": sham_origin,
                    "sham_text_sha256": _hash(sham_note),
                }
            # Ordinary notes are produced from T0 history; no seed text.
            note_prompt = (
                "BEGIN CASUS\n" + case["context"] +
                "\nVRAAG\n" + turn["question"] +
                "\nZICHTBAAR ANTWOORD\n" + host_answer
            )
            results["ordinary_note"] = provider.generate(
                stage="ordinary_memory_note_t0", case_id=case["id"],
                prompt=note_prompt, instructions=NOTES_INSTRUCTIONS,
            )
        else:
            if birth is not None:
                row["followup"] = freeze_weightless_followup(
                    actual, birth, previous=previous_checkpoint
                )
                previous_checkpoint = row["followup"]
            if frozen_seed is not None:
                # Different order at each stage. Fixed before provider calls.
                orders = {
                    1: ("E", "B", "C", "D", "A"),
                    2: ("A", "D", "B", "E", "C"),
                }
                for arm in orders[i]:
                    notes = {
                        "A": "NONE", "B": "NONE",
                        "C": results["ordinary_note"], "D": frozen_seed,
                        "E": sham_note,
                    }
                    inquiry_prompt = _inquiry_prompt(
                        case, ordinary_history + [(user_input, host_answer)],
                        turn["new_observation"], turn["question"],
                        arm=arm, note=notes[arm],
                        earlier_question=prior_inquiry[arm],
                    )
                    if arm in ("A", "B") and frozen_seed in inquiry_prompt:
                        raise RuntimeError("candidate leaked into control")
                    proposal = provider.generate(
                        stage=f"research_inquiry_t{i}_{arm}",
                        case_id=case["id"], prompt=inquiry_prompt,
                        instructions=INQUIRY_INSTRUCTIONS,
                    )
                    parsed = _parse_inquiry(proposal)
                    row["arms"][arm] = {
                        "text": proposal,
                        "parsed": parsed,
                        "parse_status": "NONE" if proposal.strip().upper() == "NONE"
                        else "valid_json" if parsed else "invalid_json",
                        "prompt_sha256": _hash(inquiry_prompt),
                        "prompt_chars": len(inquiry_prompt),
                        "note_sha256": _hash(notes[arm]),
                        "note_chars": len(notes[arm]),
                        "model_origin": "recorded_api_response_not_internal_activation",
                        "independent_test_result": None,
                    }
                    prior_inquiry[arm] = parsed["question"] if parsed else None
                    persist()
        ordinary_history.append((user_input, host_answer))
        persist()
    if actual.audit() or none.audit() or actual.inspect()["influence_records"]:
        raise RuntimeError("unexpected seed authority or answer influence")
    results["status"] = (
        "completed_exploratory_real_seed_and_arm_questions"
        if frozen_seed else "completed_no_seed_no_q2_opportunity"
    )
    results["human_review_handoff"] = _report_questions([results])
    persist()
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fixture = json.loads(Path(args.fixture).read_text(encoding="utf-8"))
    validate(fixture)
    p = Path(args.output)
    p.parent.mkdir(parents=True, exist_ok=True)
    provider = BoundedProvider(
        os.environ.get("OPENAI_API_KEY", ""),
        model_call_cap=MAX_CALLS,
        embedding_call_cap=MAX_EMBEDDINGS,
        all_token_cap=MAX_TOKENS,
        output_token_cap=OUTPUT_CAP,
    )

    def write(obj: dict) -> None:
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
        tmp.replace(p)

    try:
        result = run(fixture, provider, checkpoint=write)
    except Exception as exc:
        # Preserve partial raw observations, rather than treating a paid model
        # failure as "NONE" or throwing out all earlier steps.
        if p.exists():
            partial = json.loads(p.read_text(encoding="utf-8"))
        else:
            partial = {"schema": OUTPUT_SCHEMA, "turns": []}
        partial["status"] = "incomplete_exploratory_not_a_null_result"
        partial["failure_type"] = type(exc).__name__
        partial["last_model_status"] = next(
            (e.get("status") for e in reversed(provider.events)
             if e.get("kind") == "model"), None
        )
        partial["provider_audit"] = {
            "model_calls": provider.model_calls,
            "embedding_calls": provider.embedding_calls,
            "recorded_tokens": provider.total_tokens,
            "events": provider.events,
        }
        partial["G0"] = "NOT_PASSED"
        partial["q2_causal_novel_inquiry_established"] = False
        write(partial)
        raise RuntimeError(
            f"bounded research RF trial failed closed: {type(exc).__name__}"
        ) from None
    print(json.dumps({
        "status": result["status"],
        "model_calls": provider.model_calls,
        "embedding_calls": provider.embedding_calls,
        "tokens": provider.total_tokens,
        "seed": result["first_seed"]["id"] if result["first_seed"] else None,
        "recorded_arm_questions": sum(
            len(t["arms"]) for t in result["turns"]
        ),
        "G0": "NOT_PASSED",
    }), flush=True)


if __name__ == "__main__":
    main()
