# Lifecycle and Validation Gate

## Seed states

The manager models the lifecycle with states such as `NEW`, `ACTIVE`, `DECAYING`, `DORMANT`, `PROMOTED`, and `EXPIRED`.

State and influence are not interchangeable. A seed can be present without being allowed to steer.

## Trace

`trace` records presence, recurrence, and reactivation. It decays through TTL. A dormant seed may regain trace through TrTL when later text matches its trigger or embedding.

Trace never grants influence by itself.

## Weight

`weight` is steering power. New candidates start at `0.0`. The manager can raise weight only through a successful Validation Gate decision.

## Authority encapsulation

The authority fields — `weight`, `status`, `evidence_count`, and
`contradiction_score` — are encapsulated. They cannot be assigned directly:
`seed.weight = 0.6` raises `AttributeError`. All runtime changes go through the
manager's single transition path (`SSLManager._set_authority`), which stamps a
monotonic `authority_version` whenever weight, contradiction authority, or
promotion state changes. A point-of-use decision references that version so a
stale authorization can be detected on replay.

Tests and benchmark fixtures that need an edge-case authority state without a
full Gate run use the explicit, clearly-named `ShadowSeed.unsafe_set_authority(...)`
hook. Production code never calls it.

`trace`, `occurrence_count`, and `turns_dormant` are observation and
lifecycle-support fields and remain freely writable — they never grant
influence on their own.

**Decay and expiry (classification).** Trace decay is a pure observation and
stays outside the authority path. Expiry is the one lifecycle transition that
also resets authority: when a seed expires it loses its weight. That weight
reset is therefore routed through `_set_authority` like any other authority
change, rather than being written directly. Influence eligibility is derived
from authority state (promoted, positive weight, no blocking contradiction), not
stored as a separate mutable field.

## Validation Gate

The gate evaluates stored evidence, contradiction state, and configured thresholds. Its result is logged. Contradiction can block promotion, reduce influence, or reset a seed depending on the manager policy.

## Contradictions

Contradictions are explicit, auditable records (`ContradictionRecord`), not just
a scalar. Each record has a stable id, a reason, an optional source reference, a
strength, a lifecycle status (`open`, `resolved`, `superseded`, `withdrawn`),
and — once closed — a resolution basis and timestamp.

Blocking state is **derived**: a seed is blocked while it has any `open` record.
The legacy `contradiction_score` scalar is retained for compatibility; a seed
with a positive scalar but no records (older data) is treated as carrying one
open contradiction, and `migrate_legacy_contradictions()` can materialize those
into records.

Recovery is possible but never silent. `SSLManager.resolve_contradiction(seed_id,
basis=...)` requires a non-empty basis, moves the open record(s) to a terminal
state, records a `contradiction_resolved` Gate event, and clears the blocking
scalar — but it only *unblocks*. It does not restore authority: the seed must be
revalidated under the active policy (a fresh signal submission) before weight
rises again. Recurrence alone can never resolve a contradiction; resolution is a
separate, explicitly-recorded action.

## Point-of-use contract

Promotion is necessary but not sufficient. `AgentSafetyContract` verifies the seed again before answer modification, retrieval, warnings, probes, or downstream action. It checks promotion state, positive weight, evidence suitability, and the presence of a logged promotion decision.

Decisions are **atomic**: `AgentSafetyContract.decide_and_record(...)` decides and
records in one call, so a decision cannot be used without being recorded. Each
allowed record is linked to the Gate event that authorized it
(`gate_event_ref`) and snapshots the seed's `authority_version`, so a stale
authorization can be detected on replay. Denied decisions are recorded too, with
a stable reason.

Strict replay (`assert_influence_records_valid(records, gate_events)`) re-checks
every allowed decision against all point-of-use invariants — positive weight,
`PROMOTED` status, no blocking contradiction, and a Gate-event link that exists,
belongs to the same seed, and left it promoted — not just positive weight.

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
