# G0 v3 candidate — prospectively generated inquiry, not a prewritten answer chain

> **Date:** 2026-10-25. **Status: PROPOSED, NO INDEPENDENT APPROVAL, NO MODEL RUN.**
> **Grounding:** [v1 rejection](internal-adversarial-audit-2026-10-25.md), [v2 self-check and blocked construct](v2-review-and-selfcheck-2026-10-25.md), [original thesis](../../possibility-space-thesis.md), [first-principles study](../first-principles-reorientation-2026-10-25.md).
> **Purpose:** Define a research route in which a model must **originate a question**, not just solve the question the researcher has already written.

## Unchanged original two-clause research question

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

## The crucial move

The first two cases embedded the next step in the answer key. The alternative examples (noncommuting transformations, synergistic XOR measurement) improve the validity of negative controls but remain familiar mathematics, program synthesis or feature construction. **Making a benchmark chain longer does not make it open-ended.**

We therefore need an environment with *general independent rules for testing a large class of unanticipated, model-proposed questions*. The evaluator need not anticipate every good question, but must be able to assess each submitted question **without using that model's own judgment as the truth criterion**. Open-ended claims outside a bounded interpreter need independent human/domain judgment.

## What one run would have to demonstrate, separately

1. **Q1 selection:** Repeated ordinary generation at frozen model/decoder/context/budget establishes which *meaningful candidate-question families were observed*. An alternative procedure can be compared at the **same** cost. No claim about "model did not know X" from an omitted output.
2. **Untrusted memory:** A candidate is retained with provenance and **weight=0** until existing authority policy allows influence. Compare with ordinary notes and full-history replay; never silently bypass Gate or alter production state.
3. **Q2 new inquiry:** At T1, a candidate is used to **propose an experiment/question not supplied in the task**. A separate independent executor or reviewer validates whether it distinguishes competing possibilities under declared constraints.
4. **Later opportunity:** At T2, actual findings allow the model to **formulate another, different research question** that was not scripted at T0; at T3, a fresh independent check evaluates that question and any claimed new decision/test it opens.
5. **Causal specificity:** A/B strong-model exploration and C ordinary notes see the same budgets and tools as D actual weightless persistence, and E shuffled/ablated candidates. If capable baselines find the same novel inquiry, no distinctive Shadowseed mechanism is demonstrated.

### No prewritten ideal question

At T0, the prompt must **not** contain the eventual question name, a target transformation, a toy exercise with a single correct link, or hints to invent alternatives. Each candidate proposal is frozen **before** feedback. The independent evaluator can reject bad, tautological, inaccessible, unsafe, redundant and merely renamed questions.

**Important limit:** In a synthetic world the *author still defines the laws and affordances*. A model may discover them but does not create reality. Credit author, tools, human reviewers and model separately.

## Two distinct environment classes to *audit*, not yet to implement

### E1 — bounded interactive mechanisms

An independently seeded black-box world exposes safe elementary observations and bounded interventions. It includes hidden state or causal rules, multiple reasonable hypotheses, sterile cases, misleading correlations and effects of sequential interactions.

A model may propose *any admissible bounded experiment or novel distinction*, rather than selecting from the author's list of target questions. The independent interpreter returns actual observations under the hidden rules. A later held-out environment change tests whether its earlier insight gave a meaningful different way of investigating, not just a longer sequence of existing queries.

**Null:** A strong ordinary model, sufficient search, or an existing classical active-learning strategy may generate the same question; that result must be recorded. An obvious `p∘q` versus `q∘p` order test is an **easy calibration item**, not evidence of novel conceptual-space change.

### E2 — bounded evolving observation/instrument world

An independent simulator permits combining already available sensors into candidate measurement operators and later gathering new observations. Candidate derived measurements are **not assumed useful**: the model must give an independently checkable reason to study them using available weak evidence, and unseen data must verify a nontrivial discriminating consequence.

A *subsequent, separately held-out phenomenon* may or may not be investigable using the validated measurement. The model must originate the next question **before** seeing the target result, under identical opportunity/budget constraints.

**Null:** Synergistic XOR examples and familiar feature-interaction discovery are **standard positive controls**, not new-possibility proof. Duplicate sensors, pure noise, spurious correlations, a direct original measurement and nonpredictive downstream worlds must reject unsupported effects.

## Planned controlled arms

| Arm | Description | Equalized factor |
|---|---|---|
| A | Strong ordinary model, repeated sampling, later normal deliberation | Base model, context, token/call budget and tools |
| B | Best deliberate/diversity-aware reasoning and counterfactual exploration | Prompt/search strength without SSL |
| C | Ordinary persistent notes and full-history replay | Extra context and memory |
| D | **Actual** isolated weightless cross-turn candidate store; no automatic authority | Hypothesized SSL-specific process (not a renamed prompt) |
| E | D with precise candidate removed, shuffled or substituted with matched irrelevant notes | Causal role of individual candidate |

No arm receives another arm's answer for free. Same number of tool observations, permissible experiments and later feedback. Return all attempts, including null candidates, invalid experiments, run failures and extra exploratory costs.

## Independent success/failure criteria

A reviewer/evaluator must distinguish **observed selection**, **valid candidate**, **independently executable investigation**, **new subsequent question**, **validated second-order consequence**, **candidate-specific ablation**, and **strong-baseline increment**. Never combine these into a single "creativity score".

Mandatory conditions to advance beyond G0: an environment supports many admissible unanticipated queries with a **general validator**; at least one true negative/no-opportunity condition; independently judged nontriviality; strictly separated time-stamped candidate, observation and new-question stages; new sequestered held-outs created after preregistration; explicit cost budgets and an external veto if proposed novelty is only classic algebra, planning or feature construction.

**G0 must fail** if the author's future question is written in the prompt/key, if the model is just given a new capability via tool access, if a new predicate counts as novelty by definition, if a strong matched model already generates the same query with no shadow, or if untrusted text becomes its own evidence.

## Research decision

- **v1 F1/F2:** stop as thesis tests; preserve historical controls.
- **v2 F3/F4:** formal examples survive arithmetic self-check, but they are recognized ordinary compositional/feature engineering cases; retain as challenger/control candidates.
- **v3:** proposed *method* for prospectively generated inquiry; **not a proven design or approved experiment**. It is still possible an external reviewer will conclude that this is just ordinary open-ended active learning.
- **Next task:** independent construct review of E1/E2 and a separate evaluator author who can assess unscripted questions. **No paid API calls, runtime code, weakened Gate or accepted ADRs until G0 construct validity is independently established.**

No model evidence, approval or production functionality is asserted in this file.
