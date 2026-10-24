# External research environments: feasibility screen for Shadowseed Q1/Q2

> **Reviewed:** 2026-10-25. **Status:** primary-publication and project-description desk screen, NOT executed, NOT independently reviewed, NOT a G0 pass, and NOT a license/security approval.
> **Scope:** What established evaluations might supply an independent environment for studying model-originated, *later* investigable possibilities? This comparison does not claim that another project implements Shadowseed or proves the two-part thesis.
> **Decision authority:** [verbatim research question](../../possibility-space-thesis.md), [first-principles rivals H0–H5](../first-principles-reorientation-2026-10-25.md), [current dynamic inquiry proposal](dynamic-inquiry-protocol-candidate-2026-10-25.md), [unfilled independent review](dynamic-inquiry-independent-review.md).

## Suitability criteria, not a ranking of scientific quality

For this specific question, an existing environment would need to allow (i) model-originated, not answer-key-supplied inquiries; (ii) an independently executable family of *unanticipated* queries/interventions; (iii) multiple prospectively distinguishable subsequent questions; (iv) no-opportunity/negative cases; (v) matched ordinary-model and ordinary-notes controls; and (vi) sequestered post-preregistration cases. An excellent general benchmark may fail one or more of these requirements.

| Prior work | What its primary source actually supplies | Possible use in Shadowseed research | Where it stops for Q1/Q2 |
| --- | --- | --- | --- |
| [DiscoveryWorld](https://papers.nips.cc/paper_files/paper/2024/hash/13836f251823945316ae067350a5c366-Abstract-Datasets_and_Benchmarks_Track.html) (NeurIPS 2024) | Simulated scientific tasks with interactive experiments, hypotheses, procedural checks and explanatory-knowledge scoring | Candidate **E1** environment interface and negative/control tasks | Original goals, world rules and scoring remain authored; task completion or a novel-looking hypothesis is not a validated change in the *later question space* |
| [DiscoverPhysics](https://arxiv.org/abs/2605.26087) (arXiv v2, 2026) | 22 on-demand simulated physics worlds; agent chooses experiments; held-out trajectory prediction and explanation evaluation | Candidate **E1/E2** source of independent dynamic observations and prospective tests | The supplied end goal is still to infer physics laws; explanation scoring partly uses an LLM judge. Neither open-ended second-order inquiry nor SSL-specific value follows automatically |
| [WorldTest / AutumnBench](https://proceedings.mlr.press/v306/warrier26a.html) (ICML 2026) | 43 interactive grid worlds, 129 tasks and environment-level reachability/intervention queries | Good technical precedent for environment-level independent queries and controlled belief updating | Query families and benchmark tasks are set by the authors; successful answering is not proof that the agent originated a previously unavailable future inquiry |
| [AgentIdeaBench](https://github.com/HKUST-KnowComp/AgentIdeaBench) (2026 project) | Matched active-literature-retrieval versus supplied-reference ideation settings | Strong **active-search** comparator and warning against rewarding an adapter for extra information | Literature retrieval and evaluated research proposals are not an independently evolving environment with candidate-caused later questions |
| [Into the Unknown](https://arxiv.org/abs/2610.19159) (2026 preprint) | Research directions and necessary conditions contributed by domain scientists; evaluates agent follow-up work and evidence integrity | Precedent for domain-expert meaningfulness and integrity review, with no simple reference answer | The follow-up research direction originates with the study designer; cannot be counted as a model-created direction |
| [ScienceWorld](https://aclanthology.org/2022.emnlp-main.775/) (EMNLP 2022) | Grounded text-based scientific experiment tasks | Useful baseline/calibration for elementary experiment selection | Predetermined curricular tasks and scientific rules cannot alone establish the two-clause thesis |

**Important distinction:** DiscoveryWorld, WorldTest and DiscoverPhysics supply relevant *measurement ideas*; none has been shown here to support the complete Q1+Q2 comparison with actual weightless cross-turn persistence. We have not inspected package-level execution APIs, random seeds, model/tool budget accounting, dataset leakage resistance or repository licenses sufficiently to endorse reuse. Do not copy code or cases on the basis of this paper-level screen.

## Provisional, falsifiable choices

- **E1 contender:** inspect DiscoveryWorld and DiscoverPhysics for an independent intervention executor that accepts queries not enumerated in a fixed target-answer list. An agent may be allowed to investigate *any safe admissible question* but the evaluator must be able to reject vague, redundant or invalid proposals without consulting the proposing model.
- **E2 contender:** examine whether WorldTest's environment-level queries or DiscoverPhysics's changeable experiments can support a *second independently checked question originated after a first finding*. The fact that a benchmark has multiple questions is not enough.
- **C/B comparators:** borrow the experimental distinction between active search and supplied information from AgentIdeaBench, while giving each Shadowseed comparison arm exactly the same sources, tools, contexts and total costs.
- **Scientific judgment:** use an independent domain reviewer for meaningfulness and integrity, as in the motivation behind Into the Unknown, never a single unblinded model judging its own novelty.

An apparently impressive experimental result must be rejected as **non-discriminating** if it can be explained by ordinary active learning, a supplied tool, more context, established feature construction, or known experiment planning. A failure to find a suitable external environment is a legitimate G0 result; do not invent a toy world and redefine the thesis to make it pass.

## Required verification before selecting any environment

1. **Executable interface:** inspect an exact repository revision, API calls, allowed actions and independent scoring rules. Verify a *general* query/intervention validator, reproducible resets, bounded runtime, invalid-request handling, and genuine opportunities for unscripted follow-ups.
2. **Rights and safety:** check source-code, data and model licenses separately; network/tool permissions, sandboxing, dependencies, privacy, and cost. None is presumed approved here.
3. **Information separation:** hidden rules and held-out second-order consequences must not enter model prompts, retrieval, candidate memory or public examples. Public benchmark tasks are exploratory controls only, not sealed confirmatory test material.
4. **Pre-study controls:** independently authored positive and negative examples; no-opportunity environments; sham candidates; matched strong-model, ordinary-note and full-history baselines; exact candidate ablation; equal tool and feedback budgets.
5. **Independent verdict:** one independent technical evaluator reviewer and a separate construct/method reviewer must approve a particular environment version and held-out plan. The [review ledger](dynamic-inquiry-independent-review.md) remains **UNFILLED**.

**Decision:** no benchmark selected or imported, no G0 approval, no new paid calls or automatic Actions dispatch, and no change to product runtime, trace, weight, TTL, TrTL or Validation Gate. The next deliverable is a source-and-code-verified environment suitability review, not an efficacy run.
