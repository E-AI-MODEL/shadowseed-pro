"""Offline-only structural tests, using a fake provider with REAL Engine/Gate."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
import pytest

from shadowseed_research.benchmark.g0_dual_model_ab import (
    CASE_COUNT, MODEL_IDS, MODEL_CALL_CAP, TOKEN_CAP,
    DualModelProvider, run_model_case, run_comparison,
    make_seed_hidden_review, validate_trial,
)
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    HOST_INSTRUCTIONS, DETECTOR_INSTRUCTIONS,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import NOTES_INSTRUCTIONS

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/g0_gpt5_luna_dual_model_v1.json"
CANDIDATE = (
    "1. Onbekend of verschillen in opnamevolgorde of observatiepositie "
    "een alternatieve verklaring geven voor de gemelde discrepantie, "
    "zonder dat deze relatie al onafhankelijk is getoetst."
)

def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))

class FakeDualProvider(DualModelProvider):
    def __init__(self, model_id, cid, *, fail_at=None, wrong_model=False):
        super().__init__("TEST_NOT_A_REAL_KEY", model_id=model_id)
        self.cid, self.fail_at, self.wrong_model = cid, fail_at, wrong_model
        self.detector_count = 0
        self.response_count = 0
        self.requests = []

    def _post(self, endpoint, payload):
        if endpoint == "embeddings":
            arr = np.zeros(1536, dtype=float)
            idx = int(sha256(payload["input"][0].encode()).hexdigest()[:6], 16) % 1536
            arr[idx] = 1.
            return {"data": [{"index": 0, "embedding": arr.tolist()}],
                    "usage": {"total_tokens": 12}}
        assert endpoint == "responses"
        assert payload["model"] == self.model_id
        assert payload["store"] is False
        assert payload["reasoning"] == {"effort": "low"}
        assert payload["max_output_tokens"] == 4096
        self.response_count += 1
        self.requests.append(deepcopy(payload))
        if self.response_count == self.fail_at:
            raise RuntimeError("simulated provider error")
        instr = payload["instructions"]
        if instr == DETECTOR_INSTRUCTIONS:
            self.detector_count += 1
            if self.cid.endswith("06"):
                reply = "NONE"
            elif self.cid.endswith("02") and self.detector_count == 1:
                reply = "NONE"
            elif self.detector_count == (2 if self.cid.endswith("02") else 1):
                reply = CANDIDATE
            else:
                reply = "NONE"
        elif instr == HOST_INSTRUCTIONS:
            reply = ("Er zijn meerdere mogelijke verklaringen. "
                     "Er is nog geen onafhankelijke toets uitgevoerd.")
        elif instr == NOTES_INSTRUCTIONS:
            reply = "Nog geen onafhankelijk bewijs; bewaar gewone waarnemingen."
        else:
            reply = json.dumps({
                "status": "questions",
                "proposals": [{
                    "question": "Kan een tweede onafhankelijke waarneming onderscheiden?",
                    "test": "Vergelijk twee condities blind.",
                    "depends_on": "Deze tweede waarneming is nog niet beschikbaar.",
                }],
                "unresolved_alternatives": ["Een andere conditie blijft mogelijk."],
            }, ensure_ascii=False)
        return {
            "id": f"fake-{self.cid}-{self.response_count}",
            "model": "OTHER" if self.wrong_model else payload["model"],
            "status": "completed",
            "usage": {"input_tokens": 140, "output_tokens": 140},
            "output": [{"content": [{"type": "output_text", "text": reply}]}],
        }


def test_protocol_pins_models_cases_cost_caps_and_no_winner():
    d = fixture()
    cs = validate_trial(d)
    assert len(cs) == CASE_COUNT == 6
    assert d["model_ids"] == list(MODEL_IDS)
    assert len({x["family"] for x in cs}) == 4
    assert cs[-1]["family"] == "negative_no_opportunity"
    assert all(len(x["turns"]) == 4 for x in cs)
    assert not d["independent_evaluation_completed"]


def test_pinned_luna_provider_and_reject_mismatched_model():
    p = FakeDualProvider(MODEL_IDS[1], "DM26-C01")
    p.generate(stage="test",case_id=p.cid,prompt="fake",instructions=HOST_INSTRUCTIONS)
    assert p.events[-1]["requested_model"] == MODEL_IDS[1]
    assert p.events[-1]["returned_model"] == MODEL_IDS[1]
    assert p.events[-1]["model_identity_match"]
    assert p.model_calls == 1 and p.total_tokens == 280
    assert p.model_call_cap == MODEL_CALL_CAP
    bad = FakeDualProvider(MODEL_IDS[1], "DM26-C01", wrong_model=True)
    with pytest.raises(RuntimeError,match="identity"):
        bad.generate(stage="test",case_id=bad.cid,prompt="fake",instructions=HOST_INSTRUCTIONS)


def test_real_engine_birth_T0_and_two_AB_rounds_no_answer_influence():
    c = fixture()["cases"][0]
    p = FakeDualProvider(MODEL_IDS[0],c["id"])
    r = run_model_case(c,p,arm_order=("A","B"))
    assert r["status"] == "complete_pair_birth_T0"
    assert r["first_seed"]["birth_turn"] == 0
    assert r["birth"]["raw_detector_item_to_seed_mapping_verified"]
    assert r["first_seed"]["weight"] == 0
    assert len(r["turns"]) == 4
    assert all(x["ordinary_control_identical"] for x in r["turns"])
    assert all(x["followup"]["seed_state_after_turn"]["weight"] == 0
               for x in r["turns"][1:])
    inquiries = [x for x in p.requests if x["instructions"] not in
                 (HOST_INSTRUCTIONS,DETECTOR_INSTRUCTIONS,NOTES_INSTRUCTIONS)]
    assert len(inquiries) == 4
    seed = r["first_seed"]["text"]
    assert sum(seed in x["input"] for x in inquiries) == 2
    assert all(seed not in x["input"] for x in p.requests
               if x["instructions"] == HOST_INSTRUCTIONS)
    assert p.model_calls == 15 and p.total_tokens < TOKEN_CAP


def test_real_engine_T1_birth_has_inquiry_at_T2_and_T3():
    c=fixture()["cases"][1]
    p=FakeDualProvider(MODEL_IDS[1],c["id"])
    r=run_model_case(c,p,arm_order=("B","A"))
    assert r["status"]=="complete_pair_birth_T1"
    assert r["first_seed"]["birth_turn"]==1
    assert all(not t["research_arms"] for t in r["turns"][:2])
    assert all(len(t["research_arms"])==2 for t in r["turns"][2:])
    assert r["turns"][3]["followup"]["seed_state_after_turn"]["weight"]==0


def test_no_birth_is_not_a_fake_null_AB():
    c=fixture()["cases"][-1]
    p=FakeDualProvider(MODEL_IDS[0],c["id"])
    r=run_model_case(c,p,arm_order=("A","B"))
    assert r["status"]=="no_seed_at_any_turn"
    assert r["first_seed"] is None
    assert not any(t["research_arms"] for t in r["turns"])
    assert p.model_calls==11


def test_full_two_model_case_census_including_negatives():
    d=run_comparison(fixture(),lambda m,c:FakeDualProvider(m,c))
    assert d["G0"]=="NOT_PASSED"
    assert d["counts"]["all_model_case_trajectories_attempted"]==12
    assert d["counts"]["full_two_round_AB_trajectories"]==10
    assert len({(x["case_id"],x["model_id"]) for x in d["cases"]})==12
    assert sum(d["counts"]["status_counts"].values())==12
    assert d["counts"]["provider_model_calls_attempted"]<=12*MODEL_CALL_CAP
    assert d["counts"]["provider_reported_tokens"]<=12*TOKEN_CAP
    assert not d["q2_new_later_investigability_proven"]
    assert not d["independent_human_review_completed"]
    for c in fixture()["cases"]:
        allocated=d["randomized_balanced_arm_allocation"][c["id"]]
        assert allocated[MODEL_IDS[0]][0]!=allocated[MODEL_IDS[1]][0]
    blind,owner=make_seed_hidden_review(d,fixture())
    assert blind["blind_group_count"]==10
    assert owner["blind_track_count"]==20
    assert blind["human_reviews_received"]==0
    text=json.dumps(blind,ensure_ascii=False)
    assert "gpt-6-luna" not in text
    assert "gpt-5-2025-08-07" not in text
    assert CANDIDATE[3:] not in text
    assert '"seed_text":' not in text
    assert '"arm":' not in text
    assert '"ordinary_note":' not in text


def test_failed_model_request_keeps_full_denominator_and_no_zero_effect():
    def factory(m,c):
        return FakeDualProvider(
            m,c,fail_at=6 if (m==MODEL_IDS[1] and c.endswith("03")) else None
        )
    d=run_comparison(fixture(),factory)
    assert d["counts"]["all_model_case_trajectories_attempted"]==12
    assert d["counts"]["status_counts"]["failed_partial_not_zero"]==1
    failed=[x for x in d["cases"] if x["status"]=="failed_partial_not_zero"]
    assert failed[0]["not_a_measured_zero_effect"]


@pytest.mark.parametrize("mutation",[
    "change_model","remove_case","future_T0","increase_calls",
    "fake_review","expected_seed",
])
def test_protocol_changes_fail_closed(mutation):
    d=fixture()
    if mutation=="change_model":d["model_ids"][1]="gpt-6-astra"
    elif mutation=="remove_case":d["cases"].pop()
    elif mutation=="future_T0":d["cases"][0]["turns"][0]["new_observation"]="future leak"
    elif mutation=="increase_calls":d["study_invariants"]["per_model_case_max_model_calls"]=99
    elif mutation=="fake_review":d["independent_evaluation_completed"]=True
    elif mutation=="expected_seed":d["cases"][0]["expected_seed"]="invented"
    with pytest.raises(ValueError):validate_trial(d)
