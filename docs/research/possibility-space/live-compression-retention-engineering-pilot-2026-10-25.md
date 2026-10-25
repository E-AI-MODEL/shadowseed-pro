# Live GPT-5 compression-retention engineering pilot (2026-10-25)

> **Status:** bounded exploratory execution, not scientific efficacy validation. The original [two-part thesis](../possibility-space-thesis.md) is unchanged. The [independent G0 review](g0/dynamic-inquiry-independent-review.md) is **UNFILLED**. This pilot does not demonstrate Q1, Q2, or a unique Shadowseed advantage.

## Why this does NOT replace the research question

The original thesis asks about possible relations beyond typical language-model generation, and whether new possibilities alter which subsequent investigations become conceivable. This experiment tests an engineering prerequisite: can an actual model-generated, unverified alternative be stored separately from a shortened conversation, retrieved by a real embedding query after new fictional evidence arrives, and made available to the same model? Retention and model mention alone do not demonstrate a changed possibility space.

## Precommitted execution

- Three public, investigator-authored fictional cases: sensor drift, registration decline, and an unrelated later question (negative control). [Frozen fixtures](../../../research/fixtures/live_compression_exploratory_v0.json).
- GPT-5, low reasoning, at most 2,200 output tokens per call. At most 30 language-model calls (four first-stage calls and six follow-up calls per case), 110,000 combined tokens and three embedding requests to text-embedding-3-small. No automatic retries.
- **T0 first for ALL cases:** the model produces its first answer, two alternatives, two ordinary notes and a 65-word compression. Later observations never appear in T0 prompts. The generated first-stage records are frozen and hash-bound before any follow-up call.
- **T2 after freeze:** same later observation for compressed-only, ordinary notes, weightless Shadowseed memory, first-candidate ablation, deliberate recall, and full-history replay. The notes and candidates use the same real embedder and in-memory vector index with threshold 0.30 and top-1 retrieval. Candidate birth passes through the existing SSLManager and SeedOrigin contract; a candidate rejected at intake cannot appear in the Shadowseed arm.
- Ablation replaces the first T0 candidate, selected before later evidence, with neutral text. Full-history and deliberate-recall arms have unequal input or instruction budgets and must be interpreted separately.
- All follow-up replies contain an answer, one next question, and uncertainty. Keyword matches and negative-topic intrusions are mechanical cues, not scientific correctness or independent novelty judgments.
- Code: [bounded model run](../../../research/src/shadowseed_research/benchmark/live_compression_retention.py), [offline checks](../../../research/tests/test_live_compression_retention.py), [one-shot GitHub workflow](../../../.github/workflows/live-compression-retention.yml).

## Security, cost and data controls

The GitHub workflow triggers only on a push changing its own workflow file on the exact research branch. It is not scheduled or automatically repeated. Offline regression tests must pass before the paid-model step. The model job uses the existing GitHub Environment named **OpenAI key** and reads its OPENAI_KEY secret as OPENAI_API_KEY only at process runtime. The secret is not written into the repository or artifacts. The workflow uses read-only repository permissions. Fictional research results are uploaded even on failure.

Output artifacts contain frozen-t0.json and result.json, with raw synthetic model output, prompt hashes, provider model IDs and recorded token usage. A partial or invalid run remains a partial or invalid run. No provider-retry loop, automatic model-judge ground truth, additional Gate authority or change to trace, weight, TTL or TrTL is permitted.

## What we may conclude

**May inspect:** candidate retention after actual model summarization, semantic recall after a late observation, ordinary-note parity, spurious recall on a negative case, model questions proposed after recall, and usage/cost proxies.

**May not infer:** performance under actual context-window overflow, causal anchoring reduction, a unique effect of Shadowseed, independent semantic novelty, new possibilities arising, or verification of the original two-clause thesis. Cases and scoring hints are public and investigator-authored, not held out. Memory slots and word limits do not equalize total calls, content or prompt tokens. No independent human review has taken place, and G0 remains NOT PASSED.

This engineering pilot can justify developing a properly preregistered study only after separate technical and methodological reviewers validate general inquiry criteria, strong model/ordinary-memory controls, protected new holdouts, cost matching and human assessments. Failure and ordinary-memory equality are acceptable outcomes.
