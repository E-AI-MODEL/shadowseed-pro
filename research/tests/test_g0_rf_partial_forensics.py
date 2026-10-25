"""No-network checks for the archived-partial RF forensic reader.

The fake record tests the audit contract, not the original live manager.
The real 110 KB partial artifact is intentionally NOT committed here; it is
pinned by SHA-256 in the 25-Oct forensic note and can be replayed offline.
"""
from __future__ import annotations

import copy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "g0_rf_partial_forensics.py"
SPEC = importlib.util.spec_from_file_location("g0_rf_partial_forensics", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def source_record() -> dict:
    sid = "ss_001"
    seedtext = "Onbewezen ruimtelijk verschil tussen beide meetpunten."
    accepted = {"seed_id": sid, "text": seedtext}
    observations = [{"candidate": seedtext, "ssl_exposed": False}]
    reports = []
    turns = []
    for i in range(3):
        report = {
            "turn": i, "runtime_mode": "live",
            "question": f"question-{i}", "answer": f"answer-{i}",
            "seeds_born_weightless": [sid] if i == 0 else [],
            "selected_seed_ids": [], "surfaced_seed_ids": [],
            "same_turn_revision_applied": False,
            "self_reinforcement_applied": False,
            "intake_diagnostics": {"accepted": [accepted] if i == 0 else []},
            "candidate_observations": observations if i == 0 else [],
        }
        reports.append(report)
        turns.append({
            "turn": i, "canonical_report": report, "host_answer": report["answer"],
            "none_control_answer_identical": True, "birth": None,
            "followup": None,
            "arms": {a: {"text": a} for a in "ABCDE"} if i == 1 else {},
        })
    birth = {
        "seed_id": sid, "candidate_text_sha256": module.digest_text(seedtext),
        "accepted_candidate_sha256": module.digest_json(accepted),
        "detector_observations_sha256": module.digest_json(observations),
    }
    birth["snapshot_sha256"] = module.digest_json(birth)
    followup = {
        "seed_id": sid, "turn": 1,
        "birth_snapshot_sha256": birth["snapshot_sha256"],
        "candidate_text_sha256": birth["candidate_text_sha256"],
        "history_sha256": module.digest_json(reports[:2]),
        "turn_report_sha256": module.digest_json(reports[1]),
        "previous_checkpoint_sha256": None,
        "seed_state_after_turn": {"weight": 0, "evidence_count": 0},
        "product_answer_seed_influence_observed": False,
    }
    followup["snapshot_sha256"] = module.digest_json(followup)
    turns[0]["birth"] = birth
    turns[1]["followup"] = followup
    return {
        "schema": module.SCHEMA,
        "status": "incomplete_exploratory_not_a_null_result",
        "failure_type": "ValueError", "G0": "NOT_PASSED",
        "q1_internal_absence_established": False,
        "q2_causal_novel_inquiry_established": False,
        "no_closed_loop_feedback": True,
        "first_seed": {
            "id": sid, "text": seedtext,
            "birth_snapshot_sha256": birth["snapshot_sha256"],
            "weight": 0, "evidence_count": 0,
        },
        "turns": turns,
        "provider_audit": {
            "model_calls": 14, "embedding_calls": 10,
            "recorded_tokens": 37503,
            "events": [
                {"stage": f"research_inquiry_t1_{a}"} for a in "ABCDE"
            ] + [{"stage": "host_t2"}, {"stage": "detector_t2"}],
        },
    }


def test_synthetic_partial_proves_only_archived_birth_and_t1_hashes():
    summary = module.audit(source_record(), actual_file_digest="a" * 64)
    assert summary["first_seed_born_and_identity_recorded"] is True
    assert summary["t1_archived_history_matches_checkpoint_hash"] is True
    assert summary["t1_model_authored_question_records"] == 5
    assert summary["t2_model_authored_question_records"] == 0
    assert summary["exact_t2_checkpoint_error_reason"].startswith("UNKNOWN_")
    assert summary["t2_manager_event_gate_and_seed_state"].startswith("UNRECORDED_")
    assert summary["G0"] == "NOT_PASSED"
    assert summary["q1_or_q2_effect_established"] is False


@pytest.mark.parametrize("damage", [
    "birth", "prior_history", "reorder", "t2_questions",
    "gate_exposure", "t2_failure_disguised_as_none", "not_independent",
])
def test_cannot_launder_corrupt_or_overclaimed_partial_as_valid(damage):
    d = source_record()
    if damage == "birth":
        d["turns"][0]["birth"]["candidate_text_sha256"] = "fake"
    elif damage == "prior_history":
        d["turns"][1]["followup"]["history_sha256"] = "fake"
    elif damage == "reorder":
        d["turns"][2]["canonical_report"]["turn"] = 1
    elif damage == "t2_questions":
        d["turns"][2]["arms"]["D"] = {"text": "fake"}
    elif damage == "gate_exposure":
        d["turns"][2]["canonical_report"]["selected_seed_ids"] = ["ss_001"]
    elif damage == "t2_failure_disguised_as_none":
        d["status"] = "completed_no_seed_no_q2_opportunity"
    elif damage == "not_independent":
        d["q2_causal_novel_inquiry_established"] = True
    else:
        raise AssertionError(damage)
    with pytest.raises(ValueError):
        module.audit(d, actual_file_digest="b" * 64)


def test_reads_zip_only_with_one_single_small_json(tmp_path):
    d = source_record()
    encoded = json.dumps(d, ensure_ascii=False).encode()
    zp = tmp_path / "real-run.zip"
    with zipfile.ZipFile(zp, "w") as f:
        f.writestr("observed.json", encoded)
    loaded, digest = module.read_record(zp)
    assert digest == sha256(encoded).hexdigest()
    assert loaded == d
    with zipfile.ZipFile(zp, "a") as f:
        f.writestr("extra.json", b"{}")
    with pytest.raises(ValueError, match="single"):
        module.read_record(zp)


def test_rejects_wrong_file_type(tmp_path):
    p = tmp_path / "other.txt"
    p.write_text("{}")
    with pytest.raises(ValueError, match="only raw"):
        module.read_record(p)
