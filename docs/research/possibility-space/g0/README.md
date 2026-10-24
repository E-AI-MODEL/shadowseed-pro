# G0 research cases — distinguish possibility-making from missing-answer detection

> **G0 status: DESIGNED FOR REVIEW — NOT PASSED.** Two different, inspectable synthetic case families are specified. Their facts and falsification conditions are author-defined and **have not received independent external review**. No model calls, experiment implementation or production change is authorized by this file.
>
> **Date:** 2026-10-25. **Program authority:** [fundamental thesis](../../possibility-space-thesis.md), [first-principles mechanisms H0–H5](../first-principles-reorientation-2026-10-25.md), [revised Q1/Q2 protocol](../revised-q1-q2-experiment-2026-10-25.md), [initial failed model trial](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220).

## The whole fundamental research question — unchanged

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

These G0 cases assess whether the **meaning of the measurements** is sound. They are *not* yet an experiment on probabilities or Shadowseed performance. **Q1 is not tested here**: no ordinary-generation sample, model-internal probe, logit measurement, or novelty claim has been collected. The later coupled Q1+Q2 comparison must preserve both clauses rather than treating "an agent asked for more data" as a discovery.

## Why these two families differ

| | F1 — Competing explanations of one trace | F2 — Availability of a safe, non-sequential act |
|---|---|---|
| **What changes, if anything?** | The **question/measurement needed** to distinguish previously observationally identical interpretations. Same original variable/relationship vocabulary; changed observational frame. | The set of **physically admissible operations** under a safety invariant, conditional on independent event-level proof of an atomic action. |
| **Initial barrier** | Any amount of the **archived channel alone** is consistent with both mechanisms. A direct synchronized measure would separate them. | Existing one-at-a-time operations cannot reach a safe alternate state without an unsafe intermediate step. Coarse snapshots cannot establish an atomic transition. |
| **Candidate for investigation** | The delay could belong to the process **or** to its logging channel. Preserve doubt; design a discriminating measurement, not assert a cause. | A paired atomic act might exist. Preserve uncertainty and require physical/witness evidence before treating it as admissible. |
| **Nontrivial downstream consequence** | A justified test that would have different outcomes under the two otherwise indistinguishable mechanisms; afterwards choose the appropriate explanation, not a guessed one. | A verifiable safe before→after→return procedure **only if** a certified atomic operation exists; reject a serial or already-permitted sham. |
| **False-positive traps** | Guessing the cause from the archive; adding more archive readings; detecting only a lagged correlation; claiming the direct gauge is physically created by an idea. | Inventing permission for new transitions; mistaking coarse timestamps for atomicity; skipping intermediate safety checks; relabeling an existing operator as new. |
| **Independent evaluator** | Precommitted deterministic observation equations, paired observationally identical twins, a diagnostic value check and held-out direct-meter result. | A state-invariant/transition checker plus trusted synthetic microstep witness; atomic operation permission must be proved, not generated. |

**F1 and F2 are deliberately not just two versions of missing-edge completion.** However, they may still prove to be ordinary experiment selection and existing capability discovery. **G0 can legitimately fail** if independent scrutiny finds no nontrivial "possibility formation" construct beyond those familiar tasks.

## Files and information boundaries

1. **[F1 design](f1-observational-reframing.md)** — counterfactually identical archives from different causal origins; a new instrument-targeted experiment as possible downstream investigation.
2. **[F2 design](f2-atomic-admissibility.md)** — same coarse history, distinct hidden microstep mechanisms; operations gated by independently verified atomicity and safety.
3. **[F1 input envelope](model-facing-f1.md)** and **[F2 input envelope](model-facing-f2.md)** — the **only phase-0 case text** that a later model experiment may receive. Both are currently **drafts for review**, not active prompts.
4. **[Assessor-only key](assessor-key-and-holdouts.md)** — counterfactual truth rules, illustrative withheld sequences and negative/sham results. **Never send this file, its path, summaries, code snippets, hash, labels, or evaluator verdict to a model during generation.** Stored in Git for audit, not confidential from the internet.
5. **[G0 reviewer rubric](g0-independent-review.md)** — construct audit, leakage checks, independent review and precise approval/stop criteria. Blinded judgments are **not** filled in.

**A public repository is not a sealed experimental vault.** Keeping input and answer key in different files protects against accidental prompt construction, not retrieval contamination. Any real model test must pin an offline/no-tools model interface, keep the key outside retrieval and prompt context, and disclose that the case keys were publicly committed. A genuinely confirmatory future study requires **fresh held-out cases generated and sequestered after pre-registration**; do not reuse these illustrative examples as a hidden model benchmark.

## The two-stage structure without constructing a success

**T0:** Show the model *only* the appropriate model-facing envelope. Ordinary generation and strong alternatives will later be sampled with equal token/call budgets. Candidate suggestions are weightless and are not source evidence.

**Freeze:** Commit candidate(s), their exact words, origin and time before revealing T1. **Do not choose a different candidate after seeing the answer key.** Pre-register what counts as the same candidate; prompt variants are not proof of absence from the original model.

**T1:** Reveal the same allowed new evidence/measurement/operation to each arm at the same time and cost. Any new inference can occur without Shadowseed; attribution requires candidate-specific ablation and a strong ordinary-model comparison.

**T2:** Require a concrete downstream *question/probe or safe action plan*, with predictions/checks. Do not reward longer answers, more unique phrases, or merely naming a new relation.

**Evaluation:** Use the independent case rule for technical validity; additionally require blinded human/domain review of *meaningfulness*. Track whether the proposed move was already reachable in a strong ordinary baseline with the same resources.

## What G0 would and would not authorize

- **Now available:** two concrete, challengeable study designs; their information-flow boundaries and falsification conditions; a reviewer packet.
- **Not yet available:** independent approval of either case's construct validity; sealed confirmatory cases; actual model/LLM results; probability-distribution evidence; evidence that weightless SSL has any benefit.
- **Before any paid or automatic run:** complete the [review checklist](g0-independent-review.md) with signed independent outcomes, remove any leak/hint problems, confirm non-tautological value, establish held-out-case protection, and then preregister budgets and primary measures. **G0 remains NOT PASSED until that is done.**

No change to accepted ADRs, trace/weight, recurrence, Gate, point-of-use controls, production packages or the retired v0 fixed-edge workflow is needed.
