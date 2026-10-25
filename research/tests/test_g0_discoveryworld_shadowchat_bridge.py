"""Model-free checks around the real ShadowChatSession/DiscoveryWorld bridge.

All questions and detector texts are investigator-authored. No external
simulator is imported by these tests and no product authority is modified.
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
SCRIPT = SCRIPT_DIR / "g0_discoveryworld_shadowchat_bridge.py"
SPEC = importlib.util.spec_from_file_location("g0_real_shadowchat_bridge", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
BRIDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BRIDGE)

FIXTURE = Path("research/fixtures/g0_discoveryworld_shadowchat_bridge_v0.json")


def data() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_source_and_full_turn_contract_must_be_explicitly_scripted() -> None:
    original = data()
    assert len(BRIDGE.validate_fixture(original)) == 4
    altered = copy.deepcopy(original)
    altered["source"] = "LLM invented and verified this"
    with pytest.raises(ValueError, match="scripted"):
        BRIDGE.validate_fixture(altered)
    altered = copy.deepcopy(original)
    altered["turns"].pop()
    with pytest.raises(ValueError, match="four distinct"):
        BRIDGE.validate_fixture(altered)
    altered = copy.deepcopy(original)
    altered["turns"][2]["detector_output"] = "1. An interesting idea."
    with pytest.raises(ValueError, match="negative/new"):
        BRIDGE.validate_fixture(altered)


def test_fixture_cannot_expand_world_tools_or_hide_an_unbounded_action() -> None:
    original = data()
    altered = copy.deepcopy(original)
    altered["turns"][0]["world_action"] = {
        "action": "EXEC_PYTHON", "arg1": "print(1)"
    }
    with pytest.raises(ValueError, match="approved"):
        BRIDGE.validate_fixture(altered)
    altered = copy.deepcopy(original)
    altered["turns"][0]["world_action"] = {
        "action": "MOVE_DIRECTION", "arg1": "north", "secret": "hidden"
    }
    with pytest.raises(ValueError, match="approved"):
        BRIDGE.validate_fixture(altered)


def test_host_answer_is_only_agent_visible_projection() -> None:
    visible = {
        "position": [16, 12],
        "facing": "south",
        "legal_move_directions": ["east"],
        "world_step": 1,
        "world_history": [{"secret_oracle": "NOT_VISIBLE"}],
    }
    answer = BRIDGE._host_answer_from_visible_state(visible)
    assert "(16, 12)" in answer
    assert "south" in answer
    assert "east" in answer
    assert "NOT_VISIBLE" not in answer
    assert "world_history" not in answer
    assert "world_step" not in answer


def test_world_trajectory_compare_intentionally_excludes_seed_memory() -> None:
    view = {"position": [16, 12], "facing": "south", "world_step": 1}
    turn = {
        "question": "What is now visible?",
        "host_answer": "Facing south",
        "observed_world_before": view,
        "investigator_action": {"action": "ROTATE_DIRECTION", "arg1": "north"},
        "resolved_action": {"action": "ROTATE_DIRECTION", "arg1": "north"},
        "observed_world_after": {**view, "facing": "north"},
        "world_action_status": "accepted_observable_state_difference",
        "true_seed_born_this_turn": ["What could have changed?"],
    }
    changed = {**turn, "true_seed_born_this_turn": []}
    assert BRIDGE._world_trajectory({"turns": [turn]}) == BRIDGE._world_trajectory(
        {"turns": [changed]}
    )
    assert changed != turn


def test_detector_fixture_contains_actual_recurrence_and_none_observation() -> None:
    turns = BRIDGE.validate_fixture(data())
    assert turns[0]["detector_output"].startswith("1.")
    assert turns[1]["detector_output"] == turns[0]["detector_output"]
    assert turns[2]["detector_output"] == "NONE"
    assert turns[3]["detector_output"].startswith("1.")
    assert turns[3]["detector_output"] != turns[0]["detector_output"]
    assert turns[3]["world_action"] is None
