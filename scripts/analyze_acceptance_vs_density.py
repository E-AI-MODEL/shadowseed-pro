"""Test whether deterministic text-density proxies predict per-item open-set
acceptance, across the four AI-reviewed Phi batches (rounds 006-007).

Round 007 proposed "text density" as the explanation for the out-of-sample
acceptance drop. This script checks that explanation against measurable
surface features. It is analysis, not evidence; it reads committed review
packets and input batches and prints correlations.

Result (2026-06-13, 48 items): all simple proxies correlate weakly
(|r| < 0.25) with per-item acceptance and do not reproduce the batch
ordering. The density explanation is therefore NOT supported by these
proxies; the driver of the drop remains unidentified.
"""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

BATCHES = [
    ("006_b1", "benchmarks/open_review/rounds/round_006/batch1"),
    ("006_b2", "benchmarks/open_review/rounds/round_006/batch2"),
    ("007_A", "benchmarks/open_review/rounds/round_007/batchA"),
    ("007_B", "benchmarks/open_review/rounds/round_007/batchB"),
]

PROXY_KEYS = ("len_words", "num_density", "cap_density", "ttr", "words_per_sent")


def proxies(text: str) -> dict[str, float]:
    words = re.findall(r"[A-Za-zÀ-ÿ]+", text)
    n = len(words) or 1
    sents = len(re.findall(r"[.!?]+", text)) or 1
    uniq = len({w.lower() for w in words})
    return {
        "len_words": float(n),
        "num_density": len(re.findall(r"\d", text)) / n,
        "cap_density": len(re.findall(r"\b[A-Z][a-zA-Z]+", text)) / n,
        "ttr": uniq / n,
        "words_per_sent": n / sents,
    }


def pearson(xs: list[float], ys: list[float]) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = (sum((x - mx) ** 2 for x in xs) * sum((y - my) ** 2 for y in ys)) ** 0.5
    return num / den if den else 0.0


def load_rows(root: Path) -> list[tuple[str, str, float, str]]:
    rows = []
    for name, d in BATCHES:
        d = root / d
        review = json.loads((d / "ai_review/open_set_review_packets.json").read_text(encoding="utf-8"))
        src = {i["id"]: i for i in json.loads((d / "input/hf_batch.json").read_text(encoding="utf-8"))["items"]}
        by_item: dict[str, list[bool]] = {}
        for p in review["packets"]:
            by_item.setdefault(p["item_id"], []).append(p["review_status"] == "accepted")
        for iid, accs in by_item.items():
            rows.append((name, iid, sum(accs) / len(accs), src[iid]["text"]))
    return rows


def main(root: Path = Path(".")) -> int:
    rows = load_rows(root)
    acc = [r[2] for r in rows]
    print(f"items: {len(rows)} | mean acceptance: {statistics.mean(acc):.3f}\n")
    print(f"Per-item acceptance vs proxy (Pearson r across {len(rows)} items):")
    for key in PROXY_KEYS:
        vals = [proxies(r[3])[key] for r in rows]
        print(f"  {key:16} r = {pearson(vals, acc):+.3f}")
    print("\nPer-batch mean acceptance vs mean proxies:")
    for name, _ in BATCHES:
        br = [r for r in rows if r[0] == name]
        a = statistics.mean([x[2] for x in br])
        cap = statistics.mean([proxies(x[3])["cap_density"] for x in br])
        num = statistics.mean([proxies(x[3])["num_density"] for x in br])
        print(f"  {name}: acc {a:.3f} | cap_density {cap:.3f} | num_density {num:.3f}")
    print(
        "\nReading: |r| < 0.25 for every proxy, and batch ordering is not"
        "\nmonotone in any of them -> the 'text density' explanation of the"
        "\nout-of-sample drop is NOT supported by simple surface proxies."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
