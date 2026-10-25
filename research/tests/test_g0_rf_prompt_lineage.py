"""Negative controls for exact T1 prompt provenance reconstruction.

Only synthetic local inputs are used here. The real 14-call immutable
observed.json is fetched via a separately audited offline GitHub workflow.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from shadowseed_research.benchmark.real_seed_rf_inquiry import (
    _hash, _inquiry_prompt, _user_input, validate,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "real_seed_rf_inquiry_v1.json"
SCRIPT = ROOT / "scripts" / "g0_rf_prompt_lineage.py"
SPEC = importlib.util.spec_from_file_location("g0_rf_prompt_lineage_testonly", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def synthetic_record():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    case = validate(fixture)
    seed = "Twee sensoren meten mogelijk niet exact dezelfde ruimtelijke plek."
    sham = "ADC-crosstalk kan een incidentele piek geven op meetkanaal een."
    ordinary_note = "De sensorwaarden verschillen soms, oorzaak niet bevestigd."
    turns = []
    for i, turn in enumerate(case["turns"]):
        turns.append({
            "turn": i,
            "host_answer": f"Gewoon antwoord {i}: er is geen bewezen oorzaak.",
            "canonical_report": {
                "detected_candidates": [seed, sham] if i == 0 else [],
            },
            "birth": (
                {"candidate_text_sha256": sha256(seed.encode()).hexdigest()}
                if i == 0 else None
            ),
            "arms": {},
        })
    prior = [
        (_user_input(case, case["turns"][i]), turns[i]["host_answer"])
        for i in (0, 1)
    ]
    notes = {"A": "NONE", "B": "NONE", "C": ordinary_note,
             "D": seed, "E": sham}
    for arm, note in notes.items():
        prompt = _inquiry_prompt(
            case, prior,
            case["turns"][1]["new_observation"],
            case["turns"][1]["question"],
            arm=arm, note=note, earlier_question=None,
        )
        turns[1]["arms"][arm] = {
            "prompt_sha256": _hash(prompt),
            "prompt_chars": len(prompt),
            "note_sha256": _hash(note),
            "note_chars": len(note),
            "parse_status": "valid_json",
        }
    observed = {
        "schema": "ssl-rf-real-seed-observations-v1",
        "case_id": case["id"], "G0": "NOT_PASSED",
        "status": "incomplete_exploratory_not_a_null_result",
        "fixture_sha256": _hash(fixture),
        "first_seed": {
            "id": "ss_001", "text": seed,
            "sham_source": "different_real_T0_detector_item_not_first_seed",
            "sham_text_sha256": _hash(sham),
        },
        "ordinary_note": ordinary_note, "turns": turns,
    }
    return observed, fixture


def test_rebuilds_all_five_exact_prompts_and_detects_only_D_seed_exposure():
    observed, fixture = synthetic_record()
    result = MODULE.verify_t1_prompt_lineage(observed, fixture)
    assert result["G0"] == "NOT_PASSED"
    assert result["candidate_exposed_only_in_research_arm_D"]
    assert result["t1_prompt_reconstruction_hashes_match"]
    assert result["t1_observational_unit_count"] == 1
    assert result["q2_seed_causal_effect_proven"] is False
    assert sum(v["literal_first_seed_present"]
               for v in result["all_t1_model_arms"].values()) == 1


@pytest.mark.parametrize("change", [
    "wrong_input", "altered_t1_prompt_hash", "incorrect_arm_note_length",
    "T0_leak", "wrong_sham", "fictional_T2", "false_G0_pass",
])
def test_rejects_archival_input_drift_and_unauthorized_seed_exposure(change):
    data, fixture = synthetic_record()
    if change == "wrong_input":
        fixture["case"]["turns"][0]["question"] += " Extra."
    elif change == "altered_t1_prompt_hash":
        data["turns"][1]["arms"]["D"]["prompt_sha256"] = "0" * 64
    elif change == "incorrect_arm_note_length":
        data["turns"][1]["arms"]["C"]["note_chars"] += 3
    elif change == "T0_leak":
        data["turns"][0]["host_answer"] += " " + data["first_seed"]["text"]
        # A/B should now be seen as already seed-exposed by ordinary context.
        # Rebuild hashes to avoid confusing the reason for the rejection.
        case = validate(fixture)
        prior = [(_user_input(case, case["turns"][i]), data["turns"][i]["host_answer"])
                 for i in (0, 1)]
        notes = {"A": "NONE", "B": "NONE",
                 "C": data["ordinary_note"],
                 "D": data["first_seed"]["text"],
                 "E": data["turns"][0]["canonical_report"]["detected_candidates"][1]}
        for arm, note in notes.items():
            prompt = _inquiry_prompt(case, prior,
                case["turns"][1]["new_observation"], case["turns"][1]["question"],
                arm=arm, note=note, earlier_question=None)
            data["turns"][1]["arms"][arm]["prompt_sha256"] = _hash(prompt)
            data["turns"][1]["arms"][arm]["prompt_chars"] = len(prompt)
    elif change == "wrong_sham":
        data["first_seed"]["sham_text_sha256"] = "a" * 64
    elif change == "fictional_T2":
        data["turns"][2]["arms"]["D"] = {"text": "made up"}
    elif change == "false_G0_pass":
        data["G0"] = "PASSED"
    with pytest.raises(ValueError):
        MODULE.verify_t1_prompt_lineage(data, fixture)
