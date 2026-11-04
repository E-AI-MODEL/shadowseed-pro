"""Tests voor een zelfstandige, niet-bevestigende historische woordoverlap-screening."""
import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "research/atlas/scripts/inspect_lexical_windows.py"
spec = importlib.util.spec_from_file_location("inspect_lexical_windows", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def turn(index, prompt, answer, candidate=None):
    observation = [] if candidate is None else [{"observation_id": "o1", "raw_text": candidate}]
    lineage = [] if candidate is None else [{"observation_id": "o1", "outcome": "accepted"}]
    return {"turn": index, "user_input": prompt, "host_answer": answer,
            "canonical_report": {"candidate_observations": observation,
                                 "intake_diagnostics": {"item_lineage": lineage}}}


def test_filter_keeps_word_adjacency_after_stopwords():
    assert "meetaa/sensoo" in module.pairs("Een meetaa en sensoo zijn opnieuw bekeken")


def test_later_question_with_same_pair_is_excluded():
    source = {"cases": [{"case_id": "C1", "turns": [
        turn(0, "Andere oorzaak?", "Nog geen resultaten", "Kalibratie sensorfunctie uitgebleven"),
        turn(1, "Wat daarna?", "Kalibratie sensorfunctie verandert mogelijk")]}]}
    output = module.screen(source)
    assert (output["source_observations"], output["later_windows"], output["matched_windows"]) == (1, 1, 1)
    source["cases"][0]["turns"][1]["user_input"] = "Kalibratie sensorfunctie komt hier terug"
    assert module.screen(source)["matched_windows"] == 0


def test_last_turn_candidate_is_not_scored_as_missed():
    last = turn(3, "Laatste vraag", "Antwoord", "sensor kalibratie")
    last["canonical_report"]["intake_diagnostics"]["item_lineage"][0]["outcome"] = "rejected"
    output = module.screen({"cases": [{"case_id": "C2", "turns": [last]}]})
    assert output["source_observations"] == 1
    assert output["later_windows"] == 0
    assert output["matched_windows"] == 0


def test_original_archive_gives_frozen_matched_window_identities():
    import hashlib
    import json

    source = (Path(__file__).resolve().parents[1]
              / "research/datasets/2026-10-28-q1q2-48/original-author-kit/SOURCE/"
              / "original-observed_sha256_0a5094e3.json")
    raw = source.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == module.EXPECTED_SOURCE_SHA256
    result = module.screen(json.loads(raw.decode("utf-8")))

    assert result["source_observations"] == 94
    assert result["later_windows"] == 140
    assert result["matched_windows"] == 10
    assert result["matched_candidate_occurrences"] == 8
    assert result["accepted_matches"] == 7
    assert result["rejected_matches"] == 3
    observed = {(v["observation_id"], v["later_turn"]) for v in result["matches"]}
    assert observed == {
        ("obs_43487e11e602d3976fcc141a", 3),
        ("obs_14c6ab2837a3573ad9581b79", 3),
        ("obs_46e290bca95aa3bf0438eff2", 2),
        ("obs_46e290bca95aa3bf0438eff2", 3),
        ("obs_6475cc01142a1e43077263a3", 3),
        ("obs_2f6b382c6734b93c84f0ccba", 2),
        ("obs_325a022862288fd97988afee", 3),
        ("obs_97e6a57f67aed41df6b50dad", 2),
        ("obs_d099710502a6149d666c400b", 2),
        ("obs_d099710502a6149d666c400b", 3),
    }
    assert all("matched_stem_pairs" not in v for v in result["matches"])
    assert all("raw_text" not in v and "host_answer" not in v for v in result["matches"])


def test_cli_rejects_an_unpinned_source_and_shows_no_original_text(tmp_path):
    import subprocess
    import sys

    source = tmp_path / "changed.json"
    source.write_text('{"cases": [], "private_value": "DO_NOT_ECHO"}', encoding="utf-8")
    process = subprocess.run(
        [sys.executable, str(SCRIPT), str(source)],
        capture_output=True, text=True, check=False,
    )
    assert process.returncode != 0
    assert "SHA-256 wijkt af" in process.stderr
    assert "DO_NOT_ECHO" not in process.stderr + process.stdout
