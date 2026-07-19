# Round 011 — scaled payoff test (n=10, capable model)

> **Status: the strongest payoff signal so far — and it holds at n=10.** Real
> hosted model (`openai:gpt-4o-mini`), `max_new_tokens=300`, blind AI reader
> (`reviewer_ai_claude`). Scenarios and ground-truth gaps are **author-designed**
> and the judge is the assistant — so this is a strong *signal*, not Layer-C
> validation. Provenance: Actions run 27791442777, job 82241118051, artifact
> `ssl-openai-model-benefit-gpt-4o-mini` (id 7735…); full JSON in the job log.

## Why

Round 010 showed (a) acting on validated seeds helps on a capable model and does
no harm, but n=3; and (b) the gap-3 retrieval signal was a toy-embedding
artifact. So we **dropped gap-3 rescue and scaled experiment A** — the durable,
retrieval-independent positive — from 3 to 10 scenarios across 9 domains plus one
no-gap do-no-harm control.

## Aggregate (deterministic coverage metric)

| metric | value |
|---|---:|
| scenarios | 10 (9 gap + 1 DNH control) |
| baseline mean gap coverage | 0.10 |
| SSL mean gap coverage | **0.45** |
| coverage delta | **+0.35** |
| promoted seeds | 19 |
| **unsupported additions** | **0 (rate 0.0)** |
| mean answer length delta | +24 words |

## Blind reader win-rate (my judgment, AI — not human)

"Which answer better answers the question (correctness + coverage, not length)?"

| scenario | domain | promoted | verdict | note |
|---|---|---:|---|---|
| MODEL_A | industrial revolution | 0 | **tie** | nothing promoted → SSL == baseline (no harm) |
| MODEL_B | consumer law | 1 | **SSL** | forum-choice clause woven into geschillen + summary |
| MODEL_C | health app | 4 | **SSL** | added AVG/auth/encryptie/rate-limit (label-dump wart) |
| MODEL_D | GLP-1 drug | 3 | **SSL** | added contraindications, cost, rebound weight-gain |
| MODEL_E | solar energy | 1 | **SSL (weak)** | added lifecycle/mining caveat (label-dump) |
| MODEL_F | index investing | 3 | **SSL** | added sequence/​tax/​concentration risk (woven) |
| MODEL_G | vegan diet | 3 | **SSL** | added B12/iron-zinc/protein (woven; truncated at token cap) |
| MODEL_H | ML in prod | 3 | **SSL** | added bias-audit, label-leakage, calibration (label-dump) |
| MODEL_I | bike lanes | 1 | **SSL** | added accessibility as point 7 (cleanly woven) |
| DNH_UNITS | unit conversion | 0 | **tie** | complete answer; control |

**8 SSL wins / 2 ties / 0 losses.** Of the 9 gap scenarios: 8 improved, 1 was a
clean no-op (A, nothing promoted). **Zero derailments, zero unsupported
additions, zero factual harm** at n=10 — the round-008 small-model failure mode
(hallucinated poem, wrong product) did not reappear once.

## What broke / what this round fixed

- **Do-no-harm leak found by the control.** On DNH_UNITS the model originally
  appended a spurious generic "Gevalideerde SSL-seeds: …" platitude even though
  **zero** seeds were promoted. Harmless (the answer stayed correct) but noise.
  **Fixed**: the suite now skips the revision and keeps the baseline verbatim
  when nothing is promoted — do-no-harm by construction (and one fewer API call).
- **Integration-quality wart (open).** Several wins (C, E, H) append a labelled
  "Gevalideerde SSL-seeds:" block rather than weaving the points in; B, F, G, I
  weave naturally. The round-008 "Gevalideerde SSL-seeds:" prompt-leak persists
  cosmetically even on a strong model. Next: revise `build_ssl_revision_prompt`
  to instruct natural integration and forbid naming the seeds.
- **Token truncation.** MODEL_G hit the 300-token cap mid-third-point; raise the
  budget for revision answers.
- **Coverage-metric blind spot (still open, round 010).** The deterministic
  `coverage()` under-counts cleanly integrated seeds (MODEL_B scored 0.0, MODEL_C
  0.25) that the reader sees plainly. The blind answer-pair review is the better
  judge; the token metric is a conservative floor.

## Honest verdict

The make-or-break question — *does acting on validated seeds make answers
better?* — now has a **consistent positive at n=10 on a capable model: 8/9 gap
scenarios improved, 0 harm, 0 unsupported additions.** This is the 4.6 promise
working repeatedly, not once.

Bounding it honestly:

- **Author-designed evidence.** I wrote the scenarios, the ground-truth gaps, and
  judged the pairs. The detector is the deterministic prior-based one, so a
  promoted seed is by design a real gap. The strongest honest claim is: *when a
  valid gap-seed exists, integrating it reliably improves the answer and does no
  harm.* It is **not** independent validation that SSL discovers non-obvious gaps
  in the wild (that is the open-set detection track, rounds 005–007, and the
  human anchor κ-0.63).
- Single AI judge; no human pass on these 10 pairs yet.

## Next steps

1. **Human anchor** on these 10 blind pairs (reuse round-006 human tooling) — the
   cheapest way to lift this from AI-judged signal toward Layer-C.
2. **Weave, don't label**: refine the revision prompt; re-run; check the
   label-dump wart disappears without new unsupported additions.
3. Raise the revision token budget (MODEL_G truncation).
4. Fix the `coverage()` blind spot or lean on the answer-pair win-rate as primary.
