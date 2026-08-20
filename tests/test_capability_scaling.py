from __future__ import annotations

import json
from pathlib import Path

import pytest

from shadowseed.benchmark.capability_scaling import (
    CANDIDATE_FIELDS,
    PREREG_SCHEMA,
    SuiteSpec,
    _assert_live_authority_invariants,
    run_capability_scaling,
    summarize_reviews,
    validate_preregistration,
    verify_capability_bundle,
)


def _suite(path: Path) -> Path:
    payload = {
        "version": "fixture-capability-1",
        "language": "en",
        "conversations": [
            {
                "id": "CONV_TEST",
                "domain": "test domain",
                "turns": [
                    {"question": "Alpha is the recurring topic."},
                    {"question": "Alpha remains the recurring topic."},
                    {"question": "Alpha is still the recurring topic."},
                    {"question": "Alpha continues as the recurring topic."},
                    {"question": "Alpha closes the recurring topic."},
                ],
            }
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _prereg(path: Path) -> Path:
    payload = {
        "schema": PREREG_SCHEMA,
        "protocol_id": "fixture-protocol",
        "claim_boundary": "fixture smoke only",
        "primary_metrics": ["mechanics"],
        "exclusion_rules": ["no truth claims"],
        "review_contract": {
            "candidate_fields": list(CANDIDATE_FIELDS),
            "epistemic_roles": ["gap", "doubt", "what_if", "other", "unclear"],
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run(tmp_path: Path) -> Path:
    return run_capability_scaling(
        suites=[SuiteSpec("fixture", _suite(tmp_path / "suite.json"))],
        output_dir=tmp_path / "bundle",
        preregistration_path=_prereg(tmp_path / "prereg.json"),
        backend="fixture",
        model_id="fixture",
        model_reference="fixture",
        model_revision="test-revision",
        model_digest="test-digest",
        quantization=None,
        max_new_tokens=64,
        embedding_backend="lexical",
        embedding_model=None,
        embedding_reference="lexical-test",
        embedding_revision=None,
        surface_threshold=-1.0,
        surface_top_k=2,
        early_turn_margin=0.0,
        early_turn_history=0,
        resurface_margin=0.0,
        max_seeds_per_turn=3,
        recurrence_mode="pairwise",
        cluster_threshold=None,
        semantic_duplicate_threshold=0.80,
        evaluation_conversation_ids={"CONV_TEST"},
        reviewers=("reviewer_a", "reviewer_b"),
        run_id="fixture-run",
    )


def test_fixture_capability_run_is_hash_verified_and_live_authority_stays_zero(tmp_path: Path) -> None:
    manifest_path = _run(tmp_path)
    assert manifest_path == tmp_path / "bundle" / "manifest.json"
    verified = verify_capability_bundle(tmp_path / "bundle")
    assert verified["verified"] is True
    assert verified["artifact_count"] >= 8

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["model"]["authority_effect_of_model_identity"] == "none"
    assert manifest["runtime"]["live_gate_policy"] == "evidence_backed"
    assert manifest["runtime"]["external_evidence_injected"] is False

    summary = json.loads((tmp_path / "bundle" / "summary.json").read_text(encoding="utf-8"))
    assert summary["automatic_metrics"]["live"]["positive_weight_event_count"] == 0
    assert summary["candidate_review_item_count"] > 0
    assert summary["answer_review_item_count"] > 0

    candidate_packet = json.loads(
        (tmp_path / "bundle" / "review" / "candidate_review_packet.json").read_text(
            encoding="utf-8"
        )
    )
    first = candidate_packet["items"][0]
    assert "model" not in first
    assert "model_reference" not in first
    assert "promoted" not in first


def test_verify_capability_bundle_detects_tampering(tmp_path: Path) -> None:
    _run(tmp_path)
    summary_path = tmp_path / "bundle" / "summary.json"
    summary_path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_capability_bundle(tmp_path / "bundle")


def test_live_authority_invariant_fails_on_positive_weight_or_promotion() -> None:
    with pytest.raises(RuntimeError, match="changed authority"):
        _assert_live_authority_invariants(
            [{"weight_delta": 0.2, "decision": "validated", "signals": []}]
        )
    with pytest.raises(RuntimeError, match="promoted/validated"):
        _assert_live_authority_invariants(
            [{"weight_delta": 0.0, "decision": "promoted", "signals": []}]
        )


def test_review_summary_unblinds_ssl_choice_and_reports_agreement(tmp_path: Path) -> None:
    _run(tmp_path)
    review_dir = tmp_path / "bundle" / "review"
    candidate_packet_path = review_dir / "candidate_review_packet.json"
    answer_packet_path = review_dir / "answer_review_packet.json"
    answer_key_path = review_dir / "answer_review_key.json"

    candidate_packet = json.loads(candidate_packet_path.read_text(encoding="utf-8"))
    for item in candidate_packet["items"]:
        for response in item["reviewer_responses"]:
            scores = response["scores"]
            for field in CANDIDATE_FIELDS:
                scores[field] = "yes" if field != "assertion_masquerade" else "no"
            scores["epistemic_role"] = "gap"
    candidate_packet_path.write_text(json.dumps(candidate_packet), encoding="utf-8")

    answer_packet = json.loads(answer_packet_path.read_text(encoding="utf-8"))
    answer_key = json.loads(answer_key_path.read_text(encoding="utf-8"))
    key_by_id = {item["review_id"]: item for item in answer_key["items"]}
    for item in answer_packet["items"]:
        key = key_by_id[item["review_id"]]
        winning_option = "A" if key["option_a_source"] == "ssl" else "B"
        for response in item["reviewer_responses"]:
            response["scores"]["better_answer"] = winning_option
    answer_packet_path.write_text(json.dumps(answer_packet), encoding="utf-8")

    output = summarize_reviews(
        candidate_packet_path=candidate_packet_path,
        candidate_key_path=review_dir / "candidate_review_key.json",
        answer_packet_path=answer_packet_path,
        answer_key_path=answer_key_path,
        output_path=tmp_path / "review-summary.json",
    )
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["candidate"]["fields"]["atomic"]["yes_rate_decisive"] == 1.0
    assert payload["candidate"]["fields"]["atomic"]["agreement"]["raw_agreement"] == 1.0
    assert payload["answer"]["ssl_win_rate_non_tie"] == 1.0
    assert payload["answer"]["agreement"]["raw_agreement"] == 1.0


def test_preregistration_rejects_review_contract_drift() -> None:
    payload = {
        "schema": PREREG_SCHEMA,
        "protocol_id": "bad",
        "claim_boundary": "bad",
        "primary_metrics": [],
        "exclusion_rules": [],
        "review_contract": {
            "candidate_fields": ["atomic"],
            "epistemic_roles": ["gap", "doubt", "what_if", "other", "unclear"],
        },
    }
    with pytest.raises(ValueError, match="candidate_fields"):
        validate_preregistration(payload)


def test_unknown_evaluation_conversation_fails_before_model_run(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown evaluation conversation"):
        run_capability_scaling(
            suites=[SuiteSpec("fixture", _suite(tmp_path / "suite.json"))],
            output_dir=tmp_path / "bundle",
            preregistration_path=_prereg(tmp_path / "prereg.json"),
            backend="fixture",
            model_id="fixture",
            model_reference="fixture",
            model_revision=None,
            model_digest=None,
            quantization=None,
            max_new_tokens=64,
            embedding_backend="lexical",
            embedding_model=None,
            embedding_reference=None,
            embedding_revision=None,
            surface_threshold=0.3,
            surface_top_k=2,
            early_turn_margin=0.1,
            early_turn_history=5,
            resurface_margin=0.15,
            max_seeds_per_turn=3,
            recurrence_mode="cluster",
            cluster_threshold=None,
            semantic_duplicate_threshold=0.85,
            evaluation_conversation_ids={"DOES_NOT_EXIST"},
            reviewers=("reviewer_a", "reviewer_b"),
            run_id="bad-run",
        )
