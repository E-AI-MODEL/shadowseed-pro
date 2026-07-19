"""Human-vs-AI second-reviewer control for open-set seed review.

The delegated AI review (`reviewer_ai_claude`) is a single reviewer; round 007
showed reviewer variance is an unseparated confound. This tool sets up a *real*
independent second pass: a human (or a genuinely different agent) re-reviews the
same candidates blind, and we compute human acceptance + human-vs-AI agreement
(raw, per-criterion, Cohen's kappa) — the first agreement number since the round
005 human batch.

  build  <round-batch-dir>  -> human_review_packets.json (blind, shuffled, empty)
  score  <round-batch-dir>  -> agreement report from the FILLED human packet
                              vs the committed ai_review packets

Blind discipline: the human packet carries NO AI verdicts; order is shuffled
deterministically (seeded by seed_id) so the AI review's order cannot leak. The
reviewer fills review_fields + review_status (+ reject_reason); they must not
open ai_review/ while reviewing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

CRITERIA = ("atomicity", "relevance", "testability", "non_triviality", "follow_up_utility")


def _ai_packets(batch_dir: Path) -> dict[str, dict[str, Any]]:
    data = json.loads((batch_dir / "ai_review/open_set_review_packets.json").read_text(encoding="utf-8"))
    return {f"{p['item_id']}|{p['seed_text']}": p for p in data["packets"]}


def build(batch_dir: Path) -> Path:
    ai = _ai_packets(batch_dir)
    rows = []
    for key, p in ai.items():
        rows.append(
            {
                "item_id": p["item_id"],
                "title": p.get("title"),
                "domain": p.get("domain"),
                "source_excerpt": p.get("source_excerpt"),
                "seed_id": p.get("seed_id"),
                "seed_text": p["seed_text"],
                "reviewer_id": "reviewer_human_1",
                "review_fields": {c: None for c in CRITERIA},
                "review_status": "pending",
                "reject_reason": None,
                "reviewer_notes": "",
            }
        )
    # deterministic blind shuffle (independent of AI review order)
    rows.sort(key=lambda r: hashlib.sha1(str(r["seed_id"]).encode()).hexdigest())
    out = batch_dir / "human_review" / "human_review_packets.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "evidence_layer": "open_set_seed_quality",
        "review_note": (
            "BLIND human second pass. Fill review_fields (5 booleans), "
            "review_status accepted/rejected, and reject_reason on reject. "
            "Do NOT open ../ai_review/ while reviewing. Reject codes: "
            "too_broad, too_vague, trivial, not_relevant, not_testable, "
            "duplicate, style_not_gap."
        ),
        "criteria": list(CRITERIA),
        "packets": rows,
    }
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(rows)} blind human-review rows to {out}")
    return out


def _accept(status: str) -> bool:
    return str(status).strip().lower() in {"accept", "accepted"}


def _kappa(a: list[bool], b: list[bool]) -> float:
    n = len(a)
    if not n:
        return 0.0
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return (po - pe) / (1 - pe) if pe != 1 else 1.0


def score(batch_dir: Path) -> dict[str, Any]:
    ai = _ai_packets(batch_dir)
    human = json.loads(
        (batch_dir / "human_review/human_review_packets.json").read_text(encoding="utf-8")
    )["packets"]
    pairs = []
    pending = 0
    for h in human:
        if h.get("review_status", "pending") == "pending":
            pending += 1
            continue
        key = f"{h['item_id']}|{h['seed_text']}"
        if key in ai:
            pairs.append((_accept(h["review_status"]), _accept(ai[key]["review_status"])))
    if not pairs:
        return {"status": "no_completed_human_rows", "pending": pending, "total": len(human)}
    hum = [p[0] for p in pairs]
    aiv = [p[1] for p in pairs]
    n = len(pairs)
    agree = sum(1 for x, y in zip(hum, aiv) if x == y)
    return {
        "completed_pairs": n,
        "pending_human_rows": pending,
        "human_acceptance": round(sum(hum) / n, 3),
        "ai_acceptance": round(sum(aiv) / n, 3),
        "raw_agreement": round(agree / n, 3),
        "cohens_kappa": round(_kappa(hum, aiv), 3),
        "both_accept": sum(1 for x, y in zip(hum, aiv) if x and y),
        "both_reject": sum(1 for x, y in zip(hum, aiv) if not x and not y),
        "human_only_accept": sum(1 for x, y in zip(hum, aiv) if x and not y),
        "ai_only_accept": sum(1 for x, y in zip(hum, aiv) if y and not x),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="mode", required=True)
    b = sub.add_parser("build")
    b.add_argument("batch_dir")
    s = sub.add_parser("score")
    s.add_argument("batch_dir")
    args = ap.parse_args(argv)
    if args.mode == "build":
        build(Path(args.batch_dir))
    else:
        print(json.dumps(score(Path(args.batch_dir)), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
