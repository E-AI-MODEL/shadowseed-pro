#!/usr/bin/env python3
"""Research-only, model-free E1 open-inquiry action/observation preflight.

This is NOT a language interpreter, an independent semantic evaluator, an
experiment about Q1/Q2, or a G0 approval. Researcher-authored natural-language
questions are paired with test actions; the only mechanically determined claims
are whether an action is representable/accepted and what the agent can observe.
The upstream world is isolated per trial, not fed to a Shadowseed production host.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

UPSTREAM_SHA = "fd591323920be0d3786ef350955de1945aa571e5"
SCENARIO = "Small Skills: Dialog Test"
DIFFICULTY = "Normal"
WORLD_SEED = 0
MAX_CASES = 12
MAX_QUESTION_LENGTH = 300
MAX_ACTION_LENGTH = 350
DIRECTIONS = ("north", "east", "south", "west")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def public_projection(observation: dict) -> dict:
    """Only UI fields available to the agent; never task scores, oracle, world history, images."""
    if observation.get("errors"):
        raise RuntimeError("Upstream observation did not succeed")
    loc = observation["ui"]["agentLocation"]
    return {
        "position": [int(loc["x"]), int(loc["y"])],
        "facing": str(loc["faceDirection"]),
        "legal_move_directions": sorted(str(v) for v in loc["directions_you_can_move"]),
        "world_step": int(observation["ui"]["world_steps"]),
    }


def physical_projection(view: dict) -> dict:
    """Ignore time-only changes; even a change here is NOT a semantic information-gain score."""
    return {
        "position": view["position"],
        "facing": view["facing"],
        "legal_move_directions": view["legal_move_directions"],
    }


def resolve_action(request: Any, initial: dict, known: dict) -> tuple[dict | None, str]:
    """Convert a researcher-supplied TOOL request, not natural language, into a world action.

    No semantic classifier is used. Unsupported requests remain explicitly untestable.
    Dynamic placeholders refer only to the agent's disclosed state.
    """
    if request is None:
        return None, "natural_language_not_automatically_executable"
    if not isinstance(request, dict) or len(canonical_json(request)) > MAX_ACTION_LENGTH:
        return None, "unsupported_tool_request"
    if not isinstance(request.get("action"), str) or request["action"] not in known:
        return None, "unsupported_tool_request"
    if set(request) - {"action", "arg1", "arg2"}:
        return None, "unsupported_tool_request"
    converted = dict(request)
    for field in ("arg1", "arg2"):
        if field not in converted:
            continue
        val = converted[field]
        if val == "$current_facing":
            converted[field] = initial["facing"]
        elif val == "$alternate_facing":
            converted[field] = next(d for d in DIRECTIONS if d != initial["facing"])
        elif val == "$first_legal_move":
            if not initial["legal_move_directions"]:
                return None, "no_legal_move_in_this_start_state"
            converted[field] = initial["legal_move_directions"][0]
        elif isinstance(val, str) and val.startswith("$"):
            return None, "unsupported_tool_request"
        elif not isinstance(val, (str, int, float)):
            return None, "unsupported_tool_request"
    return converted, "executable_tool_grammar"


def action_status(resolution: str, result: dict | None, before: dict, after: dict) -> str:
    """Admissibility and observable state only; never infer meaning/novelty from state change."""
    if resolution != "executable_tool_grammar":
        return "not_testable_by_this_evaluator"
    if result is None:
        return "executor_error"
    if result.get("success") is not True:
        return "rejected_by_upstream"
    if physical_projection(before) != physical_projection(after):
        return "accepted_observable_state_difference"
    return "accepted_no_observable_state_difference"


def child_run(out_path: Path, thread_id: int, case: dict | None) -> None:
    # Import deliberately inside a fresh disposable child process.
    import pygame
    from discoveryworld.DiscoveryWorldAPI import DiscoveryWorldAPI

    api = DiscoveryWorldAPI(threadID=thread_id)
    if api.loadScenario(SCENARIO, DIFFICULTY, randomSeed=WORLD_SEED, numUserAgents=1) is not True:
        raise RuntimeError("Pinned simulator could not initialize scenario")
    known = api.listKnownActions()
    before = public_projection(api.getAgentObservation(0))

    resolution = "time_only_control"
    selected_action = None
    result = None
    if case is not None:
        selected_action, resolution = resolve_action(case.get("tool_request"), before, known)
        if selected_action is not None:
            try:
                result = api.performAgentAction(0, selected_action)
            except Exception as exc:
                # A simulator fault is not a valid negative or an absent opportunity.
                resolution = "executor_error_" + type(exc).__name__
                result = None

    if api.tick().get("success") is not True:
        raise RuntimeError("Pinned simulator tick failed")
    after = public_projection(api.getAgentObservation(0))
    status = ("time_only_control" if case is None else action_status(resolution, result, before, after))

    frame_dir = Path("video") / f"frames-thread{thread_id}"
    frame_count = len(list(frame_dir.glob("ui_agent_*.png")))
    if not frame_count:
        raise RuntimeError("No isolated observation frames were produced")

    record = {
        "case_id": "time_control" if case is None else case["id"],
        "origin": "researcher_authored_calibration_not_model_originated",
        "question": None if case is None else case["question"],
        "requested_tool_action": None if case is None else case.get("tool_request"),
        "resolved_tool_action": selected_action,
        "representation": resolution,
        "status": status,
        "upstream_action_success": None if result is None else result.get("success"),
        "before": before,
        "after": after,
        "observable_state_changed": physical_projection(before) != physical_projection(after),
        "frame_count_in_disposable_directory": frame_count,
        "frame_thread_id": thread_id,
        "semantic_informativeness": "not_assessed",
        "question_novelty": "not_assessed",
        "later_investigability": "not_assessed",
        "global_no_opportunity": "not_assessed",
    }
    out_path.write_text(canonical_json(record), encoding="utf-8")
    pygame.quit()


def _isolated_run(script: Path, case: dict | None, output_dir: Path, thread_id: int) -> dict:
    output_dir.mkdir(parents=True, exist_ok=False)
    target = output_dir / "sanitized.json"
    # No model secrets, GitHub API token or parent research path.
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": "C.UTF-8",
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    cmd = [
        sys.executable, str(script), "--child",
        "--thread-id", str(thread_id), "--output", str(target),
    ]
    if case is not None:
        cmd.extend(["--case-json", canonical_json(case)])
    try:
        subprocess.run(
            cmd, cwd=output_dir, env=env, check=True,
            capture_output=True, text=True, timeout=90,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError("Timed-out child; no semantic null inferred") from exc
    except subprocess.CalledProcessError as exc:
        raise AssertionError(
            "Isolated simulator failure; no Q2 claim: " + (exc.stderr or "")[-1500:]
        ) from exc
    return json.loads(target.read_text(encoding="utf-8"))


def _comparable(record: dict) -> dict:
    """Remove per-run thread/frame metadata, keep every scientific assertion identical."""
    return {k: v for k, v in record.items() if k not in {
        "frame_thread_id", "frame_count_in_disposable_directory",
    }}


def run_parent(upstream_dir: Path, fixture: Path, output_path: Path) -> None:
    if not upstream_dir.is_dir() or not fixture.is_file():
        raise RuntimeError("Pinned upstream checkout and calibration fixture must exist")
    actual_sha = subprocess.check_output(
        ["git", "-C", str(upstream_dir), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    if actual_sha != UPSTREAM_SHA:
        raise AssertionError("Unreviewed upstream code revision: " + actual_sha)

    data = json.loads(fixture.read_text(encoding="utf-8"))
    if data.get("schema") != "g0-open-inquiry-calibration-v0":
        raise AssertionError("Unsupported inquiry fixture schema")
    if data.get("source") != "researcher_authored_public_calibration":
        raise AssertionError("Cannot claim unverified source was researcher-authored")
    cases = data.get("cases")
    if not isinstance(cases, list) or not 1 <= len(cases) <= MAX_CASES:
        raise AssertionError("Invalid calibration case count")
    ids = [c.get("id") for c in cases]
    if len(ids) != len(set(ids)):
        raise AssertionError("Inquiry IDs are not unique")
    for case in cases:
        if not isinstance(case.get("id"), str) or not case["id"].isidentifier():
            raise AssertionError("Malformed inquiry ID")
        question = case.get("question")
        if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUESTION_LENGTH:
            raise AssertionError("Inquiry must carry a bounded, nonempty question")

    script = Path(__file__).resolve()
    duplicated = {}
    with tempfile.TemporaryDirectory(prefix="g0-open-inquiry-") as tmp:
        for ix, case in enumerate([None, *cases]):
            left = _isolated_run(script, case, Path(tmp) / f"r{ix}_a", 19000 + ix * 2)
            right = _isolated_run(script, case, Path(tmp) / f"r{ix}_b", 19001 + ix * 2)
            if _comparable(left) != _comparable(right):
                raise AssertionError("Fresh isolated replay did not reproduce: " + left["case_id"])
            duplicated[left["case_id"]] = left

    control = duplicated.pop("time_control")
    control_state = physical_projection(control["after"])
    for rec in duplicated.values():
        rec["different_from_time_matched_no_action"] = (
            physical_projection(rec["after"]) != control_state
            if rec["status"].startswith("accepted_") else None
        )
        # A different state under intervention is not itself information gain,
        # much less a novel model-originated second-order inquiry.
        if rec["status"].startswith("accepted_") and rec["upstream_action_success"] is not True:
            raise AssertionError("Accepted status contradicts upstream action success")

    statuses = {key: val["status"] for key, val in duplicated.items()}
    evidence = {
        "status": "offline_researcher_authored_open_inquiry_interface_calibration_only",
        "source_kind": data["source"],
        "fixture_sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
        "upstream_repository": "allenai/discoveryworld",
        "upstream_sha": actual_sha,
        "scenario": SCENARIO,
        "scenario_seed": WORLD_SEED,
        "agent_generated_questions": 0,
        "hosted_model_calls": 0,
        "hosted_embedding_calls": 0,
        "shadowseed_product_mutations": 0,
        "feedback_regime": "RI_interface_calibration_only",
        "replays_per_case": 2,
        "exact_reproduction_for_recorded_projection": True,
        "oracle_task_score_used": False,
        "semantic_novelty_assessed": False,
        "second_order_investigability_assessed": False,
        "global_no_opportunity_proven": False,
        "independent_technical_reviewer_signed": False,
        "independent_conceptual_reviewer_signed": False,
        "g0_passed": False,
        "status_by_case": statuses,
        "time_control": control,
        "cases": list(duplicated.values()),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(
        "G0 open-inquiry executor interface preflight:",
        len(cases), "researcher-authored requests, two isolated runs each;",
        "zero model calls, no semantic/Q2 claim.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--case-json")
    parser.add_argument("--thread-id", type=int)
    parser.add_argument("--upstream-dir", type=Path)
    parser.add_argument("--fixture", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.child:
        if args.thread_id is None:
            parser.error("Child requires --thread-id")
        case = None if args.case_json is None else json.loads(args.case_json)
        child_run(args.output.resolve(), args.thread_id, case)
    else:
        if args.upstream_dir is None or args.fixture is None:
            parser.error("Parent requires --upstream-dir and --fixture")
        run_parent(args.upstream_dir.resolve(), args.fixture.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
