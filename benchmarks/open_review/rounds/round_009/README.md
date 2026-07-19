# Round 009 — generative "kunnen staan" detector (vision gap 1), plan

> **Status: capability built, dispatch pending.** The generative prompt variant
> exists and is wired end-to-end (`--prompt-variant generative`); this round
> validates whether it produces richer seeds than the omission detector.

## Why

Rounds 005–007 showed the omission detector ("wat ONTBREEKT") plateaus at
"relevant but trivial". The vision (`docs/research/vision-generative-seeds.md`)
says the unique value is generative — "wat had hier KUNNEN staan", the not-taken
frame, beyond the RAG ceiling. Gap 1 is the linchpin; it is now buildable to run.

## Design (A/B on the same items, one lever)

Same source batch, same model, same reviewer; only `--prompt-variant` differs.

```bash
# A — omission baseline (the established detector)
shadowseed run-open-set-seed-review --input <batch> \
  --detector model --model-backend hf-transformers \
  --model-id microsoft/Phi-3.5-mini-instruct --prompt-variant absence \
  --output results/open_review/abs_seed_output.json

# B — generative "kunnen staan"
shadowseed run-open-set-seed-review --input <batch> \
  --detector model --model-backend hf-transformers \
  --model-id microsoft/Phi-3.5-mini-instruct --prompt-variant generative \
  --output results/open_review/gen_seed_output.json
```

Then: mechanical prescreen on both, blind interleaved review (reuse
`build_blind_control_packets.py`) so the reviewer can't tell omission from
generative, and report per-arm acceptance + the criterion that matters here —
**non_triviality / follow_up_utility** (where the omission detector failed).

## Success criteria (signal, not proof)

- generative arm scores **materially higher non_triviality / follow_up_utility**
  than the omission arm under blind review, without a relevance collapse;
- new failure modes (hallucinated *facts*, not frames) stay low — the
  doctrine guardrail ("een invalshoek mag nieuw zijn; een feit niet") holds.
- A null/negative result is valid and reportable: it would say generative
  framing needs a stronger model or the model-internal falsification (gap 4)
  before it pays off.

## Caveats

n is small, single (possibly AI-delegated) reviewer, CPU model. This tests the
*detector lever*, not yet the end-to-end payoff (that is round 008's line, and
ultimately needs the SSL→RAG head-to-head, gap 3).
