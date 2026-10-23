# ADR-011: One Verified Source Promotes in Evidence-Backed Live Sessions

- Status: Accepted
- Date: 2026-10-23
- Refines: ADR-004 (calibration values), ADR-005 (live product defaults)

## Context

Under the `evidence_backed` Gate policy each distinct, operator-verified
source adds one validation step of 0.2 weight. The default promotion threshold
was 0.5. Together these defaults meant a seed needed three distinct verified
sources before it could influence an answer.

That number was never a documented decision. ADR-004 states that it does not
declare a universal number of evidence units and that the weight increment and
promotion threshold are calibration values. The paper and the product
documentation only require verified external evidence.

In the product the operator is the trust anchor: submitting evidence requires
an explicit confirmation that the operator checked the source and that it
supports the seed. Three confirmations from the same operator add little
assurance over one, while the three-source requirement meant ordinary sessions
almost never reached promotion, so testers rarely saw a seed influence an
answer and efficacy studies had no surfaced turns to review.

## Decision

New live sessions created through the Workbench controller (web client and
Gradio) with the Controlled (`strict`) or Assisted (`assisted`) authority
profile use:

- `promotion_threshold = 0.2`
- `min_evidence_for_gate = 1`

so one distinct operator-verified source promotes the seed.

The calibration does not apply when an explicit `gate_strictness` is given,
to Autonomous or Open sessions (exploratory Gate), or to evaluation sessions.
Existing sessions keep their persisted configuration.

## Unchanged

- The Gate policy, its weight increment and its decision logic.
- Evidence identity: the same `source_ref` counts once (ADR-004). Resubmitting
  a source adds no weight.
- Further distinct sources still add weight. Weight orders surfacing when more
  than one promoted seed is relevant.
- Contradictions block immediately and require recorded resolution and later
  revalidation.
- Relevance selection and the point-of-use check still decide whether a
  promoted seed is used.
- Recurrence remains observation, never evidence.

## Consequences

- One verified source is enough for a seed to become eligible for use in the
  default product modes.
- A single wrong or poisoned source can promote a seed. The mitigations are the
  operator confirmation, the contradiction path, and relevance and point-of-use
  checks; they are unchanged.
- The default web authority mode is Controlled, matching the non-regression
  contract in `docs/product/authority-profiles-ux.md`.
