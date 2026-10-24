# Shadowseed — corrected Q1/Q2 research route after the first live pilot

> **Status:** revised exploratory research protocol; **not implemented**, not preregistered, and not evidence of efficacy.
> **Decision date:** 2026-10-25.
> **Preserves:** [the foundational thesis](../possibility-space-thesis.md), [original discussion and corrections](conversation-record-2026-10-24.md), [course elimination](course-elimination-2026-10-24.md), [literature boundaries](literature-map-2026-10-24.md).
> **Trigger for revision:** [PR #220](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220), especially [24-call GPT-5 feasibility attempt](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40136015917). The experiment was a *fixed-edge gap finding* assay with incomplete outputs. Preserve its raw observations; do not relabel it as either Q1/Q2 success or failure.

## Non-negotiable original research question (verbatim)

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

**Both questions matter.** This protocol cannot change the objective into completeness checking, RAG, simply generating more answers, or finding a bridge in a graph whose relation types and rules are already fixed.

## What the first attempted experiment taught us — and what it did not

In the first 24-call GPT-5 run, **16/24 outputs completed as parseable JSON** and **8/24 were incomplete at the token ceiling**. Ordinary or deliberate prompts already produced some correct missing links; the supposedly Shadowseed-like prompt was not an implemented weightless memory mechanism. The follow-up scorer sometimes penalized correct autonomous deductions because the upstream JSON had been truncated.

**Consequences:**
- The provider credential and API path work; authentication is **not** the blocker.
- Budget or JSON formatting can be repaired as *engineering*. Doing so would **not** repair what was measured.
- Connecting two already defined nodes adds a path inside an unchanged graph. It is **not** evidence of new relation *types*, let alone a changed space of what can subsequently become conceivable.
- With one ordinary sample, absence from output cannot establish what the model could or could not have selected.
- Comparison prompts with unequal visible context and empty/invalid upstream candidates cannot support causal claims.
- The original artifact and failures remain intact. **No rerun of v0 is authorized as a Q1/Q2 efficacy test.**

## Scope: three things that must stay distinct

| Distinction | Operational meaning | What must not be claimed |
|---|---|---|
| **Q1 — selection vs exploratory access** | A distribution of ordinary responses is empirically sampled; a controlled procedure may access meaningful relational candidates that ordinary generation *in the measured budget* did not select | The model never knew, cannot generate, or contains an objectively empty representation |
| **Q2 — frame/schema transformation** | A candidate changes the *rules for composing, typing, relating or describing further concepts*; a frozen independent checker can establish which **relation classes** were expressible under the old and new formal constraints | A newly connected edge within the old schema is transformation, or a mathematical softmax support changed |
| **Coupling — intertemporal possibility formation** | A candidate originating from Q1 exploration is preserved *without knowledge authority*, and later enables a validated Q2 transformation and subsequent unprompted/unseen downstream relation classes | More text, more prompts, or labeling one prompt “shadow” demonstrates an SSL effect |

The observed **reachable possibility space** (under explicit rules, model, context and compute budget) is the initial operational target. A claim about model-internal mechanisms requires additional open-weight/logit/causal evidence. A claim about real-world knowledge needs external domain validation. Do not silently substitute either.

## Proposed experiment: discover a transformation, not a missing edge

### Before any live model call — independent task design

Construct **at least two unrelated constrained relational worlds** with independent validators. For each world, create:
- A *before-state* with explicitly specified concept vocabulary `V0`, permissible relation **kinds** `R0`, composition constraints `C0`, and a checker that can enumerate or conservatively prove reachable relation types.
- **Observations and anomalies** that permit several interpretations; do **not** explicitly provide the desired transformation, its label, or the held-out target relation to the model.
- A small **bounded language of admissible transformations** `T` (e.g. introducing a conditioned relation, changing a typed operator's arity with independently justified consistency conditions, or defining a compositional relation that introduces a distinct consequence). The system must propose a transformation from the observations; the test author must not give it to the model.
- A held-out **downstream challenge** where a transform may render **previously inexpressible or invalid relation classes** expressible and externally checkable. The challenge must not be a simple paraphrase of the enabling candidate or a path made valid by arbitrary rule weakening.
- Independently validated *negative worlds* with anomalies for which no meaningful sanctioned transformation exists; a free-form “invent a rule for anything” answer must fail.
- **Wrong-rule** controls, random valid transformations, exact-information-matched irrelevant candidates, and unchanged-rule controls. A rule whose mere relaxation guarantees “more links” counts as a trivial expansion and cannot meet the primary outcome.

The task designer must explicitly distinguish **intensional change** (new grammar/constraint for relations) from **extensional change** (additional links of an existing kind). Record the evaluator and challenge construction **before** seeing model outputs, use separately held-out worlds, and avoid hand-selecting only examples on which a shadow prompt succeeds.

**Example of a permissible type of mechanism, not a validated case:** A system has relations that are timeless. Observations motivate a *temporally conditional* relationship with an independent consistency rule. A proposal introducing an event-conditioned operator can create downstream questions that were not expressible in the timeless schema. The independent checker must verify that the proposed operator is coherent under predeclared rules, not just accept new vocabulary because the model mentioned it. The specific operator must not be disclosed as a target in the model prompt.

### Stage Q1 — interrogate probability-oriented selection

1. Fix a **strong model snapshot**, input text, output shape, decoding parameters, inference budget, model calls, and temperature. Record these in an immutable run manifest.
2. Draw a **predeclared repeated ordinary-generation sample** before introducing any exploratory prompt. This measures **observed selection frequencies** of relation families, not the full probability distribution or hidden “absence”. A limited feasibility sample may be smaller; never call it a population estimate or a claim of impossibility.
3. Compare candidate generation using deliberate counterfactual exploration, semantic diversification, and an explicitly defined shadow candidate operator **under matched tokens and calls**. Separate external prompt diversification from model-internal measurement: if all variants just use different instructions, the result is *behavioral*.
4. Require blinded assessment of **semantic/structural relation families**, not lexical variants or embedding-only clustering. Preserve candidates occurring once; recurrence is not truth.
5. Optionally, with an open-weight model, check conditional likelihoods, controlled representation steering, and causal interventions. Do **not** invent an “anti-embedding vector”; if no internal test was conducted, explicitly say so.

**Q1 gate:** The strongest matched model baseline must fail to reach at least some independently meaningful **candidate relation families** in the fixed budget that the experimental procedure reaches reproducibly. Otherwise no incremental Q1 benefit has been shown. If this is observed only via prompt variations, attribute the gain to the **procedure**, not to a proven internal absence detector.

### Stage Q2 — can a relation change what comes next?

1. In a **separate observation window**, freeze the proposed enabling candidate and a no-transformation control. Keep the second-stage held-out challenge unseen until after candidate proposals have been committed.
2. Let the system propose and explain a **relation-schema / conceptual-frame transformation**, not merely name two existing nodes to connect.
3. Apply an **independent validator** to the proposed transformation and the downstream relation class. Check admissibility, nontriviality, novel structural expressibility relative to `V0/R0/C0`, and consistency under post-transform constraints.
4. Verify the purported downstream relation type is **not expressible under the original schema**. Log any case where it is just a renamed existing relation, an obvious consequence of an added arbitrary rule, or an answer directly supplied by the observation.
5. **Ablate the exact enabling candidate**; substitute a same-length irrelevant candidate and a random valid transformation; enforce equal context and inference budgets. Assess whether the downstream relation family genuinely depends on the candidate **and** on the proposed transformation.
6. Report **separately**: new syntax, admissible new relation *kind*, new testable claim, and independently verified novel real-world fact. The experiment may establish one while leaving the others entirely unproven.

**Q2 gate:** The checker establishes an independently valid, *nontrivial change in relation classes* that causes the downstream effect, survives withheld tests, and is lost or predictably altered under candidate/transform ablation. An increased count of links does **not** satisfy the gate.

### Coupled stage — does a weightless shadow add anything?

Use at least five controlled arms with the **same base model** and matched total exposure, prompt budget, time, tool access, and evaluation calls:

| Arm | Input/memory process | Purpose |
|---|---|---|
| **A** | Ordinary generation; later follow-up with equal context budget | Measures ordinary eventual access; NOT a weak artificially starved baseline |
| **B** | Strong deliberate alternatives and counterfactual search | Most demanding non-shadow prompt baseline |
| **C** | Same candidate-generation effort + ordinary persistent notes | Controls memory and accumulated context |
| **D** | Same generation budget + explicit weightless candidate preservation, relation-aware reactivation, and transformation testing | **Actual experimental shadow mechanism**, distinct from merely calling a prompt “D-shadow” |
| **E** | Same as D but candidate shuffled/ablated or replaced by matched irrelevant proposal | Candidate specificity and causal control |

Each arm sees the same revealed future observations; **no arm gets another arm's prior answer for free**. Preserve candidate provenance, retain failures, and do not promote hypothetical seeds to production truth or action authority. D must implement an actual **cross-turn weightless state** in an isolated research harness before an SSL-specific claim is tested; the shipping Gate remains unchanged.

**Coupled gate:** A relation independently assessed as meaningfully outside the *measured ordinary selection* at time `t0` is preserved without authority; at `t1` it causally enables a valid relation transformation and independently checkable downstream relation classes **more often than the strongest matched controls**, with successful exact-candidate ablation. This is an *operational* Q1+Q2 result, not proof of fundamentally changed fixed-model weights.

## Engineering/measurement requirements before first repeat

- **Budget:** Calculate maximum calls, tokens, and costs *before* enabling a paid run; make the model job **manual opt-in**, not automatically triggered by documentation or experiment edits.
- **Completeness:** Record output-status and usage for every call; use explicit structured output/reasoning settings supported by the pinned model; ensure output-token budgets cover both reasoning and visible answer. Stop invalid attempts early, and never salvage truncated JSON as a success.
- **Denominators:** Count *all* tasks and calls, including invalid, zero-candidate, unparseable, API failures, refusals and held-out failures. Report opportunity-level and model-call-level counts separately.
- **Scoring:** Distinguish `candidate_discovery`, `candidate_validity`, `transformation_validity`, `new_relation_kind`, `downstream_prediction`, `independent_downstream_discovery` and `candidate_specific_ablation`. **Do not penalize correct autonomous discovery as a false claim merely because a preceding candidate was unavailable.**
- **Leakage:** Hide fixture solutions, desired transformation classes and downstream targets from model prompts. Verify on an unseen task family. A model-generated rationale is not independent validation.
- **Models:** Start with a strong frontier baseline; add stronger open-weight and, where relevant, small reference models. Report configuration differences; no model-size causal law from uncontrolled comparisons.
- **Human oversight:** Blinded domain review is necessary for meaningful semantic novelty and scientific relevance; formal oracle results alone do not prove real-world novelty.
- **Safety:** Existing Gate and point-of-use authority controls stay intact. No disclosed key in repository, logs, or chats.

## Decision table: when to proceed

| Gate | Pass requirement | If it fails |
|---|---|---|
| **G0 — Construct validity** | Two independent worlds, genuinely different relation kinds, withheld checks, negative controls and verified nontrivial transformations | **Stop.** Do not make API calls. Redesign tasks |
| **G1 — Q1 observability** | Repeated ordinary-generation selection measured, alternatives controlled for budget and independent relation identity | Only behavioral comparison allowed, no “latent absence” claim |
| **G2 — Q2 validity** | Independent proof/verification of transformed relation kinds; cause-specific downstream ablation | The result is only search, prompting, or graph completion |
| **G3 — Coupled increment** | Actual weightless, longitudinal D arm outperforms strongest matched baseline; E/ablation separates candidate influence | Do not claim a unique SSL contribution |
| **G4 — Replication** | Held-out families, model-capability tiers, independently reviewed candidate relevance and registered exclusions | Preliminary feasibility only; no ADR or production changes |

**Research decision:** Return to the original sources and construct a test that can distinguish a **change in relational possibility-making** from merely finding a missing existing connection. Do not choose an anti-embedding architecture, a new seed schema, relaxed Gate, or an Accepted ADR yet.

## Provenance / future reading order

1. [Original hypothesis, literal Dutch wording](../possibility-space-thesis.md).
2. [Corrected historical course elimination](course-elimination-2026-10-24.md).
3. [Relevant theoretical and empirical studies](literature-map-2026-10-24.md).
4. [Earlier proposed experiment, preserved as original plan](first-discriminating-experiment.md).
5. [Live pilot PR and retained negative/invalid outcomes](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220).

**No new model experiment or concept-transformational validator was executed to create this revision.**
