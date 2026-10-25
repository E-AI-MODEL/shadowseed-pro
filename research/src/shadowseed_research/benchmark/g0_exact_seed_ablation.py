"""Single REAL canonical seed, exact deletion at frozen T1, GPT-5.

Post-hoc EXPLORATORY fixed-replay research only. Four conditions, four
stateless model calls per condition, balanced call position. No G0 approval;
no proof of Q1 internal absence or Q2 new investigability. The ordinary
product host is NOT called or modified: this is a separately isolated
research inquiry using an immutable true engine-birth artifact.

The word "paired" here means matching source context/model/prompt contract,
NOT deterministic cross-call potential outcomes: GPT-5 sampling is not fixed.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from typing import Any

from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    _hash, _inquiry_prompt, _parse_inquiry, _user_input,
    INQUIRY_INSTRUCTIONS, validate as validate_source_fixture,
)

SCHEMA = "shadowseed-g0-exact-seed-ablation-design-v1"
RESULT_SCHEMA = "shadowseed-g0-exact-seed-ablation-observations-v1"
EXPECTED_SOURCE_SHA = "62f778fb53547f2c0532795ccb31f02f09381500a2eb67b7598bf86ae597820f"
EXPECTED_SOURCE_COMMIT = "7677f8e145c4766ff3fea5451c95acea21edaacb"
EXPECTED_SOURCE_FIXTURE_SHA = "e72bc6a6846d2cbe12af672a0d12365ea571ad10091ab1ec3f4746ad87d38bee"
ORDER = (("D", "X", "P", "N"), ("X", "N", "D", "P"),
         ("P", "D", "N", "X"), ("N", "P", "X", "D"))
ARMS = ("D", "X", "P", "N")
CALLS = 16
TOKEN_CAP = 110000
OUTPUT_CAP = 4096


def _assert(ok: bool, msg: str) -> None:
    if not ok:
        raise ValueError(msg)


def validate_design(d: dict[str, Any]) -> None:
    _assert(isinstance(d, dict) and d.get("schema") == SCHEMA,
            "invalid frozen design schema")
    _assert(d.get("source_run_id") == 40224494313 and
            d.get("source_commit") == EXPECTED_SOURCE_COMMIT and
            d.get("source_raw_observed_sha256") == EXPECTED_SOURCE_SHA and
            d.get("source_fixture_sha256") == EXPECTED_SOURCE_FIXTURE_SHA and
            d.get("source_fixture_path") ==
                "research/fixtures/real_seed_rf_inquiry_v1.json",
            "source of real seed was substituted")
    _assert(d.get("source_model") == "gpt-5" and
            d.get("source_seed_id") == "ss_001" and
            d.get("seed_birth_turn") == 0 and d.get("inquiry_turn") == 1 and
            d.get("feedback_regime") == "RF",
            "incompatible seed/model/turn design")
    _assert(d.get("design_status") ==
            "POST_HOC_EXPLORATORY_SINGLE_REAL_T1_CASE_NOT_G0_OR_CONFIRMATORY",
            "cannot silently relabel post-hoc pilot as sealed study")
    _assert(d.get("model_instructions") ==
            "USE_EXISTING_REAL_SEED_RF_INQUIRY_INSTRUCTIONS_UNCHANGED",
            "inquiry instructions must be common across conditions")
    _assert(d.get("removal_text") == "NONE" and
            isinstance(d.get("control_placeholder"), str) and
            len(d["control_placeholder"]) == 185,
            "placebo must have predeclared 185-character length")
    _assert(set(d.get("arms", {})) == set(ARMS), "missing contrast arms")
    schedule = d.get("schedule")
    _assert(isinstance(schedule, list) and len(schedule) == 4,
            "exactly four preregistered sampling rounds required")
    order = tuple(tuple(row["order"]) for row in schedule)
    _assert(order == ORDER and all(row["round"] == i
                                   for i, row in enumerate(schedule)),
            "balanced model-call order was changed")
    _assert(
        all(sorted(row) == sorted(ARMS) for row in order) and
        all(sorted(order[i].index(arm) for i in range(4)) == list(range(4))
            for arm in ARMS),
        "call-order position is not balanced across conditions")
    _assert(d.get("planned_completed_model_calls") == CALLS and
            d.get("max_model_calls") == CALLS and
            d.get("max_embedding_calls") == 1 and
            d.get("max_all_reported_tokens") == TOKEN_CAP and
            d.get("max_output_tokens_per_call") == OUTPUT_CAP,
            "incompatible fixed research budget")
    _assert(not any(k in d for k in
                    ("target_question", "answer_key", "target_terms",
                     "expected_seed_effect", "ideal_answer")),
            "no outcome hints or investigator success target allowed")


def verify_recorded_source(original: dict, fixture: dict, design: dict) -> dict:
    """Validate archived REAL T0 canonical birth and T1 follow-up.

    This is provenance consistency, not independently witnessed API traffic
    nor the unknown T2 manager state.
    """
    validate_design(design)
    case = validate_source_fixture(fixture)
    _assert(
        original.get("schema") == "ssl-rf-real-seed-observations-v1"
        and original.get("model") == "gpt-5"
        and original.get("status") ==
            "incomplete_exploratory_not_a_null_result"
        and original.get("case_id") == "MEASUREMENT"
        and original.get("G0") == "NOT_PASSED"
        and original.get("fixture_sha256") == _hash(fixture)
        and original.get("fixture_sha256") == EXPECTED_SOURCE_FIXTURE_SHA,
        "original frozen RF source mismatch")
    turns = original.get("turns")
    _assert(isinstance(turns, list) and len(turns) == 3 and
            [t.get("turn") for t in turns] == [0, 1, 2],
            "source must include exact chronological T0/T1/T2 records")
    for i in (0, 1):
        t = turns[i]
        report = t.get("canonical_report")
        _assert(isinstance(report, dict) and report.get("runtime_mode") == "live"
                and report.get("turn") == i
                and report.get("answer") == t.get("host_answer")
                and t.get("none_control_answer_identical") is True
                and not report.get("selected_seed_ids")
                and not report.get("surfaced_seed_ids")
                and report.get("same_turn_revision_applied") is False
                and report.get("self_reinforcement_applied") is False,
                "ordinary source generation may be contaminated")
    birth = turns[0].get("birth")
    follow = turns[1].get("followup")
    sid = design["source_seed_id"]
    seed = original.get("first_seed")
    _assert(isinstance(seed, dict) and isinstance(seed.get("text"), str)
            and seed.get("id") == sid and seed.get("weight") == 0
            and seed.get("evidence_count") == 0,
            "source has no genuine recorded weightless first seed")
    _assert(isinstance(birth, dict) and isinstance(follow, dict)
            and birth.get("seed_id") == sid and follow.get("seed_id") == sid
            and sha256(seed["text"].encode("utf-8")).hexdigest()
                 == birth.get("candidate_text_sha256"),
            "first seed text and birth checkpoint mismatch")
    for label, checkpoint in (("birth", birth), ("follow", follow)):
        _assert(checkpoint.get("snapshot_sha256") ==
                _hash({k: v for k, v in checkpoint.items()
                       if k != "snapshot_sha256"}),
                label + " checkpoint hash invalid")
    _assert(
        follow.get("turn") == 1
        and follow.get("birth_snapshot_sha256") == birth["snapshot_sha256"]
        and follow.get("history_sha256") ==
            _hash([turns[i]["canonical_report"] for i in (0, 1)])
        and follow.get("turn_report_sha256") == _hash(turns[1]["canonical_report"])
        and follow.get("seed_state_after_turn", {}).get("weight") == 0
        and follow.get("seed_state_after_turn", {}).get("evidence_count") == 0
        and follow.get("product_answer_seed_influence_observed") is False,
        "first later-turn canonical checkpoint disagrees with source")
    _assert(
        (original.get("provider_audit") or {}).get("model_calls") == 14
        and (original.get("provider_audit") or {}).get("recorded_tokens") == 37503,
        "not the original recorded GPT-5 trial")
    note = original.get("ordinary_note")
    _assert(isinstance(note, str) and 40 <= len(note) <= 1500,
            "original ordinary note not available")
    _assert(len(seed["text"]) == 185 and seed["text"] not in note,
            "source seed length changed or leaked into ordinary note")
    _assert(
        design["control_placeholder"] != seed["text"]
        and seed["text"] not in design["control_placeholder"],
        "placebo cannot itself contain the real candidate")
    return {
        "case": case,
        "seed": seed["text"],
        "ordinary_note": note,
        "prior": [
            (_user_input(case, case["turns"][i]), turns[i]["host_answer"])
            for i in (0, 1)
        ],
        "birth_sha": birth["snapshot_sha256"],
        "followup_sha": follow["snapshot_sha256"],
    }


def build_prompts(original: dict, fixture: dict, design: dict) -> dict[str, dict]:
    record = verify_recorded_source(original, fixture, design)
    case = record["case"]
    notes = {
        "D": record["seed"],
        "X": design["removal_text"],
        "P": design["control_placeholder"],
        "N": record["ordinary_note"],
    }
    result: dict[str, dict] = {}
    common: str | None = None
    for arm in ARMS:
        prompt = _inquiry_prompt(
            case, record["prior"],
            case["turns"][1]["new_observation"],
            case["turns"][1]["question"],
            arm="D", note=notes[arm], earlier_question=None,
        )
        # Validate the ONLY change is the content of an existing note slot.
        prefix, sep, suffix = prompt.partition(
            "EERDERE ONBEWEZEN ONDERZOEKSNOTITIE:\n")
        _assert(bool(sep) and suffix.startswith(notes[arm]),
                "research adapter changed note-slot contract")
        unchanged = prefix + sep + suffix[len(notes[arm]):]
        if common is None:
            common = unchanged
        _assert(unchanged == common, "different instructions or histories across arms")
        _assert((record["seed"] in prompt) == (arm == "D"),
                "literal first seed leakage to wrong condition")
        _assert(case["turns"][2]["new_observation"] not in prompt,
                "future T2 observation leaked into T1")
        result[arm] = {
            "prompt": prompt,
            "prompt_sha256": _hash(prompt),
            "note_sha256": _hash(notes[arm]),
            "note_chars": len(notes[arm]),
            "prompt_chars": len(prompt),
        }
    _assert(result["D"]["note_chars"] == result["P"]["note_chars"] == 185,
            "placebo must match real seed character length")
    _assert(result["D"]["prompt_chars"] == result["P"]["prompt_chars"],
            "same-char placebo prompt changed its layout")
    return result


def _audit(provider: BoundedProvider) -> dict:
    return {
        "model_calls_attempted": provider.model_calls,
        "embedding_calls_attempted": provider.embedding_calls,
        "reported_tokens": provider.total_tokens,
        "model_call_cap": provider.model_call_cap,
        "output_token_cap": provider.output_token_cap,
        "all_token_cap": provider.all_token_cap,
        "events": deepcopy(provider.events),
    }


def run(original: dict, fixture: dict, design: dict,
        provider: BoundedProvider, *,
        on_checkpoint=None) -> dict:
    prompts = build_prompts(original, fixture, design)
    _assert(
        provider.model_call_cap == CALLS
        and provider.embedding_call_cap <= 1
        and provider.all_token_cap == TOKEN_CAP
        and provider.output_token_cap == OUTPUT_CAP,
        "budget not configured to exact declared caps")
    result = {
        "schema": RESULT_SCHEMA,
        "status": "running_exploratory_not_efficacy",
        "G0": "NOT_PASSED",
        "source_run_id": design["source_run_id"],
        "source_sha256": EXPECTED_SOURCE_SHA,
        "source_commit": EXPECTED_SOURCE_COMMIT,
        "feedback_regime": "RF",
        "case_count": 1,
        "same_T1_context_all_conditions": True,
        "same_prompt_template_except_note_slot": True,
        "source_real_canonical_seed_birth": True,
        "seed_in_ordinary_product_answer": False,
        "randomization": "predeclared_balanced_4x4_order_not_model_seeded",
        "no_model_sampling_seed_control": True,
        "independent_semantic_review_completed": False,
        "independent_later_experiment": False,
        "Q1_internal_absence_proven": False,
        "Q2_causal_new_investigability_proven": False,
        "condition_prompts": {
            arm: {k: v for k, v in row.items() if k != "prompt"}
            for arm, row in prompts.items()
        },
        "birth_checkpoint_sha256": verify_recorded_source(
            original, fixture, design)["birth_sha"],
        "observations": [],
        "provider_audit": {},
    }

    def save() -> None:
        result["provider_audit"] = _audit(provider)
        if on_checkpoint:
            on_checkpoint(deepcopy(result))

    save()
    for round_index, order in enumerate(ORDER):
        for pos, arm in enumerate(order):
            text = provider.generate(
                stage=f"ablation_r{round_index}_p{pos}_{arm}",
                case_id="MEASUREMENT",
                prompt=prompts[arm]["prompt"],
                instructions=INQUIRY_INSTRUCTIONS,
            )
            parsed = _parse_inquiry(text)
            result["observations"].append({
                "round": round_index, "call_position": pos,
                "arm": arm, "source_seed_available": arm == "D",
                "prompt_sha256": prompts[arm]["prompt_sha256"],
                "response_raw": text,
                "response_status": (
                    "none" if text.strip().upper() == "NONE"
                    else "valid_question" if parsed else "invalid_question"
                ),
                "parsed": parsed,
                "scientific_effect_assessed": False,
            })
            save()
    _assert(provider.model_calls == CALLS and
            len(result["observations"]) == CALLS and
            provider.embedding_calls == 0,
            "missing/hidden extra provider requests")
    result["status"] = "completed_exploratory_unreviewed_single_seed"
    save()
    return result


def make_blind_packets(result: dict) -> tuple[dict, dict]:
    """Conceal arm labels; human reviewers must NOT be given owner key."""
    _assert(result.get("status") == "completed_exploratory_unreviewed_single_seed"
            and len(result.get("observations", [])) == CALLS,
            "cannot make complete review packet from partial model calls")
    rows, key = [], {}
    for item in result["observations"]:
        token = secrets.token_hex(12)
        key[token] = {
            "arm": item["arm"], "round": item["round"],
            "call_position": item["call_position"],
            "prompt_sha256": item["prompt_sha256"],
        }
        rows.append({
            "sample_id": token, "model_response": item["response_raw"],
            "parser_status": item["response_status"],
            "rater1": {"hypothesis_retained": None,
                       "different_research_question": None,
                       "independently_testable": None,
                       "rationale": None},
            "rater2": {"hypothesis_retained": None,
                       "different_research_question": None,
                       "independently_testable": None,
                       "rationale": None},
        })
    secrets.SystemRandom().shuffle(rows)
    return ({
        "schema": "shadowseed-g0-exact-seed-ablation-blind-review-v1",
        "G0": "NOT_PASSED",
        "one_source_case_four_draws_per_condition": True,
        "independent_review_completed": False,
        "reviewer_instructions": (
            "Review question direction, retention of the original spatial "
            "hypothesis, testability, and novelty versus the ordinary "
            "visible case. Do NOT guess conditions or award a win. "
            "Both raters must independently fill their fields before unblinding."
        ),
        "samples": rows,
    }, {
        "schema": "shadowseed-g0-exact-seed-ablation-owner-key-v1",
        "independent_review_completed": False,
        "do_not_share_with_blind_reviewers_before_scoring": True,
        "sample_mapping": key,
    })


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--source-fixture", type=Path, required=True)
    parser.add_argument("--design", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--blind-output", type=Path, required=True)
    parser.add_argument("--owner-output", type=Path, required=True)
    args = parser.parse_args()
    raw = args.source.read_bytes()
    if sha256(raw).hexdigest() != EXPECTED_SOURCE_SHA:
        raise ValueError("original model artifact bytes differ from pinned SHA-256")
    original = json.loads(raw)
    source_fixture = json.loads(args.source_fixture.read_text(encoding="utf-8"))
    design = json.loads(args.design.read_text(encoding="utf-8"))
    verify_recorded_source(original, source_fixture, design)  # before key/calls
    for p in (args.output, args.blind_output, args.owner_output):
        p.parent.mkdir(parents=True, exist_ok=True)
    provider = BoundedProvider(
        os.environ.get("OPENAI_API_KEY", ""),
        model_call_cap=CALLS, embedding_call_cap=1,
        all_token_cap=TOKEN_CAP, output_token_cap=OUTPUT_CAP,
    )

    def persist(r: dict) -> None:
        args.output.write_text(
            json.dumps(r, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    try:
        result = run(original, source_fixture, design, provider,
                     on_checkpoint=persist)
    except Exception as exc:
        # Provider calls have no retries; the original partial is not
        # converted to NONE or a zero-effect trial.
        partial = (
            json.loads(args.output.read_text(encoding="utf-8"))
            if args.output.exists() else {}
        )
        partial["status"] = "incomplete_exploratory_stop_not_none"
        partial["error_type"] = type(exc).__name__
        partial["G0"] = "NOT_PASSED"
        partial["Q2_causal_new_investigability_proven"] = False
        persist(partial)
        raise RuntimeError(f"ablation stopped: {type(exc).__name__}") from None
    blind, key = make_blind_packets(result)
    args.blind_output.write_text(
        json.dumps(blind, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.owner_output.write_text(
        json.dumps(key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = {
        arm: sum(v["arm"] == arm and v["response_status"] == "valid_question"
                 for v in result["observations"])
        for arm in ARMS
    }
    print(json.dumps({
        "status": result["status"], "source_run": design["source_run_id"],
        "model_calls": provider.model_calls, "tokens": provider.total_tokens,
        "question_counts_per_arm": counts,
        "blinding_ready_not_reviewed": True, "G0": "NOT_PASSED",
    }), flush=True)


if __name__ == "__main__":
    main()
