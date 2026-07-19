# Round 006 batch 1 — human vs AI second-pass results

> First independent human-vs-AI agreement number since the round 005 human
> batch. Human review by the maintainer (binary accept/reject, blind to the AI
> verdicts); 4 candidates marked `?` were abstained. Scored with
> `scripts/human_review_control.py` over the 54 decided candidates.

## Numbers

| metric | value |
|---|---:|
| candidates scored | 54 (4 abstained) |
| **human acceptance** | **0.593** |
| **AI acceptance** (same 54) | 0.519 |
| raw agreement | 0.815 |
| **Cohen's κ** | **0.627** |
| both accept | 25 |
| both reject | 19 |
| human-only accept | 7 |
| AI-only accept | 3 |

## What this settles

1. **The delegated AI reviews are a usable proxy.** κ = 0.63 is "substantial"
   agreement (Landis & Koch 0.61–0.80). So the rounds 006–007 AI acceptance
   numbers can stand as AI-estimated signals with a now-measured reliability —
   not gospel, but not arbitrary.

2. **The headline is not inflated — if anything the human is more generous.**
   On the 0.50 "model lever works" batch the human accepts **0.593 ≥ 0.519**.
   The "model lever works" signal survives an independent human anchor.

3. **My rubric-sensitivity strict bound (0.328) was the pessimistic side, not
   the truth.** I framed the in-sample/out-of-sample gap as partly "AI
   leniency"; the human went the *other* way (more lenient than my AI review).
   The strict rule brackets how low a stricter reviewer could go; this human
   sits at the high end. Corrected in `round_007/README.md`.

## Where human and AI disagree (the structured residual)

**AI accepted, human rejected (3)** — all impact/generic asks:
`18` precision percentages of the Prediction Unit · `24` impact on air quality
· `30` strategies Sophos used. Here the human agreed with the *strict* rule.

**Human accepted, AI rejected (7)** — several are impact/speculation asks:
`19` impact on wildfire prevention · `23` expected effectiveness · `25`
possible later reactions · `47` other possibly-involved companies · plus `29`
collaboration details, `45` presentation timing, `58` competition details.

The residual disagreement is concentrated almost entirely on the
**impact/speculation boundary** — the softest, hardest-to-operationalize part
of the rubric. Notably the maintainer's *prose* said to reject broad impact /
speculation asks, but several revealed accepts (19, 23, 25, 47) are exactly
that: even a human's item-level decisions don't perfectly match their own
stated criteria. That boundary, not "form" or "density", is the real frontier.

## Maintainer's quality verdict and round-008 direction

Gestalt score **6/10**: "bruikbaar, maar nog te ruim en soms lui
geformuleerd." Strong seeds ask for concrete missing facts (name, date,
location, amount, reaction, technical measure, concrete outcome); weak seeds
are too general, already in the text, duplicate, or "what else could a longer
article cover?".

Stated precision filter for the next detector iteration:

1. Is the answer already (near-)literally in the text?
2. Is it a concrete fact, not a broad impact question?
3. Is it central to *this* item, not just "also interesting"?
4. Is it non-duplicate?

This is the round-008 north star: a higher-precision detector, not more
volume. (Still a signal, not Layer-C validation: 54 candidates / 12 items,
single human reviewer, ≥ 0.60 acceptance target unchanged.)
