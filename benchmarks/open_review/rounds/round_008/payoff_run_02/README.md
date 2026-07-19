# Round 008 payoff run 02 — no-harm seed injection

> **Status: hypothesis confirmed, with caveats.** Same run-01 baselines and the
> same promoted seeds; the only change is the **injection strategy**: a
> deterministic "do no harm" append (`ssl_append_answer`) instead of run-01's
> free rewrite. Blind reader judgment (`reviewer_ai_claude`), scored with
> `scripts/answer_pair_winrate.py`. No model call (the merge is deterministic).

## The number, vs run 01

| run | injection strategy | SSL win rate |
|---|---|---:|
| 01 | free rewrite (`build_ssl_revision_prompt`) | 0.333 (1/3) |
| **02** | **no-harm append (`ssl_append_answer`)** | **1.0 (3/3)** |

Same questions, same baselines, same validated seeds. Flipping the *use* of the
seeds from "let the model rewrite the whole answer" to "keep the answer and
append the validated points" turned 2 losses into wins and kept the win.

## What this confirms

The maintainer's point: seeds are *potential, not a must* — acting on them
should only ever add, never overwrite a good answer (the weightless-seed / Gate
philosophy). Run 01's losses were not the seeds; they were the **rewrite step
derailing** (hallucinated poem, wrong product). When the use-step is
constrained to do no harm, the same validated seeds add genuinely relevant
missing substance every time:

- **MODEL_A**: + colonial capital & cheap colonial raw materials (real IR
  causes the baseline omitted);
- **MODEL_B**: + applicable law for a cross-border contract & enforceability
  vs a non-EU retailer (the core legal gaps);
- **MODEL_C**: + GDPR compliance, encryption, rate-limiting for medical
  heart-rate data (the security/privacy dimension the baseline ignored).

This extends the Gate from *which seeds become active* to *how acting on them
affects the answer* — exactly the missing "do no harm" property run 01 exposed.

## Honest caveats (this is a floor, not a ceiling)

1. **Superset by construction.** The append is `baseline ∪ validated-seeds`, so
   on a completeness rubric it can almost never lose. 3/3 is therefore close to
   the *expected* result, not a surprise — it proves the seeds are relevant and
   safe to inject, **not** that they are integrated elegantly.
2. **Length control is empty.** The append is always longer, so
   `ssl_win_rate_length_neutral` is undefined here. The win is "more complete
   content", not "better at equal length"; a verbosity-penalising reader could
   judge differently.
3. **n=3, single AI judge, deterministic merge.** A signal, not proof.

## The real target now

Run 01 = free rewrite: elegant integration but derails (ceiling, unsafe).
Run 02 = append: safe but bolted-on (floor, inelegant). The goal is the
combination: a revision that **does no harm AND integrates fluently** — e.g. a
constrained rewrite on a stronger model, gated by an automatic "is the revised
answer at least as good as the baseline?" check that falls back to the append
(or the baseline) when it isn't. The append is now the working safety net for
that gate.

## Files

```text
model_benefit_append.json   # baseline vs no-harm-append pairs + blind verdicts
winrate.json                # scorer output (ssl_win_rate 1.0)
```
