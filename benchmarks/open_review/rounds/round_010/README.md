# Round 010 — real-model payoff (capable model) + gap-3 head-to-head

> **Status: the round-008 bottleneck is resolved on a capable model; first
> gap-3 signal.** Real hosted model (`openai:gpt-4o-mini`), greedy decoding.
> Two experiments, both at tiny n, both reader-judged by an AI judge
> (`reviewer_ai_claude`, the κ-0.63-validated judge) — **signal, not proof.**
> This is the "bigger model" next step that round 008 payoff_run_01 explicitly
> asked for.

## Provenance

| experiment | Actions run | job | artifact |
|---|---|---|---|
| model-benefit (payoff) | 27788963640 | 82232846606 | `ssl-openai-model-benefit-gpt-4o-mini` (id 7735634956) |
| ssl-vs-rag (gap 3) | 27788968553 | 82232863294 | `ssl-openai-ssl-vs-rag-gpt-4o-mini` (id 7735631165) |

Backend wired in this session (`openai_client.py` + factory wiring, PR #141);
run via the `Research · SSL Benefit (OpenAI)` workflow with the `OPENAI_API_KEY`
repo secret. Decoding `temperature=0, seed=0`. The full result JSON is printed
verbatim into each job log (egress to the artifact blob store is not always
reachable from the analysis environment).

---

## Experiment A — does acting on validated seeds improve answers?

Same harness as round 008 (`run-model-benefit-suite`, 3 scenarios, free-rewrite
revision via `build_ssl_revision_prompt`), but `--backend openai --model-id
gpt-4o-mini` instead of CPU Phi-3.5-mini.

### The headline: the derailment is gone

Round 008 on Phi-3.5 lost 2 of 3 because the **revision step derailed**
(hallucinated a Seamus-Heaney poem; bled in a wrong product). On gpt-4o-mini,
under the *same free-rewrite prompt*:

- `unsupported_ssl_addition_rate = 0.0` on **all three** scenarios;
- the baseline answer is preserved and only the validated seeds are folded in;
- where no relevant seed is promoted, the answer is left essentially unchanged
  (no harm).

So the "do no harm" property we previously had to *enforce* with the append-only
strategy (round 008 run 02) emerges naturally from a capable model even under a
free rewrite. The make-or-break risk of round 008 — *acting on seeds corrupts a
good answer* — does not reproduce here.

### Per-scenario (deterministic coverage + my blind reader verdict)

| scenario | baseline cov | ssl cov | promoted seeds (relevant) | blind verdict |
|---|---:|---:|---|---|
| MODEL_A (industrial revolution) | 0.0 | 0.0 | none relevant promoted | **tie** (answer unchanged, no harm) |
| MODEL_B (consumer law) | 0.0 | 0.0\* | 1 (afdwingbaarheid EU-recht, score 2) | **ssl** (correct point cleanly added) |
| MODEL_C (HealthTrack app) | 0.0 | **1.0** | 4 (AVG, auth, encryptie, rate-limit) | **ssl** (security layer added, 0 unsupported) |

Blind AI reader win rate: **2 ssl wins, 1 tie, 0 losses of 3** (vs Phi-3.5's
1 win / 2 losses). AI judgment, not human; n=3 → signal, not a verdict.

\* **Metric caveat (MODEL_B):** the promoted seed scored a structural match
(score 2) **and** is visibly integrated into the SSL answer ("3. Afdwingbaarheid
van EU-consumentenrecht …"), yet the lexical `coverage()` metric credited it 0.0
— a jaccard-threshold/phrasing artifact. The automatic coverage metric
*understates* the real benefit here; the blind answer-pair review is the better
judge. Worth fixing or at least flagging in the suite.

### MODEL_C, the clean win (illustrative)

Baseline was a generic UX review of a health app. The SSL revision kept it
verbatim and appended exactly the validated, domain-correct gaps for an app
handling medical heart-rate data:

> - Zorg voor AVG-compliance bij de verwerking van medische hartslagdata.
> - Implementeer een sterke authenticatiestrategie voor toegang tot gezondheidsdata.
> - Zorg voor encryptie van medische data, zowel in rust als tijdens transport.
> - Pas rate-limiting toe op API's die gezondheidsdata verwerken.

`coverage 0.0 → 1.0`, `unsupported 0`. This is the 4.6 promise working cleanly.

---

## Experiment B — gap 3: retrieve toward the *gap* vs the *question*

`run-ssl-vs-rag`, 2 items, `top_k=3`, equal context budget (Codex #139 fix).
RAG arm queries the **question**; SSL-probe arm queries the **seed/gap**. Same
model answers both; only the retrieved context differs.

> **Hard caveat:** retrieval here uses the toy deterministic 128-d
> `lexical_embedding` (a hash, not a real embedder). Both arms are brittle under
> it. So this shows the *mechanism*, not a production RAG comparison. Real
> embeddings are the obvious next step (`openai_client.embed` now exists).

### SSLRAG_LAW — the demonstration

| arm | retrieved chunks | answer |
|---|---|---|
| RAG (query=question) | 2× industrial-revolution chunks + 1 law chunk | **non-answer**: "De SSOT-context biedt geen specifieke informatie …" |
| SSL-probe (query=gap) | the 3 correct law chunks (enforcement, jurisdiction, eu_rights) | **correct, substantive**: afdwingbaarheid, internationaal privaatrecht, forumkeuze, EU-garantie, niet-EU-caveat |

Retrieving toward the question pulled the *wrong* documents and the model
honestly refused; retrieving toward the gap pulled the right ones and produced a
correct answer. `seed_only_chunk_ids` confirms the probe reached
`law::enforcement` and `law::eu_rights` that the question retrieval missed. This
is "a shadow seed finds a better answer than ordinary RAG would" — visible, with
the toy-retriever caveat.

### SSLRAG_IR — the honest counter-case

The question retrieval was already complete (it got the innovation chunk), so
RAG covered technology **and** colonial factors. The gap-probe narrowed to the
colonial angle and **dropped the technology factor** — less complete for "why
could the Industrial Revolution arise". → **RAG better** here.

Blind AI reader: **1 ssl win (LAW), 1 RAG win (IR) of 2.** The win is dramatic
(non-answer vs correct); the loss is "narrower", not "wrong". The lesson matches
the philosophy: the gap-probe helps most exactly when ordinary retrieval *misses*
the gap, and can over-narrow when the question already covers the ground.

---

## Experiment B′ — gap 3 redone with **real** embeddings (the caveat mattered)

Run 27790952137 (job 82239480150), `--embedding-backend openai`
(`text-embedding-3-small`, 1536-d). Same items, same model, same top_k; the
*only* change from B is the retriever: real embeddings instead of the 128-d hash.

**The toy-retriever caveat was load-bearing. The B headline does not survive.**

| item | toy embedding (B) | real embedding (B′) |
|---|---|---|
| SSLRAG_LAW | RAG retrieved the **wrong** (industrie) chunks → non-answer; probe → correct answer | RAG retrieves the **3 correct law chunks**; `seed_only_chunk_ids = []` — the probe finds nothing the question didn't |
| SSLRAG_IR | probe surfaced `eu_rights` (noise) | RAG complete (incl. `innovation`); probe trades `innovation` for `labour` (`seed_only = [labour]`) |

- **SSLRAG_LAW**: with a real embedder, ordinary RAG on the *question* already
  retrieves `law::enforcement / eu_rights / jurisdiction` and answers correctly.
  `seed_only_chunk_ids` is **empty**. The dramatic "RAG fails → SSL wins" from B
  was an **artifact of the weak hash retriever**, not a property of SSL.
- **SSLRAG_IR**: the probe still reaches a seed-only chunk (`ir::labour`) the
  question misses — the *mechanism* is real — but it drops the `innovation`
  chunk, and the resulting answer omits the technology factor, so it is not
  better for the core "why" question.

Blind AI reader on B′: **0 SSL wins / 2 (RAG ≥ SSL on both).** On this fixture,
with a real retriever, "a shadow seed finds a better answer than ordinary RAG"
is **not supported**.

### Why — and what it means for the thesis (not a refutation, a sharpening)

The fixture's seeds are near-paraphrases of corpus chunks, and the answer *is*
recoverable from the question once embeddings are semantic. SSL's value
proposition is the opposite setting: where the gap is **orthogonal to the
question's surface** and genuinely *not* recoverable by querying the question.
This 7-chunk fixture cannot exercise that, and the toy retriever was masking it.
So B′ is a **fixture/measurement verdict, not a verdict on SSL**: to test the
real claim we need a corpus where the gap is not a paraphrase of a retrievable
chunk. (Experiment A — acting on a *validated* seed during answering — is
untouched by this; it does not depend on retrieval.)

## Honest verdict

- **Payoff (A):** the round-008 negative was a *small-model revision-step
  artifact*, not an SSL flaw. On a capable model the revision adds validated
  substance without derailing (2 wins / 1 harmless tie / 0 losses, 0 unsupported
  additions). Still n=3, AI-judged → **strong signal, not Layer-C validation.**
- **Gap 3 (B → B′):** under the toy retriever the gap-probe looked like it beat
  RAG; under **real embeddings it does not** (0/2, `seed_only=[]` on LAW). The B
  win was a retriever artifact. The probe *mechanism* (reaching a chunk the
  question misses) is still real (IR `seed_only=[labour]`) but does not yield a
  better answer on this fixture. **Verdict on the fixture/measurement, not on
  SSL** — the corpus can't pose a gap that is orthogonal to the question.

## Next steps

1. ~~Real embeddings for gap 3~~ ✅ done (B′) — and it overturned the B signal.
2. **A fixture that actually exercises the claim**: items where the decisive gap
   is *not* a paraphrase of a retrievable chunk (the question cannot reach it
   even with good embeddings), so the gap-probe has something to find that RAG
   structurally cannot. Without this, gap 3 is untestable.
3. **Bigger n** for both experiments — 3 scenarios / 2 items can't carry a
   win-rate verdict.
4. **Human anchor** on the blind answer pairs (reuse round-006 human tooling).
5. **Fix the MODEL_B coverage-metric blind spot** (integrated seed scored 0).
6. Experiment A (payoff) is the durable positive and is **retrieval-independent**
   — prioritise scaling A over rescuing the current gap-3 fixture.
