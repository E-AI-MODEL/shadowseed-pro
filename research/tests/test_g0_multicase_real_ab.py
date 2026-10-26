"""Strict no-network multi-case RF A/B tests through REAL ShadowseedEngine.

No synthetic output here is scientific evidence. Fake provider only verifies
the real Engine/Detector/intake/birth/longitudinal/Gate mechanics and precise
paired question exposure, dropout and no-opportunity handling.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from shadowseed_research.benchmark.g0_multicase_real_ab import (
    AB_ORDERS, ARMS, CALL_CAP, CASE_COUNT, EMBED_CAP, OUTPUT_CAP,
    TOKEN_CAP, _parse_research, research_prompt, run_case, run_study,
    review_packets, validate_design,
)
from shadowseed_research.benchmark.real_model_stage1_exploratory import (
    BoundedProvider, DETECTOR_INSTRUCTIONS, HOST_INSTRUCTIONS,
)
from shadowseed_research.benchmark.real_seed_rf_inquiry import NOTES_INSTRUCTIONS

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "g0_multicase_real_ab_v1.json"
RAW_CANDIDATE = (
    "1. Onbekend of verschillen in opnamevolgorde of observatiepositie "
    "een alternatieve verklaring geven voor de gemelde discrepantie, "
    "zonder dat deze relatie al onafhankelijk is getoetst."
)


def fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FakeProvider(BoundedProvider):
    def __init__(self, cid, *, no_birth=False, fail_at=None, malformed=False):
        super().__init__(
            "TEST_ONLY", model_call_cap=CALL_CAP,
            embedding_call_cap=EMBED_CAP, all_token_cap=TOKEN_CAP,
            output_token_cap=OUTPUT_CAP)
        self.cid = cid
        self.no_birth = no_birth
        self.fail_at = fail_at
        self.malformed = malformed
        self.detector_calls = 0
        self.calls = []
        self.serial = 0

    def _post(self, endpoint, payload):
        if endpoint == "embeddings":
            v = np.zeros(1536, dtype=float)
            index = int(sha256(payload["input"][0].encode()).hexdigest()[:6], 16) % 1536
            v[index] = 1.0
            return {"data": [{"index": 0, "embedding": v.tolist()}],
                    "usage": {"total_tokens": 15}}
        assert endpoint == "responses"
        self.serial += 1
        self.calls.append((payload["instructions"], payload["input"]))
        if self.serial == self.fail_at:
            return {
                "id": "fake-incomplete", "model": "gpt-5",
                "status": "incomplete",
                "usage": {"input_tokens": 50, "output_tokens": 70},
                "output": [],
            }
        if payload["instructions"] == DETECTOR_INSTRUCTIONS:
            self.detector_calls += 1
            if self.no_birth or self.detector_calls > 1:
                raw = "NONE"
            else:
                raw = RAW_CANDIDATE
        elif payload["instructions"] == HOST_INSTRUCTIONS:
            raw = ("Er zijn verscheidene voorlopige verklaringen voor het verschil. "
                   "Een oorzaak of een extra verband is niet onafhankelijk vastgesteld.")
        elif payload["instructions"] == NOTES_INSTRUCTIONS:
            raw = "Er is een verschil gemeld; onafhankelijke verificatie ontbreekt."
        else:
            if self.malformed:
                raw = "niet geldig json"
            else:
                raw = json.dumps({
                    "status": "questions",
                    "proposals": [{
                        "question": "Kan een onafhankelijk tweede meetmoment de alternatieven onderscheiden?",
                        "test": "Leg nieuwe afzonderlijke metingen vast en vergelijk per conditie.",
                        "depends_on": "De gegevens zijn nog niet beschikbaar.",
                    }],
                    "unresolved_alternatives": [
                        "Mogelijk speelt een andere volgorde of conditie een rol."
                    ],
                })
        return {
            "id": f"fake-{self.cid}-{self.serial}", "model": "gpt-5",
            "status": "completed",
            "usage": {"input_tokens": 140, "output_tokens": 140},
            "output": [{"content": [{"type": "output_text", "text": raw}]}],
        }


def test_fixture_families_no_preselected_winner_and_original_thesis_preserved():
    d = fixture()
    cs = validate_design(d)
    assert len(cs) == 6 and cs[-1]["family"] == "negative_no_opportunity"
    assert len({c["family"] for c in cs}) == 4
    assert len(AB_ORDERS) == len(cs)
    assert sum(x[0] == "A" for x in AB_ORDERS) == 3
    assert sum(x[0] == "B" for x in AB_ORDERS) == 3
    assert not any("winner" in c or "expected_seed" in c for c in cs)


def test_one_real_engine_three_turns_exact_exposure_and_own_prior_questions():
    c = validate_design(fixture())[0]
    p = FakeProvider(c["id"])
    result = run_case(c, p)
    assert result["status"] == "completed_exploratory_pair"
    assert result["first_seed"]["weight"] == 0
    assert result["first_seed"]["birth_turn"] == 0
    assert result["birth"]["raw_detector_item_to_seed_mapping_verified"]
    assert len(result["ordinary_t0_samples"]) == 2
    assert [x["turn"] for x in result["turns"]] == [0, 1, 2]
    for t in result["turns"][1:]:
        assert t["followup"]["seed_state_after_turn"]["weight"] == 0
        assert t["followup"]["seed_state_after_turn"]["evidence_count"] == 0
        assert set(t["research_arms"]) == set(ARMS)
        assert all(v["parsed"]["status"] == "valid_questions"
                   for v in t["research_arms"].values())
        assert not t["followup"]["product_answer_seed_influence_observed"]
    assert all(t["ordinary_control_identical"] for t in result["turns"])
    assert p.model_calls == 13
    assert 0 < p.embedding_calls <= EMBED_CAP
    # Both research arms use ONE set of normal notes, same instruction,
    # and their OWN prior inquiry only at T2; no future observation at T1.
    seed = result["first_seed"]["text"]
    inquiries = [(i, s) for i, (instructions, s) in enumerate(p.calls)
                 if instructions not in (HOST_INSTRUCTIONS,
                                          DETECTOR_INSTRUCTIONS,
                                          NOTES_INSTRUCTIONS)]
    assert len(inquiries) == 4
    at_t1 = [(i, s) for i, s in inquiries if
             "EIGEN EERDERE ONDERZOEKSVRAGEN T1" not in s]
    assert len(at_t1) == 2
    assert sum(seed in s for _, s in inquiries) == 2
    assert all("DEZELFDE GEWONE AANTEKENING T0" in s for _, s in inquiries)
    assert all(c["turns"][2]["new_observation"] not in s for _, s in at_t1)


def test_negative_no_opportunity_does_not_get_a_fake_seed_or_AB_pair():
    c = validate_design(fixture())[-1]
    p = FakeProvider(c["id"], no_birth=True)
    d = run_case(c, p)
    assert d["status"] == "completed_no_T0_seed_no_AB_opportunity"
    assert d["first_seed"] is None
    assert not any(t["research_arms"] for t in d["turns"])
    assert p.model_calls == 9


def test_every_predeclared_case_attempted_even_when_one_fails():
    providers = {}
    def factory(cid):
        p = FakeProvider(cid, no_birth=cid.endswith("06"),
                         fail_at=8 if cid.endswith("02") else None)
        providers[cid] = p
        return p
    snapshots = []
    result = run_study(fixture(), factory,
                       on_change=lambda d: snapshots.append(deepcopy(d)))
    assert result["G0"] == "NOT_PASSED"
    assert result["study_counts"]["cases_attempted"] == CASE_COUNT
    assert result["study_counts"]["case_pairs_completed"] == 4
    assert result["study_counts"]["no_birth_opportunities"] == 1
    assert result["study_counts"]["failed_or_incomplete"] == 1
    assert result["status"] == "completed_exploratory_with_gaps"
    failed = result["cases"][1]
    assert failed["status"] == "failed_incomplete_not_zero_effect"
    assert failed["not_an_independent_negative_finding"] is True
    assert failed["provider"]["model_calls_attempted"] == 8
    assert len(result["cases"]) == 6
    assert len(snapshots) > 30
    blind, owner = review_packets(result)
    assert len(blind["case_groups"]) == 4
    assert len(owner["sample_to_arm"]) == 16
    assert all(not any("arm" in z for z in y["outputs"])
               for c in blind["case_groups"] for y in c["paired_outputs"])


def test_none_invalid_responses_not_fabricated_as_study_success():
    assert _parse_research('{"status":"none","proposals":[],"unresolved_alternatives":[]}')[
        "status"] == "valid_none"
    assert _parse_research('{"status":"questions","proposals":[],"unresolved_alternatives":[]}')[
        "status"] == "invalid"
    assert _parse_research("not json")["status"] == "invalid"
    assert _parse_research('{"status":"questions","proposals":[{"question":"x",'
                           '"test":"y","depends_on":"z"}],'
                           '"unresolved_alternatives":[]}')["status"] == "invalid"


@pytest.mark.parametrize("mutation", [
    "future_at_T0", "missing_negative", "case_reordered",
    "fake_expected_seed", "expand_budget", "fake_G0", "missing_family",
])
def test_fixture_fails_closed_on_outcome_leak_or_scope_expansion(mutation):
    d = fixture()
    if mutation == "future_at_T0":
        d["cases"][0]["turns"][0]["new_observation"] = "new future measurement"
    elif mutation == "missing_negative":
        d["cases"][-1]["family"] = "instrument_affordance"
    elif mutation == "case_reordered":
        d["cases"][0], d["cases"][1] = d["cases"][1], d["cases"][0]
    elif mutation == "fake_expected_seed":
        d["cases"][0]["expected_seed"] = "desired answer"
    elif mutation == "expand_budget":
        d["study_invariants"]["per_case_max_model_calls"] = 99
    elif mutation == "fake_G0":
        d["status"] = "G0_PASSED"
    elif mutation == "missing_family":
        d["cases"][4]["family"] = "condition_reframing"
    with pytest.raises(ValueError):
        validate_design(d)
