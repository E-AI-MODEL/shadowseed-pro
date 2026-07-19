# Milestone — open-set evidence arc (rounds 004–007) and the strategic pivot

> Status: synthesis, 2026-06-13. Consolidates rounds 004–007 and sets the
> direction. Reads with `docs/research/current-status.md` and the 4.6 evidence
> model (`docs/00_shadow_seed_learning_4_6.md`).

## What the arc established

| round | detector | source | reviewer | acceptance |
|---|---|---|---|---:|
| 004 | Qwen2.5-3B v0.3d | ag_news | human (2) | 0.52 |
| 005 offset-12 | Qwen2.5-3B v0.3e | ag_news | **human (2)** | **0.29** |
| 005 offset-0 + control | Qwen2.5-3B | ag_news | delegated AI | 0.185 / Δ+0.219 |
| 006 b1 | Phi-3.5-mini v0.3e | ag_news | delegated AI | 0.50 |
| 006 b2 | Phi-3.5-mini | arXiv | delegated AI | 0.458 |
| 007 A | Phi-3.5-mini v0.3g | ag_news off30 | delegated AI | 0.333 |
| 007 B | Phi-3.5-mini v0.3g | arXiv off20 | delegated AI | 0.268 |
| 006 b1 | — | ag_news | **human anchor** | **0.593** (κ 0.63 vs AI) |

### Four things are now answered

1. **The mechanical core works** (Layers A/B strong) and is reproducible.
2. **A capable model detects human-acceptable gaps.** With Phi-3.5-mini the
   human-accepted rate on news is **0.593** — essentially at the ≥0.60 target.
   The round-005 "quality warning" (0.29) was largely a weak-model artifact.
3. **The evaluation methodology is itself validated.** Human-vs-AI κ = 0.63
   (substantial) means delegated AI review is a usable, measured proxy — so the
   cheaper AI-reviewed numbers can be trusted within that reliability.
4. **Form is solved** (v0.3g): prescreen `claim_vs_gap`/`truncated` ≈ 0 on both
   domains.

### Two negative results (honest, load-bearing)

- **Acceptance is not explained by text density.** A 5-proxy check over 48
  items gives |r| < 0.25 (`scripts/analyze_acceptance_vs_density.py`). The
  round-007 out-of-sample drop is real but its driver is unidentified.
- **False-gap precision cannot be filtered mechanically.** A token-grounding
  heuristic flags 0 of the human's named false-gaps. Telling "the answer is
  already in the text" apart from a real gap is irreducibly semantic — it needs
  a model/human reader, which is exactly why `02_atomic_seeds` makes
  specificity/relevance review criteria, not generation rules.

## The strategic read

Shadow Seed Learning is **not a hopeless mission**: foundations are solid,
detection reaches near-human quality on a decent model, and the discipline
makes the accumulated evidence trustworthy (the project retracts its own
overclaims — density, reviewer-leniency framing).

But the easy wins are done. The question *"can the system detect and validate
small gaps?"* is largely answered **yes**. The question that now decides the
project's worth is different and still open:

> **Does acting on validated seeds measurably improve the model's output?**

Everything so far measures the *supply* of seeds. The 4.6 vision — "gaps as
fuel for navigation" — pays off only if the *use* of validated seeds makes
answers better, end to end, over turns. That payoff is at "first evidence"
(Layers D/E) and has never been shown at the answer level with a reader. It is
the make-or-break, and it is the right next focus — not more detector tuning,
whose remaining gains are semantic and subject to diminishing returns.

## Direction

1. **Stop detector iteration** at v0.3g (form solved; precision is a
   review/Gate function, confirmed by two failed mechanical levers).
2. **Pivot to the payoff test** (round 008): baseline answer vs SSL-guided
   answer, blind reader judgment, win-rate metric — the first end-to-end
   measurement of whether seeds help. Plan: `round_008/README.md`.
3. **Keep the human-anchor loop**: the κ-validated AI judge + occasional human
   batches is now a trustworthy, cheap evaluation spine for that test.
