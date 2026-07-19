# Round 016 — generative payoff (W5): the decisive test of the vision claim

> **Status: convergent NEGATIVE with W1 — with one confound to clear before any
> verdict.** Even SSL's *generative* "wat had hier KUNNEN staan" frames are
> ~88% raised by gpt-4.1 itself. Provenance: run 27896816817, job 82549816835.
> Frames detector-produced (v0.4-gen, openai), topics author-chosen.

## The number

8 reframe-friendly topics, 24 detector-generated frames. Baseline = gpt-4.1
answering the question unaided; we measure how many of the detected frames the
baseline already raised (semantic, real embeddings).

| metric | value |
|---|---:|
| mean baseline **frame** coverage | **0.88** |
| frames the baseline MISSED ("novel") | **3 / 24 (12.5%)** |

The detector's frames are exactly the "obvious non-obvious" lenses a frontier
model produces when asked to answer thoroughly: *macht en zeggenschap*, *sociale/
vermogensongelijkheid*, *speculatie als prijsdrijver*, *vertrouwen in instituties*,
*systeemverandering naast individueel gedrag*. gpt-4.1 raises ~7 of 8 of these
itself. The 3 genuinely novel frames (ecologische gevolgen van vroege
industrialisatie; ruimtelijke ordening/grondbeleid; systeemverandering als kader)
are modestly useful, not transformative.

## Convergence with W1 — the honest synthesis

| test | mode | baseline self-coverage |
|---|---|---:|
| W1 (round 015) | omission ("wat ONTBREEKT") | 0.82 |
| W5 (round 016) | generative ("wat had KUNNEN staan") | 0.88 |

Both interpretations of SSL — omission and generative — converge on the same
finding: **on a frontier model, the detected seeds/frames are largely things the
model produces itself.** Since the detector and the answerer are the same gpt-4.1,
this is almost structural: the model is its own gap/frame generator. SSL's
*external Niveau-1 added value over a frontier model* looks small (~12–18%, partly
metric noise).

## The confound I must flag (before any verdict)

The baseline prompt here explicitly asks for *"de belangrijkste verklarende
invalshoeken"* — it **primes** the model to produce frames. So W5 compares the
detector's specific frames against *the model's own frames when asked for frames*.
That inflates baseline coverage. A fair decider is a **naive baseline** ("just
answer the question", no framing instruction): if even then the frames are already
covered, the negative is unimpeachable; if a naive baseline covers far fewer, SSL
*does* add value over an unprimed model and W5's number is a priming artdefact.

→ **Decider task W7**: re-run W5 with a naive baseline.

## What is and isn't shown

- **Shown (subject to W7):** SSL as an *external detector for a frontier model* on
  single-shot tasks adds little over the model's own thorough answering.
- **NOT shown / still live:**
  1. weaker models (where the model is *not* its own good frame-generator) —
     SSL could lift them;
  2. cross-turn accumulation (gap 5) — value that compounds over a conversation,
     invisible to single-shot tests;
  3. Niveau 2 / model-internal (H-neurons) — a different mechanism entirely;
  4. the payoff-given-a-valid-seed result (rounds 011–013) still stands — acting
     on a good seed helps and does no harm; the issue is that few such seeds exist
     that a frontier model wouldn't raise itself.

## CORRECTIE (maintainer, 2026-06-21) — deze suites zijn GEEN SSL-pijplijn

Belangrijker nog dan de scope-correctie hieronder: `wild_payoff_suite`,
`generative_payoff_suite` en `adversarial_payoff_suite` **gebruiken de
`SSLManager`-pijplijn helemaal niet** — geen weight-0 seeding, geen Validation
Gate, geen recurrence, geen TTL/TrTL, geen constellation, geen probe. Ze doen
"detector-string → in de prompt → meten": een losstaande, zwakke afgeleide van
SSL, geen test van het systeem dat we gebouwd hebben. De W1/W5/W14-"negatieven"
**oordelen dus niet over de pijplijn** — alleen over naïeve single-shot
string-injectie. De echte test moet door de componenten lopen
(`ingest_detection_candidates` → `run_validation_gate` over beurten →
`decay_traces` → `reactivate_by_text` → `find_constellations` → probe); pas wat de
*pijplijn* promoot mag een later antwoord sturen. Zie `round_017`.

## Scope correction (maintainer, 2026-06-21) — what W1/W5 actually measured

W1 and W5 are both **single-shot**: inject a seed into one answer, check if the
model already had it. But that is **not** the SSL mechanism. SSL's mechanism is
the **weightless shadow seed (weight 0) that travels across turns via TTL/TrTL
and gets another chance to land later**, when the conversation shifts and the
context finally triggers it. A seed that looks redundant *this* turn may be
exactly the one that matters three turns on. So W1/W5 collapsed the cross-turn
dynamic into one shot and therefore measure SSL's *weakest, degenerate* form.

Two consequences:

1. **Gap 5 (the living cross-turn shadow) is not "yet another untested claim" —
   it is THE claim.** The real test is multi-turn persistence, not single-shot
   injection. W7 (naive single-shot baseline) is therefore *not* the decider; the
   cross-turn test is.
2. **The 3–10% residual may be the prize, not the noise.** If a mechanism
   *reliably and persistently* captures the blind spot even a frontier model
   misses — at zero cost (weight 0) — that is a large step for LLM reasoning, not
   a marginal one. Dismissing the residual as "small" was too quick.

So W1/W5 stand as honest results **for single-shot external detection**, and that
interpretation is genuinely weak on a frontier model. They do **not** speak to
the cross-turn mechanism, which is next.

## Next move (revised)

Build the **cross-turn payoff test** (gap 5): a multi-turn conversation where a
weight-0 seed detected early persists, decays/TrTL-reactivates, and gets a later
chance to enter an answer — compared against a normal chatbot that has the same
conversation history but no shadow memory. The fair question: does the carried
seed surface value at a later turn that the model would *not* re-derive from
history alone? It can fail (a strong model re-derives from history); that is the
honest test, and per the residual argument even a small reliable win counts.
