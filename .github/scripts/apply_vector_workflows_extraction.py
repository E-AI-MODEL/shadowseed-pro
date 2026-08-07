from __future__ import annotations

import ast
from pathlib import Path


VECTOR_SOURCE = r'''"""Vector search, external feedback, and constellation workflows.

This module owns the non-authority vector orchestration that used to live in
:mod:`shadowseed.manager`: uncertain-region search, external-feedback routing,
and in-memory constellation construction. Probe-feedback authority decisions
remain in :mod:`shadowseed.gate.runtime_adapter`.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from shadowseed.gate.signals import (
    SignalDirection,
    SignalKind,
    ValidationSignal,
)
from shadowseed.models import Constellation, SeedStatus, ShadowSeed


def find_uncertain_region(
    manager: Any,
    text: str,
    threshold: float = 0.85,
    include_promoted: bool = False,
) -> list[dict[str, Any]]:
    """Return vector-near weightless seeds from the configured vector store."""

    if manager.vector_constellation is None:
        return []
    query_emb = manager.get_embedding(text)
    matches = manager.vector_constellation.search_similar_seeds(
        query_emb,
        threshold=threshold,
    )
    uncertain: list[dict[str, Any]] = []
    for seed_id, score, metadata in matches:
        seed = manager._seeds.get(seed_id)
        if seed is None:
            continue
        if not include_promoted and seed.status == SeedStatus.PROMOTED:
            continue
        if seed.weight == 0.0:
            uncertain.append(
                {
                    "seed_id": seed_id,
                    "similarity": score,
                    "text": seed.text,
                    "status": seed.status.value,
                    "weight": seed.weight,
                    "metadata": metadata,
                }
            )
    return uncertain


def apply_external_feedback(
    manager: Any,
    feedback_text: str,
    context: str,
    positive: bool = True,
    threshold: float = 0.75,
) -> list[dict[str, Any]]:
    """Route vector-matched external feedback through the manager Gate facade."""

    if manager.vector_constellation is None:
        return []
    feedback_emb = manager.get_embedding(f"FEEDBACK: {feedback_text} ON: {context}")
    matches = manager.vector_constellation.search_similar_seeds(
        feedback_emb,
        threshold=threshold,
    )
    updates: list[dict[str, Any]] = []
    for seed_id, score, _metadata in matches:
        if seed_id not in manager._seeds:
            continue
        if positive:
            result = manager.run_validation_gate(
                seed_id,
                external_evidence=True,
                signals=[
                    ValidationSignal(
                        kind=SignalKind.HUMAN_FEEDBACK,
                        direction=SignalDirection.SUPPORT,
                        strength=float(score),
                        source_ref=context,
                        verified=True,
                        reason="external feedback (positive)",
                    )
                ],
            )
        else:
            result = manager.run_validation_gate(
                seed_id,
                contradiction=True,
                signals=[
                    ValidationSignal(
                        kind=SignalKind.CONTRADICTION,
                        direction=SignalDirection.OPPOSE,
                        strength=float(score),
                        source_ref=context,
                        reason="external feedback (negative)",
                    )
                ],
            )
        manager.vector_constellation.record_feedback(
            seed_id=seed_id,
            feedback=feedback_text,
            is_correction=positive,
            similarity=score,
        )
        updates.append(
            {
                "seed_id": seed_id,
                "similarity": score,
                "gate_result": result,
                "seed": manager._seeds[seed_id].to_dict(),
            }
        )
    return updates


def constellation_label(cluster: list[ShadowSeed]) -> str:
    """Build the historical human-readable label for one cluster."""

    for seed in cluster:
        for keyword in seed.trigger_keywords:
            clean = keyword.strip()
            if clean:
                return f"Cluster around {clean}."
    seed_text = cluster[0].text.strip().rstrip(".")
    return f"Cluster around {seed_text[:48]}."


def find_constellations(
    manager: Any,
    threshold: float = 0.70,
    min_members: int = 3,
) -> list[Constellation]:
    """Build deterministic in-memory constellations from promoted seeds."""

    promoted = [
        seed
        for seed in manager._seeds.values()
        if seed.status == SeedStatus.PROMOTED
    ]
    constellations: list[Constellation] = []
    seen: set[tuple[str, ...]] = set()

    for index, seed in enumerate(promoted):
        cluster = [seed]
        for other in promoted[index + 1 :]:
            similarity = float(np.dot(seed.embedding, other.embedding))
            if similarity >= threshold:
                cluster.append(other)

        if len(cluster) >= min_members:
            member_ids = tuple(sorted(item.id for item in cluster))
            if member_ids in seen:
                continue
            seen.add(member_ids)
            centroid = np.mean([item.embedding for item in cluster], axis=0)
            constellations.append(
                Constellation(
                    members=list(member_ids),
                    centroid=centroid.tolist(),
                    combined_weight=float(
                        np.mean([item.weight for item in cluster])
                    ),
                    id=f"const_{len(constellations) + 1:03d}",
                    label=manager._constellation_label(cluster),
                    probe_type="retrieval" if len(cluster) >= 5 else "socratic",
                )
            )

    return constellations


__all__ = [
    "apply_external_feedback",
    "constellation_label",
    "find_constellations",
    "find_uncertain_region",
]
'''


MANAGER_REPLACEMENTS = {
    "find_uncertain_region": '''    def find_uncertain_region(
        self,
        text: str,
        threshold: float = 0.85,
        include_promoted: bool = False,
    ) -> list[dict[str, Any]]:
        """Compatibility facade for vector-near uncertain-region search."""

        return vector_workflows.find_uncertain_region(
            self,
            text,
            threshold=threshold,
            include_promoted=include_promoted,
        )
''',
    "apply_external_feedback": '''    def apply_external_feedback(
        self,
        feedback_text: str,
        context: str,
        positive: bool = True,
        threshold: float = 0.75,
    ) -> list[dict[str, Any]]:
        """Compatibility facade for vector-matched external feedback."""

        return vector_workflows.apply_external_feedback(
            self,
            feedback_text,
            context,
            positive=positive,
            threshold=threshold,
        )
''',
    "_constellation_label": '''    @staticmethod
    def _constellation_label(cluster: list[ShadowSeed]) -> str:
        """Compatibility facade for historical constellation labels."""

        return vector_workflows.constellation_label(cluster)
''',
    "find_constellations": '''    def find_constellations(
        self, threshold: float = 0.70, min_members: int = 3
    ) -> list[Constellation]:
        """Compatibility facade for in-memory constellation construction."""

        return vector_workflows.find_constellations(
            self,
            threshold=threshold,
            min_members=min_members,
        )
''',
}


VECTOR_TEST = r'''"""Regression coverage for vector workflow extraction (#25 step 2e)."""

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
    )

    captured_id, kwargs = manager.captured_gate
    assert captured_id == seed_id
    assert kwargs["external_evidence"] is True
    signal = kwargs["signals"][0]
    assert signal.kind is SignalKind.HUMAN_FEEDBACK
    assert signal.direction is SignalDirection.SUPPORT
    assert signal.verified is True
    assert signal.source_ref == "source-A"
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
'''


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one anchor, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    Path("src/shadowseed/vector_workflows.py").write_text(
        VECTOR_SOURCE,
        encoding="utf-8",
    )

    manager_path = Path("src/shadowseed/manager.py")
    manager_text = manager_path.read_text(encoding="utf-8")
    import_anchor = "from shadowseed import lifecycle as lifecycle_engine\n"
    if manager_text.count(import_anchor) != 1:
        raise SystemExit("manager vector import anchor not found exactly once")
    manager_text = manager_text.replace(
        import_anchor,
        import_anchor + "from shadowseed import vector_workflows\n",
        1,
    )

    tree = ast.parse(manager_text)
    manager_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SSLManager"
    )
    methods = {
        node.name: node
        for node in manager_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    lines = manager_text.splitlines()
    spans: list[tuple[int, int, str]] = []
    for name, source in MANAGER_REPLACEMENTS.items():
        node = methods.get(name)
        if node is None:
            raise SystemExit(f"manager method {name} not found")
        decorator_lines = [item.lineno for item in node.decorator_list]
        start = min([node.lineno, *decorator_lines]) - 1
        spans.append((start, node.end_lineno, source.rstrip()))
    for start, end, source in sorted(spans, reverse=True):
        lines[start:end] = source.splitlines()
    manager_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    Path("tests/test_vector_workflows_extraction.py").write_text(
        VECTOR_TEST,
        encoding="utf-8",
    )

    replace_once(
        Path("README.md"),
        "| [`shadowseed.lifecycle`](src/shadowseed/lifecycle.py) | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |\n",
        "| [`shadowseed.lifecycle`](src/shadowseed/lifecycle.py) | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |\n"
        "| [`shadowseed.vector_workflows`](src/shadowseed/vector_workflows.py) | Uncertain-region search, external-feedback routing, and in-memory constellation construction |\n",
    )
    replace_once(
        Path("docs/architecture/overview.md"),
        "| `shadowseed.lifecycle` | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |\n",
        "| `shadowseed.lifecycle` | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |\n"
        "| `shadowseed.vector_workflows` | Uncertain-region search, external-feedback routing, and in-memory constellation construction |\n",
    )

    Path(".github/workflows/apply-vector-workflows-extraction.yml").unlink()
    Path(".github/scripts/apply_vector_workflows_extraction.py").unlink()


if __name__ == "__main__":
    main()
