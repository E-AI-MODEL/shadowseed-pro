"""Pro research event ledger: no semantic scoring or authority mutation."""
import copy
import json

import pytest

from research.scripts.pro_shadow_relation_observations import (
    record_observation,
    safe_aggregate,
)


def test_unjudged_relation_preserves_immutable_source_ids_and_no_authority():
    state = {"seeds": [{
        "id": "ss_004", "scope_status": "unresolved", "weight": 0.0,
        "text": "Welke rol hebben klok, batterij en bewegingssensor terwijl hun afhankelijkheden nog onbekend zijn?",
        "trace": 1.1, "status": "ACTIVE",
    }]}
    frozen = copy.deepcopy(state)
    event = record_observation(
        pro_state=state, source_seed_ids=["ss_004"],
        observer="research_sidecar_model (unverified reporter)",
        source_ref="synthetic:turn:5", turn_index=5, event_index=0,
        proposed_text="Een samenhang tussen meerdere begrippen mag langer zijn dan een zinsnede; mogelijke latere afhankelijkheden blijven nog onbewezen. " * 5,
    )
    assert state == frozen
    assert event["seed_origins"][0]["id"] == "ss_004"
    assert event["semantic_verdict"] is None
    assert event["originality_verdict"] is None
    assert event["authority_contribution"] == 0
    assert event["host_answer_influence"] is False
    assert event["proposed_text"].count("afhankelijkheden") == 5
    public = safe_aggregate([event])
    assert "batterij" not in json.dumps(public)
    assert "unverified" not in json.dumps(public)
    assert "synthetic:turn:5" not in json.dumps(public)


def test_no_relation_is_retained_as_real_negative_outcome():
    state = {"seeds": [{"id": "ss_006", "scope_status": "bounded", "weight": 0, "text": "Unverified possibility."}]}
    event = record_observation(pro_state=state, source_seed_ids=["ss_006"], observer="test", source_ref="test:no-result", turn_index=7, event_index=1, proposed_text=None)
    assert event["event_type"] == "no_proposal"
    assert safe_aggregate([event])["by_event_type"] == {"no_proposal": 1}


def test_unknown_seed_and_nonweightless_record_rejected():
    state = {"seeds": [{"id": "ss_006", "scope_status": "bounded", "weight": .9, "text": "Unverified possibility."}]}
    args = dict(pro_state=state, source_seed_ids=["ss_006"], observer="test", source_ref="test", turn_index=1, event_index=0, proposed_text="New possibility")
    with pytest.raises(ValueError, match="weightless"):
        record_observation(**args)
    args["source_seed_ids"] = ["unknown"]
    with pytest.raises(ValueError, match="unknown source"):
        record_observation(**args)


def test_actual_pro_engine_checkpoint_observation_does_not_change_seed_state():
    import numpy as np
    from shadowseed import ShadowseedEngine

    class FrozenCandidate:
        name = "offline-replay"
        prompt_variant = "current_pair"

        def detect_seeds(self, _item, max_seeds=5):
            return ["De camera kan afwijken. De bewegingssensor gebruikt mogelijk een gedeelde voeding."]

    engine = ShadowseedEngine(
        detector_backend=FrozenCandidate(),
        embedding_fn=lambda _text: np.array([1.0, 0.0]),
        recurrence_mode="pairwise",
        gate_policy_id="evidence_backed",
    )
    p = engine.prepare_turn("Wat zegt de bron?")
    assert p.model_context == ""
    observed = engine.observe_turn(p, "Een voorlopige technische beschrijving zonder bewijs.")
    assert len(observed["seeds_born_unresolved"]) == 1
    sid = observed["seeds_born_unresolved"][0]
    before = engine.export_state()
    event = record_observation(
        pro_state=engine.inspect(), source_seed_ids=[sid],
        observer="independent_research_sidecar_test", source_ref="synthetic:followup:1",
        turn_index=1, event_index=0, proposed_text=None,
    )
    assert event["event_type"] == "no_proposal"
    assert engine.export_state() == before
    assert engine.inspect()["seeds"][0]["weight"] == 0
    assert engine.audit() == 0
