"""Rubric-sensitivity bound on the delegated AI acceptance numbers.

The acceptance rates in rounds 006-007 come from one reviewer applying a rubric
whose softest criteria (non_triviality, follow_up_utility) are judgment calls.
This script measures how fragile those numbers are: it re-aggregates the SAME
committed AI verdicts under one deliberately stricter, fully deterministic
operationalization, and reports the swing per batch.

It is NOT independent review and NOT a claim that the strict rule is more
correct. It is a self-consistency / fragility bound: same agent, an alternative
decision rule, measuring how much acceptance moves. The human second pass
(scripts/human_review_control.py) is what decides which rule is closer to a
human's.

Strict rule: an accepted candidate is DEMOTED if it reads as a generic
detail / impact / speculation ask rather than a specific named gap -- the
exact calls a stricter reviewer would most plausibly flip.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

BATCHES = [
    ("006_b1", "benchmarks/open_review/rounds/round_006/batch1"),
    ("006_b2", "benchmarks/open_review/rounds/round_006/batch2"),
    ("007_A", "benchmarks/open_review/rounds/round_007/batchA"),
    ("007_B", "benchmarks/open_review/rounds/round_007/batchB"),
]

_IMPACT = re.compile(
    r"\b(impact|reactie|reacties|gevolg|gevolgen|effect|effecten|implicaties|invloed)\b", re.I
)
_GENERIC_HEAD = re.compile(
    r"^(de\s+)?(specifieke|exacte)\s+"
    r"(functies|soorten|aspecten|details|kenmerken|eigenschappen|aard)\b",
    re.I,
)
_VAGUE = re.compile(r"^details over\b", re.I)
# Speculation: asks about hypothetical/expected things rather than a concrete
# stated-or-clearly-missing fact ("De *mogelijke* fraudpreventiemaatregelen ...").
_SPECULATION = re.compile(r"\b(mogelijk\w*|potenti\w*|eventuel\w*|verwacht\w*)\b", re.I)


def demote(seed_text: str) -> bool:
    """True if a stricter reviewer would most plausibly reject this accept.

    Covers the four mechanically-detectable softness patterns named in the
    module docstring: impact/reaction asks, generic class-head asks, vague
    "details over" openers, and speculation about hypotheticals.
    """
    t = seed_text.strip()
    return bool(
        _IMPACT.search(t)
        or _GENERIC_HEAD.match(t)
        or _VAGUE.match(t)
        or _SPECULATION.search(t)
    )


def analyze_batch(batch_dir: Path) -> dict[str, Any]:
    packets = json.loads(
        (batch_dir / "ai_review/open_set_review_packets.json").read_text(encoding="utf-8")
    )["packets"]
    n = len(packets)
    accepted = [p for p in packets if p["review_status"] == "accepted"]
    demoted = [p for p in accepted if demote(p["seed_text"])]
    return {
        "candidates": n,
        "ai_accepted": len(accepted),
        "ai_acceptance": round(len(accepted) / n, 3) if n else 0.0,
        "strict_accepted": len(accepted) - len(demoted),
        "strict_acceptance": round((len(accepted) - len(demoted)) / n, 3) if n else 0.0,
        "demoted": [p["seed_text"] for p in demoted],
    }


def main(root: Path = Path(".")) -> int:
    print(f"{'batch':9} {'cands':>5} {'AI_acc':>7} {'strict':>7} {'swing':>7}")
    rows = []
    for name, d in BATCHES:
        r = analyze_batch(root / d)
        rows.append((name, r))
        swing = r["strict_acceptance"] - r["ai_acceptance"]
        print(f"{name:9} {r['candidates']:5} {r['ai_acceptance']:7.3f} "
              f"{r['strict_acceptance']:7.3f} {swing:+7.3f}")
    ai = [r["ai_acceptance"] for _, r in rows]
    st = [r["strict_acceptance"] for _, r in rows]
    print(
        f"\ncross-batch spread: AI {max(ai)-min(ai):.3f}  strict {max(st)-min(st):.3f}"
        "\nReading: acceptance is rubric-sensitive; the biggest swing is on the"
        "\n0.50 headline batch (006_b1), and the strict rule compresses the"
        "\ncross-batch spread -- so part of the in-sample/out-of-sample gap was"
        "\nreviewer leniency, not only items. The human pass arbitrates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
