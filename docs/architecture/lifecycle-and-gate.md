# Lifecycle and Validation Gate

## Seed states

The manager models the lifecycle with states such as `NEW`, `ACTIVE`, `DECAYING`, `DORMANT`, `PROMOTED`, and `EXPIRED`.

State and influence are not interchangeable. A seed can be present without being allowed to steer.

## Trace

`trace` records presence, recurrence, and reactivation. It decays through TTL. A dormant seed may regain trace through TrTL when later text matches its trigger or embedding.

Trace never grants influence by itself.

## Weight

`weight` is steering power. New candidates start at `0.0`. The manager can raise weight only through a successful Validation Gate decision.

## Validation Gate

The gate evaluates stored evidence, contradiction state, and configured thresholds. Its result is logged. Contradiction can block promotion, reduce influence, or reset a seed depending on the manager policy.

## Point-of-use contract

Promotion is necessary but not sufficient. `AgentSafetyContract` verifies the seed again before answer modification, retrieval, warnings, probes, or downstream action. It checks promotion state, positive weight, evidence suitability, and the presence of a logged promotion decision.

A blocked candidate is not recorded as surfaced. Resurface damping applies only after a seed was allowed and actually supplied to the model.

## Seed origin (observability only)

A seed may carry optional `SeedOrigin` metadata: a `candidate_type` from a
closed vocabulary (for example `missing_relation`, `unstated_assumption`,
`contradiction`), a free-text `detection_basis`, and an optional `context_ref`.
This records *why* a candidate absence was proposed and is written to the
`created` event and the seed export.

Origin is descriptive provenance only. It carries no epistemic force: it never
increases `trace` or `weight`, never counts as evidence, and never influences
the Validation Gate. A convincing detection rationale must still leave
`weight = 0.0`; weight rises only through a gate decision. Any psychological
framing of seeds as "hunches" or "curiosity" is an analogy for readers, not a
claim that the system models mental states — it models controlled candidate
hypotheses.

## Audit requirements

A reviewable run should retain:

- seed creation and normalization events;
- trace and status transitions;
- evidence and contradiction references;
- gate inputs, flags, result, and reason;
- point-of-use influence action and decision;
- surfaced seed identifiers and thresholds;
- baseline and SSL outputs as separate fields.
