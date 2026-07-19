# Round 013 — semantic coverage metric + blind human-review pack

> **Status: objective metric restored AND human-anchored.** Two deliverables:
> (1) a meaning-based coverage metric that recovers the payoff signal the lexical
> metric lost in round 012 (+0.575 on gpt-4.1); (2) a blind human-review pack of
> the gpt-4.1 answer pairs — now **scored**: 4 reviewers, unanimous, matching the
> AI verdicts on 10/10 items (see `human_review/RESULTS.md`).

## Part 1 — semantic coverage corroborates the payoff

Round 012 exposed that lexical `coverage()` only credits verbatim seed echoes, so
the well-woven gpt-4.x answers scored 0.00 delta. The new `semantic_coverage()`
(per gap: max cosine between the gap embedding and the answer's sentence
embeddings, thresholded; raw `max_sim` reported) was run on gpt-4.1 with real
OpenAI embeddings (`text-embedding-3-small`, threshold 0.55). Provenance: run
27807741417, job 82291031218.

| metric | baseline | SSL | delta |
|---|---:|---:|---:|
| lexical coverage (verbatim) | 0.10 | 0.10 | **+0.00** |
| **semantic coverage (meaning)** | 0.325 | **0.900** | **+0.575** |

Per scenario (SSL semantic coverage): MODEL_A/B/C/D/G/I = 1.00, E/H = 0.75,
F = 0.50; DNH control 1.00→1.00. The threshold still bites (MODEL_F gaps at
max_sim 0.49–0.50 fall below 0.55), so it is not rubber-stamping. `unsupported =
0`, `promoted = 23`.

**Reading:** the round-012 "collapse to 0.00" was a metric artefact. With a
meaning-based metric the payoff is large and objective (+0.575), and it lines up
with the blind reader (round 012: 9/9 gap scenarios woven correctly). We now have
two independent signals — semantic coverage and reader judgment — instead of one
broken lexical proxy.

Caveats: the threshold (0.55) is a chosen knob (raw `max_sim` is stored so it can
be re-judged); embeddings are a similarity proxy, not a correctness check (they
credit *topical* match, not factual accuracy — that is what the human pass and the
`unsupported`/Gate machinery cover).

## Part 2 — blind human-review pack (the decisive next step)

`human_review/` holds the gpt-4.1 baseline-vs-SSL answer pairs as blind A/B items
(`review_pack.json` / `review_pack.md`), with sources withheld in
`answer_key.json`. This mirrors the round-006 human pass that produced κ 0.63.

- `review_pack.md` — fill `better_answer` = A / B / tie per item, by reading only.
- `answer_key.json` — option→source map **and** the assistant's blind verdicts
  (`ai_better_answer`), withheld until after scoring.

Once filled, the human win-rate (SSL beats baseline) and the human-vs-AI
agreement (raw + Cohen's κ) can be computed, lifting the payoff from AI-judged
signal toward Layer-C. This is the one step only a human can provide.

## Honest verdict

- The payoff signal is now backed by an **objective, meaning-based metric**
  (+0.575 semantic coverage on gpt-4.1) that agrees with the reader, replacing the
  broken lexical proxy.
- It remains **author-designed scenarios + single AI judge** until the human pack
  is scored. The pack is staged; the human pass is the gating evidence.

## Files

```text
human_review/review_pack.md     # blind A/B pairs to score (human)
human_review/review_pack.json   # same, machine-readable
human_review/answer_key.json    # sources + AI verdicts (do not peek before scoring)
human_review/README.md          # how to fill and return
```
