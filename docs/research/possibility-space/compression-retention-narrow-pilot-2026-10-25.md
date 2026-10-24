# A narrow compression-retention test is NOT the Shadowseed thesis

> **Status (2026-10-25):** research-only, offline instrumentation and candidate study design. No real compression, LLM generation, experimental human review, or evidence for Q1/Q2 has been obtained from the synthetic fixtures. **G0 for the broad thesis remains NOT PASSED.**
> **Authority:** [verbatim full thesis](../possibility-space-thesis.md), [first-principles rival hypotheses](first-principles-reorientation-2026-10-25.md), [matched adapter comparison](g0/adapter-evaluation-contract-2026-10-25.md), and [unfilled independent review](g0/dynamic-inquiry-independent-review.md).

## The original question, preserved verbatim

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

Do not replace this with "better answers", "forgotten context", "extra RAG", or "better memory". A compression-retention result would cover **one operational prerequisite** for one hypothesized mechanism (H3), not the second clause of the thesis.

## Precisely what was reduced

**Narrow research hypothesis, not a finding:** given a candidate recorded *before* later information arrives, can a separate, weightless Shadowseed record preserve and later retrieve it across a compression boundary more reliably than equally budgeted ordinary memory or strong active recall?

Decompose it into separately falsifiable outcomes:

- **P1 / preservation:** Is an earlier candidate still retained as a distinct, source-attributed record after a compressed history replaces the visible history?
- **P2 / later access:** Can the same model retrieve that record upon a relevant but differently worded later cue, without accepting irrelevant records in no-opportunity cases?
- **P3 / incremental effect:** Do actual Shadowseed candidate records outperform ordinary notes, full-history replay, independently searchable embeddings, and strong deliberate model recall **after equalizing information, calls and context/token budgets**? A tie or win for ordinary notes counts **against** a unique Shadowseed benefit.
- **Not answered:** Did the candidate arise outside ordinary generative selection? Did its preservation generate a genuinely different subsequent research question? Did the space of possible relations change? None follows from P1–P3.

Anchoring and context compression are distinct potential *moderators*. Do not say newer models are more anchored without direct model-comparative evidence. Embedding retrieval may itself prefer conventional, semantically frequent hypotheses and miss rare or non-obvious relations. Recurrence and TTL may also cause loss; their current production behavior is not to be changed to rescue a pilot.

## Phase 0 now executable: synthetic, OFFLINE mechanics only

Code:
- [Canonical-manager research harness](../../../research/src/shadowseed_research/benchmark/compression_retention.py)
- [Author-made calibration fixtures](../../../research/fixtures/compression_retention_v0.json)
- [Negative, parity, and Gate-boundary tests](../../../research/tests/test_compression_retention.py)

The harness creates **investigator-authored**, weightless candidates using the existing SSLManager and SeedOrigin. It uses the existing vectorstore and the same configured embedder for ordinary notes, Shadowseed candidates, sham notes and exact-target ablation. It carries a supplied, investigator-written summary across the boundary. No summarizer is run. No user or real model output is used; the output is not an LLM efficacy experiment. The answer key is used only to score each result and to select the explicitly labeled *diagnostic* ablation.

### Synthetic arms and explicit fairness limits

| Arm | Input available after the authored compression | Meaning in this offline test |
| --- | --- | --- |
| Compressed-only | A prewritten summary, with **no model tasked to answer** | Logging and shape check, not a retrieval accuracy score |
| Ordinary notes | Same later query, same embedder, fixed number of ordinary notes | Demonstrates whether a normal note would have preserved the hypothesis |
| Shadowseeds | Same later query and embedder, canonical weightless candidate records | Tests existence/retrieval plumbing only |
| Sham notes | Same number of unrelated notes and query | False-context/false-relevance check |
| Candidate ablation | Identical seed store except the investigator-identified target text is replaced by a neutral placeholder | Mechanical sensitivity check, NOT a prospective blind causal estimate |

Memory **slot counts and word caps** are equal, but this is **not** equality of provider tokens, model calls, information quality, or candidate-selection effort. The investigator chooses what notes and candidates contain; a synthetic "Shadowseed win" can be trivially engineered by giving only Shadowseed the relevant sentence. The parity fixture explicitly gives an ordinary note the same hypothesis to catch this mistake.

Four illustrative cases include a false initial interpretation, an ordinary-note parity case, a no-opportunity negative, and a dependency reframe. The topic-vector test adapter deliberately guarantees simple matches to verify program behavior; it is not a validated semantic embedder. The CLI uses the repository's lexical fixture embedder; remote backends are refused by the offline CLI. Programmatic injection of a separately authorized embedding function is possible and must disclose its model and budget.

Run without credentials:

    uv sync --locked --extra test
    uv pip install --python .venv/bin/python --no-deps -e ./research
    uv run --no-sync python -m pytest -q research/tests/test_compression_retention.py
    uv run --no-sync python -m shadowseed_research.benchmark.compression_retention --fixtures research/fixtures/compression_retention_v0.json --output /tmp/shadowseed-retention-offline.json

The generated report labels itself *offline_plumbing_only_not_efficacy*, records a SHA-256 of the fixture, counts **zero** model calls and **zero** authority changes, records candidate IDs and score, and explicitly leaves downstream answer/new-question outcomes unmeasured. These synthetic fixtures are **public calibration material** and may never be promoted to sealed study holdouts.

## Phase 1 proposed, not implemented or authorized

1. **Source actual candidates prospectively** in long tasks from a pinned capable model. Freeze the T0 output, repeated ordinary sampling distribution, detector prompts and candidate IDs *before* seeing the later cue. Preserve negative/irrelevant and singleton rare candidates. Never label an omitted output as model-internal impossibility.
2. **Generate real compressions** with a pinned summarizer and fixed budgets, logging full input/output and independently checking which information the summary discarded. Do not use investigator-authored summaries as efficacy evidence.
3. **Randomize early anchoring cues**: plausible initial explanations versus neutral context, then reveal the same new observation. Measure whether the stored candidate is accessed and subsequently tested, not only mentioned.
4. **Fair strong-model arms**: ordinary repeated sampling, deliberate exploration, ordinary notes including searchable embeddings, full-history replay (reported with its actual cost), candidate memory, and exact-candidate sham/ablation. Pin model revision, sampling, prompts, total calls, input/output token costs, tools, feedback, and available context. Budget match for direct causal comparison; report unmatched full-history replay separately.
5. **Independent outcomes**: (a) recorded preservation, (b) relevant but non-redundant later retrieval and false activations, (c) independent judges' assessment of newly proposed *testable* questions, (d) whether any specific candidate causally enabled a later question rather than merely improved a response.
6. **G0 review before live Q1/Q2 work**: independent construct/method and technical reviewers must approve a version-pinned independent evaluator, unscripted question admissibility, negative cases, sequestered holdouts created *after* preregistration, power/uncertainty plan, ethics and cost limits. No paid model run or proof claim before approval.

### Explicit stop / falsification conditions

- Ordinary notes, retrieval or strong self-critique equal or beat Shadowseed under matched resources: **no unique retention advantage established**.
- Semantic false merges, excessive false reactivations, forgotten rare candidates or prompt-injection influence overwhelm correct recall: **candidate mechanism fails or requires revision**; do not fix by weakening the Gate.
- A candidate survives but contributes no independently checkable later investigation: **P1/P2 may hold; broader Q2 still untested**.
- A model can recover the same candidate from a compressed summary without Shadowseed: **no retained-information advantage in that case**.
- Invalid summary, leaked labels, unmatched information budgets, or author-written second question: **invalidate the affected efficacy comparison**.

**Decision:** This work adds a small, reproducible research fixture harness alongside existing SSL technology. It does not introduce a new runtime memory subsystem, a new accepted ADR, a Gate exception, a TTL/TrTL change, a new product feature, or a conclusion about the original two-part thesis.
