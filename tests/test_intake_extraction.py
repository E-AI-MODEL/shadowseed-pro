"""Regression coverage for the intake extraction (#25 step 2c)."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from shadowseed import intake
from shadowseed.manager import SSLManager, SeedStatus


def _embedding(text: str) -> np.ndarray:
    lowered = text.lower()
    if "beta" in lowered:
        return np.array([0.0, 1.0, 0.0])
    if "gamma" in lowered:
        return np.array([0.0, 0.0, 1.0])
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


def test_manager_intake_methods_are_thin_facades() -> None:
    expected = {
        "_load_embedder": "load_embedder",
        "get_embedding": "get_embedding",
        "_normalize_embedding": "normalize_embedding",
        "is_atomic_seed": "is_atomic_seed",
        "normalize_detection_candidates": "normalize_detection_candidates",
        "ingest_detection_candidates": "ingest_detection_candidates",
        "_maybe_deduplicate_seed": "maybe_deduplicate_seed",
        "_activate_existing_seed": "activate_existing_seed",
        "_create_seed": "create_seed",
        "add_or_update_seed": "add_or_update_seed",
    }
    for method_name, target_name in expected.items():
        method = _manager_method(method_name)
        calls = [
            call
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "intake_engine"
        ]
        assert [call.func.attr for call in calls] == [target_name]


def test_atomicity_facade_matches_canonical_function() -> None:
    samples = [
        "missing causal nuance",
        "security ontbreekt",
        "oorzaken en gevolgen en context",
        "small atomic candidate",
    ]
    for sample in samples:
        assert SSLManager.is_atomic_seed(sample) is intake.is_atomic_seed(sample)


def test_dedup_reinforces_existing_seed_without_overwriting_identity() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("alpha omission")
    duplicate_id = manager.add_or_update_seed("alpha gap")

    assert duplicate_id == seed_id
    seed = manager.get_seed(seed_id)
    assert seed.occurrence_count == 2
    assert seed.status is SeedStatus.ACTIVE
    assert len(manager.seeds) == 1


def test_dedup_selects_most_similar_seed_not_first_inserted() -> None:
    vectors = {
        "first candidate": np.array([0.90, np.sqrt(0.19), 0.0]),
        "best candidate": np.array([0.99, np.sqrt(0.0199), 0.0]),
        "incoming candidate": np.array([1.0, 0.0, 0.0]),
    }
    manager = SSLManager(embedding_fn=lambda text: vectors[text])
    first_id = manager.add_or_update_seed("first candidate", deduplicate=False)
    best_id = manager.add_or_update_seed("best candidate", deduplicate=False)

    matched_id = manager.add_or_update_seed("incoming candidate")

    assert matched_id == best_id
    assert matched_id != first_id
    assert manager.seeds[best_id].occurrence_count == 2
    assert manager.seeds[first_id].occurrence_count == 1


def test_expired_seed_is_not_revived_by_deduplication() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    first_id = manager.add_or_update_seed("alpha omission")
    manager.get_seed(first_id).unsafe_set_authority(status=SeedStatus.EXPIRED)

    second_id = manager.add_or_update_seed("alpha gap")

    assert second_id != first_id
    assert manager.get_seed(first_id).status is SeedStatus.EXPIRED
    assert len(manager.seeds) == 2


def test_ingest_preserves_batch_duplicate_reporting() -> None:
    manager = SSLManager(embedding_fn=_embedding)

    result = manager.ingest_detection_candidates(
        ["alpha omission", "alpha omission", "beta omission"],
        expand_short_fragments=False,
        split_broad=False,
    )

    assert result["input_count"] == 3
    # Candidate normalization preserves the historical terminal punctuation.
    assert [item["text"] for item in result["accepted"]] == [
        "alpha omission.",
        "beta omission.",
    ]
    assert result["rejected"] == [
        {"text": "alpha omission.", "reason": "duplicate"}
    ]


def test_embedding_normalization_stays_identical() -> None:
    vector = np.array([3.0, 4.0, 0.0])
    manager = SSLManager(embedding_fn=lambda _text: vector.copy())

    assert np.allclose(manager.get_embedding("candidate"), np.array([0.6, 0.8, 0.0]))
    assert np.array_equal(
        manager._normalize_embedding(np.zeros(3)),
        intake.normalize_embedding(np.zeros(3)),
    )


def test_get_embedding_keeps_the_historical_normalization_override_point() -> None:
    class HookedManager(SSLManager):
        @staticmethod
        def _normalize_embedding(_embedding: np.ndarray) -> np.ndarray:
            return np.array([9.0, 8.0, 7.0])

    manager = HookedManager(embedding_fn=lambda _text: np.array([1.0, 2.0, 3.0]))

    assert np.array_equal(
        manager.get_embedding("candidate"), np.array([9.0, 8.0, 7.0])
    )


def test_ingest_keeps_normalization_and_add_override_points() -> None:
    class HookedManager(SSLManager):
        def normalize_detection_candidates(
            self,
            candidates,
            expand_short_fragments: bool = True,
            split_broad: bool = True,
        ) -> list[str]:
            del candidates, expand_short_fragments, split_broad
            return ["hooked candidate"]

        def add_or_update_seed(self, text, **_kwargs) -> str:
            assert text == "hooked candidate"
            return "hooked-id"

    manager = HookedManager(embedding_fn=_embedding)

    result = manager.ingest_detection_candidates(["raw candidate"])

    assert result["accepted"] == [
        {"seed_id": "hooked-id", "text": "hooked candidate"}
    ]


def test_add_or_update_keeps_internal_manager_override_points() -> None:
    class HookedManager(SSLManager):
        @staticmethod
        def is_atomic_seed(_text: str, max_seed_words: int | None = None) -> bool:
            assert max_seed_words is not None
            return True

        def get_embedding(self, _text: str) -> np.ndarray:
            return np.array([1.0, 0.0, 0.0])

        def _maybe_deduplicate_seed(self, _embedding: np.ndarray):
            return "existing-id", 0.99

        def _activate_existing_seed(self, seed_id: str, similarity: float) -> str:
            assert (seed_id, similarity) == ("existing-id", 0.99)
            return "hooked-result"

    manager = HookedManager(embedding_fn=_embedding)

    assert manager.add_or_update_seed("candidate") == "hooked-result"
