# Round 019 — W9c: the cross-turn payoff FIRES through the real pipeline (first positive)

> **Status: first positive signal for SSL's actual mechanism (gap 5), through the
> real `SSLManager` — with honest qualifiers.** With per-run looser dedup (0.6) +
> recurrence bar (2), paraphrastic gaps merge, recurrence accumulates, the
> Validation Gate promotes, and early-born weight-0 shadows resurface to make
> later answers richer. Provenance: run 27898096621, job 82553268563,
> `openai:gpt-4.1`, openai embeddings. Global doctrine defaults unchanged.

## The mechanism finally runs

| diagnostic | round 018 (defaults) | round 019 (dedup 0.6, min_occ 2) |
|---|---:|---:|
| gaps detected | 110 | 110 |
| **max occurrence_count** | 2 | **10** |
| **seeds ever promoted** | 0 | **11** |
| **cross_turn_payoff_events** | 0 | **10** |

The chain that was blocked at "dedup" in round 018 now completes end-to-end:
detect → dedup (paraphrases merge at 0.6) → recurrence (up to 10×) → Gate
(11 promotions) → cross-turn shadow → it shapes a later answer. This is exactly
the *"not-yet-an-answer-now-becomes-one-later"* property.

## The payoff content (my blind read of CONV_CITY t5–t8)

Early-seeded, non-obvious frames travelled and resurfaced in *different* later
questions:

- **t5 "hoe vergroenen we de openbare ruimte?"** — baseline = generic greening
  plan; SSL weaves in the earlier-born *historische gelaagdheid* (greening tied to
  the city's history) and *informele netwerken* (bottom-up initiatives). Richer,
  more distinctive. **SSL better.**
- **t6 (veilig/levendig in de avond)** — SSL carries history + informal networks +
  climate-adaptation; apt and coherent (mild overstuffing risk). **SSL better.**
- **t7 (financiering)** — SSL ties funding to climate budgets, heritage subsidies
  and PPP via the carried frames; more concrete than the baseline's generic
  subsidy list. **SSL better.**
- **t8 (wat gaat het vaakst mis?)** — SSL builds the failure modes *out of the
  accumulated constellation* (losing historical identity; suppressing informal
  networks; ignoring climate adaptation); baseline gives generic project pitfalls.
  Distinctive, though self-referential. **SSL better / tie.**

So on the turns I can read, the carried shadow genuinely adds non-obvious,
on-topic depth the history-equipped baseline does not raise. First time SSL's own
mechanism shows value.

## Honest qualifiers (these bound the claim hard)

1. **It needed below-doctrine thresholds.** Promotion only fired with dedup 0.6
   (vs 0.85) and min_occ 2 (vs 3) — per-run knobs, global defaults untouched. So
   the honest statement is: *SSL's cross-turn value is real WHEN the
   recurrence/dedup model lets paraphrastic gaps accumulate.* At doctrine defaults
   it does not fire (round 018). The recurrence/dedup model needs real work (e.g.
   cluster-based recurrence) to be both safe (round 014) and able to promote.
2. **Length.** SSL answers are longer. This is *not automatically* a confound in
   this niche: the goal here is a richer, more complete answer, so extra length
   that adds genuinely relevant non-obvious angles is an improvement, not padding.
   The review judges whether the added content is *valuable* (not whether it is
   longer); "richer" still needs a blind human, my read is AI judgment.
3. **Author-chosen recurring-theme conversations.** Topics were picked so a gap
   *could* recur; that's fair (you can't observe recurrence without it) but it is
   not "in the wild".
4. n = 10 events, one model, one session. **Encouraging signal, not validation.**

## Next

1. **Blind human review** of the 10 cross-turn pairs (round-013 tooling) — the
   decisive check that "richer" is real and not length/AI bias.
2. **Fix the recurrence/dedup model** so promotion can fire at *safe* thresholds
   (cluster-based recurrence rather than pairwise 0.85), reconciling round-014
   safety with round-019 promotion.
3. Then re-run at the fixed defaults to see if the payoff survives without the
   exploratory knobs.
