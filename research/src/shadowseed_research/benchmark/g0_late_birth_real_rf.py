"""Real-Engine, five-turn RF exploratory study with early/late birth cohorts.

NO effect claim and NO automatic paid run. This research-sidecar uses the real
current-pair OpenAI detector, real Engine intake, canonical first birth,
chronological zero-authority followups, and separate inquiry prompts.

On the first of two post-birth inquiry turns A=NONE, B=exact real seed, and
C=neutral character-length placebo. The ordinary host NEVER sees any arm.
At the second inquiry, each arm receives ONLY its own unexecuted prior
questions. RF observations are researcher-written, never RI tool results.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import secrets
from typing import Any, Callable

from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import OpenAIDetectorBackend
from shadowseed_research.benchmark.g0_multicase_real_ab import (
    _parse_research, _provider_receipts,
)
from shadowseed_research.benchmark.g0_late_birth_cohort import (
    ProspectiveBirthCohort, TURN_COUNT,
)
from shadowseed_research.benchmark.g0_next_inquiry_readiness import (
    INQUIRY_INSTRUCTIONS_V2, MAX_CHARS, _common_history, _tail, _sha_json,
    check_output_contract, prepare_inquiry_pair,
)
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider, DetectorClientBridge, NoneDetector,
    HOST_INSTRUCTIONS, DETECTOR_INSTRUCTIONS, _host_prompt,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    NOTES_INSTRUCTIONS, _user_input,
)

SCHEMA = "shadowseed-g0-prospective-birth-rf-v2"
OUTPUT_SCHEMA = "shadowseed-g0-late-birth-rf-observation-v2"
MODEL = "gpt-5"
ARMS = ("A", "B", "C")
CASE_COUNT = 6
MODEL_CAP = 19
EMBED_CAP = 48
TOKEN_CAP = 65000
OUTPUT_CAP = 4096
MAX_INQUIRY_ROUNDS = 2
PLACEBO_BASIS = (
    "De kleurcode van een lege verzenddoos heeft geen aantoonbaar verband "
    "met de beschreven waarnemingen. "
)
VALID_FAMILIES = {
    "instrument_affordance", "condition_reframing",
    "relational_dependency", "negative_no_opportunity",
}


def validate_design(data: Any) -> list[dict]:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("incorrect new fixed study schema")
    if data.get("model") != MODEL or data.get("feedback_regime") != "RF":
        raise ValueError("model or external feedback regime differs")
    if (data.get("status") != "EXPLORATORY_NOT_G0_APPROVED"
        or data.get("outcome") != "NOT_RUN"):
        raise ValueError("no approved real outcomes or G0 decision in fixture")
    if (
        data.get("case_count") != CASE_COUNT
        or data.get("case_order") != [f"LB27-C{i:02d}" for i in range(1, 7)]
        or data.get("predeclared_cohorts") != {"T0_ONLY": 2, "T1_T2_ONLY": 4}
        or data.get("treatment_arms") != [
            "A_NONE", "B_REAL_SEED", "C_NEUTRAL_CHAR_MATCHED_PLACEBO"
        ]
    ):
        raise ValueError("predeclared case sequence or treatment changed")
    limits = data.get("limits", {})
    if limits != {
        "max_model_calls_per_case": MODEL_CAP,
        "max_embeddings_per_case": EMBED_CAP,
        "max_provider_tokens_per_case": TOKEN_CAP,
        "max_prompt_chars": MAX_CHARS,
        "max_output_tokens": OUTPUT_CAP, "no_retry": True,
    }:
        raise ValueError("research provider budget altered")
    inv = data.get("status_policy", {})
    if not isinstance(inv, dict) or not all(inv.get(k) is True for k in (
        "select_earliest_eligible_real_birth",
        "two_inquiry_turns_after_birth",
        "record_noneligible_and_too_late_births",
        "no_seed_and_failed_paths_keep_original_denominator",
        "no_semantic_or_causal_effect_without_independent_review",
    )):
        raise ValueError("falsification or cohort invariants removed")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) != CASE_COUNT:
        raise ValueError("all six case slots must be present")
    if [x.get("id") for x in cases] != data["case_order"]:
        raise ValueError("case identities or order not frozen")
    cohorts = {"T0_ONLY": 0, "T1_T2_ONLY": 0}
    families = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("case must be an object")
        if any(k in case for k in (
            "answer_key", "expected_seed", "birth_turn",
            "winning_arm", "target_question", "target_terms",
        )):
            raise ValueError("scripted birth or target result forbidden")
        cid = case["id"]
        family, cohort = case.get("family"), case.get("selection_window")
        if family not in VALID_FAMILIES or cohort not in cohorts:
            raise ValueError("unknown family or birth cohort")
        families.add(family)
        cohorts[cohort] += 1
        if not isinstance(case.get("context"), str) or not (
            140 < len(case["context"]) < 2400
        ):
            raise ValueError(f"{cid}: missing canonical opening context")
        turns = case.get("turns")
        if not isinstance(turns, list) or len(turns) != TURN_COUNT:
            raise ValueError(f"{cid}: exactly five turns for late birth")
        for t, turn in enumerate(turns):
            if not isinstance(turn, dict) or set(turn) != {
                "question", "new_observation",
            }:
                raise ValueError(f"{cid}: malformed turn")
            q, obs = turn["question"], turn["new_observation"]
            if (not isinstance(q, str) or not 20 <= len(q) <= 750
                or not isinstance(obs, str) or len(obs) > 1400
                or (t == 0 and obs) or (t > 0 and not obs)):
                raise ValueError(f"{cid}: future leakage or invalid turn {t}")
    if cohorts != data["predeclared_cohorts"] or (
        "negative_no_opportunity" not in families
        or len(families) < 4
    ):
        raise ValueError("missing negative control, cohort or mechanism")
    banned = data.get("prohibited_claims", [])
    if not isinstance(banned, list) or any(x not in banned for x in (
        "G0_PASS", "Q1_internal_absence", "Q2_world_expansion",
        "independent_holdout", "real_RI_feedback",
    )):
        raise ValueError("scientific claim prohibitions removed")
    check_output_contract()
    return cases


def neutral_placebo(seed: str) -> str:
    """Same characters, NOT same tokens, semantics, or credibility."""
    if not isinstance(seed, str) or not 40 <= len(seed) <= 2000:
        raise ValueError("unusual candidate length: do not silently pad it")
    placebo = (PLACEBO_BASIS * (len(seed) // len(PLACEBO_BASIS) + 1))[:len(seed)]
    if len(placebo) != len(seed) or seed in placebo:
        raise ValueError("placebo not distinct")
    return placebo


def prepare_inquiry_triplet(
    case: dict, prior: list[tuple[str, str]], ordinary_note: str,
    seed: str, turn: int, *, birth_turn: int,
    own_earlier: dict[str, dict | None],
) -> dict[str, Any]:
    """Matched A/B/C first inquiry; own-question divergence thereafter."""
    if set(own_earlier) != set(ARMS) or birth_turn not in (0, 1, 2):
        raise ValueError("invalid three-arm longitudinal research track")
    if turn not in (birth_turn + 1, birth_turn + 2):
        raise ValueError("not one of two post-birth inquiry turns")
    first = birth_turn + 1
    pair = prepare_inquiry_pair(
        case, prior, ordinary_note, seed, turn,
        {"A": own_earlier["A"], "B": own_earlier["B"]},
        first_inquiry_turn=first,
    )
    if first == turn and own_earlier["C"] is not None:
        raise ValueError("C first inquiry cannot see earlier questions")
    if own_earlier["C"] is not None and not isinstance(own_earlier["C"], dict):
        raise ValueError("invalid C prior question record")
    common = _common_history(case, prior, ordinary_note, turn)
    placebo = neutral_placebo(seed)
    suffix = _tail(own_earlier["C"], turn, first_inquiry_turn=first)
    prompt = common + placebo + suffix
    if seed in prompt or len(prompt) > MAX_CHARS:
        raise ValueError("C placebo leaked seed or exceeded prompt limit")
    prompts = dict(pair["prompts"])
    prompts["C"] = {
        "prompt": prompt, "prompt_sha256": _sha_json(prompt),
        "prompt_chars": len(prompt), "arm": "C", "turn": turn,
        "own_prior_questions_only": turn > first,
        "external_action_executed": False,
    }
    if turn == first:
        a, b, c = (prompts[arm]["prompt"] for arm in ARMS)
        if not (
            a.replace(common + "NONE" + suffix, common + seed + suffix) == b
            and a.replace(common + "NONE" + suffix, common + placebo + suffix) == c
        ):
            raise ValueError("first inquiry differs outside candidate slot")
    return {
        "schema": "shadowseed-g0-next-inquiry-triplet-v1",
        "G0": "NOT_PASSED", "first_inquiry_turn": first,
        "chosen_birth_turn": birth_turn,
        "shared_instructions_sha256": _sha_json(INQUIRY_INSTRUCTIONS_V2),
        "matched_at_first_inquiry_except_candidate_slot": True,
        "placebo_character_length_equals_seed": True,
        "placebo_content_or_tokens_not_matched": True,
        "not_independently_reviewed": True,
        "prompts": prompts,
    }


def run_case(
    case: dict, provider: BoundedProvider, *,
    order: tuple[str, str, str],
    on_change: Callable[[dict], None] | None = None,
) -> dict:
    if sorted(order) != list(ARMS):
        raise ValueError("preallocated A/B/C order required")
    if (
        provider.model_call_cap != MODEL_CAP
        or provider.embedding_call_cap != EMBED_CAP
        or provider.all_token_cap != TOKEN_CAP
        or provider.output_token_cap != OUTPUT_CAP
    ):
        raise ValueError("not an approved bounded study provider")
    detector = OpenAIDetectorBackend(
        model_id=MODEL, prompt_variant="current_pair",
    )
    bridge = DetectorClientBridge(provider)
    detector.client = bridge
    live = ShadowseedEngine(
        detector_backend=detector, embedding_fn=provider.embed,
        recurrence_mode="pairwise", gate_policy_id="evidence_backed",
        max_seeds_per_turn=3,
    )
    none = ShadowseedEngine(
        detector_backend=NoneDetector(), embedding_backend="lexical",
        allow_toy_embedder=True, recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    cohort = ProspectiveBirthCohort(case["id"], case["selection_window"])
    normal_history: list[tuple[str, str]] = []
    earlier: dict[str, dict | None] = {arm: None for arm in ARMS}
    note: str | None = None
    out: dict[str, Any] = {
        "case_id": case["id"], "family": case["family"],
        "selection_window": case["selection_window"],
        "status": "running_exploratory", "research_order_first": list(order),
        "turns": [], "ordinary_note_owner_only": None, "cohort": None,
        "provider": {}, "G0": "NOT_PASSED",
        "ordinary_host_untreated": True,
        "real_external_action_performed": False,
    }

    def save() -> None:
        out["provider"] = _provider_receipts(provider)
        out["cohort"] = cohort.snapshot()
        if on_change:
            on_change(deepcopy(out))

    save()
    for i, turn in enumerate(case["turns"]):
        user = _user_input(case, turn)
        host_prompt = _host_prompt(
            case, normal_history, turn["question"], turn["new_observation"],
        )
        prepared = live.prepare_turn(user)
        control = none.prepare_turn(user)
        if any((
            prepared.model_context, prepared.selected_seed_ids,
            prepared.surfaced_seed_ids, control.model_context,
        )):
            raise RuntimeError("ordinary host received candidate or Gate influence")
        answer = provider.generate(
            stage=f"host_t{i}", case_id=case["id"],
            prompt=host_prompt, instructions=HOST_INSTRUCTIONS,
        )
        bridge.case_id, bridge.turn = case["id"], i
        observed = live.observe_turn(prepared, answer)
        neutral = none.observe_turn(control, answer)
        if (
            neutral["answer"] != answer
            or none.inspect()["seeds"]
        ):
            raise RuntimeError("NONE control deviated from unmodified host")
        row = {
            "turn": i, "user_input": user, "host_answer": answer,
            "detector_raw": detector.last_raw_output,
            "canonical_report": observed,
            "cohort_turn": None,
            "research_arms": {},
            "ordinary_control_identical": True,
        }
        out["turns"].append(row)
        save()
        try:
            row["cohort_turn"] = cohort.observe(live, observed, i)
        except Exception:
            save()  # Persist safe checkpoint failure before fail-closed exit.
            raise
        save()
        if cohort.birth_turn == i:
            # Normal note has NO access to selected seed or research arm.
            history_for_note = normal_history + [(user, answer)]
            text = [
                "FICTIEVE BEGINCASUS:", case["context"],
                "ALLE NORMALE VRAAG/ANTWOORDPAREN TOT NU:",
            ]
            for j, (q, a) in enumerate(history_for_note):
                text.extend([f"VRAAG {j}: {q}", f"ANTWOORD {j}: {a}"])
            note = provider.generate(
                stage=f"ordinary_note_birth_t{i}", case_id=case["id"],
                prompt="\n".join(text), instructions=NOTES_INSTRUCTIONS,
            )
            out["ordinary_note_owner_only"] = note
            save()
        birth_turn = cohort.birth_turn
        if (
            birth_turn is not None
            and i in (birth_turn + 1, birth_turn + 2)
        ):
            if note is None or cohort.seed_text is None:
                raise RuntimeError("missing authentic birth or ordinary note")
            prior = normal_history + [(user, answer)]
            triplet = prepare_inquiry_triplet(
                case, prior, note, cohort.seed_text, i,
                birth_turn=birth_turn, own_earlier=earlier,
            )
            current_order = order if i == birth_turn + 1 else order[1:] + order[:1]
            for arm in current_order:
                item = triplet["prompts"][arm]
                raw = provider.generate(
                    stage=f"inquiry_birth_t{birth_turn}_t{i}_{arm}",
                    case_id=case["id"], prompt=item["prompt"],
                    instructions=INQUIRY_INSTRUCTIONS_V2,
                )
                parsed = _parse_research(raw)
                row["research_arms"][arm] = {
                    "text": raw, "parsed": parsed,
                    "prompt_sha256": item["prompt_sha256"],
                    "prompt_chars": item["prompt_chars"],
                    "seed_exposed": arm == "B",
                    "placebo_exposed": arm == "C",
                    "own_previous_questions_only": i > birth_turn + 1,
                    "external_test_executed": False,
                    "independent_review_completed": False,
                }
                earlier[arm] = parsed if parsed["status"] in {
                    "valid_questions", "valid_none",
                } else None
                save()
        normal_history.append((user, answer))
        save()
    if live.audit() or none.audit() or live.inspect()["influence_records"]:
        raise RuntimeError("Engine audit or ordinary answer influence failed")
    status = cohort.final_status()
    if status not in (
        "TWO_CANONICAL_FOLLOWUPS_NO_Q2_CLAIM",
        "NO_ELIGIBLE_BIRTH_NOT_Q2_ZERO",
    ):
        raise RuntimeError("incomplete actual-engine cohort")
    out["status"] = (
        "complete_six_inquiry_records" if cohort.selected_id
        else "no_eligible_birth_not_zero_effect"
    )
    save()
    return out


def run_study(
    d: dict, provider_factory: Callable[[str], BoundedProvider],
    *, on_change: Callable[[dict], None] | None = None,
    allocation: dict[str, tuple[str, str, str]] | None = None,
) -> dict:
    cases = validate_design(d)
    if allocation is None:
        first = ["A", "A", "B", "B", "C", "C"]
        secrets.SystemRandom().shuffle(first)
        allocation = {}
        for case, arm in zip(cases, first):
            other = [x for x in ARMS if x != arm]
            secrets.SystemRandom().shuffle(other)
            allocation[case["id"]] = (arm, *other)
    if (
        set(allocation) != {c["id"] for c in cases}
        or sorted(x[0] for x in allocation.values())
            != ["A", "A", "B", "B", "C", "C"]
        or any(sorted(x) != list(ARMS) for x in allocation.values())
    ):
        raise ValueError("balanced A/B/C first-arm allocation required before calls")
    study = {
        "schema": OUTPUT_SCHEMA, "G0": "NOT_PASSED",
        "status": "running_no_confirmatory_claim",
        "model": MODEL, "feedback_regime": "RF",
        "fixture_sha256": _sha_json(d),
        "allocation_frozen_before_first_provider_call": True,
        "allocation_owner_only": {k: list(v) for k, v in allocation.items()},
        "all_cases_public_and_investigator_authored": True,
        "independent_semantic_review_completed": False,
        "human_G0_review_completed": False,
        "Q1_internal_representation_observed": False,
        "Q2_later_world_expansion_proven": False,
        "real_RI_actions_executed": False,
        "cases": [],
    }
    def save() -> None:
        if on_change: on_change(deepcopy(study))
    save()
    for case in cases:
        provider = provider_factory(case["id"])
        row = {
            "case_id": case["id"], "family": case["family"],
            "selection_window": case["selection_window"],
            "status": "not_started",
        }
        study["cases"].append(row)
        save()
        def save_case(snapshot: dict) -> None:
            row.clear()
            row.update(snapshot)
            save()
        try:
            run_case(case, provider, order=allocation[case["id"]],
                     on_change=save_case)
        except Exception as exc:
            row["status"] = "failed_incomplete_not_zero_effect"
            row["error_class"] = type(exc).__name__
            row["no_inference_from_failure"] = True
            row["provider"] = _provider_receipts(provider)
            save()
    statuses = [x["status"] for x in study["cases"]]
    study["counts"] = {
        "case_slots_attempted": len(statuses),
        "six_inquiry_record_cases": statuses.count("complete_six_inquiry_records"),
        "no_eligible_birth": statuses.count("no_eligible_birth_not_zero_effect"),
        "failed_or_incomplete": statuses.count("failed_incomplete_not_zero_effect"),
        "raw_inquiry_records": sum(
            len(t.get("research_arms", {}))
            for c in study["cases"] for t in c.get("turns", [])
        ),
        "valid_inquiry_records": sum(
            item.get("parsed", {}).get("status") in {
                "valid_questions", "valid_none",
            }
            for c in study["cases"] for t in c.get("turns", [])
            for item in t.get("research_arms", {}).values()
        ),
        "model_calls_attempted": sum(
            c.get("provider", {}).get("model_calls_attempted", 0)
            for c in study["cases"]
        ),
        "embedding_calls_attempted": sum(
            c.get("provider", {}).get("embedding_calls_attempted", 0)
            for c in study["cases"]
        ),
        "provider_reported_tokens": sum(
            c.get("provider", {}).get("reported_tokens", 0)
            for c in study["cases"]
        ),
    }
    if len(statuses) != CASE_COUNT:
        raise RuntimeError("missing attempted case in original denominator")
    study["status"] = (
        "incomplete_observational_pilot" if study["counts"]["failed_or_incomplete"]
        else "complete_observational_pilot_not_independently_reviewed"
    )
    save()
    return study


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    d = json.loads(args.fixture.read_text(encoding="utf-8"))
    validate_design(d)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    def persist(snapshot: dict) -> None:
        args.output.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    def provider_factory(cid: str) -> BoundedProvider:
        return BoundedProvider(
            os.environ.get("OPENAI_API_KEY", ""),
            model_call_cap=MODEL_CAP, embedding_call_cap=EMBED_CAP,
            all_token_cap=TOKEN_CAP, output_token_cap=OUTPUT_CAP,
        )
    result = run_study(d, provider_factory, on_change=persist)
    print(json.dumps({
        "G0": "NOT_PASSED", "status": result["status"],
        "counts": result["counts"], "independent_review": False,
    }), flush=True)


if __name__ == "__main__":
    main()
