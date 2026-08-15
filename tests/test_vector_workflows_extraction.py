"""Regression coverage for vector workflow extraction (#25 step 2e)."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from shadowseed.gate.signals import SignalDirection, SignalKind
from shadowseed.manager import SSLManager, SeedStatus, ShadowSeed


def _embedding(text: str) -> np.ndarray:
    lowered = text.lower()
    if "beta" in lowered:
        return np.array([0.0, 1.0, 0.0])
    if "gamma" in lowered:
        return np.array([0.8, 0.6, 0.0])
    return np.array([1.0, 0.0, 0.0])


def _manager_method(name: str) -> ast.FunctionDef:
    path = Path(__file__).resolve().parents[1] / "src/shadowseed/manager.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    manager = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SSLManager"
    )
    return next(
        node
        for node in manager.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )


def test_manager_vector_methods_are_thin_facades() -> None:
    expected = {
        "find_uncertain_region": "find_uncertain_region",
        "apply_external_feedback": "apply_external_feedback",
        "_constellation_label": "constellation_label",
        "find_constellations": "find_constellations",
    }
    for method_name, target_name in expected.items():
        method = _manager_method(method_name)
        calls = [
            call
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "vector_workflows"
        ]
        assert [call.func.attr for call in calls] == [target_name]


class FakeVectorConstellation:
    def __init__(self, matches=None) -> None:
        self.matches = list(matches or [])
        self.search_calls: list[tuple[np.ndarray, float]] = []
        self.feedback_calls: list[dict[str, object]] = []

    def sync_seed(self, _seed) -> None:
        return None

    def search_similar_seeds(self, embedding, threshold: float):
        self.search_calls.append((np.asarray(embedding), threshold))
        return list(self.matches)

    def record_feedback(self, **kwargs) -> None:
        self.feedback_calls.append(kwargs)


def test_uncertain_region_filters_authority_and_promoted_by_default() -> None:
    vector = FakeVectorConstellation()
    manager = SSLManager(embedding_fn=_embedding, vector_constellation=vector)
    active_id = manager.add_or_update_seed("alpha candidate", deduplicate=False)
    promoted_id = manager.add_or_update_seed("beta candidate", deduplicate=False)
    weighted_id = manager.add_or_update_seed("gamma candidate", deduplicate=False)
    manager.get_seed(active_id).unsafe_set_authority(status=SeedStatus.ACTIVE)
    manager.get_seed(promoted_id).unsafe_set_authority(status=SeedStatus.PROMOTED)
    manager.get_seed(weighted_id).unsafe_set_authority(
        status=SeedStatus.ACTIVE,
        weight=0.4,
    )
    vector.matches = [
        (active_id, 0.96, {"source": "active"}),
        (promoted_id, 0.95, {"source": "promoted"}),
        (weighted_id, 0.94, {"source": "weighted"}),
        ("missing", 0.93, {}),
    ]

    result = manager.find_uncertain_region("alpha query", threshold=0.9)

    assert result == [
        {
            "seed_id": active_id,
            "similarity": 0.96,
            "text": "alpha candidate",
            "status": SeedStatus.ACTIVE.value,
            "weight": 0.0,
            "metadata": {"source": "active"},
        }
    ]
    assert vector.search_calls[0][1] == 0.9

    promoted = manager.find_uncertain_region(
        "alpha query",
        threshold=0.9,
        include_promoted=True,
    )
    assert [item["seed_id"] for item in promoted] == [active_id, promoted_id]


def test_positive_external_feedback_uses_verified_support_signal() -> None:
    vector = FakeVectorConstellation()

    class HookedManager(SSLManager):
        def run_validation_gate(self, seed_id: str, **kwargs):
            self.captured_gate = (seed_id, kwargs)
            return True

    manager = HookedManager(embedding_fn=_embedding, vector_constellation=vector)
    seed_id = manager.add_or_update_seed("alpha candidate", deduplicate=False)
    vector.matches = [(seed_id, 0.91, {"ignored": True})]

    updates = manager.apply_external_feedback(
        "confirmed",
        context="source-A",
        positive=True,
        threshold=0.8,
        source_ref="reviewer-A::confirmation-1",
    )

    captured_id, kwargs = manager.captured_gate
    assert captured_id == seed_id
    assert kwargs["external_evidence"] is True
    signal = kwargs["signals"][0]
    assert signal.kind is SignalKind.HUMAN_FEEDBACK
    assert signal.direction is SignalDirection.SUPPORT
    assert signal.verified is True
    assert signal.source_ref == "reviewer-A::confirmation-1"
    assert updates[0]["gate_result"] is True
    assert vector.feedback_calls == [
        {
            "seed_id": seed_id,
            "feedback": "confirmed",
            "is_correction": True,
            "similarity": 0.91,
        }
    ]


def test_negative_external_feedback_uses_opposing_contradiction() -> None:
    vector = FakeVectorConstellation()

    class HookedManager(SSLManager):
        def run_validation_gate(self, seed_id: str, **kwargs):
            self.captured_gate = (seed_id, kwargs)
            return False

    manager = HookedManager(embedding_fn=_embedding, vector_constellation=vector)
    seed_id = manager.add_or_update_seed("alpha candidate", deduplicate=False)
    vector.matches = [(seed_id, 0.88, {})]

    updates = manager.apply_external_feedback(
        "refuted",
        context="source-B",
        positive=False,
    )

    _, kwargs = manager.captured_gate
    assert kwargs["contradiction"] is True
    signal = kwargs["signals"][0]
    assert signal.kind is SignalKind.CONTRADICTION
    assert signal.direction is SignalDirection.OPPOSE
    assert signal.verified is False
    assert updates[0]["gate_result"] is False
    assert vector.feedback_calls[0]["is_correction"] is False


def _install_promoted(
    manager: SSLManager,
    seed_id: str,
    text: str,
    embedding: np.ndarray,
    weight: float,
    keywords=None,
) -> None:
    seed = ShadowSeed(
        id=seed_id,
        text=text,
        embedding=embedding,
        trigger_keywords=list(keywords or []),
    )
    seed.unsafe_set_authority(status=SeedStatus.PROMOTED, weight=weight)
    manager.unsafe_install_seed(seed)


def test_constellation_shape_and_label_are_preserved() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    _install_promoted(
        manager,
        "ss_003",
        "third seed",
        np.array([0.9, 0.1, 0.0]),
        0.9,
    )
    _install_promoted(
        manager,
        "ss_001",
        "first seed",
        np.array([1.0, 0.0, 0.0]),
        0.6,
        keywords=["topic"],
    )
    _install_promoted(
        manager,
        "ss_002",
        "second seed",
        np.array([0.8, 0.2, 0.0]),
        0.3,
    )

    result = manager.find_constellations(threshold=0.7, min_members=3)

    assert len(result) == 1
    item = result[0]
    assert item.id == "const_001"
    assert item.members == ["ss_001", "ss_002", "ss_003"]
    assert np.allclose(item.centroid, [0.9, 0.1, 0.0])
    assert item.combined_weight == 0.6
    assert item.label == "Cluster around topic."
    assert item.probe_type == "socratic"


def test_constellation_builder_keeps_label_override_point() -> None:
    class HookedManager(SSLManager):
        @staticmethod
        def _constellation_label(_cluster) -> str:
            return "hooked-label"

    manager = HookedManager(embedding_fn=_embedding)
    for index in range(3):
        _install_promoted(
            manager,
            f"ss_{index + 1:03d}",
            f"seed {index}",
            np.array([1.0, 0.0, 0.0]),
            0.5,
        )

    assert manager.find_constellations()[0].label == "hooked-label"


def test_probe_feedback_stays_on_the_gate_runtime_boundary() -> None:
    method = _manager_method("apply_probe_feedback")
    calls = [
        call.func.attr
        for call in ast.walk(method)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "gate_engine"
    ]
    assert calls == ["apply_probe_feedback"]
