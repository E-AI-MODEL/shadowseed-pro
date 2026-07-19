# Round 018 — W9b: longer conversations, and the precise bottleneck

> **Status: the cross-turn payoff still cannot be observed — and we now know
> exactly why.** Longer, theme-returning conversations did NOT change the outcome.
> The blocker is located: paraphrastic LLM gaps don't deduplicate, so recurrence
> never accumulates to promotion. Provenance: run 27897764350, job 82552366959,
> `openai:gpt-4.1`, openai embeddings, 3 conversations (4/9/9 turns).

## The numbers

| diagnostic | round 017 (4-turn) | round 018 (up to 9-turn) |
|---|---:|---:|
| gaps detected (total) | 40 | **110** |
| **max occurrence_count any seed reached** | 2 | **2** |
| seeds ever promoted | 0 | **0** |
| cross_turn_payoff_events | 0 | **0** |

More turns, far more gaps (110) — but the **max times any single gap recurred is
still 2**. So the recurrence Gate (needs ≥3) never fires; nothing promotes;
nothing can travel.

## The precise bottleneck (this is the finding)

It is **not** "conversations too short". It is **deduplication**: the generative
detector phrases the same underlying gap *differently* each turn ("privacy",
"datagebruik door derden", "vertrouwen van gebruikers op lange termijn"…). The
dedup threshold is **0.85 cosine**; paraphrases of one concept land well below
that, so the pipeline stores them as *distinct* weight-0 seeds (each occurrence
1–2) instead of merging them into one recurring seed. Recurrence therefore never
accumulates, and recurrence is the precondition for the Gate.

So the chain that should power SSL's "not-yet-an-answer-now-becomes-one-later"
property breaks at the very first link:

```
detect (works: 110 gaps) -> DEDUP (fails: paraphrases don't merge at 0.85)
   -> recurrence (stuck at <=2) -> Gate (never fires) -> promotion (0)
   -> cross-turn shadow (none) -> future answer (cannot be tested)
```

## Honest implications

1. **SSL's cross-turn value is still untested** — not refuted. The machinery that
   would let a shadow become a future answer never gets to run, because
   paraphrastic recurrence doesn't register.
2. **The bottleneck is a concrete, tunable parameter** (dedup threshold +
   min_occurrences), not a deep impossibility. But changing it is doctrine-
   adjacent: a looser dedup merges more aggressively (more recurrence, but risk of
   collapsing genuinely-distinct gaps), and a lower recurrence bar re-opens the
   noise door round 014 warned about (now backstopped by TTL/EXPIRED).
3. This reframes the whole open-set→payoff loop: SSL's recurrence model assumes
   gaps recur *recognisably*. With an LLM detector they recur *semantically but
   not lexically/embedding-closely enough*. Either the dedup must be semantic
   enough to catch paraphrase, or recurrence must be measured differently
   (e.g. cluster-based, not pairwise-threshold).

## Next decision (for the maintainer)

A clean, reversible experiment that keeps global doctrine defaults intact: expose
`dedup_threshold` / `min_occurrences` as **per-run** knobs and re-run W9b with a
looser dedup (e.g. ~0.6) so paraphrastic recurrence can merge — purely to answer:
*if promotion CAN fire, does a cross-turn shadow then surface value at a later
turn?* If yes, SSL's unique property is real and the work shifts to a better
recurrence/dedup model. If still nothing, the cross-turn claim is in serious
doubt even with the machinery unblocked.
