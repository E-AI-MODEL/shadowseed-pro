# Possibility-space thesis — annotated research map (2026-10-24)

> **Status:** source-checked literature map, not a systematic review; theory and evidence are kept separate.
> **Scope:** sources relevant to one or both clauses of the [verbatim Shadowseed thesis](../possibility-space-thesis.md).
> **Bibliographic practice:** link to the publisher/proceedings or arXiv landing page; do not copy full papers into this repository without checking license, provenance, version, and whether archiving is actually necessary. Links are not evidence that a paper proves Shadowseed's claims.
> **Language:** editorial analysis is in English; Dutch original research question remains authoritative.

## Fixed research question — unchanged

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

For review, the question contains two inseparable research problems:
- **Q1 — probability-oriented generation and non-selection:** what relations and possibilities are available, selected, not selected, or constructible *outside ordinary generation*, and what can be inferred responsibly from observable outputs or internal measurements?
- **Q2 — emergence and transformation:** can the formation of a relation/possibility change which further possibilities subsequently become conceivable, articulable, or investigable?
The meaning of "possible" must be declared separately: formal possibility under rules, semantic articulability, empirical feasibility, and observed reachability under a fixed budget are **not equivalent**.

## Sources closest to Q2: how a space of possibilities can change

### L01 — Margaret A. Boden, "Creativity and Artificial Intelligence" (1998)
- **Original:** *Artificial Intelligence* 103(1–2), 347–356, DOI [10.1016/S0004-3702(98)00055-1](https://doi.org/10.1016/S0004-3702(98)00055-1).
- **What it says:** distinguishes novel combinations, exploration inside conceptual spaces, and transformations enabling previously impossible ideas.
- **Fit:** **Q2: theoretical foundation (strong conceptual fit)**; Q1: indirect.
- **What it does not show:** an LLM's conditional-generation mechanism can perform, measure, or remember these transformations. Neither is there a proven "anti-embedding."
- **Implication:** distinguish *more diverse answers* from *changing the constraints that define which answers are admissible*; don't claim transformational creativity as a novel Shadowseed invention.

### L02 — Schapiro, Black & Varshney, "Transformational Creativity in Science: A Graphical Theory" (2025)
- **Original:** ICCC 2025 short paper, [arXiv:2504.18687](https://arxiv.org/html/2504.18687), [conference record](https://computationalcreativity.net/iccc25/accepted-papers/).
- **What it says:** formalizes a scientific conceptual space as a dependency graph of enabling constraints; transformations in constraints (especially axioms in their model) can change which artifacts are intelligible.
- **Fit:** **Q2: unusually direct formalization**, useful for explicitly declared before/after possibility sets and anti-tautology controls.
- **What it does not show:** that the LLM, or Shadowseed, discovers those transformations; a theoretical formalization and historical illustrations are not LLM efficacy evidence.
- **Critical test implication:** predefine a constrained domain, the transformation rules, and which new artifact types become expressible. Compare structural change with merely adding examples to the prompt; do not count trivial rule relaxation as a scientific discovery.

### L03 — Di Bona et al., "The Dynamics of Higher-Order Novelties" (2025)
- **Original:** *Nature Communications* 16, 393, DOI [10.1038/s41467-024-55115-y](https://doi.org/10.1038/s41467-024-55115-y).
- **What it says:** analyzes new combinations of items (higher-order novelty) and models exploration on a network whose nodes/edges and reachable combinations evolve as novelties appear; an observed new link can trigger additional possible links.
- **Fit:** **Q2: direct model of novelty leading to later novelty**; Q1: indirect.
- **What it does not show:** that a language model has an equivalent network, that a proposed link is true, or that growing candidate counts equals semantic discovery.
- **Implication:** distinguish new nodes from new relations and **second-order effects**. Include triggered-link controls, temporal dependency, and random-link baselines. This paper is closer to the full Shadowseed aspiration than a standard output-diversity benchmark.

### L04 — Geraint A. Wiggins, "Searching for Computational Creativity" (2006)
- **Original:** *New Generation Computing* 24, 209–222, [DOI landing](https://doi.org/10.1007/BF03037332).
- **What it says:** explores formalizing Boden's conceptual-space view and its relationship to conventional AI search.
- **Fit:** Q2: formal-method background; Q1: indirect.
- **Boundary:** formal search over a space of generative systems does not by itself demonstrate that a particular LLM's model-internal possibility space changes.

## Sources closest to Q1: probabilistic generation, concept geometry, and model capacity

### L05 — Schapiro, Park, Sosa & Varshney, "CreativityNeuro: Steering Language Model Weights to Improve Divergent Thinking and Reduce Mode Collapse" (2026)
- **Original:** [COLM 2026 pre-proceedings](https://proceedings.colm.cc/paper_files/paper/2026/hash/8edb116d5b288b6a9bba4c16ab647702-Abstract-Conference.html), [arXiv:2607.01433](https://arxiv.org/abs/2607.01433). The arXiv record also lists acceptance at an ICML 2026 creativity workshop; distinguish this metadata from the COLM pre-proceedings listing.
- **What it says:** contrastive weight steering changes divergent generation and reduces observed mode-collapse measures on evaluated creativity tasks; includes a reported human-evaluation sample and comparisons with activation steering.
- **Fit:** **Q1: highly pertinent experimental mechanism**, distinct from ordinary "ask for more alternatives." Q2: not demonstrated.
- **What it does not show:** that model weight steering finds empirically valid relations, or creates a new conceptual possibility space as meant in Q2.
- **Implication:** consider this as a **Q1-side intervention comparator** for open-weight models, with controlled changes in output distributions and task validity. Do not rename it "anti-embedding."

### L06 — Park, Choe & Veitch, "The Linear Representation Hypothesis and the Geometry of Large Language Models" (2024)
- **Original:** ICML 2024, [PMLR 235, 39643–39666](https://proceedings.mlr.press/v235/park24c.html).
- **What it says:** formalizes concept directions through counterfactuals in input and output (including *unembedding*) spaces; shows implications for probes and steering vectors and the importance of geometry.
- **Fit:** **Q1: relevant internal-representation method**; Q2: not established.
- **Boundary:** "unembedding" is the standard output-representation term; it is **not** an "anti-embedding space" and not evidence of the geometrical complement of unchosen meaning.
- **Implication:** if a model-internal route is pursued, define an intervention, what representation is inspected, the concept being measured, and controls for spurious probe success.

### L07 — Jiang et al., "On the Origins of Linear Representations in Large Language Models" (2024)
- **Original:** ICML 2024, [PMLR 235, 21879–21911](https://proceedings.mlr.press/v235/jiang24d.html).
- **What it says:** proposes theoretical conditions explaining linear concept representations from next-token prediction and optimization bias, with empirical illustrations.
- **Fit:** Q1: useful connection between the probability-training objective and learned representational geometry.
- **Boundary:** does not imply every meaningful relation is linearly recoverable or that absent concepts can be reverse-indexed by a negative embedding.

### L08 — Geiger et al., "Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability" (2025)
- **Original:** *Journal of Machine Learning Research* 26, paper 83, [publisher record](https://www.jmlr.org/beta/papers/v26/23-0058.html).
- **What it says:** gives a formal framework for interventions and *mechanism transformations* and a range of interpretability methods.
- **Fit:** Q1 internal experiments and Q2 mechanism-change formalization; **methodological**, not direct Shadowseed support.
- **Boundary:** transforming model mechanisms does not automatically establish a novel relation that changes what is conceivable.

### L09 — "Evaluating LLMs' Divergent Thinking Capabilities for Scientific Idea Generation with Minimal Context" / LiveIdeaBench (2026)
- **Original:** *Nature Communications*, DOI [10.1038/s41467-026-70245-1](https://doi.org/10.1038/s41467-026-70245-1).
- **What it says:** tests more than forty LLMs on divergent scientific ideation; broad intelligence benchmarks poorly predict this specialized performance (reported r = 0.357 between the cited benchmarks).
- **Fit:** **Q1: capability-study design**, shows that parameter count and general performance should not substitute for specific evaluation.
- **Boundary:** divergent ideation is not proof of a changed conceptual space or truly novel scientific knowledge. Judge/evaluation design matters.

### L10 — Shi et al., "Semantic-guided Diverse Decoding for Large Language Model" (2025)
- **Original:** NeurIPS 2025, [proceedings](https://papers.nips.cc/paper_files/paper/2025/hash/d9cb74783847e3143cf239ebd6b61cd7-Abstract-Conference.html), DOI 10.52202/085713-4953.
- **What it says:** addresses the distinction between lexical diversity and semantic diversity via embedding-guided decoding.
- **Fit:** **Q1: control and non-SSL alternative**; Q2: not demonstrated.
- **Implication:** compare with meaningful semantic diversification before claiming that Shadowseed accessed unusual relations rather than just more lexical variants.

### L11 — Patel et al., "Are LLMs Becoming Similarly Creative? Evidence from Three Years of Models" (2026)
- **Original:** [arXiv:2608.19437](https://arxiv.org/abs/2608.19437), **preprint**.
- **What it says:** preliminary analysis reports declining diversity in responses to open-ended tasks across successive releases, using semantic similarity.
- **Fit:** Q1 hypothesis generator about homogenization; not a proof of how any individual model encodes unchosen possibilities.
- **Caution:** observational preprint, not a definitive trend or support for Q2.

## Additional sources checked during first-principles reorientation (2026-10-25)

These later checks are source-critical additions to the original 2026-10-24 literature map, not a claim of comprehensive coverage. The [claim-by-claim audit](source-claim-audit-2026-10-25.md) explains why these findings cannot be carried over to SSL without further tests.

### L14 — Si, Yang & Hashimoto, "Can LLMs Generate Novel Research Ideas? A Large-Scale Human Study with 100+ NLP Researchers" (ICLR 2025)
- **Original:** [ICLR 2025 conference record and abstract](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea94957d81b1c1caf87ef5319fa6b467-Abstract-Conference.html).
- **What it says:** In blinded evaluations with 100+ NLP researchers, LLM-generated ideas were **rated** more novel than expert-generated ideas within that study, while rated slightly less feasible. The authors note inadequate idea diversity and unreliable model self-evaluation.
- **Fit:** Strong Q1 **counterevidence against the shortcut** "a strong LLM cannot propose novel ideas"; necessitates a capable same-model no-shadow baseline and independent novelty/feasibility review.
- **Does not show:** That a novel-looking proposal genuinely transforms later conceivability, or that the model introspectively accessed a known missing internal representation. Rated novelty is not external discovery.

### L15 — Suzgun et al., "Language models cannot reliably distinguish belief from knowledge and fact" (*Nature Machine Intelligence* 2025)
- **Original:** [Publisher article, DOI 10.1038/s42256-025-01113-8](https://www.nature.com/articles/s42256-025-01113-8), published 3 November 2025; KaBLE benchmark of **13,000 questions** across 13 epistemic tasks involving 24 models.
- **What it says:** Models show important failures distinguishing types of belief, knowledge and facts, including strong difficulties with first-person false beliefs.
- **Fit:** Q1 **epistemic-discrimination caution**: a model's confident self-report that a possibility is absent, latent, or known cannot serve as ground truth.
- **Does not show:** That no internal access to latent states is ever possible, or directly test the discoverability of unselected relation candidates. The benchmark tests epistemic-language tasks, not the proposed SSL mechanism.

### L16 — Anthropic, "Signs of introspection in large language models" (2025 research report)
- **Original:** [First-party primary research report, 29 October 2025](https://www.anthropic.com/research/introspection), with a linked technical paper.
- **What it says:** Concept-injection experiments provide evidence of **some limited, condition-dependent internal-state reporting** in studied Claude models. The source itself stresses unreliability, including only about 20% successful recognition for the strongest protocol in one reported model/setting.
- **Fit:** Q1 **internal-intervention candidate**, not a contradiction of L15: the studies measure different abilities. Internal representation work may be testable, but cannot be assumed from natural-language claims.
- **Does not show:** An LLM can list its ungenerated possible relations, or that an "anti-embedding" counterpart exists. This is a first-party report, not independent replication of the Shadowseed thesis.

### L17 — Machado, "Generative AI bias against scientific novelty: a cautionary tale from a small-sample evaluation of research proposals" (*Scientometrics* 2026)
- **Original:** [Springer Nature, DOI 10.1007/s11192-026-05792-x](https://doi.org/10.1007/s11192-026-05792-x), published 27 August 2026.
- **What it says:** GPT-4o-ranked decisions were compared with historic human funding decisions for **139** Austrian research proposals. Disagreement was associated with human novelty assessments; the paper explicitly says its design cannot identify the responsible model mechanism.
- **Fit:** A **selection/evaluation-bias warning** for Q1 candidate filtering and human/AI reviewer disagreement, not evidence of generation itself.
- **Does not show:** That next-token prediction causally caused the ranking differences, that all LLMs suppress novelty, or that a weightless seed mechanism avoids this bias.

## Related but not equivalent systems — do not conflate research questions

### L12 — Wang et al., "Towards Diverse Scientific Hypothesis Search with Large Language Models" / EvoDiverse (2026)
- **Original:** ICML 2026, [PMLR 306](https://proceedings.mlr.press/v306/wang26gx.html).
- **What it says:** treats scientific hypothesis generation as diversity-sensitive sampling under a validation budget; describes diversity collapse when selection pressure over-optimizes.
- **Fit:** relevant **selection-bias and baseline methodology** for Q1; possible caution for Shadowseed's trace/TTL/recurrence.
- **Not shown:** that a candidate changes the set of future *thinkable* relations; diversity is not Q2.

### L13 — Romera-Paredes et al., "Mathematical Discoveries from Program Search with Large Language Models" / FunSearch (2024)
- **Original:** *Nature* 625, 468–475, DOI [10.1038/s41586-023-06924-6](https://doi.org/10.1038/s41586-023-06924-6).
- **What it says:** evolutionary program search within a specified task/function space, using a pre-trained frozen LLM and an external evaluator; successful discoveries in cap sets and bin packing.
- **Research-fit verdict:** **OUTSIDE DIRECT SHADOWSEED COURSE COMPARISON**. FunSearch is not searching a model's unselected relational possibilities or asking whether relation formation changes the next conceptual possibility space. It is an example of rigorous external task evaluation, not a direct rival or source of evidence for Q1/Q2.
- **Historical correction:** an earlier discussion incorrectly called FunSearch a "strong challenger" in the Shadowseed course elimination. That comparison is withdrawn, explicitly at the user's request.

## Local Shadowseed evidence and constraints

- [Original SSL 4.5](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/legacy/00_shadow_seed_learning_4_5.md): negative use of completion, weightless candidate, trace/weight split; originally claims internal absence detection more strongly than the evidence currently supports.
- [Original generative vision, 2026-06-14](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md): "could have been" vs. "should have been," multi-turn shadow, **not** an observed proof of changed conceptual space.
- [Pro seed calibration](../seed-calibration.md): 51 of 60 candidate usefulness labels for GPT-5/GPT-6.1-sol from a *model rater*, not independent human judgments; recurrence embedding and semantic-sameness mismatch.
- [Pro small-model calibration](../detector-calibration.md): local 7B can generate more candidates by prompting, without reliably improving fraction of useful candidates. Test specific model capabilities rather than treating size as answer.
- [Pro Layer G null](../h-neurons-conclusion.md): no replicated linear signal on evaluated models <=0.5B; does not rule out nonlinear/internal effects in larger models.
- [Pro ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md): the current runtime admits weightless alternatives and doubts but does not yet test Q2.
- [Pro capability-scaling](../capability-scaling.md): current comparison measures candidate/detector mechanics and some answer-level effects; it does not establish Q1 non-selection mechanisms or Q2 transformations.

## Gaps in literature coverage and follow-up research

1. A validated, comparable measure distinguishing *non-selected*, *non-constructible under fixed rules*, and *constructible only after a conceptual transformation*. A corpus/embedding count alone is inadequate.
2. Paired interventions on model-generation distributions (or observable behavior when logits are unavailable) **and** a second-stage relational-transformation assay within one design.
3. Causal controls demonstrating that a particular relational change — not extra prompt context, increased search budget, or looser validity criteria — enabled later possibilities.
4. Independent domain-level verification and reviewer disagreement handling; generated ideas are not external evidence.
5. Capability testing across different architectures, model sizes, training recipes, prompt strategies, and available interfaces.
6. Whether rare, weightless candidates should be reactivated by *causal relation to future developments*, not only semantic similarity or recurrence.

## Curatorial rule

Add a study only if its specific finding or method changes Q1, Q2, a causal test, or a crucial negative control. Record date, source/DOI, method, claim boundary, and the *non-conclusion*. Do not upload copyrighted article PDFs by default; links with source interpretation are sufficient. An unreviewed paper may motivate a test but not substantiate a settled architecture claim.
