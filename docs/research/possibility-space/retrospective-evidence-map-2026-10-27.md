# Retrospective evidence map — 27 October 2026

> **Status:** research inventory and source-to-claim guide, not an independent replication or a Q1/Q2 result.
> **Reference:** [verbatim possibility-space thesis](../possibility-space-thesis.md). This index does not replace the thesis, a protocol, the product Gate, or the existing [systems manuscript](../../../paper/README.md).
> **Scope:** the research package captured on 27 October 2026 and the GitHub pull-request state checked on that date. It is a *selection* of available experiments, not all historical Actions runs.

## What is present

The archived package used for the exploratory synthesis includes **four main-branch repository source TARs, four Git bundles, and 62 original GitHub Actions ZIPs**. Hash verification against its own inventory reported no mismatches. The 62 ZIPs contain **145 files, 114 distinct SHA-256 payloads**. Repeated files are not independent observations. Four archived main-branch commit histories total **2,577 reachable commits** (222 + 1,039 + 82 + 1,234). Commit counts, workflows, model calls, candidate occurrences, reviews and independently evaluated experiments are different units.

The original archive also contains owner-only and blinding material. **Do not commit the original archive, owner keys, reviewer-arm mappings, full response bundles or other protected research payloads to this public repository.** Keep independent reviewer packets separated from any keys that reveal model or treatment arms. The numbers below are descriptive counts, not an endorsement to expose raw research data.

## Source-to-result register

| Evidence source | Recorded observations | What the material can establish | What it cannot establish |
|---|---|---|---|
| Paired **fixed22**, original Actions artifacts `12494727587`, `12494848845`, `12495100500`, `12495860373` | 196 candidates from 22-turn-per-model, three-conversation suites: GPT-5 109 (28 accepted at run time) and GPT-6.1-sol 87 (71 accepted). Both record **0 promoted and 0 surfaced** seeds. Baseline/SSL suite and answer-system-prompt hashes match. | Detector output, historical intake outcomes and preserved matched-case plain responses. | A memory-effect estimate; neither run exposed an authorised seed. Outputs can vary by sampling. |
| Dutch two-model run, original artifact `12754935105/observed.json`, [draft PR #258](https://github.com/E-AI-MODEL/shadowseed-pro/pull/258) | 12 model/case trajectories (6 investigator-authored cases); **94 candidates**, **48 accepted**, **46 rejected**; 10 complete two-round A/B comparisons; zero completed independent human reviews. | Model-call and candidate lineage, intake decisions, and feasibility of an experimental prompt continuation. | Q2 causation, blinded quality improvement or proof that detected relations were absent from ordinary generation. |
| Intake replay, `src/shadowseed/intake.py` from archived snapshot | Current English rule accepts **189/196** fixed22 texts, whereas historical recorded intake accepted **99/196**. In the Dutch run **all 46 rejections** match a multi-separator predicate; one also matches a broad-substring predicate. | Form- and language-sensitive selection; the older percentages must not be presented as the current English rule. | That rejected texts were scientifically deeper or more valuable; predicate categories can overlap. |
| Exact candidate ablation, original artifact `12613842508/observed.json`, [draft PR #254](https://github.com/E-AI-MODEL/shadowseed-pro/pull/254) | 16 responses in one case, 4 each in D/X/P/N, with a shared starting context. | A bounded intervention-slot comparison. | A general Q2 result without independent semantic review, multiple cases and stronger sampling controls. |
| AB5X original artifact `12469856581/ab5x_raw.json` | 21 of 30 planned review pairs recorded; **0 treated-B pairs**, partial run. | A traceable partial collection and treatment/opportunity failure. | Zero treatment efficacy or benefit. The treatment was not observed. |
| Qwen2.5-7B evidence-efficacy artifacts `12498617077`, `12498945630`, `12500183045` | 12 candidate/evidence opportunities; **0 answer-review pairs** because the candidate path ended before relevant seed exposure. | Bottleneck in selection and exposure. | A null result for the effect of a surfaced seed. |
| Qwen capability-scaling bundle in `benchmarks/results/capability_scaling/` | 43 live candidate occurrences; 0 live surfaced turns. | Instrumentation and candidate counts within that suite. | General value, causality or human-validated novelty. |
| Open-review rounds **022, 023, 025, 029, 031**, see `benchmarks/open_review/rounds/` in [shadowseed](https://github.com/E-AI-MODEL/shadowseed) | 83 recorded seed-effect labels: **57 helpful, 13 no difference, 13 hinder/side-track**. Changing models and protocols; rater provenance and retained review files are uneven. | Mixed registered reviewer perceptions and genuine late-turn interference signals. | 83 independently verified human trials or a pooled 69% causal effect. |
| Model-internal probe report `docs/research/h-neurons-conclusion.md` | A negative/failed preregistered replication on small models, up to 0.5B parameters. | Limits of the tested specific probe under its stated conditions. | Absence of any useful representation in larger models. |

**Older overlap claims (82% / 88%)** originate in specific review rounds 015 and 016 and included task-specific or primed comparisons. They cannot be generalized to the full cross-turn shadow mechanism.

**Earlier AI-labelled “valuable residue” percentages (627 candidate labels)** are not reintroduced as independently verified empirical rates here. Candidate-level semantic coverage requires a predeclared ordinary-generation baseline, reviewer-blind labeling, and checks of retrieval misses and within-conversation dependence. This is open research, not an established discovery count.

## Reading the evidence without collapsing the units

1. **Candidate printed** is not the same as **seed born**.
2. **Seed remembered with weight 0** is not the same as **seed authorised to influence**.
3. **Candidate entered a research prompt** is not the same as **product Gate promotion**.
4. **Different later text** is not yet **a distinct, testable new relation**.
5. **An AI or human-labelled opinion** is not independently corroborated truth.
6. **An experiment stopped before exposure** is not evidence of no effect.

The original research question has two separable clauses. Q1 asks about unselected but investigable relations relative to clearly defined ordinary generation. Q2 asks whether retaining or developing such relations alters subsequent investigability beyond matched controls. **Neither is established by the archived runs.** The archive nevertheless supports a source-grounded exploratory synthesis and a properly targeted next test.

## Publication status and next discriminating checks

The October 2026 synthesis remains an **author-controlled exploratory preprint draft**. Do not describe its figures or count tables as effect-size meta-analysis of independent experiments. Publication need not await proof of Q1 or Q2. Before external deposit, verify source-to-claim references and rater provenance, and clearly disclose non-independent and incomplete evaluations.

For a new test, first predeclare an ordinary same-model baseline (multiple samples **and** deliberate-search comparison) and label every candidate before applying any lexical intake. Use sealed multiturn cases, negative controls and blind human semantic review for Q1. Test Q2 separately with a no-seed arm, equal-length unrelated text, an ordinary persistent note and a true shadow carry, each with matched histories and token budgets. Confirm actual exposure, human-blind downstream evaluation and possible *elimination* of false research paths, not just more questions.

## Where to look

- [Research branch and pull-request map](research-branch-map-2026-10-27.md), including outstanding stacked experiments.
- [Foundational thesis](../possibility-space-thesis.md) and [first-principles review](first-principles-reorientation-2026-10-25.md).
- [Research status](../status.md) and [product-vs-research distinction](../README.md).
- [Canonical baseline/review fixtures](../../../benchmarks/README.md).
- Source TARs, Git bundles, original Actions ZIPs and the private archive inventory are held outside the public repository. Do not infer their contents from a workflow's success badge.
