#!/usr/bin/env python3
"""NO-MODEL G0 preflight linking REAL ShadowChatSession to REAL DiscoveryWorld.

Researcher-scripted host questions/answers and detector responses are processed
by the canonical product detector, parser, intake, manager and lifecycle across
four distinct turns. A separate simulator supplies agent-visible observations.
Two independent session variants receive precisely the SAME authored world
actions; one has investigator-scripted candidate detections, the other receives
explicit detector NONE. This is an integration/ablation *mechanics* test, NOT an
A/B/C/D/E model comparison and NOT evidence about Q1/Q2 or semantic growth.
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

from shadowseed.chat import ShadowChatSession
from shadowseed_research.benchmark.step1_gap_birth_instrument import (
    _NoGeneration,
    _recorded_product_detector,
    _seed_snapshots,
)
from g0_discoveryworld_open_inquiry import (
    action_status,
    canonical_json,
    physical_projection,
    public_projection,
    resolve_action,
)

SCHEMA = "g0-discoveryworld-shadowchat-bridge-v0"
UPSTREAM_SHA = "fd591323920be0d3786ef350955de1945aa571e5"
ARMS = ("scripted_seed", "explicit_none")
TURN_COUNT = 4
MAX_TEXT = 400
MAX_OUTPUT = 350


def _sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def validate_fixture(data: Any) -> list[dict[str, Any]]:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("unexpected bridge fixture schema")
    if data.get("source") != "RESEARCHER_SCRIPTED_NO_LLM":
        raise ValueError("bridge data must be identified as scripted, never model-originated")
    if data.get("upstream_revision") != UPSTREAM_SHA:
        raise ValueError("unreviewed upstream revision")
    if data.get("scenario") != "Small Skills: Dialog Test" or data.get("difficulty") != "Normal":
        raise ValueError("unreviewed scenario")
    if data.get("seed") != 0:
        raise ValueError("unreviewed scenario seed")
    turns = data.get("turns")
    if not isinstance(turns, list) or len(turns) != TURN_COUNT:
        raise ValueError("bridge requires exactly four distinct scripted turns")
    for index, row in enumerate(turns):
        if not isinstance(row, dict) or row.get("id") != f"T{index}":
            raise ValueError("invalid or nonsequential turn")
        q, raw = row.get("question"), row.get("detector_output")
        if not isinstance(q, str) or not q.strip() or len(q) > MAX_TEXT:
            raise ValueError("bounded nonempty investigator question required")
        if not isinstance(raw, str) or not raw.strip() or len(raw) > MAX_OUTPUT:
            raise ValueError("bounded scripted detector output required, explicit NONE preferred")
        action = row.get("world_action")
        if action is not None and (
            not isinstance(action, dict)
            or not isinstance(action.get("action"), str)
            or action["action"] not in {"ROTATE_DIRECTION", "MOVE_DIRECTION"}
            or set(action) - {"action", "arg1"}
            or not isinstance(action.get("arg1"), str)
            or len(action["arg1"]) > 50
        ):
            raise ValueError("world action outside approved, bounded grammar")
    if turns[0]["detector_output"] == "NONE" or turns[1]["detector_output"] != turns[0]["detector_output"]:
        raise ValueError("frozen scripted recurrence must be observable")
    if turns[2]["detector_output"] != "NONE" or turns[3]["detector_output"] == "NONE":
        raise ValueError("frozen negative/new candidate cases must be present")
    return turns


def _stable_seed_state(session: ShadowChatSession) -> list[dict[str, Any]]:
    """Read-only, without random seed identifiers, promotion or fabricated meanings."""
    by_id = _seed_snapshots(session)
    rows = [
        {
            "text": rec["text"],
            "status": rec["status"],
            "trace": rec["trace"],
            "weight": rec["weight"],
            "evidence_count": rec["evidence_count"],
            "occurrence_count": rec["occurrence_count"],
            "turns_dormant": rec["turns_dormant"],
            "origin_context_ref": None if rec["origin"] is None else rec["origin"]["context_ref"],
        }
        for rec in by_id.values()
    ]
    return sorted(rows, key=lambda item: item["text"])


def _host_answer_from_visible_state(world_view: dict[str, Any]) -> str:
    """Researcher-defined serializer of visible simulator facts, never a model reply."""
    return (
        f"Agentpositie: ({world_view['position'][0]}, {world_view['position'][1]}). "
        f"Kijkrichting: {world_view['facing']}. "
        "Toegestane looprichtingen volgens de zichtbare agentinterface: "
        f"{', '.join(world_view['legal_move_directions']) or 'geen'}."
    )


def _child_arm(arm: str, fixture: dict, thread_id: int, output: Path) -> None:
    if arm not in ARMS:
        raise ValueError("unknown arm")
    import pygame
    from discoveryworld.DiscoveryWorldAPI import DiscoveryWorldAPI

    turns = validate_fixture(fixture)
    responses = [
        (row["detector_output"] if arm == "scripted_seed" else "NONE")
        for row in turns
    ]
    detector, transport = _recorded_product_detector(responses, "current_pair")
    session = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        detector_backend=detector,
        model_backend=_NoGeneration(),
        revision_model_backend=_NoGeneration(),
        embedding_backend="lexical",
        allow_same_turn_revision=False,
        self_derived_signal_policy="fail_closed",
    )
    api = DiscoveryWorldAPI(threadID=thread_id)
    if api.loadScenario(fixture["scenario"], fixture["difficulty"], randomSeed=0, numUserAgents=1) is not True:
        raise RuntimeError("pinned DiscoveryWorld did not start")
    known_actions = api.listKnownActions()

    record_turns: list[dict[str, Any]] = []
    for index, row in enumerate(turns):
        before = public_projection(api.getAgentObservation(0))
        answer = _host_answer_from_visible_state(before)
        previous_ids = set(session.manager.seeds)
        events_before = len(session.manager.event_log)
        prepared = session.prepare_turn(row["question"])
        if prepared.surfaced_seed_ids or prepared.model_context:
            session.abort_turn(prepared)
            raise AssertionError("weightless scripted seed had unauthorized influence")
        after_prepare = _stable_seed_state(session)
        try:
            report = session.observe_turn(prepared, answer)
        except Exception:
            if session._pending_live_turn is not None:
                session.abort_turn(prepared)
            raise
        detector_audit = report["detector_audit"]
        if detector_audit["raw_output"] != responses[index]:
            raise AssertionError("canonical detector did not consume exact scripted response")

        new_ids = set(session.manager.seeds) - previous_ids
        created_events = {
            event.seed_id for event in session.manager.event_log[events_before:]
            if event.event_type == "created"
        }
        if new_ids != created_events:
            raise AssertionError("new seed registry and canonical birth events disagree")
        accepted_ids = {
            item["seed_id"] for item in report["intake_diagnostics"]["accepted"]
        }
        recurrent_ids = accepted_ids & previous_ids
        state = _stable_seed_state(session)
        if any(item["weight"] != 0.0 or item["evidence_count"] != 0 for item in state):
            raise AssertionError("research seed acquired nonzero authority or evidence")
        if any(item["status"] == "PROMOTED" for item in state):
            raise AssertionError("unverified research seed promoted")
        if report["surfaced_seed_ids"] or report["promoted_this_turn"]:
            raise AssertionError("untrusted seed influenced answer generation")
        if session.influence_records or session.manager.gate_events:
            raise AssertionError("research fixture must not produce authority use or Gate events")

        selected, resolution = resolve_action(row["world_action"], before, known_actions)
        result = None
        if selected is not None:
            result = api.performAgentAction(0, selected)
        if api.tick().get("success") is not True:
            raise RuntimeError("world tick failed")
        after = public_projection(api.getAgentObservation(0))
        action_result = (
            "no_investigator_action"
            if row["world_action"] is None
            else action_status(resolution, result, before, after)
        )
        if row["world_action"] is not None and not action_result.startswith("accepted_"):
            raise AssertionError("prescribed action unexpectedly failed; not a meaningful Q2 null")

        record_turns.append({
            "turn_id": row["id"],
            "question": row["question"],
            "question_origin": "INVESTIGATOR_SCRIPTED_NO_MODEL",
            "observed_world_before": before,
            "host_answer": answer,
            "host_answer_origin": "INVESTIGATOR_DEFINED_VISIBLE_STATE_SERIALIZER_NO_MODEL",
            "detector_input_prompt_sha256": _sha(transport.prompts[index]),
            "detector_input_prompt": transport.prompts[index],
            "detector_output_raw": responses[index],
            "detector_output_origin": "INVESTIGATOR_SCRIPTED_NO_MODEL",
            "parsed_candidates": list(report["detected_candidates"]),
            "parser_diagnostics": detector_audit["parse_diagnostics"],
            "canonical_accepted_candidate_count": len(accepted_ids),
            "true_seed_born_this_turn": sorted(session.manager.seeds[i].text for i in new_ids),
            "existing_seed_redetected_this_turn": sorted(session.manager.seeds[i].text for i in recurrent_ids),
            "seed_state_after_prepare": after_prepare,
            "seed_state_after_observe": state,
            "investigator_action": row["world_action"],
            "resolved_action": selected,
            "world_action_origin": "INVESTIGATOR_SCRIPTED_INDEPENDENT_OF_SEEDS",
            "world_action_status": action_result,
            "observed_world_after": after,
            "physical_world_change": physical_projection(after) != physical_projection(before),
            "seed_authority_uses": 0,
            "Gate_events": 0,
            "semantic_novelty": "NOT_ASSESSED",
            "semantic_seed_growth": "NOT_ASSESSED",
            "new_later_investigability": "NOT_ASSESSED",
        })

    if transport.calls != TURN_COUNT:
        raise AssertionError("not all canonical detector turns were called")
    frame_dir = Path("video") / f"frames-thread{thread_id}"
    if not list(frame_dir.glob("ui_agent_*.png")):
        raise RuntimeError("no scenario frames were rendered")
    output.write_text(
        json.dumps({
            "arm": arm,
            "turns": record_turns,
            "final_seed_state": _stable_seed_state(session),
            "canonical_detector_calls": transport.calls,
            "hosted_model_calls": 0,
            "seed_authority_uses": len(session.influence_records),
            "Gate_events": len(session.manager.gate_events),
            "frame_count_disposable_only": len(list(frame_dir.glob("ui_agent_*.png"))),
            "has_real_persistent_ShadowChatSession": True,
        }, sort_keys=True),
        encoding="utf-8",
    )
    pygame.quit()


def _subprocess_arm(script: Path, arm: str, fixture: Path, work: Path, thread_id: int) -> dict:
    work.mkdir()
    destination = work / "sanitized.json"
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": os.environ.get("HOME", "/tmp"),
        "LANG": "C.UTF-8",
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",
    }
    try:
        subprocess.run(
            [sys.executable, str(script), "--child", "--arm", arm, "--thread-id",
             str(thread_id), "--fixture", str(fixture), "--output", str(destination)],
            env=env, cwd=work, check=True, text=True,
            capture_output=True, timeout=150,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("isolated real bridge failed on time; not a null result") from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError("isolated real bridge failed:\n" + (exc.stderr or "")[-3000:]) from exc
    return json.loads(destination.read_text(encoding="utf-8"))


def _stable_projection(run: dict) -> dict:
    return {k: v for k, v in run.items() if k != "frame_count_disposable_only"}


def _world_trajectory(run: dict) -> list[dict]:
    return [
        {
            "question": row["question"],
            "host_answer": row["host_answer"],
            "observed_world_before": row["observed_world_before"],
            "investigator_action": row["investigator_action"],
            "resolved_action": row["resolved_action"],
            "observed_world_after": row["observed_world_after"],
            "world_action_status": row["world_action_status"],
        }
        for row in run["turns"]
    ]


def run_parent(fixture: Path, upstream: Path, output: Path) -> None:
    if not upstream.is_dir():
        raise ValueError("upstream code checkout missing")
    version = subprocess.check_output(
        ["git", "-C", str(upstream), "rev-parse", "HEAD"], text=True, timeout=10
    ).strip()
    if version != UPSTREAM_SHA:
        raise AssertionError("the checked external simulator does not match reviewed commit")
    raw = fixture.read_bytes()
    validate_fixture(json.loads(raw))

    result: dict[str, dict] = {}
    script = Path(__file__).resolve()
    with tempfile.TemporaryDirectory(prefix="g0-real-shadowchat-bridge-") as root:
        for arm_no, arm in enumerate(ARMS):
            first = _subprocess_arm(script, arm, fixture, Path(root) / f"{arm}_first", 32001 + 10*arm_no)
            second = _subprocess_arm(script, arm, fixture, Path(root) / f"{arm}_repeat", 32002 + 10*arm_no)
            if _stable_projection(first) != _stable_projection(second):
                raise AssertionError(f"non-reproducible canonical session in arm {arm}")
            result[arm] = first

    a, b = result["scripted_seed"], result["explicit_none"]
    if _world_trajectory(a) != _world_trajectory(b):
        raise AssertionError("the investigator-authored world trajectory was not equal across arms")
    if b["final_seed_state"] or any(x["true_seed_born_this_turn"] for x in b["turns"]):
        raise AssertionError("explicit NONE control unexpectedly created seeds")
    if not a["turns"][0]["true_seed_born_this_turn"]:
        raise AssertionError("scripted detector did not create real weightless seed on turn 0")
    if not a["turns"][1]["existing_seed_redetected_this_turn"]:
        raise AssertionError("true cross-turn recurrence was not recognized")
    if a["turns"][2]["detector_output_raw"] != "NONE":
        raise AssertionError("negative detector observation was lost")
    if not a["turns"][3]["true_seed_born_this_turn"]:
        raise AssertionError("later scripted candidate was not admitted")
    if a["seed_authority_uses"] != 0 or b["seed_authority_uses"] != 0:
        raise AssertionError("an unverified seed influenced a host reply")

    payload = {
        "schema": "g0-real-shadowchat-discoveryworld-bridge-audit-v0",
        "status": "model_free_product_pipeline_plus_real_world_mechanics_only",
        "source": "INVESTIGATOR_SCRIPTED_NO_LLM",
        "fixture_sha256": _sha(raw),
        "upstream_repo": "allenai/discoveryworld",
        "upstream_sha": version,
        "model_calls": 0,
        "embedding_hosted_calls": 0,
        "actual_world_turns_per_arm": TURN_COUNT,
        "replays_per_arm": 2,
        "same_world_observations_and_investigator_actions_in_both_arms": True,
        "used_true_canonical_detector_parser_intake_manager": True,
        "seed_maturation_or_novelty_assessed": False,
        "Q1_measured": False,
        "Q2_measured": False,
        "independent_semantic_review_completed": False,
        "g0_passed": False,
        "arm_definitions": {
            "scripted_seed": "real product live ShadowChatSession + scripted detector output; seed weight remains zero",
            "explicit_none": "real product live ShadowChatSession + canonical detector response NONE each turn",
        },
        "arms": result,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        "PASS: genuine product detector/intake/manager plus real DiscoveryWorld over 4 turns, "
        "replayed twice per arm; identical worlds; ZERO provider calls; NO Q1/Q2 result."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--thread-id", type=int, default=32001)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--upstream-dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.child:
        if args.arm is None:
            parser.error("--arm required for child")
        fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
        _child_arm(args.arm, fixture, args.thread_id, args.output.resolve())
    else:
        if args.upstream_dir is None:
            parser.error("--upstream-dir required for parent")
        run_parent(args.fixture.resolve(), args.upstream_dir.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
