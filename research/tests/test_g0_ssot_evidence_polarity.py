"""No-model source-traceable characterization of SSOT polarity misattribution.

All semantic polarities are explicitly *researcher-authored synthetic controls*;
this is not an independent entailment assessment or Q1/Q2 result. The test
locks what the current canonical SSOT + Gate implementation does so an
authority error cannot be hidden behind an unrelated model benchmark.
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


def test_explicitly_opposing_synthetic_statements_receive_same_support_direction() -> None:
    r = MODULE.build_result()
    a, b = r["cases"]["affirmation"], r["cases"]["explicit_negation"]
    assert r["status"] == "existing_product_code_characterized_not_repaired"
    assert a["accepted_evidence_count"] == b["accepted_evidence_count"] == 4
    assert all(
        signal == "support"
        for case in (a, b)
        for event in case["gate_decisions"]
        for signal in event["directions"]
    )
    assert len(a["gate_decisions"]) == len(b["gate_decisions"]) == 4
    assert all(
        all(ref and ref.startswith("g0_") for ref in event["source_refs"])
        for case in (a, b)
        for event in case["gate_decisions"]
    )
    assert a["final_seed"]["weight"] > 0
    assert b["final_seed"]["weight"] > 0
    assert a["final_seed"]["evidence_count"] == b["final_seed"]["evidence_count"]


def test_author_supplied_polarity_is_distinct_from_computed_similarity() -> None:
    assert all(" niet" not in text.lower() for text in MODULE.AFFIRMING)
    assert all(" niet" in text.lower() for text in MODULE.NEGATING)
    r = MODULE.build_result()
    for case in r["cases"].values():
        assert case["final_seed"]["text"] == r["hypothesis"]
        assert case["final_seed"]["occurrence_count"] == 3
        assert len(case["retrieval_hits"]) == 4
    a, b = r["cases"]["affirmation"], r["cases"]["explicit_negation"]
    assert min(x["similarity"] for x in a["retrieval_hits"]) > 0.65
    assert min(x["similarity"] for x in b["retrieval_hits"]) > 0.65
    assert b["input_polarity_author_label_not_model_judgment"] == "author_negates"
    assert not r["observations_are_not_independent_truth_labels"] is False


def test_unverified_new_model_text_does_not_gain_ssot_authority() -> None:
    r = MODULE.build_result()
    none = r["cases"]["unverified_negation"]
    assert none["accepted_evidence_count"] == 0
    assert not none["gate_decisions"]
    assert all(hit["status"] == "proposed" for hit in none["retrieval_hits"])
    assert none["final_seed"]["weight"] == 0
    assert none["final_seed"]["evidence_count"] == 0


def test_result_is_research_only_without_new_signal_policy_or_model_claims(tmp_path: Path) -> None:
    output = tmp_path / "g0-ssot-polarity.json"
    sys.argv = [str(SCRIPT), "--output", str(output)]
    MODULE.main()
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["schema"] == "g0-ssot-polarity-mechanical-characterization-v0"
    assert result["model_calls"] == result["human_verifiers"] == 0
    assert result["input_provenance"] == "INVESTIGATOR_AUTHORED_FICTIONAL_POLARITIES"
    assert result["gate_logic_changed"] is result["experimental_policy_changed"] is False
    assert result["product_code_changed"] is False
    assert result["Q1_tested"] is result["Q2_tested"] is result["G0_passed"] is False
    assert result["observations_are_not_independent_truth_labels"] is True
