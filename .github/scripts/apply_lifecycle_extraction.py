from __future__ import annotations

import ast
from pathlib import Path


LIFECYCLE_SOURCE = r'''"""TTL, dormancy, TrTL reactivation, and expiry workflows.

This module owns the executable seed-lifecycle concern that used to live in
:mod:`shadowseed.manager`. ``SSLManager`` keeps its historical public and private
methods as thin compatibility facades, while mechanical authority transitions
remain explicit and separately allowlisted from Gate-controlled decisions.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np

from shadowseed.models import SeedStatus, ShadowSeed


def status_after_decay(manager: Any, seed: ShadowSeed) -> SeedStatus:
    """Return the historical status transition after trace decay."""

    if seed.trace < manager.dormant_threshold and seed.weight == 0.0:
        return SeedStatus.DORMANT
    if seed.trace < manager.config.min_trace_for_gate and seed.status not in {
        SeedStatus.PROMOTED,
        SeedStatus.DORMANT,
    }:
        return SeedStatus.DECAYING
    return seed.status


def decay_traces(manager: Any, turns_passed: int = 1) -> None:
    """Decay trace and run the dormant TTL clock for every live seed."""

    for seed_id, seed in manager._seeds.items():
        if seed.status == SeedStatus.EXPIRED:
            continue

        before_trace = seed.trace
        seed.trace *= math.exp(-turns_passed / manager.half_life_turns)
        manager._set_authority(seed, status=manager._status_after_decay(seed))

        expired = False
        if seed.status == SeedStatus.DORMANT:
            seed.turns_dormant += turns_passed
            if (
                manager.dormant_ttl_turns > 0
                and seed.turns_dormant >= manager.dormant_ttl_turns
            ):
                manager._set_authority(
                    seed,
                    status=SeedStatus.EXPIRED,
                    weight=0.0,
                )
                expired = True
        else:
            seed.turns_dormant = 0

        manager._touch_seed(seed)
        manager._record_and_sync(
            "trace_decayed",
            seed_id,
            turns_passed=turns_passed,
            trace_before=before_trace,
            trace_after=seed.trace,
            status=seed.status.value,
            turns_dormant=seed.turns_dormant,
        )
        if expired:
            manager._record_event(
                "expired",
                seed_id,
                reason="dormant_ttl",
                turns_dormant=seed.turns_dormant,
            )


def reactivate_by_text(
    manager: Any,
    text: str,
    threshold: float = 0.65,
) -> list[str]:
    """Reactivate matching dormant seeds through semantic or keyword triggers."""

    query_emb = manager.get_embedding(text)
    reactivated: list[str] = []

    for seed_id, seed in manager._seeds.items():
        if seed.status != SeedStatus.DORMANT:
            continue

        similarity = float(np.dot(query_emb, seed.embedding))
        keyword_hit = any(
            keyword.lower() in text.lower() for keyword in seed.trigger_keywords
        )

        if similarity >= threshold or keyword_hit:
            seed.trace = min(
                seed.trace + manager.reactivation_increment,
                manager.max_trace,
            )
            manager._set_authority(seed, status=SeedStatus.NEW)
            seed.turns_dormant = 0
            manager._touch_seed(seed)
            semantic_hit = similarity >= threshold
            if semantic_hit and keyword_hit:
                basis = "semantic+keyword"
            elif semantic_hit:
                basis = "semantic"
            else:
                basis = "keyword"
            manager._record_and_sync(
                "reactivated",
                seed_id,
                similarity=similarity,
                keyword_hit=keyword_hit,
                basis=basis,
                trace=seed.trace,
            )
            reactivated.append(seed_id)

    return reactivated


def scan_trtl_triggers(
    manager: Any,
    text: str,
    threshold: float = 0.65,
) -> list[str]:
    """Canonical TrTL alias that preserves the manager override point."""

    return manager.reactivate_by_text(text, threshold=threshold)


def expire_vector_only_open_seeds(
    manager: Any,
    max_age_days: int = 30,
) -> list[str]:
    """Apply terminal expiry returned by vector-store housekeeping."""

    if manager.vector_constellation is None:
        return []
    expired = manager.vector_constellation.housekeeping(max_age_days=max_age_days)
    for seed_id in expired:
        if seed_id in manager._seeds:
            seed = manager._seeds[seed_id]
            manager._set_authority(
                seed,
                status=SeedStatus.EXPIRED,
                weight=0.0,
            )
            manager._touch_seed(seed)
            manager._record_event("expired", seed_id, max_age_days=max_age_days)
    return expired


__all__ = [
    "decay_traces",
    "expire_vector_only_open_seeds",
    "reactivate_by_text",
    "scan_trtl_triggers",
    "status_after_decay",
]
'''


MANAGER_REPLACEMENTS = {
    "_status_after_decay": '''    def _status_after_decay(self, seed: ShadowSeed) -> SeedStatus:
        """Compatibility facade for lifecycle status derivation."""

        return lifecycle_engine.status_after_decay(self, seed)
''',
    "decay_traces": '''    def decay_traces(self, turns_passed: int = 1) -> None:
        """Compatibility facade for TTL decay, dormancy, and expiry."""

        lifecycle_engine.decay_traces(self, turns_passed=turns_passed)
''',
    "reactivate_by_text": '''    def reactivate_by_text(
        self, text: str, threshold: float = 0.65
    ) -> list[str]:
        """Compatibility facade for TrTL reactivation."""

        return lifecycle_engine.reactivate_by_text(
            self,
            text,
            threshold=threshold,
        )
''',
    "scan_trtl_triggers": '''    def scan_trtl_triggers(
        self, text: str, threshold: float = 0.65
    ) -> list[str]:
        """Compatibility facade for the canonical TrTL name."""

        return lifecycle_engine.scan_trtl_triggers(
            self,
            text,
            threshold=threshold,
        )
''',
    "expire_vector_only_open_seeds": '''    def expire_vector_only_open_seeds(
        self, max_age_days: int = 30
    ) -> list[str]:
        """Compatibility facade for vector-store-driven terminal expiry."""

        return lifecycle_engine.expire_vector_only_open_seeds(
            self,
            max_age_days=max_age_days,
        )
''',
}


LIFECYCLE_TEST = r'''"""Regression coverage for lifecycle extraction (#25 step 2d)."""

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
'''


AUTHORITY_EXPECTATION_OLD = '''    assert _authority_calls(source_root / "manager.py", "SSLManager") == {
        "decay_traces": 2,
        "reactivate_by_text": 1,
        "expire_vector_only_open_seeds": 1,
    }
    assert _authority_calls(source_root / "intake.py") == {
        "activate_existing_seed": 1,
    }
'''

AUTHORITY_EXPECTATION_NEW = '''    assert _authority_calls(source_root / "manager.py", "SSLManager") == {}
    assert _authority_calls(source_root / "intake.py") == {
        "activate_existing_seed": 1,
    }
    assert _authority_calls(source_root / "lifecycle.py") == {
        "decay_traces": 2,
        "reactivate_by_text": 1,
        "expire_vector_only_open_seeds": 1,
    }
'''


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"{path}: expected one anchor, got {text.count(old)}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    Path("src/shadowseed/lifecycle.py").write_text(
        LIFECYCLE_SOURCE,
        encoding="utf-8",
    )

    manager_path = Path("src/shadowseed/manager.py")
    manager_text = manager_path.read_text(encoding="utf-8")
    manager_text = manager_text.replace("import math\n", "", 1)
    import_anchor = "from shadowseed import intake as intake_engine\n"
    if manager_text.count(import_anchor) != 1:
        raise SystemExit("manager lifecycle import anchor not found exactly once")
    manager_text = manager_text.replace(
        import_anchor,
        import_anchor + "from shadowseed import lifecycle as lifecycle_engine\n",
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

    Path("tests/test_lifecycle_extraction.py").write_text(
        LIFECYCLE_TEST,
        encoding="utf-8",
    )
    replace_once(
        Path("tests/test_gate_boundary_completion.py"),
        AUTHORITY_EXPECTATION_OLD,
        AUTHORITY_EXPECTATION_NEW,
    )

    replace_once(
        Path("README.md"),
        "| [`shadowseed.intake`](src/shadowseed/intake.py) | Embedding acquisition, atomicity heuristics, detector-candidate normalization, deduplication, and seed creation/update |\n",
        "| [`shadowseed.intake`](src/shadowseed/intake.py) | Embedding acquisition, atomicity heuristics, detector-candidate normalization, deduplication, and seed creation/update |\n"
        "| [`shadowseed.lifecycle`](src/shadowseed/lifecycle.py) | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |\n",
    )
    replace_once(
        Path("docs/architecture/overview.md"),
        "| `shadowseed.intake` | Embedding acquisition, atomicity heuristics, detector-candidate normalization, deduplication, and seed creation/update |\n",
        "| `shadowseed.intake` | Embedding acquisition, atomicity heuristics, detector-candidate normalization, deduplication, and seed creation/update |\n"
        "| `shadowseed.lifecycle` | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |\n",
    )

    Path(".github/workflows/apply-lifecycle-extraction.yml").unlink()
    Path(".github/scripts/apply_lifecycle_extraction.py").unlink()


if __name__ == "__main__":
    main()
