# Shadowseed as an external epistemic LLM adapter — positioning candidate

> **Status (2026-10-25):** evidence-bounded *positioning candidate* and integration analysis, **not** a new accepted ADR, product feature, implemented research-discovery engine or efficacy result.
> **Proposal:** "Shadowseed as an LLM adapter, not an LLM improver" means an **external, model-independent research adapter** rather than a promise of universal LLM quality gain. Better answers may be a measured *secondary outcome*, never the entire thesis.
> **Implementation provenance:** [public ShadowseedEngine API](../../../src/shadowseed/engine.py), [engine integration guide](../../engine/README.md), [main product README](../../../README.md), [ADR-001](../../architecture/adr/ADR-001-validation-gate-authority.md), [ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md), [original generative vision](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md).

## The unchanged two-part question

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

## Verdict: qualified YES, without claiming a new model

The repository already implements a **model-agnostic candidate-memory/validation integration boundary**. The `ShadowseedEngine` API provides `prepare_turn` and `observe_turn` / `abort_turn`; the **host application** owns the language model, provider selection, credentials, actual generation and conversation history. The engine never calls an LLM itself. The Workbench is a client of the canonical `ShadowChatSession` runtime; do not imply it must use the external `ShadowseedEngine` facade internally.

A **separate research hypothesis** is that a weightless candidate from an ordinarily unselected generative direction might become investigable later and causally open *another* meaningful research question. This has **not** been established by existing Shadowseed experiments or the retired 24-call GPT-5 pilot.

### Avoid "adapter" terminological confusion

In the neural-network literature, "adapter" can mean **trainable additional layers** inside a model, e.g. [Houlsby et al. (ICML 2019)](https://proceedings.mlr.press/v97/houlsby19a.html). Shadowseed is **not** a LoRA/parameter-efficient fine-tuning method. Use **"application-level epistemic research adapter"** (Dutch: *modelonafhankelijke epistemische onderzoekslaag*) when precision matters. Do not suggest changing frozen model weights or directly reading a model's hidden thoughts.

## Responsibilities and boundaries

| Responsibility | Host / existing model | Implemented Shadowseed | Hypothetical separate research adapter |
|---|---|---|---|
| Provider, keys, model choice, user dialog | **Owns** | Does not own | Uses pre-authorized host calls |
| Text generation, sampling/logits where available | **Owns** | Never generates directly | Can *observe* samples; cannot assert access to internal knowledge |
| Uncertain candidate intake, lifecycle, trace, contradiction | Provides answer and source context | **Implemented** | May use isolated candidate provenance |
| `weight=0`, Gate-only authority and point-of-use relevance | Must honor instructions and permissions | **Implemented** | **Must not bypass** existing product Gate |
| Hypothetical experimental questions | May originate and evaluate proposals | Not a proven creative capability | **Research hypothesis**, only safe sandboxed tests |
| Independently verified external outcomes | Produces no authoritative evidence by default | Accepts source-bound signals via Gate | Independent query evaluator / humans; never model self-grading alone |
| Better final answers | May be measured | Conditional, scoped evaluation | **Not** the primary claim |
| New space of later investigable possibilities | Not established by model output | **Not demonstrated** | **Q1+Q2 research objective**, needs causal evidence |

### Correct process diagram (responsibilities, not a new runtime)

```text
Host application: owns model, prompt, history, credentials, allowed tools
         |
         v
Existing Shadowseed boundary: prepare / retain / observe
         |                 \
         |                  -> weightless candidate memory (no truth authority)
         v
Host calls selected LLM (model unchanged)
         |
         v
Host records response + independently attested evidence via Gate

[Separate sandboxed research design ONLY]
Q1 ordinary repeated sampling -> frozen candidate -> later independent test
                                              -> subsequent model-originated question
                                              -> matched baseline + candidate ablation
```

**Safety boundary:** Exploring a speculative idea in an isolated research environment is *not permission* to steer an actual user, submit unverified evidence, call expensive/unsafe tools or violate ADR-001/002. A test sandbox requires explicit, bounded permissions and no real-world consequential action.

## What "adds value" must mean scientifically

**Compare the same strong base LLM under equal budget, context, observed tool results, total calls and feedback.**

- **A:** ordinary generation plus full-history replay.
- **B:** strong deliberate/diversity-aware generation and active research with no Shadowseed.
- **C:** normal persistent notes and reminders, same candidate/context budget.
- **D:** *actually implemented* weightless cross-turn candidate retention in a research-only adapter (not a different prompt called "shadow").
- **E:** D minus or shuffled exact precommitted candidate; same information budget.

For **Q1**, measure observed ordinary selection of *meaningful relation/question families* through repeated baseline samples. A missing sample does not prove internal impossibility. For **Q2**, measure independent, prospected, causally **candidate-dependent later investigable questions**, not more strings, edges or "better answers". Report when strong baselines equal or beat the adapter. Credit authors, humans, independent validators and external observations separately.

**If D brings no extra Q1/Q2 result, the epistemic-memory/safety adapter can still be a valid product.** Conversely, a better answer is not automatically evidence of a changing possibility space.

## Research and engineering decision

**Keep current interfaces, accepted ADRs, Gate, TTL/TrTL, Workbench and product claims unchanged.** Adopt this as an **explicit candidate positioning**, not a production architecture mandate. Before a new paid run, vet existing independent open-ended research environments, rights, leak risks, tool budgets and the host/adapter interface; see [external environment review](g0/external-benchmark-feasibility-2026-10-25.md) and [adapter comparison contract](g0/adapter-evaluation-contract-2026-10-25.md).

The canonical question remains open, and its two clauses cannot be redefined by a convenient adapter API.
