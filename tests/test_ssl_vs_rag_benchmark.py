"""Tests for the SSL-vs-RAG head-to-head harness (vision gap 3)."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from shadowseed.benchmark.ssl_vs_rag_benchmark import run_ssl_vs_rag_benchmark

_spec = importlib.util.spec_from_file_location("apw", "scripts/answer_pair_winrate.py")
apw = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(apw)

DATA = "src/shadowseed/data/ssl_vs_rag_benchmark.json"


def test_harness_produces_blind_pairs_and_key(tmp_path: Path):
    out = run_ssl_vs_rag_benchmark(DATA, str(tmp_path / "o.json"), top_k=2)
    d = json.loads(out.read_text(encoding="utf-8"))
    assert d["summary"]["item_count"] == 2
    assert len(d["blind_review_items"]) == 2
    assert len(d["blind_answer_key"]) == 2
    # arms are exactly rag(baseline) and ssl(probe), hidden behind A/B
    for k in d["blind_answer_key"]:
        assert {k["option_a_source"], k["option_b_source"]} == {"baseline", "ssl"}


def test_probe_reaches_gap_context_the_question_misses(tmp_path: Path):
    out = run_ssl_vs_rag_benchmark(DATA, str(tmp_path / "o.json"), top_k=2)
    d = json.loads(out.read_text(encoding="utf-8"))
    # for the IR item the colonial-capital seed should pull a chunk that the
    # question retrieval (about why the IR arose) need not surface
    ir = next(r for r in d["results"] if r["scenario_id"] == "SSLRAG_IR")
    assert ir["seed_only_chunk_ids"]  # the probe expanded beyond the question
    assert any("colonial" in c or "raw_materials" in c for c in ir["probe_chunk_ids"])


def test_scorer_runs_on_harness_output(tmp_path: Path):
    out = run_ssl_vs_rag_benchmark(DATA, str(tmp_path / "o.json"), top_k=2)
    d = json.loads(out.read_text(encoding="utf-8"))
    # leave better_answer unfilled -> scorer reports all pending, no crash
    report = apw.score(d)
    assert report["decided_pairs"] == 0
    assert report["pending"] == 2
