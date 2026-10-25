"""Historical SSOT polarity defect remains attributable to PR #240.

The *current* code is exercised through actual product SSOT + Gate objects;
researcher-assigned labels are never presented as independent truth evidence.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SCRIPT = SCRIPTS / "g0_ssot_evidence_polarity_preflight.py"
SPEC = importlib.util.spec_from_file_location("g0_ssot_polarity_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_unreviewed_and_opposing_sources_do_not_gain_authority() -> None:
    r = MODULE.build_result()
    assert r["status"] == (
        "researcher_asserted_relations_read_only_no_gate_authority"
    )
    for name in (
        "affirmation_without_relation",
        "explicit_negation_with_author_opposition",
        "unverified_with_author_support",
    ):
        case = r["cases"][name]
        assert case["review_candidate_count"] == 0
        assert case["gate_events"] == []
        assert case["final_seed"]["weight"] == 0
        assert case["final_seed"]["evidence_count"] == 0


def test_researcher_declared_support_yields_candidates_not_authority() -> None:
    r = MODULE.build_result()
    affirmative = r["cases"]["affirmation_with_author_support"]
    assert affirmative["review_candidate_count"] == 4
    assert affirmative["gate_events"] == []
    assert affirmative["gate_authorized"] is False
    assert affirmative["candidate_review_required"] is True
    assert affirmative["final_seed"]["weight"] == 0.0
    assert affirmative["final_seed"]["evidence_count"] == 0
    assert affirmative["final_seed"]["status"] != "PROMOTED"
    assert all(
        case["gate_authorized"] is False and case["gate_events"] == []
        for case in r["cases"].values()
    )


def test_search_still_retrieves_explicitly_negative_source() -> None:
    r = MODULE.build_result()
    opposing = r["cases"]["explicit_negation_with_author_opposition"]
    assert len(opposing["retrieval_hits"]) == 4
    assert min(row["similarity"] for row in opposing["retrieval_hits"]) > 0.65
    assert all(" niet" in text.lower() for text in MODULE.NEGATING)
    assert not opposing["gate_events"]


def test_historical_baseline_is_explicitly_archived_not_misreported_as_new() -> None:
    r = MODULE.build_result()
    history = r["historic_pre_fix_result"]
    assert history["original_git_commit"] == (
        "4c433c6e95733491e4b4720950bf997f5f1af634"
    )
    assert history["source"].endswith("/40176388209")
    assert history["affirmation"]["ssot_support"] == 4
    assert history["explicit_negation"]["ssot_support"] == 4
    assert history["explicit_negation"]["final_weight"] == 0.6
    assert "not re-executed" in history["note"]


def test_results_have_no_independent_verification_claims(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "ssot-polarity-after-fix.json"
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--output", str(output)])
    MODULE.main()
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema"] == "g0-ssot-polarity-read-only-handoff-v2"
    assert result["model_calls"] == result["human_verifiers"] == 0
    assert result["no_research_gate_or_polarity_classifier"] is True
    assert result["authorized_actor_submissions"] == 0
    assert result["intermediate_unsafe_attestation_run"].endswith("/40182789691")
    assert result["current_product_code_executed"] is True
    assert result["input_provenance"] == "INVESTIGATOR_AUTHORED_FICTIONAL_POLARITIES"
    assert result["Q1_tested"] is result["Q2_tested"] is result["G0_passed"] is False
    assert result["observations_are_not_independent_truth_labels"] is True
