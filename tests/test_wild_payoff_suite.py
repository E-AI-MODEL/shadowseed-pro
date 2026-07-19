"""Tests for the wild-payoff suite (P0/W1), fixture backend + injected model."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from shadowseed.benchmark.wild_payoff_suite import (
    build_wild_ssl_prompt,
    run_wild_payoff_suite,
)


def test_ssl_prompt_includes_text_and_seeds():
    p = build_wild_ssl_prompt("Een kort bericht.", ["Ontbrekend punt A.", "Ontbrekend punt B."])
    assert "Een kort bericht." in p
    assert "Ontbrekend punt A." in p and "Ontbrekend punt B." in p
    instruction = p.lower().split("report:")[0]
    assert "do not refer to seeds" in instruction  # seed jargon is explicitly prohibited
    assert "missing points to cover" in p.lower()


def test_wild_suite_runs_on_real_dataset_fixture(tmp_path: Path):
    out = tmp_path / "wild.json"
    run_wild_payoff_suite(
        "src/shadowseed/data/wild_payoff_suite.json",
        str(out),
        backend="fixture",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["summary"]["artifact"] == "wild_payoff_suite"
    assert payload["summary"]["item_count"] == len(payload["results"]) == 12
    assert len(payload["blind_review_items"]) == 12
    # every item carries real detected seeds (not author-designed)
    assert all(r["detected_seeds"] for r in payload["results"])


def test_wild_suite_semantic_added_value_with_injected_model(tmp_path: Path, monkeypatch):
    # Fake model: baseline ignores the gaps; ssl echoes them. Fake embedder makes
    # a gap "covered" only if its first word appears in the answer.
    class _Model:
        name = "fake"

        def generate(self, prompt, item, mode, seeds):
            if mode == "baseline":
                return "Algemene analyse zonder de specifieke ontbrekende punten."
            return "Analyse. " + " ".join(seeds)

    import numpy as np

    def fake_make_embedding_fn(backend, model_id=None, **kw):
        vocab: dict[str, int] = {}

        def embed(text: str):
            v = np.zeros(64)
            for w in text.lower().split():
                v[hash(w) % 64] += 1.0
            n = np.linalg.norm(v)
            return v / n if n else v

        return embed, 64

    monkeypatch.setattr(
        "shadowseed.benchmark.wild_payoff_suite.make_backend", lambda **kw: _Model()
    )
    monkeypatch.setattr(
        "shadowseed.adapters.embedding.make_embedding_fn", fake_make_embedding_fn
    )

    out = tmp_path / "wild.json"
    run_wild_payoff_suite(
        "src/shadowseed/data/wild_payoff_suite.json",
        str(out),
        backend="openai",
        semantic_embedding_backend="lexical",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    # baseline ignored the gaps -> low baseline coverage -> detector adds value
    assert payload["summary"]["mean_baseline_gap_coverage"] is not None
    assert payload["summary"]["mean_baseline_gap_coverage"] < 0.5
    assert all(r["baseline_gap_coverage"] is not None for r in payload["results"])
