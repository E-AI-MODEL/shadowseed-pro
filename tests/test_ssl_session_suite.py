"""Tests for the SSL session suite (W9) — proves it drives the REAL pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from shadowseed.benchmark import ssl_session_suite as sess
from shadowseed.benchmark.ssl_session_suite import run_ssl_session
from shadowseed.surfacing import build_chat_prompt, select_cross_turn_seeds


def test_select_cross_turn_seeds_ranks_and_caps():
    # round 023 use-time discipline: rank by similarity desc, keep top_k
    cands = [(0.4, "a", "A"), (0.9, "b", "B"), (0.6, "c", "C")]
    assert [t for _s, _i, t in select_cross_turn_seeds(cands, 2)] == ["B", "C"]
    assert [t for _s, _i, t in select_cross_turn_seeds(cands, -1)] == ["B", "C", "A"]  # no cap
    assert select_cross_turn_seeds(cands, 0) == []  # nothing steers


def test_chat_prompt_is_potential_not_must():
    p = build_chat_prompt([("Q1", "A1")], "Q2", ["A carried perspective."])
    assert "A carried perspective." in p
    assert "only when they materially improve" in p
    assert "must never shift" in p and "Omit any perspective" in p
    assert "explain why a perspective was included or omitted" in p


def test_chat_prompt_compactness_applies_to_both_arms():
    # round 025: the rounded-off/compact instruction must be in BOTH arms so it
    # cannot bias the A/B comparison (round 024: 7/18 answers truncated mid-word).
    baseline = build_chat_prompt([("Q1", "A1")], "Q2", [])
    ssl = build_chat_prompt([("Q1", "A1")], "Q2", ["Perspective."])
    for p in (baseline, ssl):
        assert "compact" in p and "closing paragraph" in p
    assert "previously identified" not in baseline


def test_transfer_suite_runs_through_pipeline(tmp_path: Path):
    # W10: the doctrine-transfer dataset (new domains) must run through the same
    # pipeline. Fixture backend -> deterministic, no model/secret needed.
    out = tmp_path / "t.json"
    run_ssl_session(
        "src/shadowseed/data/ssl_session_transfer_suite.json", str(out), backend="fixture"
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["artifact"] == "ssl_session_suite"
    assert payload["summary"]["conversation_count"] == 3
    domains = {c["domain"] for c in payload["conversations"]}
    assert domains == {"onderwijs", "publieke gezondheid", "beleid"}


def test_surface_settings_recorded(tmp_path: Path):
    out = tmp_path / "s.json"
    run_ssl_session(
        "src/shadowseed/data/ssl_session_suite.json", str(out), backend="fixture", surface_top_k=1
    )
    appl = json.loads(out.read_text(encoding="utf-8"))["conversations"][0]["applied_thresholds"]
    assert appl["surface_top_k"] == 1
    assert "surface_threshold" in appl


def test_fixture_smoke_runs(tmp_path: Path):
    out = tmp_path / "s.json"
    run_ssl_session(
        "src/shadowseed/data/ssl_session_suite.json", str(out), backend="fixture"
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["artifact"] == "ssl_session_suite"
    assert payload["summary"]["conversation_count"] == 3


def test_per_topic_thresholds_override_run_level(tmp_path: Path):
    # one conversation carries its own thresholds; they must win over run-level
    conv = {
        "version": "t",
        "conversations": [
            {"id": "A", "domain": "d", "dedup_threshold": 0.55, "min_occurrences": 2,
             "turns": [{"question": "Q1?"}, {"question": "Q2?"}]},
            {"id": "B", "domain": "d", "turns": [{"question": "Q1?"}, {"question": "Q2?"}]},
        ],
    }
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")
    out = tmp_path / "s.json"
    run_ssl_session(str(inp), str(out), backend="fixture", dedup_threshold=0.8)
    payload = json.loads(out.read_text(encoding="utf-8"))
    by_id = {c["conversation_id"]: c for c in payload["conversations"]}
    # A overrides to 0.55 / min_occ 2; B inherits run-level 0.8 / default min_occ
    assert by_id["A"]["applied_thresholds"]["dedup_threshold"] == 0.55
    assert by_id["A"]["applied_thresholds"]["min_occurrences"] == 2
    assert by_id["B"]["applied_thresholds"]["dedup_threshold"] == 0.8
    assert by_id["B"]["applied_thresholds"]["min_occurrences"] == "default(3)"


def test_chat_prompt_includes_history_and_surfaced():
    p = build_chat_prompt([("Q1", "A1")], "Q2", ["A carried perspective."])
    assert "Q1" in p and "A1" in p and "Q2" in p
    assert "A carried perspective." in p


def test_recurring_seed_promotes_and_surfaces_cross_turn(tmp_path: Path, monkeypatch):
    # 6-turn conversation so a recurring seed can clear the Gate (weight>=0.5
    # needs ~3 validated passes) and then surface at a later turn.
    conv = {
        "version": "t",
        "conversations": [
            {"id": "C", "domain": "d", "turns": [{"question": f"Vraag {i}?"} for i in range(6)]}
        ],
    }
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")

    class _Model:
        name = "fake"

        def generate(self, prompt, scenario, mode, seeds):
            return ("SSL-antwoord met invalshoek." if mode == "ssl" else "Baseline-antwoord.")

    class _Detector:
        name = "fake-det"

        def detect_seeds(self, item, max_seeds=5):
            return ["Koloniaal kapitaal als verklarend kader."]  # same gap every turn -> recurs

    def _all_ones_embedder(backend, model_id=None, **kw):
        def embed(text: str) -> np.ndarray:
            v = np.ones(8)
            return v / np.linalg.norm(v)

        return embed, 8

    monkeypatch.setattr(sess, "make_backend", lambda **kw: _Model())
    monkeypatch.setattr(sess, "make_detector_backend", lambda *a, **kw: _Detector())
    monkeypatch.setattr(sess, "make_embedding_fn", _all_ones_embedder)

    out = tmp_path / "s.json"
    run_ssl_session(str(inp), str(out), backend="openai")
    payload = json.loads(out.read_text(encoding="utf-8"))

    # the recurring gap must have reached PROMOTED via the real Gate...
    turns = payload["conversations"][0]["turns"]
    assert any(tr["promoted_total"] for tr in turns), "recurring seed should promote via the Gate"
    # ...and then surfaced as a CROSS-TURN seed (born earlier) shaping a later answer
    assert payload["summary"]["cross_turn_payoff_events"] >= 1
    assert any(tr["is_cross_turn_payoff"] for tr in turns)
    assert payload["blind_review_items"], "a blind pair should exist for the cross-turn turn"
    # and on that turn the SSL answer differs from baseline (the seed was used)
    ct = next(tr for tr in turns if tr["is_cross_turn_payoff"])
    assert ct["ssl_answer"] != ct["baseline_answer"]


def test_early_turn_margin_raises_bar_on_early_turns(tmp_path: Path, monkeypatch):
    # Vroege-beurt-discipline (round 029): een matig-passende promoted seed
    # (sim ~0.35) haalt de verhoogde lat (0.30 + 0.10) niet zolang een beurt
    # als "vroeg" telt, en surfacet wel zodra de marge vervalt. Fit-selectie,
    # geen beurt-blok: de basisdrempel blijft 0.30.
    conv = {
        "version": "t",
        "conversations": [
            {"id": "A", "domain": "d", "min_occurrences": 2,
             "turns": [{"question": f"Vraag {i}?"} for i in range(8)]},
        ],
    }
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")

    class _Model:
        name = "fake"

        def generate(self, prompt, scenario, mode, seeds):
            return "SSL-antwoord." if mode == "ssl" else "Baseline-antwoord."

    class _Detector:
        name = "fake-det"

        def detect_seeds(self, item, max_seeds=5):
            return ["SEEDGAP terugkerend ontbrekend punt."]

    v_seed = np.zeros(8)
    v_seed[0] = 1.0
    v_q = np.zeros(8)
    v_q[0] = 0.35
    v_q[1] = float(np.sqrt(1 - 0.35**2))

    def _embedder(backend, model_id=None, **kw):
        def embed(text: str) -> np.ndarray:
            return v_seed.copy() if "SEEDGAP" in text else v_q.copy()

        return embed, 8

    monkeypatch.setattr(sess, "make_backend", lambda **kw: _Model())
    monkeypatch.setattr(sess, "make_detector_backend", lambda *a, **kw: _Detector())
    monkeypatch.setattr(sess, "make_embedding_fn", _embedder)

    def _payoff_turns(margin, history):
        out = tmp_path / f"s{margin}-{history}.json"
        run_ssl_session(
            str(inp), str(out), backend="openai",
            early_turn_margin=margin, early_turn_history=history,
        )
        payload = json.loads(out.read_text(encoding="utf-8"))
        turns = payload["conversations"][0]["turns"]
        appl = payload["conversations"][0]["applied_thresholds"]
        return [tr["turn"] for tr in turns if tr["is_cross_turn_payoff"]], appl

    # zonder marge surfacet de sim-0.35-seed zodra hij promoted is
    base_turns, _ = _payoff_turns(0.0, 3)
    assert base_turns, "zonder marge moet de seed surfacen (sim 0.35 >= 0.30)"

    # met marge en alle beurten "vroeg": de lat wordt 0.40 en niets surfacet
    blocked, appl = _payoff_turns(0.10, 100)
    assert blocked == []
    assert appl["early_turn_margin"] == 0.10 and appl["early_turn_history"] == 100

    # met marge maar een korte vroege zone die vóór de promotie eindigt,
    # gedraagt de run zich als zonder marge (fit-selectie, geen beurt-blok)
    late_ok, _ = _payoff_turns(0.10, 3)
    assert late_ok == base_turns

    # defaults (codex round-031): de round-029-ruis zat op beurtindex 4, dus
    # de default-zone moet t=4 dekken — geen payoff vóór index 5
    def _payoff_defaults():
        out = tmp_path / "sdef.json"
        run_ssl_session(str(inp), str(out), backend="openai")
        payload = json.loads(out.read_text(encoding="utf-8"))
        turns = payload["conversations"][0]["turns"]
        appl = payload["conversations"][0]["applied_thresholds"]
        return [tr["turn"] for tr in turns if tr["is_cross_turn_payoff"]], appl

    def_turns, def_appl = _payoff_defaults()
    assert def_appl["early_turn_history"] == 5
    assert def_turns and min(def_turns) >= 5


def test_resurface_margin_damps_consecutive_steering(tmp_path: Path, monkeypatch):
    # Gebruiksdemping (round 031-les, TrTL op use-time): een seed die net een
    # antwoord stuurde krijgt de dírect volgende beurt een hogere lat
    # (halverend per beurt) en moet zich via verse fit opnieuw bewijzen.
    # Round 031 mat precies dit falen: dezelfde matig-passende seed kleurde
    # t05 én t06 (8/14 hinder). Geen beurt-blok, weight onaangeroerd.
    conv = {
        "version": "t",
        "conversations": [
            {"id": "A", "domain": "d", "min_occurrences": 2,
             "turns": [{"question": f"Vraag {i}?"} for i in range(10)]},
        ],
    }
    inp = tmp_path / "in.json"
    inp.write_text(json.dumps(conv), encoding="utf-8")

    class _Model:
        name = "fake"

        def generate(self, prompt, scenario, mode, seeds):
            return "SSL-antwoord." if mode == "ssl" else "Baseline-antwoord."

    class _Detector:
        name = "fake-det"

        def detect_seeds(self, item, max_seeds=5):
            return ["SEEDGAP terugkerend ontbrekend punt."]

    v_seed = np.zeros(8)
    v_seed[0] = 1.0
    v_q = np.zeros(8)
    v_q[0] = 0.35
    v_q[1] = float(np.sqrt(1 - 0.35**2))

    def _embedder(backend, model_id=None, **kw):
        def embed(text: str) -> np.ndarray:
            return v_seed.copy() if "SEEDGAP" in text else v_q.copy()

        return embed, 8

    monkeypatch.setattr(sess, "make_backend", lambda **kw: _Model())
    monkeypatch.setattr(sess, "make_detector_backend", lambda *a, **kw: _Detector())
    monkeypatch.setattr(sess, "make_embedding_fn", _embedder)

    def _payoff_turns(resurface):
        out = tmp_path / f"r{resurface}.json"
        run_ssl_session(
            str(inp), str(out), backend="openai",
            early_turn_margin=0.0, early_turn_history=0,
            resurface_margin=resurface,
        )
        payload = json.loads(out.read_text(encoding="utf-8"))
        turns = [
            tr["turn"]
            for tr in payload["conversations"][0]["turns"]
            if tr["is_cross_turn_payoff"]
        ]
        return turns, payload["conversations"][0]["applied_thresholds"]

    # zonder demping stuurt de sim-0.35-seed élke beurt na promotie
    free, appl0 = _payoff_turns(0.0)
    assert len(free) >= 3
    assert appl0["resurface_margin"] == 0.0
    assert any(b - a == 1 for a, b in zip(free, free[1:])), (
        "zonder demping horen opeenvolgende stuur-beurten voor te komen"
    )

    # met demping (0.08: +0.08 direct erna, +0.04 een beurt later) kan
    # dezelfde seed nooit twee beurten op rij sturen — maar komt hij wél
    # terug zodra de extra lat onder sim - drempel (0.05) zakt
    damped, appl = _payoff_turns(0.08)
    assert appl["resurface_margin"] == 0.08
    assert damped, "demping mag surfacing niet permanent uitzetten"
    assert damped[0] == free[0], "de eerste surfacing blijft ongemoeid"
    assert all(b - a >= 2 for a, b in zip(damped, damped[1:])), (
        "direct opeenvolgend hersturen moet gedempt zijn"
    )

    # default staat aan en wordt vastgelegd in het artifact
    out = tmp_path / "rdef.json"
    run_ssl_session(str(inp), str(out), backend="openai")
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["conversations"][0]["applied_thresholds"]["resurface_margin"] == 0.15


def test_chat_prompt_keeps_question_leading():
    # Round 029: de gestelde vraag blijft leidend — de weave-instructie verbiedt
    # onderwerp-/focusverschuiving expliciet (alleen in de SSL-arm aanwezig).
    ssl = build_chat_prompt([("Q1", "A1")], "Q2", ["Perspective."])
    assert "question remains leading" in ssl and "never shift" in ssl
    assert "question remains leading" not in build_chat_prompt([("Q1", "A1")], "Q2", [])
