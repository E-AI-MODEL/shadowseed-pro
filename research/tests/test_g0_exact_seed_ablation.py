"""No-network, synthetic checks for the real-source single-seed exact deletion.

The real observed.json is NOT committed as test fixture. Its original SHA
is verified in the opt-in paid workflow before any GPT-5 calls.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest

from shadowseed_research.benchmark.g0_exact_seed_ablation import (
    ARMS, CALLS, EXPECTED_SOURCE_SHA, ORDER, TOKEN_CAP, OUTPUT_CAP,
    _hash, build_prompts, make_blind_packets, run,
    validate_design, verify_recorded_source,
)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / "fixtures" / "g0_exact_seed_ablation_v1.json"
SOURCE_FIXTURE = ROOT / "fixtures" / "real_seed_rf_inquiry_v1.json"
SEED = (
    "Onbekende ruimtelijke offset: de twee sensoren bemonsteren mogelijk "
    "niet exact dezelfde plek/volume van het materiaal, waardoor lokale, "
    "echte transiënten alleen in kanaal 1 verschijnen."
)


def _frozen_inputs():
    design = json.loads(DESIGN.read_text(encoding="utf-8"))
    fixture = json.loads(SOURCE_FIXTURE.read_text(encoding="utf-8"))
    reports = []
    for i in range(3):
        reports.append({
            "runtime_mode": "live", "turn": i, "answer": f"gewoon antwoord {i}",
            "selected_seed_ids": [], "surfaced_seed_ids": [],
            "same_turn_revision_applied": False,
            "self_reinforcement_applied": False,
        })
    birth = {
        "seed_id": "ss_001", "candidate_text_sha256": sha256(SEED.encode()).hexdigest()
    }
    birth["snapshot_sha256"] = _hash(birth)
    follow = {
        "seed_id": "ss_001", "turn": 1,
        "birth_snapshot_sha256": birth["snapshot_sha256"],
        "history_sha256": _hash(reports[:2]),
        "turn_report_sha256": _hash(reports[1]),
        "seed_state_after_turn": {"weight": 0, "evidence_count": 0},
        "product_answer_seed_influence_observed": False,
    }
    follow["snapshot_sha256"] = _hash(follow)
    turns = [{
        "turn": i, "canonical_report": reports[i],
        "host_answer": reports[i]["answer"],
        "none_control_answer_identical": True,
        "birth": birth if i == 0 else None,
        "followup": follow if i == 1 else None,
    } for i in range(3)]
    orig = {
        "schema": "ssl-rf-real-seed-observations-v1",
        "model": "gpt-5", "case_id": "MEASUREMENT",
        "status": "incomplete_exploratory_not_a_null_result",
        "G0": "NOT_PASSED", "fixture_sha256": _hash(fixture),
        "first_seed": {"id": "ss_001", "text": SEED,
                       "weight": 0, "evidence_count": 0},
        "turns": turns,
        "ordinary_note": (
            "Voorlopig zijn firmware en regelkast mogelijke verklaringen; "
            "zonder onafhankelijke sensortijden blijft causaliteit onzeker."
        ),
        "provider_audit": {"model_calls": 14, "recorded_tokens": 37503},
    }
    return orig, fixture, design


class NoNetworkProvider:
    model_call_cap = CALLS
    embedding_call_cap = 1
    all_token_cap = TOKEN_CAP
    output_token_cap = OUTPUT_CAP
    def __init__(self, fail_at: int | None = None):
        self.model_calls = 0
        self.embedding_calls = 0
        self.total_tokens = 0
        self.events = []
        self.fail_at = fail_at
        self.sent: list[tuple[str, str]] = []

    def generate(self, *, stage, case_id, prompt, instructions):
        self.model_calls += 1
        assert instructions
        assert case_id == "MEASUREMENT"
        self.sent.append((stage, prompt))
        if self.fail_at == self.model_calls:
            raise RuntimeError("incomplete_model_response")
        self.total_tokens += 100
        self.events.append({
            "kind": "model", "stage": stage,
            "response_id": f"fake-{self.model_calls}",
            "model": "FAKE_NETWORK_FREE",
            "input_tokens": 50, "output_tokens": 50,
        })
        return json.dumps({
            "question": "Welke onafhankelijke proef onderscheidt verklaringen?",
            "test": "Vergelijk onafhankelijk gemeten waarden per kanaal.",
            "uncertainty": "Causaliteit is nog onbekend.",
        })


def test_predeclared_order_all_arms_and_no_hidden_success_key():
    d = _frozen_inputs()[2]
    validate_design(d)
    assert len(SEED) == len(d["control_placeholder"]) == 185
    assert len(ORDER) == 4 and sum(len(x) for x in ORDER) == 16
    assert sorted({p for row in ORDER for p in row}) == sorted(ARMS)
    assert d["design_status"].startswith("POST_HOC_EXPLORATORY")
    assert d["source_raw_observed_sha256"] == EXPECTED_SOURCE_SHA


def test_true_birth_source_with_two_turns_and_control_parity():
    original, fixture, design = _frozen_inputs()
    valid = verify_recorded_source(original, fixture, design)
    assert valid["seed"] == SEED
    prompts = build_prompts(original, fixture, design)
    assert set(prompts) == set(ARMS)
    assert prompts["D"]["prompt_chars"] == prompts["P"]["prompt_chars"]
    assert prompts["D"]["note_chars"] == prompts["P"]["note_chars"] == 185
    assert SEED in prompts["D"]["prompt"]
    assert all(SEED not in prompts[a]["prompt"] for a in ("X", "P", "N"))
    assert prompts["D"]["prompt_sha256"] != prompts["X"]["prompt_sha256"]
    future = fixture["case"]["turns"][2]["new_observation"]
    assert all(future not in p["prompt"] for p in prompts.values())
    # The only changed text is the note slot.
    for arm in ARMS:
        prefix, _, _ = prompts[arm]["prompt"].partition(
            "EERDERE ONBEWEZEN ONDERZOEKSNOTITIE:")
        assert prefix == prompts["D"]["prompt"].partition(
            "EERDERE ONBEWEZEN ONDERZOEKSNOTITIE:")[0]


def test_full_fake_16_call_balance_raw_outputs_and_owner_separation():
    original, fixture, design = _frozen_inputs()
    p = NoNetworkProvider()
    checkpoints = []
    result = run(original, fixture, design, p,
                 on_checkpoint=lambda v: checkpoints.append(deepcopy(v)))
    assert result["status"] == "completed_exploratory_unreviewed_single_seed"
    assert result["Q1_internal_absence_proven"] is False
    assert result["Q2_causal_new_investigability_proven"] is False
    assert result["G0"] == "NOT_PASSED"
    assert result["source_real_canonical_seed_birth"] is True
    assert p.model_calls == 16 and p.embedding_calls == 0
    assert len(checkpoints) == 17
    assert [x["arm"] for x in result["observations"]] == [
        arm for order in ORDER for arm in order
    ]
    assert all(sum(x["arm"] == arm for x in result["observations"]) == 4
               for arm in ARMS)
    assert all(x["response_status"] == "valid_question"
               for x in result["observations"])
    assert all(p.sent[i][1] == p.sent[j][1]
               for i in range(16) for j in range(16)
               if result["observations"][i]["arm"] ==
                  result["observations"][j]["arm"])
    blind, owner = make_blind_packets(result)
    assert len(blind["samples"]) == len(owner["sample_mapping"]) == 16
    assert not any("arm" in x for x in blind["samples"])
    assert set(x["sample_id"] for x in blind["samples"]) == set(owner["sample_mapping"])
    assert blind["independent_review_completed"] is False


def test_incomplete_provider_call_is_never_mislabeled_as_none_or_effect():
    original, fixture, design = _frozen_inputs()
    p = NoNetworkProvider(fail_at=7)
    seen = []
    with pytest.raises(RuntimeError, match="incomplete_model_response"):
        run(original, fixture, design, p,
            on_checkpoint=lambda v: seen.append(deepcopy(v)))
    assert p.model_calls == 7
    assert len(seen[-1]["observations"]) == 6
    assert seen[-1]["status"] == "running_exploratory_not_efficacy"
    assert seen[-1]["Q2_causal_new_investigability_proven"] is False


@pytest.mark.parametrize("broken", [
    "pass", "replace_seed", "source_hash", "future", "model",
    "schedule", "result_hints", "placebo_length", "wrong_g0",
    "bad_birth", "bad_T1", "ordinary_exposure",
])
def test_no_source_or_method_changes_can_masquerade_as_causal_evidence(broken):
    original, fixture, design = _frozen_inputs()
    if broken == "pass":
        design["design_status"] = "CONFIRMATORY_PASSED"
    elif broken == "replace_seed":
        original["first_seed"]["text"] = "Investigator-authored substitute"
    elif broken == "source_hash":
        design["source_raw_observed_sha256"] = "a" * 64
    elif broken == "future":
        fixture["case"]["turns"][2]["new_observation"] = (
            fixture["case"]["turns"][1]["new_observation"]
        )
        # Re-hash fixture; the source case cannot be substituted.
        original["fixture_sha256"] = _hash(fixture)
        # Future observations may not be smuggled into T1 by design.
        # This case is valid as staged updates but source first note would
        # now be inconsistent with its frozen original fixture. Pin original
        # source fixture by independent digest in the validated design.
        design["source_fixture_path"] = "fake"
    elif broken == "model":
        design["source_model"] = "small-model"
    elif broken == "schedule":
        design["schedule"][2]["order"][0] = "D"
    elif broken == "result_hints":
        design["target_question"] = "the spatial offset is correct"
    elif broken == "placebo_length":
        design["control_placeholder"] += " extra"
    elif broken == "wrong_g0":
        original["G0"] = "PASSED"
    elif broken == "bad_birth":
        original["turns"][0]["birth"]["snapshot_sha256"] = "b" * 64
    elif broken == "bad_T1":
        original["turns"][1]["followup"]["history_sha256"] = "b" * 64
    elif broken == "ordinary_exposure":
        original["turns"][1]["canonical_report"]["surfaced_seed_ids"] = ["ss_001"]
    else:
        raise AssertionError(broken)
    with pytest.raises((ValueError, AssertionError)):
        build_prompts(original, fixture, design)
