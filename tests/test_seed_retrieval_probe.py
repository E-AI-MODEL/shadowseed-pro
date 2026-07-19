"""Tests for the SSL->RAG bridge: the seed-driven Retrieval Probe (gap 2)."""
from __future__ import annotations

from shadowseed.retrieval_probe import (
    centroid_of,
    retrieval_probe_vs_question,
    run_seed_retrieval_probe,
)
from shadowseed.benchmark.ssl45_gap_suite import lexical_embedding
from shadowseed.vectorstore import create_vector_store


def _store():
    s = create_vector_store(backend="memory", dimensions=128)
    chunks = {
        "c_innovation": "James Watt verbeterde de stoommachine en de spinning jenny.",
        "c_colonial": "Koloniaal kapitaal en grondstoffen uit de koloniën financierden fabrieken.",
        "c_labour": "Arbeidsomstandigheden in vroege fabrieken en kinderarbeid.",
        "c_weather": "Het weer in Manchester is vaak nat en bewolkt.",
    }
    for cid, text in chunks.items():
        s.add(cid, lexical_embedding(text), {"text": text, "doc_id": cid})
    return s


def test_seed_probe_retrieves_for_the_gap_and_expands_beyond_the_question():
    store = _store()
    # The question is about innovation; the seed is the colonial-capital gap.
    out = retrieval_probe_vs_question(
        store,
        question="Waarom dreven uitvindingen de Industriële Revolutie?",
        seed_texts=["Koloniaal kapitaal als financieringsbron voor fabrieken."],
        top_k=2,
    )
    # the seed probe surfaces the gap-relevant (colonial) chunk
    assert "c_colonial" in out["probe_chunk_ids"]
    # and the probe changes what is retrieved: it brings in context the question
    # retrieval did not — the core "a seed finds what the question wouldn't".
    assert out["seed_only_chunk_ids"]
    assert set(out["probe_chunk_ids"]) != set(out["question_chunk_ids"])


def test_centroid_probe_unions_a_constellation():
    store = _store()
    hits = run_seed_retrieval_probe(
        store,
        ["Koloniaal kapitaal als financieringsbron.", "Arbeidsomstandigheden in fabrieken."],
        top_k=2,
        use_centroid=True,
    )
    assert hits and all(h["probe_query"] == "__centroid__" for h in hits)


def test_per_seed_probe_dedups_by_chunk_keeping_best():
    store = _store()
    hits = run_seed_retrieval_probe(
        store,
        ["Koloniaal kapitaal financiering.", "Koloniale grondstoffen voor fabrieken."],
        top_k=3,
    )
    ids = [h["chunk_id"] for h in hits]
    assert len(ids) == len(set(ids))  # no duplicate chunks across seed queries
    # sorted by score descending
    assert hits == sorted(hits, key=lambda d: d["score"], reverse=True)


def test_empty_seeds_returns_nothing():
    assert run_seed_retrieval_probe(_store(), [], top_k=3) == []


def test_centroid_of_requires_seeds():
    import pytest
    with pytest.raises(ValueError):
        centroid_of([])
