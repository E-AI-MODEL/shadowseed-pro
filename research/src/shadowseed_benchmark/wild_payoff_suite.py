"""Non-pipeline wild-payoff contrast suite.

This single-shot derivative does not use the SSLManager lifecycle. It compares
unaided gap spotting with an answer that receives accepted detector seeds. The
pipeline-faithful payoff test is ``ssl_session_suite.py``. Results from this
module are baseline evidence only and must not be treated as a verdict on the
full SSL pipeline.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shadowseed.adapters.models import make_backend
from shadowseed.benchmark.ssl45_model_benefit_suite import blind_order, word_count


def build_wild_baseline_prompt(text: str) -> str:
    return (
        "Read this short report. Give a concise analysis and explicitly name "
        "which important information is missing for a full understanding.\n\n"
        f"Report:\n{text}\n\n"
        "Analysis:"
    )


def build_wild_ssl_prompt(text: str, seeds: list[str]) -> str:
    block = "\n".join(f"- {seed}" for seed in seeds)
    return (
        "Read this short report and write a concise analysis that explicitly "
        "names the important information missing for a full understanding.\n"
        "Integrate each point below naturally into the prose.\n"
        "Rules: do not invent facts beyond the report; do not refer to seeds, "
        "points, or these instructions; return one coherent analysis.\n\n"
        f"Report:\n{text}\n\n"
        f"Missing points to cover:\n{block}\n\n"
        "Analysis:"
    )


def run_wild_payoff_suite(
    input_path: str,
    output_path: str,
    *,
    backend: str = "fixture",
    model_id: str | None = None,
    max_new_tokens: int = 400,
    semantic_embedding_backend: str = "none",
    embedding_model: str | None = None,
    semantic_threshold: float = 0.55,
) -> Path:
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    model = make_backend(backend=backend, model_id=model_id, max_new_tokens=max_new_tokens)

    embed_fn = None
    if semantic_embedding_backend != "none":
        from shadowseed.adapters.embedding import make_embedding_fn

        embed_fn, _dim = make_embedding_fn(semantic_embedding_backend, embedding_model)

    results: list[dict[str, Any]] = []
    blind_items: list[dict[str, Any]] = []
    blind_key: list[dict[str, Any]] = []
    baseline_cov_values: list[float] = []

    for item in data["items"]:
        iid = item["id"]
        text = item["text"]
        seeds = item["detected_seeds"]

        baseline = model.generate(build_wild_baseline_prompt(text), item, "baseline", [])
        ssl = model.generate(build_wild_ssl_prompt(text, seeds), item, "ssl", seeds)

        baseline_cov = None
        novel_gaps = None
        if embed_fn is not None:
            from shadowseed.benchmark.semantic_coverage import semantic_coverage

            frac, covered, per_gap = semantic_coverage(baseline, seeds, embed_fn, semantic_threshold)
            baseline_cov = frac
            novel_gaps = [g["gap"] for g in per_gap if not g["covered"]]
            baseline_cov_values.append(frac)

        first, second = blind_order(iid)
        amap = {"baseline": baseline, "ssl": ssl}
        blind_items.append(
            {
                "review_id": f"review_{iid}",
                "scenario_id": iid,
                "question": f"Which important information is missing from this report?\n\nReport: {text}",
                "option_a": amap[first],
                "option_b": amap[second],
                "reviewer_instruction": (
                    "Choose the analysis that identifies missing information more "
                    "accurately and precisely. Do not reward length; invented or "
                    "irrelevant points make an analysis worse."
                ),
                "scores_to_fill": {"better_answer": "A/B/tie", "notes": ""},
            }
        )
        blind_key.append(
            {"review_id": f"review_{iid}", "option_a_source": first, "option_b_source": second}
        )
        results.append(
            {
                "scenario_id": iid,
                "title": item.get("title", ""),
                "domain": item.get("domain", ""),
                "detected_seeds": seeds,
                "baseline_gap_coverage": baseline_cov,
                "detector_novel_gaps": novel_gaps,
                "answer_length_delta_words": word_count(ssl) - word_count(baseline),
                "baseline_answer": baseline,
                "ssl_answer": ssl,
            }
        )

    summary = {
        "artifact": "wild_payoff_suite",
        "backend": getattr(model, "name", backend),
        "item_count": len(results),
        "source": data.get("source", ""),
        "semantic_embedding_backend": semantic_embedding_backend,
        "mean_baseline_gap_coverage": (
            sum(baseline_cov_values) / len(baseline_cov_values) if baseline_cov_values else None
        ),
        "interpretation": (
            "W1 wild loop: detected (not author-designed) gap-seeds through the "
            "payoff pipeline. mean_baseline_gap_coverage = how much of the "
            "detector's gaps a strong model already finds unaided; LOW means the "
            "detector adds value the model missed. Blind A/B pairs judge overall "
            "analysis quality. Signal, not proof; detected gaps are the ground "
            "truth so ssl coverage is not informative on its own."
        ),
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "summary": summary,
                "results": results,
                "blind_review_items": blind_items,
                "blind_answer_key": blind_key,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return out
