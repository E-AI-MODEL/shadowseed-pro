"""Tests for the round-008 payoff win-rate scorer."""
from __future__ import annotations

import importlib.util

_spec = importlib.util.spec_from_file_location("apw", "scripts/answer_pair_winrate.py")
assert _spec and _spec.loader
apw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(apw)


def _payload(items, keys, results):
    return {"blind_review_items": items, "blind_answer_key": keys, "results": results}


def test_unblinds_and_counts_ssl_win():
    # A=ssl chosen -> ssl win; SSL not longer -> counts length-neutral
    p = _payload(
        items=[{"review_id": "r1", "scenario_id": "s1",
                "scores_to_fill": {"better_answer": "A"}}],
        keys=[{"review_id": "r1", "option_a_source": "ssl", "option_b_source": "baseline"}],
        results=[{"scenario_id": "s1", "answer_length_delta_words": -3}],
    )
    r = apw.score(p)
    assert r["ssl_wins"] == 1 and r["baseline_wins"] == 0
    assert r["ssl_win_rate"] == 1.0
    assert r["ssl_win_rate_length_neutral"] == 1.0


def test_length_control_excludes_longer_ssl_wins():
    # ssl wins but SSL was longer -> excluded from length-neutral denominator
    p = _payload(
        items=[{"review_id": "r1", "scenario_id": "s1",
                "scores_to_fill": {"better_answer": "B"}}],
        keys=[{"review_id": "r1", "option_a_source": "baseline", "option_b_source": "ssl"}],
        results=[{"scenario_id": "s1", "answer_length_delta_words": 25}],
    )
    r = apw.score(p)
    assert r["ssl_wins"] == 1
    assert r["length_neutral_decided_pairs"] == 0
    assert r["ssl_win_rate_length_neutral"] is None


def test_ties_and_pending_are_separated():
    p = _payload(
        items=[
            {"review_id": "r1", "scenario_id": "s1", "scores_to_fill": {"better_answer": "tie"}},
            {"review_id": "r2", "scenario_id": "s2", "scores_to_fill": {"better_answer": "A/B/tie"}},
        ],
        keys=[
            {"review_id": "r1", "option_a_source": "ssl", "option_b_source": "baseline"},
            {"review_id": "r2", "option_a_source": "ssl", "option_b_source": "baseline"},
        ],
        results=[{"scenario_id": "s1", "answer_length_delta_words": 0},
                 {"scenario_id": "s2", "answer_length_delta_words": 0}],
    )
    r = apw.score(p)
    assert r["ties"] == 1 and r["pending"] == 1 and r["decided_pairs"] == 0
    assert r["ssl_win_rate"] is None


def test_mixed_winrate_half():
    p = _payload(
        items=[
            {"review_id": "r1", "scenario_id": "s1", "scores_to_fill": {"better_answer": "A"}},
            {"review_id": "r2", "scenario_id": "s2", "scores_to_fill": {"better_answer": "A"}},
        ],
        keys=[
            {"review_id": "r1", "option_a_source": "ssl", "option_b_source": "baseline"},
            {"review_id": "r2", "option_a_source": "baseline", "option_b_source": "ssl"},
        ],
        results=[{"scenario_id": "s1", "answer_length_delta_words": 0},
                 {"scenario_id": "s2", "answer_length_delta_words": 0}],
    )
    r = apw.score(p)
    assert r["ssl_wins"] == 1 and r["baseline_wins"] == 1
    assert r["ssl_win_rate"] == 0.5


def test_ssl_append_answer_is_no_harm():
    import importlib.util
    spec = importlib.util.spec_from_file_location("mb", "src/shadowseed/benchmark/ssl45_model_benefit_suite.py")
    mb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mb)
    base = "Het basisantwoord blijft staan."
    out = mb.ssl_append_answer(base, ["Seed een.", "Seed twee."])
    # baseline preserved verbatim (no-harm), seeds appended as a bounded block
    assert out.startswith(base)
    assert "Additional relevant points" in out
    assert "Seed een." in out and "Seed twee." in out
    # empty seeds -> baseline unchanged
    assert mb.ssl_append_answer(base, []) == base
