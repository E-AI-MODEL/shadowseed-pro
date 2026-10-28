"""Pro contract: retained unbounded possibilities are never an authority shortcut.

Synthetic fixtures inspect actual Engine, Manager, Gate and TTL/TrTL mechanics.
No paid model calls and no claim about intellectual value or model novelty.
"""
from __future__ import annotations

from copy import deepcopy

import numpy as np
import pytest

from shadowseed import ShadowseedEngine
from shadowseed.gate.events import GateDecision
from shadowseed.gate.signals import (
    SignalDirection, SignalKind, ValidationSignal, recurrence_signal,
)
from shadowseed.manager import SSLManager, SeedStatus
from shadowseed.models import ShadowSeed


BATTERY = (
    "Of lage batterijspanning ook de bewegingssensor of de tijdregistratie "
    "kan beïnvloeden, naast de camera."
)
COMPOUND = "Is de klok betrouwbaar? Werkt de bewegingssensor onder lage spanning?"


def embedding(text: str) -> np.ndarray:
    return np.array([1.0, 0.0]) if "batterij" in text.lower() else np.array([0.0, 1.0])


def evidence(ref: str) -> ValidationSignal:
    return ValidationSignal(
        kind=SignalKind.SSOT, direction=SignalDirection.SUPPORT,
        strength=1.0, verified=True, independent=True, source_ref=ref,
        reason="synthetic source for guarded state transition",
    )


class OnceDetector:
    name = "synthetic-detector"
    prompt_variant = "synthetic"

    def __init__(self, text: str | None):
        self.text = text
        self.calls = 0

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        self.calls += 1
        return [self.text] if self.text and self.calls == 1 else []


def engine(text: str | None) -> ShadowseedEngine:
    return ShadowseedEngine(
        detector_backend=OnceDetector(text), embedding_fn=embedding,
        recurrence_mode="pairwise", gate_policy_id="evidence_backed",
    )


def progress(e: ShadowseedEngine, question: str = "Test?", answer: str = "Neutral answer."):
    prepared = e.prepare_turn(question)
    assert prepared.model_context == ""
    assert prepared.surfaced_seed_ids == ()
    return prepared, e.observe_turn(prepared, answer)


def test_original_battery_candidate_becomes_real_weightless_seed():
    e = engine(BATTERY)
    _prepared, result = progress(e)
    assert result["intake_diagnostics"]["accepted"] == []
    assert result["intake_diagnostics"]["rejected"] == []
    assert len(result["seeds_born_unresolved"]) == 1
    assert result["seeds_born_unresolved"] == result["seeds_born_weightless"]
    sid = result["seeds_born_unresolved"][0]
    state = e.inspect()["seeds"][0]
    assert state["id"] == sid
    assert state["text"] == BATTERY
    assert state["scope_status"] == "unresolved"
    assert state["trace"] > 0
    assert state["weight"] == 0
    assert state["occurrence_count"] == 1
    lineage = result["intake_diagnostics"]["item_lineage"][0]
    assert lineage["seed_transition"] == "created_unresolved"
    assert lineage["observation_id"]
    assert result["candidate_observations"][0]["raw_text"] == BATTERY


def test_weightless_unresolved_travels_through_save_restore_and_dormant_trtl():
    e = engine(BATTERY)
    none = engine(None)
    _, first = progress(e)
    _, blank = progress(none)
    assert not blank["seeds_born_weightless"]
    sid = first["seeds_born_unresolved"][0]
    state = e.export_state()
    assert state["manager"]["seeds"][0]["scope_status"] == "unresolved"
    restored = ShadowseedEngine.from_state(
        state, detector_backend=OnceDetector(None), embedding_fn=embedding,
    )
    assert restored.inspect()["seeds"][0]["id"] == sid
    assert restored.inspect()["seeds"][0]["text"] == BATTERY
    for _ in range(35):
        progress(restored, question="Unrelated note about climate policy")
        progress(none, question="Unrelated note about climate policy")
        if restored.inspect()["seeds"][0]["status"] == "DORMANT":
            break
    else:
        pytest.fail("seed never went dormant")
    before = restored.inspect()["seeds"][0]
    prepared = restored.prepare_turn(BATTERY)
    assert sid in prepared.reactivated_trtl
    assert prepared.model_context == ""
    restored.observe_turn(prepared, "No external evidence")
    after = restored.inspect()["seeds"][0]
    assert after["id"] == sid
    assert after["weight"] == 0
    assert after["trace"] > before["trace"]
    assert after["occurrence_count"] == 1
    assert restored.audit() == 0


def test_gate_blocks_unresolved_even_with_verified_support_and_recurrence():
    manager = SSLManager(embedding_fn=embedding)
    result = manager.ingest_detection_candidates(
        [COMPOUND], expand_short_fragments=False, split_broad=False,
    )
    sid = result["unresolved"][0]["seed_id"]
    seed = manager.seeds[sid]
    for policy, signal in (
        ("evidence_backed", evidence("synthetic:1")),
        ("exploratory", recurrence_signal(12, threshold=2, source_ref="synthetic:r")),
        ("legacy_evidence_required", evidence("synthetic:2")),
    ):
        event = manager.submit_signals(sid, [signal], policy_id=policy)
        assert event.decision == GateDecision.BLOCKED
        assert event.policy_id == policy
        assert seed.weight == 0
        assert seed.evidence_count == 0
        assert seed.status != SeedStatus.PROMOTED
    assert not manager.current_gate_authorizes(sid, policy_id="exploratory")
    with pytest.raises(AttributeError, match="immutable"):
        seed.scope_status = "bounded"
    with pytest.raises(ValueError, match="unresolved"):
        seed.unsafe_set_authority(weight=0.8, status=SeedStatus.PROMOTED)


def test_snapshot_tamper_fails_and_legacy_default_remains_bounded():
    manager = SSLManager(embedding_fn=embedding)
    sid = manager.ingest_detection_candidates(
        [BATTERY], expand_short_fragments=False, split_broad=False
    )["unresolved"][0]["seed_id"]
    payload = manager.seeds[sid].to_dict()
    for weight in (0.2, 1.0):
        tampered = deepcopy(payload)
        tampered["weight"] = weight
        with pytest.raises(ValueError, match="unresolved"):
            ShadowSeed.from_dict(tampered)
    tampered = deepcopy(payload)
    tampered["scope_status"] = "unknown"
    with pytest.raises(ValueError, match="scope_status"):
        ShadowSeed.from_dict(tampered)
    legacy = deepcopy(payload)
    legacy.pop("scope_status")
    assert ShadowSeed.from_dict(legacy).scope_status == "bounded"


def test_exact_redetection_keeps_id_without_forged_gate_credit():
    manager = SSLManager(embedding_fn=embedding)
    first = manager.ingest_detection_candidates(
        [BATTERY], split_broad=False, expand_short_fragments=False
    )
    sid = first["unresolved"][0]["seed_id"]
    next_turn = manager.ingest_detection_candidates(
        [BATTERY, BATTERY], split_broad=False, expand_short_fragments=False
    )
    assert len(manager.seeds) == 1
    assert [x["seed_id"] for x in next_turn["unresolved"]] == [sid, sid]
    assert [x["transition"] for x in next_turn["unresolved"]] == [
        "reobserved_unresolved", "reobserved_same_batch_no_credit"
    ]
    assert manager.seeds[sid].occurrence_count == 1
    assert manager.seeds[sid].weight == 0
    assert manager.gate_events == []
    assert len([e for e in manager.event_log if e.event_type == "unresolved_reobserved"]) == 1


def test_bounded_seed_does_not_semantically_deduplicate_into_unresolved():
    manager = SSLManager(embedding_fn=embedding)
    first = manager.ingest_detection_candidates(
        [BATTERY], split_broad=False, expand_short_fragments=False
    )
    unresolved_sid = first["unresolved"][0]["seed_id"]
    accepted = manager.ingest_detection_candidates(
        ["Can shared power supplies affect camera measurements?"],
        split_broad=False, expand_short_fragments=False,
    )
    assert len(accepted["accepted"]) == 1
    bounded_sid = accepted["accepted"][0]["seed_id"]
    assert bounded_sid != unresolved_sid
    assert manager.seeds[bounded_sid].scope_status == "bounded"
    assert manager.seeds[unresolved_sid].scope_status == "unresolved"
