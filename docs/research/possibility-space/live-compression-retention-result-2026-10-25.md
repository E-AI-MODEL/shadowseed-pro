# Actual live GPT-5 compression-retention pilot — result (2026-10-25)

> **Verdict:** TECHNICALLY COMPLETE; RESEARCH RESULT NON-DISCRIMINATING. This is NOT evidence of a unique Shadowseed effect and NOT evidence for either clause of the original [possibility-space thesis](../possibility-space-thesis.md). The initial pilot attempt stopped during offline validation before any model call. The corrected run completed.
>
> **Ground truth:** [GitHub Actions run #40145161574](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40145161574), exact research revision 3f470a093508c74b1a9a84a8d313b0d603991fb2, artifact ID 12580790591. Full raw fictional model outputs are in the archived GitHub Actions artifact, NOT selectively transcribed into this report.

## Execution and reproducibility

| Recorded fact | Actual result |
| --- | --- |
| Model reported by provider | gpt-5-2025-08-07 |
| Embedding backend | text-embedding-3-small (actual provider requests, NOT a lexical fixture) |
| Cases | 3 author-written fictional scenarios, including 1 negative |
| Model calls | **30 completed / 30 attempted**, all produced parseable JSON |
| Embedding requests | **3** |
| Model input tokens | 14,160 |
| Model output tokens, including reasoning | 20,314 |
| Embedding tokens | 787 |
| **Total** | **35,261** recorded tokens |
| T0 freeze | 3 first responses, 3 two-candidate sets, 3 normal-note sets, 3 model-made summaries, all valid; saved before first T2 call |
| T2 | 18 complete follow-ups (6 arms x 3 cases), all supplied a next question |
| Shadowseed intake | 5 candidates accepted, 1 rejected as not atomic |
| Gate / authority | **0 Gate events; all accepted candidates remained weightless** |
| Provider errors | 0; no retries |
| Raw artifact integrity | result.json SHA-256: 8fd9dde61290dfe1c68bdd48be15bc181379b6bcd661faf93499e8864f3d0faa; frozen-t0.json SHA-256: 19404f4818dc3f7f4f568297a7edc7b633d2814f2988f2ba14b63aff175203ef |

This comparison is **not** equal-budget in tokens, number of model calls, information volume, or initial candidate/normal-note selection cost; it must not be treated as a causal effect estimate.

## What the raw records show, case by case

### Measurement drift: initial answer already selected the relevant direction

The original GPT-5 answer proposed electrical interference/voltage drop through the shared power supply. Its **own compressed summary preserved that explanation**. The eventual evidence (sensor swap ineffective, isolated power removes the problem) therefore did not force a recovery from lost context.

The separate T0 Shadowseed hypothesis generator created a different first candidate, temperature-dependent sensor bias **rather than power problems**, and a second candidate about datalogger firmware. The real embedding query at T2 retrieved the **less useful temperature-bias candidate** (cosine 0.396); the standard-note arm retrieved a note on rotating sensors (0.503). Despite the retrieved distractions, all six follow-up arms prioritized power/ground interference and proposed related measurements. Ablating the first candidate did not eliminate that direction.

**Interpretation:** useful model reasoning with and without candidate memory; no demonstrated Shadowseed advantage. The vector hit illustrates that semantic proximity is not the same as evidence or relevance.

### Registration decline: same explanation survived ordinary compression

The original answer already suspected a September deduplication/export counting artifact rather than a genuine participation decline. The compressed summary preserved the same idea. The ordinary-note generator independently wrote down the deduplication hypothesis, including lost multi-activity entries. The Shadowseed generator also named export truncation and merge-key filtering.

After the new 40-form confirmation check, all six arms explained the likely loss of secondary activity choices and proposed independent comparison against raw confirmations and re-exports. The normal-note arm, the compressed-only arm and the ablated arm all reached this conclusion. Removing the first candidate did not remove the later inquiry.

**Interpretation:** ordinary model generation and notes matched the relevant Shadowseed direction. No incremental contribution was isolated.

### Unrelated lunch question: useful negative behavior

The later question deliberately switched from warehouse operations to a vegetarian staff lunch. The real retrieval threshold yielded **no recalled notes or candidates** in any memory arm. All six answers stayed on lunch options, with zero matches against the predeclared warehouse-intrusion markers. One of the two original candidate texts had failed the canonical atomicity check and was excluded from Shadowseed memory.

**Interpretation:** no inappropriate carryover in this ONE synthetic negative case. Do not extrapolate false-positive safety from one example.

## What we can say

- A real GPT-5 produced candidate records and ordinary notes before seeing the fictional later events; a separate, model-produced compression was saved; real OpenAI embeddings subsequently retrieved weightless seeds through existing Shadowseed modules.
- Original seed provenance and authority boundaries held: neither similarity nor reappearance granted weight or passed the Validation Gate.
- The normal model/summary/notes already retained the relevant interpretations in both informative cases. The data therefore show **no distinctive retention benefit** of Shadowseed.
- All 18 final responses contained proposed next questions; most converged on similar checks. They were not independently rated for novelty, usefulness, or causal dependence on a seed.

## What this does NOT show

- No controlled context-window overflow or demonstrated loss of the relevant candidate under ordinary compression. The compressed summaries retained the answer before the later evidence was supplied.
- No independent blinded reviewers, post-preregistration holdouts, random sample, uncertainty interval, or claim about model-internal awareness of 'nonchosen' possibilities.
- No experimental separation of anchored model behavior from normal strong-model reasoning. The author-crafted initial cases evidently provided enough clues for GPT-5 to select the relevant hypothesis early.
- No proof that retaining a candidate changed what could *later* be meaningfully investigated. A different next question phrased by an LLM alone would not prove the second clause of the thesis.
- No causal evidence from the ablation: the supplied future observation itself was sufficient for all arms, and deleting one hypothesis simply left another ordinary explanation available.

## Decision before another paid trial

**STOP the current pilot. Do not rerun these same examples or adjust thresholds until a win appears.**

The follow-up research need is methodological, not another API call: independently authored harder cases with an *observably lost* early hypothesis, locked before the future cue, genuinely constrained compression across longer sessions, strong same-model ordinary notes with the **same** semantic retrieval and total budget, falsifying negatives, and independent blinded judgment about changed later investigability. The full two-part thesis remains untouched. The independent [G0 review form](g0/dynamic-inquiry-independent-review.md) is still **UNFILLED**. The engineering result cannot fill it automatically.

## Files

- [Raw freeze + final result, GitHub run artifact](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40145161574) (artifact ID 12580790591)
- [Precommitted study limitations](live-compression-retention-engineering-pilot-2026-10-25.md)
- [Frozen synthetic cases](../../../research/fixtures/live_compression_exploratory_v0.json)
- [Code](../../../research/src/shadowseed_research/benchmark/live_compression_retention.py)
- [Offline tests](../../../research/tests/test_live_compression_retention.py)

**Evidence boundary:** this is a descriptive examination of one completed engineered trial, not a general efficacy evaluation of Shadowseed or a rejection of the original philosophical/scientific question.
