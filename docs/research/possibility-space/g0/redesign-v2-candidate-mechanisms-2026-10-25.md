# G0 v2 — replacement candidate mechanisms after rejecting the first two cases

> **Date:** 2026-10-25.
> **Status:** **TWO NEW CANDIDATE CASE FAMILIES PROPOSED; NEITHER VALIDATED.** F1/F2 are retired as *primary* tests in the [adversarial audit](internal-adversarial-audit-2026-10-25.md); their mathematical fixtures remain valid as calibration/negative cases.
> **Boundaries:** Research design only. This is not a preregistration, external independent review, executed model experiment, Shadowseed implementation, evidence of novelty, or approval to call a paid API.
> **Rationale:** Distinguish **self-proposed changes in the set of questions or probes that can be meaningfully investigated** from answer completion, straightforward diagnosis, newly granted capabilities or longer author-supplied chains. The researcher *still* designs the world. Any novelty claim is relative to a controlled before-frame and budgets.

## Unmodified two-part question

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

## Stop designing benchmarks that give the answer away

The [original F1 and F2 cases](README.md) had a hidden answer prewritten by the author, and the model-facing requests explicitly invited uncertain alternatives and future tests. The T3 "second-order" step also largely consisted of author-written familiar follow-ups. That does not instantiate either model-internal nonselection (Q1) or self-originating new possibility-making (Q2).

A more discriminating design must separate **three independently time-stamped records**:

1. **At time T0**, ordinary responses and other exploratory proposals are frozen, **without seeing the later question family or answers**. An experimental arm may generate a specific novel *investigation operator/question*, not merely a conclusion about a supplied problem.
2. **At T1**, the environment makes the previously proposed operator/investigation *testable*. Its outcomes and limits are checked against precommitted, independently generated simulation truths. Invalid proposals and the absence of meaningful new operations remain in the denominator.
3. **At T2/T3**, a new held-out problem tests whether the earlier proposal opens a **different, downstream discriminating question or capability**. It must not simply ask the model to repeat the originally supplied target answer. A separate, equal-budget ordinary strong-model arm must be permitted to discover the same thing; a tie means no SSL-specific benefit.

Do not define Q2 as a mandatory new relation type. A change of *which questions can be asked and falsified* is potentially relevant, though not automatically novel.

## Candidate family F3 — discover whether transformations compose differently by order

**Kind of possible:** A proposed *new experiment family about sequence and order*, leading to distinct counterfactual state predictions and previously untested control paths. This is a change of the *investigation frame*, not an extra missing node or a renamed relation type.

**World generation:** A seeded, independently auditable simulator draws two black-box state transformations `p` and `q` on a finite state set, along with distractor descriptions. Externally verified rules govern how a sequence actually changes state. Model-facing observations at T0 may be limited to **single-operation results** and partial trajectories, not labels such as "noncommutative", "order effect", "commutator", or target task names.

**Illustrative hidden positive mechanism (assessor only, not a prompt):**
- State `s` in `{0,1,2,3,4}`; `p(s)=(s+1) mod 5`, `q(s)=2s mod 5`.
- At `s=1`, doing `p` then `q` gives `q(p(1))=4`, while doing `q` then `p` gives `p(q(1))=3`.
- Thus observing operators only one-at-a-time cannot determine all compositional consequences by direct observation; an investigation of **ordered compositions** may expose a distinct dependency.

**Matched negative:** Replace `q` with `h(s)=(s+2) mod 5`: then `h(p(s))=p(h(s))` for every state. A model that insists "order always matters" or simply rewards the existence of more possible sequences must fail. Additional negative: a changed state due only to repeated application, not order, does not establish order-dependence.

**At T0:** Ask a **neutral broad inquiry** about what the data warrant and how to investigate system behavior, *not* "find an overlooked relation or invent an operation". Log all candidate question/experiment operators actually proposed. The research procedure can retain tentative questions without epistemic authority. Precommit the operator and its expected discriminating observations *before* any pair-operation data is revealed.

**At T1:** Permit matched access to a bounded black-box executor. If and only if the earlier frozen candidate requests ordered composition, the corresponding calls can expose a non-commuting behavior. Baselines also have equal ability to request this experiment at equal cost. Without the candidate, ordinary deliberation may independently request it; that is not a failure to be hidden.

**At T2/T3:** Reveal **fresh states or altered environment constraints**, not the old sample. Ask the model to formulate a new and distinct *downstream inquiry* such as whether command order can be used as a control variable for targeted state selection. Use a preregistered independent executor to verify both a positive consequence and a null/commuting case. The downstream question must be proposed before the targeted outcome; do not give it away in T0 instructions.

**Technical oracle:** Replay the frozen operator sequences on the same simulator seed and test predicted state contrasts. Reject claims of general order dependence if the proposed `p,q` commute; reject claims of model-specific novelty when all ordinary arms produce the test as easily. A strictly syntactic count of combinations is never the primary outcome.

**Fatal failure mode:** This may be **standard program synthesis / active learning / algebraic non-commutativity**, widely available to capable models. Two-step experiments and their consequences are mostly encoded in our evaluator. If an independent reviewer finds no meaningful nontrivial "new possibility" beyond ordinary planning/search, **retire F3 too**, even when the graph of investigations grows.

## Candidate family F4 — construct an observable that neither initial channel provides alone

**Kind of possible:** Formation of a **new investigable distinction** through a model-proposed measurement composition, not new physical evidence, a new relation *type*, or a better wording of the same answer.

**World generation:** A seeded data generator draws a hidden binary latent state `z`, independent nuisance `n`, and two individually uninformative measurements; a model receives observations of `a,b` without being told the latent production rule, the target composite, or later outcomes. A future model or experiment can *propose a measurement function* `m(a,b)` and later test it with independently acquired observations or a source-valid device.

**Illustrative hidden positive mechanism (assessor only):**
- `n,z` each independent unbiased bits; `a=n`; `b=n XOR z`.
- Each of `a` and `b` on its own carries **zero information about z** in this toy distribution, but `a XOR b = z` exactly.
- A candidate to **compose measurements** may therefore make a meaningful previously unavailable latent distinction directly observable, *conditional on independent validation*.

**Matched negative conditions:**
- **N0:** `a=n`, `b=n`; `a XOR b=0` carries no information about `z`. A proposed composite that just produces constants is not a new meaningful observability opportunity.
- **N1:** `a=n`, `b=n XOR e` with `e` independent of `z`; the combination predicts `e`, not `z`.
- **N2:** a third channel already directly reports `z`; the supposedly new measurement adds no differential investigability at equal information budget.
- **N3:** a model claims a useful latent factor merely because two streams differ, but its derived variable has no independently checkable downstream consequence.

**At T0:** Show mixed observation streams `a,b` (and equally informative distractors) **without a declared hidden target `z`**. Any useful composite measurement/question must originate with the candidate procedure and be frozen before the later independent source/intervention is available. If the designer says "extract the XOR bit" in the prompt, the test is invalid.

**At T1:** Model-generated `m(a,b)` is a **falsifiable proposed instrument**, not truth. The evaluator supplies an independent, held-back source of labeled states or physical tests; only then can the candidate be judged. A detector cannot count arbitrary new variables as meaningful, and the model must not generate the ground truth labels itself.

**At T2/T3:** Instead of rewarding "we found `z`", the future task asks which **new investigation** becomes meaningful using the validated measurement (e.g. predicting an unknown environmental regime or testing a contingent dependence on `m`). The second-stage target relationship must be **separately generated and held out**, including cases where `m` succeeds as a measurement but predicts *nothing* later. If the model merely reuses a supplied outcome or the author supplies the next question, no Q2 credit.

**Independent oracle:** Mutual information / classification accuracy of the proposed composite against held-out independently labeled `z`, plus a **separate** test of downstream predictiveness and significance under shuffled/duplicate controls. A purely random `m` or an operator name without independent predictive/discriminatory value fails.

**Fatal failure mode:** In the synthetic positive case the author built the XOR relation into the data, so the model may simply rediscover a classic Boolean operation. That is *not invention of new physics or internal probability-space expansion*. If a strong baseline finds the same composite from the same data, or independent reviewers judge the derived instrument trivial, **retire F4**.

## Why this is more demanding than F1/F2 — but still only a proposal

- In **F1**, the author pre-selected the independent meter; in **F4**, the model would have to propose *which composite to test*, and an independent evaluator separately decides if it earns useful access. The synthetic generator still determines the answer.
- In **F2**, the author introduced a certified new hardware operation; in **F3**, the model would have to propose *an experiment family or operation-composition question* and independently test its consequences. The combinational action language still exists in the world before the model asks.
- Both families require **second-order questions not revealed at T0**, and both include matched negatives where the same kind of proposal does not unlock anything.
- **Neither family shows what an LLM could not have generated in a fixed probability distribution.** That is the separate Q1 sampling requirement.
- **Neither family is automatically a conceptual-space transformation.** A model can be performing standard compositional inference or instrumentation; G0 fails if only that is measured.

## Predeclared discrimination against H0–H5

| Explanation | Minimum observation needed | How it would defeat a purported Shadowseed increment |
|---|---|---|
| **H0 — strong ordinary generation/search** | Baseline with identical model, context, time, total calls, token budget, tool access and output constraint; predeclared repeated ordinary sampling | A/B/best-of-N already proposes the same meaningful composite/experiment and downstream question |
| **H1 — probability-selection effect** | Compare empirical frequencies of **semantically distinct proposal families** under fixed ordinary generation and controlled alternative decoders/instructions | "Unselected" candidate is common in ordinary generation at matched budget; effect is prompt diversity rather than a distinct mechanism |
| **H2 — internal representational access** | Optional open-weight intervention and sham on same model and tasks | No causal intervention or no improvement over ordinary output is observed; do not infer absence introspection |
| **H3 — weightless longitudinal candidate** | Isolated multi-turn candidate store that retains uncertain proposals without upgrading truth; same-length ordinary notes/replay and shuffled candidate controls | Candidate has no specific effect after ablation, or ordinary notes yield same downstream study |
| **H4 — frame/probe formation** | Independent evidence that the earlier candidate opens a **distinct, previously unavailable discriminating question** under the original frame and that it is not merely an extra answer | Change reduces to obvious algebra, known feature construction, external evidence supplied by examiner, or author scripted question |
| **H5 — human/tool/environment contribution** | Actor/provenance ledger per proposed operator, later measurement, validator and enabled test | Author, tool or human supplies the actual capability/idea; LLM contribution is only recall or explanation |

## Audit rules before further execution

1. **Independent reviewers R1/R2 (not this author) must assess both v2 families against C0–C11** and be free to reject both. Do not fabricate reviewer signatures, approvals, likelihoods, metrics or model data.
2. **Do not use the public illustrative mechanisms as confirmatory holdouts.** Create new independently seeded/curated cases *after preregistration*, sequestered from model retrieval. The examples in this file are deliberately disclosed to make reasoning auditable.
3. **Measure Q1 directly as observed selection:** repeated ordinary outputs under frozen conditions and semantic relation identity adjudication. One absent string is not a model-internal absence; an internal claim requires an appropriate intervention.
4. **Measure Q2 with causally dependent downstream opportunity** and actual candidate/transform ablation versus matched ordinary notes, not with generated-answer quality or number of graph links.
5. **Defend the difference between a generated proposal and externally granted reality:** the author generates the worlds, the model might choose a question, the oracle supplies validity and later facts, and humans assess scientific meaning.
6. **Cost limit and consent:** no paid or automatic model run before G0 review, a versioned protocol and explicit approval for a budgeted experimental execution.
7. **Architecture unchanged:** no accepted ADR, new seed data type, weakened Gate, production change or legacy-pilot rerun follows from this redesign.

## Working decision

**G0 v1: NO-GO for the fundamental thesis.**
**G0 v2: candidate mechanisms specified, awaiting independent assessment and technical oracle feasibility checks.**
**Q1/Q2: not tested with v2; neither hypothesis established.**

The next *useful* milestone is a reviewable, independent **discriminability audit**, not more complicated pseudo-scientific language or a further unreviewed GPT-5 run.
