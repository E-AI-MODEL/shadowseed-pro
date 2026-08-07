"""Regression coverage for lifecycle extraction (#25 step 2d)."""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np

from shadowseed.manager import SSLManager, SeedStatus


def _embedding(text: str) -> np.ndarray:
    if "needle" in text.lower():
        return np.array([0.0, 1.0, 0.0])
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


def test_manager_lifecycle_methods_are_thin_facades() -> None:
    expected = {
        "_status_after_decay": "status_after_decay",
        "decay_traces": "decay_traces",
        "reactivate_by_text": "reactivate_by_text",
        "scan_trtl_triggers": "scan_trtl_triggers",
        "expire_vector_only_open_seeds": "expire_vector_only_open_seeds",
    }
    for method_name, target_name in expected.items():
        method = _manager_method(method_name)
        calls = [
            call
            for call in ast.walk(method)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "lifecycle_engine"
        ]
        assert [call.func.attr for call in calls] == [target_name]


def test_dormant_ttl_expiry_is_terminal_and_clears_weight() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    manager.dormant_ttl_turns = 1
    seed_id = manager.add_or_update_seed("alpha candidate")
    seed = manager.get_seed(seed_id)
    seed.unsafe_set_authority(weight=0.6, status=SeedStatus.DORMANT)
    seed.trace = 0.01

    manager.decay_traces(turns_passed=1)

    assert seed.status is SeedStatus.EXPIRED
    assert seed.weight == 0.0
    assert seed.turns_dormant == 1
    assert [event.event_type for event in manager.event_log[-2:]] == [
        "trace_decayed",
        "expired",
    ]


def test_expired_seed_is_skipped_by_decay() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("alpha candidate")
    seed = manager.get_seed(seed_id)
    seed.unsafe_set_authority(status=SeedStatus.EXPIRED)
    seed.trace = 0.4
    before_events = len(manager.event_log)

    manager.decay_traces(turns_passed=3)

    assert seed.trace == 0.4
    assert len(manager.event_log) == before_events


def test_decay_uses_the_historical_status_override_point() -> None:
    class HookedManager(SSLManager):
        def _status_after_decay(self, _seed):
            return SeedStatus.PROMOTED

    manager = HookedManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("alpha candidate")

    manager.decay_traces()

    assert manager.get_seed(seed_id).status is SeedStatus.PROMOTED


def test_keyword_reactivation_restores_new_without_authority_weight() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed(
        "alpha candidate",
        trigger_keywords=["needle"],
    )
    seed = manager.get_seed(seed_id)
    seed.unsafe_set_authority(weight=0.0, status=SeedStatus.DORMANT)
    seed.turns_dormant = 4
    seed.trace = 0.1

    reactivated = manager.reactivate_by_text("needle appears", threshold=0.99)

    assert reactivated == [seed_id]
    assert seed.status is SeedStatus.NEW
    assert seed.weight == 0.0
    assert seed.turns_dormant == 0
    assert manager.event_log[-1].event_type == "reactivated"
    assert manager.event_log[-1].detail["basis"] == "keyword"


def test_expired_seed_is_never_reactivated() -> None:
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed(
        "alpha candidate",
        trigger_keywords=["needle"],
    )
    seed = manager.get_seed(seed_id)
    seed.unsafe_set_authority(status=SeedStatus.EXPIRED)

    assert manager.reactivate_by_text("needle appears") == []
    assert seed.status is SeedStatus.EXPIRED


def test_scan_trtl_keeps_reactivation_override_point() -> None:
    class HookedManager(SSLManager):
        def reactivate_by_text(
            self,
            text: str,
            threshold: float = 0.65,
        ) -> list[str]:
            assert (text, threshold) == ("context", 0.7)
            return ["hooked"]

    manager = HookedManager(embedding_fn=_embedding)

    assert manager.scan_trtl_triggers("context", threshold=0.7) == ["hooked"]


def test_vector_housekeeping_expiry_resets_authority() -> None:
    class FakeVectorConstellation:
        def housekeeping(self, max_age_days: int) -> list[str]:
            assert max_age_days == 7
            return ["ss_001", "missing"]

    manager = SSLManager(
        embedding_fn=_embedding,
        vector_constellation=FakeVectorConstellation(),
    )
    seed_id = manager.add_or_update_seed("alpha candidate")
    seed = manager.get_seed(seed_id)
    seed.unsafe_set_authority(weight=0.8, status=SeedStatus.PROMOTED)

    expired = manager.expire_vector_only_open_seeds(max_age_days=7)

    assert expired == [seed_id, "missing"]
    assert seed.status is SeedStatus.EXPIRED
    assert seed.weight == 0.0
    assert manager.event_log[-1].event_type == "expired"
    assert manager.event_log[-1].detail["max_age_days"] == 7
