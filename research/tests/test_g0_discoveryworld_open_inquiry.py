"""Pure contract checks for researcher-authored, model-free open-inquiry calibration.

These tests run without DiscoveryWorld, an LLM, credentials, a network,
independent human assessment or any Shadowseed product-state mutation.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "g0_discoveryworld_open_inquiry.py"
)
SPEC = importlib.util.spec_from_file_location("g0_open_inquiry_calibration", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _observation(*, x: int = 16, facing: str = "south", tick: int = 1) -> dict:
    return {
        "position": [x, 12],
        "facing": facing,
        "legal_move_directions": ["east"],
        "world_step": tick,
    }


def test_tick_alone_is_not_information_or_a_change_of_agent_state() -> None:
    assert MODULE.physical_projection(_observation(tick=1)) == MODULE.physical_projection(
        _observation(tick=2)
    )
    assert MODULE.action_status(
        "executable_tool_grammar",
        {"success": True},
        _observation(tick=1),
        _observation(tick=2),
    ) == "accepted_no_observable_state_difference"


def test_upstream_action_success_and_observable_difference_are_separate() -> None:
    assert MODULE.action_status(
        "executable_tool_grammar",
        {"success": True},
        _observation(),
        _observation(facing="north", tick=2),
    ) == "accepted_observable_state_difference"
    assert MODULE.action_status(
        "executable_tool_grammar",
        {"success": False},
        _observation(),
        _observation(tick=2),
    ) == "rejected_by_upstream"


def test_a_free_natural_language_question_is_not_called_invalid_or_false() -> None:
    assert MODULE.resolve_action(None, _observation(), {"MOVE_DIRECTION": {}}) == (
        None,
        "natural_language_not_automatically_executable",
    )
    assert MODULE.action_status(
        "natural_language_not_automatically_executable",
        None,
        _observation(),
        _observation(tick=2),
    ) == "not_testable_by_this_evaluator"


def test_unknown_action_and_malformed_request_remain_unassessable() -> None:
    before = _observation()
    supported = {"MOVE_DIRECTION": {}}
    for payload in (
        "not a tool action",
        ["MOVE_DIRECTION", "north"],
        {"action": "INFER_NEW_CAUSAL_LAW"},
        {"action": "MOVE_DIRECTION", "arg1": {"injection": "not a scalar"}},
        {"action": "MOVE_DIRECTION", "arg1": "$unknown_hint"},
    ):
        request, reason = MODULE.resolve_action(payload, before, supported)
        assert request is None
        assert reason == "unsupported_tool_request"


def test_runtime_placeholders_are_grounded_in_agent_visible_state() -> None:
    before = _observation()
    known = {"MOVE_DIRECTION": {}, "ROTATE_DIRECTION": {}}
    move, reason = MODULE.resolve_action(
        {"action": "MOVE_DIRECTION", "arg1": "$first_legal_move"}, before, known
    )
    assert reason == "executable_tool_grammar"
    assert move == {"action": "MOVE_DIRECTION", "arg1": "east"}

    rotate, reason = MODULE.resolve_action(
        {"action": "ROTATE_DIRECTION", "arg1": "$alternate_facing"}, before, known
    )
    assert reason == "executable_tool_grammar"
    assert rotate is not None and rotate["arg1"] != before["facing"]

    no_move, reason = MODULE.resolve_action(
        {"action": "MOVE_DIRECTION", "arg1": "$first_legal_move"},
        {**before, "legal_move_directions": []},
        known,
    )
    assert no_move is None
    assert reason == "no_legal_move_in_this_start_state"


def test_public_observation_excludes_oracle_scores_and_hidden_world() -> None:
    response = {
        "errors": [],
        "ui": {
            "agentLocation": {
                "x": 16,
                "y": 12,
                "faceDirection": "south",
                "directions_you_can_move": ["east"],
            },
            "world_steps": 1,
            "taskProgress": [{"secret_answer": "NOT_FOR_MODEL"}],
            "worldHistory": [{"oracle": True}],
        },
        "vision": {"base64_no_grid": "DATA_NOT_FOR_ARTIFACT"},
    }
    got = MODULE.public_projection(response)
    assert got == _observation()
    serialized = MODULE.canonical_json(got)
    assert "taskProgress" not in serialized
    assert "worldHistory" not in serialized
    assert "DATA_NOT_FOR_ARTIFACT" not in serialized
    assert "NOT_FOR_MODEL" not in serialized


def test_public_calibration_manifest_is_not_a_sealed_model_originated_set() -> None:
    fixture = (
        Path(__file__).resolve().parents[1]
        / "fixtures"
        / "g0_discoveryworld_open_inquiry_calibration_v0.json"
    )
    contents = json.loads(fixture.read_text(encoding="utf-8"))
    assert contents["schema"] == "g0-open-inquiry-calibration-v0"
    assert contents["source"] == "researcher_authored_public_calibration"
    assert len(contents["cases"]) == 7
    assert any(c["tool_request"] is None for c in contents["cases"])
    assert any(c["tool_request"]["action"] == "TEST_HIDDEN_CAUSAL_RELATION"
               for c in contents["cases"] if c["tool_request"] is not None)
