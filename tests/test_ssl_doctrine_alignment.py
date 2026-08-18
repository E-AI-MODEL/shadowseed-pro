"""Regression contracts for the 2026-08 SSL doctrine alignment ADRs."""

from __future__ import annotations

import sqlite3

import numpy as np
import pytest

from shadowseed.benchmark.live_session_measurement import _normalized_candidates
from shadowseed.chat import ShadowChatSession
from shadowseed.core_config import SSLCoreConfig
from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import SignalKind, ValidationSignal
from shadowseed.intake import is_atomic_seed
from shadowseed.manager import SSLManager
from shadowseed.models import validate_seed_snapshot
from shadowseed.storage.schema import SCHEMA_VERSION
from shadowseed.storage.sqlite import SQLiteWorkspaceRepository, WorkspaceStorageError
from shadowseed.surfacing import SurfacingPolicy


class _StaticModel:
    name = "static-model"

    def generate(self, prompt, scenario, mode, seeds):
        return "A stable visible answer for detector regression testing."


class _StaticDetector:
    name = "static-detector"

    def __init__(self, candidate: str) -> None:
        self.candidate = candidate

    def detect_seeds(self, item, max_seeds=5):
        return [self.candidate]


def _embedding(_text: str) -> np.ndarray:
    return np.array([1.0, 0.0])


def _session(candidate: str, runtime_mode: str) -> ShadowChatSession:
    return ShadowChatSession(
        backend="openai",
        embedding_backend="sentence-transformers",
        runtime_mode=runtime_mode,
        recurrence_mode="pairwise",
        model_backend=_StaticModel(),
        detector_backend=_StaticDetector(candidate),
        embedding_fn=_embedding,
    )


@pytest.mark.parametrize("runtime_mode", ["live", "evaluation"])
def test_real_detector_sentence_is_not_split_by_historical_human_normalization(runtime_mode):
    candidate = "Market power, rather than technology, as an alternative explanatory frame."
    session = _session(candidate, runtime_mode)

    report = session.turn("What other explanation deserves investigation?")

    assert len(report["seeds_born_weightless"]) == 1
    seed = session.manager.seeds[report["seeds_born_weightless"][0]]
    assert seed.text == candidate
    assert seed.weight == 0.0


@pytest.mark.parametrize("runtime_mode", ["live", "evaluation"])
def test_real_detector_short_fragment_is_not_rewritten_into_dutch(runtime_mode):
    candidate = "Alternative causal boundary"
    session = _session(candidate, runtime_mode)

    report = session.turn("Which boundary is still uncertain?")

    assert len(report["seeds_born_weightless"]) == 1
    seed = session.manager.seeds[report["seeds_born_weightless"][0]]
    assert seed.text == "Alternative causal boundary."
    assert "ontbreekt" not in seed.text.casefold()


def test_live_measurement_uses_model_output_normalization_contract():
    candidate = "Market power, rather than technology, as an alternative explanatory frame."
    assert _normalized_candidates(candidate, max_seed_words=18) == [candidate]


def test_empty_and_whitespace_candidates_are_not_atomic():
    assert not is_atomic_seed("")
    assert not is_atomic_seed("   \n\t")


def test_snapshot_rejects_whitespace_seed_text():
    with pytest.raises(ValueError, match="text.*non-empty"):
        validate_seed_snapshot(
            {
                "id": "ss_001",
                "text": "   ",
                "embedding": [1.0, 0.0],
                "trace": 1.0,
            }
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"trace_start": 0.0},
        {"half_life_turns": 0.0},
        {"half_life_turns": -1.0},
        {"dedup_threshold": 1.1},
        {"promotion_threshold": 0.0},
        {"promotion_threshold": 1.1},
        {"dormant_threshold": -0.1},
        {"validation_increment": -0.1},
        {"contradiction_penalty": 1.1},
        {"reward_step": -0.1},
        {"penalty_step": 1.1},
        {"max_trace": 0.0},
        {"reactivation_increment": -0.1},
        {"min_occurrences_for_gate": 0},
        {"min_evidence_for_gate": -1},
        {"min_trace_for_gate": -0.1},
        {"max_seed_words": 0},
        {"dormant_ttl_turns": -1},
        {"contradiction_trace_penalty": -0.1},
        {"trace_start": 2.0, "max_trace": 1.0},
    ],
)
def test_core_config_rejects_invalid_ranges(kwargs):
    with pytest.raises(ValueError):
        SSLCoreConfig(**kwargs)


def test_core_config_rejects_non_finite_values():
    with pytest.raises(ValueError):
        SSLCoreConfig(half_life_turns=float("nan"))
    with pytest.raises(ValueError):
        SSLCoreConfig(trace_start=float("inf"))


def test_surfacing_policy_rejects_negative_top_k():
    with pytest.raises(ValueError, match="surface_top_k"):
        SurfacingPolicy(surface_top_k=-1)


def test_seed_ids_do_not_collide_after_sparse_registry_state():
    manager = SSLManager(embedding_fn=_embedding)
    first = manager.add_or_update_seed("First missing ownership relation.", deduplicate=False)
    second = manager.add_or_update_seed("Second missing dependency relation.", deduplicate=False)
    assert (first, second) == ("ss_001", "ss_002")

    manager._seeds.pop(first)
    third = manager.add_or_update_seed("Third missing boundary relation.", deduplicate=False)

    assert third == "ss_003"
    assert set(manager.seeds) == {"ss_002", "ss_003"}


def test_same_external_source_is_idempotent_across_signal_kinds():
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("One evidence identity for one source.")
    events = []
    for kind in (SignalKind.SSOT, SignalKind.RETRIEVAL, SignalKind.HUMAN_FEEDBACK):
        events.append(
            manager.submit_signals(
                seed_id,
                [
                    ValidationSignal(
                        kind=kind,
                        verified=True,
                        independent=True,
                        source_ref="source::same-underlying-evidence",
                    )
                ],
                policy_id="evidence_backed",
            )
        )

    assert [event.decision for event in events] == [
        GateDecision.VALIDATED,
        GateDecision.BLOCKED,
        GateDecision.BLOCKED,
    ]
    assert manager.seeds[seed_id].weight == pytest.approx(0.2)
    assert manager.seeds[seed_id].evidence_count == 1
    assert "duplicate authority support ignored" in events[1].reason
    assert "duplicate authority support ignored" in events[2].reason


def test_distinct_external_sources_can_accumulate_bounded_authority():
    manager = SSLManager(embedding_fn=_embedding)
    seed_id = manager.add_or_update_seed("Independent sources for one candidate.")
    for index, kind in enumerate(
        (SignalKind.SSOT, SignalKind.RETRIEVAL, SignalKind.HUMAN_FEEDBACK)
    ):
        manager.submit_signals(
            seed_id,
            [
                ValidationSignal(
                    kind=kind,
                    verified=True,
                    independent=True,
                    source_ref=f"source::{index}",
                )
            ],
            policy_id="evidence_backed",
        )

    assert manager.seeds[seed_id].weight == pytest.approx(0.6)
    assert manager.seeds[seed_id].evidence_count == 3


def test_failed_older_workspace_restore_keeps_current_database_intact(tmp_path):
    live_path = tmp_path / "live.sqlite"
    repository = SQLiteWorkspaceRepository(live_path)
    repository.initialize()
    assert repository.schema_version() == SCHEMA_VERSION

    bad_backup = tmp_path / "older.sqlite"
    with sqlite3.connect(bad_backup) as connection:
        connection.execute("CREATE TABLE workspace_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO workspace_meta(key, value) VALUES('schema_version', '0')"
        )
        connection.commit()

    with pytest.raises(WorkspaceStorageError, match="no migration path"):
        repository.restore_from(bad_backup)

    assert repository.schema_version() == SCHEMA_VERSION
