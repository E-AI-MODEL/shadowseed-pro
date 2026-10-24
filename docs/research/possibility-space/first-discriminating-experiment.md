# The first discriminating Shadowseed experiment — design candidate

> **Status:** Proposed **feasibility protocol** (not preregistered; no experiment executed).
> **Date:** 2026-10-24.
> **Research authority:** [unchanged, verbatim fundamental question](../possibility-space-thesis.md).
> **Evidence:** [source map](literature-map-2026-10-24.md), [corrected elimination](course-elimination-2026-10-24.md), [conversation record](conversation-record-2026-10-24.md).
> **Architecture:** no approved ADR or runtime-change authorization follows from this protocol.

## The unshortened question

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

**Objective:** Create an experiment that can *fail* separately on the probability-oriented non-selection question (**Q1**) and on the recursive possibility-change question (**Q2**), and can test whether the *coupled mechanism* exceeds a very capable ordinary model with equal resources. Neither clause may be substituted by "more ideas" or "better answers."

## A decisive distinction before running anything

There are three conceptually different meanings that must not be conflated:

1. **Selection under a fixed generative model:** The base model could output some relational candidate when conditioned differently, although ordinary generation did not select it. A repeated ordinary-generation sample estimates *observed accessibility*, not the total support of a hidden probability distribution.
2. **Discovering a new relational construction:** A candidate relation is formed by a changed question, a counterfactual frame, or an intervention, but it may still be possible under the original fixed model weights. This must be distinguished from random ideation and familiar analogies.
3. **Changing the future space of conceivability:** One relational construction serves as a **causal enabler** for a different class of follow-up possibilities. This need not imply any parameter update, previously zero-probability tokens, or an ontologically new law of nature. We first measure **contextual/operational reachability under declared constraints and compute budgets**, not a global metaphysical space.

The *higher-order novelty* literature concerns new combinations and subsequent combinatorial possibilities, not a Bloom-style cognitive hierarchy. Counting larger combinations does not by itself establish Q2.

## The first research question requires the model's probability-oriented behavior to matter

**Q1 hypothesis (open):** Ordinary generation may underselect coherent, investigable relations that can be accessed through a controlled intervention informed by the same model's generative/representational structure.

**Q1 null:** At matched inference budget and prompting strength, a strong model's ordinary deliberate alternative-generation or semantic-diversity baseline reaches the same classes of coherent investigable relations as the shadow procedure.

### Required Q1 observations

- Fix a model snapshot, explicit task, initial context, decoding settings, and the exact output budget before comparing conditions.
- Repeat ordinary generation across independent samples to characterize the *empirical* frequencies and relation **types** actually produced.
- Compare a declared, controlled exploratory intervention and the strongest matched alternative-generation procedure; do not simply take the lowest-probability sequence.
- Cluster/identify **relations semantically and structurally**, not by exact words, while preserving conflicting and rare candidates for blinded review. Do not let embeddings silently merge different hypotheses.
- For open-weight models, **optionally** test the predeclared relation representation with conditional likelihoods, counterfactual interventions, or hidden-state methods and controls. Output frequency and a single "model self-report" are **not** proof of internal absence/knowledge or of an "anti-embedding space."
- Report model-capability/role differences independently from algorithm effects. A Qwen 7B result does not decide the frontier-model question.

**Q1 evidence threshold (qualitative pilot):** One or more independently validated *meaningfully different relation families* are obtained by the intervention but not by matched strong baselines under the same budget; the result replicates on fresh problems. Such an observation supports a **bounded reachability** claim, not a claim about every ungenerated relation inside the model.

## The second question is not merely "produce an idea, then produce more ideas"

**Q2 hypothesis (open):** An earlier relational construction may enable a **different downstream relation type** whose discovery/access is causally dependent on that earlier construction, not merely on extra context, token count, or a trivially weakened constraint.

**Q2 null:** All downstream discoveries are attributable to ordinary additional prompting/reasoning, task leakage, copy/rephrasing, generic context persistence, or externally supplied new rules. Or no independently meaningful downstream class is found.

### Required Q2 observations

- Begin with independently specified relational environments in which valid inference, changed constraints, and genuinely different **types of relations** can be checked. Avoid selecting only examples known to work for SSL.
- Include more than one environment family, and design a separate open-world transfer follow-up. A closed-world toy alone cannot establish broad creative discovery.
- Hide the enabling transformation from the model where possible; the experimental procedure must **construct or discover** it rather than be handed the answer.
- Use the same formal validity rules for all experimental conditions. An operator may represent a proposed alternative rule for investigation, but it cannot silently declare that every newly permitted edge is a discovery.
- Freeze an evaluator independent from the generating model and use held-out downstream tasks. A result is not valid merely because an LLM judges its own idea plausible.
- **Ablate the enabling relation**: remove it, shuffle it, or replace it with an equal-length irrelevant plausible relation while holding model calls, retrieval scope, and context budget fixed. Test whether the claimed downstream relation class disappears or changes as predicted.
- Distinguish **newly observed**, **newly constructible**, **newly admissible under constraints**, and **newly verified in the world**. Do not claim the latter two from text generation alone.

**Q2 evidence threshold (qualitative pilot):** A new independently valid *downstream relation class* is reproducibly dependent on the enabling relation, beyond matched context/compute controls, with the mechanism of dependence explainable under the declared rules. No demonstration of changed fixed-model weights is implied.

## Coupled Q1 + Q2 experiment — the actual Shadowseed test

The final question is not answered by proving Q1 or Q2 separately. The strongest test is whether **a meaningful but ordinarily unselected candidate generated by Q1 exploration can become an enabling relation for Q2**, causing novel downstream relation classes that matched alternatives do not reach.

Keep the **same underlying answering/generating model** per comparison (and a common budget counted by tokens, model calls, external validation steps, and feedback). Use different models only in a separate capability comparison.

| Arm | Procedure | Why it exists |
|---|---|---|
| A — Ordinary model | Baseline generation and downstream work with complete same-length conversation history | Establish observed default relational reachability |
| B — Strong deliberate model | Explicit counterfactual or divergent-reasoning prompt, self-critique, semantic alternatives; same budget | **Hardest non-SSL baseline**: do capable models already do this? |
| C — Ordinary persistent notes | Save and return candidate notes, no shadow-specific exploration or selection mechanism | Controls memory, text exposure, and extra token history |
| D — Exploratory Shadowseed | Observe candidates without authority; preserve rare relational hypotheses; investigate counterfactual enabling changes and dependent follow-ups; no automatic answer steering | Tests combined candidate access and relational transformation |
| E — Shadow control | Same as D, but substitute random/context-matched or shuffled candidate relations, same token length and budget | Rules out that any extra speculative text or graph perturbation causes apparent benefit |

**Do not assume D is already implemented.** This is a protocol for an isolated research adapter or harness, not a declaration that the current product runtime has a Q1/Q2 engine. The existing Pro Gate, authority audit, and point-of-use checks remain unchanged.

### Model-capability design

- First establish a **high-capability frontier-model baseline**, because a weak model's inability to generate relations is not an SSL achievement.
- Pair it with a **substantially stronger open-weight model** on which logits/activations and causal interventions are available, if compute permits.
- Keep **Qwen 2.5 7B** as a historical stress/reference tier, not as the primary adjudicator. Do not infer a model-size law from family/model differences.
- Fix model identifiers/snapshots, decoding parameters, quantization, seed settings, evaluation costs, and exact task sets. If hardware/snapshots are unavailable, report that rather than substituting and claiming equivalence.

### Pilot units and independence

- First do a **small feasibility pilot** with independently designed, heterogeneous relational environments. It tests instrumentation, evaluator agreement, and whether the Q1/Q2 distinction can even be observed.
- Only **after the pilot**, fix the held-out dataset, sample size, primary metrics, baselines, exclusion rules, and effect thresholds in a versioned preregistration. Do not tune prompt and evaluate confirmatory claims on the same examples.
- Blind independent human/domain experts to arm identity for semantic relevance, and report inter-rater disagreements; an LLM judge may assist but is not independent human evidence.
- Count negative and null outcomes. Do not report only the cases where a usable seed surfaced.

## Stop/go gates — no architecture based on eloquence

**Stop or redesign** if any of the following happens:
1. Q1 exploratory access is no better than a matched strong model's deliberate search.
2. Q2 downstream relations disappear under independent checking or are just paraphrases / trivial consequences of added context.
3. The candidate-ablation effect is absent, unstable or reproduced by random unrelated seeds.
4. Gains arise from extra model/tool budget, a hidden extra constraint, author-selected cases, or leakages.
5. Effects require mislabeling model self-report, embedding similarity, or recurrence as truth/evidence.
6. One model succeeds and others do not: investigate the capability interaction first; do not generalize or force a product change.

**Go to preregistered study** only when Q1 and Q2 each have feasible measures, an independent checker, a strong matched baseline and a demonstrated discriminating pilot case. "Go" here means **test further**, not "accept an ADR."

**Consider a future ADR** only after replicated empirical evidence isolates what a shadow mechanism adds. Then decide whether persistent individual seeds, relational transformations, constellations/graphs, new representations, or model-internal interventions are warranted. Avoid choosing that data structure now.

## What happens next — executable research sequence

1. **Freeze the language of the fundamental question** (already done in PR #219). Preserve user corrections.
2. **Design a few independent Q1/Q2 relational environments and formal validators**. Start with a clear negative case and a strong non-shadow baseline; no confirmation-by-construction.
3. **Run feasibility pilots** on a capable model and, where available, one open-weight model. Record all seeds, rejected possibilities, model outputs, resource budgets, counterfactual interventions, and failed downstream searches.
4. **Analyze failure modes first.** Determine whether the first hypothesis fails, the representation of possibilities was too weak, or the test cannot discriminate mechanisms.
5. If viable, preregister held-out confirmatory tests and only later evaluate a product architecture change.

## Explicit non-claims

No new experiment has been executed or preregistered here. No superiority of the shadow mechanism, latent-space inversion, causal transformation of model weights, or emergence of genuinely new real-world scientific relations has been demonstrated by this document. The protected question remains scientifically open.

This file is documentation for experimental decisions, not a runtime implementation and not an instruction for agents to claim that the research is complete.
