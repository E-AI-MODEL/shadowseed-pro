# Round 013 — blind human review (how to fill)

These are 10 blind answer pairs from the gpt-4.1 payoff run (round 013). One
answer in each pair used SSL-guided revision, the other did not — **you do not
know which**, and that is the point.

## What to do

1. Open `review_pack.md`.
2. For each item, read the question and both answers (A and B).
3. Write `better_answer` = **A**, **B**, or **tie** — which answer addresses the
   question better (correctness + coverage). **Do not reward length on its own**:
   a longer answer that adds noise or unsupported claims is not better.
4. Do **not** open `answer_key.json` until you have scored everything (it reveals
   which side is SSL and the assistant's own verdicts).

## What happens next

Hand the filled file back and I will compute:

- **human SSL win-rate** (how often the SSL answer beat the baseline);
- **human-vs-AI agreement** (raw agreement + Cohen's κ) against `ai_better_answer`
  in the key — the same check that gave κ 0.63 in round 006.

That turns the current AI-judged payoff signal into a human-anchored result.

## Honesty notes

- One scenario (`DNH_UNITS`) is a deliberate do-no-harm control: a complete
  factual answer with no real gap. If both sides look equivalent, score `tie`.
- It is fine to score against SSL. A few honest "baseline is better" or "tie"
  judgments make the agreement number meaningful; rubber-stamping does not.
