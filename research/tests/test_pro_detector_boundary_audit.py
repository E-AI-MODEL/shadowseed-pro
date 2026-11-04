"""Synthetic offline tests for deterministic candidate-fate accounting."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import pytest
from research.scripts.pro_detector_boundary_audit import audit, main


def fixture(raw: str, detected: list[str], accepted: int, rejected: int,
            cap: bool = False):
    rows = (
        [{"outcome": "accepted", "reason": None, "source_mapping_status": "canonical"}]
        * accepted +
        [{"outcome": "rejected", "reason": "not_atomic", "source_mapping_status": "canonical"}]
        * rejected
    )
    return {"cases": [{"model_id": "synthetic", "case_id": "C0", "turns": [{
        "turn": 0, "canonical_report": {
            "detector_audit": {"raw_output": raw,
                "parse_diagnostics": {"truncated_after_max_seeds": cap,
                    "explicit_none": raw.strip() == "NONE"}},
            "detected_candidates": detected,
            "intake_diagnostics": {"normalized_candidates": detected,
                "item_lineage": rows},
        }
    }]}]}


def test_cap_flag_does_not_prove_loss():
    src = fixture("1. Alpha?", ["Alpha?"], 1, 0, cap=True)
    result = audit(src)
    assert result["counts"]["cap_flagged_turns"] == 1
    assert result["counts"]["raw_numbered_exceeds_parsed_turns"] == 0
    assert result["parser_flag_is_proof_of_discarded_text"] is False


def test_real_loss_is_recorded_without_claiming_novelty():
    src = fixture("1. Alpha?\n2. Beta?", ["Alpha?"], 1, 0)
    result = audit(src)
    assert result["counts"]["raw_numbered_exceeds_parsed_turns"] == 1
    assert result["counts"]["parsed_candidates"] == 1
    assert result["no_semantic_quality_or_q1q2_proof"] is True


def test_bad_source_hash_fails_before_writing(tmp_path: Path):
    src = tmp_path / "source.json"
    dest = tmp_path / "report.json"
    src.write_text(json.dumps(fixture("NONE", [], 0, 0)))
    with pytest.raises(SystemExit, match="SHA-256 mismatch"):
        main(["--observed", str(src), "--source-sha256", "0" * 64,
              "--output", str(dest)])
    assert not dest.exists()


def test_summary_excludes_raw_candidates(tmp_path: Path):
    src = tmp_path / "source.json"
    dest = tmp_path / "report.json"
    original = "Confidential hypothesis: beta?"
    src.write_text(json.dumps(fixture("1. " + original, [original], 1, 0)))
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    assert main(["--observed", str(src), "--source-sha256", sha,
                 "--output", str(dest)]) == 0
    assert original not in dest.read_text()
