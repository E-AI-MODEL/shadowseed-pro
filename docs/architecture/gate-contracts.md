# Validation Gate contracts

This document describes the typed contracts every authority decision uses. They
live in the `shadowseed.gate` package and implement Phase 1 of the Validation
Gate alignment (issue #10) and the data model in
[ADR-001](adr/ADR-001-validation-gate-authority.md).

These are data contracts. They do not yet change how `SSLManager` mutates
authority — wiring the runtime onto them is a separate step (issues #11 and #12).

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

Two concrete policies ship today:

- **`exploratory`** (the default): strong recurrence *or* external support, with
  no unresolved contradiction, proposes a positive change. This keeps SSL
  permissive — recurrence alone can promote.
- **`evidence_backed`**: requires a verified external-evidence signal. Recurrence
  may accompany it but can never satisfy the requirement alone.

The default policy is **explicit**: `DEFAULT_POLICY_ID` names it, `default_policy()`
returns it, and `resolve_policy(None)` resolves to it. `resolve_policy` raises on
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
