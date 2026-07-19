# SLM open evaluation — design

Status: design
Date: 2026-05-22
Evidence layer relevance: Layer C (open-set seedkwaliteit), Layer E (probe utility)
Resolves: #56

## Purpose

The existing `slm-model-benefit` workflow runs a real Hugging Face backed
model-benefit suite but it still produces companion fixture outputs from the
fixed gap, false-positive and benefit suites before analysis. As a result the
public SLM route can lean on stable, known scenario files. Those are useful
for regression checks but weak for measuring whether SSL actually helps a
small language model on unfamiliar prompts.

This document specifies how to extend the SLM lane with an **open-evaluation**
mode whose main comparison does not depend on the fixed scenario suites and
does not pretend that a `coverage_delta` on three curated scenarios is
evidence of general SSL effectiveness.

## Out of scope for this design

- changing the standard CI
- changing `publish-test-results.yml` or non-SLM publication routes
- changing analyzer behavior
- changing public claim strength
- combining this with unrelated workflow cleanup

The fixed suites stay. They are explicitly labelled as **regression and
smoke support**, not as the main SLM effectiveness claim.

## Core comparison

The SLM open-evaluation route compares **the same model on the same prompt
in two modes**:

- `baseline`: no SSL seeds in context, no SSL-guided revision step
- `ssl_assisted`: SSL detection runs first; promoted seeds are passed back
  to the model as a revision instruction

Fresh prompts come from a rotating source so the comparison is not on
prompts the system has seen during regression development.

## Prompt sources

The route accepts prompts from one of these modes, configured per run:

1. **rotating HF dataset slice**: pinned `dataset / split / revision / offset / limit`
   so the slice is reproducible per run window but not the same across runs.
   Default first mode. Uses the same `open_set_hf_sources.json` registry
   already used by round 003.
2. **committed run-window file**: `benchmarks/slm_open_eval/window/YYYY-Wxx.json`
   with explicit prompts. Useful for replaying an exact window.
3. **generated prompt batch saved as a run artifact before evaluation**:
   the workflow generates prompts (e.g. by paraphrasing seed topics) and
   commits the generated batch alongside the evaluation result.

Mode 1 is the primary route. Modes 2 and 3 are for reproducing an interesting
finding or for adversarial follow-up.

## Comparison schema

Per item the route records:

```
{
  "item_id": str,
  "source": { "dataset": str, "split": str, "revision": str, "offset": int },
  "prompt": str,
  "baseline_answer": str,
  "ssl_seeds_promoted": [ {"seed_id", "text", "weight"} ],
  "ssl_assisted_answer": str,
  "answer_length_baseline_words": int,
  "answer_length_ssl_words": int,
  "blind_review_pair_id": str,
  "blind_review_order": "baseline_first" | "ssl_first"
}
```

The `blind_review_pair_id` and `blind_review_order` exist so a human judge
can score the answer pair without knowing which side used SSL.

## Outputs

Three artifact files per run, with explicit names and evidence-layer labels:

| Path | Contents | Status label |
|---|---|---|
| `results/slm_open_eval/<run-id>/raw_answers.json` | the comparison schema above, one row per item | `evidence_layer: slm_open_evaluation_raw` |
| `results/slm_open_eval/<run-id>/blind_review_packets.json` | blinded pairs for human review, one per item | `evidence_layer: slm_open_evaluation_blind_pairs` |
| `results/slm_open_eval/<run-id>/judge_summary.json` | only created after human review is filled in; counts SSL-wins / baseline-wins / ties + reject reasons | `evidence_layer: slm_open_evaluation_judged` |

The judge summary is the **only** artifact that may inform a public claim
about SSL helping the SLM. Until it exists the run is `pending_review`.

## Human review boundary

Blind review packets follow the same pattern as the open-set round packets:

- two reviewer slots (`reviewer_a`, `reviewer_b`)
- per row: pick `ssl_wins` / `baseline_wins` / `tie` / `both_bad`
- five booleans on the SSL-assisted answer:
  `addresses_a_real_gap`, `text_grounded`, `no_unsupported_claims`,
  `style_acceptable`, `would_use_in_practice`
- short note

Reject codes for `both_bad`:
- `both_off_topic`
- `both_unsupported`
- `prompt_unanswerable`
- `prompt_ambiguous`

The fixed suites are not reviewed here. They keep their own contracts.

## Workflow integration

A new workflow `.github/workflows/slm-open-eval.yml` (separate from the
existing `slm-model-benefit`) with `workflow_dispatch` inputs:

- `prompt_source_mode`: `rotating_hf_slice` (default) | `committed_window` | `generated_batch`
- `prompt_source_id`: HF source id from `open_set_hf_sources.json`, or a
  filename for the other modes
- `limit`: number of prompts (default 8 for a manageable review batch)
- `offset`: for `rotating_hf_slice`
- `model_id`: HF model-id (see #81 for the ladder)
- `max_new_tokens`: per side (default 400)

Backwards compatibility: the existing `slm-model-benefit` workflow is **not
modified** by this design. It continues to run the fixture-suite-companion
comparison for regression purposes.

## Claim discipline

After a run with a filled-in judge summary the **allowed** claim is:

> Op een blind beoordeelde batch van N prompts met model M wint SSL-assistentie
> in X% van de gevallen, gelijk in Y%, baseline in Z%, met de bekende limieten
> van een kleine review-ronde en één modelkeuze.

**Not allowed**:

> SSL bewijst dat SLM's beter werken met SSL.

This separation must be visible in the analyzer output and the public report
text. The judge summary populates a dedicated section in the analyzer report
that is distinct from the fixture-benefit numbers.

## Failure modes the design must handle

| Failure mode | Mitigation |
|---|---|
| Same prompts appear in regression suites | Refuse `prompt_source_id` whose items overlap with curated fixtures (a small overlap check at intake) |
| Model hallucinates SSL seeds into the answer | `unsupported_ssl_addition_rate` continues to be computed alongside; non-zero rate flags the run |
| Reviewers see which side used SSL | Blind ordering uses a deterministic checksum of `item_id` (same pattern as the existing blind benchmark) |
| Small N makes results look more convincing than they are | Public report must include N and uncertainty caveats; analyzer adds a `confidence: small_sample` flag when N < 20 |
| One model run gets cherry-picked | Run-id (timestamp + model_id + slice ref) is part of the path; old runs are not overwritten |

## Implementation order

This design ships in one PR (this one). The implementation is split into
follow-up PRs in this order:

1. `src/shadowseed/benchmark/slm_open_eval.py` — the comparison engine, prompt
   source loader (HF rotating slice first), and the comparison-schema writer
2. CLI command `run-slm-open-eval` wired through `cli_dispatch.py`
3. Blind review packet generator (mirrors the existing open-set seed review
   packet generator)
4. Judge summary CLI (`summarize-slm-open-eval`)
5. Workflow `slm-open-eval.yml`
6. Analyzer hook for the judge summary

Each step lands separately so a regression in one does not block the others.

## What "done" looks like for #56

This issue is done when:

- the route goal is reframed from fixture validation to open evaluation
- the fixed suites are explicitly labelled as regression/smoke support (this
  document is the labelling; the existing suite docstrings already say so for
  the benefit-suite, the SLM workflow README will inherit this label after
  the implementation lands)
- the fresh-input evaluation design is documented (this document)
- artifact names and review boundaries are specified (Outputs + Human review
  boundary sections above)
- a later implementation PR can add a new SLM open-evaluation workflow or
  mode safely (Workflow integration section above is implementable as written)

The implementation PRs (1-6 above) are separate and tracked under follow-up
issues created off this one.
