"""Ask a model whether two recorded candidates name the same open question.

Compares the model's SAME/DIFFERENT verdicts on the calibration pair sample with
reference labels and with the embedding similarity at the product cluster
threshold, so model-based recurrence recognition can be judged on data before
it is built into the detector.

Usage:
    python scripts/recurrence_judge.py --pairs benchmarks/seed_calibration/results/pair_sample.json \\
        --labels benchmarks/seed_calibration/results/claude_pair_labels.json \\
        --model qwen2.5:7b-instruct-q4_K_M --output <file>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

from shadowseed.recurrence_clustering import DEFAULT_CLUSTER_THRESHOLD

PROMPT = """Two notes were written about open questions in the same conversation, at different turns.

Note A: {a}
Note B: {b}

Do A and B point at the same open question or gap, even if they are worded differently?
Answer with exactly one word: SAME or DIFFERENT."""


def parse_verdict(raw: str) -> str:
    text = raw.strip().upper()
    if text.startswith("SAME"):
        return "same"
    if text.startswith("DIFFERENT"):
        return "different"
    return "unparsed"


def _confusion(predictions: dict[str, str], labels: dict[str, str]) -> dict[str, Any]:
    rows = [(labels[k], predictions.get(k, "unparsed")) for k in labels if labels[k] != "unclear"]
    same = [p for label, p in rows if label == "same"]
    different = [p for label, p in rows if label == "different"]
    correct = sum(label == p for label, p in rows)
    return {
        "same_recognized": f"{same.count('same')}/{len(same)}",
        "different_wrongly_merged": f"{different.count('same')}/{len(different)}",
        "unparsed": sum(p == "unparsed" for _, p in rows),
        "accuracy": round(correct / len(rows), 3) if rows else None,
    }


def judge(pairs: list[dict[str, Any]], generate: Callable[[str], str]) -> dict[str, dict[str, str]]:
    verdicts = {}
    for pair in pairs:
        raw = generate(PROMPT.format(a=pair["text_a"], b=pair["text_b"]))
        verdicts[pair["pair_id"]] = {"raw": raw.strip()[:80], "verdict": parse_verdict(raw)}
    return verdicts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pairs", required=True, type=Path)
    parser.add_argument("--labels", required=True, type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--model-digest", default=None)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    from shadowseed.adapters.ollama_client import OllamaClient

    pairs = json.loads(args.pairs.read_text(encoding="utf-8"))["pairs"]
    labels = json.loads(args.labels.read_text(encoding="utf-8"))["labels"]
    client = OllamaClient(model=args.model)
    client.timeout = 600.0
    verdicts = judge(pairs, lambda prompt: client.generate(prompt, max_new_tokens=8))
    model_predictions = {k: v["verdict"] for k, v in verdicts.items()}
    embedding_predictions = {
        p["pair_id"]: "same" if p["similarity"] >= DEFAULT_CLUSTER_THRESHOLD else "different"
        for p in pairs
    }
    result = {
        "schema": "ssl-recurrence-judge-v1",
        "model": args.model,
        "model_digest": args.model_digest,
        "prompt": PROMPT,
        "reference_labeler": json.loads(args.labels.read_text(encoding="utf-8")).get("labeler"),
        "model_vs_reference": _confusion(model_predictions, labels),
        "embedding_at_default_threshold_vs_reference": _confusion(embedding_predictions, labels),
        "verdicts": verdicts,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("model", "model_vs_reference", "embedding_at_default_threshold_vs_reference")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
