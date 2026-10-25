"""Blind semantic review PACKAGING ONLY: no automatic Q1/Q2, no independent scores."""

from __future__ import annotations

import copy
from datetime import datetime
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "g0_blind_later_inquiry_review.py"
SPEC = importlib.util.spec_from_file_location("g0_blind_review", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REVIEW = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REVIEW)

FAKE_SECRET = bytes(range(32))  # Only a *unit-test* secret. Real packets use secrets.token_bytes.


def _turn(i: int, *, question: str = "What should I investigate next?") -> dict:
    return {
        "turn_id": f"T{i}",
        "question": question,
        "question_origin": "INVESTIGATOR_SCRIPTED_NO_MODEL",
        "host_answer": "A visible observation, not a verified new idea.",
        "host_answer_origin": "INVESTIGATOR_DEFINED_VISIBLE_STATE_SERIALIZER_NO_MODEL",
        "observed_world_before": {"position": [0, i], "facing": "south"},
        "investigator_action": {"action": "MOVE_DIRECTION", "arg1": "north"},
        "world_action_origin": "INVESTIGATOR_SCRIPTED_INDEPENDENT_OF_SEEDS",
        "world_action_status": "accepted_observable_state_difference",
        "observed_world_after": {"position": [0, i + 1], "facing": "north"},
    }


def _source() -> dict:
    return {
        "schema": REVIEW.SOURCE_SCHEMA,
        "provenance_class": "investigator_scripted_calibration",
        "feedback_regime": "MECHANICS_CALIBRATION",
        "episodes": [
            {
                "private_case_id": "source-arm-X",
                "private_arm": "TOP_SECRET_CANDIDATE_ARM",
                "private_group": "matched-world",
                "turns": [
                    _turn(0, question="What can be observed?"),
                    _turn(1, question="What happened after that action?"),
                ],
                "private_candidate_record": "Never reveal a seed or its condition",
                "private_independent_future_consequence_verified": True,
            },
            {
                "private_case_id": "source-arm-Y",
                "private_arm": "TOP_SECRET_ABLATION_ARM",
                "private_group": "matched-world",
                "turns": [
                    _turn(0, question="What can be observed?"),
                    _turn(1, question="What happened after that action?"),
                ],
                "private_candidate_record": None,
                "private_independent_future_consequence_verified": False,
            },
        ],
    }


def _reviewer(template: dict, reviewer: str) -> dict:
    form = copy.deepcopy(template)
    form["reviewer_id"] = reviewer
    form["human_independence_declared"] = True
    form["reviewer_timestamp_iso8601"] = "2026-10-25T07:37:00+01:00"
    for row in form["reviews"]:
        row["distinct_from_prior_questions"] = "uncertain"
        row["testable_under_independent_rules"] = "uncertain"
        row["later_consequence_observed"] = "not_demonstrated"
        row["evidence_turn_ids"] = ["T0", "T1"]
        row["reasoned_explanation"] = (
            "The observable event sequence is scripted, so no model-originated "
            "later inquiry can be established from these two turns."
        )
        row["stronger_ordinary_model_or_human_explanation"] = (
            "Ordinary exploration and investigator-authored actions explain the sequence."
        )
    return form


def _bridge() -> dict:
    """Small synthetic *shape* of PR232, not an independently generated outcome."""
    turns = []
    for i in range(4):
        t = _turn(i)
        t.update({
            "question_origin": "INVESTIGATOR_SCRIPTED_NO_MODEL",
            "host_answer_origin": "INVESTIGATOR_DEFINED_VISIBLE_STATE_SERIALIZER_NO_MODEL",
            "world_action_origin": "INVESTIGATOR_SCRIPTED_INDEPENDENT_OF_SEEDS",
            "seed_authority_uses": 0,
            "Gate_events": 0,
            "semantic_novelty": "NOT_ASSESSED",
            "semantic_seed_growth": "NOT_ASSESSED",
            "new_later_investigability": "NOT_ASSESSED",
            "detector_output_raw": "1. An authored candidate" if i == 0 else "NONE",
            "true_seed_born_this_turn": ["An authored candidate"] if i == 0 else [],
            "existing_seed_redetected_this_turn": [],
        })
        turns.append(t)
    return {
        "schema": "g0-real-shadowchat-discoveryworld-bridge-audit-v0",
        "status": "model_free_product_pipeline_plus_real_world_mechanics_only",
        "source": "INVESTIGATOR_SCRIPTED_NO_LLM",
        "model_calls": 0,
        "embedding_hosted_calls": 0,
        "Q1_measured": False,
        "Q2_measured": False,
        "g0_passed": False,
        "upstream_sha": "fd591323920be0d3786ef350955de1945aa571e5",
        "same_world_observations_and_investigator_actions_in_both_arms": True,
        "arms": {
            "scripted_seed": {
                "seed_authority_uses": 0, "Gate_events": 0, "hosted_model_calls": 0,
                "has_real_persistent_ShadowChatSession": True,
                "final_seed_state": [{"text": "scripted", "weight": 0}],
                "turns": copy.deepcopy(turns),
            },
            "explicit_none": {
                "seed_authority_uses": 0, "Gate_events": 0, "hosted_model_calls": 0,
                "has_real_persistent_ShadowChatSession": True,
                "final_seed_state": [],
                "turns": copy.deepcopy(turns),
            },
        },
    }


def test_blind_packet_is_hash_bound_and_cannot_leak_treatment_or_outcome_hints() -> None:
    source = _source()
    packet, private, blank = REVIEW.create_pack(source, FAKE_SECRET)
    assert packet["schema"] == REVIEW.PACK_SCHEMA
    assert packet["G0_status"] == "NOT_PASSED"
    assert packet["Q1_or_Q2_result_established"] is False
    assert packet["independent_semantic_review_completed"] is False
    assert len(packet["episodes"]) == 2
    assert len({x["matched_group"] for x in packet["episodes"]}) == 1
    assert len({x["blind_id"] for x in packet["episodes"]}) == 2
    assert blank["G0_approval"] is False
    assert all(x["distinct_from_prior_questions"] is None for x in blank["reviews"])
    public = json.dumps(packet)
    for secret in (
        "TOP_SECRET_CANDIDATE_ARM", "TOP_SECRET_ABLATION_ARM",
        "source-arm-X", "source-arm-Y", "Never reveal a seed",
        "private_independent_future_consequence_verified",
        "required_later_consequence_present",
        "secret_hex", "private_candidate_record",
    ):
        assert secret not in public
    assert private["owner_only_never_publish"] is True
    assert all("private_arm" in c for c in private["mapping"])
    assert "secret_hex" not in private
    assert packet["content_sha256"] == REVIEW.fingerprint(
        {k: v for k, v in packet.items() if k != "content_sha256"}
    )


def test_public_calibrations_are_explicitly_not_q1_q2_and_no_auto_scores() -> None:
    packet, _, blank = REVIEW.create_pack(_source(), FAKE_SECRET)
    assert all(c["review_scope"].startswith("RESEARCHER_SCRIPTED") for c in packet["episodes"])
    assert blank["automated_semantic_verdict"] is None
    assert all(r["later_consequence_observed"] is None for r in blank["reviews"])
    assert not any("candidate" in r for r in blank["reviews"])


def test_tampered_packet_and_incomplete_review_are_rejected() -> None:
    packet, _, blank = REVIEW.create_pack(_source(), FAKE_SECRET)
    with pytest.raises(ValueError, match="reviewer identity"):
        REVIEW.validate_completed_review(packet, blank)
    complete = _reviewer(blank, "Independent Reviewer A")
    REVIEW.validate_completed_review(packet, complete)
    modified = copy.deepcopy(packet)
    modified["episodes"][0]["evidence_turns"][0]["question"] = "Injected answer"
    with pytest.raises(ValueError, match="original blind packet was changed"):
        REVIEW.validate_completed_review(modified, complete)
    wrong = copy.deepcopy(complete)
    wrong["packet_sha256"] = "x" * 64
    with pytest.raises(ValueError, match="does not correspond"):
        REVIEW.validate_completed_review(packet, wrong)
    inserted = copy.deepcopy(complete)
    inserted["reviews"][0]["later_consequence_observed"] = "verified_later_consequence"
    with pytest.raises(ValueError, match="scripted-only"):
        REVIEW.validate_completed_review(packet, inserted)
    alleged_approval = copy.deepcopy(complete)
    alleged_approval["G0_approval"] = True
    with pytest.raises(ValueError, match="forbidden"):
        REVIEW.validate_completed_review(packet, alleged_approval)


def test_only_two_attributed_reviews_can_be_reconciled_and_never_pass_g0() -> None:
    packet, private, blank = REVIEW.create_pack(_source(), FAKE_SECRET)
    a = _reviewer(blank, "External Reviewer One")
    b = _reviewer(blank, "External Reviewer Two")
    with pytest.raises(ValueError, match="distinct human reviewers"):
        REVIEW.reconcile(packet, private, a, copy.deepcopy(a))
    result = REVIEW.reconcile(packet, private, a, b)
    assert result["status"] == "STRUCTURAL_RECONCILIATION_NOT_G0_APPROVAL"
    assert result["human_identity_and_independence_still_require_external_verification"]
    assert result["G0_passed"] is result["Q2_causality_established"] is False
    assert len(result["comparisons"]) == 2
    assert all(x["causal_seed_contribution_established"] is False for x in result["comparisons"])


def test_unknown_novelty_is_not_forced_to_false() -> None:
    packet, private, blank = REVIEW.create_pack(_source(), FAKE_SECRET)
    r1 = _reviewer(blank, "Reviewer One")
    r2 = _reviewer(blank, "Reviewer Two")
    r2["reviews"][0]["distinct_from_prior_questions"] = "materially_different"
    out = REVIEW.reconcile(packet, private, r1, r2)
    assert any(x["human_disagreement_unresolved"] for x in out["comparisons"])
    assert out["G0_passed"] is False


def test_bad_input_provenance_cannot_claim_real_model_or_rf_ri_feedback() -> None:
    source = _source()
    source["feedback_regime"] = "RI"
    with pytest.raises(ValueError, match="must not masquerade"):
        REVIEW.create_pack(source, FAKE_SECRET)
    source = _source()
    source["provenance_class"] = "recorded_model_unverified"
    source["feedback_regime"] = "RI"
    with pytest.raises(ValueError, match="raw evidence reference"):
        REVIEW.create_pack(source, FAKE_SECRET)
    source = _source()
    source["episodes"][0]["turns"][0]["turn_id"] = "T10"
    with pytest.raises(ValueError, match="nonconsecutive"):
        REVIEW.create_pack(source, FAKE_SECRET)


def test_model_episodes_keep_unverified_origin_and_private_outcome_private() -> None:
    model = _source()
    model["provenance_class"] = "recorded_model_unverified"
    model["feedback_regime"] = "RI"
    for case in model["episodes"]:
        case["private_raw_trace_ref"] = "PRIVATE_SHA_OR_LOG"
        case["turns"][1]["question_origin"] = "MODEL_GENERATED_RECORDED_UNVERIFIED"
    packet, private, blank = REVIEW.create_pack(model, FAKE_SECRET)
    assert all(x["review_scope"] == "MODEL_OUTPUT_PROVENANCE_NOT_INDEPENDENTLY_VERIFIED"
               for x in packet["episodes"])
    assert "TOP_SECRET_CANDIDATE_ARM" not in json.dumps(packet)
    assert "private_independent_future_consequence_verified" not in json.dumps(packet)
    assert blank["G0_approval"] is False
    assert private["owner_only_never_publish"]


def test_verified_bridged_run_is_calibration_only_and_bad_source_fails_closed() -> None:
    bridge = _bridge()
    source = REVIEW.source_from_verified_bridge(bridge, b"verified shape only")
    packet, private, blank = REVIEW.create_pack(source, FAKE_SECRET)
    assert source["provenance_class"] == "investigator_scripted_calibration"
    assert all(x["review_scope"].startswith("RESEARCHER_SCRIPTED") for x in packet["episodes"])
    assert all(x["private_candidate_record"] for x in private["mapping"])
    assert blank["G0_approval"] is False
    poisoned = copy.deepcopy(bridge)
    poisoned["model_calls"] = 1
    with pytest.raises(ValueError, match="provenance"):
        REVIEW.source_from_verified_bridge(poisoned, b"wrong")
    poisoned = copy.deepcopy(bridge)
    poisoned["arms"]["scripted_seed"]["turns"][1]["observed_world_after"]["position"] = [3, 9]
    with pytest.raises(ValueError, match="not actually identical"):
        REVIEW.source_from_verified_bridge(poisoned, b"wrong")
    poisoned = copy.deepcopy(bridge)
    poisoned["arms"]["explicit_none"]["turns"][0]["seed_authority_uses"] = 1
    with pytest.raises(ValueError, match="stronger or untraceable"):
        REVIEW.source_from_verified_bridge(poisoned, b"wrong")


def test_owner_file_is_created_with_private_mode(tmp_path: Path) -> None:
    p = tmp_path / "owner-only.json"
    REVIEW._safe_write_json(p, {"secret": "not for GitHub"}, private=True)
    assert p.exists()
    assert p.stat().st_mode & 0o077 == 0
    with pytest.raises(FileExistsError):
        REVIEW._safe_write_json(p, {"secret": "accidental overwrite"}, private=True)


def test_end_to_end_cli_owner_separation_and_structural_only_review(tmp_path: Path) -> None:
    source = tmp_path / "owner-source.json"
    packet_path = tmp_path / "reviewer" / "blind.json"
    blank_path = tmp_path / "reviewer" / "blank.json"
    owner = tmp_path / "owner" / "mapping.json"
    source.write_text(json.dumps(_source()), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT),
            "prepare", "--input", str(source),
            "--packet", str(packet_path),
            "--blank-review", str(blank_path),
            "--owner-map", str(owner),
        ],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    assert owner.stat().st_mode & 0o077 == 0
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    blank = json.loads(blank_path.read_text(encoding="utf-8"))
    source_repr = packet_path.read_text(encoding="utf-8")
    assert "TOP_SECRET_CANDIDATE_ARM" not in source_repr
    assert packet["G0_status"] == "NOT_PASSED"
    assert all(v["distinct_from_prior_questions"] is None for v in blank["reviews"])

    review_a = tmp_path / "first.json"
    review_b = tmp_path / "second.json"
    review_a.write_text(json.dumps(_reviewer(blank, "Fake Fixture Reviewer A")), encoding="utf-8")
    review_b.write_text(json.dumps(_reviewer(blank, "Fake Fixture Reviewer B")), encoding="utf-8")
    unblinded = tmp_path / "owner" / "reconciled.json"
    result = subprocess.run(
        [
            sys.executable, str(SCRIPT), "reconcile",
            "--packet", str(packet_path),
            "--owner-map", str(owner),
            "--review-one", str(review_a),
            "--review-two", str(review_b),
            "--output", str(unblinded),
        ],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0, result.stderr
    decoded = json.loads(unblinded.read_text(encoding="utf-8"))
    assert decoded["G0_passed"] is False
    assert decoded["Q2_causality_established"] is False
    assert decoded["human_identity_and_independence_still_require_external_verification"] is True
    assert len(decoded["comparisons"]) == 2


def test_undated_or_timezone_naive_review_does_not_pass_reconciliation() -> None:
    packet, private, blank = REVIEW.create_pack(_source(), FAKE_SECRET)
    good = _reviewer(blank, "Independent Reviewer A")
    bad = _reviewer(blank, "Independent Reviewer B")
    bad["reviewer_timestamp_iso8601"] = "not-an-actual-date"
    with pytest.raises(ValueError, match="valid ISO-8601"):
        REVIEW.reconcile(packet, private, good, bad)
    bad["reviewer_timestamp_iso8601"] = "2026-10-25T07:37:00"
    with pytest.raises(ValueError, match="timezone"):
        REVIEW.reconcile(packet, private, good, bad)
