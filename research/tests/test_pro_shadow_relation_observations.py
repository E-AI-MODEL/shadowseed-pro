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
