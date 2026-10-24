# Shadowseed adapter comparison contract — prospective G0 candidate

> **Date:** 2026-10-25. **Status:** evaluation-contract proposal only. **G0 NOT PASSED**; not a preregistration, signed review, ready-to-run experiment, shipped adapter mode, or efficacy result.
> **Applies to:** [verbatim Q1+Q2 thesis](../../possibility-space-thesis.md), [candidate adapter position](../adapter-not-model-improver-2026-10-25.md), [dynamic inquiry proposal](dynamic-inquiry-protocol-candidate-2026-10-25.md), [external environment screen](external-benchmark-feasibility-2026-10-25.md), and [independent reviewer veto](dynamic-inquiry-independent-review.md).

## Preserve both questions and existing product boundaries

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

This contract tests an **application-level research adapter** using a host-controlled LLM. It does not train or conceal that model, read its private reasoning, or bypass source verification and the product's Gate. A candidate in the isolated research memory starts **without authority**. Trace, weight, TTL, TrTL, recurrence, existing accepted ADRs and point-of-use authorization are **unchanged**, not research knobs to tweak for a favorable result.

**Q1 is behavioral unless direct internal measurements are separately justified.** Repeated ordinary generations can establish which meaningful question/relation families appeared under *one pinned distribution and budget*. A nonappearance is not evidence of zero probability, internal absence, inaccessible knowledge, or global novelty.

**Q2 requires a prospective and checked later research question**, not merely an alternative answer, more tokens, a missing edge, or a new relation label. A changed distinction, condition, constraint, intervention or follow-up experiment may count only when an evaluator independent of the proposing model validates why it makes a *different* later investigation meaningful.

## Before selecting an environment (G0, all still pending)

**Pass is not currently permitted.** Obtain a separately authored technical evaluator review and a separately authored conceptual/method review for a *version-pinned* environment. Each reviewer must be able to veto it. Require an executor with a general admissibility check for **unscripted** safe queries, meaningful negative/no-opportunity cases and prospective second-order consequences. Public old fixtures do not count as hidden confirmation cases.

An independent reviewer must explicitly try to reduce the phenomenon to (a) ordinary strong-model inference or deliberate search; (b) active learning and familiar experiment planning; (c) standard feature engineering or program synthesis; (d) longer context/extra notes; (e) an externally supplied new action/observation; and (f) task-author leakage. If any such explanation fully accounts for a claimed distinctive effect, the specific SSL claim fails. A fair environment can support a valid study even when the final result is null.

## Controlled arms: same capable model in the primary comparison

| Arm | Process | Essential comparison |
| --- | --- | --- |
| **A — ordinary** | Same strong model with ordinary, repeated generation, identical history and allowed future observations; no SSL memory | What ordinary probability-oriented generation selects with the same resource budget |
| **B — deliberate / diverse** | Same model with its strongest pre-specified counterfactual, divergent, or search procedure | Whether more deliberate ordinary exploration makes D redundant |
| **C — ordinary memory** | Same model with equal-budget ordinary notes and full-history/replay, including delayed user/environment updates | Whether simple persistence and context explain D |
| **D — actual weightless store** | A *real* isolated candidate store persists across turns with timestamp, provenance, zero authority and no hidden product-Gate bypass | Whether retaining an uncertain candidate makes a measurable incremental difference |
| **E — matched ablation/sham** | Same D machinery but remove, swap or replace the **specific frozen candidate**, with equal context length and future observations | Whether the claimed effect depends on that candidate rather than generic extra content |

The historical D-*prompt* in the 24-call fixed-edge pilot is **not D**: it never stored a candidate across turns. A renamed prompt, extra generations or higher token ceiling is not an adapter implementation.

Budget matching includes **all** LLM calls and tokens (including detector and revision calls), tool queries, feedback events, retrieval/results, latency or capped compute where applicable, and context available at every turn. Do not provide A's answer to other arms without granting a separately balanced equivalent to A. Keep provider, model revision, system prompts, temperature/decoder and accessible tool inventory pinned within a comparison; test model tiers *after* the primary controlled comparison.

**Research-state isolation:** run each arm on its own disposable state; never mutate ordinary Workbench production records with experimental candidate memory. A research candidate's existence, semantic similarity or recurrence grants no evidence, confidence calibration, steering permission or Gate promotion.

## Prospectively frozen trajectory

| Stage | Frozen before disclosure | What is observed | What is forbidden |
| --- | --- | --- | --- |
| **T0 — ordinary distribution** | Model, prompts, decoding, randomization, sampling budget, question-family coding and arm allocation | Repeated ordinary responses and observed semantic families; uncertainty of estimates | A single unselected answer treated as internal impossibility |
| **T1 — first inquiry** | Candidate text/ID, parent question, content hash, origin, selected tool budget, allowed action grammar | Each arm independently proposes a question/intervention; general validator can accept, reject or return no opportunity | Author-provided ideal question, leaked answer key, hand-selected only successful candidate |
| **T2 — new evidence** | Exact intervention and evaluator version, timestamp and returned observation; randomized disclosure schedule | All arms receive equivalent opportunities and the **actual result** of their own allowed interventions | Different feedback, private hints or free access to another arm's proposed answers |
| **T3 — later inquiry** | Subsequent model-originated question, dependency on T1/T2, claims about what changed | Independently checked consequence, meaningful distinct investigability and documented counterfactual | Calling more answer variants or a prewritten second task a transformed possibility space |
| **T4 — comparison** | All trajectories and failure/null cases, independent human assessments and scoring code | Compare D to A/B/C and candidate-specific E without post-hoc rescue | Moving the goalposts, merging incomparable budgets or using self-rating as ground truth |

All candidate and evaluator records must be append-only or hash-bound, with a predeclared handling rule for parser errors, model refusal, tool failures, ambiguous questions, duplicate candidates, inaccessible queries and no-opportunity cases.

### Minimal proposed record fields (not a new production schema)

- Protocol/environment: protocol version, environment ID/revision, restricted holdout ID, arm/run IDs, model ID/revision, decoder, random seed, budget preset.
- Candidate: turn and stage, question, origin, candidate ID/text/hash, original timestamp and explicit research-weightless status.
- Independent check: tool request and response hash, admissibility decision, independent rule, invalid/no-opportunity reason and full token/call/tool costs.
- Next question: later-question ID, candidate/observation dependency IDs, withheld-consequence result, independent human meaningfulness verdict and reviewer provenance.
- Comparison: exact ablated candidate, ablation outcome, failed attempts, contamination flags, model/researcher/tool/human contributions and blinding status.

These are *research log requirements* to vet, not a command to expand Shadowseed's normal seed model. Some fields will require an exact environment-specific definition before preregistration.

## Separate outcomes; no synthetic aggregate score

1. **Q1:** distribution of observed meaningful families and selection differences among *cost-matched* ordinary/sampling procedures. Report confidence intervals and number of draws; absence is always budget-relative.
2. **Inquiry validity:** proportion of model-originated questions that a separate general validator can execute, reject or mark untestable. Preserve all attempted queries.
3. **Q2:** verified **different later investigations**, whose meaning is justified independently and whose relevant follow-up outcome was not given to the agent in advance.
4. **D-specific causal contribution:** D versus strongest A/B/C control and E candidate-specific ablation, with predeclared effect size and uncertainty. A successful baseline counts as evidence **against** a unique D advantage.
5. **Safety and cost:** any invalid intervention, leak, unauthorized influence, price/time overhead, failure to retain rare valuable candidates, or detector flooding. Do not hide negative externalities behind a success score.

**Stop rules:** pause for leakage, benchmark-key contamination, unequal budgets, unauthorized external action, unsandboxed secrets, unexpected spend, invalid evaluator behavior or inability to blind the independent review. An invalid protocol gives no efficacy conclusion regardless of the number of model calls.

## Required decisions before implementation, currently unanswered

- Which environment and exact version actually validates unscripted prospective questions, not only predetermined answers?
- How will independent domain experts decide "meaningfully new later inquiry" without merely favoring surprising language?
- Which normal-note baseline is strongest, and how are extra memory/detector tokens debited fairly?
- How will truly new, sequestered confirmatory cases be created *after* preregistration and protected from retrieval leakage?
- What is the precommitted minimal D-over-strongest-control effect, sample size and uncertainty threshold? Neither is chosen yet.
- Can a negative/no-opportunity trajectory, an ordinary model outperforming D, or a technically correct yet scientifically trivial new question be reported as a genuine negative result? **They must be.**
- Does the external adapter actually add measurable value over a host simply persisting ordinary notes? If not, retain only the demonstrated auditable-memory/security product claim.

## Gate and execution decision

**Current state: NO-GO for a new live Q1/Q2 trial.** This contract is a checklist for a later independently reviewed preregistration; it grants no approval to implement, merge a new experimental runtime, enable paid workflows, read secrets, change production Gate policy or announce scientific efficacy. The [independent reviewer ledger](dynamic-inquiry-independent-review.md) remains unfilled until actual independent reviewers provide dated, attributable decisions.
