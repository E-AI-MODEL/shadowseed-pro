# Round 019 — human review results (cross-turn payoff)

> **Status: the cross-turn payoff is human-anchored.** Two independent reviewers
> blind-scored the 10 cross-turn pairs; agreement with the AI blind verdicts was
> **92% and 98%** (maintainer-reported, 2026-06-21).

## Outcome

| measure | value |
|---|---:|
| independent reviewers | 2 |
| cross-turn pairs | 10 (real SSL pipeline, gpt-4.1) |
| AI blind verdict | 8 ssl-better / 2 tie |
| **reviewer 1 agreement with AI** | **92%** |
| **reviewer 2 agreement with AI** | **98%** |

Both reviewers, independently and blind, largely confirm the AI judgment that the
**cross-turn SSL answers are richer/more useful** than the baseline (same
conversation history, no shadow memory). This removes the two biggest worries
about the round-019 read:

- **not AI bias** — independent humans agree at 92–98%;
- **not a length artefact** — reviewers were explicitly told that, in this niche,
  a longer answer that adds genuinely relevant non-obvious angles is *better*, and
  to penalise only padding/repetition/forced additions.

Combined with round 013 (4 reviewers, unanimous, matching the AI 10/10), the AI
judge is now a **twice-validated faithful proxy**, and SSL's own cross-turn
mechanism shows a human-anchored positive.

## What this does and does not establish

- **Does:** through the *real* `SSLManager` pipeline, an early-born weight-0
  shadow that recurs, promotes via the Gate and resurfaces makes a later answer
  richer — and independent humans agree. The vision's "not-yet-an-answer-now-
  becomes-one-later" property pays off and is human-confirmed on this set.
- **Does not (unchanged):** it still required **below-doctrine thresholds**
  (dedup 0.6, min_occ 2) to let promotion fire; n=10; one model; conversation
  topics chosen so a theme *could* recur. So: a **human-anchored positive
  signal**, not yet a general validation. Next: make promotion fire at *safe*
  thresholds (W9e) and widen scope.

## Exact win-rate / κ
Agreement was reported in conversation (92% / 98%). If the per-item A/B/tie
choices are handed back, the exact human SSL-win-rate and Cohen's κ can be
computed with `scripts/human_review_control.py`-style scoring against
`answer_key.json`.
