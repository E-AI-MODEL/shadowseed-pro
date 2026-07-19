# Open-set round 006 — substance iteration (Layer C) + first domain signal (Layer F)

> **Status: both batches executed and AI-reviewed — round complete.**
> Batch 1 (news, run 27256277709): acceptance 0.185 → **0.50** vs the round
> 005 AI pass — the model lever works. Batch 2 (arXiv abstracts, run
> 27350504602, first Layer-F data point): acceptance **0.458**, and 0.51
> excluding the one LaTeX-mangled item — **the quality transfers across
> domains**; what shifts is the failure profile ("of"-stacking upstream,
> LaTeX truncation), not the substance. Both reviews are delegated AI
> (`reviewer_ai_claude`); see `batch1/README.md` and `batch2/README.md`.

## Why this round

Round 005 offset-12 delivered the first real Layer-C evidence and it is a
quality warning, not a success:

- acceptance **0.29** (criterion was ≥ 0.60), reviewer agreement unanimous;
- relevance **0.98**, but non_triviality **0.29** and follow_up_utility **0.29**;
- reject reasons: `style_not_gap` 20, `not_testable` 18, `too_vague` 10.

Reading: v0.3e fixed the *form* (claim-vs-gap 30 → 0 versus round 004 — the
nine remaining missing-marker candidates turned out to be truncated clauses,
see the `truncated` prescreen code), but not the *substance*. The detector
finds on-topic absences that are mostly trivial, untestable or stylistic.

## Doctrine boundary (read before touching the prompt)

Per `docs/02_atomic_seeds.md` §2 and the v0.3f revert (commit 425df4a):
triviality, specificity, relevance and redundancy are **review/Gate
judgments, not generation blockades**. Adding "don't be trivial" rules to the
detection prompt pre-assigns value at birth and breaks the weightless-seed
principle — that exact mistake was already made and reverted once.

The levers this round may use are therefore:

1. **model capability** (the detector model, per the #81 ladder);
2. **round design** (domains, batch sizes, decoding budget);
3. **downstream triage** (prescreen codes, including the new `truncated`).

The v0.3e prompt itself stays **unchanged** this round, so the model effect is
isolated. One lever per comparison.

## Design: two batches, one model change

**Model arm for both batches:** one step up the #81 ladder. Preferred:
`microsoft/Phi-3.5-mini-instruct` (MIT license, in the workflow dropdown).
No special runner is needed: the public-repo `ubuntu-latest` runner has 16 GB
RAM, and the HF backends now load the checkpoint's native half precision on
CPU (~8 GB for a 3.8B model instead of ~15 GB at float32). `Qwen/Qwen3-4B`
(Apache-2.0) is the equally-sized alternative; `phi3.5` is available via the
Ollama backend (Q4-quantized). Note that Qwen2.5-3B (rounds 004/005) carries
a research-only license; moving to an MIT/Apache model also cleans that up.

### Batch 1 — substance replication (Layer C, anchored)

- Source: `ag_news_test`, Sci/Tech items, **same domain as round 005** so the
  acceptance/non-triviality delta is attributable to the model change alone.
- Baseline to beat: round 005 offset-12 (acceptance 0.29, non_triviality 0.29,
  follow_up_utility 0.29) on the same review rubric.

### Batch 2 — first domain signal (Layer F, exploratory)

- Source: **`arxiv_abstracts`** (`gfissore/arxiv-abstracts-2021`, CC0,
  registered in `open_set_hf_sources.json` v0.2) — scientific abstracts,
  maximally distant from the news priors of batches so far, with the **same**
  detector, prompt and rubric.
- **Verify before the model run** (the field mapping could not be live-checked
  from the dev environment): one cheap smoke dispatch first —
  `source_id=arxiv_abstracts, limit=2, detector=adapter_v1` (~1 min, no model
  install). If the artifact contains two abstracts with real titles, dispatch
  the model run:

```yaml
source_id: arxiv_abstracts
limit: 12
offset: 0
detector: model
model_backend: hf-transformers
model_id: microsoft/Phi-3.5-mini-instruct
max_new_tokens: 512
```

- This is the cheapest possible first Layer-F signal: it does not need new
  infrastructure, only a different input batch. It is exploratory; batch 1 is
  the anchored comparison.

## Go / no-go gate (mechanical prescreen, before any review)

```bash
python scripts/prescreen_open_set_output.py results/open_review/open_set_seed_output.json \
  --input benchmarks/open_review/rounds/round_006/input/hf_batch.json \
  --round round_006 \
  --output benchmarks/open_review/rounds/round_006/mechanical_prescreen.json
```

Reference: round 005 combined scored clean-rate 0.553 with `truncated` 9,
`parse_leak` 10, `not_atomic` 38, `near_duplicate` 13.

Proceed to human review only if:

- yield ≥ ~3 candidates/item;
- clean-rate clearly above 0.553;
- `truncated` ≈ 0 — the round-005 truncations were degenerate model lines, and
  a more capable model is expected to remove them. If they persist, diagnose
  the decoding budget (`max_new_tokens`) before spending reviewer time;
- `claim_vs_gap` stays 0 (v0.3e holds on the new model).

The prescreen is deterministic triage — not human review, not Layer-C evidence.

## Review protocol

Identical to round 005: two reviewers, all five criterion booleans, fixed
reject codes, `summarize-open-set-seed-review` as the canonical metric route,
disagreement log preserved, no total score. See
`docs/research/open-set-review-protocol.md`.

## Success criteria

### Primary — substance (the round-005 weakness)

- non_triviality and follow_up_utility **materially above 0.29** on batch 1;
- acceptance rate moving toward the ≥ 0.60 Layer-C target;
- all criterion rates reported separately (no total score).

### Secondary — domain signal (exploratory)

- batch 2 reviewed with the same rubric; per-domain rates reported side by
  side with batch 1. No pass/fail threshold yet — this is a first F
  observation, not an F validation.

### Failure is a valid outcome

If a stronger model still produces trivial absences, that is real evidence
about the v0.3 prompt-only approach, and it redirects the work (e.g. toward
retrieval-grounded detection) — it must be reported just as plainly as a
success. Do not soften the criteria mid-round.

## Artifact contract

Same as round 005 (`docs/research/artifact-contracts.md`, round-local):

```text
input/hf_batch.json                 # batch 1 (+ batch 2 under input/, clearly named)
model_seed_output.json              # detector=model raw + normalized, per batch
mechanical_prescreen.json / .md     # deterministic gate (triage, not evidence)
open_set_review_packets.json        # two-reviewer packets (after go)
open_set_seed_review_summary.json   # canonical summary per batch
open_set_review_report.md           # human-readable summary
open_set_disagreements.json         # disagreement log
```

## Explicitly out of scope this round

- prompt value-rules (see doctrine boundary above);
- auto-dedup of near-paraphrases (human `duplicate` code stays the arbiter);
- collapsing batch 1 and batch 2 into one score;
- claiming Layer-F validation from a single exploratory batch.
