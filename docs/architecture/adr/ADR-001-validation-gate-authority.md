# ADR-001: The Validation Gate Is the Sole Authority-Changing Boundary

- Status: Accepted (with amendments — see "Amendments" and "Implementation status")
- Date: 2026-07-20
- Accepted: 2026-07-20, after issue #17 verified runtime/test/documentation alignment
- Related issue: #8

## Context

Shadow Seed Learning (SSL) is intended to preserve and develop weak, uncertain, minority, recurring, contradictory, and potentially useful signals without treating them as established facts too early.

That requires a permissive shadow-learning layer. However, if recurrence handling, probes, human feedback, SSOT integration, contradiction processing, or caller-specific helpers can independently change weight, promotion state, contradiction authority, or influence eligibility, those mechanisms can bypass the Validation Gate and become more important than the Gate itself.

The architecture therefore needs a strict distinction between observation and authority.

## Decision

The Validation Gate is the only component allowed to change a seed's authority.

Canonical rule:

> Signals may be collected outside the Gate. Authority may change only through the Gate. Actual influence still requires a separate point-of-use decision.

### Operations allowed outside the Gate

Components may directly:

- create a seed with zero authority;
- update trace and recurrence observations;
- record typed support or contradiction signals;
- store SSOT, retrieval, human, probe, task-outcome, or dialectical observations;
- reactivate dormant material into an investigatory state;
- calculate relevance and candidate surfacing scores;
- preserve conflicting hypotheses and unresolved questions.

These operations must not grant or restore influence eligibility.

### Operations reserved for the Gate

Only the Validation Gate may:

- increase or decrease weight;
- promote, demote, or re-promote a seed;
- apply authority effects from recurrence, probes, feedback, SSOT, retrieval, or dialectical results;
- apply contradiction penalties;
- resolve or supersede a contradiction for authority purposes;
- restore eligibility after contradiction;
- change any field that determines whether a seed may influence downstream behavior.

### Point-of-use control remains separate

Gate approval is necessary but not sufficient for influence.

A separate point-of-use contract decides whether an authorised seed may affect a specific action in a specific context. It must consider at least:

- current promotion state;
- positive weight;
- a valid Gate event reference;
- unresolved contradictions;
- policy and action type;
- contextual relevance;
- an auditable decision record.

## Typed signals and policy profiles

The Gate should receive typed signals instead of overloaded booleans such as `external_evidence=True`.

Illustrative signal kinds include:

- recurrence;
- SSOT;
- human review;
- retrieval;
- dialectical survival or refutation;
- probe outcome;
- task outcome;
- contradiction;
- contradiction resolution.

SSOT is optional. Different Gate policies may require different combinations of signals.

Examples:

- exploratory: strong recurrence and no unresolved contradiction;
- research: multiple independent support signals;
- evidence-backed: verified external evidence;
- creative: bounded utility feedback;
- high-impact: verified evidence plus human approval.

All profiles still use the same Gate. The active policy determines the required evidence and permitted authority change.

## Recurrence

Recurrence is a valid SSL signal and may contribute to promotion under an appropriate policy.

It must not be mislabeled as external evidence or counted twice under different names. Gate events must record recurrence as recurrence and identify the policy that allowed it to affect authority.

## Contradictions

Contradictions should neither be silently erased nor create an irreversible lifetime ban by default.

Contradictions should have an explicit lifecycle, such as:

- open;
- resolved;
- superseded;
- withdrawn.

Recurrence alone must not resolve a contradiction. Resolution requires a recorded basis, followed by Gate revalidation before authority can be restored.

## Prompt boundary

Surfaced seeds may contain instruction-like text. SSL should not aggressively sanitize candidate thought content because that can remove meaningful signals.

The runtime should instead use a lightweight structural boundary that clearly marks surfaced seeds as quoted candidate data rather than instructions, with bounded length, bounded count, and adversarial tests.

## Audit requirements

Every Gate decision must record:

- seed identifier;
- previous authority state;
- typed input signals and source references;
- active policy identifier;
- weight before and after;
- status before and after;
- contradiction state;
- decision and reason;
- timestamp and event identifier.

Every point-of-use decision must reference the relevant Gate event and be recorded before influence occurs.

## Consequences

### Positive

- preserves SSL's permissive learning philosophy;
- prevents helper-specific authority bypasses;
- makes multiple causes of weight explicit and auditable;
- supports optional SSOT and multiple operating profiles;
- enables contradiction recovery without silent forgetting;
- separates learned authority from contextual permission to influence.

### Costs

- requires typed signal and event models;
- requires refactoring direct weight mutations;
- requires migration of existing tests and documentation;
- adds policy and audit complexity.

## Invariants

1. Detection never grants authority.
2. Shadow-memory operations may change observations, trace, recurrence, metadata, and recorded signals without granting influence.
3. Only the Validation Gate may change weight, promotion state, contradiction authority, or influence eligibility.
4. Every authority change must be attributable to typed signals, a named policy, and a Gate event.
5. No authorised seed may influence an action without a separate recorded point-of-use decision.
6. No helper, benchmark, probe, SSOT component, or caller may directly mutate authority fields.

## Amendments (accepted second opinion)

The proposal was accepted **with material amendments** from an independent
review. The amendments do not change the doctrine; they make it concrete and
falsifiable:

1. **Policy profiles.** Only the two profiles with concrete semantics ship as
   real policies: `exploratory` (the explicit default) and `evidence_backed`.
   `research`, `creative`, and `high_impact` are documented examples that raise
   a clear error if requested, until their required signal combinations are
   justified. The default policy is never implicit.
2. **Decay and expiry.** Trace decay is a pure observation and stays outside the
   authority path. Expiry is the one lifecycle transition that also resets
   authority (it clears weight), so that reset is routed through the single
   authority path. Influence eligibility is *derived* from authority state, not
   stored as a separate field.
3. **Contradictions supplement the scalar.** Contradiction records are the
   canonical blocking source; the legacy `contradiction_score` scalar is
   retained for compatibility and migration, and a legacy positive scalar with
   no records is treated as one open contradiction.
4. **Authority versioning.** The manager stamps a monotonic `authority_version`
   on every authority change. A point-of-use decision links to a Gate event of
   the seed's *current* version, and both decision-time and replay reject stale
   authorizations.
5. **Encapsulation and migration.** Authority fields are constructor-excluded
   and guarded; the seed registry is a read-only view. Persisted seeds are
   restored via `ShadowSeed.from_dict` / `SSLManager.restore_seed` (preserving
   the original version). Explicit, clearly-named unsafe hooks remain available
   for tests and benchmarks — an unsupported escape hatch, not a claim that
   mutation is technically impossible for third parties.

## Implementation status

Implemented and verified on the alignment branch (issues #10–#17):

| ADR area | Where | Verified by |
|---|---|---|
| Typed signals, policies, Gate events | `shadowseed.gate` | `test_gate_contracts` |
| Encapsulated, non-bypassable authority | `SSLManager`, `ShadowSeed` | `test_authority_encapsulation`, `test_gate_signal_routing` (static guards) |
| Effects routed through the Gate | `submit_signals`, chat/SSOT/feedback/probe | `test_gate_signal_routing` |
| Contradiction lifecycle + recovery | `shadowseed.gate.contradictions`, `SSLManager` | `test_contradiction_lifecycle` |
| Atomic, replayable point-of-use | `shadowseed_agent` contract + audit | `test_point_of_use` |
| Prompt-data boundary | `shadowseed.surfacing` | `test_prompt_boundary` |
| English alignment + enforcement | core runtime, checker | `test_language_alignment` |
| End-to-end invariants | — | `test_ssl_invariants` |

The full suite passes (545 passed, 4 skipped), ruff is clean, the wheel builds,
and the CLI runs. Umbrella issue #8 tracks final closure once this branch is
merged.
