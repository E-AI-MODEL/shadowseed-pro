"""No external calls, no product seed or Gate update."""
import hashlib
import json

import pytest

from research.scripts.pro_reinspection_queue import build_queue, main


def source():
    return {"cases": [{"case_id": "synthetic", "model_id": "test-model", "turns": [
        {"user_input": "Original question?", "host_answer": "Original answer.",
         "canonical_report": {"intake_diagnostics": {"item_lineage": [
             {"normalized_text": "Of spanning ook klok of sensor beïnvloedt, naast camera.",
              "outcome": "rejected", "reason": "not_atomic",
              "observation_id": "synthetic-1", "raw_candidate_index": 0},
             {"normalized_text": "Good note.", "outcome": "accepted",
              "seed_transition": "created"},
         ]}}},
        {"user_input": "Follow-up?", "host_answer": "Follow-up answer.",
         "canonical_report": {"intake_diagnostics": {"item_lineage": [
             {"normalized_text": "Of batterij en sensor een gemeenschappelijke oorzaak hebben, of niet.",
              "outcome": "rejected", "reason": "not_atomic",
              "observation_id": "synthetic-2", "raw_candidate_index": 0},
         ]}}},
    ]}]}


def test_original_context_and_identity_kept_without_seeds():
    x = build_queue(source())
    assert len(x["items"]) == 2
    first, second = x["items"]
    assert first["observation_id"] == "synthetic-1"
    assert first["seed_born"] is False
    assert first["unfilled_review"]["relation_structure"] is None
    assert len(first["original_context_through_this_turn"]) == 1
    assert len(second["original_context_through_this_turn"]) == 2
    assert x["no_seed_admission"] is True


def test_checksum_failure_does_not_create_file(tmp_path):
    src, output = tmp_path / "input.json", tmp_path / "owner.json"
    src.write_text(json.dumps(source()))
    with pytest.raises(SystemExit, match="checksum"):
        main(["--observed", str(src), "--source-sha256", "0" * 64,
              "--private-output", str(output)])
    assert not output.exists()


def test_valid_source_still_requires_private_output(tmp_path):
    src, output = tmp_path / "input.json", tmp_path / "owner.json"
    src.write_text(json.dumps(source()))
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    assert main(["--observed", str(src), "--source-sha256", digest,
                 "--private-output", str(output)]) == 0
    result = json.loads(output.read_text())
    assert len(result["items"]) == 2
    assert result["source_sha256"] == digest
    assert result["items"][0]["original_context_through_this_turn"][0]["host_answer"] == "Original answer."
