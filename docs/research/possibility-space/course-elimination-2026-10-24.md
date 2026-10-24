# Shadowseed — course elimination, source re-audit, and two-clause test

> **Recorded:** 2026-10-24. **Status:** provisional research-direction analysis, not an accepted ADR or an efficacy result.
> **Links:** [fixed thesis](../possibility-space-thesis.md) · [annotated literature](literature-map-2026-10-24.md) · [conversation and correction record](conversation-record-2026-10-24.md).
> **Decision rule:** This document may recommend a **research design**, not declare that an untested implementation is the scientifically best course. Reopen every eliminated approach when new evidence changes its fit.

## The full original research question, protected verbatim

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

**The two clauses must be treated together.** A method succeeding only at ideation, omission detection, or second-order search is a partial result, not an answer to the complete question.

## Epistemic decomposition: avoid a false solution

**Q1 — the probability-oriented model and non-standard possibilities.**
- What does ordinary conditioned generation preferentially select in a defined task/model/decoding regime?
- Can another controlled procedure identify meaningful relational hypotheses outside that *observed ordinary generation*?
- What observable/interventional evidence connects such discovery to the model's learned probability-oriented representations rather than just extra prompting, more tokens, retrieval, or one more model call?
- Never infer a model's internal knowledge solely from what it did not print; distinguish generated output, estimated distribution, and interventionally demonstrated internal representations.

**Q2 — possibility-generating possibility.**
- Can an emergent or constructed candidate relation change which further **classes of meaningful relations** become articulable, testable, or reachable?
- Are downstream relations **causally dependent** on the earlier relational transformation, rather than just cumulative prompt context or longer reasoning?
- Which interpretation of "possible" is being tested: allowed by formal rules, logically consistent, known in a corpus, semantically expressible, scientifically feasible, or empirically reachable under a compute budget?

**Important mathematical boundary:** For many ordinary softmax-based LLMs, almost every vocabulary token has strictly positive next-token probability, before external hard constraints. Therefore a fixed model's output support is usually not meaningfully divided into "possible words" and "impossible words." A literal claim that Shadowseed *creates previously zero-probability token sequences* is the wrong operationalization. What may change is the *reachable, semantically meaningful, rule-valid, or experimentally accessible* possibility space under explicit assumptions and budgets, or the model's mechanisms if actual interventions/updates are made. No such effect is established yet.

A Q2 proof must not rely on the tautology that "if we supply more ideas to a model it can repeat them." It needs an explicit constraint system and controlled evidence of downstream relational change.

## Corrections to the first elimination exercise

**Reclassify FunSearch, do not put it in the final four.** The [Nature program-search paper](https://doi.org/10.1038/s41586-023-06924-6) describes evolutionary program proposals and external scoring within problem-defined search; this is fundamentally different from investigating a model's unselected semantic relations and recursively changed conceptual possibilities. It may teach evaluation discipline; it is **not** a direct alternative answer to Q1+Q2. The earlier classification as "strong challenger" is withdrawn.

**Correct the declared winner.** The previous "counterfactual relational possibility expansion" approach mostly targets Q2. It did not specify how the probability-oriented generation in Q1 itself is involved, nor how to distinguish model-internal access from prompted variation. Therefore it has **not** yet won. The best present result is a **two-clause, coupled experimental program**, which may in turn fail.

**Correct model-size rhetoric.** A 7B model finding fewer answer-gaps than a frontier model on different suites cannot by itself establish scaling of Q1/Q2. Review of candidate "usefulness" by another model is not equivalent to independent human verification. [Current detector calibration](../detector-calibration.md) measures answer-conditioned gaps, not this thesis. [Current capability scaling](../capability-scaling.md) does not yet test Q2.

**Do not confuse safe authority with epistemic exploration.** [Pro ADR-001](../../architecture/adr/ADR-001-validation-gate-authority.md) and [ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md) already distinguish proposal and influence. Possible candidates may be investigated in bounded, read-only ways without treating them as facts or granting influence. Weakening production Gate rules is neither necessary nor evidentially sufficient.

## Revised elimination bracket

| Proposed direction | Q1 | Q2 | Verdict now | Why / what survives |
|---|---|---|---|---|
| 1. Omission finding + RAG retrieval | No | No | **OUT as core thesis** | Existing information recovery is a valuable application, not the research object. |
| 2. Stronger model alone; more prompts/sampling/temperature | Partial behavioral baseline | No | **CONTROL ONLY** | Necessary to test whether SSL adds anything, but not proof of transformed possibilities. |
| 3. Generic brainstorming / alternative-answer memory | Partial | No | **CONTROL ONLY** | May be useful, but can merely collect unselected phrases without enabling new relation types. |
| 4. Evolutionary candidate search / EvoDiverse-like selection | Indirect (search diversity) | Not shown | **METHOD / CONTROL, NOT FINALIST** | Relevant to rare-candidate loss and optimization pressure, but not equivalent to both clauses. |
| 5. FunSearch program search | No direct test | No direct test | **EXCLUDED as category mismatch** | Useful example of external validators; user explicitly corrected earlier comparison. |
| 6. Literal "anti-embedding = negative vector" | No supported mechanism | No | **REJECT AS CLAIM** | Negative vector has no established meaning as an inverse of skipped thought; retain *metaphor only*. |
| 7. Model-internal probes / steering / causal intervention | Potentially high | Unknown | **KEEP AS INDEPENDENT RESEARCH ARM** | Connects Q1 to learned representations, but cannot alone establish Q2. Larger-model and counterfactual experiments needed; small-model Layer-G null is bounded. |
| 8. Counterfactual relation/constraint transformations | Q1 unspecified | Potentially high | **KEEP, Q2 ARM ONLY** | Graphical transformational-creativity work provides tools; does not by itself connect to ordinary probabilistic selection. |
| 9. Coupled probability-conditioned generation + relation-transformation + weightless history | **Intended direct test** | **Intended direct test** | **PREFERRED RESEARCH DESIGN — NOT A WINNER YET** | Only option defined to interrogate both linked clauses, subject to strong controls and open falsification. |

This bracket is a **conceptual fit analysis**, not experimental rankings. The verdicts "OUT" and "KEEP" relate to *the full thesis*, not universal usefulness or feasibility.

## What the underlying literature actually supports

| Source | Evidence that matters | Does **not** prove |
|---|---|---|
| [Boden, 1998](https://doi.org/10.1016/S0004-3702(98)00055-1) | Distinguishes combining, exploring, and transforming conceptual spaces | That LLMs or Shadowseed enact transformation |
| [Schapiro, Black & Varshney, 2025](https://arxiv.org/abs/2504.18687) | Explicit graph/constraint account of transformational scientific creativity | That an LLM detects transformative, valid changes autonomously |
| [Di Bona et al., 2025](https://doi.org/10.1038/s41467-024-55115-y) | Higher-order novelty and evolving networks of possible combinations | That a language model has such a network or discovers objective novelty |
| [Park, Choe & Veitch, 2024](https://proceedings.mlr.press/v235/park24c.html) | Counterfactual concepts in representation geometry, candidate tools for internal interventions | "Anti-embedding" as a formal inverse of an embedding |
| [CreativityNeuro, 2026](https://arxiv.org/abs/2607.01433) | Weight/activation-space interventions can change measured divergence; relevant Q1 experimental comparator | Novel knowledge or Q2 space expansion |
| [LiveIdeaBench, 2026](https://doi.org/10.1038/s41467-026-70245-1) | Model ability at divergent scientific ideation needs specialized assessment; broad strength is not a sufficient proxy | A parameter-count scaling law for Shadowseed |
| [EvoDiverse, 2026](https://proceedings.mlr.press/v306/wang26gx.html) | Search pressure can reduce diversity in hypothesis sets; methodological warning about candidate suppression | That generative possibility spaces expand through higher-order relations |
| [Original SSL generative vision](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md) | Original deliberate "could have been" ambition and weightless cross-turn carrier | Any demonstrated latent-space inverse or Q2 causal effect |
| [Pro Layer G conclusion](../h-neurons-conclusion.md) | Small-model linear readout probe did not replicate; warns against invented internal-signal claims | Absence of relevant internal structure in frontier models |

See the [source-by-source critical map](literature-map-2026-10-24.md) for venue, year, link, findings, and non-conclusions. Keep concept/theory, lab observations, and speculative application separate.

## Preferred next *test*, not preferred production architecture

Use one linked preregistered research program with separate Q1, Q2, and coupled-effect assessments. Do not silently make the user-visible answer better the target measure.

### Phase A — Q1: ordinary generation and candidates outside it

1. Declare task and semantic relation schema; fix model identity, prompts, inference parameters and budgets.
2. Observe **ordinary generation** with a repeated sample protocol and strict no-extra-context baseline. Record relation classes actually generated.
3. Compare matched-cost methods: explicit alternatives, semantic diversification, counterfactual condition shifts, ordinary cross-turn notes, and possible shadow candidates.
4. For API models, assess **behavioral reachability under stated interventions**. For open-weight models, optionally examine candidate log-probability shifts, hidden-state interventions, and causal probes. Neither black-box missing outputs nor a learned embedding alone proves internal knowledge.
5. Blind, independently assess candidate relation identity, logical consistency, nontriviality, and investigation potential. Retain rare/unrepeated candidates as potential scientific events rather than automatic discard.

**Q1 evidence criterion:** A candidate is more than a paraphrase or generic "alternative" and reaches a meaningful relation reliably under a controlled exploration operation that ordinary sampled generation and matched-cost alternatives did not reach. If no additional relation family appears, Q1-added-value is unsupported.

### Phase B — Q2: transform what subsequent relations become possible

1. Use an independently checkable *formal relational environment*: typed entities, permitted edge types, constraints, and valid rules for composing/transforming relations.
2. Define the before-state, an explicitly proposed transformation, and a after-state whose reachable relation classes can be verified by an **independent evaluator**.
3. Test whether the system can **discover/construct a valid enabling transformation** rather than simply receive it in the task instructions.
4. Test the transformation's effect on *later*, initially withheld problems/relations. This must exceed directly copying the enabling seed or mechanical consequences of relaxing a rule.
5. Perform causal ablation: remove, scramble, or replace the enabling candidate, hold the total context/token budget constant, and measure whether the dependent relation class still appears. Include random valid and random invalid transformations to avoid a trivial "more changes = more options" result.

**Q2 evidence criterion:** Verified, structurally new downstream relation classes are causally dependent on the earlier enabling transformation, not reducible to repetition, extra text, or a larger permitted vocabulary. The measured "possibility-space change" must be **operationally defined**, not assumed to be a change to fixed model weights.

### Phase C — the full coupled question

Compare conditions at the same underlying model and matched reasoning/validation budgets:

- **A:** ordinary generation and follow-up with same complete conversation history;
- **B:** ordinary generation + deliberate alternatives or self-critique (no persistent shadow);
- **C:** ordinary generation + persistent ordinary notes or generic diversity-preserving search;
- **D:** shadow observation + weightless preservation + independently testable relational transformation and downstream investigation.

**Factorial model capability:** repeat across an explicitly pinned local 7B reference, a stronger open-weight model (e.g. ~14B or more where feasible), and a frontier model. Record quantization, prompting, training/model-family differences; do not attribute differences to size alone. Keep all actor roles (generating, transforming, evaluating) controlled or separately varied.

**Key discrimination:** Does the *combination* of a Q1-origin candidate and a Q2 transformation produce externally verifiable downstream possibilities that neither ordinary generation nor the strongest matched controls generate within the fixed budget? Does removing the Q1-origin candidate selectively eliminate the downstream result?

### Separate evaluation outcomes (never collapse into one score)

| Outcome | What would be observed | Main confound |
|---|---|---|
| Ordinary-generation selection (Q1) | Distribution of relation classes under pinned baseline | Sampling variance and prompt choices |
| Exploratory access (Q1) | Valid novel-to-baseline relation classes under fixed budget | Extra calls / generic brainstorming |
| Mechanistic evidence (optional Q1) | Reproducible causal effect on candidate distributions from controlled internal interventions | Probe artifacts / feature entanglement |
| Relation-dependent downstream reachability (Q2) | Verified new relation classes after an enabling change | Trivial new rules or longer context |
| Ablation result (Q2) | Downstream effect disappears or changes when enabling relation is removed | Input-length/context differences |
| Net contribution (coupled Q1+Q2) | Full approach exceeds the strongest matched control on held-out tasks | Unfair compute budgets / evaluator leakage |
| Safety | Speculative candidates do not gain undeserved factual/action authority | Self-validation and circular feedback |

### What would make us abandon or revise this course

- Deliberate ordinary prompting, diversified decoding, or normal memory achieves the same Q1/Q2 observations under matched constraints.
- Formal Q2 "expansion" arises solely because the evaluator was explicitly handed a relaxed rule, without independent identification of a meaningful enabling transformation.
- New output types vanish once paraphrases, random seeds, longer prompts, and extra compute are controlled.
- Apparent gains come from model-rated plausibility, with no independent task validity or external evidence.
- The result holds only under cherry-picked tasks, one author-selected model, one decoder configuration, or leaked test labels.
- A reliable negative result at matched capability fails the benefit claim: retain the interesting philosophy but **do not** force a runtime implementation.

## How strict should Shadowseed be?

**Keep:** no automatic truth from generated candidates, a clear Gate for authority-changing operations, separate point-of-use authorization for user-facing steering and actions, explicit provenance, replay, and contradiction handling.

**Investigate independently:** candidate creation, rare-candidate preservation, trace/TTL policy, and exploration permissions. Do not make *recurrence* a hidden proxy for value or empirical truth. Investigative actions may remain read-only and bounded while a seed is weightless; no need to promote it first. This distinction is already compatible with Pro's core accepted ADRs.

**Do not decide now:** one-seed-one-gap as the only structure for transformations, persistent graph/database design, zero/negative-embedding geometry, threshold tuning, a mandatory H-neuron route, model-size cutoffs, or any new autonomous action authority.

## Decision on 2026-10-24

1. **Reject the earlier premature declaration** that "counterfactual relational possibility expansion" won the scientific elimination.
2. **Select only a provisional research plan** designed to test Q1 and Q2 together and separately, with specific drop-out criteria.
3. **Preserve FunSearch as an external evaluator example only**, outside the direct course bracket.
4. **Keep existing code and accepted ADRs untouched.** A future ADR must cite evidence and explain its bounded design decision; this document is not that ADR.
5. **Preserve full conversation history insofar as accessible and label the reconstruction honestly**, so user corrections and the eliminated routes survive later model turns.

No new model experiment was run by this document. **The currently best-backed claim is that the earlier route does not fully answer the protected research question; no final technical winner has been empirically determined.**
