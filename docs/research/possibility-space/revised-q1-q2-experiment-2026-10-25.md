# Shadowseed — corrected Q1/Q2 research route after the first live pilot

> **Status:** exploratory **amended research protocol (2026-10-25)**; not implemented, not preregistered, and not efficacy evidence. The [first-principles review](first-principles-reorientation-2026-10-25.md) corrects its earlier over-narrow claim: a new relation type is **one optional Q2 instance**, not the mandatory definition of a changing possibility space.
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
| **Q2 — change in later investigability** | A candidate alters a working **interpretation, condition, meaning, dependency, admissibility rule, question or available experiment**; independent checks test its downstream effects | New predicates are required, or mere output changes establish fundamental new model capabilities |
| **Coupling — intertemporal possibility formation** | A Q1-origin candidate is retained *without authority*, later enabling a genuinely new **question, distinction, test, relation or next action** under declared working conditions | Extra context, repetitions or a prompt labeled 'shadow' demonstrate an SSL effect |

The observed **reachable possibility space** (under explicit rules, model, context and compute budget) is the initial operational target. A claim about model-internal mechanisms requires additional open-weight/logit/causal evidence. A claim about real-world knowledge needs external domain validation. Do not silently substitute either.

## Proposed experiment: discover a transformation, not a missing edge

### Before any live model call — distinguish mechanisms rather than impose an ontology

**G0 must not presuppose one ontology.** The [first-principles synthesis](first-principles-reorientation-2026-10-25.md) distinguishes generation support, observed selection, constructive expressibility, formal admissibility, and practical investigability. A **new relation kind** is optional, neither required nor automatically sufficient.

Develop at least **two independently adjudicable, qualitatively different families**, with positive, negative and tempting-invalid cases:
- **F1 — Reframing with unchanged relation vocabulary.** Candidate alters a context condition, interpretive distinction, dependency or time assumption. A *newly testable comparison or question* is assessed against a predeclared frame and withheld follow-up. Do not score mere paraphrase, extra reasoning time, or explicit hinting.
- **F2 — Formal change of constraints/composition.** Define a finite before-frame and consistent admissibility conditions. A candidate may propose a meaningful transformation of composition/rules, with independently checkable unseen consequences. Arbitrarily allowing every rule does not count; adding a new predicate alone does not count.
- **F3 (later) — External, environment-dependent adjacent possible.** Candidate opens a previously unavailable investigation through controlled observations, tools or human collaboration. Attribute each actor and verify external outcomes independently.

For each case explicitly register **which meaning of possible changes**, its before/after frame and the distinct dependent consequence. Independent evaluators must be fixed **before the model proposals**. Withhold the intended enabling move and downstream answer. Include ordinary additional reasoning, matched irrelevant candidate, candidate ablation, sham transformation, and no-opportunity controls.

**G0 fails** if a static missing-edge test, trivial constraint loosening, or a larger count of answer variants would score as success. No model calls before G0 is inspectably satisfied.

**Current G0 candidate packet (2026-10-25):** [two case families, input envelopes, author counterfactual key and independent reviewer rubric](g0/README.md) have been drafted. They have an additional **T3 second-generation** test: the first possibility must enable a distinct later investigation, not merely an immediate diagnosis or action. The [blocking independent review](g0/g0-independent-review.md) is still **empty**. These cases are *not* approved, are publicly documented (not sealed model holdouts), and must be replaced if independent reviewers conclude they amount to ordinary troubleshooting or granted operator permissions. No model tests are authorized by their existence.

### Stage Q1 — interrogate probability-oriented selection

1. Fix a **strong model snapshot**, input text, output shape, decoding parameters, inference budget, model calls, and temperature. Record these in an immutable run manifest.
2. Draw a **predeclared repeated ordinary-generation sample** before introducing any exploratory prompt. This measures **observed selection frequencies** of relation families, not the full probability distribution or hidden “absence”. A limited feasibility sample may be smaller; never call it a population estimate or a claim of impossibility.
3. Compare candidate generation using deliberate counterfactual exploration, semantic diversification, and an explicitly defined shadow candidate operator **under matched tokens and calls**. Separate external prompt diversification from model-internal measurement: if all variants just use different instructions, the result is *behavioral*.
4. Require blinded assessment of **semantic/structural relation families**, not lexical variants or embedding-only clustering. Preserve candidates occurring once; recurrence is not truth.
5. Optionally, with an open-weight model, check conditional likelihoods, controlled representation steering, and causal interventions. Do **not** invent an “anti-embedding vector”; if no internal test was conducted, explicitly say so.

**Q1 gate:** The strongest matched model baseline must fail to reach at least some independently meaningful **candidate relation families** in the fixed budget that the experimental procedure reaches reproducibly. Otherwise no incremental Q1 benefit has been shown. If this is observed only via prompt variations, attribute the gain to the **procedure**, not to a proven internal absence detector.

### Stage Q2 — can a possibility change what comes next?

1. Freeze the candidate's origin and a **no-change counterfactual** before exposing the future challenge.
2. Allow a changed condition, interpretation, dependency, rule, meaningful question, relation kind, or action; **do not require newly named predicates**.
3. Validate with case-specific independent evidence: in F1 an adjudicable new explanation/test; in F2 a consistent formal transformation and nontrivial previously unavailable consequence; in F3 external verification and actor provenance.
4. Reject paraphrase, directly prompted answers, trivial rule relaxation, and a longer prompt alone; a meaningful newly *restricted* possibility set may be an advance too.
5. Ablate **candidate and transformation separately** with matched context length, tool access, model calls and counterfactual controls. Hold later challenge fixed.
6. Keep distinct fields for new expression, new meaningful distinction, formal new relation kind, new independently testable question, demonstrated external fact, and ablation effect; never compress them into an "expansion score".

**Q2 gate:** An **independently adjudicated, nontrivial change in downstream investigability** is causally dependent on the earlier candidate/transform, survives withheld tests, and is not reducible to extra context. A new predicate or extra graph path is not sufficient.

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

**Coupled gate:** A candidate not seen in the **measured ordinary Q1 selection sample** at `t0` remains weightless; at `t1` it causally enables an independently checked later question, distinction, relation, test or action, **more often than strong matched controls**, with specific candidate ablation. This is a bounded behavioral/operational finding, not proof of previously zero-probability model outputs or changing model weights.

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
| **G0 — Construct validity** | Two **different mechanisms of possibility-making** (F1 meaningful reframing and F2 formal transformation), independent withheld consequences, negative and sham controls, and no trivial rule-relaxation wins | **Stop.** No model/API calls until these constructs are independently assessable |
| **G1 — Q1 observability** | Repeated ordinary-generation selection measured, alternatives controlled for budget and independent relation identity | Only behavioral comparison allowed, no “latent absence” claim |
| **G2 — Q2 validity** | Independent check of a nontrivial changed downstream **investigability** (question, distinction, relation or intervention) with candidate and transform ablations | Only prompting, search, rule relaxation, paraphrase or graph completion |
| **G3 — Coupled increment** | Actual weightless, longitudinal D arm outperforms strongest matched baseline; E/ablation separates candidate influence | Do not claim a unique SSL contribution |
| **G4 — Replication** | Held-out families, model-capability tiers, independently reviewed candidate relevance and registered exclusions | Preliminary feasibility only; no ADR or production changes |

**Research decision (amended):** First distinguish competing explanatory mechanisms H0–H5 and several meanings of *possible*; test **selection Q1** and multiple **future possibility-making Q2** pathways. Do not choose anti-embedding geometry, new seed schemas, relaxed Gate, or an Accepted ADR. G0 precedes any implementation or further paid run.

## Provenance / future reading order

1. [Original hypothesis, literal Dutch wording](../possibility-space-thesis.md).
2. [Corrected historical course elimination](course-elimination-2026-10-24.md).
3. [Relevant theoretical and empirical studies](literature-map-2026-10-24.md).
4. [Earlier proposed experiment, preserved as original plan](first-discriminating-experiment.md).
5. [Live pilot PR and retained negative/invalid outcomes](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220).
6. [First-principles inquiry and competing explanations](first-principles-reorientation-2026-10-25.md).
7. [Source-to-claim audit of the underlying science](source-claim-audit-2026-10-25.md).

**No new model experiment or concept-transformational validator was executed to create this revision.**
