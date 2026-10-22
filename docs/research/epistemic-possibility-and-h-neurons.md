# Shadowseed research doctrine: the model as an epistemic instrument

Status: **research alignment proposal** on PR #202, 23 October 2026.
This is not a new production policy, a demonstrated model-internal SSL signal,
or a replacement for ADR-001/ADR-002. Historical 4.5 and 4.6 sources, prompts,
runs and counterexamples remain unchanged.

## The question we had stopped asking

SSL asks a language model to do something other than simply finish its answer.
It uses the model's learned relational/completion capacity to **propose an
adjacent, unexpressed possibility**: an alternative connection, unresolved
boundary, counterfactual or interpretation that *could* have been expressed
in this context. The original vision's distinction is:

- "what could have appeared here?" is an **open search**;
- "what should have appeared here?" is an **omission checklist**.

Neither question reveals an objective, complete inventory of what is absent
from the model's weights. An unexpressed possibility is not necessarily unknown
to the model; "the LLM does not know" has at least two different readings:

1. the model has relevant representations/capacity but did not **activate or
   express** that direction in its actual answer;
2. the model **lacks** the information or cannot represent the relation.

Output-level generation cannot discriminate between those readings.
Do not repackage a plausible generated alternative as evidence of hidden
model knowledge, calibrated uncertainty or a measured latent state.

This distinction comes from
[the original generative vision](../../archive/source-docs/research/vision-generative-seeds.md),
[SSL 4.6](../../archive/source-docs/00_shadow_seed_learning_4_6.md)
and [ADR-002](../architecture/adr/ADR-002-epistemic-seed-contract.md).
ADR-002 is the accepted **runtime** semantic refinement: atomic candidates
can be gaps, doubts, unstated assumptions, alternative hypotheses or
investigable what-if relations, not only missing items.

## The technical doctrine is an epistemic design, not an answer-memory feature

**Birth:** One context-linked, atomic, investigable candidate is recorded
with trace above zero and weight exactly zero. This records an observation,
not the model's endorsement and not the candidate's objective value.

**TrTL:** A new, clean context can reactivate the trace of an existing
possibility. Semantic recurrence means *recognized again*, not *proven*;
the same source/SSL-derived answer must not manufacture independent recurrence.

**TTL:** A possibility not reactivated loses trace and can expire. Expiry
reflects the chosen memory horizon, not proof that a hypothesis was false.

**Gate:** A named policy evaluates typed support, contradiction and possibly
recurrence to control **authority**. The exploratory research policy can
consider recurrence, while the ordinary evidence-backed live policy requires
verified external support. Neither policy makes the candidate intrinsically
true. At use time, an independent authorization and relevance check still
control actual influence.

**Probes:** A weightless candidate may motivate a read-only validation search
where the result is not fed into an answer. Influence-bearing Socratic,
retrieval and dialectical actions remain governed by the effective policy
and point-of-use boundaries. Falsification is distinct from forgetting.

**Constellations:** Relations between multiple atomic candidates may suggest
a still-untested conceptual region; clustering or similarity cannot
transform hypotheses into evidence.

Do not redefine SSL as a list of reminders, a fact-checking engine, a
confidence calibrator or an automatic answer improver. Those may be
possible ancillary functions, not the research construct.

### Oordeelloos at birth does not mean unbounded input

Generation and intake may enforce structural admissibility: one identifiable
epistemic direction, attributable context, non-assertive formulation, no
fabricated facts posed as facts, no executable instructions/prompt leaks, and
bounded operational output. A candidate is *not* rejected at birth merely
because it lacks demonstrated originality, utility, high recurrence or a
reviewer's preferred answer. Those are later measurements, not candidate
authority. Recording a candidate is not agreeing with it.

The current **v0.7** prompt still says "worth keeping open" and "worth
preserving". These can induce a premature utility verdict. Fix this through a
separately versioned vNext prompt experiment rather than silently changing the
hash/version of v0.7 or retroactively relabelling existing bundles.

## What H-Neurons does and does not establish

Primary source: Gao et al., *H-Neurons: On the Existence, Impact, and Origin of
Hallucination-Associated Neurons in LLMs*, arXiv:2512.01797v2 (2 Dec 2025):
https://arxiv.org/html/2512.01797

Official implementation: https://github.com/thunlp/H-Neurons

**Directly demonstrated in the studied settings:**

- Internal feed-forward-neuron contributions, measured on answer tokens,
  contain predictive information about faithful vs hallucinated factual
  responses. Sparse L1-regularized classifiers select fewer than 0.1% of
  neurons in six studied model families/variants (4B through 70B).
- Scaling selected neuron activations in inference changes the studied
  **over-compliance** behaviors, including accepting invalid premises,
  misleading contexts and user disagreement. That is a causal **behavioral
  intervention**, not a demonstration that a neuron stores a proposition.
- Selected signals remain predictive in corresponding base models before
  instruction tuning, within the study's transfer design.

**Limits that must not be lost:**

- Hallucination association / over-compliance is NOT "reading the model's
  ignorance", identifying the missing relation in an answer, or observing
  epistemic counterfactuals directly.
- There is no single cross-model universal H-Neuron set; neurons are identified
  for a model/task with labeled data and a trained probe.
- Generalization is not uniform: for Llama-3.1-8B on the study's fabricated
  NonExist task, the H-Neuron classifier scored 43.1% versus 50.6% for the
  equal-size random-neuron comparator (Table 1).
- Sparse-feature prediction is not the same thing as semantic identification;
  causal scaling of a selected circuit is not proof that the desired SSL
  epistemic candidate exists internally.
- The paper explicitly warns that simply suppressing/amplifying H-Neurons is
  insufficient for robust hallucination reduction without hurting helpfulness.

**Why the result nevertheless matters:** The same model can be studied as
a *measurement substrate*, rather than only used as a fluent text generator.
It is meaningful to test an SSL hypothesis about internal representations,
but not to declare it verified from the H-Neurons result.

A separate, relevant 2026 causal study on confidence and abstention also
shows that internal signals can influence whether models answer or abstain
(https://www.nature.com/articles/s42256-026-01293-x).
That study measures confidence-guided behavior, not the SSL "unspoken
possibility" construct. Do not merge these variables.

## Two implementation/research levels must remain separate

| Level | Actual observation | What it can justify | What it cannot |
| --- | --- | --- | --- |
| L1: external SSL beside an LLM | Draft/question; proposed unspoken possibility; trace, TTL, TrTL, Gate and observed behavior | Whether the external epistemic lifecycle functions and whether candidates are useful under a specified review | That the LLM's hidden state encoded an unknown, or that it experienced curiosity |
| L2: model-internal research (Layer G) | Hidden activation traces on open-weight models, paired with independent, preregistered labels, counterexamples and causal controls | At most a scoped neural correlate/intervention for an operationally defined construct | A universal "ignorance neuron", direct truth, or automatic authority |

Hosted generation APIs often do not expose activations. A prompted
second-pass candidate generator is therefore L1 even when a frontier model
performs it; calling a prompt a "neural probe" is a category error.

### What SSL's own negative Layer G results mean

[The Layer G research record](../../archive/source-docs/research/laag-g-scoping.md),
[the study conclusion](h-neurons-conclusion.md) and the preregistered
Rounds 032–033 measured whether small probe models (up to Qwen2.5 0.5B)
linearly recover a **different model's dialectical maintain/reject verdict**
from selected activations. A suggestive Round-032 classifier did not pass the
multiple-testing correction and failed preregistered Round-033 replication.
That rules out a replicated signal **under that setup and scale**, not L2 SSL
in general. It also does not test whether unexpressed, coherent relations
have a distinctive hidden representation. Do not revive the same small-model
probe without a new preregistration.

H-Neurons studied larger models and differently constructed response-grounded
labels, internal read locations and interventions. Their positive result
does not overwrite our valid null result, nor does our null falsify theirs.

## Research decisions for PR #202

1. **Keep the twelve v0.6/v0.7 short cases as smoke/regression only.**
   They test prompt format, parser, explicit injection boundaries and
   appropriate abstention. The variants have different objectives;
   candidate counts or 3B/7B A/B wins cannot approve SSL's philosophy.
   Preserve all original runs, hashes, versions, raw artifacts and negative
   findings. A failed or recognizable blind comparison stays failed.
2. **L1 open-set study comes first:** sample natural, context-rich,
   multi-turn conversations with capable models, including fully adequate
   answers and unasked adjacent conceptual pathways. Accept atomic and
   attributable candidates without a pre-birth usefulness label. Analyze
   trace changes, clean vs contaminated recurrence, TTL loss, TrTL
   reactivation, contradictions, Gate events, unauthorized influence and
   when a potential remains legitimately silent. Keep candidate creation,
   judged utility and answer-level effects separate.
3. **Compare only when the claim needs a control:** For answer effects,
   pair the *same* strong generation model and pre-turn state with SSL-off,
   and include a simple external memory alternative if claiming a uniquely
   better memory mechanism. Inspect opportunities with no promotions and
   null/no-op sessions too. A detector v0.6 control is not an SSL-off control.
4. **Define L2's target before probing:** e.g. whether an independently
   reviewable, coherent but **unexpressed** relation can be identified from
   activations *before* it is supplied as a candidate. Separate this from
   hallucination, confident guessing, refusal, ordinary lexical difference
   and an independent judge's post-hoc verdict. Freeze target labels,
   balanced negatives, extraction tokens/layers, model revision, split,
   permutation/multiple-testing plan and reviewer blindness before data
   collection. Hold out topics, sources and prompts. Test a suitably capable
   open-weight model; H-Neurons' 4B–70B range is context, not a magic
   SSL parameter threshold. Consider interventions only after a replicated
   predictive signal, with collateral-behavior controls.
5. **Gate remains untouched in this correction.** Detector scores, neuron
   activities, generated candidates, recurrence and retrieval presence are
   observations, not promotion shortcuts. No model family or larger model
   gains authority by reputation.

## Claim boundary and next acceptance gate

The current SSL lifecycle/Gate mechanics are implemented and tested. Open
questions remain about the quality of counterfactual candidate generation,
the correspondence between output omissions and model-internal signals, and
the downstream value of interventions. **Green CI checks mechanical
integrity, not a model-internal epistemic discovery or general SSL
efficacy.**

PR #202 stays draft until source-level compatibility, representative
open-set L1 evidence, admission/safety review and the updated research
protocol are assessed. L2 is explicitly a separate study, not a hidden
prerequisite for shipping the external L1 engine.

## Source hierarchy and provenance

- Canonical historical intent: [SSL 4.5](../../archive/legacy/docs/00_shadow_seed_learning_4_5.md),
  [SSL 4.6](../../archive/source-docs/00_shadow_seed_learning_4_6.md),
  [generative vision](../../archive/source-docs/research/vision-generative-seeds.md).
- Accepted runtime semantics: [ADR-001](../architecture/adr/ADR-001-validation-gate-authority.md),
  [ADR-002](../architecture/adr/ADR-002-epistemic-seed-contract.md),
  [ADR-003](../architecture/adr/ADR-003-contaminated-observation-boundary.md).
- Tested technical limitations: [Layer G null](h-neurons-conclusion.md)
  and [PR #202 protocol](inquiry-first-acceptance.md).
- External precedent: Gao et al. (2025), arXiv:2512.01797v2, **not**
  an SSL validation experiment.
