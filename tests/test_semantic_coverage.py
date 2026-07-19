"""Tests for the semantic gap-coverage metric (no network).

A fake embedder maps text to vectors by keyword so cosine similarity is
controllable: an answer that addresses a gap in different words still scores as
covered, which is the whole point — the lexical coverage() would score it 0.
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from shadowseed.benchmark.semantic_coverage import _cosine, semantic_coverage
from shadowseed.benchmark.ssl45_model_benefit_suite import run_ssl45_model_benefit_suite


def _embedder(table, default=(0.0, 0.0, 1.0)):
    def embed(text: str) -> np.ndarray:
        low = text.lower()
        for kw, vec in table.items():
            if kw in low:
                return np.asarray(vec, dtype=float)
        return np.asarray(default, dtype=float)

    return embed


def test_cosine_basics():
    assert _cosine(np.array([1.0, 0.0]), np.array([1.0, 0.0])) == pytest.approx(1.0)
    assert _cosine(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == pytest.approx(0.0)
    assert _cosine(np.array([0.0, 0.0]), np.array([1.0, 0.0])) == 0.0


def test_empty_expected_is_full_coverage():
    frac, covered, per = semantic_coverage("iets", [], _embedder({}))
    assert frac == 1.0 and covered == [] and per == []


def test_semantic_credits_paraphrase_not_just_verbatim():
    # gap and the addressing sentence share NO surface tokens but the same vector
    table = {
        "encryptie": [1.0, 0.0, 0.0],
        "versleuteld": [1.0, 0.0, 0.0],  # paraphrase -> same direction
        "navigatie": [0.0, 1.0, 0.0],
    }
    answer = "De data wordt versleuteld opgeslagen. De navigatie is intuitief."
    frac, covered, per = semantic_coverage(
        answer, ["Encryptie van medische data."], _embedder(table), threshold=0.9
    )
    assert frac == 1.0
    assert per[0]["max_sim"] == pytest.approx(1.0)


def test_semantic_misses_unaddressed_gap():
    table = {"navigatie": [0.0, 1.0, 0.0], "ratelimiet": [1.0, 0.0, 0.0]}
    answer = "De navigatie is intuitief en overzichtelijk."
    frac, covered, per = semantic_coverage(
        answer, ["Ratelimiet op de API."], _embedder(table), threshold=0.5
    )
    assert frac == 0.0
    assert covered == []
    assert per[0]["covered"] is False


def test_suite_with_lexical_semantic_metric_runs(tmp_path):
    out = tmp_path / "mb.json"
    run_ssl45_model_benefit_suite(
        "src/shadowseed/data/ssl45_model_benefit_suite.json",
        str(out),
        backend="fixture",
        semantic_embedding_backend="lexical",
    )
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert "semantic_coverage" in payload["summary"]
    sem = payload["summary"]["semantic_coverage"]
    assert sem["embedding_backend"] == "lexical"
    assert "ssl_mean_semantic_coverage" in sem
    # at least one scenario carries a per-gap semantic block
    assert any("semantic_coverage" in r for r in payload["results"])
