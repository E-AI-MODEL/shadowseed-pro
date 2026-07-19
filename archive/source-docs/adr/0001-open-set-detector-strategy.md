# ADR 0001 — Open-set detector strategy

Status: accepted (evolving)
Date: 2026-05-22
Deciders: shadowseed maintainers
Related: #41, #56, #74, #81; PRs #76, #78, #79, #86, #88
Supersedes: none
Evidence layer: C (open-set seedkwaliteit) in `docs/00_shadow_seed_learning_4_6.md`

## Context

The 4.6 one-sentence claim (`docs/00_shadow_seed_learning_4_6.md`) is:

> Shadow Seed Learning is een mechanisme waarmee een taalmodel kleine
> structurele afwezigheden in een antwoord detecteert ...

The original open-set lane did not satisfy this. Its candidate generator,
`open_set_candidate_adapter` (v0.1), is a regex + five Dutch templates. On the
round 001 AG News batch it produced only 21 unique seed texts across 60 slots
and emitted exactly the meta-categories that `docs/02_atomic_seeds.md` §3
forbids (for example "Onderbouwing van de centrale bewering"). It is therefore
infrastructure, not Layer C evidence (see
`benchmarks/open_review/rounds/round_001/STATIC_QUALITY_FINDING.md`).

We needed a path that actually uses a language model for detection, without
throwing away the deterministic baselines that keep CI cheap and let us measure
improvement.

## Decision

The open-set lane has **three selectable detectors** behind one
`--detector` flag on `run-open-set-seed-review`. The canonical list lives in
`SUPPORTED_DETECTORS` in `src/shadowseed/benchmark/open_set_candidate_adapter.py`
and is the single source of truth that the CLI and the workflow follow.

1. **`adapter_v1`** (default) — the v0.1 regex/template baseline. Default for
   backwards compatibility. Deterministic, free, fast. Not Layer C evidence.
2. **`adapter_v2`** — text-grounded template baseline
   (`open_set_candidate_adapter_v2`). Extracts salient tokens from the input
   so seeds reference the actual item. Stronger baseline; still not a language
   model, still not Layer C.
3. **`model`** — the v0.3 taalmodel detector (`open_set_model_detector`) with
   two backends:
   - `fixture` — deterministic, `[FIXTURE]`-prefixed, no model download, for CI.
   - `hf-transformers` — a real local model via the transformers stack.

Only **`--detector model --model-backend hf-transformers`** satisfies the 4.6
one-sentence claim and is eligible to produce Layer C evidence. Everything else
is baseline infrastructure or a regression fixture.

### Supporting decisions

- **Default stays `adapter_v1`.** Standard CI and any caller that does not opt
  in keeps the old, deterministic behavior. The model path is opt-in.
- **The model path suppresses the auto-"ontbreekt" normalization.** The
  normalizer (`seed_normalization.py`) appends " ontbreekt." to short fragments,
  which is right for broad human-written categories but disguises weak model
  output as well-formed seeds. `run_open_set_seed_review` passes
  `expand_short_fragments=(detector != "model")` so a language model is judged
  on what it actually produced. (PR #86)
- **Few-shot prompt examples must come from a domain OTHER than the open-set
  corpus.** Round 003b (Qwen2.5-1.5B) leaked news-domain example entities
  (Sven Jaschan, Apple) into unrelated news items. The examples now come from
  history / medicine / law (reused from `docs/02_atomic_seeds.md`), and a
  verbatim/near-verbatim leak filter is the safety net. (PR #88)
- **Model selection is per-round, not fixed in code.** The model ladder lives
  in #81; rounds are dispatched via the `open-set-hf-review` workflow.

## Round history (the evidence trail)

| Round | Detector | Outcome |
|---|---|---|
| 001 | adapter_v1 | infrastructure baseline; meta-category seeds; paused, not Layer C |
| 002 (planned) | adapter_v2 | stronger template baseline; not yet dispatched |
| 003a | model + SmolLM2-360M | pipeline works; model too small — output was citations and fragments, not gaps |
| 003b | model + Qwen2.5-1.5B | full Dutch sentence gaps (big jump) but few-shot leakage + hallucination |
| 003c (pending) | model + Qwen2.5-1.5B | re-dispatch against the v0.3c foreign-domain prompt + leak filter |
| 004 (v0.3d, reviewed) | model + Qwen2.5-3B-Instruct | 12 AG News items. Human review complete (two reviewers); AI prescreen flagged claim-vs-gap, mistranslation, false-gap — addressed in the v0.3d/v0.3e prompt + entity filter |
| 005 (v0.3e) | model + Qwen2.5-3B-Instruct | `ag_news_test` offset 0 + 12, 23 items / 114 candidates. v0.3e removed claim-vs-gap (prescreen: 30→0; clean-rate 0.553). Built with an `adapter_v1` blind baseline control. **Offset-12 batch human-reviewed (PR #116): 41 seeds, acceptance 0.29 — relevance 0.98 but non-triviality/follow-up 0.29; form fixed, substance not.** Offset-0 + blind control closed as delegated AI review (offset-0 0.185, same pattern; blind control model 0.219 vs baseline 0.0, delta +0.219). See `benchmarks/open_review/rounds/round_005/` and `.../ai_review/` |
| 006 (v0.3e, Phi) | model + Phi-3.5-mini-instruct | Batch 1 (news, same items as 005 offset-0): AI-reviewed acceptance 0.185 -> 0.50 — the model lever works. Batch 2 (arXiv abstracts, first Layer-F point): 0.458 — quality transfers. Phi follows the few-shot noun-phrase examples instead of the absence-scaffold rule (form compliance is domain-dependent: 0/60 vs 18/60 scaffolded). **Resolved in prompt v0.3g**: the gap-label noun phrase (the canonical 4.5 form) is now the rule as well as the examples; absence sentences stay allowed; the prescreen claim_vs_gap check now detects actual assertions (main-clause finite verb) instead of requiring a marker. See `benchmarks/open_review/rounds/round_006/` |

## Consequences

Positive:
- the 4.6 one-sentence claim is satisfiable through a concrete, dispatchable path
- baselines are preserved, so improvement is measurable round over round
- CI stays cheap (fixture backends), real model runs are opt-in and manual
- claim discipline is explicit: only model + hf-transformers is Layer C

Negative / open:
- the `hf-transformers` generation path is not exercised in CI (needs a real
  model); only its construction and parsing are unit-tested
- mutated few-shot leakage (same template, swapped entity) is not caught
  mechanically; it needs content-grounding of the seed against the input text,
  which is future work
- the open-set batch is still single-domain (AG News offset 0 is all Sci/Tech);
  a domain-spread intake is future work before a broad Layer C claim
- model quality is the current ceiling: a sub-1B model cannot follow the
  detection prompt; the practical floor is around 1.5B on a CPU runner

## Status and revisit triggers

Accepted and evolving. Revisit this ADR when any of these happen:
- a round produces seeds that pass human review well enough to call it real
  Layer C evidence (then record the model + acceptance rate here)
- mutation-leakage forces a content-grounding filter (new supporting decision)
- a fourth detector is added (update `SUPPORTED_DETECTORS` and this ADR together)
- the domain-spread intake lands (changes what a Layer C claim can cover)
