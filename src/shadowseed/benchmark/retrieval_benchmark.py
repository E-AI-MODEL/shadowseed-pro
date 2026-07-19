from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from shadowseed.text_similarity import lexical_embedding
from shadowseed.vectorstore import create_vector_store


def compute_metrics(ranks: list[int], k: int = 3):
    hits = [1 if r <= k else 0 for r in ranks]
    precision = mean(hits)
    recall = mean(hits)
    avg_rank = mean(ranks)
    return {
        "hit@k": precision,
        "precision@k": precision,
        "recall@k": recall,
        "avg_rank": avg_rank,
    }


def run_retrieval_benchmark(data_path: str, output_path: str, backend: str = "memory", k: int = 3):
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))

    store = create_vector_store(backend=backend, dimensions=128)

    # index documents
    for doc in data["documents"]:
        for chunk in doc["chunks"]:
            emb = lexical_embedding(chunk["text"])
            store.add(chunk["chunk_id"], emb, {"text": chunk["text"], "doc_id": doc["doc_id"]})

    ranks = []
    details = []

    for q in data["queries"]:
        emb = lexical_embedding(q["query"])
        results = store.search(emb, top_k=10)

        found_rank = 999
        for i, (cid, _, _) in enumerate(results, start=1):
            if cid in q["relevant_chunk_ids"]:
                found_rank = i
                break

        ranks.append(found_rank)
        details.append({
            "query": q["query"],
            "rank": found_rank,
            "top_result": results[0][0] if results else None,
        })

    metrics = compute_metrics(ranks, k=k)

    payload = {
        "backend": backend,
        "metrics": metrics,
        "details": details,
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    return out
