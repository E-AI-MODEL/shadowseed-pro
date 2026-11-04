#!/usr/bin/env python3
"""Offline five-arm RF inquiry runner for synthetic mechanics calibration.

No model-network adapter, product Gate, hidden assessor key, or G0 approval.
The synthetic replies are not scientific observations. A future provider
requires separately approved research and a new reviewed integration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
from pathlib import Path
from typing import Any

from mit_matched_preflight import PreflightError, check_plan, require

RUNNER_SCHEMA = "shadowseed-matched-runner-calibration-v1"
SYSTEM_PROMPT = (
    "You are examining a research question. Do not treat a prior candidate "
    "as evidence. Offer a distinct testable question, an experiment that "
    "could refute it, and an expected discriminating observation. "
    "Reply with one JSON object with exactly these text fields: "
    "question, experiment, expected_result. No other text."
)
OUTPUT_FIELDS = {"question", "experiment", "expected_result"}


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def token_units(text: str) -> int:
    """Synthetic-only word-count unit. Never claim this matches a real tokenizer."""
    return len(text.split())


def safe_text(value: Any, name: str) -> str:
    require(isinstance(value, str) and 0 < len(value.strip()) <= 12000, f"invalid {name}")
    return value


def parse_reply(raw: Any) -> dict:
    if not isinstance(raw, str) or len(raw) > 12000:
        return {"valid": False, "reason": "invalid_text", "value": None}
    try:
        obj = json.loads(raw)
    except (ValueError, TypeError):
        return {"valid": False, "reason": "invalid_json", "value": None}
    if not isinstance(obj, dict) or set(obj) != OUTPUT_FIELDS:
        return {"valid": False, "reason": "invalid_schema", "value": None}
    if not all(isinstance(obj[k], str) and 0 < len(obj[k].strip()) <= 2000 for k in OUTPUT_FIELDS):
        return {"valid": False, "reason": "invalid_fields", "value": None}
    return {"valid": True, "reason": None, "value": obj}


class FakeProvider:
    """Deterministic offline contract double. Output does not depend on arm."""

    kind = "FAKE_NO_NETWORK"

    @staticmethod
    def count_tokens(messages: list[dict]) -> int:
        return sum(token_units(msg["content"]) for msg in messages)

    @staticmethod
    def complete(messages: list[dict], *, stage: str, max_output_tokens: int,
                 model_id: str, model_revision: str, decoding: dict) -> dict:
        assert stage in ("T1", "T3")
        reply = {
            "question": "Which recorded measurement would distinguish the competing explanations?",
            "experiment": "Collect two comparable observations and check for different predictions.",
            "expected_result": "One explanation should fail a predeclared measurable condition.",
        }
        raw = canonical(reply)
        output_tokens = token_units(raw)
        if output_tokens > max_output_tokens:
            return {"text": "", "input_tokens": FakeProvider.count_tokens(messages),
                    "output_tokens": 0, "model_id": model_id,
                    "model_revision": model_revision, "finish_reason": "length"}
        return {"text": raw, "input_tokens": FakeProvider.count_tokens(messages),
                "output_tokens": output_tokens, "model_id": model_id,
                "model_revision": model_revision, "finish_reason": "stop"}


def validate_input(payload: dict) -> tuple[dict, dict]:
    require(isinstance(payload, dict) and payload.get("schema") == RUNNER_SCHEMA,
            "wrong runner input schema")
    require(set(payload) == {"schema", "plan", "payloads", "allocation_seed"},
            "unexpected top-level fields, including potential answer keys")
    plan = payload.get("plan")
    report = check_plan(plan)
    require(plan["feedback_regime"] == "RF",
            "RI not supported: independent adaptive executor and validator required")
    require(type(payload.get("allocation_seed")) is int and 0 <= payload["allocation_seed"] < 2**32,
            "allocation seed required")
    records = payload.get("payloads")
    require(isinstance(records, list), "payloads must be a list")
    by_id = {p.get("case_id"): p for p in records if isinstance(p, dict)}
    require(len(records) == len(by_id) == len(plan["cases"]),
            "payload count or repeated case ID")
    require(set(by_id) == {c["case_id"] for c in plan["cases"]}, "payload IDs differ")
    for case in plan["cases"]:
        cid = case["case_id"]
        item = by_id[cid]
        require(set(item) == {"case_id", "history", "t0_context", "feedback",
                              "candidate_text", "sham_text", "ordinary_notes"},
                f"{cid}: unexpected payload fields")
        shared = case["shared"]
        for field, expected in (("history", "history_sha256"),
                                ("t0_context", "t0_context_sha256"),
                                ("feedback", "feedback_sha256")):
            value = safe_text(item.get(field), f"{cid}/{field}")
            require(digest_text(value) == shared[expected], f"{cid}: altered {field} bytes")
        candidate = safe_text(item.get("candidate_text"), f"{cid}/candidate_text")
        sham = safe_text(item.get("sham_text"), f"{cid}/sham_text")
        ordinary = safe_text(item.get("ordinary_notes"), f"{cid}/ordinary_notes")
        require(digest_text(candidate) == case["candidate"]["sha256"],
                f"{cid}: candidate does not match frozen hash")
        arms = {arm["arm"]: arm for arm in case["arms"]}
        require(digest_text(sham) == arms["E"]["sham_sha256"],
                f"{cid}: sham does not match frozen hash")
        require(token_units(candidate) == token_units(sham) == case["candidate"]["token_count"],
                f"{cid}: synthetic candidate/sham word-unit mismatch")
        require(candidate != sham, f"{cid}: sham repeats the actual candidate")
        # Prevent accidental exact candidate exposure outside the treatment slot.
        require(all(candidate not in item[k] and sham not in item[k]
                    for k in ("history", "t0_context", "feedback", "ordinary_notes")),
                f"{cid}: candidate or sham already occurs in shared content")
        require(shared["model_id"] == "fake-calibration-model" and
                shared["model_revision"] == "pinned-test-revision",
                "CLI calibration may only use the pinned fake model")
        require(shared["budget"]["max_model_calls"] >= 2,
                f"{cid}: two model turns need at least two calls")
    return report, by_id


def make_messages(case: dict, payload: dict, arm: str, stage: str,
                  first_response: str | None = None) -> list[dict]:
    parts = ["PREVIOUS RESEARCH HISTORY:\n" + payload["history"],
             "CURRENT QUESTION:\n" + payload["t0_context"]]
    if arm == "B":
        parts.append("Before choosing, examine competing explanations and counterfactual tests.")
    elif arm == "C":
        parts.append("ORDINARY PREVIOUS NOTES (not independent evidence):\n" + payload["ordinary_notes"])
    elif arm in ("D", "E"):
        text = payload["candidate_text"] if arm == "D" else payload["sham_text"]
        parts.append("UNVERIFIED PREVIOUS RESEARCH CANDIDATE (not evidence):\n" + text)
    if stage == "T3":
        require(isinstance(first_response, str) and first_response, "missing T1 response")
        parts.extend(["NEW EXOGENOUS OBSERVATION (same in all arms):\n" + payload["feedback"],
                      "YOUR EARLIER QUESTION/PLAN:\n" + first_response,
                      "Propose a DIFFERENT later investigation prompted by the new observation."])
    else:
        parts.append("Propose a first testable research question.")
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n\n".join(parts)}]


def run_case(case: dict, item: dict, provider: Any, allocation_seed: int) -> dict:
    shared = case["shared"]
    cap = shared["budget"]
    order = list("ABCDE")
    random.Random(f"{allocation_seed}:{case['case_id']}").shuffle(order)
    arms = {}
    for arm in order:
        calls = []
        used_calls = 0
        used_tokens = 0
        earlier = None
        for stage in ("T1", "T3"):
            if stage == "T3" and earlier is None:
                calls.append({"stage": stage, "status": "skipped_invalid_prior", "reason": "T1_unavailable"})
                break
            msgs = make_messages(case, item, arm, stage, earlier)
            estimated = provider.count_tokens(msgs)
            max_output = min(192, cap["max_model_tokens"] - used_tokens - estimated)
            if used_calls >= cap["max_model_calls"] or max_output <= 0:
                calls.append({"stage": stage, "status": "budget_blocked", "estimated_input": estimated})
                continue
            request_digest = digest_text(canonical(msgs))
            # Count attempts, including provider errors. No retry is hidden from the ledger.
            used_calls += 1
            request = {"stage": stage, "request_sha256": request_digest,
                       "messages": msgs, "estimated_input_units": estimated,
                       "max_output_units": max_output}
            try:
                resp = provider.complete(msgs, stage=stage, max_output_tokens=max_output,
                                         model_id=shared["model_id"],
                                         model_revision=shared["model_revision"],
                                         decoding=shared["decoding"])
                require(isinstance(resp, dict), "provider returned no result")
                require(resp.get("model_id") == shared["model_id"] and
                        resp.get("model_revision") == shared["model_revision"],
                        "provider model identity changed")
                prompt_tokens, output_tokens = resp.get("input_tokens"), resp.get("output_tokens")
                require(type(prompt_tokens) is int and type(output_tokens) is int and
                        prompt_tokens >= 0 and output_tokens >= 0, "invalid reported token use")
                used_tokens += prompt_tokens + output_tokens
                require(prompt_tokens == estimated, "fake token accounting drift")
                require(output_tokens <= max_output and used_tokens <= cap["max_model_tokens"],
                        "token limit exceeded")
                raw = resp.get("text")
                require(isinstance(raw, str) and output_tokens == token_units(raw),
                        "fake provider token count does not match response")
                parsed = parse_reply(raw)
                reason = resp.get("finish_reason")
                status = "parsed" if parsed["valid"] and reason == "stop" else "invalid"
                calls.append({**request, "status": status, "response_text": raw,
                              "parsed": parsed, "finish_reason": reason,
                              "input_units": prompt_tokens, "output_units": output_tokens})
                if status != "parsed":
                    continue
                earlier = raw
            except Exception as exc:
                calls.append({**request, "status": "provider_or_contract_error",
                              "error_type": type(exc).__name__, "error": str(exc)[:250]})
                continue
        arms[arm] = {"arm": arm, "calls_used": used_calls, "synthetic_token_units": used_tokens,
                     "allocated_model_calls": cap["max_model_calls"],
                     "allocated_model_token_units": cap["max_model_tokens"], "events": calls}
    return {"case_id": case["case_id"], "execution_order": order, "arms": arms}


def run_calibration(input_data: dict, provider: Any = None) -> tuple[dict, dict]:
    report, by_id = validate_input(input_data)
    provider = FakeProvider() if provider is None else provider
    require(getattr(provider, "kind", None) == "FAKE_NO_NETWORK",
            "this calibration runner refuses connected or paid providers")
    results = [run_case(case, by_id[case["case_id"]], provider, input_data["allocation_seed"])
               for case in input_data["plan"]["cases"]]
    complete = sum(all(len(a["events"]) == 2 and all(e["status"] == "parsed"
                            for e in a["events"]) for a in case["arms"].values())
                   for case in results)
    summary = {"schema": "shadowseed-matched-run-summary-v1",
               "status": "SYNTHETIC_EXECUTION_NO_SCIENTIFIC_RESULT",
               "g0_status": "NOT_PASSED", "provider": provider.kind,
               "input_sha256": digest_text(canonical(input_data)),
               "preflight_status": report["status"], "feedback_regime": "RF",
               "cases": len(results), "completed_five_arm_cases": complete,
               "arm_calls": {arm: sum(case["arms"][arm]["calls_used"] for case in results)
                             for arm in "ABCDE"},
               "errors": [{"case": case["case_id"], "arm": arm, "stage": ev["stage"],
                           "status": ev["status"]}
                          for case in results for arm in "ABCDE" for ev in case["arms"][arm]["events"]
                          if ev["status"] != "parsed"],
               "model_network_calls": 0, "human_reviews": 0,
               "real_candidate_birth_verified": False,
               "actual_model_tokenizer_used": False,
               "scientific_comparative_effect_calculated": False,
               "independent_g0_review_approved": False}
    owner_trace = {"schema": "shadowseed-matched-owner-trace-v1", "visibility": "OWNER_ONLY_NOT_BLIND",
                   "input_sha256": summary["input_sha256"], "provider": provider.kind,
                   "cases": results, "summary": summary}
    return summary, owner_trace


def write_private_json(path: Path, payload: dict) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--provider", choices=("fake",), default="fake")
    args = parser.parse_args(argv)
    require(args.input.is_file(), "missing input")
    require(not args.output_dir.exists(), "output directory already exists")
    input_data = json.loads(args.input.read_text(encoding="utf-8"))
    summary, trace = run_calibration(input_data)
    args.output_dir.mkdir(parents=True, mode=0o700, exist_ok=False)
    write_private_json(args.output_dir / "run_summary.json", summary)
    write_private_json(args.output_dir / "owner_trace.json", trace)
    print(json.dumps({"status": summary["status"], "cases": summary["cases"],
                      "complete": summary["completed_five_arm_cases"],
                      "g0": summary["g0_status"], "output_dir": str(args.output_dir)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
