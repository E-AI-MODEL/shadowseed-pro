"""Win-rate scorer for the SSL payoff test (round 008).

`run-model-benefit-suite` already emits, per scenario, a blind answer-pair
review item (`option_a`/`option_b`, order shuffled) plus a hidden
`blind_answer_key` mapping each option to `baseline`/`ssl`. A reader fills
`scores_to_fill.better_answer` = `A` / `B` / `tie` without seeing the key.

This script unblinds the FILLED output and reports whether the SSL-guided
answer actually wins under blind judgment:

- ssl_win_rate = ssl_wins / (ssl_wins + baseline_wins), ties reported apart;
- a length control: the same win rate restricted to pairs where the SSL answer
  was NOT longer than the baseline, so a win cannot be just "more words".

It is the end-to-end payoff metric (does acting on validated seeds help?), not
the deterministic coverage-delta the suite already computes. Still a signal,
not proof: small n, reader-judged. A null/negative result is a valid, important
outcome.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _letter_to_source(item: dict[str, Any], key: dict[str, Any], letter: str) -> str | None:
    letter = (letter or "").strip().upper()
    if letter == "A":
        return key["option_a_source"]
    if letter == "B":
        return key["option_b_source"]
    return None  # tie / unfilled


def score(payload: dict[str, Any]) -> dict[str, Any]:
    keys = {k["review_id"]: k for k in payload.get("blind_answer_key", [])}
    results = {r["scenario_id"]: r for r in payload.get("results", [])}

    ssl_wins = baseline_wins = ties = pending = 0
    ssl_wins_len_neutral = baseline_wins_len_neutral = 0
    decided_len_neutral = 0

    for item in payload.get("blind_review_items", []):
        rid = item["review_id"]
        key = keys.get(rid)
        if not key:
            continue
        verdict = str(item.get("scores_to_fill", {}).get("better_answer", "")).strip().lower()
        if verdict in ("a", "b"):
            winner = _letter_to_source(item, key, verdict)
        elif verdict == "tie":
            ties += 1
            continue
        else:
            pending += 1
            continue

        # length control: was the SSL answer longer than baseline for this item?
        res = results.get(item["scenario_id"], {})
        ssl_longer = res.get("answer_length_delta_words", 0) > 0

        if winner == "ssl":
            ssl_wins += 1
            if not ssl_longer:
                decided_len_neutral += 1
                ssl_wins_len_neutral += 1
        elif winner == "baseline":
            baseline_wins += 1
            if not ssl_longer:
                decided_len_neutral += 1
                baseline_wins_len_neutral += 1

    decided = ssl_wins + baseline_wins

    def rate(num: int, den: int) -> float | None:
        return round(num / den, 3) if den else None

    return {
        "artifact": "answer_pair_winrate",
        "disclaimer": (
            "End-to-end payoff signal: SSL-guided vs baseline answer under blind "
            "reader judgment. Small n, reader-judged; a signal, not proof. A "
            "null/negative result is a valid outcome."
        ),
        "decided_pairs": decided,
        "ssl_wins": ssl_wins,
        "baseline_wins": baseline_wins,
        "ties": ties,
        "pending": pending,
        "ssl_win_rate": rate(ssl_wins, decided),
        "length_neutral_decided_pairs": decided_len_neutral,
        "ssl_win_rate_length_neutral": rate(ssl_wins_len_neutral, decided_len_neutral),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("benefit_output", help="filled run-model-benefit-suite output JSON")
    ap.add_argument("--output", default=None)
    args = ap.parse_args(argv)
    payload = json.loads(Path(args.benefit_output).read_text(encoding="utf-8"))
    report = score(payload)
    if args.output:
        Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
