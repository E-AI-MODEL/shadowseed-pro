# Round 007 batch B — arXiv abstracts offset 20 (Phi v0.3g, first v0.3g run)

> **Status: AI review complete.** Detector run is real (Actions run
> [27438927839](https://github.com/E-AI-MODEL/shadowseed/actions/runs/27438927839)).
> That run's summary commit lost the push race against the parallel batch-A run
> (fixed separately with `git rebase --autostash`); the model output itself
> succeeded and is committed here **verbatim** from the maintainer-uploaded
> Actions artifact. Review is **delegated AI** (`reviewer_ai_claude`, single
> reviewer) — labeled AI, not human.

## Run provenance

- **Model:** `hf-transformers:microsoft/Phi-3.5-mini-instruct`, **prompt v0.3g**
  (first live run of the gap-label-noun-phrase rule), `max_new_tokens=512`.
- **Input:** `arxiv_abstracts` offset **20**, 12 abstracts — fresh items, no
  overlap with round 006 batch 2 (offset 0). Mostly condensed-matter /
  high-energy physics.

## v0.3g did exactly what it was meant to

- **Prescreen clean-rate 0.95** (was 0.0 on the same domain under v0.3e):
  `claim_vs_gap` **0**, `truncated` **0**, only 3 `not_atomic`. The candidates
  are now crisp noun-phrase gap labels ("Transition probabilities van de
  emissie van Goldstone bosonen uit een quark"), not absence-scaffold spam.
- Manager atomicity gate rejected 4 of 60 raw; the prescreen `not_atomic`
  overlaps it. Form is no longer the problem.

## AI review result (genre rubric, same as round 006 batch 2)

- unique seeds **56** · accepted **15** · acceptance **0.268**
- criterion pass rates: atomicity 1.00, relevance 0.36, testability 0.43,
  non_triviality 0.27, follow_up_utility 0.27
- reject codes: **`style_not_gap` 28**, `not_relevant` 8, `too_vague` 4,
  `trivial` 1

## The finding: acceptance drops out of sample; the cause is NOT confirmed

| arXiv batch | offset | acceptance | dominant reject |
|---|---|---|---|
| round 006 batch 2 | 0 | 0.458 | mixed |
| round 007 batch B | 20 | **0.268** | `style_not_gap` 28 |

The drop is **marginal** (pooled two-proportion z ≈ 2.0 SE on 22/48 vs 15/56,
and that is per-seed — weaker once clustered by the 12 items). 28/56
candidates were rejected `style_not_gap` because they restate a finding the
abstract already gives — a stated finding is not a gap.

Reading the items suggested a "results-dense text leaves fewer gaps" (text
density) story. **That explanation was tested and failed:**
`scripts/analyze_acceptance_vs_density.py` finds |r| < 0.25 between per-item
acceptance and five deterministic surface proxies across all 48 round-006/007
items, with the batch ordering non-monotone in each. So the per-item driver is
**unidentified**; do not read this batch as evidence that "density" explains
the drop. See the round-level synthesis in `../README.md`.

### New failure mode worth flagging

Item ARXIV_21 (stochastic Lie group integrators) produced three **fabricated
applications** — "autonoom onderwatervoertuig", "bevroren rigide object",
"twee onafhankelijke stochastische laagnoiseprocessen" — none in the abstract.
That violates the generation rule "no fabricated facts" (`02_atomic_seeds` §2)
and is a content-grounding gap the prescreen cannot catch (it is not a form
error). Candidate for a future grounding check, not a prompt value-rule.

### Translation strain on jargon

Recurrent garbled Dutch on technical terms ("wavelheggen" for wavelengths,
"golf" for phonon, "luchtingsfactor" for filling factor). Did not by itself
drive rejections but is a quality drag; a larger or English-output model would
likely reduce it.

## What this does NOT claim

Delegated AI review, single reviewer, one 12-item batch: a signal, not Layer-F
validation; ≥ 0.60 not met; no total score. The genre rubric (accept
claimed-but-unstated specifics; reject restatements of stated findings) is the
same one documented for round 006 batch 2.

## Artifacts

```text
input/hf_batch.json                  # verbatim run input (12 abstracts)
open_set_seed_output.json            # verbatim run output (60 raw candidates)
run_review_packets_pending.json      # the run's untouched two-reviewer packets
mechanical_prescreen.json / .md      # deterministic triage on the raw 60
ai_review/open_set_review_packets.json       # 56 judged packets, reviewer_ai_claude
ai_review/open_set_seed_review_summary.json  # canonical summary route output
ai_review/open_set_review_report.md          # human-readable summary
ai_review/open_set_disagreements.json        # empty (single reviewer)
```
