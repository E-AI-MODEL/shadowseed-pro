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


class _AuthorityCallCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.scope: list[str] = []
        self.calls: dict[str, int] = {}

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.scope.append(node.name)
        self.generic_visit(node)
        self.scope.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "_set_authority":
            owner = ".".join(self.scope) or "<module>"
            self.calls[owner] = self.calls.get(owner, 0) + 1
        self.generic_visit(node)


def _repository_authority_calls(source_root: Path) -> dict[str, dict[str, int]]:
    locations: dict[str, dict[str, int]] = {}
    for path in sorted(source_root.rglob("*.py")):
        collector = _AuthorityCallCollector()
        collector.visit(ast.parse(path.read_text(encoding="utf-8")))
        if collector.calls:
            locations[path.relative_to(source_root).as_posix()] = dict(
                sorted(collector.calls.items())
            )
    return locations


def test_direct_authority_transitions_are_exactly_allowlisted() -> None:
    source_root = Path(__file__).resolve().parents[1] / "src/shadowseed"

    assert _repository_authority_calls(source_root) == {
        "gate/runtime_adapter.py": {
            "_submit_legacy_signals": 3,
            "apply_probe_feedback": 1,
            "resolve_contradiction": 1,
            "submit_signals": 2,
        },
        "intake.py": {
            "activate_existing_seed": 1,
        },
        "lifecycle.py": {
            "decay_traces": 2,
            "expire_vector_only_open_seeds": 1,
            "reactivate_by_text": 1,
        },
        "recurrence.py": {
            "refresh_cluster_representative": 1,
        },
    }
