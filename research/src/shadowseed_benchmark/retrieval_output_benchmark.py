from __future__ import annotations

import json
from pathlib import Path

from shadowseed.text_similarity import lexical_embedding
from shadowseed.vectorstore import create_vector_store


def simple_llm_answer(question: str, retrieved_chunks: list[str]):
    # Simple simulation: the answer is the concatenation of top chunks.
    return " ".join(retrieved_chunks[:3])


def compute_gap_coverage(answer: str, expected: list[str]):
    hits = sum(1 for e in expected if any(word in answer for word in e.split()))
    return hits / len(expected)


def run_retrieval_output_benchmark(data_path: str, retrieval_data_path: str, output_path: str, backend: str):
    data = json.loads(Path(data_path).read_text())
    retrieval_data = json.loads(Path(retrieval_data_path).read_text())

    store = create_vector_store(backend=backend, dimensions=128)

    # index retrieval dataset chunks
    for doc in retrieval_data["documents"]:
        for chunk in doc["chunks"]:
            store.add(chunk["chunk_id"], lexical_embedding(chunk["text"]), {"text": chunk["text"]})

    results = []

    for scenario in data["scenarios"]:
        retrieved = []

        for q in scenario["queries"]:
            emb = lexical_embedding(q)
            hits = store.search(emb, top_k=3)
            retrieved.extend([h[2]["text"] for h in hits])

        answer = simple_llm_answer(scenario["question"], retrieved)
        coverage = compute_gap_coverage(answer, scenario["expected_additions"])

        results.append({
            "id": scenario["id"],
            "coverage": coverage
        })

    avg = sum(r["coverage"] for r in results) / len(results)

    payload = {
        "backend": backend,
        "average_gap_coverage": avg,
        "results": results
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))

    return out
