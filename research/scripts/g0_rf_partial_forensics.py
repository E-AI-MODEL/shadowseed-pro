"""Offline audit of an ACTUAL partial RF model artifact, with no API calls.

Inputs are a GitHub Action's original observed.json or its single-entry ZIP.
No raw text is emitted. This only verifies *archived* records. It cannot
reconstruct a missing internal Engine manager state or diagnose the exact
ValueError thrown at the second follow-up.

Usage:
  python research/scripts/g0_rf_partial_forensics.py \
      /path/to/observed.json --expected-sha256 <pinned-json-sha>

Do not treat this result as a G0 pass, Q1/Q2 measurement, independent
semantic validation, new-seed proof from internal activations, or a complete
RI run. The original paper trail is fixed to run 40224494313.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile
from typing import Any


SCHEMA = "ssl-rf-real-seed-observations-v1"
RESULT_SCHEMA = "shadowseed-rf-partial-forensics-v1"
SOURCE_RUN = 40224494313


def digest_json(value: Any) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()


def digest_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _verify_snapshot(obj: dict, label: str) -> None:
    _require(
        isinstance(obj, dict)
        and obj.get("snapshot_sha256")
        == digest_json({k: v for k, v in obj.items() if k != "snapshot_sha256"}),
        label + " snapshot missing or altered",
    )


def read_record(path: Path) -> tuple[dict, str]:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as z:
            infos = z.infolist()
            _require(
                len(infos) == 1
                and infos[0].filename == "observed.json"
                and infos[0].file_size < 5_000_000
                and not infos[0].is_dir(),
                "expected a single small observed.json inside artifact ZIP",
            )
            raw = z.read(infos[0])
    elif path.suffix.lower() == ".json":
        raw = path.read_bytes()
        _require(len(raw) < 5_000_000, "unreasonably large model result")
    else:
        raise ValueError("only raw observed.json or official artifact ZIP supported")
    result = json.loads(raw)
    _require(isinstance(result, dict), "observed record must be an object")
    return result, hashlib.sha256(raw).hexdigest()


def audit(data: dict, *, actual_file_digest: str) -> dict[str, Any]:
    """Check identities and history copies, not the unrecorded T2 manager."""
    _require(data.get("schema") == SCHEMA, "not the correct RF artifact schema")
    _require(
        data.get("status") == "incomplete_exploratory_not_a_null_result"
        and data.get("failure_type") == "ValueError",
        "wrong or unexpectedly completed research run",
    )
    _require(
        data.get("G0") == "NOT_PASSED"
        and data.get("q1_internal_absence_established") is False
        and data.get("q2_causal_novel_inquiry_established") is False
        and data.get("no_closed_loop_feedback") is True,
        "research evidence boundaries were altered",
    )
    turns = data.get("turns")
    _require(isinstance(turns, list) and len(turns) == 3, "not three recorded turns")
    reports: list[dict] = []
    for idx, turn in enumerate(turns):
        report = turn.get("canonical_report")
        _require(
            turn.get("turn") == idx
            and isinstance(report, dict)
            and report.get("turn") == idx
            and report.get("runtime_mode") == "live"
            and report.get("answer") == turn.get("host_answer"),
            "invalid or reordered canonical turn",
        )
        _require(
            report.get("selected_seed_ids") == []
            and report.get("surfaced_seed_ids") == []
            and report.get("same_turn_revision_applied") is False
            and report.get("self_reinforcement_applied") is False
            and turn.get("none_control_answer_identical") is True,
            "an untrusted seed may have influenced ordinary answering",
        )
        reports.append(report)
    _require(
        not turns[0].get("arms")
        and set(turns[1].get("arms", {})) == set("ABCDE")
        and not turns[2].get("arms")
        and turns[2].get("followup") is None,
        "T1 arms or fail-closed T2 were silently changed",
    )

    birth = turns[0].get("birth")
    followup = turns[1].get("followup")
    _verify_snapshot(birth, "first birth")
    _verify_snapshot(followup, "T1 longitudinal")
    seed = data.get("first_seed")
    _require(isinstance(seed, dict), "no genuinely recorded seed")
    _require(
        seed.get("id") == birth.get("seed_id") == followup.get("seed_id")
        and seed.get("birth_snapshot_sha256") == birth.get("snapshot_sha256")
        and followup.get("birth_snapshot_sha256") == birth.get("snapshot_sha256")
        and digest_text(seed.get("text", "")) == birth.get("candidate_text_sha256")
        and seed.get("weight") == 0
        and seed.get("evidence_count") == 0,
        "candidate identity, birth text, or zero-authority state does not match",
    )
    accepted = [
        a for a in reports[0].get("intake_diagnostics", {}).get("accepted", [])
        if a.get("seed_id") == seed["id"]
    ]
    _require(
        len(accepted) == 1
        and digest_json(accepted[0]) == birth.get("accepted_candidate_sha256")
        and digest_json(reports[0].get("candidate_observations", []))
        == birth.get("detector_observations_sha256")
        and reports[0].get("seeds_born_weightless", []).count(seed["id"]) == 1,
        "original canonical T0 detector-to-birth trail disagrees",
    )
    _require(
        followup.get("turn") == 1
        and followup.get("history_sha256") == digest_json(reports[:2])
        and followup.get("turn_report_sha256") == digest_json(reports[1])
        and followup.get("seed_state_after_turn", {}).get("weight") == 0
        and followup.get("seed_state_after_turn", {}).get("evidence_count") == 0
        and followup.get("product_answer_seed_influence_observed") is False,
        "T1 snapshot does not match the stored T0/T1 reports",
    )
    _require(
        followup.get("candidate_text_sha256") == birth.get("candidate_text_sha256")
        and followup.get("previous_checkpoint_sha256") is None,
        "T1 snapshot candidate or chronology changed",
    )

    audit_row = data.get("provider_audit", {})
    _require(
        audit_row.get("model_calls") == 14
        and audit_row.get("recorded_tokens") == 37503
        and audit_row.get("embedding_calls") == 10,
        "not the recorded source-run provider receipt counts",
    )
    stages = [
        e.get("stage")
        for e in audit_row.get("events", [])
        if isinstance(e, dict) and e.get("stage")
    ]
    _require(
        all(f"research_inquiry_t1_{arm}" in stages for arm in "ABCDE")
        and all(f"research_inquiry_t2_{arm}" not in stages for arm in "ABCDE")
        and "host_t2" in stages
        and "detector_t2" in stages,
        "provider stage evidence disagrees with T1/T2 records",
    )
    return {
        "schema": RESULT_SCHEMA,
        "source_run": SOURCE_RUN,
        "source_observed_sha256": actual_file_digest,
        "G0": "NOT_PASSED",
        "first_seed_born_and_identity_recorded": True,
        "t0_first_birth_snapshot_hash_verified": True,
        "t1_followup_snapshot_hash_verified": True,
        "t1_archived_history_matches_checkpoint_hash": True,
        "t1_archived_turn_report_matches_checkpoint_hash": True,
        "ordinary_answer_seed_exposure_recorded": False,
        "t1_model_authored_question_records": len(turns[1]["arms"]),
        "t2_host_and_detector_completed_before_error": True,
        "t2_model_authored_question_records": 0,
        "source_provider_calls": audit_row["model_calls"],
        "source_embedding_calls": audit_row["embedding_calls"],
        "source_recorded_tokens": audit_row["recorded_tokens"],
        "exact_t2_checkpoint_error_reason": "UNKNOWN_NOT_PRESERVED_IN_SOURCE_ARTIFACT",
        "t2_manager_event_gate_and_seed_state": "UNRECORDED_CANNOT_VERIFY",
        "q1_or_q2_effect_established": False,
        "independent_review_completed": False,
        "authoritative_conclusion": (
            "T0 birth and archived T1 records pass hash checks; the T2 "
            "ValueError cannot be diagnosed from this partial archive alone."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=Path)
    parser.add_argument(
        "--expected-sha256", required=True,
        help="Hash of raw observed.json, not hash of outer ZIP",
    )
    args = parser.parse_args()
    data, raw_hash = read_record(args.artifact)
    if raw_hash != args.expected_sha256:
        raise ValueError("original observed.json bytes differ from expected SHA-256")
    print(json.dumps(audit(data, actual_file_digest=raw_hash),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
