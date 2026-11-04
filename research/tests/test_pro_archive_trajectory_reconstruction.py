"""Tests use synthetic local records; no provider calls or private archive content."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from research.scripts.pro_archive_trajectory_reconstruction import (
    CANDIDATES, FULL_STAGE, STAGE_INDEX, load_register, write_owner_only,
)


def _csv(data):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=list(data[0]))
    writer.writeheader()
    writer.writerows(data)
    return buf.getvalue()


def make_zip(path: Path, *, bad_turn=False, change_index=False) -> Path:
    full = []
    for turn in range(2):
        original = {"turn": turn, "question": "synthetic private question", "answer": "synthetic private answer"}
        full.append({
            "dataset": "example", "artifact_id": "a-1", "model": "model-a",
            "case_id": "case", "turn": str(turn if not bad_turn else 1),
            "vraag": "synthetic private question", "antwoord": "synthetic private answer",
            "originele_complete_beurt_json": json.dumps(original),
        })
    stage = [{k: row[k] for k in ("dataset", "artifact_id", "model", "case_id", "turn")} for row in full]
    if change_index:
        stage[-1]["turn"] = "2"
    candidates = [
        {"dataset": "example", "artid": "a-1", "model": "model-a", "case_id": "case", "turn": "0", "candidate_text": "SENSITIVE_EXACT", "candidate_ord": "0"},
        {"dataset": "example", "artid": "a-1", "model": "different-model-label", "case_id": "case", "turn": "1", "candidate_text": "SENSITIVE_LABEL", "candidate_ord": "0"},
        {"dataset": "outside", "artid": "b-1", "model": "model-b", "case_id": "other", "turn": "0", "candidate_text": "SENSITIVE_UNMATCHED", "candidate_ord": "0"},
    ]
    with ZipFile(path, "w") as z:
        z.writestr(FULL_STAGE, _csv(full))
        z.writestr(STAGE_INDEX, _csv(stage))
        z.writestr(CANDIDATES, _csv(candidates))
    return path


def test_preserve_all_candidates_but_only_literal_trajectory_joins(tmp_path):
    manifest, private = load_register(make_zip(tmp_path / "synthetic.zip"))
    assert manifest["stage_turn_records"] == 2
    assert manifest["stage_trajectories"] == 1
    assert manifest["candidate_occurrences_preserved"] == 3
    assert manifest["candidate_to_stage_literal_join"] == {
        "literal_source_key_match": 1,
        "model_label_differs_not_joined": 1,
        "no_literal_stage_match": 1,
    }
    assert len(private["trajectories"][0]["turns"]) == 2
    assert all(x["stage_trajectory_id_only_if_exact"] is None for x in private["candidate_occurrences"][1:])
    assert "SENSITIVE" not in json.dumps(manifest)
    assert manifest["original_action_artifacts_individually_reverified"] is False


def test_original_full_turn_object_is_preserved_and_never_printed(tmp_path, capsys):
    manifest, private = load_register(make_zip(tmp_path / "synthetic.zip"))
    assert "synthetic private question" in private["trajectories"][0]["turns"][0]["row"]["originele_complete_beurt_json"]
    assert "synthetic private question" not in json.dumps(manifest)
    assert capsys.readouterr().out == ""


def test_output_requires_explicit_private_directory_and_refuses_overwrite(tmp_path):
    public, private = load_register(make_zip(tmp_path / "synthetic.zip"))
    output = tmp_path / "owner"
    write_owner_only(output, private, public)
    assert len(list((output / "trajectories").glob("*.json"))) == 1
    assert "SENSITIVE_EXACT" in (output / "all_candidate_occurrences.jsonl").read_text()
    with pytest.raises(FileExistsError):
        write_owner_only(output, private, public)


def test_duplicate_trajectory_turn_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="duplicate full stage turn"):
        load_register(make_zip(tmp_path / "bad.zip", bad_turn=True))


def test_stage_index_and_full_turn_must_agree(tmp_path):
    with pytest.raises(ValueError, match="stage-index turn keys diverge"):
        load_register(make_zip(tmp_path / "bad.zip", change_index=True))


def test_input_zip_requires_all_three_source_tables(tmp_path):
    with ZipFile(tmp_path / "bad.zip", "w") as z:
        z.writestr(FULL_STAGE, "a\n1\n")
    with pytest.raises(ValueError, match="missing required"):
        load_register(tmp_path / "bad.zip")
