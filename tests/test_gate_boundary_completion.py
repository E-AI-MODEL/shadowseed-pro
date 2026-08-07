"""Regression guards for the sole runtime authority boundary (#28)."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import SignalDirection, SignalKind, ValidationSignal
from shadowseed.manager import SSLManager, SeedStatus


def _embedding(_text: str) -> np.ndarray:
    return np.array([1.0, 0.0, 0.0])


def _manager_method(name: str) -> ast.FunctionDef:
    # Pin the facade shape as well as behavior so authority logic cannot drift
    # back into manager.py while still producing superficially correct events.
    path = Path(__file__).resolve().parents[1] / "src/shadowseed/manager.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    manager = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SSLManager"
    )
    return next(
        node
        for node in manager.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def _called_attributes(node: ast.AST) -> set[str]:
    return {
        call.func.attr
        for call in ast.walk(node)
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
    }


def test_probe_and_resolution_manager_methods_are_gate_facades() -> None:
    probe_calls = _called_attributes(_manager_method("apply_probe_feedback"))
    resolution_calls = _called_attributes(_manager_method("resolve_contradiction"))

    assert "apply_probe_feedback" in probe_calls
    assert "resolve_contradiction" in resolution_calls
    assert "_set_authority" not in probe_calls
    assert "_record_gate_event" not in probe_calls
    assert "_set_authority" not in resolution_calls
    assert "_record_gate_event" not in resolution_calls


def test_probe_feedback_preserves_behavior_and_records_one_typed_gate_event() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("bounded probe candidate")
    seed = manager.seeds[seed_id]
    seed.unsafe_set_authority(weight=0.4, status=SeedStatus.ACTIVE)
    before_events = len(manager.gate_events)

    result = manager.apply_probe_feedback(seed_id, "reward", probe_type="retrieval")

    assert not result.skipped
    assert result.status_after == SeedStatus.ACTIVE.value
    assert len(manager.gate_events) == before_events + 1
    event = manager.gate_events[-1]
    assert event.policy_id == "probe_feedback"
    assert event.decision in {GateDecision.VALIDATED, GateDecision.NO_CHANGE}
    assert len(event.signals) == 1
    assert event.signals[0].kind is SignalKind.PROBE


def test_formal_resolution_unblocks_without_restoring_authority() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("contradicted candidate")
    seed = manager.seeds[seed_id]
    seed.unsafe_set_authority(weight=0.6, status=SeedStatus.PROMOTED)
    manager.submit_signals(
        seed_id,
        [
            ValidationSignal(
                kind=SignalKind.CONTRADICTION,
                direction=SignalDirection.OPPOSE,
                strength=1.0,
                reason="test contradiction",
            )
        ],
        policy_id="exploratory",
    )
    weight_before_resolution = seed.weight
    before_events = len(manager.gate_events)

    event = manager.resolve_contradiction(seed_id, basis="verified correction")

    assert len(manager.gate_events) == before_events + 1
    assert event is manager.gate_events[-1]
    assert event.decision is GateDecision.CONTRADICTION_RESOLVED
    assert event.policy_id == "contradiction_resolution"
    assert event.signals[0].kind is SignalKind.CONTRADICTION_RESOLUTION
    assert not manager.is_blocking_contradiction(seed_id)
    assert seed.contradiction_score == 0.0
    assert seed.weight == weight_before_resolution
    assert seed.status is not SeedStatus.PROMOTED


def _authority_calls(path: Path, class_name: str | None = None) -> dict[str, int]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    if class_name is None:
        definitions = [
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
    else:
        owner = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        )
        definitions = [
            node
            for node in owner.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]

    calls: dict[str, int] = {}
    for definition in definitions:
        count = sum(
            1
            for call in ast.walk(definition)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and call.func.attr == "_set_authority"
        )
        if count:
            calls[definition.name] = count
    return calls


def test_direct_authority_transitions_are_exactly_allowlisted() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src/shadowseed"

    assert _authority_calls(source_root / "manager.py", "SSLManager") == {}
    assert _authority_calls(source_root / "intake.py") == {
        "activate_existing_seed": 1,
    }
    assert _authority_calls(source_root / "lifecycle.py") == {
        "decay_traces": 2,
        "reactivate_by_text": 1,
        "expire_vector_only_open_seeds": 1,
    }

