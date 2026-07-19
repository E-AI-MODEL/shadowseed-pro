"""Tests for the mechanical open-set prescreen triage aid.

The prescreen is a deterministic triage helper, not Layer C evidence. These
tests lock the deterministic failure-code behavior so the v0.3e run can be
compared against the round 004 baseline on stable ground.
"""

import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path("src").resolve()))

_SCRIPT = Path("scripts/prescreen_open_set_output.py").resolve()
_spec = importlib.util.spec_from_file_location("prescreen_open_set_output", _SCRIPT)
assert _spec and _spec.loader
prescreen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(prescreen)


def test_claim_is_flagged_as_claim_vs_gap() -> None:
    codes = prescreen.prescreen_seed(
        "De toezichthouder heeft geen onderzoek gedaan naar de zaak."
    )
    assert "claim_vs_gap" in codes


def test_absence_form_is_not_flagged_as_claim_vs_gap() -> None:
    codes = prescreen.prescreen_seed(
        "Of de toezichthouder onderzoek heeft gedaan, wordt niet vermeld."
    )
    assert "claim_vs_gap" not in codes


def test_gap_label_noun_phrase_is_not_a_claim() -> None:
    # v0.3g: the canonical candidate form is the gap-label noun phrase —
    # it has no main-clause verb and can assert nothing.
    for seed in (
        "De prijs van de discount video-editing software bundle.",
        "Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.",
        "Ontbreken van de reactie van Apple op de nieuwe service.",
    ):
        assert "claim_vs_gap" not in prescreen.prescreen_seed(seed), seed


def test_relative_clause_verb_is_not_a_claim() -> None:
    # Finite verbs inside relative/subordinate clauses do not assert facts.
    for seed in (
        "Specifieke fase-ruimte waarin de berekening het meest betrouwbaar is.",
        "Specifieke diphoton paarverdelingen die zijn voorspeld voor LHC.",
        "Details over hoe de basis ramp en shock methoden worden gekoppeld.",
    ):
        assert "claim_vs_gap" not in prescreen.prescreen_seed(seed), seed


def test_main_clause_assertion_is_a_claim() -> None:
    # A finite verb in the main clause without an absence marker asserts a
    # fact — the failure mode the code exists for (round 004 signature).
    for seed in (
        "De toezichthouder heeft geen onderzoek gedaan naar de zaak.",
        "De Prediction Unit weet niet precies waar branden zich bevinden.",
    ):
        assert "claim_vs_gap" in prescreen.prescreen_seed(seed), seed


def test_round_006_batches_are_claim_free_under_v03g_contract() -> None:
    # Evidence anchor: under the v0.3g form contract both Phi batches carry
    # zero assertions; the only remaining mechanical flags are the manager
    # gate's not_atomic (b1: 2, b2: 12) plus b2's truncations/near-dup.
    for batch in ("batch1", "batch2"):
        seed_output = json.loads(
            Path(
                f"benchmarks/open_review/rounds/round_006/{batch}/open_set_seed_output.json"
            ).read_text(encoding="utf-8")
        )
        report = prescreen.prescreen_output(seed_output, round_label=batch)
        assert report["failure_code_counts"]["claim_vs_gap"] == 0, batch


def test_unfinished_subordinate_clause_is_truncated_not_claim() -> None:
    # An "Of ..." clause that never reaches its absence scaffold was cut off
    # by the decoding budget — a truncation artifact, not a claim-form
    # regression of the prompt.
    codes = prescreen.prescreen_seed(
        "Of Google een beperking heeft opgelegd aan het aantal aandelen dat."
    )
    assert "truncated" in codes
    assert "claim_vs_gap" not in codes


def test_function_word_tail_is_truncated_even_with_marker() -> None:
    codes = prescreen.prescreen_seed("De reden wordt niet vermeld in de.")
    assert "truncated" in codes
    assert "claim_vs_gap" not in codes


def test_complete_claim_is_not_truncated() -> None:
    # A complete assertion without an opener stays claim_vs_gap.
    codes = prescreen.prescreen_seed(
        "De toezichthouder heeft geen onderzoek gedaan naar de zaak."
    )
    assert "claim_vs_gap" in codes
    assert "truncated" not in codes


def test_complete_absence_form_is_not_truncated() -> None:
    codes = prescreen.prescreen_seed(
        "Of de toezichthouder onderzoek heeft gedaan, wordt niet vermeld."
    )
    assert "truncated" not in codes
    assert "claim_vs_gap" not in codes


def test_subordinate_clause_verb_ending_is_not_truncated() -> None:
    # Dutch subordinate clauses end in a verb; that is not truncation.
    # (Round 006 false positive: "... waar de wildfires voorspeld worden.")
    codes = prescreen.prescreen_seed(
        "Specifieke geografische locaties waar de wildfires voorspeld worden."
    )
    assert "truncated" not in codes


def test_dangling_auxiliary_after_marker_is_truncated() -> None:
    # A marker-bearing candidate cut off at a conjunction+auxiliary is still
    # a truncation (Codex review on #120).
    codes = prescreen.prescreen_seed("De reden wordt niet vermeld en zal.")
    assert "truncated" in codes


def test_bare_modal_subordinate_ending_is_not_truncated() -> None:
    # "... wat ze mogen." is a complete subordinate clause; a bare modal tail
    # without a dangling conjunction/determiner before it is not truncation.
    codes = prescreen.prescreen_seed(
        "Wat de werknemers volgens de cao mogen, wordt niet vermeld."
    )
    assert "truncated" not in codes


def test_round_005_offset12_truncations_are_not_claim_vs_gap() -> None:
    # Evidence anchor: the nine missing-marker candidates in the reviewed
    # offset-12 batch are unfinished clauses (human-rejected as not_testable),
    # not prompt claim-form regressions. v0.3e removed claim_vs_gap entirely.
    seed_output = json.loads(
        Path(
            "benchmarks/open_review/rounds/round_005/reviewed_offset12/"
            "open_set_seed_output.json"
        ).read_text(encoding="utf-8")
    )
    report = prescreen.prescreen_output(seed_output, round_label="round_005")
    counts = report["failure_code_counts"]
    assert counts["claim_vs_gap"] == 0
    assert counts["truncated"] == 9


def test_embedded_numbering_is_a_parse_leak() -> None:
    codes = prescreen.prescreen_seed(
        "De prijs wordt niet genoemd. 1. De leverancier wordt niet vermeld."
    )
    assert "parse_leak" in codes


def test_html_entity_is_entity_bleed() -> None:
    codes = prescreen.prescreen_seed("De besparing van #36;5 wordt niet genoemd.")
    assert "entity_bleed" in codes


def test_dutch_homographs_do_not_trigger_language_leak() -> None:
    # Every v0.3e gap starts with "Of ..." and often contains "in"/"is";
    # these Dutch words must not be counted as an English echo.
    codes = prescreen.prescreen_seed(
        "Of de Prediction Unit een bepaalde periode in dienst is, wordt niet vermeld."
    )
    assert "language_leak" not in codes


def test_real_english_echo_is_language_leak() -> None:
    codes = prescreen.prescreen_seed("Apple Launches Graphics Software with the new bundle.")
    assert "language_leak" in codes


def test_round_004_baseline_is_dominated_by_claim_vs_gap() -> None:
    seed_output = json.loads(
        Path("benchmarks/open_review/rounds/round_004/open_set_seed_output.json").read_text(
            encoding="utf-8"
        )
    )
    report = prescreen.prescreen_output(seed_output, round_label="round_004")
    assert report["seed_count"] > 0
    assert report["flagged_count"] > 0
    counts = report["failure_code_counts"]
    # claim_vs_gap was the headline failure mode of the v0.3d round 004 run.
    assert counts["claim_vs_gap"] == max(counts.values())


def test_report_carries_non_evidence_disclaimer() -> None:
    report = prescreen.prescreen_output({"summary": {}, "results": []})
    assert "NOT human review" in report["disclaimer"]
    assert report["artifact"] == "mechanical_prescreen"


def test_near_duplicate_flags_reworded_same_gap() -> None:
    # Same gap, only the scaffold verb changes -> the later one is redundant.
    item = {
        "item_id": "a",
        "normalized_candidates": [
            "Of Charles Schwab een competitor heeft, wordt niet vermeld.",
            "Of Charles Schwab wordt beschreven als een competitor, wordt niet genoemd.",
        ],
    }
    report = prescreen.prescreen_output({"summary": {}, "results": [item]})
    codes = [v["codes"] for v in report["verdicts"]]
    assert "near_duplicate" not in codes[0]  # first occurrence kept clean
    assert "near_duplicate" in codes[1]
    assert report["near_duplicate_rate"] == 0.5


def test_distinct_related_gaps_are_not_near_duplicates() -> None:
    # Distinct-but-related gaps are Constellation material (4.5 §9.1), not noise.
    item = {
        "item_id": "a",
        "normalized_candidates": [
            "Of de financieringsbron van de fabrieken wordt niet vermeld.",
            "Of de arbeidsomstandigheden in de fabrieken worden niet beschreven.",
            "Of de milieugevolgen van de productie worden niet genoemd.",
        ],
    }
    report = prescreen.prescreen_output({"summary": {}, "results": [item]})
    assert all("near_duplicate" not in v["codes"] for v in report["verdicts"])


def test_yield_counts_empty_items() -> None:
    seed_output = {
        "summary": {},
        "results": [
            {"item_id": "a", "normalized_candidates": ["De prijs wordt niet genoemd."]},
            {"item_id": "b", "normalized_candidates": []},
            {"item_id": "c", "raw_candidates": []},
        ],
    }
    report = prescreen.prescreen_output(seed_output)
    y = report["yield"]
    assert y["item_count"] == 3
    assert y["items_empty"] == 2
    assert y["items_with_candidates"] == 1
