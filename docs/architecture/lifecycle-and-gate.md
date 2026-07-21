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
monotonic `authority_version` whenever weight, evidence count, or contradiction
score changes, or the PROMOTED boundary is crossed. A point-of-use decision
references that version so a stale authorization can be detected on replay.

The encapsulation is closed on every side:

- authority fields are `init=False`, so the constructor cannot set them — a
  seed is always born weightless;
- `authority_version` is itself an authority field, so it cannot be assigned
  directly; it is stamped automatically by the transition path;
- the seed registry is exposed as a read-only `Mapping` view
  (`SSLManager.seeds`), so callers cannot replace it or insert/remove entries;
  seed creation goes through `add_or_update_seed`.

Persisted seeds are restored through `ShadowSeed.from_dict(...)` /
`SSLManager.restore_seed(...)`, which reinstate the stored authority snapshot
*including the original `authority_version`* without running the Gate. This is
deserialization/migration, not an authority decision, and is the supported path
now that authority fields are `init=False` (so `ShadowSeed(**saved)` no longer
works).

### Restoration is a validated, trusted persistence boundary

Restoration reconstructs authority; it never *grants* it. Because it bypasses
the Gate by design, the boundary is hardened with defense-in-depth validation so
a malformed or internally inconsistent snapshot cannot enter the runtime:

- **Snapshots are validated before installation.** `ShadowSeed.from_dict(...)`
  calls `validate_seed_snapshot(...)` first, so an invalid snapshot raises a
  clear, field-specific `ValueError`/`TypeError` before any seed object is built
  or installed into a manager. Validated fields include `id` (non-empty string),
  `text` (string), `embedding` (non-empty, numeric, all finite), `trace`
  (finite, non-negative), the integer counters `occurrence_count`,
  `turns_dormant`, `evidence_count`, and `authority_version` (genuine integers —
  `bool` is rejected because it subclasses `int` — and non-negative), `weight`
  (finite and within the `[0.0, 1.0]` authority range that every Gate/probe/decay
  path already clamps to), `contradiction_score` (finite, non-negative), `status`
  (a valid `SeedStatus`), and `origin` (when present, a mapping with a valid
  `CandidateType`, a string `detection_basis`, and a string-or-`None`
  `context_ref`).
- **Cross-field invariants** already implied by the runtime are enforced: an
  `EXPIRED` seed must have zero weight and stays terminal after restoration, and
  no restored value may be `NaN` or ±infinity.
- **Restoration preserves authority rather than granting it.** It reinstates the
  stored `authority_version` exactly — validation never increments it — produces
  **no `GateEvent`**, counts as **no new evidence**, and never relabels
  recurrence as evidence.
- **Duplicate replacement is explicit.** `restore_seed(data, *,
  replace_existing=False)` installs a new id, raises on an existing id by
  default, and only replaces a live seed when `replace_existing=True` is passed.
  Validation completes before the duplicate check, and invalid data never
  partially mutates the registry — an existing seed is never silently
  overwritten.

**Compatibility rule.** Fields that `from_dict` supplies defaults for
(`trace`, the counters, `contradiction_score`, `status`, and
`authority_version`) are only checked when present, so a legitimate legacy
snapshot that omits `authority_version` still restores with version `0`, and a
snapshot with `occurrence_count = 0` remains valid. Only `id`, `text`, and
`embedding` are strictly required. No minimum-weight constraint is imposed on
`PROMOTED` snapshots, since a promoted seed whose weight was later reduced is a
legitimate historical state.

Tests and benchmark fixtures that need an edge-case authority state without a
full Gate run use the explicit, clearly-named `ShadowSeed.unsafe_set_authority(...)`
and `SSLManager.unsafe_install_seed(...)` hooks. These are explicit, unsupported
escape hatches, not normal APIs: this repository's runtime never calls them and
a static test over the whole `src/` tree enforces that. They do not claim to
make mutation *technically impossible* for third-party callers — the guarantee
is that the normal public API surface offers no authority mutator.

The `authority_version` bumps only when an authority-determining value actually
changes — weight, evidence count, or contradiction score — or when the PROMOTED
boundary is crossed. An unchanged rewrite does not bump it, and neither does a
pure lifecycle status move (for example ACTIVE → DORMANT).

**Why status is an authority field.** `status` carries both lifecycle presence
(`NEW`/`ACTIVE`/`DECAYING`/`DORMANT`/`EXPIRED`) and the authority state
`PROMOTED`. Rather than split one enum, all status writes go through the single
transition path, and only PROMOTED-boundary crossings affect the authority
version. Lifecycle moves that never cross that boundary change presence without
changing authority.

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

The Gate-event link is selected strictly: the latest event for the same seed
that left it promoted, carries no blocking contradiction, and whose
`authority_version` equals the seed's current version. If no such event exists,
the decision is denied at decision time with reason `stale_gate_authorization`
— a stale promotion is never enough. Blocking-contradiction state passed to the
decision is the canonical value derived from contradiction records
(`SSLManager.is_blocking_contradiction`), not the legacy scalar.

Strict replay (`assert_influence_records_valid(records, gate_events)`, with the
Gate ledger required) re-checks every allowed decision against all point-of-use
invariants — positive weight, `PROMOTED` status, no blocking contradiction, a
present authority version, a present policy id, a present timestamp, and a
Gate-event link that exists, belongs to the same seed, carries an
authority-confirming decision (`promoted`/`validated`), left the seed promoted,
records a non-blocking contradiction state, matches the recorded
`authority_version`, and matches the recorded `policy_id`.

`decide_and_record` is the only route that records — and the only public method
that returns an authorization result (via the recorded `AgentInfluenceRecord`).
For status/UX, `inspect()` returns an `InfluenceInspection` with diagnostic
`blocking_reasons` and **no** `allowed` verdict, so it cannot be used to gate
influence. The chat, retrieval, and agent helper paths all use
`decide_and_record`.

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
