"""2026-10-27 prospective, exploratory dual-model REAL Shadowseed A/B.

Two real models each run their own unmodified ShadowseedEngine and detector.
The only research-arm difference inside one model/case is the exact true
weightless seed versus NONE. Both models see the same authored RF world but
may generate different ordinary histories and seeds. This is a *pipeline*
comparison, NOT a claim that the two seeds or Q2 discoveries are identical.

G0 NOT PASSED. No RI action, no independent discovery, no product change.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import argparse
import json
import os
from pathlib import Path
import secrets
from typing import Any, Callable

from shadowseed import ShadowseedEngine
from shadowseed.detection.model_detector import OpenAIDetectorBackend
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider, DetectorClientBridge, NoneDetector,
    HOST_INSTRUCTIONS, DETECTOR_INSTRUCTIONS, MAX_PROMPT_CHARS,
    _host_prompt,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    NOTES_INSTRUCTIONS, _user_input,
)
from shadowseed_research.benchmark.g0_multicase_real_ab import (
    _parse_research, _provider_receipts,
)
from shadowseed_research.benchmark.g0_birth_cohort_v2 import (
    select_first_eligible_birth,
)
from shadowseed_research.benchmark.g0_next_inquiry_readiness import (
    INQUIRY_INSTRUCTIONS_V2, prepare_inquiry_pair,
    safe_checkpoint_failure, check_output_contract, _sha_json,
)
from shadowseed_research.benchmark.weightless_longitudinal_handoff import (
    freeze_weightless_followup,
)

SCHEMA = "shadowseed-dual-model-four-turn-rf-ab-v1"
OUTPUT_SCHEMA = "shadowseed-g0-dual-model-gpt5-luna-observed-v1"
MODEL_IDS = ("gpt-5-2025-08-07", "gpt-6-luna")
CASE_COUNT = 6
TURN_COUNT = 4
MODEL_CALL_CAP = 16
EMBEDDING_CAP = 24
TOKEN_CAP = 65000
OUTPUT_CAP = 4096
ARMS = ("A", "B")
FAMILIES = {
    "condition_reframing", "instrument_affordance",
    "relational_dependency", "negative_no_opportunity",
}
FAILSAFE_STATUSES = {
    "complete_pair_birth_T0", "complete_pair_birth_T1",
    "no_eligible_birth_with_late_birth", "no_seed_at_any_turn",
    "failed_partial_not_zero",
}


def validate_trial(fixture: dict) -> list[dict]:
    if not isinstance(fixture, dict) or fixture.get("schema") != SCHEMA:
        raise ValueError("unrecognized, unpublished dual-model protocol")
    if (
        fixture.get("design_date") != "2026-10-27"
        or fixture.get("status") != "EXPLORATORY_NOT_G0_CONFIRMED"
        or fixture.get("model_ids") != list(MODEL_IDS)
        or fixture.get("feedback_regime") != "RF"
        or fixture.get("case_count") != CASE_COUNT
        or fixture.get("independent_evaluation_completed") is not False
        or fixture.get("ordinary_host_must_remain_seed_blind") is not True
    ):
        raise ValueError("unsupported dual-model design or dishonest G0 claim")
    expected = [f"DM26-C{i:02d}" for i in range(1, CASE_COUNT + 1)]
    cases = fixture.get("cases")
    if (
        not isinstance(cases, list)
        or len(cases) != CASE_COUNT
        or [c.get("id") for c in cases] != expected
        or fixture.get("case_order") != expected
    ):
        raise ValueError("all six predeclared cases must be included")
    invariants = fixture.get("study_invariants")
    if not isinstance(invariants, dict) or any(
        invariants.get(k) != val for k, val in {
            "per_model_case_max_model_calls": MODEL_CALL_CAP,
            "per_model_case_max_embedding_calls": EMBEDDING_CAP,
            "per_model_case_max_reported_tokens": TOKEN_CAP,
            "max_output_tokens": OUTPUT_CAP,
            "reasoning_effort": "low",
            "one_shot_no_retry": True,
            "minimum_two_later_turns": True,
            "first_eligible_birth_T0_or_T1": True,
            "no_birth_and_late_birth_never_zero_effect": True,
            "independent_review_required": True,
        }.items()
    ):
        raise ValueError("trial budget or evidence constraints changed")
    if "G0_PASS" not in fixture.get("claims_not_supported", []):
        raise ValueError("Q1/Q2/G0 limitations must be explicit")
    for case in cases:
        if (
            case.get("family") not in FAMILIES
            or not isinstance(case.get("context"), str)
            or not 140 < len(case["context"]) < 2500
            or any(k in case for k in (
                "expected_seed", "winning_arm", "ideal_question",
                "target_question", "answer_key", "reward"
            ))
        ):
            raise ValueError("case lacks provenance or contains a target answer")
        turns = case.get("turns")
        if not isinstance(turns, list) or len(turns) != TURN_COUNT:
            raise ValueError("must retain exactly four observed turns")
        for i, turn in enumerate(turns):
            if (
                not isinstance(turn, dict)
                or set(turn) != {"question", "new_observation"}
                or not isinstance(turn["question"], str)
                or not 20 <= len(turn["question"]) <= 750
                or not isinstance(turn["new_observation"], str)
                or len(turn["new_observation"]) > 1400
                or (i == 0 and turn["new_observation"])
                or (i > 0 and len(turn["new_observation"]) < 25)
            ):
                raise ValueError("invalid chronological turn or leaked observation")
    if set(x["family"] for x in cases) != FAMILIES:
        raise ValueError("research mechanisms and negative control incomplete")
    check_output_contract()
    return cases


class DualModelProvider(BoundedProvider):
    """Use the *existing* provider caps and embedding backend, never retry.

    Only override text completion so actual requested/returned model, token
    use and provenance are recorded without the old GPT-5-only hardcoding.
    """

    def __init__(self, key: str, *, model_id: str, transport: Any = None):
        if model_id not in MODEL_IDS:
            raise ValueError("model not approved in frozen exploratory design")
        super().__init__(
            key, transport=transport, model_call_cap=MODEL_CALL_CAP,
            embedding_call_cap=EMBEDDING_CAP, all_token_cap=TOKEN_CAP,
            output_token_cap=OUTPUT_CAP,
        )
        self.model_id = model_id

    def generate(self, *, stage: str, case_id: str, prompt: str,
                 instructions: str) -> str:
        if self.model_calls >= self.model_call_cap:
            raise RuntimeError("hard model-call cap reached")
        if self.total_tokens > self.all_token_cap - (self.output_token_cap + 1200):
            raise RuntimeError("insufficient remaining token budget")
        if not isinstance(prompt, str) or not 1 <= len(prompt) <= MAX_PROMPT_CHARS:
            raise ValueError("invalid or oversized model prompt")
        self.model_calls += 1  # pessimistic, even for a provider rejection
        response = self._post("responses", {
            "model": self.model_id,
            "instructions": instructions,
            "input": prompt,
            "max_output_tokens": self.output_token_cap,
            "reasoning": {"effort": "low"},
            "store": False,
        })
        usage = response.get("usage")
        if not isinstance(usage, dict):
            raise RuntimeError("model usage absent: cannot enforce budget")
        inp, out = usage.get("input_tokens"), usage.get("output_tokens")
        if type(inp) is not int or type(out) is not int:
            raise RuntimeError("model returned invalid token counts")
        self._consume(inp)
        self._consume(out)
        text = "\n".join(
            piece["text"]
            for item in response.get("output", [])
            if isinstance(item, dict)
            for piece in item.get("content", [])
            if isinstance(piece, dict)
            and piece.get("type") == "output_text"
            and isinstance(piece.get("text"), str)
        ).strip()
        returned_model = response.get("model")
        ok_model = (
            returned_model == self.model_id
            or (isinstance(returned_model, str)
                and returned_model.startswith(self.model_id + "-"))
        )
        self.events.append({
            "kind": "model", "stage": stage, "case_id": case_id,
            "requested_model": self.model_id, "returned_model": returned_model,
            "status": response.get("status"),
            "response_id": response.get("id"),
            "prompt_sha256": _sha_json(prompt),
            "response_sha256": _sha_json(text),
            "input_tokens": inp, "output_tokens": out,
            "model_identity_match": ok_model,
        })
        # Do not log model content or credential.
        print(json.dumps({
            "model": self.model_id, "case": case_id, "stage": stage,
            "status": response.get("status"),
            "calls": self.model_calls, "tokens": self.total_tokens,
        }), flush=True)
        if not ok_model:
            raise RuntimeError("provider model identity changed from pinned request")
        if response.get("status") != "completed" or not text:
            raise RuntimeError("model returned no complete visible text")
        return text


def _receipts(provider: BoundedProvider) -> dict:
    receipt = _provider_receipts(provider)
    receipt["model_id"] = provider.model_id
    return receipt


def run_model_case(
    case: dict, provider: DualModelProvider, *,
    arm_order: tuple[str, str],
    on_change: Callable[[dict], None] | None = None,
) -> dict:
    if tuple(sorted(arm_order)) != ARMS or provider.model_id not in MODEL_IDS:
        raise ValueError("invalid model or A/B allocation")
    detector = OpenAIDetectorBackend(
        model_id=provider.model_id, prompt_variant="current_pair",
    )
    bridge = DetectorClientBridge(provider)
    detector.client = bridge
    engine = ShadowseedEngine(
        detector_backend=detector, embedding_fn=provider.embed,
        recurrence_mode="pairwise", gate_policy_id="evidence_backed",
        max_seeds_per_turn=3,
    )
    none = ShadowseedEngine(
        detector_backend=NoneDetector(), embedding_backend="lexical",
        allow_toy_embedder=True, recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    result = {
        "case_id": case["id"], "family": case["family"],
        "model_id": provider.model_id, "status": "running",
        "first_seed": None, "birth": None, "ordinary_note": None,
        "ordinary_t0_samples": [], "turns": [],
        "T0_or_T1_birth_selected": False,
        "born_too_late_turns": [],
        "arm_order": list(arm_order),
        "ordinary_answer_seed_influence": False,
        "G0": "NOT_PASSED", "provider": {},
    }

    def save() -> None:
        result["provider"] = _receipts(provider)
        if on_change is not None:
            on_change(deepcopy(result))

    save()
    chosen = None
    birth = None
    birth_turn: int | None = None
    previous_checkpoint = None
    normal_history: list[tuple[str, str]] = []
    earlier: dict[str, dict | None] = {"A": None, "B": None}
    completed_inquiry_rounds = 0

    for i, turn in enumerate(case["turns"]):
        user_input = _user_input(case, turn)
        ordinary_prompt = _host_prompt(
            case, normal_history, turn["question"], turn["new_observation"],
        )
        if i == 0:
            for replicate in (1, 2):
                result["ordinary_t0_samples"].append(provider.generate(
                    stage=f"t0_ordinary_replicate_{replicate}",
                    case_id=case["id"], prompt=ordinary_prompt,
                    instructions=HOST_INSTRUCTIONS,
                ))
                save()
        prepared = engine.prepare_turn(user_input)
        control_prepared = none.prepare_turn(user_input)
        if any((
            prepared.model_context, prepared.selected_seed_ids,
            prepared.surfaced_seed_ids, control_prepared.model_context,
        )):
            raise RuntimeError("shadow seed entered ordinary answer prompt")
        answer = provider.generate(
            stage=f"host_t{i}", case_id=case["id"],
            prompt=ordinary_prompt, instructions=HOST_INSTRUCTIONS,
        )
        bridge.case_id, bridge.turn = case["id"], i
        report = engine.observe_turn(prepared, answer)
        no_report = none.observe_turn(control_prepared, answer)
        if no_report["answer"] != answer or none.inspect()["seeds"]:
            raise RuntimeError("ordinary no-SSL parity failed")
        row = {
            "turn": i, "question": turn["question"],
            "new_observation": turn["new_observation"],
            "user_input": user_input, "host_answer": answer,
            "detector_raw": detector.last_raw_output,
            "canonical_report": report,
            "followup": None, "research_arms": {},
            "ordinary_control_identical": True,
        }
        result["turns"].append(row)
        save()

        if chosen is None:
            decision = select_first_eligible_birth(
                engine, report, turn=i, total_turns=TURN_COUNT,
            )
            if decision.status == "selected_real_weightless_birth":
                chosen, birth, birth_turn = decision.seed_id, decision.checkpoint, i
                state = engine.export_state()
                matches = [
                    seed for seed in state["manager"]["seeds"]
                    if seed.get("id") == chosen
                ]
                if len(matches) != 1:
                    raise RuntimeError("first canonical accepted seed ambiguous")
                seed = matches[0]
                if seed.get("weight") != 0 or seed.get("evidence_count") != 0:
                    raise RuntimeError("seed was given unearned authority")
                if sha256(seed["text"].encode()).hexdigest() != birth["candidate_text_sha256"]:
                    raise RuntimeError("selected seed has changed identity")
                result["first_seed"] = {
                    "id": chosen, "text": seed["text"],
                    "birth_turn": birth_turn,
                    "birth_snapshot_sha256": birth["snapshot_sha256"],
                    "weight": 0, "evidence_count": 0,
                    "selection": "first_eligible_canonical_birth_T0_or_T1",
                }
                result["birth"] = birth
                result["T0_or_T1_birth_selected"] = True
            elif decision.status == "real_birth_too_late_for_two_followups":
                result["born_too_late_turns"].append(i)
                save()
        else:
            try:
                row["followup"] = freeze_weightless_followup(
                    engine, birth, previous=previous_checkpoint,
                )
                previous_checkpoint = row["followup"]
                save()
            except ValueError as exc:
                row["checkpoint_failure"] = safe_checkpoint_failure(
                    exc, engine.export_state(), case_id=case["id"], turn=i,
                    birth=birth, previous=previous_checkpoint,
                )
                save()
                raise

        if i == 0:
            note_prompt = (
                "CASUS:\n" + case["context"]
                + "\nVRAAG:\n" + turn["question"]
                + "\nGEWOON ANTWOORD:\n" + answer
            )
            result["ordinary_note"] = provider.generate(
                stage="ordinary_note_t0", case_id=case["id"],
                prompt=note_prompt, instructions=NOTES_INSTRUCTIONS,
            )
            save()

        if birth_turn is not None and birth_turn < i <= birth_turn + 2:
            first_inquiry = birth_turn + 1
            prior = normal_history + [(user_input, answer)]
            try:
                pair = prepare_inquiry_pair(
                    case, prior, result["ordinary_note"],
                    result["first_seed"]["text"], i, earlier,
                    first_inquiry_turn=first_inquiry,
                )
            except ValueError as exc:
                row["inquiry_preflight_failure"] = {
                    "type": type(exc).__name__,
                    "reason": "prompt_cap_or_context_validation",
                    "reason_sha256": _sha_json(str(exc)),
                    "no_truncation_or_model_call": True,
                }
                save()
                raise
            order = arm_order if completed_inquiry_rounds == 0 else tuple(reversed(arm_order))
            for arm in order:
                p = pair["prompts"][arm]
                out = provider.generate(
                    stage=f"inquiry_T{i}_{arm}", case_id=case["id"],
                    prompt=p["prompt"], instructions=INQUIRY_INSTRUCTIONS_V2,
                )
                parsed = _parse_research(out)
                row["research_arms"][arm] = {
                    "text": out, "parsed": parsed,
                    "prompt_sha256": p["prompt_sha256"],
                    "prompt_chars": p["prompt_chars"],
                    "research_seed_exposure": arm == "B",
                    "inquiry_round": completed_inquiry_rounds + 1,
                    "prior_own_question_only": completed_inquiry_rounds > 0,
                    "external_test_executed": False,
                    "independent_human_review_completed": False,
                }
                # Even a syntactically invalid real response must not silently
                # disappear from later own-arm context as if the model said NONE.
                earlier[arm] = (
                    parsed if parsed["status"] in {"valid_questions", "valid_none"}
                    else {"invalid_unverified_raw_output": out,
                          "parser_reason": parsed.get("reason")}
                )
                save()
            completed_inquiry_rounds += 1

        normal_history.append((user_input, answer))
        save()

    if engine.audit() or none.audit() or engine.inspect()["influence_records"]:
        raise RuntimeError("product Engine or no-SSL control failed final audit")
    if birth_turn in (0, 1):
        if completed_inquiry_rounds != 2 or any(
            set(t["research_arms"]) != set(ARMS)
            for t in result["turns"][birth_turn + 1:birth_turn + 3]
        ):
            raise RuntimeError("real birth has no complete two-turn A/B")
        result["status"] = f"complete_pair_birth_T{birth_turn}"
    elif result["born_too_late_turns"]:
        result["status"] = "no_eligible_birth_with_late_birth"
    else:
        result["status"] = "no_seed_at_any_turn"
    save()
    return result


def run_comparison(
    fixture: dict, provider_factory: Callable[[str, str], DualModelProvider],
    *, on_change: Callable[[dict], None] | None = None,
    allocation: dict | None = None,
) -> dict:
    cases = validate_trial(fixture)
    if allocation is None:
        first = ["A"] * 3 + ["B"] * 3
        secrets.SystemRandom().shuffle(first)
        allocation = {
            case["id"]: {
                MODEL_IDS[0]: [a, "B" if a == "A" else "A"],
                MODEL_IDS[1]: ["B" if a == "A" else "A", a],
            }
            for case, a in zip(cases, first)
        }
    if (
        set(allocation) != {x["id"] for x in cases}
        or any(set(allocation[c["id"]]) != set(MODEL_IDS) for c in cases)
        or any(sorted(v) != list(ARMS)
               for c in cases for v in allocation[c["id"]].values())
        or any(sorted(allocation[c["id"]][MODEL_IDS[0]]) != list(ARMS)
               for c in cases)
        or any(
            allocation[c["id"]][MODEL_IDS[1]][0] == allocation[c["id"]][MODEL_IDS[0]][0]
            for c in cases
        )
        or sorted(allocation[c["id"]][MODEL_IDS[0]][0] for c in cases)
        != ["A"] * 3 + ["B"] * 3
    ):
        raise ValueError("allocation not prospectively balanced across models")
    result = {
        "schema": OUTPUT_SCHEMA, "G0": "NOT_PASSED",
        "status": "running", "models": list(MODEL_IDS),
        "feedback_regime": "RF",
        "source_cases_public_investigator_authored": True,
        "independent_human_review_completed": False,
        "external_RI_test_executed": False,
        "q1_internal_state_proven": False,
        "q2_new_later_investigability_proven": False,
        "matched_worlds_not_identical_model_histories_or_seed_texts": True,
        "study_fixture_sha256": _sha_json(fixture),
        "same_reasoning_effort_and_maximum_budget": True,
        "T0_T1_birth_separate_observed_cohorts": True,
        "allocation_recorded_before_first_provider_request": True,
        "randomized_balanced_arm_allocation": allocation,
        "cases": [], "counts": None,
    }

    def save() -> None:
        if on_change:
            on_change(deepcopy(result))
    save()

    for index, case in enumerate(cases):
        # Cross-case alternating model order controls a simple position bias.
        model_order = MODEL_IDS if index % 2 == 0 else tuple(reversed(MODEL_IDS))
        for model_id in model_order:
            item = {
                "case_id": case["id"], "family": case["family"],
                "model_id": model_id, "status": "not_started",
            }
            result["cases"].append(item)
            save()
            provider = provider_factory(model_id, case["id"])
            def checkpoint(snapshot: dict) -> None:
                item.clear()
                item.update(snapshot)
                save()
            try:
                run_model_case(
                    case, provider,
                    arm_order=tuple(allocation[case["id"]][model_id]),
                    on_change=checkpoint,
                )
            except Exception as exc:
                item["status"] = "failed_partial_not_zero"
                item["error_type"] = type(exc).__name__
                item["error_code"] = (
                    "provider_rejection_or_model_unavailable" if
                    "provider HTTP" in str(exc)
                    else "research_preflight_or_checkpoint_or_model_failure"
                )
                item["not_a_measured_zero_effect"] = True
                item["provider"] = _receipts(provider)
                save()

    status_counts = {x: sum(c["status"] == x for c in result["cases"])
                     for x in sorted(FAILSAFE_STATUSES)}
    totals = {
        "all_model_case_trajectories_attempted": len(result["cases"]),
        "per_model": {
            m: {x: sum(c["status"] == x and c["model_id"] == m
                       for c in result["cases"]) for x in sorted(FAILSAFE_STATUSES)}
            for m in MODEL_IDS
        },
        "status_counts": status_counts,
        "full_two_round_AB_trajectories": (
            status_counts["complete_pair_birth_T0"]
            + status_counts["complete_pair_birth_T1"]
        ),
        "provider_model_calls_attempted": sum(
            x.get("provider", {}).get("model_calls_attempted", 0)
            for x in result["cases"]),
        "provider_embedding_calls_attempted": sum(
            x.get("provider", {}).get("embedding_calls_attempted", 0)
            for x in result["cases"]),
        "provider_reported_tokens": sum(
            x.get("provider", {}).get("reported_tokens", 0)
            for x in result["cases"]),
    }
    if (
        len(result["cases"]) != CASE_COUNT * len(MODEL_IDS)
        or sum(status_counts.values()) != len(result["cases"])
        or totals["provider_model_calls_attempted"]
        > CASE_COUNT * len(MODEL_IDS) * MODEL_CALL_CAP
        or totals["provider_embedding_calls_attempted"]
        > CASE_COUNT * len(MODEL_IDS) * EMBEDDING_CAP
        or totals["provider_reported_tokens"]
        > CASE_COUNT * len(MODEL_IDS) * TOKEN_CAP
    ):
        raise RuntimeError("study census or hard budget inconsistent")
    result["counts"] = totals
    result["status"] = (
        "completed_exploratory_with_dropouts"
        if status_counts["failed_partial_not_zero"]
        else "completed_exploratory_without_claim_of_Q2"
    )
    save()
    return result


def make_seed_hidden_review(result: dict, fixture: dict) -> tuple[dict, dict]:
    """Strict next-study blind packet: hide seed, model, arm and parser status.

    Raw outputs are unmodified and may reveal arm style. The owner key holds
    all first-birth and per-model information. This is not a human review.
    """
    if result.get("schema") != OUTPUT_SCHEMA or result.get("G0") != "NOT_PASSED":
        raise ValueError("wrong model study for blind review")
    if result.get("study_fixture_sha256") != _sha_json(fixture):
        raise ValueError("source fixture hash mismatch")
    if not isinstance(result.get("counts"), dict):
        raise ValueError("incomplete original model/case census")
    blind = {
        "schema": "shadowseed-g0-dual-model-blind-human-review-v1",
        "G0": "NOT_PASSED",
        "human_reviews_received": 0,
        "arm_and_model_and_source_seed_hidden": True,
        "public_fixture_and_visible_wording_not_guaranteed_blind": True,
        "not_an_external_RI_test": True,
        "phase1_independently_rating_inquiry_quality_only": True,
        "rating_guide": (
            "Per twee-turn traject: onafhankelijke toetsbare vraag? "
            "Nieuwe conditie/relatie? Heeft T2 inhoudelijk iets nodig uit T1? "
            "Wordt een niet-getoetste hypothese slechts herhaald? "
            "Geef eigen tekstuele motivatie; geen Q2-resultaat toekennen."
        ),
        "cases_attempted_including_failures": len(result["cases"]),
        "case_groups": [],
    }
    owner = {
        "schema": "shadowseed-g0-dual-model-owner-only-unblind-v1",
        "G0": "NOT_PASSED",
        "never_share_until_two_independent_reviewers_submit": True,
        "reviewer_independence_not_automatically_verified": True,
        "model_case_census": [
            {"case_id": x["case_id"], "model_id": x["model_id"],
             "status": x["status"]}
            for x in result["cases"]
        ],
        "blind_track_mapping": {},
    }
    seen: set[str] = set()
    by_case = {c["id"]: c for c in fixture["cases"]}
    for item in result["cases"]:
        if item["status"] not in {"complete_pair_birth_T0", "complete_pair_birth_T1"}:
            continue
        cid = item["case_id"]
        turns = item.get("turns", [])
        seed = item.get("first_seed")
        if (
            not isinstance(seed, dict)
            or len(turns) != TURN_COUNT
            or not isinstance(seed.get("text"), str)
        ):
            raise ValueError("complete model result missing true seed")
        ordinary = [{
            "turn": x["turn"], "question": x["question"],
            "external_observation": x["new_observation"],
            "normal_answer": x["host_answer"],
        } for x in turns]
        common = {
            "original_context": by_case[cid]["context"],
            "ordinary_chronology_without_seed_or_notes": ordinary,
        }
        if seed["text"] in json.dumps(common, ensure_ascii=False):
            owner["model_case_census"].append({
                "case_id": cid, "model_id": item["model_id"],
                "note": "literal seed in common context, excluded from phase1",
            })
            continue
        group_id = secrets.token_hex(12)
        tracks = []
        birth_turn = seed["birth_turn"]
        for arm in ARMS:
            track_id = secrets.token_hex(12)
            if track_id in seen:
                raise RuntimeError("duplicate blind review pseudonym")
            seen.add(track_id)
            outputs = []
            for turn in turns[birth_turn + 1:birth_turn + 3]:
                raw = turn["research_arms"].get(arm)
                if not isinstance(raw, dict) or not raw.get("text"):
                    raise ValueError("missing complete paired output")
                outputs.append({
                    "turn_after_birth": turn["turn"] - birth_turn,
                    "unedited_model_inquiry": raw["text"],
                    "reviewer_1": {
                        "different_question_family": None,
                        "independently_testable": None,
                        "dependent_later_inquiry": None,
                        "mere_repetition": None,
                        "not_assessable": None,
                        "reason": None,
                    },
                    "reviewer_2": {
                        "different_question_family": None,
                        "independently_testable": None,
                        "dependent_later_inquiry": None,
                        "mere_repetition": None,
                        "not_assessable": None,
                        "reason": None,
                    },
                })
            tracks.append({"track_id": track_id, "two_rounds": outputs})
            owner["blind_track_mapping"][track_id] = {
                "case_id": cid, "model_id": item["model_id"], "arm": arm,
                "birth_turn": birth_turn,
                "seed_text": seed["text"],
                "birth_snapshot_sha256": seed["birth_snapshot_sha256"],
            }
        secrets.SystemRandom().shuffle(tracks)
        blind["case_groups"].append({
            "group_id": group_id, "ordinary_common": common,
            "two_randomized_inquiry_tracks": tracks,
        })
    secrets.SystemRandom().shuffle(blind["case_groups"])
    blind["blind_group_count"] = len(blind["case_groups"])
    owner["blind_track_count"] = len(owner["blind_track_mapping"])
    return blind, owner


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--blind-output", type=Path, required=True)
    ap.add_argument("--owner-output", type=Path, required=True)
    args = ap.parse_args()
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    validate_trial(fixture)
    for p in (args.output, args.blind_output, args.owner_output):
        p.parent.mkdir(parents=True, exist_ok=True)

    def persist(d: dict) -> None:
        args.output.write_text(json.dumps(
            d, ensure_ascii=False, indent=2,
        ) + "\n", encoding="utf-8")

    def factory(model: str, case_id: str) -> DualModelProvider:
        return DualModelProvider(
            os.environ.get("OPENAI_API_KEY", ""), model_id=model,
        )

    result = run_comparison(fixture, factory, on_change=persist)
    blind, owner = make_seed_hidden_review(result, fixture)
    args.blind_output.write_text(json.dumps(
        blind, ensure_ascii=False, indent=2,
    ) + "\n", encoding="utf-8")
    args.owner_output.write_text(json.dumps(
        owner, ensure_ascii=False, indent=2,
    ) + "\n", encoding="utf-8")
    print(json.dumps({
        "G0": result["G0"], "status": result["status"],
        "counts": result["counts"],
        "independent_Q2_effect_established": False,
    }, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
