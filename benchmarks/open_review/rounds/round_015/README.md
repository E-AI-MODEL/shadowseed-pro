# Round 015 — wild-payoff (W1): real detected seeds vs a strong model's own gap-spotting

> **Status: an honest, largely NEGATIVE result — and a directional one.** On short
> news abstracts, SSL's own detected gaps are mostly things gpt-4.1 already names
> unaided. This is the PvA P0/W1 step (real, non-author-designed seeds through the
> payoff pipeline). Provenance: run 27896498845, job 82548932793. Source seeds:
> round 006 batch1, AI-reviewed accepted (κ 0.63 vs human).

## The number

12 items, 29 detected (AI-accepted) gap-seeds. Baseline = gpt-4.1 reading the text
and doing its **own** "what is missing" analysis; we then measure how many of the
detector's gaps that unaided analysis already covered (semantic, real embeddings).

| metric | value |
|---|---:|
| mean baseline coverage of detected gaps | **0.82** |
| detected gaps the baseline MISSED ("novel") | **4 / 29 (14%)** |
| …of which genuine on inspection | **~2 / 29 (~7%)** |

So a strong model, unaided, already surfaces ~82% of the detector's gaps — and on
reading, two of the four "novel" misses are **semantic-metric near-misses**, not
real catches:

- `AG_NEWS_TEST_2`: detector "Omvang van het gehonoreerde grant" — baseline
  already says *"Hoogte en bron van de subsidie: er wordt niet genoemd…"* (same
  gap, different words; cosine fell below 0.55).
- `AG_NEWS_TEST_10`: detector "De exacte groep technologiebedrijven" — baseline
  already names Texas Instruments, STMicroelectronics, Broadcom.

That leaves ~2 niche gaps (e.g. *Sophos' specific identification strategies*) the
model genuinely didn't raise — low value, not the kind of insight that would make
an answer meaningfully better.

## What this means (the directional part)

This is the make-or-break honesty check for the wild loop, and it says: **on easy,
short texts a capable model self-critiques well enough that SSL's detected gaps add
little.** It connects two earlier findings:

- rounds 005/007: the detector finds "relevant but **trivial**" gaps — and trivial
  gaps are exactly the ones a strong model also names itself;
- round 014: a capable model is a strong backstop — here that cuts *against* SSL's
  marginal value, not for it.

So SSL's payoff value is **not** on short self-contained texts. Where it could
still pay off (testable next):

1. **Hard / dense / specialised texts** where the model does *not* spontaneously
   see the gap (the round-007 science domain, long documents, technical specs).
2. **Generative "kunnen staan" frames** (gap 1, v0.4-gen) — not omissions a
   summary would list, but non-obvious angles a model won't raise unprompted.
3. **Cross-turn accumulation** (gap 5) — value from a seed that persists and
   compounds over a conversation, which a single-shot analysis cannot show.

## Honest bounds

- n=12, one corpus (AG-News abstracts), one model (gpt-4.1), AI/metric-judged.
- The semantic metric under-counts baseline coverage (≥2 false "novel"), so the
  true redundancy is *higher* than 82% — the result is conservative against SSL,
  i.e. the negative is, if anything, understated.
- This bounds SSL's value on *easy* texts; it does **not** refute SSL on hard
  texts or generative frames — those are exactly the untested cases above.

## Files

```text
results live in the job log (run 27896498845); dataset:
src/shadowseed/data/wild_payoff_suite.json
```
