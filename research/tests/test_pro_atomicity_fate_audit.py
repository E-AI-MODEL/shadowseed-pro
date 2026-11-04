"""Offline Pro candidate-fate audit. No model calls, no seed creation or Gate updates."""
import hashlib
import json
from pathlib import Path

import pytest

from research.scripts.pro_atomicity_fate_audit import classify_lineage, main


def fake_source(rows):
    return {"cases": [{"case_id": "SYNTHETIC", "model_id": "synthetic-backend",
        "turns": [{"canonical_report": {"intake_diagnostics": {"item_lineage": rows}}}]}]}


def test_one_relation_rejected_on_form_not_lost_from_private_lineage():
    battery = "Of lage batterijspanning ook de bewegingssensor of de tijdregistratie kan beïnvloeden, naast de camera."
    other = "Whether the result depends on sensor calibration."
    report, rows = classify_lineage(fake_source([
        {"normalized_text": battery, "outcome": "rejected", "reason": "not_atomic",
         "observation_id": "fake:1", "seed_transition": None},
        {"normalized_text": other, "outcome": "accepted", "reason": None,
         "observation_id": "fake:2", "seed_transition": "created"},
    ]))
    assert report["candidate_occurrences"] == 2
    assert report["not_atomic_rejections"] == 1
    assert report["rejected_that_pass_question_punctuation_counterfactual"] == 1
    assert report["seed_transitions"] == {"created": 1}
    assert report["replay_disagreements"] == 0
    assert rows[0]["original_text"] == battery
    assert rows[0]["observation_id"] == "fake:1"
    assert rows[0]["seed_transition"] is None


def test_counterfactual_punctuation_never_declares_atomicity():
    text = "Oorzaken, gevolgen en perspectieven ontbreken."
    report, rows = classify_lineage(fake_source([
        {"normalized_text": text, "outcome": "rejected", "reason": "not_atomic"}
    ]))
    assert report["rejected_that_pass_question_punctuation_counterfactual"] == 1
    assert report["counterfactual_is_not_semantic_atomicity"] is True
    assert report["no_value_or_truth_judgment"] is True
    assert rows[0]["original_text"] == text


def test_source_checksum_required_before_writing(tmp_path):
    source, output = tmp_path / "source.json", tmp_path / "output.json"
    source.write_text(json.dumps(fake_source([])), encoding="utf-8")
    with pytest.raises(SystemExit, match="checksum"):
        main(["--observed", str(source), "--source-sha256", "0" * 64,
              "--output", str(output)])
    assert not output.exists()


def test_public_summary_does_not_include_original_text(tmp_path):
    source = tmp_path / "source.json"
    public = tmp_path / "summary.json"
    private = tmp_path / "owner-items.json"
    secret_example = "Zeldzame kandidaat A en B worden als relatie beschreven, nog zonder bewijs."
    source.write_text(json.dumps(fake_source([
        {"normalized_text": secret_example, "outcome": "rejected", "reason": "not_atomic"}
    ])), encoding="utf-8")
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    assert main(["--observed", str(source), "--source-sha256", checksum,
                 "--output", str(public), "--private-items", str(private)]) == 0
    assert secret_example not in public.read_text(encoding="utf-8")
    assert secret_example in private.read_text(encoding="utf-8")
