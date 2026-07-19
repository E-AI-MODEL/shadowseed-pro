"""Lock the rubric-sensitivity analysis behaviour (fragility bound)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("rs", "scripts/analyze_rubric_sensitivity.py")
assert _spec and _spec.loader
rs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rs)


def test_demote_flags_impact_and_generic_asks() -> None:
    assert rs.demote("De impact van de arrestatie op de algehele trend.")
    assert rs.demote("Specifieke functies van de nieuwe download service.")
    assert rs.demote("Details over hoe de methoden worden gekoppeld.")


def test_demote_flags_speculation() -> None:
    # the rule's docstring names speculation; the predicate must catch it
    assert rs.demote("De mogelijke fraudpreventiemaatregelen voor de recall-stemmen.")
    assert rs.demote("De verwachte effecten van de regeling.")


def test_demote_keeps_specific_named_gaps() -> None:
    assert not rs.demote("De prijs van de discount video-editing software bundle.")
    assert not rs.demote("De naam van de tweede private team.")


def test_strict_acceptance_never_exceeds_ai_on_every_batch() -> None:
    for _, d in rs.BATCHES:
        r = rs.analyze_batch(Path(d))
        assert r["strict_acceptance"] <= r["ai_acceptance"]


def test_headline_batch_is_the_most_fragile() -> None:
    # 006_b1 (the 0.50 "model lever" batch) swings the most under the strict rule.
    swings = {}
    for name, d in rs.BATCHES:
        r = rs.analyze_batch(Path(d))
        swings[name] = r["ai_acceptance"] - r["strict_acceptance"]
    assert swings["006_b1"] == max(swings.values())
    assert swings["006_b1"] > 0.1
