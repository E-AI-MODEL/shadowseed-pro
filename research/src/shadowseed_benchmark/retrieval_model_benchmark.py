"""Benchmark retrieval-backed model output quality.

This suite connects the final chain:

    retrieval -> SSOT context -> model answer -> gap coverage

It compares the same model in two conditions:

1. baseline: answer without retrieved SSOT context;
2. retrieval: answer with chunks retrieved from the chosen vectorstore backend.

The fixture model is deterministic and CI-safe. The hf-transformers model is
optional for real SLM runs.
"""

from __future__ import annotations

import json
from pathlib import Path

from shadowseed.text_similarity import lexical_embedding
from shadowseed.benchmark.ssl45_model_benefit_suite import (
    HFTransformersBackend,
    OpenAIBackend,
    coverage,
    word_count,
)
from shadowseed.vectorstore import create_vector_store


class RetrievalFixtureModel:
    name = "fixture"

    def generate(self, prompt: str, retrieved_chunks: list[str], mode: str) -> str:
        if mode == "baseline":
            return "General answer without specific SSOT context."
        return " ".join(retrieved_chunks)


def make_output_model(model_backend: str, model_id: str | None, max_new_tokens: int):
    if model_backend == "fixture":
        return RetrievalFixtureModel()
    if model_backend == "hf-transformers":
        if not model_id:
            raise ValueError("--model-id is required for hf-transformers")
        return HFTransformersBackend(model_id=model_id, max_new_tokens=max_new_tokens)
    if model_backend == "openai":
        if not model_id:
            raise ValueError("--model-id is required for openai")
        return OpenAIBackend(model_id=model_id, max_new_tokens=max_new_tokens)
    raise ValueError(f"Unknown model backend: {model_backend}")


def unique_preserve_order(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def build_baseline_prompt(question: str) -> str:
    return (
        "Answer the question clearly and concisely. Do not use additional "
        "source context.\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


def build_retrieval_prompt(question: str, chunks: list[str]) -> str:
    context = "\n".join(f"- {chunk}" for chunk in chunks)
    return (
        "Answer the question using only this SSOT context. Include only points "
        "supported by the context.\n\n"
        f"Question: {question}\n\n"
        f"SSOT context:\n{context}\n\n"
        "Answer:"
    )


def model_generate(model, prompt: str, retrieved_chunks: list[str], mode: str) -> str:
    if isinstance(model, RetrievalFixtureModel):
        return model.generate(prompt, retrieved_chunks, mode)
    return model.generate(prompt, {}, mode, [])


def index_retrieval_corpus(store, retrieval_data: dict, embed_fn=None) -> None:
    embed = embed_fn if embed_fn is not None else lexical_embedding
    for doc in retrieval_data["documents"]:
        for chunk in doc["chunks"]:
            store.add(
                chunk["chunk_id"],
                embed(chunk["text"]),
                {
                    "text": chunk["text"],
                    "doc_id": doc["doc_id"],
                    "chunk_id": chunk["chunk_id"],
                    "source": doc.get("source", "fixture"),
                },
            )


def retrieve_chunks(store, queries: list[str], top_k: int) -> list[dict]:
    retrieved = []
    for query in queries:
        hits = store.search(lexical_embedding(query), top_k=top_k)
        for chunk_id, score, metadata in hits:
            retrieved.append(
                {
                    "query": query,
                    "chunk_id": chunk_id,
                    "score": score,
                    "text": metadata.get("text", ""),
                    "doc_id": metadata.get("doc_id"),
                }
            )
    return retrieved


def run_retrieval_model_benchmark(
    data_path: str,
    retrieval_data_path: str,
    output_path: str,
    vector_backend: str = "memory",
    model_backend: str = "fixture",
    model_id: str | None = None,
    max_new_tokens: int = 220,
    top_k: int = 3,
) -> Path:
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    retrieval_data = json.loads(Path(retrieval_data_path).read_text(encoding="utf-8"))
    store = create_vector_store(backend=vector_backend, dimensions=128)
    index_retrieval_corpus(store, retrieval_data)
    model = make_output_model(model_backend, model_id, max_new_tokens)

    results = []
    baseline_coverages = []
    retrieval_coverages = []
    length_deltas = []

    for scenario in data["scenarios"]:
        retrieved = retrieve_chunks(store, scenario["queries"], top_k=top_k)
        retrieved_texts = unique_preserve_order([item["text"] for item in retrieved if item["text"]])

        baseline_prompt = build_baseline_prompt(scenario["question"])
        retrieval_prompt = build_retrieval_prompt(scenario["question"], retrieved_texts)

        baseline_answer = model_generate(model, baseline_prompt, [], "baseline")
        retrieval_answer = model_generate(model, retrieval_prompt, retrieved_texts, "retrieval")

        baseline_cov, baseline_covered = coverage(baseline_answer, scenario["expected_additions"])
        retrieval_cov, retrieval_covered = coverage(retrieval_answer, scenario["expected_additions"])
        baseline_words = word_count(baseline_answer)
        retrieval_words = word_count(retrieval_answer)
        length_delta = retrieval_words - baseline_words
        coverage_delta = retrieval_cov - baseline_cov

        baseline_coverages.append(baseline_cov)
        retrieval_coverages.append(retrieval_cov)
        length_deltas.append(length_delta)

        results.append(
            {
                "scenario_id": scenario["id"],
                "domain": scenario["domain"],
                "question": scenario["question"],
                "baseline_gap_coverage": baseline_cov,
                "retrieval_gap_coverage": retrieval_cov,
                "coverage_delta": coverage_delta,
                "baseline_word_count": baseline_words,
                "retrieval_word_count": retrieval_words,
                "answer_length_delta_words": length_delta,
                "coverage_delta_per_100_added_words": (
                    coverage_delta / length_delta * 100 if length_delta > 0 else coverage_delta
                ),
                "baseline_covered": baseline_covered,
                "retrieval_covered": retrieval_covered,
                "retrieved_chunks": retrieved,
                "baseline_answer": baseline_answer,
                "retrieval_answer": retrieval_answer,
            }
        )

    baseline_mean = sum(baseline_coverages) / len(baseline_coverages)
    retrieval_mean = sum(retrieval_coverages) / len(retrieval_coverages)
    mean_length_delta = sum(length_deltas) / len(length_deltas)
    summary = {
        "suite_version": data.get("version"),
        "vector_backend": vector_backend,
        "model_backend": model.name,
        "scenario_count": len(data["scenarios"]),
        "top_k": top_k,
        "baseline_mean_gap_coverage": baseline_mean,
        "retrieval_mean_gap_coverage": retrieval_mean,
        "coverage_delta": retrieval_mean - baseline_mean,
        "mean_answer_length_delta_words": mean_length_delta,
        "coverage_delta_per_100_added_words": (
            (retrieval_mean - baseline_mean) / mean_length_delta * 100
            if mean_length_delta > 0
            else retrieval_mean - baseline_mean
        ),
        "interpretation": (
            "This benchmark tests whether retrieved SSOT context improves model output quality. "
            "The fixture model isolates retrieval effects; hf-transformers is the real SLM mode."
        ),
    }

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"summary": summary, "results": results}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
