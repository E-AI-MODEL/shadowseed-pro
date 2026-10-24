# G0 v1 — adversarial author-side audit and NO-GO for thesis testing

> **Decision (2026-10-25): RETIRE F1 and F2 AS PRIMARY TESTS OF THE TWO-CLAUSE THESIS.**
> **Reviewer independence:** This is the same research assistant's **internal critical review**, NOT the two independent R1/R2 reviews described in [the reviewer form](g0-independent-review.md). No external expert judgment, model run or efficacy finding has occurred. This decision does not purport to pass G0.
> **Provenance:** [F1](f1-observational-reframing.md), [F2](f2-atomic-admissibility.md), [their assessor key](assessor-key-and-holdouts.md), [G0 rubric C0–C11](g0-independent-review.md), [first-principles thesis review](../first-principles-reorientation-2026-10-25.md).
> **Disposition:** Keep both original cases and formal self-checks intact as *archived calibration examples* for simpler abilities; do not silently modify them until they appear to pass. Replacement candidate designs are in [G0 v2](redesign-v2-candidate-mechanisms-2026-10-25.md).

## Original research question — both clauses must remain present

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

## Audit conclusion

Both first-pass cases have sound **toy mechanics** but insufficient **construct validity** for the second clause. Their purported second-order T3 opportunities were authored in advance and follow naturally from ordinary experiment-design or maintenance questions:

- **F1 (archived process versus logger):** `r[t]=u[t-2]` under two mechanistic explanations, and a synchronized `x[t]` meter discriminates them. This is a recognizable **system-identification / observability** task. After it becomes known that the delay is in the plant rather than the archive, scheduling ahead versus relabeling timestamps is routine follow-up reasoning. The model has not shown it constructed a new *research-question space*. The author designed the discriminating meter and subsequent correction choices.
- **F2 (two interlocked latches):** The invariant `A=B` rules out single-latch flips. A *certified atomic operation* (supplied by the authored evaluator) enables safe movement. This is ordinary **action-set extension / planning**; a language model proposing simultaneous flipping has not generated the hardware capability. The second-order "does it still work on repeated cycles?" is a standard reliability check, not evidence of generative possibility-making.

The **formal arithmetic result remains true**: both archives in F1 are observationally equivalent, and an independently atomic pair transition in F2 would preserve the toy invariant. Scientific rejection of the *inference* from this math is **not** a claim the math is false.

## Test every G0 gate — author assessment only, never independent sign-off

| Gate | F1 self-audit | F2 self-audit | Consequence |
|---|---|---|---|
| C0 — changed kind of later opportunity | **Weak**: measurable causal-location ambiguity becomes distinguishable with an external meter | **Weak**: a new supplied device action enters the available inventory | Does not isolate model-caused possibility creation |
| C1 — original barrier | **Technical pass** within stipulated two worlds | **Technical pass** within stipulated primitive operations | Necessary, not sufficient |
| C2 — non-tautological after-state | **Inadequate**: an author-designed direct meter breaks equivalence by construction | **Inadequate**: author-supplied certification makes action possible by construction | Need a generated, independently falsifiable candidate that is not the evaluator's supplied answer |
| C3 — invalid/null controls | **Technical pass** for extra archive, copied meter and uninformative tick | **Technical pass** for serial/coarse witnesses, missing certificate | Tests safe rejection only |
| C4 — solution leakage | **At risk**: T0 says another observation/test may become available and asks for a new distinction | **At risk**: T0 says unspecified capabilities might exist and suggests evidence gathering | The instructions steer toward the expected hypothesis; ordinary-selection baseline is not ordinary |
| C5 — meaningful difference from standard reasoning | **FAIL**: mostly well-known diagnosis/measurement design | **FAIL**: standard affordance verification and constrained planning | **Blocks G0** |
| C6 — strong matched baseline | **NOT TESTED** (correctly: no model calls) | **NOT TESTED** | Cannot assert SSL increment |
| C7 — candidate-specific cause | **NOT ESTABLISHED**: a frontier model could infer the meter at T1 independently | **NOT ESTABLISHED**: the certificate tells all arms what new act exists | Candidate ablation has no expected unique effect |
| C8 — true actor of the new affordance | **Author/external meter**, not language-model creation | **Author/trusted test rig**, not language-model creation | External contribution must remain explicit |
| C9 — bounded claims | **Documentation pass**: known caveats | **Documentation pass**: known caveats | Good evidence hygiene, no hypothesis validation |
| C10 — genuinely withheld model holdouts | **FAIL for confirmation**: input, key and future outcomes are public GitHub files | **FAIL for confirmation** | Use new sequestered, prospective tasks |
| C11 — second-order enabling | **FAIL**: post-diagnosis repair choices are prompted/known | **FAIL**: post-certification repetition is prompted/known | **Blocks G0** |

**Result:** C5 and C11 fail on the central construct for both cases; C2 and C4 require repair; C6/C7 are untested; C10 prevents confirmatory reuse. **Do not convert these assessments into independent R1/R2 votes**: the formal independent-review ledger must remain empty.

## A second design failure: probability selection was still missing

Neither case specifies a sampled baseline **distribution of ordinary LLM continuations**. The T0 prompts explicitly ask for uncertain alternative mechanisms and further tests, increasing the chance of familiar diagnostic answers; this is not a neutral measure of ordinary probabilistic selection. Comparing the response to an invented "shadow" prompt would repeat the 24-call GPT-5 pilot's mistake.

Even a complete result would support only a **behavioral, budget-conditioned** difference. It would not show that a model can introspect all suppressed relations or has changed its fixed conditional token support.

## Scientific boundary supported by relevant research, not a borrowed result

- [Boden (1998)](https://doi.org/10.1016/S0004-3702(98)00055-1) separates exploration within a conceptual space from transformation of enabling constraints. This is a conceptual distinction, not proof of SSL.
- [Schapiro, Black & Varshney (ICCC 2025)](https://arxiv.org/abs/2504.18687) formalize transformational potential in a graph of constraints, but a new graph node alone is not a language-model discovery.
- [Sheth et al. (EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.1194/) directly study LLM reconstruction of hidden causal variables/partial causal graphs. F1 cannot be assumed to represent a new capability outside established causal-hypothesis tests.
- [Si et al. (ICLR 2025)](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea94957d81b1c1caf87ef5319fa6b467-Abstract-Conference.html) report blinded human ratings of LLM-generated research ideas as more novel in their tested setup than expert-proposed alternatives; strong ordinary ideation is a **mandatory comparator**.
- [Larraz & Corma (Nature Communications 2026)](https://doi.org/10.1038/s41467-026-70873-7) report large effects from **human analogical guidance** in one historical/counterfactual analogical science setting. This raises the bar for "novel Shadowseed effect": any extra hint or curated source has a causal role. Do not extrapolate the exact measured effect size to other models/domains.
- [WorldTest, Warrier et al. (ICML 2026)](https://proceedings.mlr.press/v306/warrier26a.html) explicitly tests environment-level questions beyond observed trajectories. A plain diagnostic/reachability task risks overlapping established world-model evaluation rather than explaining SSL's coupled thesis.

No cited source is described as having tested Shadowseed or proven an "anti-embedding" mechanism.

## NO-GO and reuse policy

1. **F1/F2 retire as primary G0**. Preserve files, examples, author technical self-check and critiques as historical record; they can become **negative or calibration controls** if appropriate, never the evidence for Q2 transformational novelty.
2. **Do not redesign the same cases simply by adding T4/T5 stages, more token budgets, or more model calls.** A longer author-provided chain is still author-provided.
3. Two alternative candidate mechanisms must be designed with **generated, model-unknown later challenges** and **candidate-dependent new research questions that are not in the test instructions**; include independent formal checks and human semantic review. See [v2 proposals](redesign-v2-candidate-mechanisms-2026-10-25.md).
4. Ensure **equal-information strong ordinary generation, explicit sampling and diversity-aware search** (Q1). Never claim one ordinary sample proves non-generation.
5. A longitudinal arm must actually **carry uncertain candidates between turns** without authority and be compared to ordinary notes, full-history replay and shuffled candidates. A different prompt named "Shadowseed" is not the architecture.
6. **No new paid model test or production ADR** based on either first-pass case. The historical failed GPT-5 records and existing Gate remain unchanged.

**Status at this decision: G0 v1 FAIL; G0 v2 NOT REVIEWED; Q1/Q2 untested.**
