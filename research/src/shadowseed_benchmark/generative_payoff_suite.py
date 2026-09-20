"""Non-pipeline generative-payoff contrast suite.

This single-shot derivative does not use the SSLManager lifecycle. It measures
``detector output -> prompt -> answer`` and must not be presented as a result
about the full SSL pipeline. The pipeline-faithful payoff test is
``ssl_session_suite.py``.

The suite tests whether a generative detector proposes non-obvious explanatory
frames that a baseline model does not raise unaided and whether blind reviewers
prefer the answer after those frames are integrated. It is a research signal,
not proof.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from shadowseed.detection.model_detector import make_detector_backend
from shadowseed.adapters.models import make_backend
from shadowseed.benchmark.ssl45_model_benefit_suite import blind_order, word_count


def build_generative_baseline_prompt(question: str) -> str:
    return (
        "Answer this question thoroughly and insightfully. Identify the main "
        "explanatory angles.\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )


def build_generative_ssl_prompt(question: str, frames: list[str]) -> str:
    block = "\n".join(f"- {frame}" for frame in frames)
    return (
        "Answer this question thoroughly and insightfully. Integrate the "
        "following explanatory frames naturally into the answer.\n"
        "Rules: do not invent facts; do not refer to angles, frames, seeds, or "
        "these instructions; return one coherent answer.\n\n"
        f"Question: {question}\n\n"
        f"Frames to integrate:\n{block}\n\n"
        "Answer:"
    )


def run_generative_payoff_suite(
    input_path: str,
    output_path: str,
    *,
    backend: str = "fixture",
    model_id: str | None = None,
    max_new_tokens: int = 400,
    max_frames: int = 3,
    semantic_embedding_backend: str = "none",
    embedding_model: str | None = None,
    semantic_threshold: float = 0.55,
) -> Path:
    data = json.loads(Path(input_path).read_text(encoding="utf-8"))
    model = make_backend(backend=backend, model_id=model_id, max_new_tokens=max_new_tokens)
    detector = make_detector_backend(
        backend, model_id=model_id, max_new_tokens=max_new_tokens, prompt_variant="generative"
    )

    embed_fn = None
    if semantic_embedding_backend != "none":
        from shadowseed.adapters.embedding import make_embedding_fn

        embed_fn, _dim = make_embedding_fn(semantic_embedding_backend, embedding_model)

    results: list[dict[str, Any]] = []
    blind_items: list[dict[str, Any]] = []
    blind_key: list[dict[str, Any]] = []
    baseline_cov_values: list[float] = []
    items_with_frames = 0

    for item in data["items"]:
        iid = item["id"]
        question = item["question"]
        frames = detector.detect_seeds({"text": item["text"]}, max_seeds=max_frames)

        baseline = model.generate(build_generative_baseline_prompt(question), item, "baseline", [])
        if frames:
            items_with_frames += 1
            ssl = model.generate(build_generative_ssl_prompt(question, frames), item, "ssl", frames)
        else:
            ssl = baseline  # no frame detected -> nothing to act on (do-no-harm)

        baseline_cov = None
        novel_frames = None
        if embed_fn is not None and frames:
            from shadowseed.benchmark.semantic_coverage import semantic_coverage

            frac, _cov, per = semantic_coverage(baseline, frames, embed_fn, semantic_threshold)
            baseline_cov = frac
            novel_frames = [g["gap"] for g in per if not g["covered"]]
            baseline_cov_values.append(frac)

        first, second = blind_order(iid)
        amap = {"baseline": baseline, "ssl": ssl}
        blind_items.append(
            {
                "review_id": f"review_{iid}",
                "scenario_id": iid,
                "question": question,
                "option_a": amap[first],
                "option_b": amap[second],
                "reviewer_instruction": (
                    "Choose the richer and more insightful answer. A non-obvious "
                    "but relevant angle can improve an answer; forced or invented "
                    "angles make it worse. Do not reward length by itself."
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
                "detected_frames": frames,
                "baseline_frame_coverage": baseline_cov,
                "novel_frames": novel_frames,
                "answer_length_delta_words": word_count(ssl) - word_count(baseline),
                "baseline_answer": baseline,
                "ssl_answer": ssl,
            }
        )

    summary = {
        "artifact": "generative_payoff_suite",
        "backend": getattr(model, "name", backend),
        "detector": getattr(detector, "name", backend),
        "item_count": len(results),
        "items_with_frames": items_with_frames,
        "semantic_embedding_backend": semantic_embedding_backend,
        "mean_baseline_frame_coverage": (
            sum(baseline_cov_values) / len(baseline_cov_values) if baseline_cov_values else None
        ),
        "interpretation": (
            "W5 generative payoff. mean_baseline_frame_coverage = how often the "
            "model raises the detected reframing angle UNAIDED; LOW means the frame "
            "is genuinely non-obvious (SSL's unique territory). Blind A/B judges "
            "whether weaving the frame made the answer richer. SSL shows unique "
            "value only if frames are non-obvious AND improve the answer. Signal, "
            "not proof; topics author-chosen, frames detector-produced."
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
