# Round 020 — W9e: cross-turn payoff fires at SAFE doctrine thresholds

> **Status: "make it work" achieved.** With cluster-based recurrence, the
> cross-turn payoff (round 019) now fires at the **safe doctrine thresholds**
> (strict 0.85 storage dedup, Gate bar 3) — the only change from round 018's
> zero-result is that recurrence is counted *semantically* (clustering), not by
> pairwise 0.85. Reconciles round-014 safety with round-019 payoff. Provenance:
> run 27967887887, job 82766341470, `openai:gpt-4.1`, openai embeddings,
> `recurrence_mode=cluster` (dedup/min_occ left blank → defaults).

## The numbers (same conversations as R018/R019)

| run | dedup | Gate bar | recurrence | max_occ | promoted | cross-turn events |
|---|---|---|---|---:|---:|---:|
| R018 | 0.85 (safe) | 3 (safe) | pairwise | 2 | 0 | 0 |
| R019 | **0.6 (loose)** | **2 (loose)** | pairwise | 10 | 11 | 10 |
| **R020** | **0.85 (safe)** | **3 (safe)** | **cluster** | **29** | **49** | **10** |

The decisive comparison is R018 vs R020: **same safe thresholds, opposite
outcome.** The blocker was never the conversation length or the Gate's strictness;
it was that pairwise 0.85 dedup cannot see that paraphrastic gaps are the *same*
recurring gap. Counting recurrence by semantic cluster fixes it without touching
the safe storage/Gate bars.

## Why this matters

- **R019 needed loose, doctrine-adjacent knobs** (0.6 / 2) to make promotion fire,
  which weakened the safety story. **R020 does not** — it keeps the strict dedup
  and the strict Gate bar that round 014 validated as the noise filter, and still
  promotes genuinely recurring (paraphrastic) gaps. So the cross-turn "future
  answer" mechanism is reproducible at *defensible* settings.
- A one-off irrelevant gap stays a singleton cluster (count 1) and never reaches
  the bar → the round-014 safety property is preserved by construction.

## Honest qualifiers (unchanged + one new)

1. **Quality not re-measured here.** R020 is the *engineering* win: the mechanism
   fires at safe thresholds and produces 10 cross-turn answers by the same
   construction as R019. The "richer" *quality* claim still rests on the R019
   human review (2 independent reviewers, 92%/98% agreement) on equivalent
   content; these specific R020 pairs are not separately human-scored yet.
2. **Promotion volume is high (49).** v1 cluster mode promotes *all members* of a
   recurring cluster, not a single representative — on these tightly-themed
   conversations that inflates the promoted count. It does not change the 10
   cross-turn events (surfacing is relevance-gated), but the cluster should
   promote a *representative* in a refinement. Promotion volume is also
   topic-dependent — the per-topic threshold knobs (and auto-calibrate) are the
   intended control.
3. n=3 conversations, one model, author-chosen recurring-theme topics. Signal,
   not general validation.

## Next
- Refine cluster mode to promote a representative per cluster (cut the 49→~cluster
  count) and re-run.
- Human-review a fresh R020 batch to confirm quality holds at safe thresholds.
- Then this is the configuration to carry forward: strict safety + semantic
  recurrence + per-topic tuning.
