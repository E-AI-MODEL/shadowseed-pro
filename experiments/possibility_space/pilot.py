"""Exploratory Q1/Q2 possibility-space feasibility assay; not a Shadowseed runtime.

Only synthetic networks and independent, deterministic validators are used.
OpenAI calls are optional, bounded, and never contain user conversation data.
The assay measures *operational reachability*, not expansion of a model's
mathematically defined set of possible token sequences or real-world novelty.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadowseed-possibility-pilot-v0"
ARMS = ("A-ordinary", "B-deliberate", "C-notes", "D-shadow")
SYSTEM = (
    "You are analyzing a fictional typed data-flow network. "
    "Links must respect output type, input type, zone, and direction. "
    "Do not assume a proposed connection exists or has been tested. "
    "Use node IDs exactly and return only a JSON object."
)
STAGE1 = {
    "A-ordinary": "Recommend up to two useful missing links to make the workflow operational.",
    "B-deliberate": "Deliberately explore overlooked and alternative type-compatible missing links; recommend up to two that could open new workflows.",
    "C-notes": "Make up to two concise working-memory notes about possible missing links that could become useful in a later task.",
    "D-shadow": "Inspect what a conventional recommendation might leave unselected. Propose up to two weightless, uncertain candidate links that could enable relations not yet reachable. Speculation has no authority.",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_cases(path: Path) -> list[dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("schema") != "shadowseed-possibility-pilot-cases-v0":
        raise ValueError("unsupported case schema")
    cases = doc.get("cases", [])
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("no cases or duplicate case IDs")
    for c in cases:
        ids = [x["id"] for x in c["nodes"]]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate node IDs")
        nodes = {n["id"]: n for n in c["nodes"]}
        for u, v in c["existing_edges"]:
            if u not in nodes or v not in nodes or u == v:
                raise ValueError("bad base edge")
            if not compatible(nodes[u], nodes[v]):
                raise ValueError(f"base link violates constraints: {u} -> {v}")
        if _cycle([tuple(edge) for edge in c["existing_edges"]]):
            raise ValueError(f"cyclic base graph in case {c['id']}")
    return cases


def compatible(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return bool(a["produces"] is not None and a["produces"] == b["consumes"] and a["zone"] == b["zone"] and a["id"] != b["id"])


def reachable_pairs(case: dict[str, Any], edges: list[list[str]] | list[tuple[str, str]]) -> set[tuple[str, str]]:
    nodes = {n["id"]: n for n in case["nodes"]}
    adj: dict[str, list[str]] = {n: [] for n in nodes}
    for u, v in edges:
        adj[u].append(v)
    out: set[tuple[str, str]] = set()
    for n in case["nodes"]:
        if n["kind"] != "source":
            continue
        seen = {n["id"]}
        queue = deque([n["id"]])
        while queue:
            here = queue.popleft()
            for there in adj[here]:
                if there not in seen:
                    seen.add(there)
                    queue.append(there)
        for t in seen:
            if nodes[t]["kind"] == "sink":
                out.add((n["id"], t))
    return out


def legal_bridge(case: dict[str, Any], bridge: tuple[str, str]) -> bool:
    nodes = {n["id"]: n for n in case["nodes"]}
    u, v = bridge
    if u not in nodes or v not in nodes or (u, v) in map(tuple, case["existing_edges"]):
        return False
    if not compatible(nodes[u], nodes[v]):
        return False
    # Reject a candidate that creates a directed cycle.
    adj = [(a, b) for a, b in case["existing_edges"]] + [(u, v)]
    if _cycle(adj):
        return False
    return True


def _cycle(edges: list[tuple[str, str]]) -> bool:
    adj: dict[str, list[str]] = {}
    for u, v in edges:
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, [])
    state: dict[str, int] = {}

    def visit(node: str) -> bool:
        if state.get(node) == 1:
            return True
        if state.get(node) == 2:
            return False
        state[node] = 1
        for next_node in adj.get(node, []):
            if visit(next_node):
                return True
        state[node] = 2
        return False

    return any(visit(node) for node in adj if state.get(node) != 2)


def delta(case: dict[str, Any], bridge: tuple[str, str]) -> set[tuple[str, str]]:
    if not legal_bridge(case, bridge):
        return set()
    before = reachable_pairs(case, case["existing_edges"])
    after = reachable_pairs(case, case["existing_edges"] + [list(bridge)])
    return after - before


def legal_candidates(case: dict[str, Any]) -> list[tuple[str, str]]:
    ids = sorted(n["id"] for n in case["nodes"])
    return [(u, v) for u in ids for v in ids if legal_bridge(case, (u, v))]


def selftest(cases: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for c in cases:
        before = reachable_pairs(c, c["existing_edges"])
        good = c["positive_fixture_bridge"]
        bad = tuple(c["invalid_fixture_bridge"])
        if legal_bridge(c, bad) or delta(c, bad):
            raise AssertionError("negative control is accepted")
        if good:
            good = tuple(good)
            if not legal_bridge(c, good) or not delta(c, good):
                raise AssertionError("positive control must be valid and causal")
            if reachable_pairs(c, c["existing_edges"]) != before:
                raise AssertionError("ablation did not restore baseline")
            effect = sorted([list(z) for z in delta(c, good)])
        else:
            if any(delta(c, k) for k in legal_candidates(c)):
                raise AssertionError("negative case has an undisclosed positive link")
            effect = []
        rows.append({"id": c["id"], "baseline_terminal_pairs": len(before), "admissible_unobserved_links": len(legal_candidates(c)), "positive_fixture_bridge": list(good) if good else None, "positive_fixture_delta": effect, "invalid_control_rejected": True})
    return {"schema": SCHEMA, "kind": "offline-oracle-selftest", "status": "passed", "model_calls": 0, "this_is_not_model_evidence": True, "cases": rows}


def _wire_case(case: dict[str, Any]) -> str:
    return json.dumps({"setting": case["setting"], "nodes": case["nodes"], "existing_edges": case["existing_edges"], "relation_rule": "A proposed link is permitted only when produces == consumes and zones agree; no cycles."}, separators=(",", ":"))


def first_prompt(case: dict[str, Any], arm: str, ordinary_answer: str = "") -> str:
    ordinary_context = ("\nShared ordinary-generation reference (same for B, C and D; may be incomplete): " + ordinary_answer[:1200]) if ordinary_answer and arm != "A-ordinary" else ""
    return (
        "Fictional network (no real organizations or people): " + _wire_case(case)
        + ordinary_context + "\nTask: " + STAGE1[arm]
        + '\nReturn exactly {"bridges":[["source_node","target_node"],...],"why":"up to 25 words"}. '
        + "Do not introduce new node IDs. If no justified link exists, return an empty list."
    )


def second_prompt(case: dict[str, Any], proposed: list[tuple[str, str]]) -> str:
    return (
        "Fictional network: " + _wire_case(case)
        + "\nHypothetical earlier candidate links: " + json.dumps([list(x) for x in proposed])
        + "\nAssume only those proposals that meet the network's typed/zone constraints and no-cycle rule can be used. "
        + "Which previously unreachable source-to-sink pairs would then become reachable by adding at most ONE candidate link? "
        + "Do not claim the candidate is real-world evidence."
        + '\nReturn exactly {"new_paths":[["source_node","sink_node"],...],"why":"up to 25 words"}. '
        + "If none, return an empty list."
    )


def _json_object(text: str) -> dict[str, Any]:
    if not isinstance(text, str):
        return {}
    try:
        d = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not m:
            return {}
        try:
            d = json.loads(m.group(0))
        except json.JSONDecodeError:
            return {}
    return d if isinstance(d, dict) else {}


def extract_pairs(value: Any, limit: int) -> list[tuple[str, str]]:
    if not isinstance(value, list):
        return []
    out = []
    for item in value[:limit]:
        if isinstance(item, list) and len(item) == 2 and all(isinstance(x, str) for x in item):
            pair = (item[0], item[1])
            if pair not in out:
                out.append(pair)
    return out


def valid_pair_array(payload: dict[str, Any], field: str, limit: int) -> bool:
    """Require the declared JSON schema; missing/invalid arrays are not abstentions."""

    value = payload.get(field)
    return (
        isinstance(value, list)
        and len(value) <= limit
        and all(
            isinstance(item, list)
            and len(item) == 2
            and all(isinstance(part, str) for part in item)
            for item in value
        )
    )


def score_first(case: dict[str, Any], proposed: list[tuple[str, str]]) -> dict[str, Any]:
    valid = [e for e in proposed if legal_bridge(case, e)]
    gains = {e: delta(case, e) for e in valid}
    union = set().union(*gains.values()) if gains else set()
    # Explicit ablation of the newly proposed bridge, not model self-validation.
    prior = reachable_pairs(case, case["existing_edges"])
    ablations = {}
    for e, paths in gains.items():
        augmented = reachable_pairs(case, case["existing_edges"] + [list(e)])
        ablated = reachable_pairs(case, case["existing_edges"])
        ablations[e] = bool(paths == (augmented - prior) and paths.isdisjoint(ablated))
    return {
        "proposed": [list(x) for x in proposed],
        "valid": [list(x) for x in valid],
        "invalid": [list(x) for x in proposed if x not in valid],
        "verified_new_terminal_pairs": sorted([list(x) for x in union]),
        "per_link_effect": [{"bridge": list(e), "delta": sorted([list(x) for x in paths])} for e, paths in gains.items()],
        "ablation_pass": all(ablations.values()),
    }


def score_second(case: dict[str, Any], stage1: dict[str, Any], claimed: list[tuple[str, str]]) -> dict[str, Any]:
    true = set(map(tuple, stage1["verified_new_terminal_pairs"]))
    predictions = set(claimed)
    nodes = {n["id"]: n for n in case["nodes"]}
    well_typed = {p for p in predictions if p[0] in nodes and p[1] in nodes and nodes[p[0]]["kind"] == "source" and nodes[p[1]]["kind"] == "sink"}
    return {
        "claimed_new_terminal_pairs": sorted([list(x) for x in predictions]),
        "verified_correct_claims": sorted([list(x) for x in predictions & true]),
        "false_positive_claims": sorted([list(x) for x in predictions - true]),
        "missed_verified_relations": sorted([list(x) for x in true - predictions]),
        "claim_precision": (len(predictions & true) / len(predictions)) if predictions else None,
        "out_of_schema_claims": sorted([list(x) for x in predictions - well_typed]),
    }


def responses_call(model: str, prompt: str, max_output_tokens: int, reasoning_effort: str, api_key: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "instructions": SYSTEM,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "reasoning": {"effort": reasoning_effort},
        "store": False,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=100) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        # No potentially sensitive provider error payloads in public artifacts/logs.
        raise RuntimeError(f"provider HTTP status {exc.code}") from None
    except Exception as exc:
        raise RuntimeError(f"provider request failed: {type(exc).__name__}") from None
    fragments = [part.get("text", "") for item in result.get("output", []) for part in item.get("content", []) if part.get("type") == "output_text"]
    output_text = "\n".join(fragments)
    return {
        "output_text": output_text,
        "status": result.get("status"),
        "model": result.get("model", model),
        "usage": result.get("usage", {}),
        "incomplete_details": result.get("incomplete_details"),
    }


def pilot(cases: list[dict[str, Any]], args: argparse.Namespace, cases_path: Path) -> dict[str, Any]:
    metadata = {
        "schema": SCHEMA, "kind": "live-probability-and-reachability-feasibility-pilot",
        "research_claim_status": "exploratory; neither Q1 nor Q2 scientifically established",
        "created_utc": datetime.now(timezone.utc).isoformat(), "model_requested": args.model,
        "reasoning_effort": args.reasoning_effort, "max_output_tokens_per_call": args.max_output_tokens,
        "max_calls": args.max_calls, "cases_sha256": digest(cases_path),
        "git_sha": os.getenv("GITHUB_SHA"), "no_user_data": True,
        "independence": "Formal graph validator independent of model; semantic novelty/human review not present",
        "method_note": "This measures formal source-sink reachability under a proposed new edge, NOT mathematical expansion of a frozen model's output support.",
        "status": "not_run", "calls": 0, "failed_calls": [], "cases": [],
    }
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        metadata["status"] = "blocked_no_api_key"
        return metadata
    if args.max_calls < len(cases) * len(ARMS) * 2:
        metadata["status"] = "blocked_insufficient_call_budget"
        return metadata
    metadata["status"] = "running"
    for case in cases:
        case_results = {"id": case["id"], "arms": {}, "baseline_shared_with_BCD": True}
        metadata["cases"].append(case_results)
        ordinary_answer = ""
        ordinary_pairs: list[tuple[str, str]] = []
        for arm in ARMS:
            row: dict[str, Any] = {}
            case_results["arms"][arm] = row
            p1 = first_prompt(case, arm, ordinary_answer)
            try:
                raw1 = responses_call(args.model, p1, args.max_output_tokens, args.reasoning_effort, key)
                metadata["calls"] += 1
                parsed1 = _json_object(raw1["output_text"])
                first_valid = valid_pair_array(parsed1, "bridges", 2)
                proposals = extract_pairs(parsed1.get("bridges"), 2) if first_valid else []
                row["first_status"] = raw1["status"]
                row["first_usage"] = raw1["usage"]
                row["first_raw_output"] = raw1["output_text"]
                row["first_parse_success"] = first_valid
                row["first_score"] = score_first(case, proposals) if first_valid else None
                if arm == "A-ordinary":
                    ordinary_answer = raw1["output_text"]
                    ordinary_pairs = proposals
                else:
                    unseen = [e for e in proposals if e not in ordinary_pairs]
                    row["candidate_links_unselected_by_A_observation"] = [list(e) for e in unseen]
                    row["valid_unselected_by_A_observation"] = [list(e) for e in unseen if legal_bridge(case, e)]
                p2 = second_prompt(case, proposals)
                raw2 = responses_call(args.model, p2, args.max_output_tokens, args.reasoning_effort, key)
                metadata["calls"] += 1
                parsed2 = _json_object(raw2["output_text"])
                second_valid = valid_pair_array(parsed2, "new_paths", 12)
                claims = extract_pairs(parsed2.get("new_paths"), 12) if second_valid else []
                row["second_status"] = raw2["status"]
                row["second_usage"] = raw2["usage"]
                row["second_raw_output"] = raw2["output_text"]
                row["second_parse_success"] = second_valid
                row["second_score"] = (
                    score_second(case, row["first_score"], claims)
                    if second_valid and first_valid
                    else None
                )
            except RuntimeError as exc:
                row["error"] = str(exc)
                metadata["failed_calls"].append({"case": case["id"], "arm": arm, "reason": str(exc)})
                metadata["status"] = "incomplete_live_error"
                return metadata
    metadata["status"] = "complete_exploratory_live_pilot"
    for cr in metadata["cases"]:
        for arm_row in cr["arms"].values():
            if arm_row.get("first_status") != "completed" or arm_row.get("second_status") != "completed" or not arm_row.get("first_parse_success") or not arm_row.get("second_parse_success"):
                metadata["status"] = "completed_calls_with_incomplete_or_unparseable_output"
    for case_result in metadata["cases"]:
        arms = case_result["arms"]
        a_score = arms["A-ordinary"]["first_score"]
        d_score = arms["D-shadow"]["first_score"]
        if a_score is None or d_score is None:
            case_result["exploratory_D_downstream_pairs_not_reached_by_A"] = None
            case_result["D_outperforms_A_on_oracle_pairs"] = None
            case_result["comparison_status"] = "unavailable_invalid_first_stage_schema"
            continue
        a = set(map(tuple, a_score["verified_new_terminal_pairs"]))
        d = set(map(tuple, d_score["verified_new_terminal_pairs"]))
        case_result["exploratory_D_downstream_pairs_not_reached_by_A"] = sorted([list(x) for x in d-a])
        case_result["D_outperforms_A_on_oracle_pairs"] = len(d) > len(a)
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditable first Shadowseed Q1/Q2 feasibility pilot")
    parser.add_argument("mode", choices=["selftest", "run"])
    parser.add_argument("--cases", type=Path, default=Path(__file__).with_name("first_pilot_cases.json"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--case-ids", nargs="*", default=["ARCHIVE", "LOGISTICS", "NEGATIVE"])
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--reasoning-effort", default="low", choices=["minimal", "low", "medium", "high"])
    parser.add_argument("--max-output-tokens", type=int, default=900)
    parser.add_argument("--max-calls", type=int, default=24)
    parser.add_argument(
        "--acknowledge-retired-paid-run",
        action="store_true",
        help="Explicitly opt in to the retired and scientifically invalid paid pilot.",
    )
    args = parser.parse_args()
    if args.mode == "run" and not args.acknowledge_retired_paid_run:
        raise SystemExit("retired paid pilot: explicit --acknowledge-retired-paid-run is required")
    if args.max_calls > 24 or args.max_output_tokens > 1200 or args.max_calls < 0 or args.max_output_tokens < 128:
        raise SystemExit("safety budget exceeded or invalid")
    cases = read_cases(args.cases)
    if args.mode == "selftest":
        result = selftest(cases)
    else:
        selected = [c for c in cases if c["id"] in args.case_ids]
        if len(selected) != len(set(args.case_ids)) or len(selected) == 0:
            raise SystemExit("unknown case selection")
        result = pilot(selected, args, args.cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"schema": result["schema"], "status": result["status"], "model_calls": result.get("calls", result.get("model_calls", 0)), "cases": len(result["cases"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
