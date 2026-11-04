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


def test_original_48_turn_archive_can_be_read_without_raw_text_output():
    import json
    source = (Path(__file__).resolve().parents[1]
              / "research/datasets/2026-10-28-q1q2-48/original-author-kit/SOURCE/"
              / "original-observed_sha256_0a5094e3.json")
    result = module.screen(json.loads(source.read_text(encoding="utf-8")))
    assert result["source_observations"] == 94
    assert result["later_windows"] == 140
    assert result["matched_candidate_occurrences"] <= result["matched_windows"]
    assert result["matched_windows"] <= result["later_windows"]
