# Source-to-claim audit for Shadowseed's fundamental possibility-space inquiry

> **Date:** 2026-10-25. **Status:** bounded primary-source and repository-source audit; not a systematic literature review, research-integrity allegation, formal EAI classification, or an experiment.
> **Scope:** Evaluate the **fit of evidence to specific claims**. A publication describing a plausible mechanism is not experimental proof that Shadowseed implements it. The original historical files remain authoritative as a record of *intent*, not necessarily scientifically verified claims.
> **Read with:** [first-principles reorientation](first-principles-reorientation-2026-10-25.md) and [full literature map](literature-map-2026-10-24.md).

## The unchanged user-defined question

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

## How to read this audit

- **Source says:** limited to direct material read in source records (publisher abstract/primary repository file, unless otherwise specified).
- **Defensible inference:** what the cited source can reasonably support.
- **Unsupported leap:** a tempting broader claim the source cannot establish.
- **Decisive evidence needed:** what additional study, intervention or independently validated comparison would justify moving beyond the boundary.
- The strength of a source for *its own claim* is distinct from its suitability for our **coupled Q1+Q2** question. No composite score.

### S01 — Original 4.5 completion-as-negative-signal proposal

**Source:** [Original SSL 4.5](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/legacy/00_shadow_seed_learning_4_5.md), introduction, §2–4 and §7.

**Source says:** It proposes using LLM completion capabilities "negatively" to detect structural absences, recording atomic candidates with separate `trace` and `weight`. The document characterizes this as the model recognizing what is absent in its own knowledge/latent space.

**Defensible inference:** This is the foundational **hypothesis and architecture proposal**: attempt to turn generative prediction into candidate-absence exploration; weightless presence is distinct from authorized influence.

**Unsupported leap:** A plausible candidate, an omitted answer element, or a generated "missing relation" is *direct evidence that the model introspected a latent internal absence*. It is not.

**Decisive evidence:** Same-model matched output baselines plus direct or intervention-based evidence where technically possible. Distinguish generated hypotheses from estimates of model-internal states. If only behavior is measured, label behavioral rather than introspective.

### S02 — Original 4.5 epistemic uncertainty citation

**Sources:** [Original 4.5 §2.1](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/legacy/00_shadow_seed_learning_4_5.md), [Kendall & Gal (NeurIPS 2017)](https://papers.nips.cc/paper_files/paper/2017/hash/2650d6089a6d640c5e85b2b88265dc2b-Abstract.html).

**Source says:** The scholarly study distinguishes **epistemic uncertainty about model parameters** from observation/data noise and evaluates Bayesian methods for computer-vision prediction. SSL 4.5 draws an analogy to observing structural omissions from language-model completion.

**Defensible inference:** The distinction between reducible model uncertainty and irreducible measurement noise is useful background.

**Unsupported leap:** Kendall & Gal validated a detector for *which ideas/relations a language model failed to generate*, or that an unmentioned topic constitutes measured parameter uncertainty. **Citation is theoretical analogy, not evidence that SSL's core ability exists.**

**Decisive evidence:** An explicit model of what quantity is estimated, calibration under known generative uncertainty, independent ground truth for a specific task, and tests separating uncertainty from novelty/diversity/omission.

### S03 — Original 4.5 H-neuron premise

**Sources:** [SSL 4.5](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/legacy/00_shadow_seed_learning_4_5.md), [Gao et al. (arXiv 2512.01797; 2025 preprint)](https://arxiv.org/abs/2512.01797), [Pro Layer G conclusion](../h-neurons-conclusion.md).

**Source says:** Gao et al. identify sparse hallucination-associated units/signals in tested models and report controlled effects linked to over-compliance. The legacy SSL proposal *interprets these as a possible route* for model-internal support for novel candidate/falsification processes.

**Defensible inference:** Model-internal intervention research is a viable *separate research direction*; some prediction-related features may be causally studied.

**Unsupported leap:** Every modern LLM has the same signal; H-neurons imply a model can recognize its **unselected creative possibilities**; or a hallucination detector can certify that a proposed unknown relation is true/false. The original SSL text is **stronger than the paper warrants** on these points. Pro's own Layer G small-model results did not replicate the targeted dialectical signal in models up to 0.5B, and explicitly limit the inference.

**Decisive evidence:** An independent, controlled stronger-model replication targeting **non-selection/relational possibility** rather than hallucination labels, with shuffles and direct causal checks. No model-internal probe may bypass the Gate.

### S04 — June 2026 Shadowseed vision

**Source:** [Original generative vision](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md), §1–5 and §8, explicitly marked **vision not proof**.

**Source says:** Shifts from "what should have been in this answer" to "what could have been"; a candidate may remain speculative and move across turns until later context makes it investigable. It describes a broader intent than trivial omission checking.

**Defensible inference:** An early **generative gap intuition**, delayed judgment and longitudinal candidate retention genuinely precede the October research thesis.

**Unsupported leap:** "The conversation selects a useful seed" proves truth, model-internal access, or that retention is literally costless. Storage, attention, selection pressure, prompt/context budgets and bias are real resource/confound categories. "Interesting later" is not automatically evidence of a transformed future possibility space.

**Decisive evidence:** Longitudinal active-candidate versus equivalent normal-note memory, same-model, same-budget, delayed held-out consequences; include rare candidate decay/TTL failure analysis and candidate-specific ablation.

### S05 — The canonical/current Pro safety decision

**Sources:** [ADR-001](../../architecture/adr/ADR-001-validation-gate-authority.md), [ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md), and [ADR-012](../../architecture/adr/ADR-012-model-recurrence-recognition.md).

**Source says:** A seed may be an atomic investigable gap, doubt, missing relation, contradiction or relevant what-if; it is born without authority. Only the Gate changes authority, with an additional point-of-use influence decision. Recurrence is an **observation**, not independent evidence. Recognizer calibration contained both cross-turn false merges and bounded model-based judgments.

**Defensible inference:** **Useful existing contracts** for keeping uncertain candidates investigable without making them true or user-influential. A multi-candidate transformation may be recorded as a higher-level research object with provenance without assuming it already fits a single atomic seed.

**Unsupported leap:** That current seed storage, similarity clustering, recurrence or acceptance demonstrates the existence of Q1 nonselected ideas or the Q2 possibility-generation mechanism; or that safety gates should be weakened because they inhibit creative exploration.

**Decisive evidence:** Keep observation/authority separation unchanged while separately measuring *research exploration* and *downstream influence*. Any production schema change needs its own justified ADR, not a retroactive reinterpretation of accepted invariants.

### S06 — Conceptual spaces and transformation in creativity

**Sources:** [Boden, *Creativity and Artificial Intelligence* (1998)](https://doi.org/10.1016/S0004-3702(98)00055-1) and [Wiggins, *Searching for Computational Creativity* (2006)](https://doi.org/10.1007/BF03037332).

**Source says:** Boden separates familiar-idea combination, search *within* a conceptual space, and transformations enabling previously impossible ideas. Wiggins studies formalizations and their relationship to search.

**Defensible inference:** These are crucial conceptual precedents for distinguishing Q2 from more generated ideas and more graph edges.

**Unsupported leap:** That every conceptual transformation must introduce a named new relation type, or that the theory has empirically demonstrated the user's specific LLM-probability-and-cross-time hypothesis. This is a **conceptual framework**, not an SSL experiment.

**Decisive evidence:** Define independent before/after working frames and meaningful consequences, compare frame-shift with mere extra samples and paraphrases, and rule out trivial rule relaxation.

### S07 — Graphical theory of transformational creativity

**Source:** [Schapiro, Black & Varshney, *Transformational Creativity in Science: A Graphical Theory* (2025, ICCC)](https://arxiv.org/abs/2504.18687).

**Source says:** A graphical mathematical account of enabling constraints; changes to axioms in the authors' model have the largest transformational potential. Historical scientific examples illustrate a framework.

**Defensible inference:** One promising **formal branch** for Q2 tests involving altered rules/relations.

**Unsupported leap:** This is **the unique interpretation** of the original Shadowseed question; or a model-generated change of rules must be meaningful or factual. The paper does not test Shadowseed or establish that frozen LLM weights themselves change.

**Decisive evidence:** Independently predeclare valid transformations, prevent trivially adding all relations, and compare against condition/meaning reframing cases with **no new named predicate**.

### S08 — Higher-order novelties and an evolving adjacent possible

**Source:** [Di Bona et al., *The Dynamics of Higher-Order Novelties* (Nature Communications 2025)](https://doi.org/10.1038/s41467-024-55115-y).

**Source says:** First occurrences of combinations at different orders have distinct empirical novelty-growth patterns; a random-walk model on an evolving network reproduces patterns and can open adjacent opportunities when new nodes/links appear.

**Defensible inference:** Novel combinations may shape future **observable access** to other combinations in such processes. It is a formal/data-driven precedent for thinking across time rather than simply counting unique answer strings.

**Unsupported leap:** Higher order means Bloom-style cognitive superiority; counts of more triples than pairs imply *conceptually more profound possibilities*; a language model has this exact network or creates meaningful new science merely by generating combinations. **The work concerns combinatorial order and modeled dynamics, not a Bloom pyramid.**

**Decisive evidence:** Causal, counterfactual candidate-dependent downstream effect on independently validated tasks, not just higher combinatorial novelty count.

### S09 — Representation geometry and its limits

**Source:** [Park, Choe & Veitch, *Linear Representation Hypothesis and the Geometry of LLMs* (ICML 2024)](https://proceedings.mlr.press/v235/park24c.html).

**Source says:** Gives counterfactually defined conditions for linear concept representations, probes/steering, and a geometry sensitive to the metric. The paper experimentally evaluates studied models.

**Defensible inference:** Internal representations can be studied *causally and formally*, and model choice/metric matters.

**Unsupported leap:** An inverse or complement of an embedding directly encodes all unselected semantic possibilities. **Unembedding** is a standard output-representation concept, not our proposed **anti-embedding** metaphor.

**Decisive evidence:** Define a concept family, controlled intervention and behavior/likelihood change. Treat probing without causality as correlation, not an explanation for missing ideas.

### S10 — Genuine model idea-generation is already formidable

**Source:** [Si, Yang & Hashimoto, *Can LLMs Generate Novel Research Ideas?* (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea94957d81b1c1caf87ef5319fa6b467-Abstract-Conference.html).

**Source says:** In blinded review with over one hundred NLP researchers, generated ideas were rated more novel than human-expert ideas on the study's measures, somewhat less feasible; the authors identify self-evaluation and diversity challenges.

**Defensible inference:** A simplistic "LLMs cannot create new ideas" premise is empirically unsound. A **strong model with disciplined generation** is an essential baseline, and novelty and feasibility should remain separate.

**Unsupported leap:** These ratings prove that an LLM changed its conceptual possibility space, can evaluate its own novelty reliably, or that Shadowseed adds anything.

**Decisive evidence:** Include a strong model on matched budgets and blind **independent** relevance/feasibility assessment; require downstream candidate-specific causal effect, not only "rated novel".

### S11 — Model self-knowledge is not a reliable absence oracle

**Sources:** [Suzgun et al., *Language models cannot reliably distinguish belief from knowledge and fact* (Nature Machine Intelligence 2025)](https://doi.org/10.1038/s42256-025-01113-8); [Anthropic, *Emergent introspective awareness* (research report 2025)](https://www.anthropic.com/research/introspection).

**Source says:** The first finds important limits in distinguishing epistemic categories in tested models. The second reports experimental signs of **limited and condition-dependent** internal state reporting, while warning that such introspection often fails.

**Defensible inference:** Introspection is **an empirical candidate**, not a self-certifying way to read internal "what I know but didn't say". The positive research report and the negative epistemic-discrimination evidence should both inform test design.

**Unsupported leap:** A model confidently says "I did not consider X", therefore X was absent from its representations; or "the model reported a latent vector" proves it directly measured its internal state.

**Decisive evidence:** An independently controlled internal intervention or access experiment, with fake/sham injected concepts and correct counterfactual predictions. Black-box language is at most behavioral report.

### S12 — Novelty selection and evaluation confounds

**Source:** [*Generative AI bias against scientific novelty* (Scientometrics 2026)](https://doi.org/10.1007/s11192-026-05792-x).

**Source says:** In a **small specific study** of 139 historical research proposals, AI-ranking disagreements with human decisions were associated with human novelty scores; authors explicitly acknowledge their design cannot identify the responsible model mechanism.

**Defensible inference:** Novelty *evaluation* can be biased; a selection/validation mechanism may favor familiar-looking outputs. Consider independent blinded reviewers and disagreement/novelty-stratified outcomes.

**Unsupported leap:** All generative AI inevitably suppresses novelty, or next-token prediction has been experimentally isolated as the cause of the observed proposal-review pattern. Small retrospective selection studies do not establish general LLM laws.

**Decisive evidence:** Cross-model and cross-domain tests of model rating, human rating and independent task validity, with experimental manipulation rather than attributing mechanism from correlation.

### S13 — First real Pro pilot, a methodological negative

**Source:** [Run 40136015917](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40136015917), [artifact 12576709359](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40136015917/artifacts/12576709359), [full negative/limitation report](https://github.com/E-AI-MODEL/shadowseed-pro/blob/research/possibility-pilot-20261024/docs/research/possibility-space/first-live-pilot-result-2026-10-24.md).

**Source says:** 24 real GPT-5 calls; 16 completed parseable JSON, 8 incomplete; checks for ordinary graph edges and fixed rules, not relations transformed across time. D was a different prompt, not the actual longitudinal SSL system. Strong controls in some cases already produced the useful missing links.

**Defensible inference:** API plumbing succeeded; the preliminary assay did not meet the protected research question's **construct validity**, nor did it produce a fair efficacy comparison. Preserve its raw failed results.

**Unsupported leap:** A red workflow proves SSL is false, a true positive bridge proves possibility-space expansion, or increasing output-token budgets alone turns the assay into a test of Q1/Q2.

**Decisive evidence:** Redesign the *meaning of measured possibility* first; independently validate conceptual/interpretive/relational changes; test with a strong baseline, matched context, actual cross-turn weightless memory and candidate ablation.

## Five source-critical research rules

1. **Do not convert original vision into demonstrated mechanism.** Historical SSL claims about internal model knowledge remain research premises until measured. Distinguish repository **implementation facts** from published external evidence.
2. **Do not convert generated plausibility into truth.** The status `candidate`, model confidence, repetition, embedding similarity and human interest are different observations. A verified external claim needs independent support.
3. **Do not convert creativity theory into an LLM experiment.** Boden/Schapiro/Di Bona give conceptual or mathematical frameworks and empirical data from specified processes, not evidence that SSL already expands future conceivability.
4. **Do not confuse mechanism and output.** More ideas/novelty ratings/graphs, better answers, and human preference are not the same outcome as causally altered future investigability.
5. **Credit the actor that provides the possibility.** Model, researcher who designed the test, human domain evaluator, retrieved source and external tools can each contribute. A successful hybrid result is **not** an AI-only effect.

## Research decision

The **highest-risk unverified premise** is that an LLM's probability-oriented generation can reveal or causally exploit *meaningful unselected possibilities* instead of just responding to extra human prompting or search budget. The **second critical premise** is that a selected/reinterpreted candidate can make genuinely different **subsequent** possibilities reachable, beyond more textual continuations.

**Therefore:** remain mechanism-agnostic at first; test both premises separately and jointly in contrasting examples, with all historical nulls and constraints preserved. The Gate stays authoritative for actual influence. No new architecture/ADR, no return to RAG completeness, no further paid model run before the constructs are independently validated.

This document offers **a transparent evidence boundary**, not an EAI education outcome or a certainty rating for the whole theory.
