#!/usr/bin/env python3
"""Read-only G0 v3 review readiness ledger, never a synthetic approval.

G0 is an independent human, version-specific construct review of E1/E2.
This script checks whether the public review handoff is COMPLETE AS A RECORD.
It cannot verify reviewer identity, human independence, domain expertise,
evaluator semantic validity, or the scientific contribution itself.

A green CI result is NOT a G0 pass. No API calls, credential use, model
generation, production changes, private holdouts, or review-signature
impersonation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "g0-v3-review-readiness-v1"
DECISIONS = frozenset({
    "ACCEPT FOR LIMITED FEASIBILITY", "REJECT", "INDETERMINATE",
})
ROLES = ("technical", "conceptual")
FAMILIES = ("E1", "E2")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_REVIEW_KEYS = frozenset({
    "reviewer_id", "reviewer_role", "authored_on",
    "reviewed_product_sha", "reviewed_review_subject",
    "evaluator_sha_by_family", "verdict_by_family",
    "evidence_refs_by_family", "reasoning_by_family",
    "declared_independent_of_study_authors",
})
REQUIRED_EVAL_BOOL = (
    "general_unscripted_evaluator_executed_and_independently_verified",
    "negative_cases_independent_verified",
)


def check_manifest(doc: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise ValueError("wrong G0 review schema")
    if doc.get("G0") != "NOT_PASSED":
        raise ValueError("manifest cannot grant G0 approval")
    if doc.get("automatic_G0_pass_allowed") is not False:
        raise ValueError("automatic G0 PASS is prohibited")
    if doc.get("review_scope") != "CONSTRUCT_ACCEPTANCE_FOR_FEASIBILITY_ONLY":
        raise ValueError("G0 scope must not claim efficacy")
    if doc.get("review_subject") != "dynamic_inquiry_E1_E2":
        raise ValueError("wrong study version")
    if doc.get("repository") != "E-AI-MODEL/shadowseed-pro":
        raise ValueError("unexpected source repository")
    if not SHA_RE.fullmatch(str(doc.get("product_main_sha", ""))):
        raise ValueError("product version not pinned")
    sources = doc.get("exploratory_sources")
    if not isinstance(sources, list) or len(sources) != 2:
        raise ValueError("missing source snapshots")
    if {(s.get("pr"), s.get("run_id")) for s in sources} != {
        (250, 40215854335), (251, 40224494313),
    }:
        raise ValueError("incomplete or substituted exploratory provenance")
    if any(not SHA_RE.fullmatch(str(s.get("head_sha", ""))) for s in sources):
        raise ValueError("unpinned exploratory provenance")
    reviewers = doc.get("reviews")
    environments = doc.get("environments")
    if not isinstance(reviewers, dict) or set(reviewers) != set(ROLES):
        raise ValueError("the two independent reviewer roles are mandatory")
    if not isinstance(environments, dict) or set(environments) != set(FAMILIES):
        raise ValueError("both distinct E1 and E2 are required")
    missing: list[str] = []
    review_structure = {}
    person_ids: list[str] = []
    for role in ROLES:
        item = reviewers[role]
        if not isinstance(item, dict) or item.get("issue") != (
            234 if role == "technical" else 235
        ):
            raise ValueError("reviewer must be linked to original G0 issue")
        reviewer = item.get("reviewer")
        evidence = item.get("review_record")
        if reviewer is None or evidence is None:
            missing.append("independent_" + role + "_review")
            review_structure[role] = "NOT_SUBMITTED"
            continue
        if not isinstance(reviewer, str) or not reviewer.strip():
            raise ValueError("blank human reviewer identity")
        if not isinstance(evidence, dict) or not REQUIRED_REVIEW_KEYS.issubset(evidence):
            raise ValueError("review record lacks required source/provenance")
        if evidence["reviewer_id"] != reviewer or evidence["reviewer_role"] != role:
            raise ValueError("reviewer identity or role mismatch")
        if (
            evidence["reviewed_product_sha"] != doc["product_main_sha"]
            or evidence["reviewed_review_subject"] != doc["review_subject"]
        ):
            raise ValueError("review is not about the pinned G0 version")
        if evidence["declared_independent_of_study_authors"] is not True:
            raise ValueError("reviewer has not independently attested authorship")
        if not isinstance(evidence["authored_on"], str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}", evidence["authored_on"]
        ):
            raise ValueError("undated human review")
        if (
            not isinstance(evidence["verdict_by_family"], dict)
            or set(evidence["verdict_by_family"]) != set(FAMILIES)
            or any(v not in DECISIONS for v in evidence["verdict_by_family"].values())
        ):
            raise ValueError("reviewer must issue a reasoned E1 and E2 verdict")
        for family in FAMILIES:
            sha = evidence["evaluator_sha_by_family"].get(family)
            refs = evidence["evidence_refs_by_family"].get(family)
            justification = evidence["reasoning_by_family"].get(family)
            if (
                not SHA_RE.fullmatch(str(sha or ""))
                or not isinstance(refs, list) or not refs
                or not all(isinstance(ref, str) and ref.strip() for ref in refs)
                or not isinstance(justification, str)
                or len(justification.strip()) < 40
            ):
                raise ValueError("missing family-specific independent evidence")
        person_ids.append(reviewer.strip().lower())
        if item.get("independence_verified_by_human") is not True:
            missing.append("human_independence_check_" + role)
        review_structure[role] = "RECORD_PRESENT_NOT_AUTHENTICATED"
    if len(set(person_ids)) != len(person_ids):
        raise ValueError("two reviews cannot be written by the same person")
    for family in FAMILIES:
        row = environments[family]
        if not isinstance(row, dict):
            raise ValueError("environment record missing")
        for key in REQUIRED_EVAL_BOOL:
            if row.get(key) is not True:
                missing.append(f"{family}_{key}")
        if not SHA_RE.fullmatch(str(row.get("pinned_upstream_revision", ""))):
            missing.append(f"{family}_pinned_executable_evaluator")
        for role in ROLES:
            # Review verdict is recorded in the independent review document,
            # not inferred from or supplied by the study author's environment.
            if row.get(role + "_decision") is None:
                missing.append(f"{family}_{role}_formal_environment_decision")
            elif row[role + "_decision"] not in DECISIONS:
                raise ValueError("unknown independent environment verdict")
    for field in (
        "sequestered_confirmatory_cases_created_by_independent_case_owner",
        "evaluator_allowlisted_safe_execution_verified",
        "known_T2_checkpoint_failure_resolved",
    ):
        if doc.get(field) is not True:
            missing.append(field)
    if doc.get("ssot_evidence_polarity_issue_241_open") is True:
        missing.append("ssot_evidence_polarity_issue_241_open")
    if doc.get("later_RI_effect_independently_validated") is False:
        # RI evidence is not necessarily a pre-G0 prerequisite; its absence
        # always limits later claims, not structural G0 review eligibility.
        ri_status = "NOT_DEMONSTRATED"
    else:
        ri_status = "UNVERIFIED_NEEDS_SOURCE_REVIEW"

    return {
        "schema": "g0-v3-structural-readiness-result-v1",
        "study": doc["review_subject"],
        "G0": "NOT_PASSED",
        "review_packet_structurally_inspectable": True,
        "independent_human_reviews": review_structure,
        "unresolved_items": sorted(set(missing)),
        "unresolved_count": len(set(missing)),
        "ri_later_effect_status": ri_status,
        "automatic_approval": False,
        "human_identity_and_construct_validity_not_programmatically_verifiable": True,
        "note": (
            "No automated function may declare G0-PASS. Two independent "
            "human version-specific reviews and external evaluator evidence "
            "must be checked by a human decision owner."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    value = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    result = check_manifest(value)
    data = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(data, encoding="utf-8")
    print(data, end="")


if __name__ == "__main__":
    main()
