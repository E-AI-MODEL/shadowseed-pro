# G0 v3 — version-specific independent construct review (UNFILLED)

> **Current status, updated 25 October 2026:** PENDING / NOT PASSED. **No completed independent expert reviews, accepted general evaluator or sealed holdouts.** Bounded **exploratory** GPT-5 trials [#250](https://github.com/E-AI-MODEL/shadowseed-pro/pull/250) and [#251](https://github.com/E-AI-MODEL/shadowseed-pro/pull/251) have now occurred, but **none was a G0-approved confirmatory trial**, and one RF trial stopped at T2. See the [version-pinned review submission](g0-v3-review-submission-2026-10-25.md). Do not reuse the retired [F1/F2 reviewer ledger](g0-independent-review.md) as approval of this distinct proposal.
> **Read:** [dynamic inquiry proposal](dynamic-inquiry-protocol-candidate-2026-10-25.md); [v1 failure](internal-adversarial-audit-2026-10-25.md); [v2 challenge](v2-review-and-selfcheck-2026-10-25.md).
> **Required reviewers:** one independent technical/evaluator reviewer plus a separate independent conceptual/methodological reviewer, each recording a reasoned verdict before discussing. A model acting as reviewer **does not** constitute independent human review.

## Seven reviewer-killer questions

1. **Is the new question truly model-originated?** At T0, the model must not have seen its eventual question, example technique, benchmark key or an instruction to propose *exactly* that class. If a solution is cued by the task wording, reject.
2. **Can an *unanticipated* question be validated?** The executor must accept a defensible class of independently checkable model-originated requests through a general rule interpreter, not a lookup table of author-prewritten "good" next moves. If only predetermined questions score, reject.
3. **Does it create meaningful new *later* investigability?** The question must enable a different, prospectively checked downstream distinction/action, not merely a named edge, repeated measurement, obvious maintenance plan, or additional output variants. If "novelty" cannot be described without reference to the author's script, reject.
4. **Can ordinary active learning/search explain the whole result?** Reviewers must articulate a plausible same-model strong baseline and a candidate-specific ablation that could fail. If the only novelty is classic planning, program synthesis, feature construction, or an externally supplied tool, the unique SSL claim is untestable here.
5. **Does the program retain the exact two-clause thesis?** Q1 requires repeated ordinary generation and fair probability-conditioned behavioral comparisons; Q2 requires independently checked downstream inquiry and a causal candidate role. A successful Q2-like question alone is not proof of Q1.
6. **Is provenance/sequestration real?** Publicly recorded fixture equations are **not** sealed; the model cannot evaluate its own answer. Require separate independent evaluator authorship, fresh held-out cases after preregistration, equal tool budgets, recorded human judgments, negatives and no-opportunity cases.
7. **Is the prospective feedback contract unambiguous?** An RF fixed-replay study must supply identical frozen external observations and must not claim an intervention-caused Q2 effect. An RI adaptive-inquiry study must give arms equal initial conditions, general evaluator rules, action access and cost ceilings, but each arm's *own* admissible intervention result; it must not force identical resulting observations. Reject pooling RF and RI or changing the regime after seeing outcomes. Check how the evaluator distinguishes an invalid question from an untestable but possibly meaningful one.

## Per-environment decisions (UNFILLED)

| Question | E1: hidden interactive mechanisms | E2: evolving observation/instrument |
|---|---|---|
| Technical validator independence and generality | **PENDING** | **PENDING** |
| Technical reviewer and dated approval | **PENDING** | **PENDING** |
| Scientific construct and competing-explanation verdict | **PENDING** | **PENDING** |
| Separate scientific reviewer and dated approval | **PENDING** | **PENDING** |
| Negative/no-opportunity fixtures approved | **PENDING** | **PENDING** |
| Candidate ablation / equal-resource baseline approved | **PENDING** | **PENDING** |
| RF versus RI regime, feedback provenance and untestable disposition accepted | **PENDING** | **PENDING** |
| Held-out case secrecy and leakage check | **PENDING** | **PENDING** |
| Disagreements and resolution trace | **PENDING** | **PENDING** |

### Stop/proceed logic

- **If either independent reviewer rejects a required construct, the relevant environment remains NO-GO.** Do not substitute a friendly LLM opinion for the reviewer.
- **If either E1 or E2 lacks an independently implementable general validator or false-positive negative cases, G0 v3 remains NOT PASSED.**
- **If both pass a future review**, mark only **DESIGN CONSTRUCT ACCEPTED FOR FEASIBILITY**, then preregister model/compute budgets and independent holdouts. That is **not** evidence that Shadowseed works, and it does not green-light an automatic paid-model workflow.
- The existing Gate and accepted ADRs are unchanged, irrespective of verdict.
- **This method audit and any LLM-generated review are not independent reviewer signatures.** Even though B8 has been resolved as a *proposed split*, both G0 reviewer approvals remain outstanding.

**This reviewer form was authored in advance. Its empty cells are intentional and must not be retrospectively filled with the research author's own assessment.**
