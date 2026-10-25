"""Real detector->canonical intake->observation lineage without new authority.

No model calls or external sources; synthetic input strings exercise the
actual existing intake and multi-turn engine. Provenance is NOT proof of
semantic accuracy, novelty or hidden model representations.
"""

from __future__ import annotations

import numpy as np

from shadowseed import ShadowseedEngine
from shadowseed.manager import SSLManager
from shadowseed.observations import (
    CandidateObservationLedger,
    link_intake_lineage_to_observations,
)
from shadowseed.seed_normalization import (
    normalize_detection_candidates,
    normalize_detection_candidates_with_sources,
)


def _embed(text: str) -> np.ndarray:
    lowered = text.lower()
    if "beta" in lowered or "calibration" in lowered:
        return np.array([0.0, 1.0, 0.0])
    return np.array([1.0, 0.0, 0.0])


def _manager() -> SSLManager:
    return SSLManager(embedding_fn=_embed)


def test_single_normalizer_preserves_each_raw_index_and_historical_strings() -> None:
    raw = ["ontbrekende context: alpha, beta", "alpha", "  "]
    for split in (True, False):
        for expand in (True, False):
            with_sources = normalize_detection_candidates_with_sources(
                raw, split_broad=split, expand_short_fragments=expand
            )
            assert normalize_detection_candidates(
                raw, split_broad=split, expand_short_fragments=expand
            ) == [text for _index, text in with_sources]
    assert normalize_detection_candidates_with_sources(raw) == [
        (0, "alpha ontbreekt."),
        (0, "beta ontbreekt."),
        (1, "alpha ontbreekt."),
    ]


def test_intake_preserves_duplicate_raw_occurrences_and_real_seed_events() -> None:
    manager = _manager()
    outcome = manager.ingest_detection_candidates(
        ["alpha omission", "alpha omission", "beta omission"],
        split_broad=False, expand_short_fragments=False,
    )
    assert outcome["input_count"] == 3
    assert outcome["lineage_status"] == "canonical"
    assert [row["raw_candidate_index"] for row in outcome["lineage"]] == [0, 1, 2]
    assert [row["normalized_index"] for row in outcome["lineage"]] == [0, 1, 2]
    assert [row["outcome"] for row in outcome["lineage"]] == [
        "accepted", "rejected", "accepted",
    ]
    assert outcome["lineage"][1]["reason"] == "duplicate"
    assert outcome["lineage"][1]["seed_id"] is None
    assert outcome["lineage"][0]["seed_transition"] == "created"
    assert outcome["lineage"][2]["seed_transition"] == "created"
    assert [x["seed_id"] for x in outcome["accepted"]] == [
        outcome["lineage"][0]["seed_id"],
        outcome["lineage"][2]["seed_id"],
    ]
    assert all(manager.get_seed(x["seed_id"]).weight == 0 for x in outcome["accepted"])
    assert all(manager.get_seed(x["seed_id"]).evidence_count == 0 for x in outcome["accepted"])
    assert not manager.gate_events


def test_split_and_dropped_raw_item_remain_auditable() -> None:
    manager = _manager()
    result = manager.ingest_detection_candidates(
        ["ontbrekende context: alpha, beta", " \n  "]
    )
    lineage = result["lineage"]
    assert result["lineage_status"] == "canonical"
    assert [row["normalized_text"] for row in lineage[:2]] == [
        "alpha ontbreekt.", "beta ontbreekt.",
    ]
    assert [row["raw_candidate_index"] for row in lineage] == [0, 0, 1]
    assert lineage[2]["normalized_index"] is None
    assert lineage[2]["outcome"] == "dropped"
    assert lineage[2]["reason"] == "normalizer_dropped"
    assert len(result["accepted"]) == 2
    assert not manager.gate_events


def test_preexisting_dedup_and_rejection_reasons_have_separate_paths() -> None:
    manager = _manager()
    initial = manager.add_or_update_seed("alpha omission")
    result = manager.ingest_detection_candidates(
        [
            "alpha gap",
            "voeg een volledig analysekader toe met aandacht voor data en condities",
            "beta",
        ],
        expand_short_fragments=False,
        split_broad=False,
        min_seed_words=2,
    )
    rows = result["lineage"]
    assert rows[0]["raw_candidate_index"] == 0
    assert rows[0]["outcome"] == "accepted"
    assert rows[0]["seed_id"] == initial
    assert rows[0]["seed_transition"] == "deduplicated"
    assert rows[1]["reason"] == "not_atomic"
    assert rows[2]["reason"] == "too_vague"
    assert rows[1]["seed_id"] is rows[2]["seed_id"] is None
    assert manager.get_seed(initial).occurrence_count == 2
    assert not manager.gate_events


def test_custom_normalizer_is_not_reverse_matched_by_string_guesswork() -> None:
    class Hooked(SSLManager):
        def normalize_detection_candidates(
            self, candidates, expand_short_fragments=True, split_broad=True
        ) -> list[str]:
            del candidates, expand_short_fragments, split_broad
            return ["hooked candidate"]

        def add_or_update_seed(self, text, **kwargs) -> str:
            assert text == "hooked candidate"
            return "external-hook-seed-id"

    manager = Hooked(embedding_fn=_embed)
    result = manager.ingest_detection_candidates(["some raw candidate"])
    assert result["accepted"] == [
        {"seed_id": "external-hook-seed-id", "text": "hooked candidate"}
    ]
    assert result["lineage_status"] == "unresolved_normalizer_override"
    row = result["lineage"][0]
    assert row["raw_candidate_index"] is None
    assert row["source_mapping_status"] == "unresolved_normalizer_override"
    assert row["seed_transition"] == "unresolved_custom_adapter"
    assert row["seed_id"] == "external-hook-seed-id"


def test_observation_ids_link_actual_raw_positions_not_text_duplicates() -> None:
    manager = _manager()
    raw = ["alpha omission", "alpha omission", "   "]
    ingested = manager.ingest_detection_candidates(
        raw, split_broad=False, expand_short_fragments=False,
    )
    ledger = CandidateObservationLedger()
    observations = ledger.record_batch(
        raw,
        context_ref="turn:0:visible_answer",
        detector_backend="scripted-no-model",
        detector_prompt_provenance=None,
        candidate_type="unspecified",
        ssl_exposed=False,
        created_at="2026-10-25T14:00:00+01:00",
    )
    linked = link_intake_lineage_to_observations(
        ingested["lineage"], raw, observations,
        context_ref="turn:0:visible_answer",
    )
    assert linked[0]["observation_id"] == observations[0].observation_id
    assert linked[1]["observation_id"] == observations[1].observation_id
    assert linked[0]["observation_id"] != linked[1]["observation_id"]
    assert linked[0]["observation_link_status"] == "recorded_exact_raw_item"
    assert linked[1]["reason"] == "duplicate"
    assert linked[2]["observation_id"] is None
    assert linked[2]["observation_link_status"] == "empty_unrecorded_source"

    # The append-only ledger deduplicates a repeated observation batch.
    # A later call cannot invent new observation IDs from historical data.
    omitted = ledger.record_batch(
        raw,
        context_ref="turn:0:visible_answer",
        detector_backend="scripted-no-model",
        detector_prompt_provenance=None,
        candidate_type="unspecified",
        ssl_exposed=False,
        created_at="2026-10-25T14:01:00+01:00",
    )
    assert omitted == []
    later = link_intake_lineage_to_observations(
        ingested["lineage"], raw, omitted,
        context_ref="turn:0:visible_answer",
    )
    assert later[0]["observation_id"] is None
    assert later[0]["observation_link_status"] == "not_recorded_in_current_batch"


class _FirstTurnDetector:
    name = "INVESTIGATOR-SCRIPTED-NO-MODEL"
    prompt_variant = "scripted"

    def __init__(self) -> None:
        self.calls = 0

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        assert isinstance(item["text"], str)
        self.calls += 1
        if self.calls == 1:
            return [
                "How does valve position affect chamber B pressure?",
                "How does valve position affect chamber B pressure?",
                "Could calibration drift affect the reliability of the measurement?",
            ]
        return []


def test_live_engine_reports_exact_lineage_and_preserves_weightless_memory() -> None:
    detector = _FirstTurnDetector()
    engine = ShadowseedEngine(
        detector_backend=detector,
        embedding_fn=_embed,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    prepared = engine.prepare_turn("Which readings are available?")
    assert prepared.model_context == ""
    first = engine.observe_turn(prepared, "Only one pressure reading is available.")
    diag = first["intake_diagnostics"]
    assert diag["lineage_status"] == "canonical"
    rows = diag["item_lineage"]
    assert len(rows) == 3
    assert [row["raw_candidate_index"] for row in rows] == [0, 1, 2]
    assert [row["outcome"] for row in rows] == [
        "accepted", "rejected", "accepted",
    ]
    assert rows[1]["reason"] == "duplicate"
    assert all(row["observation_id"] for row in rows)
    assert len({row["observation_id"] for row in rows}) == 3
    assert len(first["candidate_observations"]) == 3
    assert len(first["seeds_born_weightless"]) == 2
    for row in rows:
        assert row["observation_link_status"] == "recorded_exact_raw_item"
        assert row["source_mapping_status"] == "canonical"
    assert not first["surfaced_seed_ids"]
    assert not engine.inspect()["influence_records"]
    assert not engine._session.manager.gate_events

    prepared_next = engine.prepare_turn("What changed in the experiment?")
    assert prepared_next.model_context == ""
    second = engine.observe_turn(prepared_next, "No additional measurements.")
    assert second["intake_diagnostics"]["item_lineage"] == []
    assert second["seeds_born_weightless"] == []
    assert engine.inspect()["turns"] == 2
    assert detector.calls == 2
    assert all(s["weight"] == 0 for s in engine.inspect()["seeds"])
    assert all(s["evidence_count"] == 0 for s in engine.inspect()["seeds"])
    assert not engine._session.manager.gate_events
    assert engine.audit() == 0
    exported = engine.export_state()
    assert exported["turn_reports"][0]["intake_diagnostics"]["item_lineage"] == rows


class _NoNetworkModel:
    name = "scripted-local-host"

    def generate(self, prompt, scenario, mode, seeds):
        assert isinstance(prompt, str)
        assert mode in {"baseline", "ssl"}
        assert isinstance(seeds, list)
        return "Only one pressure reading was available."


def test_evaluation_and_source_observation_report_the_same_lineage() -> None:
    from shadowseed.chat import ShadowChatSession

    evaluation = ShadowChatSession(
        backend="fixture",
        runtime_mode="evaluation",
        detector_backend=_FirstTurnDetector(),
        model_backend=_NoNetworkModel(),
        embedding_fn=_embed,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    comparison = evaluation.turn("What did the instrument measure?")
    diag = comparison["intake_diagnostics"]
    assert diag["lineage_schema"] == "candidate-intake-lineage-v1"
    assert diag["lineage_status"] == "canonical"
    assert [x["outcome"] for x in diag["item_lineage"]] == [
        "accepted", "rejected", "accepted",
    ]
    assert [x["raw_candidate_index"] for x in diag["item_lineage"]] == [0, 1, 2]
    recorded = {
        item["observation_id"] for item in comparison["candidate_observations"]
    }
    assert len(recorded) == 3
    assert {x["observation_id"] for x in diag["item_lineage"]} == recorded
    assert not comparison["promoted_this_turn"]
    assert all(s["weight"] == 0 for s in evaluation.shadow_report()["seeds"])

    source = ShadowChatSession(
        backend="fixture",
        runtime_mode="live",
        detector_backend=_FirstTurnDetector(),
        model_backend=_NoNetworkModel(),
        embedding_fn=_embed,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    imported = source.observe_source_text(
        "A synthetic report with one pressure reading.",
        context_ref="source:fixture:007",
    )
    source_diag = imported["intake_diagnostics"]
    assert source_diag["lineage_schema"] == "candidate-intake-lineage-v1"
    assert source_diag["lineage_status"] == "canonical"
    assert [x["raw_candidate_index"] for x in source_diag["item_lineage"]] == [
        0, 1, 2,
    ]
    assert [x["outcome"] for x in source_diag["item_lineage"]] == [
        "accepted", "rejected", "accepted",
    ]
    source_ids = {
        item["observation_id"] for item in imported["candidate_observations"]
    }
    assert source_ids == {
        x["observation_id"] for x in source_diag["item_lineage"]
    }
    assert all(
        x["observation_link_status"] == "recorded_exact_raw_item"
        for x in source_diag["item_lineage"]
    )
    assert not imported["promoted_this_observation"]
    assert all(s.weight == 0 for s in source.manager.seeds.values())
