"""Contract tests for the research-only relational review audit."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_relational_reviews.py"
_spec = importlib.util.spec_from_file_location("audit_relational_reviews", SCRIPT)
assert _spec and _spec.loader
AUDIT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(AUDIT)


def _write(path: Path, reviewer="a", *, different=False):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=AUDIT.FIELDS)
        writer.writeheader()
        for case_id, relation, score, proposed in [
            ("R01", "SAME_CLAIM", "0", ""),
            ("R02", "BROAD_ONLY", "1", ""),
            ("R03", "RELATED_DISTINCT", "2", "Test a different future question"),
        ]:
            if different and case_id == "R03":
                relation, score = "UNCERTAIN", "1"
            writer.writerow(dict(
                case_id=case_id, relation=relation,
                usefulness_0_to_3=score,
                specific_new_test_if_any=proposed,
                evidence_for_relation="Citation to blind text only",
                reason_for_rating="No additional evidence",
                reviewer_id=reviewer,
            ))


def test_single_pass_is_draft_not_independent_evidence(tmp_path):
    path = tmp_path / "review.csv"
    _write(path)
    report = AUDIT.make_audit(AUDIT.read_review(path))
    assert report["review_status"] == "single_rater_draft"
    assert report["g0_status"] == "NOT_PASSED"
    assert report["reviewer_independence_verified"] is False
    assert report["source_pair_text_inspected"] is False
    assert report["shadowseed_incremental_benefit_established"] is False
    assert report["first_review"]["relations"]["SAME_CLAIM"] == 1
    assert report["first_review"]["test_proposal_case_ids"] == ["R03"]


def test_two_raters_keep_disagreements_not_false_independence(tmp_path):
    p1, p2 = tmp_path / "one.csv", tmp_path / "two.csv"
    _write(p1)
    _write(p2, "b", different=True)
    report = AUDIT.make_audit(AUDIT.read_review(p1), AUDIT.read_review(p2))
    assert report["comparison"]["different_annotations"] == 1
    assert report["comparison"]["differences"][0]["case_id"] == "R03"
    assert report["comparison"]["independent_review_completed"] is False
    assert report["g0_status"] == "NOT_PASSED"


def test_duplicate_case_and_incomplete_fields_fail(tmp_path):
    path = tmp_path / "review.csv"
    _write(path)
    data = path.read_text(encoding="utf-8")
    path.write_text(data + data.splitlines()[-1] + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="repeated case_id"):
        AUDIT.read_review(path)
    _write(path)
    path.write_text(path.read_text().replace("Citation to blind text only", ""), encoding="utf-8")
    with pytest.raises(ValueError, match="empty evidence_for_relation"):
        AUDIT.read_review(path)


def test_mismatched_cases_and_same_rater_fail(tmp_path):
    p1, p2 = tmp_path / "one.csv", tmp_path / "two.csv"
    _write(p1)
    _write(p2)
    with pytest.raises(ValueError, match="cannot share"):
        AUDIT.make_audit(AUDIT.read_review(p1), AUDIT.read_review(p2))
    _write(p2, "b")
    p2.write_text(p2.read_text().replace("R03", "R04"), encoding="utf-8")
    with pytest.raises(ValueError, match="different case_id"):
        AUDIT.make_audit(AUDIT.read_review(p1), AUDIT.read_review(p2))


def test_cli_output_is_new_file_and_never_overwrites_reviews(tmp_path):
    source = tmp_path / "review.csv"
    output = tmp_path / "audit.json"
    _write(source)
    assert AUDIT.main(["--review", str(source), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["first_review"]["case_count"] == 3
    with pytest.raises(FileExistsError):
        AUDIT.main(["--review", str(source), "--output", str(output)])
    with pytest.raises(SystemExit):
        AUDIT.main(["--review", str(source), "--output", str(source)])


def test_invalid_relation_is_not_silently_classified(tmp_path):
    path = tmp_path / "review.csv"
    _write(path)
    path.write_text(path.read_text().replace("BROAD_ONLY", "NEW_DISCOVERY"), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid relation"):
        AUDIT.read_review(path)


def test_none_sentinel_is_not_a_test_proposal(tmp_path):
    source = tmp_path / "review.csv"
    _write(source)
    text = source.read_text(encoding="utf-8")
    text = text.replace("SAME_CLAIM,0,,", "SAME_CLAIM,0,none,")
    text = text.replace("BROAD_ONLY,1,,", "BROAD_ONLY,1,NONE,")
    source.write_text(text, encoding="utf-8")
    result = AUDIT.make_audit(AUDIT.read_review(source))
    assert result["first_review"]["test_proposal_case_ids"] == ["R03"]


def test_second_reviewer_proposals_count_and_agreement(tmp_path):
    source_a, source_b = tmp_path / "first.csv", tmp_path / "second.csv"
    _write(source_a)
    _write(source_b, "b", different=True)
    result = AUDIT.make_audit(AUDIT.read_review(source_a), AUDIT.read_review(source_b))
    assert result["second_review"]["test_proposal_case_ids"] == ["R03"]
    assert result["comparison"]["same_relation"] == 2
    assert result["comparison"]["same_usefulness"] == 2
    assert result["comparison"]["same_test_proposal"] == 3
