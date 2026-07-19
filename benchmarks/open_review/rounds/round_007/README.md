# Open-set round 007 — out-of-sample replication under prompt v0.3g

> **Status: complete — both batches run, verbatim artifacts, AI-reviewed.**
> Both ran `microsoft/Phi-3.5-mini-instruct` with the **v0.3g** prompt on fresh
> out-of-sample items. Three findings, in order of confidence:
>
> 1. **v0.3g fixes form everywhere** — prescreen clean-rate 0.90 (news) / 0.95
>    (science), `claim_vs_gap` 0, `truncated` 0 on both. Solid.
> 2. **The model lever holds out of sample** — news 0.333, science 0.268, both
>    well above round 005's Qwen baseline (0.185). Phi >> Qwen replicates.
> 3. **Round 006's absolute levels (0.50 / 0.458) were optimistic, and the
>    news/science framing was wrong.** Out of sample both drop to ~0.30
>    (news offset 30 = 0.333 ≈ science offset 20 = 0.268), so the split is not
>    domain. An initial "text density" explanation did **not** survive a proxy
>    check (see below); the driver of the drop is currently unidentified.

## The five-point picture (delegated AI review, one reviewer, one rubric)

| round | detector | source | offset | acceptance |
|---|---|---|---|---:|
| 005 (AI arm) | Qwen2.5-3B | ag_news | 0 | 0.185 |
| 006 batch 1 | Phi-3.5-mini | ag_news | 0 | 0.50 |
| 006 batch 2 | Phi-3.5-mini | arXiv | 0 | 0.458 |
| **007 batch A** | Phi-3.5-mini | ag_news | 30 | **0.333** |
| **007 batch B** | Phi-3.5-mini | arXiv | 20 | **0.268** |

**What drives the drop is not yet identified.** Reading the items suggested a
"text density" story — fact-complete wire items (Indians-beat-Twins box scores)
and results-dense physics abstracts (stated Hopf bifurcations, stated kondo
peaks) leave few genuine gaps. That reading is intuitive but **does not survive
a check**: `scripts/analyze_acceptance_vs_density.py` correlates per-item
acceptance against five deterministic surface proxies (length, number density,
proper-noun density, type-token ratio, words/sentence) over all 48 reviewed
items and finds **|r| < 0.25 for every one**, with the batch ordering
non-monotone in each (007_A has the highest proper-noun density yet low
acceptance). So:

> The same-domain out-of-sample drops are **marginal, not decisive**: pooled
> two-proportion z is ~1.8 SE (news, 29/58 → 18/54) and ~2.0 SE (arXiv,
> 22/48 → 15/56), and that is per-seed — treating seeds as independent when
> they cluster by item (n=12), so the real evidence is weaker still.
> "Density" as measured by simple surface features does **not** explain the
> drop. The driver is unidentified; candidates that this n=48,
> single-reviewer setup cannot separate include sub-domain difficulty, item
> selection, and reviewer variance.

Round 006 was right to flag *single-batch noise*; out-of-sample replication
shows the caveat mattered. The honest implication for round 008 is **not** a
density-stratified intake (the proxy that would drive it doesn't work) but
**reducing measurement variance**: a second independent reviewer (or a human
anchor) on the existing complete batches, and larger n, before more detector
iteration.

### Rubric-sensitivity bound (`scripts/analyze_rubric_sensitivity.py`)

Re-aggregating the same AI verdicts under one deliberately stricter,
deterministic rule (demote accepts that are generic detail / impact /
speculation asks) shows the acceptance numbers are **rubric-fragile**, and
asymmetrically so:

| batch | AI acceptance | strict | swing |
|---|---:|---:|---:|
| 006_b1 (news off0) | 0.500 | **0.328** | −0.172 |
| 006_b2 (sci off0) | 0.458 | 0.396 | −0.062 |
| 007_A (news off30) | 0.333 | 0.278 | −0.055 |
| 007_B (sci off20) | 0.268 | 0.250 | −0.018 |

The **0.50 headline batch swings the most** and collapses toward the
out-of-sample numbers; the strict rule compresses the cross-batch spread from
0.232 to 0.146. This is a self-consistency bound (same agent, alternative
rule), not independent review.

**Update — the human pass arbitrated, and it landed on the lenient side.**
The blind maintainer review of batch 1 (`round_006/batch1/human_review/`) gives
human acceptance **0.593 ≥ AI 0.519**, κ = 0.63 (substantial). So the strict
rule (0.328) is the *pessimistic* bracket, not the truth: the in-sample
headline is **not** inflated by AI leniency — a real human is slightly more
generous. The residual human-vs-AI disagreement is concentrated on the
impact/speculation boundary, the softest part of the rubric. The
rubric-sensitivity table below therefore bounds how low a stricter reading
could push acceptance; the human anchor bounds the realistic high end.

## Why this round

Round 006 established two signals with one batch each: the model lever works
(Layer C) and quality transfers across domains (first Layer-F point). Both
carry the explicit caveat *single-batch noise*. Round 007 attacks exactly that
caveat: same model, same (now self-consistent) prompt, fresh inputs.

Secondary: this is the first live run of prompt v0.3g, which aligned the rule
with the few-shot examples after the scaffold contradiction (see ADR 0001,
round 006 row). Expected effect on Phi is small (it already followed the
examples); the prescreen claim/truncation profile is the check.

## Design

| | Batch A (news) | Batch B (science) |
|---|---|---|
| source | `ag_news_test` | `arxiv_abstracts` |
| offset | **30** (rounds 004–006 used 0–25) | **20** (round 006 used 0–14) |
| limit | 12 | 12 |
| model | Phi-3.5-mini-instruct | Phi-3.5-mini-instruct |
| max_new_tokens | 512 | 512 |

One lever versus round 006: fresh items (plus the v0.3g form fix). No model
change, no domain change, no rubric change.

## Success criteria (replication, no total score)

- Batch A acceptance in the neighborhood of 0.50; batch B in the neighborhood
  of 0.46–0.51 — same reviewer (`reviewer_ai_claude`), same documented rubric
  including the genre reading for abstracts.
- Prescreen: `claim_vs_gap` 0 under the assertion-based check; truncation and
  "of"-stacking profiles reported per domain.
- A material drop on fresh items would mean the round 006 numbers leaned on
  item luck — that is a reportable, course-changing outcome, not a failure of
  the round.

## Review

Delegated AI review (`reviewer_ai_claude`), explicitly labeled, single
reviewer; the runs' own two-reviewer packets are preserved untouched per batch
so a human pass stays possible. AI review is a signal, not Layer-C/F evidence.

## Artifact contract

Per batch under `batchA/` / `batchB/`: same round-local contract as round 006
(`input/hf_batch.json`, `open_set_seed_output.json`,
`run_review_packets_pending.json`, `mechanical_prescreen.json/.md`,
`ai_review/*`).
