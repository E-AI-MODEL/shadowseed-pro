from __future__ import annotations

import json
from pathlib import Path

import pytest

from shadowseed.benchmark.evidence_efficacy import (
    PREREG_SCHEMA,
    SUITE_SCHEMA,
    run_evidence_efficacy,
    validate_preregistration,
    validate_suite,
    verify_evidence_efficacy_bundle,
)


def _prereg(path: Path) -> Path:
    payload = {
        "schema": PREREG_SCHEMA,
        "protocol_id": "fixture-evidence-efficacy-v1",
        "claim_boundary": "fixture mechanics only; no efficacy claim",
        "primary_metrics": ["surfaced_opportunities", "blind_answer_preference"],
        "exclusion_rules": ["no A/B item when no authorized seed surfaced"],
        "evidence_contract": {
            "gate_policy_id": "evidence_backed",
            "generated_model_output_is_evidence": False,
            "operator_attestation_required": True,
        },
        "review_contract": {"blind_answer_preference": True},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _suite(path: Path) -> Path:
    payload = {
        "schema": SUITE_SCHEMA,
        "version": "fixture-efficacy-1",
        "language": "en",
        "conversations": [
            {
                "id": "CONV_EFFICACY",
                "domain": "fixture",
                "surface_threshold": -1.0,
                "surface_top_k": 2,
                "recurrence_mode": "pairwise",
                "turns": [
                    {"question": "Alpha is the first research topic."},
                    {"question": "How should Alpha affect the next answer?"},
                    {"question": "What follows from Alpha now?"},
                ],
                "evidence_plan": [
                    {
                        "evidence_id": "support-alpha-1",
                        "after_turn": 0,
                        "selector": {"born_turn": 0, "seed_index": 0},
                        "kind": "ssot",
                        "source_ref": "fixture://independent-source/alpha-1",
                        "strength": 1.0,
                        "independent": True,
                        "reason": "fixture operator attestation one for mechanics",
                    },
                    {
                        "evidence_id": "support-alpha-2",
                        "after_turn": 0,
                        "selector": {"born_turn": 0, "seed_index": 0},
                        "kind": "retrieval",
                        "source_ref": "fixture://independent-source/alpha-2",
                        "strength": 1.0,
                        "independent": True,
                        "reason": "fixture operator attestation two for mechanics",
                    },
                    {
                        "evidence_id": "support-alpha-3",
                        "after_turn": 0,
                        "selector": {"born_turn": 0, "seed_index": 0},
                        "kind": "human_feedback",
                        "source_ref": "fixture://independent-source/alpha-3",
                        "strength": 1.0,
                        "independent": True,
                        "reason": "fixture operator attestation three for mechanics",
                    },
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run(tmp_path: Path) -> Path:
    return run_evidence_efficacy(
        suite_path=_suite(tmp_path / "suite.json"),
        preregistration_path=_prereg(tmp_path / "prereg.json"),
        output_dir=tmp_path / "bundle",
        backend="fixture",
        model_id="fixture",
        model_reference="fixture",
        model_revision=None,
        model_digest=None,
        max_new_tokens=64,
        embedding_backend="lexical",
        embedding_model=None,
        embedding_reference="lexical-test",
        embedding_revision=None,
        surface_threshold=-1.0,
        surface_top_k=2,
        reviewers=("reviewer_a", "reviewer_b"),
        run_id="fixture-evidence-efficacy",
    )


def test_fixture_evidence_efficacy_generates_only_authorized_pairs(tmp_path: Path) -> None:
    manifest_path = _run(tmp_path)
    assert manifest_path == tmp_path / "bundle" / "manifest.json"
    assert verify_evidence_efficacy_bundle(tmp_path / "bundle")["verified"] is True

    summary = json.loads((tmp_path / "bundle" / "summary.json").read_text(encoding="utf-8"))
    assert summary["evidence_opportunity_count"] == 3
    assert summary["candidate_observed_count"] == 3
    assert summary["authority_granted_count"] == 1
    assert summary["surfaced_opportunity_count"] == 3
    assert summary["answer_review_item_count"] >= 1

    audit = json.loads(
        (tmp_path / "bundle" / "opportunity_audit.json").read_text(encoding="utf-8")
    )
    items = audit["items"]
    assert [item["gate_decision"] for item in items] == [
        "validated",
        "validated",
        "promoted",
    ]
    assert [item["weight_after_evidence"] for item in items] == pytest.approx([0.2, 0.4, 0.6])
    assert all(item["evidence_submitted"] is True for item in items)
    assert [item["authority_granted"] for item in items] == [False, False, True]
    assert all(item["later_surfaced_turns"] for item in items)
    assert [item["terminal_reason"] for item in items] == [
        "gate_did_not_grant_authority",
        "gate_did_not_grant_authority",
        "ab_generated",
    ]

    raw = json.loads(
        (tmp_path / "bundle" / "raw" / "evidence_backed_paired.json").read_text(
            encoding="utf-8"
        )
    )
    assert raw["gate_policy_id"] == "evidence_backed"
    assert raw["production_policy"] is False
    surfaced = [
        turn
        for conversation in raw["conversations"]
        for turn in conversation["turns"]
        if turn.get("surfaced_seed_ids")
    ]
    assert surfaced
    assert all(turn["baseline_answer"] != turn["ssl_answer"] for turn in surfaced)


def test_unmatched_predeclared_selector_is_recorded_not_fabricated(tmp_path: Path) -> None:
    suite_path = _suite(tmp_path / "suite.json")
    suite = json.loads(suite_path.read_text(encoding="utf-8"))
    suite["conversations"][0]["evidence_plan"] = [suite["conversations"][0]["evidence_plan"][0]]
    suite["conversations"][0]["evidence_plan"][0]["selector"] = {
        "text_contains": "candidate that cannot exist in the fixture"
    }
    suite_path.write_text(json.dumps(suite), encoding="utf-8")

    run_evidence_efficacy(
        suite_path=suite_path,
        preregistration_path=_prereg(tmp_path / "prereg.json"),
        output_dir=tmp_path / "bundle",
        backend="fixture",
        model_id="fixture",
        model_reference="fixture",
        model_revision=None,
        model_digest=None,
        max_new_tokens=64,
        embedding_backend="lexical",
        embedding_model=None,
        embedding_reference=None,
        embedding_revision=None,
        surface_threshold=-1.0,
        surface_top_k=2,
        reviewers=("reviewer_a", "reviewer_b"),
        run_id="unmatched",
    )
    audit = json.loads(
        (tmp_path / "bundle" / "opportunity_audit.json").read_text(encoding="utf-8")
    )
    item = audit["items"][0]
    assert item["candidate_observed"] is False
    assert item["evidence_submitted"] is False
    assert item["terminal_reason"] == "text_selector_not_observed"


def test_efficacy_protocol_rejects_non_external_or_unverified_design() -> None:
    prereg = {
        "schema": PREREG_SCHEMA,
        "protocol_id": "bad",
        "claim_boundary": "bad",
        "primary_metrics": [],
        "exclusion_rules": [],
        "evidence_contract": {
            "gate_policy_id": "exploratory",
            "generated_model_output_is_evidence": False,
        },
        "review_contract": {"blind_answer_preference": True},
    }
    with pytest.raises(ValueError, match="evidence_backed"):
        validate_preregistration(prereg)

    suite = {
        "schema": SUITE_SCHEMA,
        "language": "en",
        "conversations": [
            {
                "turns": [{"question": "one"}, {"question": "two"}],
                "evidence_plan": [
                    {
                        "evidence_id": "bad",
                        "after_turn": 0,
                        "selector": {"born_turn": 0, "seed_index": 0},
                        "kind": "recurrence",
                        "source_ref": "bad://source",
                        "reason": "not external",
                    }
                ],
            }
        ],
    }
    with pytest.raises(ValueError, match="efficacy evidence kind"):
        validate_suite(suite)


def test_verify_evidence_bundle_detects_tampering(tmp_path: Path) -> None:
    _run(tmp_path)
    summary = tmp_path / "bundle" / "summary.json"
    summary.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_evidence_efficacy_bundle(tmp_path / "bundle")
