"""Exploratory multi-case, longitudinal REAL-engine Shadowseed A/B study.

Research sidecar only. Two independent inquiry conditions use the same GPT-5,
same strong exploratory instructions, identical ordinary notes and frozen RF
external observations. The ONLY treatment difference is one actual first T0
weightless seed in a marked note slot (B); A receives NONE.

This measures observable response and subsequent question *formation*, not
model-internal latent representations, mathematical novelty, external Q2
investigability, or G0 success. RI requires a separately reviewed evaluator.
No faked seed is substituted when canonical detector admits no T0 candidate.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from typing import Any, Callable

from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import OpenAIDetectorBackend
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider, DetectorClientBridge, NoneDetector,
    HOST_INSTRUCTIONS, DETECTOR_INSTRUCTIONS, _host_prompt,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    NOTES_INSTRUCTIONS, _user_input, _hash,
)
from shadowseed_research.benchmark.weightless_birth_handoff import (
    freeze_canonical_weightless_birth,
)
from shadowseed_research.benchmark.weightless_longitudinal_handoff import (
    freeze_weightless_followup,
)

SCHEMA = "shadowseed-multicase-rf-ab-prospect-v1"
OUTPUT_SCHEMA = "shadowseed-multicase-real-ab-exploratory-v1"
MODEL = "gpt-5"
ARMS = ("A", "B")
CASE_COUNT = 6
CALL_CAP = 14
EMBED_CAP = 24
TOKEN_CAP = 65000
OUTPUT_CAP = 4096
ALL_CALL_CAP = CASE_COUNT * CALL_CAP
ALLOCATION_MODE = "balanced_random_allocation_before_first_model_call"
ALLOWED_FAMILIES = {
    "condition_reframing", "instrument_affordance",
    "relational_dependency", "negative_no_opportunity",
}
EXPLORATORY_INSTRUCTIONS = (
    "Je onderzoekt een fictieve situatie. Zoek ook naar minder vanzelfsprekende "
    "maar inhoudelijk verdedigbare relaties. Dwing geen onderzoeksvraag af. "
    "Noem maximaal twee inhoudelijk verschillende toetsbare onderzoekspaden; "
    "slechts één of geen is prima. Een mogelijke verklaring of eerdere notitie "
    "is geen feit of bewijs. Gebruik uitsluitend zichtbare gegevens, geen "
    "verzonnen metingen. Kies een nieuwe onafhankelijke test per voorstel en "
    "leg uit onder welke voorwaarde een latere vraag betekenis krijgt. "
    'Geef exact één JSON object: {"status":"questions"|"none",'
    '"proposals":[{"question":"...","test":"...","depends_on":"..."}],'
    '"unresolved_alternatives":["..."]}. '
    "Geef bij geen zinvolle test status none, lege proposals. "
    "Beoordeel jezelf niet als origineel en voer geen tests uit."
)


def validate_design(d: Any) -> list[dict]:
    if not isinstance(d, dict) or d.get("schema") != SCHEMA:
        raise ValueError("not the frozen multi-case study")
    if (d.get("model"), d.get("feedback_regime"), d.get("case_count")) != (
        MODEL, "RF", CASE_COUNT
    ):
        raise ValueError("wrong model/feedback regime/case count")
    if d.get("status") != "EXPLORATORY_NOT_G0_CONFIRMED":
        raise ValueError("unapproved study must remain exploratory")
    if d.get("all_cases_public_investigator_authored_not_sealed") is not True:
        raise ValueError("cannot misrepresent cases as sealed holdouts")
    for field, val in {
        "unselected_candidate_selection": "first_real_canonical_weightless_T0_birth_no_cherrypicking",
        "prompt_template": "shared_strong_search_with_same_ordinary_notes_A_NONE_B_REAL_SEED",
    }.items():
        if d.get(field) != val:
            raise ValueError(f"study invariant {field} changed")
    inv = d.get("study_invariants")
    if not isinstance(inv, dict) or any(inv.get(k) != v for k, v in {
        "ordinary_host_never_see_weightless_seed": True,
        "authority_weight_always_zero": True,
        "auto_gate_change_forbidden": True,
        "per_case_max_model_calls": CALL_CAP,
        "per_case_max_embedding_calls": EMBED_CAP,
        "per_case_max_tokens": TOKEN_CAP,
        "one_shot_no_retry": True,
    }.items()):
        raise ValueError("study provider/Gate limits altered")
    cases = d.get("cases")
    if not isinstance(cases, list) or len(cases) != CASE_COUNT:
        raise ValueError("exactly six cases, no cherry-picked omissions")
    ids = [x.get("id") for x in cases]
    if ids != [f"AB26-C{i:02d}" for i in range(1, CASE_COUNT + 1)]:
        raise ValueError("case identity/order changed")
    if d.get("case_order") != ids:
        raise ValueError("case order differs from frozen fixture")
    families = set()
    for x in cases:
        families.add(x.get("family"))
        if x.get("family") not in ALLOWED_FAMILIES:
            raise ValueError("unknown mechanism family")
        if not isinstance(x.get("context"), str) or not 140 < len(x["context"]) < 2400:
            raise ValueError("case context outside declared length")
        turns = x.get("turns")
        if not isinstance(turns, list) or len(turns) != 3:
            raise ValueError("exactly three turns per case")
        for i, t in enumerate(turns):
            if set(t) != {"question", "new_observation"}:
                raise ValueError("unspecified turn data")
            if not isinstance(t["question"], str) or not 20 <= len(t["question"]) <= 750:
                raise ValueError("invalid ordinary question")
            if not isinstance(t["new_observation"], str) or not 0 <= len(t["new_observation"]) <= 1400:
                raise ValueError("invalid external observation")
            if (i == 0 and t["new_observation"]) or (i > 0 and not t["new_observation"]):
                raise ValueError("future observations may not leak into T0")
        if any(k in x for k in ("answer_key", "expected_seed", "target_new_question", "winning_arm")):
            raise ValueError("case may not include a target answer")
    if not {"negative_no_opportunity", "condition_reframing", "instrument_affordance", "relational_dependency"} <= families:
        raise ValueError("missing contrasting mechanism or negative case")
    if d.get("claims_not_supported") is None or "G0_PASS" not in d["claims_not_supported"]:
        raise ValueError("G0/claim boundaries removed")
    return cases


def _parse_research(raw: str) -> dict[str, Any]:
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return {"status": "invalid", "proposals": [], "unresolved_alternatives": [],
                "reason": "not_json"}
    if not isinstance(obj, dict) or set(obj) != {
        "status", "proposals", "unresolved_alternatives"
    }:
        return {"status": "invalid", "proposals": [], "unresolved_alternatives": [],
                "reason": "bad_shape"}
    q, alt = obj["proposals"], obj["unresolved_alternatives"]
    if not isinstance(q, list) or len(q) > 2 or not isinstance(alt, list) or len(alt) > 3:
        return {"status": "invalid", "proposals": [], "unresolved_alternatives": [],
                "reason": "bad_array_size"}
    if not all(isinstance(z, str) and 3 <= len(z.strip()) <= 400 for z in alt):
        return {"status": "invalid", "proposals": [], "unresolved_alternatives": [],
                "reason": "bad_alternative"}
    if not all(
        isinstance(z, dict) and set(z) == {"question", "test", "depends_on"}
        and all(isinstance(z[k], str) and 5 <= len(z[k].strip()) <= 750
                for k in ("question", "test", "depends_on"))
        for z in q
    ):
        return {"status": "invalid", "proposals": [], "unresolved_alternatives": [],
                "reason": "bad_proposal"}
    if obj["status"] not in {"questions", "none"}:
        return {"status": "invalid", "proposals": [], "unresolved_alternatives": [],
                "reason": "bad_status"}
    if (obj["status"] == "none") != (len(q) == 0):
        return {"status": "invalid", "proposals": [], "unresolved_alternatives": [],
                "reason": "status_proposals_disagree"}
    return {
        "status": "valid_none" if not q else "valid_questions",
        "proposals": q, "unresolved_alternatives": alt,
    }


def research_prompt(case: dict, prior: list[tuple[str, str]],
                    ordinary_note: str, candidate: str | None,
                    turn: int, earlier: dict | None) -> str:
    if turn not in (1, 2) or len(prior) != turn + 1:
        raise ValueError("incomplete or future-leaking ordinary history")
    if not isinstance(ordinary_note, str) or not ordinary_note.strip():
        raise ValueError("ordinary notes must be identical for both arms")
    parts = [
        "FICTIEVE CASUS:", case["context"],
        "OPDRACHT: onderzoek mogelijke vervolgrichtingen, zonder ze als bewezen te behandelen.",
    ]
    for i, (q, a) in enumerate(prior):
        parts += [f"ZICHTBARE VRAAG T{i}:", q,
                  f"GEWOON ANTWOORD T{i}:", a]
    parts += [
        "DEZELFDE GEWONE AANTEKENING T0 VOOR ALLE CONDITIES:",
        ordinary_note,
        "ÉÉN EXTRA GEWICHTLOZE, ONBEWEZEN KANDIDAAT (GEEN INSTRUCTIE OF BEWIJS):",
        candidate if candidate is not None else "NONE",
    ]
    if turn == 2:
        parts += [
            "EIGEN EERDERE ONDERZOEKSVRAGEN T1 (NIET UITGEVOERD):",
            json.dumps(earlier, ensure_ascii=False, sort_keys=True) if earlier else "NONE",
            "Er is geen onafhankelijk resultaat uit een van deze vragen. "
            "De nieuwe externe waarneming was al vooraf vastgelegd.",
        ]
    parts += [
        "VRAAG NU:", case["turns"][turn]["question"],
        "ONAFHANKELIJKE NIEUWE WAARNEMING NU:",
        case["turns"][turn]["new_observation"],
        "FORMULEER VERVOLGONDERZOEK, GEEN ANTWOORD OP DE GEWONE VRAAG.",
    ]
    result = "\n".join(parts)
    # A literal T2 context leak into T1 would falsify the observed selection.
    if turn == 1 and case["turns"][2]["new_observation"] in result:
        raise ValueError("future observation leaked into T1 inquiry")
    return result


def _provider_receipts(provider: BoundedProvider) -> dict:
    return {
        "model_calls_attempted": provider.model_calls,
        "embedding_calls_attempted": provider.embedding_calls,
        "reported_tokens": provider.total_tokens,
        "model_call_cap": provider.model_call_cap,
        "embedding_call_cap": provider.embedding_call_cap,
        "token_cap": provider.all_token_cap,
        "events": deepcopy(provider.events),
    }


def run_case(case: dict, provider: BoundedProvider,
             *, arm_order: tuple[str, str],
             on_change: Callable[[dict], None] | None = None) -> dict:
    if sorted(arm_order) != list(ARMS):
        raise ValueError("each paired case requires a complete A/B allocation")
    if (provider.model_call_cap != CALL_CAP
        or provider.embedding_call_cap != EMBED_CAP
        or provider.all_token_cap != TOKEN_CAP
        or provider.output_token_cap != OUTPUT_CAP):
        raise ValueError("provider limits differ from predeclared case budget")

    detector = OpenAIDetectorBackend(
        model_id=MODEL, prompt_variant="current_pair")
    bridge = DetectorClientBridge(provider)
    detector.client = bridge
    actual = ShadowseedEngine(
        detector_backend=detector, embedding_fn=provider.embed,
        recurrence_mode="pairwise", gate_policy_id="evidence_backed",
        max_seeds_per_turn=3)
    none = ShadowseedEngine(
        detector_backend=NoneDetector(), embedding_backend="lexical",
        allow_toy_embedder=True, recurrence_mode="pairwise",
        gate_policy_id="evidence_backed")
    result = {
        "case_id": case["id"], "family": case["family"],
        "status": "running_exploratory", "first_seed": None,
        "birth": None, "turns": [], "ordinary_t0_samples": [],
        "ordinary_note": None, "research_arms": [],
        "ordinary_answer_seed_influence": False,
        "T1_randomized_first_arm": arm_order[0],
        "T2_first_arm": arm_order[1],
        "G0": "NOT_PASSED", "provider": {},
    }

    def save() -> None:
        result["provider"] = _provider_receipts(provider)
        if on_change:
            on_change(deepcopy(result))
    save()
    previous_checkpoint = None
    birth = None
    frozen_seed = None
    normal_history: list[tuple[str, str]] = []
    earlier: dict[str, dict | None] = {"A": None, "B": None}
    for i, turn in enumerate(case["turns"]):
        user_input = _user_input(case, turn)
        prompt = _host_prompt(case, normal_history, turn["question"], turn["new_observation"])
        if i == 0:
            for j in (1, 2):
                out = provider.generate(
                    stage=f"t0_ordinary_replicate_{j}",
                    case_id=case["id"], prompt=prompt,
                    instructions=HOST_INSTRUCTIONS)
                result["ordinary_t0_samples"].append(out)
                save()
        prepared = actual.prepare_turn(user_input)
        control_prepared = none.prepare_turn(user_input)
        if any((prepared.model_context, prepared.selected_seed_ids,
                prepared.surfaced_seed_ids, control_prepared.model_context)):
            raise RuntimeError("weightless research candidate entered ordinary host")
        host_answer = provider.generate(
            stage=f"host_t{i}", case_id=case["id"],
            prompt=prompt, instructions=HOST_INSTRUCTIONS)
        bridge.case_id, bridge.turn = case["id"], i
        observed = actual.observe_turn(prepared, host_answer)
        controlled = none.observe_turn(control_prepared, host_answer)
        if controlled["answer"] != host_answer or none.inspect()["seeds"]:
            raise RuntimeError("NONE engine ordinary-answer parity broken")
        row = {
            "turn": i, "question": turn["question"],
            "new_observation": turn["new_observation"],
            "user_input": user_input, "host_answer": host_answer,
            "detector_raw": detector.last_raw_output,
            "canonical_report": observed,
            "followup": None, "research_arms": {},
            "ordinary_control_identical": True,
        }
        result["turns"].append(row)
        save()
        if i == 0:
            newborns = [
                sid for sid in observed.get("seeds_born_weightless", [])
                if actual.export_state().get("born_turn", {}).get(sid) == 0
            ]
            if newborns:
                birth = freeze_canonical_weightless_birth(
                    actual, observed, newborns[0])
                matching = [
                    s for s in actual.export_state()["manager"]["seeds"]
                    if s.get("id") == newborns[0]]
                if len(matching) != 1:
                    raise RuntimeError("first canonical seed not unique")
                s = matching[0]
                if s["weight"] != 0 or s["evidence_count"] != 0:
                    raise RuntimeError("first candidate has unearned authority")
                frozen_seed = s["text"]
                if sha256(frozen_seed.encode()).hexdigest() != birth["candidate_text_sha256"]:
                    raise RuntimeError("born seed text hash mismatch")
                result["first_seed"] = {
                    "id": newborns[0], "text": frozen_seed,
                    "selection": "first_T0_canonical_accepted",
                    "birth_snapshot_sha256": birth["snapshot_sha256"],
                    "birth_turn": 0, "weight": 0, "evidence_count": 0}
                result["birth"] = birth
            note_prompt = ("CASUS:\n" + case["context"]
                           + "\nVRAAG:\n" + turn["question"]
                           + "\nGEWOON ANTWOORD:\n" + host_answer)
            result["ordinary_note"] = provider.generate(
                stage="ordinary_note_t0", case_id=case["id"],
                prompt=note_prompt, instructions=NOTES_INSTRUCTIONS)
            if frozen_seed and frozen_seed in result["ordinary_note"]:
                result["literal_seed_already_in_ordinary_note"] = True
            else:
                result["literal_seed_already_in_ordinary_note"] = False
            save()
        elif birth is not None:
            # Mandatory: these are actual chronological product checkpoints.
            # DO NOT bypass T2 on ValueError; preserve the failed trajectory.
            try:
                row["followup"] = freeze_weightless_followup(
                    actual, birth, previous=previous_checkpoint)
                previous_checkpoint = row["followup"]
            except ValueError as exc:
                state = actual.export_state()
                key = {
                    "previous checkpoint is not the preceding history",
                    "previous event ledger prefix was modified",
                    "first-birth product history no longer matches freeze",
                    "original candidate is missing or ambiguous",
                    "original candidate text or origin changed",
                    "first created-event has changed or been duplicated",
                    "recorded detector-to-first-birth item changed",
                    "ordinary answer route received SSL influence",
                    "candidate has crossed the Gate authority boundary",
                    "candidate is no longer authority-free",
                    "terminal expiry has no verified lifecycle Gate record",
                    "repeat candidate lacks recorded deduplication",
                    "noncanonical or reordered live history",
                }
                row["checkpoint_failure"] = {
                    "error_code": str(exc) if str(exc) in key
                                  else "other_validation_failure",
                    "turn": i,
                    "prior_checkpoint_sha256": (
                        previous_checkpoint.get("snapshot_sha256")
                        if previous_checkpoint else None),
                    "prior_event_count": (
                        previous_checkpoint.get("event_log_count")
                        if previous_checkpoint else None),
                    "observed_event_count": len(
                        state["manager"].get("event_log", [])),
                    "prior_history_sha256": (
                        previous_checkpoint.get("history_sha256")
                        if previous_checkpoint else None),
                    "actual_prior_history_sha256": _hash(
                        state.get("turn_reports", [])[:i]),
                    "no_repair_or_bypass": True,
                }
                result["status"] = "incomplete_checkpoint_failure"
                save()
                raise
        if i in (1, 2) and frozen_seed is not None:
            # The ordinary host saw NEITHER arm. Both research arms use
            # exactly the same normal note, case, earlier observations,
            # model and inquiry instructions, differing only in seed slot.
            prior = normal_history + [(user_input, host_answer)]
            prompts = {
                arm: research_prompt(case, prior, result["ordinary_note"],
                                      frozen_seed if arm == "B" else None,
                                      i, earlier[arm])
                for arm in ARMS
            }
            if frozen_seed in prompts["A"]:
                raise RuntimeError("exact seed text leaked into ordinary arm")
            for arm in arm_order if i == 1 else tuple(reversed(arm_order)):
                out = provider.generate(
                    stage=f"inquiry_T{i}_{arm}", case_id=case["id"],
                    prompt=prompts[arm],
                    instructions=EXPLORATORY_INSTRUCTIONS)
                parsed = _parse_research(out)
                row["research_arms"][arm] = {
                    "text": out, "parsed": parsed,
                    "prompt_sha256": _hash(prompts[arm]),
                    "prompt_chars": len(prompts[arm]),
                    "research_seed_exposure": arm == "B",
                    "previous_own_question_only": i == 2,
                    "external_test_executed": False,
                    "independent_review_completed": False,
                }
                earlier[arm] = parsed if parsed["status"] in {
                    "valid_questions", "valid_none"} else None
                save()
        normal_history.append((user_input, host_answer))
        save()
    if actual.audit() or none.audit() or actual.inspect()["influence_records"]:
        raise RuntimeError("ordinary host candidate influence or state audit error")
    result["status"] = (
        "completed_exploratory_pair"
        if frozen_seed is not None else "completed_no_T0_seed_no_AB_opportunity")
    save()
    return result


def run_study(d: dict, provider_factory: Callable[[str], BoundedProvider],
              *, on_change: Callable[[dict], None] | None = None,
              allocation: dict[str, tuple[str, str]] | None = None) -> dict:
    cases = validate_design(d)
    if allocation is None:
        first = ["A"] * (CASE_COUNT // 2) + ["B"] * (CASE_COUNT // 2)
        secrets.SystemRandom().shuffle(first)
        allocation = {
            c["id"]: (arm, "B" if arm == "A" else "A")
            for c, arm in zip(cases, first)
        }
    if (set(allocation) != {c["id"] for c in cases}
        or sorted(x[0] for x in allocation.values()) != ["A"] * 3 + ["B"] * 3
        or any(sorted(x) != list(ARMS) for x in allocation.values())):
        raise ValueError("must preallocate randomized balanced A/B before calls")
    result = {
        "schema": OUTPUT_SCHEMA, "status": "running",
        "G0": "NOT_PASSED", "model": MODEL, "feedback_regime": "RF",
        "research_question": "UNALTERED_ORIGINAL_Q1_Q2_THESIS",
        "study_fixture_sha256": _hash(d),
        "source_cases_public_not_sealed": True,
        "same_model_and_normal_notes_both_conditions": True,
        "only_seed_slot_differs_between_AB": True,
        "allocation_mode": ALLOCATION_MODE,
        "allocation_frozen_before_first_provider_call": True,
        "recorded_allocation": {
            cid: list(pair) for cid, pair in allocation.items()
        },
        "later_questions_are_model_generated": True,
        "no_real_derived_action_feedback": True,
        "q1_internal_activation_not_observed": True,
        "q2_new_later_investigability_proven": False,
        "independent_semantic_review_completed": False,
        "cases": [],
    }
    def save() -> None:
        if on_change: on_change(deepcopy(result))
    save()
    for case in cases:
        provider = provider_factory(case["id"])
        case_output = {
            "case_id": case["id"], "family": case["family"],
            "status": "not_started",
        }
        result["cases"].append(case_output)
        save()
        def save_case(snapshot: dict) -> None:
            case_output.clear()
            case_output.update(snapshot)
            save()
        try:
            run_case(case, provider, arm_order=allocation[case["id"]],
                     on_change=save_case)
        except Exception as exc:
            # Continue the other predeclared cases but preserve each failed
            # attempted trajectory. No automatic retry, zero as outcome,
            # or replacement by an investigator-authored seed.
            case_output["status"] = "failed_incomplete_not_zero_effect"
            case_output["error_type"] = type(exc).__name__
            case_output["not_an_independent_negative_finding"] = True
            case_output["provider"] = _provider_receipts(provider)
            save()
    statuses = [x["status"] for x in result["cases"]]
    result["study_counts"] = {
        "cases_attempted": len(statuses),
        "case_pairs_completed": statuses.count("completed_exploratory_pair"),
        "no_birth_opportunities": statuses.count(
            "completed_no_T0_seed_no_AB_opportunity"),
        "failed_or_incomplete": statuses.count(
            "failed_incomplete_not_zero_effect"),
        "inquiry_records": sum(
            len(t.get("research_arms", {}))
            for x in result["cases"] for t in x.get("turns", [])),
        "provider_model_calls": sum(
            x.get("provider", {}).get("model_calls_attempted", 0)
            for x in result["cases"]),
        "provider_embedding_calls": sum(
            x.get("provider", {}).get("embedding_calls_attempted", 0)
            for x in result["cases"]),
        "provider_reported_tokens": sum(
            x.get("provider", {}).get("reported_tokens", 0)
            for x in result["cases"]),
    }
    if len(statuses) != CASE_COUNT:
        raise RuntimeError("an investigator-selected case was silently omitted")
    result["status"] = (
        "completed_exploratory_with_gaps"
        if any(x == "failed_incomplete_not_zero_effect" for x in statuses)
        else "completed_exploratory_not_independently_reviewed"
    )
    save()
    return result


def review_packets(result: dict) -> tuple[dict, dict]:
    if result.get("status") not in {
        "completed_exploratory_with_gaps",
        "completed_exploratory_not_independently_reviewed",
    }:
        raise ValueError("incomplete study cannot be passed as review-ready")
    groups = []
    owner = {}
    for case in result["cases"]:
        if case.get("status") != "completed_exploratory_pair":
            continue
        case_row = {
            "case_id": case["case_id"],
            "family": case["family"],
            "same_case_for_both_answers": True,
            "source_t0_first_seed": case["first_seed"]["text"],
            "ordinary_note": case["ordinary_note"],
            "ordinary_dialogue": [
                {"turn": t["turn"], "question": t["question"],
                 "external_observation": t["new_observation"],
                 "ordinary_answer": t["host_answer"]}
                for t in case["turns"]],
            "paired_outputs": [],
        }
        for t in case["turns"][1:]:
            block = []
            for arm in ARMS:
                if arm not in t["research_arms"]:
                    raise ValueError("missing arm in complete case")
                item = t["research_arms"][arm]
                code = secrets.token_hex(12)
                owner[code] = {
                    "case_id": case["case_id"], "turn": t["turn"], "arm": arm,
                    "prompt_sha256": item["prompt_sha256"]}
                block.append({
                    "sample_id": code,
                    "model_output": item["text"],
                    "parser_status": item["parsed"]["status"],
                    "reviewer_1": {"retained_unverified_hypothesis": None,
                                   "different_inquiry_family": None,
                                   "independently_testable": None,
                                   "dependent_second_question": None,
                                   "reason": None},
                    "reviewer_2": {"retained_unverified_hypothesis": None,
                                   "different_inquiry_family": None,
                                   "independently_testable": None,
                                   "dependent_second_question": None,
                                   "reason": None},
                })
            secrets.SystemRandom().shuffle(block)
            case_row["paired_outputs"].append(
                {"turn": t["turn"], "outputs": block})
        groups.append(case_row)
    return ({
        "schema": "shadowseed-multicase-real-ab-blind-review-v1",
        "independent_human_review_completed": False,
        "G0": "NOT_PASSED",
        "conditions_human_raters_must_not_see": True,
        "no_AB_causal_effect_validated": True,
        "case_groups": groups,
    }, {
        "schema": "shadowseed-multicase-real-ab-owner-key-v1",
        "do_not_share_with_raters_until_both_done": True,
        "sample_to_arm": owner,
    })


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--blind-output", type=Path, required=True)
    ap.add_argument("--owner-output", type=Path, required=True)
    args = ap.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    validate_design(fixture)
    for p in (args.output, args.blind_output, args.owner_output):
        p.parent.mkdir(parents=True, exist_ok=True)
    def persist(s: dict) -> None:
        args.output.write_text(json.dumps(
            s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    def provider_factory(_cid: str) -> BoundedProvider:
        return BoundedProvider(
            os.environ.get("OPENAI_API_KEY", ""),
            model_call_cap=CALL_CAP, embedding_call_cap=EMBED_CAP,
            all_token_cap=TOKEN_CAP, output_token_cap=OUTPUT_CAP,
        )
    result = run_study(fixture, provider_factory, on_change=persist)
    blind, unblind = review_packets(result)
    args.blind_output.write_text(json.dumps(
        blind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.owner_output.write_text(json.dumps(
        unblind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "G0": "NOT_PASSED",
        "study_counts": result["study_counts"],
        "human_review_completed": False,
        "Q1_or_Q2_theory_proven": False,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
