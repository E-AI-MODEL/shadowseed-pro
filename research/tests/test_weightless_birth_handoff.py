"""Mechanics-only canonical birth handoff: NO model, novelty or Q1/Q2 result.

Use the existing real ShadowseedEngine, manager, parser/intake and event log;
all host answers and detector proposals are authored test inputs. One
persistent session runs over multiple genuine prepare/observe turns.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

import numpy as np
import pytest

from shadowseed import ShadowseedEngine
from shadowseed_research.benchmark.weightless_birth_handoff import (
    SCHEMA,
    freeze_canonical_weightless_birth,
)

QUESTION = "Welke meting hebben we in kamer B?"
ANSWER = "Er is één drukmeting beschikbaar."
CANDIDATE = "Hoe verandert een niet-gekende klepstand de druk in kamer B?"


class ScriptedDetector:
    name = "INVESTIGATOR-SCRIPTED-NO-MODEL"
    prompt_variant = "scripted_candidate"

    def __init__(self, proposed: str | None) -> None:
        self.proposed = proposed
        self.calls = 0

    def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
        assert isinstance(item["question"], str)
        assert isinstance(item["text"], str)
        assert isinstance(item["conversation_context"], str)
        self.calls += 1
        return [self.proposed] if self.calls == 1 and self.proposed else []


def toy_embedding(text: str) -> np.ndarray:
    """Synthetic vectors for identity/transport only, not semantic similarity."""
    lowered = text.lower()
    return np.array(
        [1.0, 0.0] if "druk" in lowered or "klep" in lowered
        else [0.0, 1.0], dtype=float
    )


def engine(proposal: str | None) -> tuple[ShadowseedEngine, ScriptedDetector]:
    scripted = ScriptedDetector(proposal)
    app = ShadowseedEngine(
        detector_backend=scripted,
        embedding_fn=toy_embedding,
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    return app, scripted


def complete_turn(app: ShadowseedEngine, question: str, answer: str) -> dict:
    pending = app.prepare_turn(question)
    assert pending.model_context == ""
    assert pending.surfaced_seed_ids == ()
    report = app.observe_turn(pending, answer)
    assert report["answer"] == answer
    return report


def test_actual_seed_birth_is_frozen_with_no_authority_or_causal_claim() -> None:
    seeded, detector = engine(CANDIDATE)
    empty, empty_detector = engine(None)
    first = complete_turn(seeded, QUESTION, ANSWER)
    none = complete_turn(empty, QUESTION, ANSWER)
    assert not none["seeds_born_weightless"]
    assert len(first["seeds_born_weightless"]) == 1
    sid = first["seeds_born_weightless"][0]

    before_state = deepcopy(seeded.export_state())
    handoff = freeze_canonical_weightless_birth(seeded, first, sid)
    assert seeded.export_state() == before_state
    assert handoff["schema"] == SCHEMA
    assert handoff["session_turn"] == 0
    assert handoff["seed_id"] == sid
    assert handoff["candidate_text_sha256"] == sha256(
        CANDIDATE.encode("utf-8")
    ).hexdigest()
    assert "candidate_text" not in handoff
    assert len(handoff["snapshot_sha256"]) == 64
    assert handoff["origin"]["context_ref"] == "turn:0:visible_answer"
    assert handoff["origin"]["detection_basis"] == "visible_answer_non_ssl_attributed"
    assert handoff["authority_at_birth"]["weight"] == 0
    assert handoff["authority_at_birth"]["evidence_count"] == 0
    assert handoff["authority_at_birth"]["occurrence_count"] == 1
    assert handoff["authority_at_birth"]["authority_version"] == 0
    assert handoff["ordinary_answer_model_was_not_seed_exposed"] is True
    assert handoff["origin_of_visible_answer_not_verified"] is True
    assert handoff["candidate_origin_is_observed_not_independently_validated"] is True
    assert handoff["raw_detector_item_to_seed_mapping_verified"] is True
    assert handoff["raw_to_seed_link_scope"] == (
        "recorded_canonical_item_to_first_birth"
    )
    lineage = handoff["raw_to_seed_item_lineage"]
    assert lineage["raw_candidate_index"] == 0
    assert lineage["normalized_index"] == 0
    assert lineage["normalized_candidate_sha256"] == sha256(
        CANDIDATE.encode("utf-8")
    ).hexdigest()
    assert len(lineage["observation_id"]) > 16
    assert len(lineage["item_lineage_record_sha256"]) == 64
    assert len(lineage["observation_record_sha256"]) == 64
    assert handoff["detector_observation_count"] == 1
    assert handoff["subsequent_inquiry_generated"] is False
    assert handoff["independent_question_or_evidence_review"] is False
    assert handoff["q1_or_q2_effect_established"] is False
    assert handoff["eligible_for_automatic_gate_or_prompt"] is False
    assert seeded.inspect()["influence_records"] == []
    assert seeded._session.manager.gate_events == []
    assert seeded.audit() == empty.audit() == 0
    assert detector.calls == empty_detector.calls == 1


def test_same_candidate_identity_over_multiple_real_turns_is_not_a_new_question() -> None:
    seeded, _ = engine(CANDIDATE)
    none, _ = engine(None)
    first = complete_turn(seeded, QUESTION, ANSWER)
    complete_turn(none, QUESTION, ANSWER)
    sid = first["seeds_born_weightless"][0]
    old_handoff = freeze_canonical_weightless_birth(seeded, first, sid)
    original_text = seeded.inspect()["seeds"][0]["text"]

    for question, answer in (
        ("Wat ontbreekt aan de drukmeting?", "Geen nieuwe informatie."),
        ("Wat zegt de proef?", "De observatie blijft onbeslist."),
    ):
        later = complete_turn(seeded, question, answer)
        control = complete_turn(none, question, answer)
        assert later["answer"] == control["answer"]
        assert later["seeds_born_weightless"] == []
        assert not control["seeds_born_weightless"]
        assert not later["promoted_this_turn"]
        assert not later["surfaced_seed_ids"]
        assert not seeded._session.manager.gate_events
        current = seeded.inspect()["seeds"][0]
        assert current["id"] == sid
        assert current["text"] == original_text
        assert current["weight"] == 0
        assert current["evidence_count"] == 0
        assert current["occurrence_count"] == 1
        assert not seeded.inspect()["influence_records"]
        assert not none.inspect()["seeds"]
        with pytest.raises(ValueError, match="latest canonical"):
            freeze_canonical_weightless_birth(seeded, first, sid)
        with pytest.raises(ValueError, match="was not accepted"):
            freeze_canonical_weightless_birth(seeded, later, sid)

    assert old_handoff["session_turn"] == 0
    assert old_handoff["subsequent_inquiry_generated"] is False


def test_true_birth_and_later_acceptance_are_not_interchangeable() -> None:
    class Repeats(ScriptedDetector):
        def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
            self.calls += 1
            return [CANDIDATE]

    eng, _ = engine(CANDIDATE)
    eng._session.detector = Repeats(CANDIDATE)
    first = complete_turn(eng, QUESTION, ANSWER)
    sid = first["seeds_born_weightless"][0]
    later = complete_turn(eng, "Nog steeds die druk?", "Onbeslist.")
    assert later["seeds_born_weightless"] == [sid]
    assert eng._session.manager.get_seed(sid).occurrence_count == 2
    with pytest.raises(ValueError, match="accepted recurrence"):
        freeze_canonical_weightless_birth(eng, later, sid)


def test_tampering_with_report_or_origin_cannot_create_a_forged_birth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eng, _ = engine(CANDIDATE)
    first = complete_turn(eng, QUESTION, ANSWER)
    sid = first["seeds_born_weightless"][0]
    modified = deepcopy(first)
    modified["answer"] = "A later rewritten answer"
    with pytest.raises(ValueError, match="latest canonical"):
        freeze_canonical_weightless_birth(eng, modified, sid)

    real_export = eng.export_state

    def corrupt_origin() -> dict:
        snapshot = real_export()
        wrong = deepcopy(snapshot)
        wrong["manager"]["seeds"][0]["origin"]["context_ref"] = "turn:99"
        return wrong

    monkeypatch.setattr(eng, "export_state", corrupt_origin)
    with pytest.raises(ValueError, match="seed origin"):
        freeze_canonical_weightless_birth(eng, first, sid)
    monkeypatch.setattr(eng, "export_state", real_export)

    def corrupt_created_event() -> dict:
        wrong = deepcopy(real_export())
        for event in wrong["manager"]["event_log"]:
            if event["event_type"] == "created" and event["seed_id"] == sid:
                event["detail"]["text"] = "forged"
                break
        return wrong

    monkeypatch.setattr(eng, "export_state", corrupt_created_event)
    with pytest.raises(ValueError, match="created event"):
        freeze_canonical_weightless_birth(eng, first, sid)


def test_none_abort_and_missing_seed_fail_closed() -> None:
    blank, _ = engine(None)
    none = complete_turn(blank, QUESTION, ANSWER)
    with pytest.raises(ValueError, match="was not accepted"):
        freeze_canonical_weightless_birth(blank, none, "ss_001")

    seeded, _ = engine(CANDIDATE)
    pending = seeded.prepare_turn(QUESTION)
    with pytest.raises(ValueError, match="complete or abort"):
        freeze_canonical_weightless_birth(seeded, {}, "ss_001")
    seeded.abort_turn(pending)
    assert seeded.turn == 0
    assert not seeded.inspect()["seeds"]


def test_opt_in_candidate_text_stays_separate_from_authority() -> None:
    eng, _ = engine(CANDIDATE)
    first = complete_turn(eng, QUESTION, ANSWER)
    sid = first["seeds_born_weightless"][0]
    plain = freeze_canonical_weightless_birth(eng, first, sid)
    include = freeze_canonical_weightless_birth(
        eng, first, sid, include_candidate_text=True
    )
    assert include["candidate_text"] == CANDIDATE
    assert "candidate_text" not in plain
    assert include["snapshot_sha256"] != plain["snapshot_sha256"]
    assert include["eligible_for_automatic_gate_or_prompt"] is False
    assert eng._session.manager.get_seed(sid).weight == 0
    assert not eng._session.manager.gate_events


def test_diagnostic_snapshot_is_json_serializable_without_hidden_model_calls() -> None:
    eng, detector = engine(CANDIDATE)
    first = complete_turn(eng, QUESTION, ANSWER)
    sid = first["seeds_born_weightless"][0]
    snapshot = freeze_canonical_weightless_birth(eng, first, sid)
    assert json.loads(json.dumps(snapshot, ensure_ascii=False)) == snapshot
    assert detector.calls == 1
    assert eng.inspect()["turns"] == 1


def test_duplicate_raw_items_do_not_lose_first_birth_attribution() -> None:
    OTHER = "Welke onbekende variabele bepaalt de temperatuur in kamer C?"

    class Multiple(ScriptedDetector):
        def detect_seeds(self, item: dict, max_seeds: int = 5) -> list[str]:
            self.calls += 1
            return [CANDIDATE, CANDIDATE, OTHER]

    eng, _ = engine(None)
    eng._session.detector = Multiple(None)
    first = complete_turn(eng, QUESTION, ANSWER)
    assert len(first["seeds_born_weightless"]) == 2
    assert len(first["candidate_observations"]) == 3
    assert [
        row["outcome"] for row in first["intake_diagnostics"]["item_lineage"]
    ] == ["accepted", "rejected", "accepted"]

    a, b = first["seeds_born_weightless"]
    first_birth = freeze_canonical_weightless_birth(eng, first, a)
    other_birth = freeze_canonical_weightless_birth(eng, first, b)
    assert first_birth["raw_to_seed_item_lineage"]["raw_candidate_index"] == 0
    assert other_birth["raw_to_seed_item_lineage"]["raw_candidate_index"] == 2
    assert (
        first_birth["raw_to_seed_item_lineage"]["observation_id"]
        != other_birth["raw_to_seed_item_lineage"]["observation_id"]
    )
    assert first_birth["raw_detector_item_to_seed_mapping_verified"]
    assert other_birth["raw_detector_item_to_seed_mapping_verified"]
    assert eng._session.manager.get_seed(a).weight == 0
    assert eng._session.manager.get_seed(b).weight == 0
    assert not eng._session.manager.gate_events


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("drop_schema", "exact canonical item lineage"),
        ("drop_item_rows", "item lineage, raw detector items"),
        ("unresolved_adapter", "exact canonical item lineage"),
        ("duplicate_accepted", "first-birth item lineage missing or ambiguous"),
        ("bad_raw_index", "raw or normalized item index"),
        ("bad_normalized_index", "raw or normalized item index"),
        ("bad_raw_observation_id", "raw observation identity"),
        ("missing_observation", "raw observation is missing"),
        ("fake_transition", "item lineage lacks exact source"),
        ("incorrect_raw_text", "raw observation identity"),
        ("fake_source_status", "item lineage lacks exact source"),
    ],
)
def test_missing_or_corrupt_item_provenance_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    expected_error: str,
) -> None:
    eng, _ = engine(CANDIDATE)
    original = complete_turn(eng, QUESTION, ANSWER)
    sid = original["seeds_born_weightless"][0]
    altered = deepcopy(eng.export_state())
    report = altered["turn_reports"][-1]
    diagnostics = report["intake_diagnostics"]
    item = diagnostics["item_lineage"][0]

    if mutation == "drop_schema":
        diagnostics.pop("lineage_schema")
    elif mutation == "drop_item_rows":
        diagnostics.pop("item_lineage")
    elif mutation == "unresolved_adapter":
        diagnostics["lineage_status"] = "unresolved_normalizer_override"
    elif mutation == "duplicate_accepted":
        diagnostics["item_lineage"].append(deepcopy(item))
    elif mutation == "bad_raw_index":
        item["raw_candidate_index"] = 10
    elif mutation == "bad_normalized_index":
        item["normalized_index"] = 10
    elif mutation == "bad_raw_observation_id":
        item["observation_id"] = "obs_forged"
    elif mutation == "missing_observation":
        report["candidate_observations"] = [{
            **observation, "observation_id": "obs_unrelated"
        } for observation in report["candidate_observations"]]
    elif mutation == "fake_transition":
        item["seed_transition"] = "deduplicated"
    elif mutation == "incorrect_raw_text":
        report["detected_candidates"][0] = "rewritten raw detector text"
    elif mutation == "fake_source_status":
        item["source_mapping_status"] = "unresolved_normalizer_mismatch"
    else:
        raise AssertionError("Unexpected mutation")

    # Replacing BOTH supplied and exported reports prevents the usual
    # latest-report guard from hiding flaws in the item-level verifier.
    monkeypatch.setattr(eng, "export_state", lambda: altered)
    with pytest.raises(ValueError, match=expected_error):
        freeze_canonical_weightless_birth(eng, report, sid)


def test_previous_product_reports_without_item_lineage_remain_unverifiable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eng, _ = engine(CANDIDATE)
    first = complete_turn(eng, QUESTION, ANSWER)
    sid = first["seeds_born_weightless"][0]
    past = deepcopy(eng.export_state())
    del past["turn_reports"][-1]["intake_diagnostics"]["item_lineage"]
    monkeypatch.setattr(eng, "export_state", lambda: past)
    with pytest.raises(ValueError, match="item lineage"):
        freeze_canonical_weightless_birth(eng, past["turn_reports"][-1], sid)
    assert eng._session.manager.get_seed(sid).weight == 0
    assert not eng._session.manager.gate_events
