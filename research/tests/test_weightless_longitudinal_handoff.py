"""Canonical multi-turn mechanics: scripted host and detector, zero LLM calls.

The experiments here are NOT Q1/Q2 evidence and cannot score semantic growth.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

import numpy as np
import pytest

from shadowseed import ShadowseedEngine
from shadowseed_research.benchmark.weightless_birth_handoff import (
    freeze_canonical_weightless_birth,
)
from shadowseed_research.benchmark.weightless_longitudinal_handoff import (
    SCHEMA, freeze_weightless_followup,
)

SEED = "Hoe verandert een niet-gekende klepstand de druk in kamer B?"
QUESTION = "Welke meting hebben we in kamer B?"
ANSWER = "Er is alleen een drukmeting beschikbaar."


class ScriptedDetector:
    name = "investigator-scripted-not-model"
    prompt_variant = "investigator-scripted"

    def __init__(self, at_turns: tuple[int, ...] = (1,)):
        self.at_turns = at_turns
        self.calls = 0

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        assert isinstance(item["question"], str)
        assert isinstance(item["text"], str)
        assert isinstance(item["conversation_context"], str)
        self.calls += 1
        return [SEED] if self.calls in self.at_turns else []


def embed(text: str) -> np.ndarray:
    return np.array(
        [1., 0.] if "klep" in text.lower() or "druk" in text.lower()
        else [0., 1.], dtype=float,
    )


def engine(at_turns: tuple[int, ...] = (1,)):
    detector = ScriptedDetector(at_turns)
    app = ShadowseedEngine(
        detector_backend=detector,
        embedding_fn=embed,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    return app, detector


def turn(app: ShadowseedEngine, question: str, answer: str = ANSWER):
    prepared = app.prepare_turn(question)
    assert prepared.model_context == ""
    assert prepared.surfaced_seed_ids == ()
    report = app.observe_turn(prepared, answer)
    assert report["answer"] == answer
    return report


def first_birth(app: ShadowseedEngine):
    first = turn(app, QUESTION)
    sid = first["seeds_born_weightless"][0]
    return sid, freeze_canonical_weightless_birth(app, first, sid)


def rehash(obj: dict) -> dict:
    data = deepcopy(obj)
    data.pop("snapshot_sha256", None)
    data["snapshot_sha256"] = sha256(json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()
    return data


def test_actual_multiple_turns_chain_one_weightless_seed_without_model_claim():
    shadow, detector = engine()
    none, baseline = engine(())
    sid, birth = first_birth(shadow)
    turn(none, QUESTION)

    pair = ("Wat weten we nog niet?", "Dat blijft onbeslist.")
    assert turn(shadow, *pair)["answer"] == turn(none, *pair)["answer"]
    state = deepcopy(shadow.export_state())
    a = freeze_weightless_followup(shadow, birth)
    assert shadow.export_state() == state
    assert a["schema"] == SCHEMA
    assert a["turn"] == 1
    assert a["seed_id"] == sid
    assert a["candidate_text_sha256"] == birth["candidate_text_sha256"]
    assert a["previous_checkpoint_sha256"] is None
    assert a["seed_state_after_turn"]["weight"] == 0
    assert a["seed_state_after_turn"]["occurrence_count"] == 1
    assert a["redetected_same_seed_reported"] is False
    assert a["trtl_reactivated_same_seed"] is False
    assert a["actual_llm_origin_verified"] is False
    assert a["semantic_growth_assessed"] is False
    assert a["later_model_originated_inquiry_assessed"] is False
    assert a["q1_or_q2_effect_established"] is False
    assert a["eligible_for_automatic_gate_or_prompt"] is False
    assert "candidate_text" not in a and "answer" not in a

    pair = ("Welke nieuwe meting zou zinvol zijn?", "Er is nog geen bewijs.")
    assert turn(shadow, *pair)["answer"] == turn(none, *pair)["answer"]
    before = deepcopy(shadow.export_state())
    b = freeze_weightless_followup(shadow, birth, previous=a)
    assert shadow.export_state() == before
    assert b["turn"] == 2
    assert b["previous_checkpoint_sha256"] == a["snapshot_sha256"]
    assert b["seed_state_after_turn"]["trace"] < a["seed_state_after_turn"]["trace"]
    assert b["event_log_count"] >= a["event_log_count"]
    assert b["seed_state_after_turn"]["weight"] == 0
    assert b["seed_state_after_turn"]["evidence_count"] == 0
    assert not shadow.inspect()["influence_records"]
    assert not none.inspect()["seeds"]
    assert shadow.audit() == none.audit() == 0
    assert detector.calls == baseline.calls == 3


def test_unobserved_turns_cannot_be_recreated_retroactively():
    app, _ = engine()
    _, birth = first_birth(app)
    with pytest.raises(ValueError, match="no complete subsequent"):
        freeze_weightless_followup(app, birth)
    turn(app, "Een eerste vervolg zonder detectorproposal?")
    first = freeze_weightless_followup(app, birth)
    with pytest.raises(ValueError, match="first follow-up"):
        freeze_weightless_followup(app, birth, previous=first)
    turn(app, "Tweede vervolg")
    turn(app, "Derde vervolg")
    with pytest.raises(ValueError, match="previous checkpoint is not the preceding history"):
        freeze_weightless_followup(app, birth, previous=first)


def test_real_repeat_in_canonical_intake_is_not_second_birth():
    app, _ = engine((1, 3))
    sid, birth = first_birth(app)
    turn(app, "Wat maakt de klepstand onzeker?")
    a = freeze_weightless_followup(app, birth)
    observed = turn(app, "Is de klepstand nog steeds niet bekend?")
    assert observed["seeds_born_weightless"] == [sid]
    b = freeze_weightless_followup(app, birth, previous=a)
    assert b["redetected_same_seed_reported"] is True
    assert b["seed_state_after_turn"]["occurrence_count"] >= 2
    assert b["seed_state_after_turn"]["weight"] == 0
    assert b["candidate_text_sha256"] == a["candidate_text_sha256"]


def test_recurrence_gate_block_is_not_conflated_with_authority():
    app, _ = engine((1, 2, 3))
    sid, birth = first_birth(app)
    turn(app, "Nog altijd onbekende klepstand?")
    a = freeze_weightless_followup(app, birth)
    turn(app, "Nogmaals: onbekende klepstand?")
    b = freeze_weightless_followup(app, birth, previous=a)
    assert b["redetected_same_seed_reported"]
    assert b["seed_state_after_turn"]["weight"] == 0
    assert b["seed_state_after_turn"]["evidence_count"] == 0
    assert b["seed_state_after_turn"]["authority_version"] == 0
    assert b["new_gate_decisions"] == ["blocked"]  # not a vacuous all([])
    assert app.audit() == 0


def test_dormant_and_trtl_are_lifecycle_not_semantic_growth():
    app, detector = engine()
    sid, birth = first_birth(app)
    previous = None
    for i in range(1, 35):
        turn(app, f"Welke andere apparaten zijn beschikbaar? {i}",
             "Geen nieuw experimenteel bewijs.")
        checkpoint = freeze_weightless_followup(app, birth, previous=previous)
        previous = checkpoint
        if checkpoint["seed_state_after_turn"]["status"] == "DORMANT":
            break
    else:
        raise AssertionError("existing TTL did not create DORMANT state")
    old_trace = checkpoint["seed_state_after_turn"]["trace"]
    observed = turn(app, "Welke klepstand hoort bij de druk?", "Nog onbekend.")
    assert sid in observed["reactivated_trtl"]
    revived = freeze_weightless_followup(app, birth, previous=previous)
    assert revived["trtl_reactivated_same_seed"] is True
    assert revived["seed_state_after_turn"]["trace"] > old_trace
    assert revived["seed_state_after_turn"]["status"] == "NEW"
    assert revived["seed_state_after_turn"]["weight"] == 0
    assert revived["seed_state_after_turn"]["occurrence_count"] == 1
    assert revived["semantic_growth_assessed"] is False
    assert detector.calls == app.turn


def test_terminal_dormant_ttl_expiry_is_observed_as_a_negative_path():
    app, _ = engine()
    sid, birth = first_birth(app)
    previous = None
    for i in range(1, 45):
        turn(app, f"Losstaande latere waarneming {i}", "Nog altijd geen nieuw bewijs.")
        checkpoint = freeze_weightless_followup(app, birth, previous=previous)
        previous = checkpoint
        if checkpoint["seed_state_after_turn"]["status"] == "EXPIRED":
            break
    else:
        raise AssertionError("normal dormant TTL never caused expiry")
    assert checkpoint["seed_id"] == sid
    assert checkpoint["seed_state_after_turn"]["weight"] == 0
    assert checkpoint["seed_state_after_turn"]["evidence_count"] == 0
    assert checkpoint["seed_state_after_turn"]["authority_version"] == 0
    assert "expired" in checkpoint["new_gate_decisions"]
    assert checkpoint["semantic_growth_assessed"] is False
    assert checkpoint["q1_or_q2_effect_established"] is False


@pytest.mark.parametrize("kind,error", [
    ("birth_hash", "birth snapshot hash"),
    ("wrong_seed", "original candidate text or origin"),
    ("previous_hash", "previous snapshot hash"),
    ("previous_history", "previous checkpoint is not the preceding history"),
    ("raw_item", "raw observation identity"),
    ("created", "first created-event"),
    ("answer", "ordinary answer route"),
    ("gate", "crossed the Gate authority boundary"),
    ("weight", "authority-free"),
    ("old_event", "previous event ledger prefix was modified"),
    ("old_gate", "previous event ledger prefix was modified"),
])
def test_tampered_turns_and_audit_history_fail_closed(monkeypatch, kind, error):
    app, _ = engine()
    _, birth = first_birth(app)
    turn(app, "Beurt 2")
    a = freeze_weightless_followup(app, birth)
    turn(app, "Beurt 3")
    state = deepcopy(app.export_state())
    b = deepcopy(birth)
    prev = deepcopy(a)
    if kind == "birth_hash":
        b["seed_id"] = "forged"
    elif kind == "wrong_seed":
        b["candidate_text_sha256"] = "0" * 64
        b = rehash(b)
        # Rebind the claimed previous checkpoint so this test reaches the
        # independent seed-text check, rather than an earlier hash mismatch.
        prev["birth_snapshot_sha256"] = b["snapshot_sha256"]
        prev = rehash(prev)
    elif kind == "previous_hash":
        prev["turn"] = 999
    elif kind == "previous_history":
        prev["history_sha256"] = "1" * 64
        prev = rehash(prev)
    elif kind == "raw_item":
        state["turn_reports"][0]["detected_candidates"][0] = "Forged raw item"
        # Match the new (falsified) historical report hash in the checkpoint.
        # The original observation ID must still reject the changed raw item.
        prev["history_sha256"] = sha256(json.dumps(
            state["turn_reports"][:2], ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
        prev = rehash(prev)
    elif kind == "created":
        for event in state["manager"]["event_log"]:
            if event["event_type"] == "created":
                event["detail"]["text"] = "wrong"
                break
    elif kind == "answer":
        state["turn_reports"][-1]["selected_seed_ids"] = [birth["seed_id"]]
    elif kind == "gate":
        state["manager"]["gate_events"].append({
            "seed_id": birth["seed_id"], "decision": "promoted",
            "weight_before": 0, "weight_after": 0.6,
            "authority_version": 1, "status_before": "NEW",
            "status_after": "PROMOTED",
        })
    elif kind == "weight":
        state["manager"]["seeds"][0]["weight"] = 0.6
    elif kind == "old_event":
        state["manager"]["event_log"].insert(0, {
            "seed_id": "unrelated", "event_type": "new", "detail": {},
        })
    elif kind == "old_gate":
        state["manager"]["gate_events"].insert(0, {
            "seed_id": "unrelated", "decision": "blocked",
        })
        # Supply a claimed previous Gate prefix to test its integrity check.
        # It is intentionally synthetic and cannot count as a real Gate run.
        prev["gate_log_count"] = 1
        prev["gate_log_sha256"] = "0" * 64
        prev = rehash(prev)
    else:
        raise AssertionError(kind)
    monkeypatch.setattr(app, "export_state", lambda: state)
    with pytest.raises(ValueError, match=error):
        freeze_weightless_followup(app, b, previous=prev)


def test_pending_turn_does_not_count_as_completed_followup():
    app, _ = engine()
    _, birth = first_birth(app)
    pending = app.prepare_turn("Nog niet geantwoord.")
    with pytest.raises(ValueError, match="finish or abort"):
        freeze_weightless_followup(app, birth)
    app.abort_turn(pending)
    assert app.turn == 1
