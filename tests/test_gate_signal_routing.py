"""Tests for routing runtime effects through the Gate via typed signals (#12)."""

from __future__ import annotations

import ast
import pathlib

import numpy as np
import pytest

from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
    recurrence_signal,
)
from shadowseed.manager import AUTHORITY_FIELDS, SSLManager, SeedStatus


def fake_embedding(text: str) -> np.ndarray:
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vector = rng.standard_normal(16)
    return vector / np.linalg.norm(vector)


def _promote_via_recurrence(manager: SSLManager, seed_id: str) -> None:
    manager.seeds[seed_id].occurrence_count = 5
    for _ in range(3):
        manager.submit_signals(
            seed_id,
            [recurrence_signal(5, threshold=2)],
            policy_id="exploratory",
        )


def test_recurrence_promotes_without_touching_evidence_count():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a recurring atomic seed")
    _promote_via_recurrence(manager, seed_id)
    seed = manager.seeds[seed_id]
    assert seed.status is SeedStatus.PROMOTED
    assert seed.weight >= manager.promotion_threshold
    # The core anti-double-counting guarantee: recurrence never became evidence.
    assert seed.evidence_count == 0


def test_gate_event_records_recurrence_as_recurrence():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("another recurring seed")
    manager.seeds[seed_id].occurrence_count = 4
    event = manager.submit_signals(
        seed_id, [recurrence_signal(4, threshold=2)], policy_id="exploratory"
    )
    kinds = {s.kind for s in event.signals}
    assert SignalKind.RECURRENCE in kinds
    assert not any(s.is_external_evidence for s in event.signals)
    assert event.decision in {GateDecision.VALIDATED, GateDecision.PROMOTED}


def test_evidence_backed_policy_rejects_recurrence_only():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("evidence hungry seed")
    manager.seeds[seed_id].occurrence_count = 9
    event = manager.submit_signals(
        seed_id, [recurrence_signal(9, threshold=2)], policy_id="evidence_backed"
    )
    assert event.decision is GateDecision.BLOCKED
    assert manager.seeds[seed_id].weight == 0.0


def test_evidence_backed_policy_promotes_on_verified_evidence():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("well supported seed")
    for _ in range(3):
        manager.submit_signals(
            seed_id,
            [ValidationSignal(kind=SignalKind.SSOT, verified=True, strength=0.9)],
            policy_id="evidence_backed",
        )
    seed = manager.seeds[seed_id]
    assert seed.status is SeedStatus.PROMOTED
    # Verified external evidence does increment the evidence counter.
    assert seed.evidence_count >= 1


def test_contradiction_signal_routes_through_gate():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a seed to contradict")
    _promote_via_recurrence(manager, seed_id)
    event = manager.submit_signals(
        seed_id,
        [ValidationSignal(kind=SignalKind.CONTRADICTION, direction=SignalDirection.OPPOSE)],
        policy_id="exploratory",
    )
    assert event.decision is GateDecision.CONTRADICTED
    assert manager.seeds[seed_id].contradiction_score > 0.0
    assert manager.seeds[seed_id].status is SeedStatus.NEW


def test_expired_seed_cannot_regain_authority_via_signals():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("a seed that will expire")
    manager.seeds[seed_id].unsafe_set_authority(status=SeedStatus.EXPIRED)
    event = manager.submit_signals(
        seed_id, [recurrence_signal(9, threshold=2)], policy_id="exploratory"
    )
    assert event.decision is GateDecision.EXPIRED
    assert manager.seeds[seed_id].weight == 0.0


def test_boolean_gate_still_records_recurrence_not_evidence_in_event():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("legacy path seed")
    manager.seeds[seed_id].occurrence_count = 3
    manager.run_validation_gate(seed_id, external_evidence=True)
    event = manager.gate_events[-1]
    recurrence = [s for s in event.signals if s.kind is SignalKind.RECURRENCE]
    external = [s for s in event.signals if s.is_external_evidence]
    assert recurrence and not recurrence[0].is_external_evidence
    assert external, "external_evidence=True should be recorded as an external signal"


def test_probe_feedback_records_a_gate_event():
    manager = SSLManager(embedding_fn=fake_embedding)
    seed_id = manager.add_or_update_seed("probeable seed")
    manager.seeds[seed_id].unsafe_set_authority(weight=0.6, status=SeedStatus.PROMOTED)
    before = len(manager.gate_events)
    manager.apply_probe_feedback(seed_id, "penalty", probe_type="dialectic")
    assert len(manager.gate_events) == before + 1
    assert manager.gate_events[-1].signals[0].kind is SignalKind.PROBE


def test_no_direct_authority_mutation_in_non_benchmark_runtime():
    """Static guard: only manager.py and the explicit unsafe hook may write
    authority fields. No other runtime module (excluding benchmark harnesses and
    tests) assigns weight/status/evidence_count/contradiction_score directly."""

    src_root = pathlib.Path(__file__).resolve().parents[1] / "src" / "shadowseed"
    offenders: list[str] = []
    for path in src_root.rglob("*.py"):
        if "benchmark" in path.parts:
            continue
        if path.name == "manager.py":
            continue  # the single owner of the authority transition path
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, ast.AugAssign):
                targets = [node.target]
            for target in targets:
                if isinstance(target, ast.Attribute) and target.attr in AUTHORITY_FIELDS:
                    offenders.append(f"{path.relative_to(src_root)}:{target.lineno} .{target.attr}")
    assert not offenders, "direct authority writes outside the Gate: " + ", ".join(offenders)


def test_no_unsafe_authority_hooks_in_runtime():
    """The explicit unsafe escape hatches (unsafe_set_authority /
    unsafe_install_seed) exist for tests and benchmarks only. No runtime module
    may call them."""

    src_root = pathlib.Path(__file__).resolve().parents[1] / "src" / "shadowseed"
    unsafe_calls = {"unsafe_set_authority", "unsafe_install_seed"}
    offenders: list[str] = []
    for path in src_root.rglob("*.py"):
        if "benchmark" in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in unsafe_calls
            ):
                offenders.append(f"{path.relative_to(src_root)}:{node.lineno} .{node.func.attr}")
    assert not offenders, "unsafe authority hook used in runtime: " + ", ".join(offenders)
