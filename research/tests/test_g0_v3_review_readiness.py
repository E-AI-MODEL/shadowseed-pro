"""G0 independence/readiness preflight tests. Test identities are fake data only.

Green tests can establish that no false PASS is serialized. They cannot
replace two human domain experts or validate an open-ended evaluator.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "g0_v3_review_readiness.py"
FIXTURE = ROOT / "fixtures" / "g0_v3_review_readiness_v1.json"
SPEC = importlib.util.spec_from_file_location("g0_v3_readiness_testonly", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def document():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_existing_review_packet_is_inspectable_but_not_passed():
    result = MODULE.check_manifest(document())
    assert result["G0"] == "NOT_PASSED"
    assert result["review_packet_structurally_inspectable"] is True
    assert result["automatic_approval"] is False
    assert result["human_identity_and_construct_validity_not_programmatically_verifiable"]
    assert result["independent_human_reviews"] == {
        "technical": "NOT_SUBMITTED",
        "conceptual": "NOT_SUBMITTED",
    }
    reasons = result["unresolved_items"]
    assert "independent_technical_review" in reasons
    assert "independent_conceptual_review" in reasons
    assert "E1_pinned_executable_evaluator" in reasons
    assert "E2_pinned_executable_evaluator" in reasons
    assert "holdout_creation_protocol_independently_approved" in reasons
    assert "live_Rf_T2_checkpoint_failure_unresolved" in result["parallel_non_G0_work_items"]
    assert "product_SSOT_polarity_issue_241_open" in result["parallel_non_G0_work_items"]
    assert "future_confirmatory_cases_not_created" in result["parallel_non_G0_work_items"]
    assert result["ri_later_effect_status"] == "NOT_DEMONSTRATED"


@pytest.mark.parametrize("mutation", [
    "grant_g0", "enable_automatic", "drop_E2", "drop_reviewer",
    "replace_product", "drop_exploratory", "scope_claims_efficacy",
])
def test_manifest_cannot_silently_expand_approval_or_launder_missing_sources(mutation):
    doc = deepcopy(document())
    if mutation == "grant_g0":
        doc["G0"] = "PASSED"
    elif mutation == "enable_automatic":
        doc["automatic_G0_pass_allowed"] = True
    elif mutation == "drop_E2":
        doc["environments"].pop("E2")
    elif mutation == "drop_reviewer":
        doc["reviews"].pop("conceptual")
    elif mutation == "replace_product":
        doc["product_main_sha"] = "wrong"
    elif mutation == "drop_exploratory":
        doc["exploratory_sources"].pop()
    elif mutation == "scope_claims_efficacy":
        doc["review_scope"] = "Q2_EFFECT_PROVEN"
    else:
        assert False, mutation
    with pytest.raises(ValueError):
        MODULE.check_manifest(doc)


def fake_reviewer(doc, role, reviewer_id):
    return {
        "reviewer_id": reviewer_id,
        "reviewer_role": role,
        "authored_on": "2026-10-25",
        "reviewed_product_sha": doc["product_main_sha"],
        "reviewed_review_subject": doc["review_subject"],
        "evaluator_sha_by_family": {"E1": "a" * 40, "E2": "b" * 40},
        "verdict_by_family": {
            "E1": "ACCEPT FOR LIMITED FEASIBILITY",
            "E2": "INDETERMINATE",
        },
        "evidence_refs_by_family": {
            "E1": ["fake:test-only:not-a-real-evaluator"],
            "E2": ["fake:test-only:not-a-real-evaluator"],
        },
        "reasoning_by_family": {
            "E1": "TEST_ONLY " * 12,
            "E2": "TEST_ONLY " * 12,
        },
        "declared_independent_of_study_authors": True,
    }


def test_even_two_structural_fake_reviews_cannot_yield_automatic_g0_pass():
    doc = deepcopy(document())
    for role, reviewer_id in (("technical", "fake-r1"), ("conceptual", "fake-r2")):
        doc["reviews"][role]["reviewer"] = reviewer_id
        doc["reviews"][role]["review_record"] = fake_reviewer(doc, role, reviewer_id)
        doc["reviews"][role]["independence_verified_by_human"] = False
    for family, sha in (("E1", "a" * 40), ("E2", "b" * 40)):
        row = doc["environments"][family]
        row["general_unscripted_evaluator_executed_and_independently_verified"] = True
        row["negative_cases_independent_verified"] = True
        row["pinned_upstream_revision"] = sha
        row["technical_decision"] = "ACCEPT FOR LIMITED FEASIBILITY"
        row["conceptual_decision"] = "INDETERMINATE"
    doc["sequestered_confirmatory_cases_created_by_independent_case_owner"] = True
    doc["holdout_creation_protocol_independently_approved"] = True
    doc["evaluator_allowlisted_safe_execution_verified"] = True
    doc["known_T2_checkpoint_failure_resolved"] = True
    doc["ssot_evidence_polarity_issue_241_open"] = False
    result = MODULE.check_manifest(doc)
    assert result["G0"] == "NOT_PASSED"
    assert result["automatic_approval"] is False
    assert "human_independence_check_technical" in result["unresolved_items"]
    assert "human_independence_check_conceptual" in result["unresolved_items"]
    assert result["independent_human_reviews"]["technical"] == (
        "RECORD_PRESENT_NOT_AUTHENTICATED"
    )


def test_same_person_cannot_pass_as_two_independent_reviewers():
    doc = document()
    for role in ("technical", "conceptual"):
        doc["reviews"][role]["reviewer"] = "SAME-FAKE-REVIEWER"
        doc["reviews"][role]["review_record"] = fake_reviewer(doc, role, "SAME-FAKE-REVIEWER")
    with pytest.raises(ValueError, match="same person"):
        MODULE.check_manifest(doc)


def test_llm_or_unattributed_review_cannot_replace_human_independent_review():
    doc = document()
    doc["reviews"]["technical"]["reviewer"] = "llm-draft-not-a-human"
    review = fake_reviewer(doc, "technical", "llm-draft-not-a-human")
    review["declared_independent_of_study_authors"] = False
    doc["reviews"]["technical"]["review_record"] = review
    with pytest.raises(ValueError, match="not independently attested"):
        MODULE.check_manifest(doc)


def test_no_historical_pr_can_by_itself_claim_q2_or_g0():
    d = document()
    assert {x["pr"] for x in d["exploratory_sources"]} == {250, 251}
    assert d["later_RI_effect_independently_validated"] is False
    assert d["G0"] == "NOT_PASSED"
    assert d["environments"]["E1"]["technical_decision"] is None
    assert d["environments"]["E2"]["conceptual_decision"] is None
