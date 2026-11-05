"""Keep the optional paper smoke aligned with read-only SSOT inspection."""

import json

from shadowseed_research.benchmark.paper_evidence_smoke import run_paper_evidence_smoke


def test_paper_evidence_smoke_requires_review_without_gate_authority(tmp_path):
    output = run_paper_evidence_smoke(str(tmp_path / "paper-smoke.json"))
    result = json.loads(output.read_text(encoding="utf-8"))
    summary = result["summary"]
    assert summary["passed"] is True
    assert summary["blocked_validations"] == 0
    assert summary["unreviewed_candidates"] == 0
    assert summary["review_candidates"] > 0
    assert summary["gate_events_after"] == 0
    assert summary["before_weight"] == 0.0
    assert summary["after_verified_weight"] == 0.0
    assert summary["after_review_weight"] == 0.0
    assert result["review_candidates"]
    assert all(not record["gate_authorized"] for record in result["review_candidates"])
