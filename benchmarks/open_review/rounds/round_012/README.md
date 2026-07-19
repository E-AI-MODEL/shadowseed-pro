# Round 012 — weave-don't-label prompt + stronger models (gpt-4o-mini / gpt-4o / gpt-4.1)

> **Status: the integration wart is fixed across all models; and the run exposed
> that the deterministic coverage metric measures the wrong thing.** Same 10
> scenarios as round 011, new revision prompt, three models, blind AI reader.
> Author-designed scenarios + AI judge → signal, not Layer-C.

## What changed since round 011

1. **Revision prompt rewritten** to weave each missing point into flowing prose
   and to *forbid* naming "seeds", lists, or appending a heading
   (`build_ssl_revision_prompt`).
2. **Token budget** raised 220 → 400 (round 011 MODEL_G truncation).
3. Ran on three models with the new prompt: `gpt-4o-mini`, `gpt-4o`, `gpt-4.1`.

Provenance (Actions runs / jobs): gpt-4o-mini 27806046178/82286007138;
gpt-4o 27806051203/82286021947; gpt-4.1 27806054362/82286031773. Full JSON in
each job log.

## Result 1 — the label-dump is gone (the wart is fixed)

Round 011 appended a literal "Gevalideerde SSL-seeds:" block on several wins.
Now, scanning all answers for any seed/list/SSL label leak:

| model | label-leak scenarios |
|---|---:|
| gpt-4o-mini | **0 / 9** |
| gpt-4o | **0 / 9** |
| gpt-4.1 | **0 / 9** |

Even the weakest model (mini), which leaked in round 011, now integrates
naturally — e.g. *"Bij het verwerken van medische hartslagdata is het essentieel
dat de app voldoet aan de AVG-compliance, wat de privacy van gebruikers
waarborgt."* gpt-4.1 goes further and reframes whole answers around the gap
(MODEL_B folds the forum-choice clause into the reasoning rather than tacking it
on). The seeds are now explained, not parroted.

## Result 2 — the do-no-harm fix holds

On all three models the DNH_UNITS control has `ssl_answer == baseline_answer`
(the round-011 spurious-append fix), and **unsupported additions = 0** on all 10
scenarios for every model. Zero derailments, zero fabrication.

## Result 3 (the important one) — the coverage metric measures verbatim echo

The deterministic `coverage()` delta **collapsed to 0.00 on all three models**,
even though 22–23 seeds were promoted and answers grew +64–73 words of correct,
on-topic content:

| model | promoted | unsupported | coverage delta | mean +words |
|---|---:|---:|---:|---:|
| gpt-4o-mini | 22 | 0 | **0.00** | +73 |
| gpt-4o | 23 | 0 | **0.00** | +71 |
| gpt-4.1 | 22 | 0 | **0.00** | +64 |

Compare round 011 (old label-dump prompt, same scenarios/model): coverage delta
was **+0.35**. Nothing got worse — the answers got *better*. The metric scores
`jaccard(expected_addition, answer_fragment) ≥ 0.70`, which only fires when the
answer repeats the gap's noun-phrase **verbatim**. The label-dump did exactly
that; natural weaving paraphrases the concept, so the lexical match disappears.

**Conclusion: `coverage()` rewards parroting the seed text and penalises good
writing. It was never measuring whether the gap was addressed.** The verbatim
"+0.35" in rounds 010–011 was partly an echo artefact. The blind answer-pair
reader is the only valid payoff measure here, and it stays strongly positive:
reading the gpt-4.1 answers, all 9 gap scenarios weave the promoted seeds in
correctly with rationale (DNH a clean tie) — 9/9 improved, 0 harm.

## Honest verdict

- The integration quality wart from round 011 is **fixed** and the fix
  generalises down to the weakest model.
- Stronger models (gpt-4o, gpt-4.1) do not change the *correctness* verdict
  (all integrate cleanly, 0 unsupported); they differ in prose quality, with
  gpt-4.1 the most fluent and willing to restructure around the gap.
- **Methodological cost:** the only objective floor we had (`coverage()`) is now
  confirmed unreliable for well-written answers. The payoff result therefore now
  rests entirely on reader judgment — which makes the human anchor more
  important, not less.

## Next steps

1. **Replace the broken metric**: a semantic coverage check (does the answer
   address each expected gap? via embeddings `openai_client.embed`, or an
   explicit LLM-judge per gap) instead of lexical jaccard. Needed before any
   win-rate can have an objective corroborator again.
2. **Human anchor** on the blind pairs (round-006 tooling) — now the decisive
   step, since the deterministic floor is gone.
3. Optional: a couple of adversarial scenarios where the "gap" is wrong/irrelevant,
   to confirm the Gate/reader reject it (false-positive control at the payoff level).
