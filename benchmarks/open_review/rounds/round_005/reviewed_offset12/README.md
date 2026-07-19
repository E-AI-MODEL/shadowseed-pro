# Round 005 — reviewed batch (offset 12), first real Layer-C evidence

> **Status: completed human review (single-arm).** This is the first landed
> open-set (Layer C) human-review evidence in the repo. It is the canonical
> `summarize-open-set-seed-review` output for the offset-12 batch of the v0.3e
> Qwen2.5-3B-Instruct run.

## What this is

- **Detector:** `model` + `hf-transformers:Qwen/Qwen2.5-3B-Instruct`, prompt v0.3e.
- **Batch:** `ag_news_test` offset 12, limit 12 (Sci/Tech items).
- **Review:** two reviewers (`reviewer_a`, `reviewer_b`), single-arm (model only,
  not the blind baseline control), all packets completed.

This is the **primary** Layer-C metric source per `evaluation-matrix §3` and
remains the authoritative human evidence for the round. The **secondary**
blind model-vs-baseline control and the offset-0 batch were subsequently
closed as delegated AI review (`../ai_review/`, single reviewer, 98%
accept-agreement with this human batch); they do not change this batch.

## Results (read per layer, no total score)

- unique seeds: **41** · accepted **12** · rejected **29** → acceptance rate **0.29**
- criterion pass rates: atomicity **0.66**, relevance **0.98**, testability **0.66**,
  non_triviality **0.29**, follow_up_utility **0.29**
- reviewer agreement: unanimous (pairwise decision agreement **1.0**)
- reject reasons: `style_not_gap` 20, `not_testable` 18, `too_vague` 10,
  `duplicate` 6, `not_relevant` 2, `trivial` 2

## Interpretation notes (honest)

- **The signal is substance, not form.** Relevance is high (0.98) but
  non_triviality and follow_up_utility are low (0.29): the detector finds
  on-topic absences that are mostly trivial or low-value. This matches the
  mechanical prescreen direction and is the real open-set weakness to work on —
  v0.3e fixed *form* (claim-vs-gap 30→0 vs round 004), not *substance*.
- **Agreement is reported as unanimous.** If the two reviewers were not fully
  independent, the agreement metric overstates reliability; read it as
  "no adjudication was needed for this batch", not as proven inter-rater
  robustness.
- **Scope:** offset-12 only (12 items), single-arm. Not a paper-level claim;
  this is a first usable Layer-C data point.

## Artifacts

```text
open_set_seed_output.json          # raw v0.3e detector output (offset 12)
open_set_review_packets.json       # completed two-reviewer packets
open_set_seed_review_summary.json  # canonical summary (review_completed)
open_set_review_report.md          # human-readable summary
open_set_disagreements.json        # seed-level disagreements (none unresolved here)
input/hf_batch.json                # the offset-12 source items
```
