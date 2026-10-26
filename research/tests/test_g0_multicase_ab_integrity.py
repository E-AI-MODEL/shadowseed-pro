"""No-network regression for matched-prompt and scientific-denominator audit.

Test fakes are never evidence of real multi-turn Q2 behavior.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from test_g0_multicase_real_ab import FakeProvider, fixture
from shadowseed_research.benchmark.g0_multicase_real_ab import run_study
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "g0_multicase_ab_integrity.py"
SPEC = importlib.util.spec_from_file_location("g0_multicase_ab_integrity_check", SCRIPT)
assert SPEC and SPEC.loader
AUDIT_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT_MODULE)
audit = AUDIT_MODULE.audit


def _fake_study(with_failure: bool = False):
    return run_study(
        fixture(),
        lambda cid: FakeProvider(
            cid, no_birth=cid.endswith("06"),
            fail_at=8 if with_failure and cid.endswith("02") else None
        )
    )


def test_all_real_engine_fake_provider_paths_reconstruct_paired_prompt_hashes():
    d = _fake_study()
    a = audit(d, fixture())
    assert a["independent_case_count"] == 6
    assert a["completed_case_pairs"] == 5
    assert a["no_birth_cases_not_effect_nulls"] == 1
    assert a["failed_cases_not_effect_nulls"] == 0
    assert a["full_T1_T2_paired_inquiry_records"] == 20
    assert a["all_recorded_full_pair_prompt_hashes_match"] is True
    assert a["G0"] == "NOT_PASSED"
    assert not a["candidate_specific_semantic_or_causal_effect_established"]
    assert a["ordinary_note_contamination_cases"] == []


def test_failure_does_not_become_a_null_effect_or_a_completed_pair():
    d = _fake_study(with_failure=True)
    a = audit(d, fixture())
    assert a["completed_case_pairs"] == 4
    assert a["failed_cases_not_effect_nulls"] == 1
    assert a["no_birth_cases_not_effect_nulls"] == 1
    assert a["full_T1_T2_paired_inquiry_records"] == 16


@pytest.mark.parametrize("mutation", [
    "false_g0", "false_q2", "fake_no_birth", "missing_B", "altered_prompt_hash",
    "altered_birth", "altered_followup", "wrong_study_counts", "ordinary_gate",
    "extra_case", "malformed_allocation", "too_many_model_calls",
])
def test_auditor_rejects_distorted_provenance_or_claims(mutation):
    d = _fake_study()
    if mutation == "false_g0":
        d["G0"] = "PASSED"
    elif mutation == "false_q2":
        d["q2_new_later_investigability_proven"] = True
    elif mutation == "fake_no_birth":
        d["cases"][5]["first_seed"] = d["cases"][0]["first_seed"]
    elif mutation == "missing_B":
        d["cases"][0]["turns"][1]["research_arms"].pop("B")
    elif mutation == "altered_prompt_hash":
        d["cases"][0]["turns"][2]["research_arms"]["A"]["prompt_sha256"] = "0"*64
    elif mutation == "altered_birth":
        d["cases"][0]["birth"]["snapshot_sha256"] = "0"*64
    elif mutation == "altered_followup":
        d["cases"][0]["turns"][2]["followup"]["history_sha256"] = "0"*64
    elif mutation == "wrong_study_counts":
        d["study_counts"]["case_pairs_completed"] += 1
    elif mutation == "ordinary_gate":
        d["cases"][0]["turns"][1]["canonical_report"]["surfaced_seed_ids"] = ["ss_001"]
    elif mutation == "extra_case":
        d["cases"].append(deepcopy(d["cases"][-1]))
    elif mutation == "malformed_allocation":
        d["recorded_allocation"]["AB26-C01"] = ["A", "A"]
    elif mutation == "too_many_model_calls":
        d["cases"][0]["provider"]["model_calls_attempted"] = 99
    with pytest.raises(ValueError):
        audit(d, fixture())
