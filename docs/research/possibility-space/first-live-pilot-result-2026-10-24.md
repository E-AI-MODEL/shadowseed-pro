# First real GPT-5 possibility-space pilot: result and failure analysis (2026-10-24)

> **Status: attempted real-model feasibility run; output incomplete; scientific inference blocked.**
> This document corrects the previous [offline-only instrumentation report](first-pilot-instrumentation-result-2026-10-24.md). It does **not** replace, rewrite or hide that earlier result.
> **Evidence:** [GitHub Actions run #40136015917](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40136015917) (workflow **failed**), [raw model artifact](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40136015917/artifacts/12576709359), JSON `model-pilot.json` within the artifact.
> **Code revision:** `468cd24cf79a1cb81fda8f0b8774760fb106ebb6`. **Environment:** `OpenAI key`; GitHub secret name `OPENAI_KEY` (value never disclosed). **Model:** `gpt-5`, Responses API, `reasoning.effort=low`, 900 maximum output tokens per call (inclusive of reasoning).
> **Scope:** three fictional typed networks; four first-stage prompt strategies (A/B/C/D); one second-stage question per strategy; 24 real model calls, no real-world research claims, no actual Shadowseed memory runtime.

## Grounded result — not an efficacy result

- `24` **real model requests completed**. The job obtained the environment secret and made requests; no credential or HTTP error was recorded.
- Only `16/24` responses produced completed, parseable JSON; `8/24` were marked `incomplete` and did not yield parseable JSON. All eight incomplete responses consumed **at or near the 900-token ceiling** (mostly `896`), with reasoning tokens consuming the budget and either empty or truncated visible content. This is a **pilot design/resource-budget failure**.
- `7/12` first-stage proposals parsed, `9/12` second-stage predictions parsed.
- GitHub Actions marked the `strong-model` job **failure** at the completeness check; raw data was uploaded successfully.
- `9,922` reported input tokens and `18,370` reported output tokens across the 24 model calls. **Token totals are not invoice costs.** No inferred dollar amount is asserted.

### Results per case/arm (descriptive only; do not rank arms from incomplete data)

| Synthetic case | A — ordinary | B — deliberate alternatives | C — ordinary notes | D — shadow-*prompt* |
|---|---|---|---|---|
| ARCHIVE | First-stage **incomplete**; later prediction incorrectly evaluated against an empty candidate set | Found the valid causal bridge; 2 new source-to-sink pairs in the formal oracle | Found the same bridge and 2 pairs; second-stage output incomplete | First-stage JSON **incomplete**, despite a visible partial proposal of the same bridge; second stage incomplete |
| LOGISTICS | Found the valid bridge; 2 new source-to-sink pairs; follow-up prediction correct | First-stage incomplete; follow-up predicted paths unsupported by the parsed candidate set | Found the same bridge and 2 pairs; follow-up prediction correct | Both stages incomplete |
| NEGATIVE | Correctly returned no legal links and no new paths | Correctly returned no legal links and no new paths (first stage reported incomplete in the original source? **see correction below**) | Correctly returned no legal links and no new paths | Correctly returned no legal links and no new paths |

**Exact source-corrected NEGATIVE details:** A, C and D completed both stages. **B first-stage was incomplete**, so B's empty candidate set is a parser/response failure, *not* evidence that it correctly abstained; its second-stage answer independently predicted no paths. The table's B cell must be read with this correction. Failure cases stay visible.

### Nontrivial protocol flaws beyond output length

1. **Q1 is not actually sampled as a distribution.** A is one ordinary generation only. Observing another arm return an edge missing from A does **not** mean it was outside what the underlying model could readily produce. No logits, probability sampling curve, controlled internal intervention, or accessibility estimate was collected.
2. **Q2 tests missing fixed-ontology links, not the emergence of new kinds of possible relation.** An allowed edge opening a formally reachable terminal route is a valid graph arithmetic check, but does not demonstrate changes in the space of *conceivable relational types*; it is particularly prone to collapsing into the omission-finder problem Shadowseed's thesis explicitly rejected.
3. **D is not an implementation of Shadowseed.** It is one exploratory prompt; there is no weightless longitudinal persistence, cross-turn competition, candidate lifecycle, or relation-schema transformation. **No result may be described as Shadowseed Pro failing or succeeding.**
4. **Second-stage leakage/false-positive scoring:** the follow-up prompt could infer a suitable bridge directly from the base network, even if the first stage produced no parsed candidate. A's ARCHIVE response and B's LOGISTICS response predicted real paths by imagining the missing bridge. The scorer marked the paths **false positives with respect to the empty submitted candidate list**. This is a mismatch between the follow-up instruction and the conditional evaluator, not independent proof of the model hallucinating. A later protocol must tie follow-ups to a strictly declared candidate, or separately score autonomous second-stage discovery.
5. **Unequal information exposure:** B/C/D received A's output (often blank due incomplete), whereas A did not receive an equivalent prior reference. This is not a fair causal comparison.
6. **Small hand-designed examples and one model:** even complete outputs would not justify capability scaling or a broad effect claim.

## Corrected interpretation

**The real API connection and model run worked; the experimental design did not produce interpretable Q1/Q2 evidence.** The main reason the workflow is red is the output/reasoning ceiling and resulting unparseable data, not the Environment secret.

Independently, on the subset of parseable outputs, the ordinary or deliberate model already identifies the useful type-compatible edges. **There is no observed incremental discovery unique to the D prompt.** Because D's relevant positive outputs were incomplete, that is an **inconclusive observation**, not a negative or superiority result about Shadowseed itself.

The successful negative oracle fixtures do not establish that model-mediated hypothesis expansion works. Likewise, `ablation_pass` in the graph oracle simply confirms that removing the single newly added link removes the corresponding path; it is not an LLM causal intervention.

## Research decision and next gate

1. **Archive this failed trial unchanged. Do not overwrite, relabel as green, or cherry-pick the surviving positive examples.**
2. **Do not blindly repeat the same missing-link benchmark with a larger output-token cap and announce progress.** A rerun may validate JSON/completion engineering but does not fix the Q1/Q2 construct mismatch.
3. First revise the independent research design to ask about *what ordinary probabilistic generation suppresses* (Q1) and *what relation-generation rules/frames could change* (Q2), with non-tautological held-out downstream tests. Include a fully capable ordinary model and equal information budget before an SSL implementation comparison.
4. If a limited rerun is used **only** as a plumbing/control check, increase the response budget or use a verified lower reasoning effort, record the change as a different protocol revision, and enforce structured parsing/conditional scoring. Do not use it as confirmatory evidence.
5. No Gate, agent authority, production model routing, existing accepted ADR or primary thesis changes are warranted from these data.

**Bottom line:** 24 live GPT-5 calls, 16 fully parseable answers, 8 incomplete due token ceiling, ordinary-model control already finding key edges. Our *first measurement design*, not the Shadowseed fundamental thesis, needs revision.
