# Round 017 — W9: SSL through the REAL pipeline (multi-turn), first run

> **Status: the faithful pipeline ran clean; 0 cross-turn events — and the
> diagnostic explains exactly why.** This is the corrected test (after the
> standalone wild/generative/adversarial derivatives were flagged as
> NIET-PIJPLIJN): a multi-turn conversation driven through the actual
> `SSLManager` (weight-0 seeding, recurrence dedup, Validation Gate across turns,
> TTL decay, TrTL reactivation, constellations). Provenance: run 27897562262,
> job 82551821845, `openai:gpt-4.1`, openai embeddings.

## The numbers

| diagnostic | value |
|---|---:|
| conversations | 2 (4 turns each) |
| gaps detected (total) | 40 |
| **max occurrence_count any seed reached** | **2** |
| **seeds ever promoted** | **0** |
| cross_turn_payoff_events | 0 |

## Why 0 — mechanism, not bug

The Validation Gate requires **recurrence ≥ 3** (`min_occurrences_for_gate`) for
internal recognition, then ~3 validated passes for `weight ≥ 0.5` (PROMOTED). In
a 4-turn *evolving* conversation no single gap recurred more than **twice**, so
nothing cleared even the recognition bar — let alone promotion. With nothing
promoted, no weight-0 shadow could earn the right to shape a later answer. The
pipeline behaved exactly as designed; the conversations were simply too short and
too topically-shifting for the recurrence mechanism to fire.

## The real tension this exposes (honest)

This is the genuine design tension, surfaced cleanly:

- Round 014 + the lifecycle work **validated the Gate's strictness** as SSL's
  safety layer (bad seeds must not promote/persist).
- But that same strictness means a seed needs to **recur 3× and validate 3×** to
  promote — which a short conversation rarely delivers. So the cross-turn payoff
  (gap 5) cannot even be observed in 4 shifting turns: the mechanism is correct
  but never gets to act.

There are only two honest ways forward, and they trade off:

1. **Give recurrence a fair chance**: longer conversations (8–12 turns) and/or a
   conversation that genuinely *returns* to a theme, so a real gap recurs 3×+ and
   promotes on its own merit. (Not rigging — a 4-turn shifting fixture
   structurally cannot produce 3× recurrence.)
2. **Lower the promotion bar** — but that re-opens exactly the noise door round
   014 warned about. Only acceptable with the lifecycle TTL/EXPIRED as the
   backstop, and it changes the doctrine.

Option 1 is the faithful next test; option 2 is a doctrine decision.

## What this does and does not say

- It does **not** say SSL's cross-turn mechanism fails — it was never given a
  conversation in which a gap could recur enough to promote.
- It **does** say: in short evolving conversations, the recurrence-gated pipeline
  produces no promoted shadow, so there is nothing to carry. The payoff question
  (gap 5) remains genuinely open, pending longer/recurring-theme conversations.

## Next (W9b)

Longer conversations (≥8 turns) and/or deliberately theme-returning dialogues, so
the recurrence Gate can fire on a genuinely recurring gap; then measure whether a
self-promoted shadow surfaces value at a later turn the history-equipped baseline
misses.
