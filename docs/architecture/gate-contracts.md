# Validation Gate contracts

This document describes the typed contracts every Gate-controlled authority decision
uses. They
live in the `shadowseed.gate` package and implement Phase 1 of the Validation
Gate alignment (issue #10) and the data model in
[ADR-001](adr/ADR-001-validation-gate-authority.md).

These contracts are wired into the runtime.
`shadowseed.gate.runtime_adapter` is the single executable **Gate-controlled**
authority-decision engine. `SSLManager.submit_signals` is its signal-native policy
entry point; compatibility methods and the bounded probe/resolution authority
workflows delegate into the same engine rather than implementing Gate decisions
in `manager.py`. Mechanical intake/lifecycle transitions (dedup activation, decay,
dormancy/expiry, and TrTL reactivation) remain explicit non-Gate state transitions
through `_set_authority`; invariant tests keep those call sites on an exact
allowlist so a new manager-side authority path cannot appear silently.

## Signals (`shadowseed.gate.signals`)

A `ValidationSignal` is an observation offered to the Gate, never an authority
change. Collecting or recording a signal grants no influence on its own.

- `kind` (`SignalKind`): the support channel — `recurrence`, `ssot`,
  `human_feedback`, `retrieval`, `dialectic`, `probe`, `task_outcome`,
  `contradiction`, `contradiction_resolution`.
- `direction` (`SignalDirection`): `support`, `oppose`, or `neutral`.
- `strength`: a bounded magnitude in `[0.0, 1.0]`. It is not tied to a fixed
  threshold at this layer; policies decide how to use it.
- `source_ref`, `verified`, `independent`, `reason`: provenance and trust a
  policy may require.

**Recurrence is not external evidence.** `EXTERNAL_EVIDENCE_KINDS` contains only
`ssot`, `human_feedback`, and `retrieval`. `ValidationSignal.is_external_evidence`
is `False` for recurrence, so recurrence can never satisfy an
external-evidence requirement by relabeling. The `recurrence_signal(count, ...)`
helper builds a recurrence signal from an occurrence count and always keeps the
`recurrence` kind — it replaces the previous `external_evidence = occurrence_count >= 2`
relabeling in the chat runtime.

## Policies (`shadowseed.gate.policies`)

A `GatePolicy` reads the offered signals plus a read-only `AuthoritySnapshot`
and returns a `GateDecisionProposal`. Policies propose; only the Gate applies.

A policy may weigh **either or both** of its two inputs: the typed observations
offered in this call (`signals`), and the seed's accumulated authority facts
(`authority` — weight, status, blocking contradiction, evidence count,
occurrence count, trace). Policies legitimately differ here. `exploratory` and
`evidence_backed` decide from the offered signals; `legacy_evidence_required`
reproduces the historical accumulation thresholds and therefore decides from the
accumulated facts. Every policy receives the same two arguments, and none of
them mutates state — that difference is in what a policy *reads*, not in what it
is allowed to do.

Two public policies and one compatibility policy ship today:

- **`exploratory`** (the manager and evaluation default): qualifying recurrence *or verified* external
  support, with no unresolved contradiction, proposes a positive change. This
  keeps SSL permissive — recurrence alone can promote, but an unverified external
  observation cannot.
- **`evidence_backed`** (the live conversation default): requires a verified
  external-evidence signal. Recurrence may accompany it but can never satisfy
  the requirement alone.
- **`legacy_evidence_required`**: compatibility-only behavior for the historical
  boolean API. It preserves the configured recurrence, trace, accumulated
  evidence, and weight thresholds while using the same signal-native Gate engine.

The manager-level default policy is **explicit**: `DEFAULT_POLICY_ID` names it,
`default_policy()` returns it, and `resolve_policy(None)` resolves to it. The live
session selects `evidence_backed` unless its caller explicitly chooses another policy.
`resolve_policy` raises on
an unknown id and raises a distinct, actionable error for the documented-but-not-
implemented example profiles (`research`, `creative`, `high_impact` in
`EXAMPLE_POLICY_IDS`) rather than silently falling back.

> Amendment (accepted second opinion): ADR-001 listed five illustrative
> profiles. Only the two with concrete semantics are implemented now; the rest
> are named examples until their required signal combinations are justified.

## Gate events (`shadowseed.gate.events`)

Every Gate invocation produces one immutable `GateEvent`: the audit record of an
authority change (or a refusal to change authority). It captures the typed input
signals, the policy id, the decision (`GateDecision`), status/weight before and
after, the contradiction state before and after, an `authority_version`, a
reason, and an optional timestamp.

`authority_version` is a monotonic counter the manager stamps on a seed's
authority state. A later point-of-use decision (issue #14) references a
`GateEvent` by `event_id` and `authority_version` so a stale authorization can
be detected during replay.

Event ids are deterministic (`gate::<seed_id>::<sequence>`) so replay and
golden-file tests are stable. For deterministic replay hashing, exclude
timestamps or inject a fixed clock rather than relying on wall-clock stability.

## Runtime wiring (issue #12)

The manager exposes two public input shapes that converge on one executable
Gate engine and append one event per call to `SSLManager.gate_events`:

- **`submit_signals(seed_id, signals, policy_id=None)`** — the signal-native
  entry point. Helpers build `ValidationSignal`s and call here; the named policy
  proposes and the Gate applies through `_set_authority`. Recurrence can promote
  under `exploratory` without incrementing `evidence_count`. External support can
  authorize or count as evidence only when `verified=True` and accompanied by a
  non-empty `source_ref`. Evidence identity is the source-and-kind pair, so the
  same `source_ref` under a different external signal kind is distinct support.
  For non-expired seeds, new anonymous verified evidence raises `ValueError`
  before a Gate event or authority change. Expired seeds short-circuit to a
  terminal `EXPIRED` event without applying evidence or authority. Historical
  anonymous signals remain readable during ledger replay.
- **`run_validation_gate[_detailed](...)`** — a deprecated compatibility adapter.
  It translates the historical `external_evidence` / `contradiction` booleans
  into typed signals, selects `legacy_evidence_required` unless another policy is
  explicitly requested, delegates to `submit_signals`, and translates the event
  back into the historical return shape. Because the boolean cannot identify a
  source, bare `external_evidence=True` now fails loudly for a non-expired seed;
  callers must provide a typed verified external signal with `source_ref`.
  Expired seeds remain terminal and record `EXPIRED` without applying the
  synthesized evidence. The old private core alias redirects to this adapter; it
  is not a second decision engine.

Migrated callers:

- **chat** submits changed recurrence under the selected session policy. The
  evaluation default remains `exploratory`; the live default is `evidence_backed`,
  so recurrence alone cannot raise live authority. Live callers offer verified
  external support through `ShadowChatSession.submit_evidence`, which rejects
  non-evidence kinds, opposition, unverified input, and missing `source_ref`
  before invoking the Gate. This boundary validates the attestation shape, not
  the underlying source: the operator or host application must authenticate and
  verify the source before setting `verified=True`. Treating every input as
  verified would bypass the intended evidence-backed distinction.
- **SSOT** (`validate_open_seeds_against_ssot`) passes a verified `ssot` signal
  carrying the source chunk id.
- **external feedback** (`apply_external_feedback`) passes a `human_feedback`
  support signal or a `contradiction` signal.
- **probe feedback** (`apply_probe_feedback`) records a `probe` signal and a
  Gate event for the bounded weight nudge.

A static test (`test_no_direct_authority_mutation_in_non_benchmark_runtime`)
enforces that no runtime module outside `manager.py` writes an authority field
directly.
