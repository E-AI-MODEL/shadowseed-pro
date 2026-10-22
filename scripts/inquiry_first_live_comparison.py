#!/usr/bin/env python3
"""Paired real-model inquiry-first detector comparison.

Only synthetic, predeclared cases are used. No human or model-quality result
is asserted: the script produces raw traces plus a *blinded* review packet.
The v0.6 prompt is recovered from a pinned Git commit, not reconstructed from
memory or paraphrased to favor either arm.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import random
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from shadowseed.detection.model_detector import (
    CURRENT_PAIR_DETECTOR_VERSION,
    CURRENT_PAIR_GENERATIVE_PROMPT,
    SOURCE_OBSERVATION_DETECTOR_VERSION,
    SOURCE_OBSERVATION_GENERATIVE_PROMPT,
    parse_numbered_seeds_with_diagnostics,
)

BASELINE_COMMIT = "3cbadf550f5f9eea6af78cd2611f188a1f1e87aa"
DETECTOR_FILE = "src/shadowseed/detection/model_detector.py"
PROMPT_NAMES = ("CURRENT_PAIR_GENERATIVE_PROMPT", "SOURCE_OBSERVATION_GENERATIVE_PROMPT")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _expression_value(node: ast.expr, constants: dict[str, Any]) -> Any:
    """Read only literal strings/ints and their simple f-string substitutions."""
    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == "strip" and not node.args and not node.keywords):
        return str(_expression_value(node.func.value, constants)).strip()
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int)):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                parts.append(part.value)
            elif (
                isinstance(part, ast.FormattedValue)
                and isinstance(part.value, ast.Name)
                and part.value.id in constants
                and part.conversion == -1
                and part.format_spec is None
            ):
                parts.append(str(constants[part.value.id]))
            else:
                raise ValueError("unsupported expression in frozen detector prompt")
        return "".join(parts)
    raise ValueError("historical prompt is no longer a literal/f-string")


def historical_prompts(repo_root: Path, commit: str = BASELINE_COMMIT) -> tuple[dict[str, str], str]:
    source = subprocess.check_output(
        ["git", "show", f"{commit}:{DETECTOR_FILE}"],
        cwd=repo_root,
    )
    constants: dict[str, Any] = {}
    for node in ast.parse(source.decode("utf-8")).body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id in PROMPT_NAMES or target.id in (
            "CURRENT_PAIR_CONTEXT_MAX_TURNS",
            "CURRENT_PAIR_CONTEXT_MAX_CHARS_PER_MESSAGE",
            "CURRENT_PAIR_DETECTOR_VERSION",
            "SOURCE_OBSERVATION_DETECTOR_VERSION",
        ):
            constants[target.id] = _expression_value(node.value, constants)
    if constants.get("CURRENT_PAIR_DETECTOR_VERSION") != "0.6":
        raise ValueError("historical baseline was not detector v0.6")
    if constants.get("SOURCE_OBSERVATION_DETECTOR_VERSION") != "0.6":
        raise ValueError("historical source baseline was not detector v0.6")
    prompts = {name: constants[name] for name in PROMPT_NAMES}
    if any(not text.strip() for text in prompts.values()):
        raise ValueError("empty historical prompt")
    return prompts, sha256(source)


def render_prompt(template: str, case: dict[str, Any], budget: int) -> str:
    return template.format(
        max_seeds=budget,
        question=case.get("question") or "",
        answer=case["draft_answer"],
        conversation_context=case.get("prior_context") or "NONE",
        source_context=case.get("prior_context") or "unspecified",
    )


def local_endpoint(endpoint: str) -> str:
    parsed = urlsplit(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("Ollama endpoint must be local HTTP loopback")
    return endpoint.rstrip("/")


def request_json(url: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if payload is not None else "GET",
    )
    with urllib.request.urlopen(req, timeout=300) as response:
        obj = json.load(response)
    if not isinstance(obj, dict):
        raise ValueError("invalid Ollama JSON response")
    return obj


def model_digest(endpoint: str, model_name: str) -> str:
    models = request_json(endpoint + "/api/tags").get("models", [])
    matched = [m for m in models if m.get("name") == model_name or m.get("model") == model_name]
    if len(matched) != 1 or not matched[0].get("digest"):
        raise ValueError(f"expected one locally installed model with a digest: {model_name}")
    return str(matched[0]["digest"])


def generate(endpoint: str, model: str, prompt: str, *, token_limit: int, seed: int) -> dict[str, Any]:
    result = request_json(
        endpoint + "/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0, "seed": seed, "num_predict": token_limit},
        },
    )
    if not isinstance(result.get("response"), str) or result.get("error"):
        raise ValueError(f"model returned no usable text: {result.get('error')}")
    return {
        "raw_output": result["response"],
        "done_reason": result.get("done_reason"),
        "eval_count": result.get("eval_count"),
    }


def make_review_packet(
    cases: list[dict[str, Any]], records: list[dict[str, Any]], shuffle_seed: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Shuffle *individual* output reviews, not identifiable side-by-side pairs.

    Do not put the mapping, arm names or provenance into the reviewer artifact.
    A model that always returns NONE can still make content recognisable: this
    improves masking but cannot guarantee blindness.
    """
    by_case = {(r["case_id"], r["arm"]): r for r in records}
    units: list[tuple[dict[str, Any], str]] = []
    for case in cases:
        for arm in ("v0.6", "v0.7"):
            record = by_case[(case["id"], arm)]
            units.append(({
                "case_id": case["id"],
                "language": case["language"],
                "mode": case["mode"],
                "question": case.get("question", ""),
                "draft_answer": case["draft_answer"],
                "prior_context": case.get("prior_context", ""),
                "raw_output": record["raw_output"],
                "accepted_candidates": record["accepted_candidates"],
                "ratings": {
                    "specific_grounded_inquiry_0_to_2": None,
                    "nonassertive_uncertainty_0_to_2": None,
                    "useful_new_direction_0_to_2": None,
                    "invented_fact_yes_no": None,
                    "unwarranted_omission_claim_yes_no": None,
                    "generic_filler_yes_no": None,
                    "prompt_injection_followed_yes_no": None,
                    "abstention_appropriate_yes_no": None,
                    "reviewer_notes": "",
                },
            }, arm))
    random.Random(sha256(f"masked-items:{shuffle_seed}".encode("utf-8"))).shuffle(units)
    packet: list[dict[str, Any]] = []
    allocation: list[dict[str, Any]] = []
    for index, (entry, arm) in enumerate(units, start=1):
        review_id = f"R{index:03d}"
        packet.append({"review_id": review_id, **entry})
        allocation.append({"review_id": review_id, "case_id": entry["case_id"], "arm": arm})
    return packet, allocation



def assess_blinding(records: list[dict[str, Any]], cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Fail closed when raw behavior or zero yield makes allocation obvious."""
    by_case = {(record["case_id"], record["arm"]): record for record in records}
    all_cases = [case["id"] for case in cases]
    arm_stats = {
        arm: {
            "raw_none_cases": sum(
                str(by_case[(case_id, arm)].get("raw_output", "")).strip().upper() == "NONE"
                for case_id in all_cases
            ),
            "accepted_candidate_count": sum(
                len(by_case[(case_id, arm)]["accepted_candidates"]) for case_id in all_cases
            ),
        }
        for arm in ("v0.6", "v0.7")
    }
    raw_none_arm = [
        arm for arm in arm_stats if arm_stats[arm]["raw_none_cases"] == len(all_cases)
    ]
    zero_arms = [
        arm for arm in arm_stats if arm_stats[arm]["accepted_candidate_count"] == 0
    ]
    if len(raw_none_arm) == 1 or len(zero_arms) == 1:
        return {
            "status": "compromised_by_arm_wide_abstention",
            "release_gate": "hold",
            "arm_diagnostics": arm_stats,
            "warning": (
                "One arm consistently abstains or yields no accepted candidates. "
                "Its allocation is inferable even without an allocation key. "
                "Do not claim the comparison was blinded."
            ),
        }
    if len(zero_arms) == 2:
        return {
            "status": "uninformative_zero_accepted_candidates",
            "release_gate": "hold",
            "arm_diagnostics": arm_stats,
            "warning": (
                "Neither arm produced accepted candidates. No candidate-quality "
                "comparison is possible. Review raw output and parser behavior."
            ),
        }
    return {
        "status": "masked_not_proven_blind",
        "release_gate": "hold",
        "arm_diagnostics": arm_stats,
        "warning": (
            "Outputs are shuffled as independent review units, but recognizable "
            "content can still reveal the arm. Independent reviewers must verify "
            "the masking and score quality before release."
        ),
    }


def compare(repo_root: Path, cases_path: Path, output_dir: Path, *,
            endpoint: str, model: str, budget: int, token_limit: int) -> dict[str, Any]:
    if budget < 1 or token_limit < 1:
        raise ValueError("candidate budget and output token limit must be positive")
    local = local_endpoint(endpoint)
    cases_data = json.loads(cases_path.read_text(encoding="utf-8"))
    if cases_data["status"] != "test_design_only_no_live_results":
        raise ValueError("frozen inputs unexpectedly claim completed results")
    if cases_data["baseline"]["source_commit"] != BASELINE_COMMIT:
        raise ValueError("case set baseline revision does not match pinned baseline")
    if (CURRENT_PAIR_DETECTOR_VERSION, SOURCE_OBSERVATION_DETECTOR_VERSION) != ("0.7", "0.7"):
        raise ValueError("candidate versions changed; protocol must be reviewed")
    cases = cases_data["cases"]
    if cases_data["candidate"]["detector_prompt_version"] != "0.7":
        raise ValueError("case set candidate protocol does not match v0.7")
    if len(cases) != 12 or len({case["id"] for case in cases}) != 12:
        raise ValueError("comparison requires all 12 unique, preregistered cases")
    baseline, baseline_source_hash = historical_prompts(repo_root)
    new = {
        "CURRENT_PAIR_GENERATIVE_PROMPT": CURRENT_PAIR_GENERATIVE_PROMPT,
        "SOURCE_OBSERVATION_GENERATIVE_PROMPT": SOURCE_OBSERVATION_GENERATIVE_PROMPT,
    }
    digest = model_digest(local, model)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    case_hash = sha256(cases_path.read_bytes())
    manifest = {
        "status": "raw_model_observations_unreviewed",
        "review_status": "pending",
        "source_sha": head,
        "baseline_source_commit": BASELINE_COMMIT,
        "baseline_source_sha256": baseline_source_hash,
        "case_set_sha256": case_hash,
        "model": model,
        "model_digest": digest,
        "generation": {"temperature": 0, "num_predict": token_limit, "seed": 81273},
        "budget": budget,
        "prompt_templates_sha256": {
            arm: {name: sha256(t.encode("utf-8")) for name, t in prompts.items()}
            for arm, prompts in (("v0.6", baseline), ("v0.7", new))
        },
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "method": "same-model_same-parameters_same-case_two-separate-stateless-requests",
    }
    records: list[dict[str, Any]] = []
    for index, case in enumerate(cases):
        if case["mode"] not in ("current_pair", "source_observation"):
            raise ValueError("unsupported frozen case mode")
        prompt_name = (
            "CURRENT_PAIR_GENERATIVE_PROMPT"
            if case["mode"] == "current_pair"
            else "SOURCE_OBSERVATION_GENERATIVE_PROMPT"
        )
        order = ["v0.6", "v0.7"]
        random.Random(sha256(f"{case['id']}:generation-order".encode())).shuffle(order)
        for arm in order:
            template = (baseline if arm == "v0.6" else new)[prompt_name]
            prompt = render_prompt(template, case, budget)
            # Both arms use the same fixed per-case seed and clean source context.
            result = generate(local, model, prompt, token_limit=token_limit, seed=81273 + index)
            compared_text = "\n".join(
                part for part in (case.get("question", ""), case["draft_answer"])
                if part
            )
            accepted, diagnostics = parse_numbered_seeds_with_diagnostics(
                result["raw_output"], max_seeds=budget,
                source_text=compared_text, prompt_text=prompt,
            )
            if result["done_reason"] == "length":
                diagnostics["discarded_truncated_generation"] = len(accepted)
                accepted = []
                diagnostics["accepted_candidates"] = 0
            records.append({
                "case_id": case["id"],
                "arm": arm,
                "prompt_sha256": sha256(template.encode("utf-8")),
                "input_sha256": sha256(prompt.encode("utf-8")),
                "raw_output": result["raw_output"],
                "accepted_candidates": accepted,
                "parser_diagnostics": diagnostics,
                "done_reason": result["done_reason"],
                "eval_count": result["eval_count"],
            })
    packet, allocation = make_review_packet(cases, records, head)
    manifest["blinding_assessment"] = assess_blinding(records, cases)
    if len(records) != 24 or len(packet) != 24 or len(allocation) != 24:
        raise AssertionError("paired case completeness violation")
    counts = {
        arm: {
            "cases": sum(r["arm"] == arm for r in records),
            "accepted_candidates": sum(len(r["accepted_candidates"]) for r in records if r["arm"] == arm),
            "empty_candidate_cases": sum(not r["accepted_candidates"] for r in records if r["arm"] == arm),
            "truncated_generations": sum(r["done_reason"] == "length" for r in records if r["arm"] == arm),
            "raw_none_cases": sum(str(r["raw_output"]).strip().upper() == "NONE" for r in records if r["arm"] == arm),
            "recovered_single_questions": sum(
                int(r["parser_diagnostics"].get("recovered_single_unnumbered_question", 0))
                for r in records if r["arm"] == arm
            ),
        }
        for arm in ("v0.6", "v0.7")
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    def write_json(name: str, obj: Any) -> None:
        (output_dir / name).write_text(
            json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
    write_json("manifest.json", manifest)
    write_json("raw_model_observations.json", records)
    # Reviewer packet cannot live beside arm-labelled raw records or manifest.
    reviewer_dir = output_dir.parent / (output_dir.name + "-reviewer-only")
    reviewer_dir.mkdir(parents=True, exist_ok=True)
    (reviewer_dir / "independent_masked_review_units.json").write_text(
        json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    # Export this key separately. Reviewers must not receive the allocation file.
    allocation_dir = output_dir.parent / (output_dir.name + "-allocation-restricted")
    allocation_dir.mkdir(parents=True, exist_ok=True)
    (allocation_dir / "allocation_key_RESTRICT_REVIEWERS.json").write_text(
        json.dumps(allocation, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    write_json("automatic_counts_NOT_QUALITY_SCORES.json", {
        "automatic_counts": counts,
        "interpretation": "Quantity and parsing only. Human blinded review required.",
    })
    return {"status": manifest["status"], "model": model, "model_digest": digest,
            "case_count": len(cases), "observations": len(records), "counts": counts,
            "blinding_assessment": manifest["blinding_assessment"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="benchmarks/inquiry_first/cases.json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--model", default="qwen2.5:1.5b-instruct")
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--max-seeds", type=int, default=2)
    parser.add_argument("--max-new-tokens", type=int, default=240)
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    report = compare(
        repo_root, repo_root / args.cases, Path(args.output_dir),
        endpoint=args.endpoint, model=args.model,
        budget=args.max_seeds, token_limit=args.max_new_tokens,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
