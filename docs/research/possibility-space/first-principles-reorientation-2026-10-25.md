# Shadowseed: first-principles reorientation before another experiment

> **Recorded:** 2026-10-25.
> **Status:** Critical research synthesis and provisional mechanism competition, **not** proof, a preregistered study, an architecture decision, or a new experiment.
> **Purpose:** Return to the original SSL sources, identify unexamined assumptions, and prevent an attractive technical test from redefining the research question.
> **Inputs:** [original 4.5 theory](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/legacy/00_shadow_seed_learning_4_5.md), [4.6 evidence discipline](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/00_shadow_seed_learning_4_6.md), [June 2026 generative vision](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md), [current Pro ADRs](../../architecture/adr/ADR-001-validation-gate-authority.md), [source/claim audit](source-claim-audit-2026-10-25.md), and the failed [first live pilot](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220).
> **Next gate:** Clarify rival mechanisms and what would count as the sought phenomenon, **before** G0, coding, or another paid-model call.

## Unmodified fundamental research question

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

**Do not shorten or redefine the question.** It has two *connected* problems: (Q1) using the probabilistic generative mechanism of the LLM to investigate meaningful possibilities outside usual selection; (Q2) investigating how a possibility, relation or reframing might alter what becomes conceivable or investigable afterwards.

## Executive conclusion — no early winner

We made the same methodological mistake twice. The earlier route translated the thesis into "novel **relation types**"; the 24-call pilot translated it into "a missing **edge** in an unchanged graph." Neither translation is universally entailed by the research question. A new relation type can be one *instance* of Q2, but is **not a necessary condition**; merely finding an omitted edge is neither sufficient nor especially close to Q2.

The more defensible object of study is **changes in the effective space of meaningful, investigable possibilities under stated conditions**, examined together with *why a probability-oriented generator selects some relations and not others*. This is *not* a mathematical claim that we make previously zero-probability token sequences possible under fixed LLM weights.

The current answer to "which mechanism wins?" is **not determined**. The next scientific product is a *discriminating specification* and a set of genuinely rival explanations, **not** a new graph runtime or a renamed anti-embedding component.

## 1. Read the original sources against the new thesis — not as proof

| Source | What was originally intended or decided | What is demonstrated / not demonstrated | Implication |
|---|---|---|---|
| SSL 4.5 | Repurpose completion to detect structural absence, store an atomic weightless gap, observe recurrence, validate before influencing | This is a mechanism *claim/proposal*. It does **not** demonstrate introspection into unchosen model-internal semantics. The paper on Bayesian epistemic uncertainty is conceptually related but studies computer-vision uncertainty, not SSL absence detection | Retain ambition and traceability; **demote the latent-absence assertion to a testable hypothesis** |
| SSL 4.6 | Separate mechanics, safety, evidence layers and unproved efficacy | Strong methodological/evidential discipline; the defined output remains mostly a missing *answer element* | Keep rigor; do not let answer completeness define the research question |
| June 2026 vision | Explicitly rejects "what should have been there" in favor of "what **could** have been there"; preserves a candidate without immediate authority across turns | Prescient framing, but still largely seeks eventual *better answers*, and hypothesizes rather than demonstrates latency/internal signals | Carry the non-selected possibility idea **past answer improvement** toward the genesis of *further* possibilities |
| Pro ADR-001 | Observation, Gate-authorized authority and point-of-use influence are separate | Implemented policy boundaries, **not** evidence of possibility-space discovery | Preserve unchanged |
| Pro ADR-002 | A seed can be a gap, doubt, alternative, contradiction or relevant what-if; atomic, investigable and nonassertive | A sound **candidate/authority contract**, not proof that atomization can represent a change of frames | Investigate transformations as **linked collections of candidates** in a research representation without silently changing the accepted seed contract |
| Pro Layer G / H-neuron scoping | Explore activation-based signals as a possible internal supplement | Small-model probes to 0.5B had a bounded null; H-neuron work is about hallucination-correlated activity, not absent creative possibilities | Model-internal route remains **optional, unproved**, and should not be a dependency of the safety Gate |
| Pro 24-call GPT-5 feasibility pilot | Intended to test Q1/Q2 with four arms in synthetic typed networks | **16/24 parseable**, **8/24 incomplete**; matched controls imperfect; discovered fixed-rule graph edges rather than changed possibility mechanisms; D was a prompt, not cross-turn SSL | Preserve as a **negative methodological finding**. Do not simply increase output tokens and call the thesis tested |

Important difference from a narrow return to SSL 4.5: the new question is **more ambitious than the answer-centric descriptions in both 4.5 and 4.6**. Returning to sources means understanding their premises, preserving genuine inventions (weightless investigability and delayed authority), and questioning inherited assumptions. It does **not** mean reverting the research goal to omission detection.

## 2. Five senses of "possible" — not one undifferentiated space

1. **Token/syntactic support:** A frozen autoregressive model, without hard restrictions, normally assigns nonzero probability to an enormous set of token continuations. Showing a new printed string is not expanding this support.
2. **Observed generative accessibility:** Which **meaningful relation families** are actually produced in repeated ordinary generations at fixed model, prompt, decoding and resource budget. Absence from a sample is not evidence of impossibility.
3. **Constructive/conceptual expressibility:** Which questions, distinctions, interpretations, constraints, relations and operators are articulable under a particular *working frame*. The model's underlying weights may stay fixed while this frame changes.
4. **Rule-governed admissibility:** Which relations are permitted under an explicit grammar, causal model, logic or scientific hypothesis. A new rule may expand or **restrict** admissibility. More admitted sentences can be trivial, harmful or nonsensical.
5. **Investigable or empirically realizable possibility:** Which candidate can be seriously tested, realized or checked in an environment. Human input, tools, new evidence and new experimental access may be essential.

**A new class of relation is only one way that 3–5 might change.** Equally eligible in the thesis: changed **conditions**, changed **meaning**, an unexpected **dependency** between familiar constructs, a new **question** enabling a different research intervention, or a new **affordance** in an evolving environment. Each must pass its own independent validity test. Merely prompting the model to produce more sentences is *not* evidence of any of these.

Useful notation, not an ontology imposed on all cases:

- The probability-oriented model supplies a conditional distribution `P_theta(next_tokens | context)`.
- For fixed model, context family, decoder and resource budget `B`, define an **observed meaningful-relation repertoire** `R_obs(theta, context, B, evaluator)`.
- At time `t`, also describe the *external working frame* `F_t` (assumptions, admissibility rules, meanings, observations, experimental access). The downstream **investigable** set `I(F_t, B, evaluator)` can differ after a bounded, inspectable transformation `F_t -> F_(t+1)`.
- No observation of `R_obs` or `I` by itself establishes any change to model weights, a complete internal set of ideas, or objective novelty in nature.
- The relevant Q2 claim is about a **dependent change in downstream investigability under explicit conditions**, not an arbitrary increase in counts.

## 3. Six live rival explanations — and what would defeat each

The alternatives below can coexist in an implementation; they compete over **which mechanism is necessary for an observed incremental effect**. Treat the ordinary strong model as a serious *null*, not a straw man.

| Candidate explanation | Mechanism that might account for the result | What would distinguish it | Strong defeat / reduction |
|---|---|---|---|
| **H0 — ordinary model capability and more search** | An excellent LLM with enough independent samples, deliberate counterfactual prompting, and compute accesses the same relational families | Equal-model, equal-token/call/time, independent comparisons | If H0 matches every downstream result, no *incremental* Shadowseed mechanism is demonstrated |
| **H1 — probability-selection effect** | Standard decoding/conditioning tends to select familiar relation families; controlled alternate decoding/context accesses meaningfully distinct candidates | Pinned ordinary-response distribution; semantic relation-family measurement; matched decoding/prompt baselines; optional likelihood shifts | Effect vanishes under equally strong diversity-aware decoding, or semantic difference reduces to paraphrases |
| **H2 — internal representational intervention** | Perturbations in model activations/representations reveal or causally support underselected relation families | Open-weight intervention vs sham/shuffle and model/prompt controls; measured likelihood and validity effects | Probe/steering provides no reproducible causal access beyond H1, or labels leak into probes |
| **H3 — persistent weightless candidate memory** | A rare, weak or conflicting hypothesis remains available across changing contexts without becoming a fact; later context allows re-interpretation | Same-model multi-turn trial: actual carried candidate state vs ordinary notes, replay, candidate ablation and random-candidate controls | Notes/self-critique/replay yield the same result; isolated candidate never changes downstream possibilities |
| **H4 — frame/relation transformation** | Reinterpreting, conditionally relating or changing composition/constraints makes previously inaccessible follow-up questions or tests meaningful | Predefined **before/after** semantics; withheld downstream challenge; independent validity; same-content-but-no-transform counterfactual | Difference reduces to added text, trivial rule relaxation, an obvious paraphrase, or task-author supplied solution |
| **H5 — co-construction with environment or human** | A candidate opens a test; new external evidence, interaction or human insight then changes future practical possibilities | Attribute model, human, tools, feedback and environment **separately** and test steps with/without each actor | Apparent novelty comes entirely from supplied external information or is not independently validated; do not attribute it to the LLM alone |

**Leading observation, not victory:** The most distinctive *existing Shadowseed architectural asset* is H3 (retain uncertainty with trace, prevent unearned authority via weight/Gate). But H3 alone does **not** answer Q1 or Q2. The priority is to test whether it adds anything in combination with H1/H2 and a defensible H4/H5 phenomenon. It could be redundant. We should be prepared to conclude that.

## 4. Why the earlier "relation kind" G0 is too restrictive

The **earlier version** of the [2026-10-25 Q1/Q2 plan](revised-q1-q2-experiment-2026-10-25.md) initially required changed **relation kinds/constraints** at G0, treating a "new relation kind" as the core Q2 outcome. **This restriction has now been amended in that plan**: a new relation kind remains one optional test case, not an overall definition.

**Correction:** new predicate vocabulary or a new operator is a **sufficient *candidate example* of an inspectable formal change**, not the unique signature of possibility-making. It may even be a superficial renaming or a trivial axiom relaxation.

Our true G0 should instead require **at least two distinct explanatory pathways** (for example, a novel dependency within existing relation types versus a genuine constraint/frame transformation), with *different expected downstream consequences*, and at least one negative case where an attractive candidate does **not** unlock meaningful possibilities.

A constructive transformation need not *increase* counts: a new distinction may **remove** invalid paths while making a previously undefined experiment or comparison possible. Quality and change-of-questions matter more than the total number of propositions generated.

### Three discriminating example families — **not yet constructed datasets**

**F1 — Reframing without a new named relation type.** Two descriptions appear incompatible under a shared tacit assumption. New evidence or an unselected candidate suggests the descriptions concern different conditions. The resulting conditional interpretation creates a *new testable comparison or research question*. Record whether a strong ordinary model could do the same, whether the conditional distinction was already explicit, and whether withholding the candidate blocks the independent downstream comparison. If merely adding a longer explanation gives the same result, the extra 'possibility' is ordinary context expansion.

**F2 — Transformation of admissibility / composition.** An initial formal system makes certain artifacts or predictions inexpressible. A candidate proposes a justified change to an axiom or composition rule, with an independent checker of consistency and held-out consequences. A merely permissive rule that makes everything expressible is *not* a finding. This is where [Schapiro, Black & Varshney](https://arxiv.org/abs/2504.18687) is most directly relevant, but success in this family alone does not establish the full thesis.

**F3 — Time/environment-dependent adjacent possible.** A previously unavailable observation or action changes what can now be investigated. The claimed enabling step must be *specifically* responsible for later distinct investigations, checked against random plausible observations, equal context and the same tool budget. This is closer to [Di Bona et al.](https://doi.org/10.1038/s41467-024-55115-y), but their statistical model does not itself demonstrate LLM-specific possibility formation.

For all families: hide the intended enabling operation and held-out test; count attempted as well as successful transitions; accept genuine no-opportunity outcomes; keep human input attributed.

## 5. An evidence ladder before coding

**R0 — Meaning:** For each case, state *what* could change: selection frequency, interpretive frame, admissible relations, investigable questions, or actual feasible actions. Establish both a null and a nontrivial alternative. Do not mix them in a single "expansion score."

**R1 — Q1 identifiability:** Measure observed ordinary selection at a predeclared budget, compare strong prompted/decoding alternatives, distinguish availability under conditioning from claimed model introspection. An "unselected" candidate is only unselected relative to an explicit tested baseline.

**R2 — Q2 causal dependency:** Independent held-out downstream checks; ablate candidate and enabling step separately; use same-length uninformative candidates and no-transform controls. Neither a newly printed relation nor more graph edges passes automatically.

**R3 — SSL-specific contribution:** Model-identical, budget-identical cross-turn H3 versus ordinary-notes and strong deliberate-search baselines. Confirm the effect genuinely relies on weightless persistence, not arbitrary added context.

**R4 — Mechanistic attribution and external validity:** Where model-internal claims are made, perform causal interventions. Where world/scientific novelty is claimed, require independent domain evidence and credited human/tool roles. Reproduce on unseen families and multiple model tiers before any product or ADR decision.

The steps above are **readiness criteria, not passed gates**. We currently have no positive Q1/Q2 experiment to advance through them.

## 6. Sources re-read: what they support, and what they do NOT

The [paired source-to-claim audit](source-claim-audit-2026-10-25.md) contains the detailed chain. Key sources:

- [Boden 1998, *Artificial Intelligence*](https://doi.org/10.1016/S0004-3702(98)00055-1): distinguishes **combination, exploration, transformation** of conceptual spaces. The concept predates Shadowseed; its existence is not SSL evidence.
- [Wiggins 2006, *New Generation Computing*](https://doi.org/10.1007/BF03037332): conceptual-space theory can be formalized and compared with search; a formal search account is not automatically the full generative-possibility question.
- [Schapiro, Black & Varshney 2025 (ICCC)](https://arxiv.org/abs/2504.18687): changes to enabling constraints/axioms have transformative potential **in their graphical theory**; this does not show an LLM can discover them.
- [Di Bona et al. 2025, *Nature Communications*](https://doi.org/10.1038/s41467-024-55115-y): observed higher-order combination patterns and a model of evolving accessible links; **higher-order** means combination order, not a Bloom-style cognitive ladder, and not proof of semantics.
- [Kendall & Gal 2017, NeurIPS](https://papers.nips.cc/paper_files/paper/2017/hash/2650d6089a6d640c5e85b2b88265dc2b-Abstract.html): distinguishes Bayesian epistemic/aleatoric uncertainty in computer vision; **does not validate 'a missing relation sensed in an LLM's latent space'**.
- [Gao et al. 2025, H-Neurons preprint](https://arxiv.org/abs/2512.01797): hallucination-associated activation/probes/interventions in studied models; **not evidence of a model introspecting missing creative possibilities**. SSL's local small-model Layer G null remains bounded.
- [Park, Choe & Veitch 2024, ICML](https://proceedings.mlr.press/v235/park24c.html): counterfactually grounded concept directions and geometry; **not an anti-embedding complement**.
- [Si, Yang & Hashimoto 2025, ICLR](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea94957d81b1c1caf87ef5319fa6b467-Abstract-Conference.html): human-blind reviewed LLM research proposals were rated more novel than researcher proposals on their study, but less feasible and generation less diverse. **A strong challenge to claims that LLMs simply cannot produce new ideas**; also no proof of Q2.
- [Suzgun et al. 2025, *Nature Machine Intelligence*](https://doi.org/10.1038/s42256-025-01113-8): models in evaluated settings cannot reliably distinguish belief, knowledge and fact; **do not use verbal self-assessment as an internal truth/absence detector**.
- [Anthropic 2025, introspection research report](https://www.anthropic.com/research/introspection): reports limited, condition-dependent internal-state reporting with many failures; **not a general introspective power** and not independent replication of SSL.
- [Generative AI and scientific novelty evaluation, *Scientometrics* 2026](https://doi.org/10.1007/s11192-026-05792-x): small-sample proposal-ranking study finds GPT-4o disagreements linked to human novelty judgments; **does not identify causal next-token mechanisms or prove all LLMs suppress novelty**.

Strong counterexamples belong in the analysis: some models produce genuinely novel-looking work in human review; some self-evaluation is unreliable; novelty counts and meaningful validity can diverge. No single study resolves our exact coupled question.

## 7. Explicitly rejected shortcuts (not competing theories)

- **Omission detection/RAG completeness**: useful products, not the thesis.
- **Bigger model alone**: serious capability factor, not by itself a distinct Shadowseed mechanism.
- **Negative embedding vector / 'anti-embedding space' as an asserted geometry**: no validated definition; preserve the metaphor only.
- **H-neuron hallucination detection = finding unchosen relations**: non sequitur; study separately.
- **FunSearch**: successful evolutionary program search with an external evaluator, **different research question**; keep outside the direct Shadowseed elimination.
- **More combinations or higher-order novelty counts = transformed conceivability**: too weak.
- **Any newly invented relation operator = scientific discovery**: too weak and subject to arbitrary rule-relaxation artifacts.
- **A strong model produces a new proposal = model knew it was internally missing**: unsupported introspection.
- **The current Gate is too strict, therefore reduce authority checks**: changes influence rules, not evidence of possibility formation.

## 8. Practical decision and change boundary

1. **Do not run another GPT-5 test yet.** The 24-call failed pilot is archived and its automatic paid trigger retired. More tokens would fix output completeness but not construct validity.
2. **Do not write a new accepted ADR** and do not alter existing trace/weight, Gate or production data structures.
3. Use this **mechanism competition** (H0–H5) and the *five meanings of possibility* as the anchor for designing **contrasting cases**; allow a case to falsify a favored theory.
4. **Completed documentation correction:** The [amended Q1/Q2 protocol](revised-q1-q2-experiment-2026-10-25.md) now makes new relation kinds one *optional* branch. This does **not** pass G0 or authorize running a model.
5. When a new independent G0 design has valid positive *and negative* conceptual cases in at least two distinct families and meaningful discriminators between H0–H5, implement the minimum research harness. Only then decide if a paid strong-model run is informative.

**The strongest current conclusion is methodological:** the two-clause research question survives; the old candidate mechanisms are still competing; the first tested proxy did not measure the intended phenomenon. This is not a negative result about the hypothesis itself.

## Provenance and governance

- [Full original thesis](../possibility-space-thesis.md), unchanged.
- [Conversation history and user's corrections](conversation-record-2026-10-24.md), reconstructed not verbatim full export.
- [Literature source map](literature-map-2026-10-24.md) and [new source/claim audit](source-claim-audit-2026-10-25.md).
- [First protocol, now historical](first-discriminating-experiment.md); [revised schema-focused candidate protocol](revised-q1-q2-experiment-2026-10-25.md).
- [First GPT-5 experimental archive PR #220](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220) (24 calls; 16 parseable, 8 incomplete).

No changes to code, seeds, ADRs, API secrets or production behavior are warranted by this reorientation.
