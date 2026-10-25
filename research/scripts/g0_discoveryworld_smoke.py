#!/usr/bin/env python3
"""Offline, model-free DiscoveryWorld E1 interface smoke; NOT a Shadowseed Q1/Q2 trial.

Run only in a disposable environment without model keys. Upstream DiscoveryWorld
is installed from its exact pinned commit by the companion GitHub workflow.
This script writes only sanitized action/state evidence, never oracle scorecards,
world histories, rendered images, credentials, or the upstream world's rules.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_UPSTREAM_SHA = "fd591323920be0d3786ef350955de1945aa571e5"
SCENARIO = "Small Skills: Dialog Test"
DIFFICULTY = "Normal"
SCENARIO_SEED = 0


def _view(observation: dict) -> dict:
    if observation.get("errors"):
        raise AssertionError("Agent observation failed: " + repr(observation["errors"]))
    ui = observation["ui"]
    loc = ui["agentLocation"]
    return {
        "x": int(loc["x"]),
        "y": int(loc["y"]),
        "faceDirection": str(loc["faceDirection"]),
        "world_steps": int(ui["world_steps"]),
    }


def _run_child(thread_id: int, out_file: Path) -> None:
    # No LLM client, hosted detector, research adapter, benchmark score, or key is used.
    import pygame  # Import only inside the separately isolated child process.
    from discoveryworld.DiscoveryWorldAPI import DiscoveryWorldAPI

    api = DiscoveryWorldAPI(threadID=thread_id)
    if api.loadScenario(SCENARIO, DIFFICULTY, randomSeed=SCENARIO_SEED, numUserAgents=1) is not True:
        raise AssertionError("Upstream scenario initialization failed")

    actions = api.listKnownActions()
    if "ROTATE_DIRECTION" not in actions:
        raise AssertionError("Upstream general action inventory lacks ROTATE_DIRECTION")

    original = _view(api.getAgentObservation(agentIdx=0))
    valid = api.performAgentAction(
        agentIdx=0, actionJSON={"action": "ROTATE_DIRECTION", "arg1": "north"}
    )
    if valid.get("success") is not True or valid.get("errors"):
        raise AssertionError("Safe, grammatically valid independent action was rejected: " + repr(valid))

    if api.tick().get("success") is not True:
        raise AssertionError("Upstream world tick after valid action failed")
    rotated = _view(api.getAgentObservation(agentIdx=0))
    if rotated["faceDirection"] != "north":
        raise AssertionError("A reported successful rotation did not change/retain the target orientation")
    if rotated["world_steps"] <= original["world_steps"]:
        raise AssertionError("Upstream world time did not progress")

    invalid = api.performAgentAction(
        agentIdx=0, actionJSON={"action": "ROTATE_DIRECTION", "arg1": "northwest"}
    )
    if invalid.get("success") is not False or not invalid.get("errors"):
        raise AssertionError("An unrecognized direction was not rejected as invalid: " + repr(invalid))

    if api.tick().get("success") is not True:
        raise AssertionError("Upstream world tick after invalid action failed")
    after_invalid = _view(api.getAgentObservation(agentIdx=0))
    if after_invalid["faceDirection"] != rotated["faceDirection"]:
        raise AssertionError("A rejected rotation unexpectedly changed orientation")

    frame_dir = Path("video") / f"frames-thread{thread_id}"
    image_count = len(list(frame_dir.glob("ui_agent_*.png")))
    if image_count == 0:
        raise AssertionError("Observation rendering did not produce the expected isolated frame files")

    out_file.write_text(
        json.dumps(
            {
                "initial": original,
                "after_valid_action": rotated,
                "after_invalid_action": after_invalid,
                "valid_action_accepted": True,
                "invalid_action_rejected": True,
                "rendered_frame_count": image_count,
                "per_arm_frame_directory": str(frame_dir),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    pygame.quit()


def _run_parent(upstream_dir: Path, out_file: Path) -> None:
    if not upstream_dir.is_dir():
        raise AssertionError("Missing pinned upstream checkout: " + str(upstream_dir))
    resolved_sha = subprocess.check_output(
        ["git", "-C", str(upstream_dir), "rev-parse", "HEAD"],
        text=True,
        timeout=10,
    ).strip()
    if resolved_sha != EXPECTED_UPSTREAM_SHA:
        raise AssertionError("Unexpected upstream revision: " + resolved_sha)

    source_script = Path(__file__).resolve()
    summaries = []
    # Explicitly narrow child environment: no GITHUB_TOKEN, model-provider keys,
    # host Github context, secrets, or product repository working directory.
    safe_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": "C.UTF-8",
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    with tempfile.TemporaryDirectory(prefix="g0-discoveryworld-offline-") as tmp:
        for index in (0, 1):
            arm_dir = Path(tmp) / f"arm_{index}"
            arm_dir.mkdir()
            result_file = arm_dir / "sanitized.json"
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(source_script),
                        "--child",
                        "--thread-id",
                        str(9101 + index),
                        "--output",
                        str(result_file),
                    ],
                    cwd=arm_dir,
                    env=safe_env,
                    check=True,
                    text=True,
                    capture_output=True,
                    timeout=120,
                )
            except subprocess.TimeoutExpired as exc:
                raise AssertionError("Isolated external simulator timed out") from exc
            except subprocess.CalledProcessError as exc:
                raise AssertionError(
                    "Isolated simulator failed (no raw world history saved): "
                    + (exc.stderr or "")[-1800:]
                ) from exc
            data = json.loads(result_file.read_text(encoding="utf-8"))
            summaries.append(data)

    comparable_fields = (
        "initial",
        "after_valid_action",
        "after_invalid_action",
        "valid_action_accepted",
        "invalid_action_rejected",
    )
    if any(summaries[0][key] != summaries[1][key] for key in comparable_fields):
        raise AssertionError("Identical scenario seeds diverged between independent isolated arms")
    if summaries[0]["per_arm_frame_directory"] == summaries[1]["per_arm_frame_directory"]:
        raise AssertionError("Frame paths overlap between the two isolated arms")

    evidence = {
        "status": "offline_external_executor_interface_smoke_only",
        "claimed_q1_or_q2_efficacy": False,
        "hosted_model_calls": 0,
        "hosted_embedding_calls": 0,
        "shadowseed_product_mutations": 0,
        "upstream_repository": "allenai/discoveryworld",
        "upstream_sha": resolved_sha,
        "scenario": SCENARIO,
        "difficulty": DIFFICULTY,
        "scenario_seed": SCENARIO_SEED,
        "arm_isolation": "fresh OS process, fresh cwd, separate pygame instance and thread/frame ID",
        "initial_agent_states_match": True,
        "identical_action_trajectories_match": True,
        "valid_action_was_executed": True,
        "invalid_action_was_rejected": True,
        "agent_originated_new_research_question_tested": False,
        "second_order_investigability_tested": False,
        "independent_evaluator_approval": False,
        "independent_method_reviewer_approval": False,
        "g0_passed": False,
        "arms": summaries,
    }
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "OFFLINE INTERFACE SMOKE PASSED: isolated seeds/actions verified; "
        "0 model calls; NO G0/Q1/Q2 conclusion."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--thread-id", type=int, default=9101)
    ap.add_argument("--upstream-dir", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.child:
        _run_child(args.thread_id, args.output.resolve())
        return
    if args.upstream_dir is None:
        ap.error("--upstream-dir is required in the parent process")
    _run_parent(args.upstream_dir.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
