#!/usr/bin/env python3
"""Research-only preflight for a matched five-arm inquiry pilot.

Does not call a model, decide scientific novelty, unblind case IDs, or grant
Shadowseed candidates any product authority. Reports design defects before
costly runs. Historic replay auditing is separate from prospective readiness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

SCHEMA = "shadowseed-matched-inquiry-calibration-v1"
ARMS = {"A", "B", "C", "D", "E"}
BUDGET_KEYS = {"max_model_calls", "max_model_tokens", "max_tool_calls", "max_retrieval_calls"}
HEX256 = re.compile(r"[0-9a-f]{64}\Z")


class PreflightError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PreflightError(message)


def valid_hash(value: object) -> bool:
    return isinstance(value, str) and HEX256.fullmatch(value) is not None


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check_plan(plan: dict) -> dict:
    """Enforce structural parity; never interpret this as a scientific pass."""
    require(isinstance(plan, dict) and plan.get("schema") == SCHEMA, "unknown plan schema")
    require(plan.get("mode") == "mechanics_calibration_only", "only offline mechanics calibration is allowed")
    require(plan.get("feedback_regime") in {"RF", "RI"}, "freeze RF or RI feedback regime")
    require(plan.get("g0_authorized") is False, "preflight may not authorize G0")
    cases = plan.get("cases")
    require(isinstance(cases, list) and 1 <= len(cases) <= 100, "need 1-100 calibration cases")
    seen_cases = set()
    for case in cases:
        require(isinstance(case, dict) and isinstance(case.get("case_id"), str), "invalid case")
        cid = case["case_id"]
        require(cid and cid not in seen_cases, "duplicate or blank case_id")
        seen_cases.add(cid)
        require(case.get("provenance") == "synthetic_calibration", f"{cid}: not a synthetic fixture")
        shared = case.get("shared")
        require(isinstance(shared, dict), f"{cid}: missing shared contract")
        for key in ("history_sha256", "t0_context_sha256", "feedback_sha256"):
            require(valid_hash(shared.get(key)), f"{cid}: invalid shared {key}")
        require(isinstance(shared.get("model_id"), str) and shared["model_id"], f"{cid}: model missing")
        require(isinstance(shared.get("model_revision"), str) and shared["model_revision"], f"{cid}: model revision missing")
        require(isinstance(shared.get("decoding"), dict) and shared["decoding"], f"{cid}: decoding missing")
        require(isinstance(shared.get("budget"), dict) and set(shared["budget"]) == BUDGET_KEYS,
                f"{cid}: incomplete resource budget")
        require(all(type(n) is int and n >= 0 for n in shared["budget"].values()), f"{cid}: invalid budget")
        require(shared["budget"]["max_model_calls"] > 0 and shared["budget"]["max_model_tokens"] > 0,
                f"{cid}: zero model budget")
        candidate = case.get("candidate")
        require(isinstance(candidate, dict), f"{cid}: frozen candidate missing")
        require(isinstance(candidate.get("id"), str) and candidate["id"], f"{cid}: candidate ID missing")
        require(valid_hash(candidate.get("sha256")), f"{cid}: candidate hash missing")
        require(type(candidate.get("birth_turn")) is int and type(candidate.get("exposure_turn")) is int
                and 0 <= candidate["birth_turn"] < candidate["exposure_turn"],
                f"{cid}: candidate not frozen before exposure")
        require(candidate.get("weight") == 0 and candidate.get("authority") is False,
                f"{cid}: candidate must remain weightless with no authority")
        require(type(candidate.get("token_count")) is int and candidate["token_count"] > 0,
                f"{cid}: missing candidate token count")
        arms = case.get("arms")
        require(isinstance(arms, list) and len(arms) == 5, f"{cid}: five arms required")
        mapping = {item.get("arm"): item for item in arms if isinstance(item, dict)}
        require(set(mapping) == ARMS and len(arms) == len(mapping), f"{cid}: missing/duplicate arm")
        for aid, item in mapping.items():
            for key in ("history_sha256", "t0_context_sha256"):
                require(item.get(key) == shared[key], f"{cid}/{aid}: different {key}")
            if plan["feedback_regime"] == "RF":
                require(item.get("feedback_sha256") == shared["feedback_sha256"],
                        f"{cid}/{aid}: RF feedback differs")
            else:
                # In RI, arms can observe different consequences of their own actions.
                require(item.get("feedback_sha256") is None,
                        f"{cid}/{aid}: RI cannot pre-fill outcomes")
            for key in ("model_id", "model_revision", "decoding", "budget"):
                require(item.get(key) == shared[key], f"{cid}/{aid}: unequal {key}")
            if aid in {"A", "B", "C"}:
                require(item.get("candidate_visibility") == "absent" and item.get("candidate_sha256") is None,
                        f"{cid}/{aid}: candidate leakage into baseline")
                require(item.get("sham_sha256") is None, f"{cid}/{aid}: unsolicited sham content")
            elif aid == "D":
                require(item.get("candidate_visibility") == "frozen_weightless" and
                        item.get("candidate_sha256") == candidate["sha256"] and
                        item.get("sham_sha256") is None, f"{cid}/D: candidate identity mismatch")
                require(item.get("extra_tokens") == candidate["token_count"],
                        f"{cid}/D: incorrect candidate-token count")
            elif aid == "E":
                require(item.get("candidate_visibility") == "sham_ablation" and
                        item.get("candidate_sha256") is None and valid_hash(item.get("sham_sha256")) and
                        item["sham_sha256"] != candidate["sha256"],
                        f"{cid}/E: exact candidate not ablated")
                require(item.get("extra_tokens") == candidate["token_count"],
                        f"{cid}/E: unmatched sham-token count")
        require("results" not in case and "results" not in plan,
                f"{cid}: no outcome labels in a preflight plan")
    return {
        "schema": "shadowseed-preflight-report-v1",
        "status": "MECHANICS_ONLY_NOT_APPROVED",
        "g0_status": "NOT_PASSED",
        "prospective_model_runs": 0,
        "case_count": len(cases),
        "arms_per_case": 5,
        "feedback_regime": plan["feedback_regime"],
        "invariants_checked": ["complete_arms", "identical_model_and_budgets",
                               "common_T0_information", "weightless_candidate_before_exposure",
                               "candidate_specific_sham_ablation", "feedback_regime_isolation"],
        "limitations": ["Hash values and budget declarations are checked for structural consistency, not independently tied to actual model calls.",
                        "Calibration fixtures are not fresh sealed holdouts, approved evaluator designs or a paid-model experiment.",
                        "No Q1/Q2 effect, scientific novelty or independent G0 approval is measured."],
    }


def audit_historical_replay(results: list) -> dict:
    """Count technical validity, not scientific success or statistical effects."""
    require(isinstance(results, list) and results, "historical replay missing checkpoints")
    observed = set()
    invalid = Counter()
    same_history = 0
    valid = 0
    for row in results:
        require(isinstance(row, dict), "malformed checkpoint record")
        turn = row.get("checkpoint_turn")
        require(type(turn) is int and turn not in observed, "duplicate or missing checkpoint")
        observed.add(turn)
        require("ordinary_llm_raw" in row and "ordinary_llm_parsed" in row,
                "missing raw reply or parser disposition")
        parsed = row["ordinary_llm_parsed"]
        require(isinstance(parsed, dict) and type(parsed.get("valid")) is bool,
                "invalid parser outcome")
        if row.get("same_prior_notes_in_both_arms") is True:
            same_history += 1
        if parsed["valid"]:
            valid += 1
        else:
            reason = parsed.get("reason_code")
            require(isinstance(reason, str) and reason, "missing invalid-reason code")
            invalid[reason] += 1
    return {
        "schema": "shadowseed-replay-diagnostic-v1",
        "status": "RETROSPECTIVE_TECHNICAL_AUDIT_ONLY",
        "checkpoints": len(results),
        "same_prior_notes_declared": same_history,
        "parseable_qwen_results": valid,
        "unscorable_qwen_results": len(results) - valid,
        "invalid_reasons": dict(sorted(invalid.items())),
        "relative_method_effect_estimated": False,
        "g0_status": "NOT_PASSED",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check-plan", help="check synthetic five-arm calibration contract")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    p = sub.add_parser("audit-history", help="count invalid historical model outputs")
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--report", required=True, type=Path)
    args = parser.parse_args(argv)
    require(args.input.resolve() != args.report.resolve(), "never overwrite input")
    payload = load_json(args.input)
    report = check_plan(payload) if args.command == "check-plan" else audit_historical_replay(payload)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
