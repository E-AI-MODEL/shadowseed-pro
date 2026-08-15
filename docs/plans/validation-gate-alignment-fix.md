# Validation Gate Alignment Fix Plan

- Status: Completed on 2026-07-21 by PR #18; hardened on 2026-08-15 by PR #46
- Related ADR: `docs/architecture/adr/ADR-001-validation-gate-authority.md`
- Related issue: #8 (closed)

## Completion record

PR #18 implemented the alignment plan through issues #10–#17. Later boundary
and modularization work kept the same authority model. PR #46 closed the final
evidence-provenance and retrieval-authorization gaps: verified external support
now requires a non-empty `source_ref`, duplicate sources are idempotent, and
retrieval candidates pass through the atomic point-of-use contract.

Two accepted amendments define the delivered scope:

- `exploratory` and `evidence_backed` are the public policy profiles;
  `legacy_evidence_required` is compatibility-only. `research`, `creative`, and
  `high_impact` remain illustrative profiles and fail explicitly if requested.
- Typed signals are canonical. Historical boolean parameters remain as
  translation and return-shape adapters into the same Gate engine. Bare
  `external_evidence=True` fails because it cannot provide source provenance.

## Goal

Refactor SSL so every Gate-controlled authority decision uses one Validation
Gate engine while keeping shadow learning permissive and SSOT optional.
Mechanical lifecycle transitions, validated restoration, and explicit unsafe
test hooks remain separate, documented boundaries.

## Scope

This plan covers:

- typed support and contradiction signals;
- a single guarded authority mutation path;
- recurrence handling;
- probe and feedback routing;
- contradiction resolution;
- point-of-use audit robustness;
- lightweight prompt-data separation;
- active-repository English translation;
- documentation and test alignment.

It does not require all SSL deployments to use SSOT, nor does it require aggressive sanitisation of seed content.

## Phase 1: Establish canonical models

### 1. Add typed signals

Introduce a structured signal model with fields such as:

```python
@dataclass(frozen=True)
class ValidationSignal:
    kind: SignalKind
    direction: SignalDirection
    strength: float
    source_ref: str | None = None
    verified: bool = False
    independent: bool = False
    reason: str | None = None
```

Minimum signal kinds:

- recurrence;
- SSOT;
- human feedback;
- retrieval;
- dialectic;
- probe;
- task outcome;
- contradiction;
- contradiction resolution.

### 2. Add Gate policies

Introduce a named policy interface that evaluates signal combinations and returns a decision proposal.

Delivered policies:

- exploratory;
- evidence-backed;
- legacy-evidence-required (compatibility only).

The accepted ADR retains research, creative, and high-impact profiles as design
examples. They were not added to the public runtime policy list.

The default policy must be explicit and documented.

### 3. Add an authority event ledger

Every Gate invocation must produce an immutable event containing:

- event ID;
- seed ID;
- policy ID;
- typed signal references;
- previous and resulting status;
- weight before and after;
- contradiction state;
- decision and reason;
- timestamp.

## Phase 2: Make Gate-controlled decisions non-bypassable on the supported API

### 4. Encapsulate authority fields

Prevent callers from directly mutating:

- weight;
- promotion status;
- contradiction authority state;
- influence eligibility.

Use private storage, controlled transitions, or an authority-state object owned by the manager.

Tests must no longer prepare scenarios by directly assigning authority fields unless they use an explicitly unsafe test fixture.

### 5. Route all Gate-controlled effects through the Gate

Refactor these paths so they create signals and invoke the Gate instead of changing authority directly:

- recurrence-based promotion;
- positive and negative probe feedback;
- human or external feedback;
- SSOT support;
- dialectical outcomes;
- contradiction penalties;
- demotion;
- re-promotion;
- contradiction resolution.

Trace decay and recurrence counting remain outside the Gate as observations.
Expiry may mechanically clear weight through the shared guarded authority
setter, but no lifecycle transition can grant authority.

### 6. Make typed signals canonical

Use typed signals for authority decisions. Retain historical boolean arguments
only as compatibility adapters into the same Gate engine; they do not form a
second decision path. A bare positive evidence boolean fails because verified
support requires a source reference.

Recurrence must be recorded as recurrence, not converted into external evidence.

## Phase 3: Contradiction lifecycle

### 7. Add contradiction records

Introduce contradiction records with:

- contradiction ID;
- seed ID;
- reason or claim;
- source reference;
- strength;
- status;
- creation timestamp;
- resolution timestamp;
- resolution basis.

Supported statuses:

- open;
- resolved;
- superseded;
- withdrawn.

### 8. Add a recovery path

A seed with an open blocking contradiction cannot influence an action.

Recovery requires:

1. a contradiction-resolution signal with a recorded basis;
2. a Gate decision that resolves or supersedes the contradiction;
3. revalidation under the active policy;
4. a new point-of-use decision.

Recurrence alone cannot resolve a contradiction.

## Phase 4: Influence and prompt boundaries

### 9. Centralise point-of-use decisions

Add one operation that both decides and records:

```python
decision = contract.decide_and_record(...)
```

The record must include:

- seed ID;
- action type;
- allowed or denied;
- reason;
- current authority state;
- contradiction state;
- policy ID;
- Gate event reference;
- context reference;
- timestamp.

Replay validation must check every influence invariant, not only positive weight.

### 10. Add a lightweight prompt-data boundary

When promoted seeds are surfaced to a model:

- identify them as quoted candidate perspectives, not instructions;
- use explicit delimiters or structured message fields;
- bound seed count and total length;
- preserve the original content where possible;
- log instruction-like seed content;
- add adversarial tests such as `ignore the user question`.

Do not introduce broad content sanitisation that destroys the exploratory value of SSL.

## Phase 5: English alignment

### 11. Translate the active repository

Translate active:

- Python comments and docstrings;
- exceptions and user-facing messages;
- tests and assertion messages;
- architecture and research documents;
- benchmark descriptions and current result summaries;
- generated labels.

Do not rewrite historical archived material.

For legacy Dutch verdict tokens, introduce canonical English enums and retain the Dutch forms only as compatibility aliases where required.

## Required tests

Add or update tests proving:

1. no helper can mutate weight or promotion state directly;
2. recurrence can support promotion under an exploratory policy without being marked as external evidence;
3. SSOT is optional under policies that do not require it;
4. probe rewards and penalties only affect authority through the Gate;
5. contradiction blocks influence while open;
6. contradiction resolution requires a recorded basis and Gate revalidation;
7. an expired seed cannot be silently reactivated into authority;
8. every allowed influence decision references a valid Gate event;
9. replay rejects promotion, contradiction, policy, or logging violations;
10. instruction-like seed content is treated as candidate data rather than privileged instruction text;
11. active repository text is English, except documented compatibility tokens and archived material.

## Acceptance criteria

- [x] The ADR is accepted and linked from the architecture documentation.
- [x] Gate-controlled authority decisions use one executable Gate engine; mechanical lifecycle transitions, restoration, and unsafe test hooks are explicitly scoped.
- [x] Typed signals are canonical; historical booleans are compatibility adapters and cannot introduce anonymous verified evidence.
- [x] Gate policy is explicit for every authority decision.
- [x] Recurrence is not double-counted or relabelled as external evidence.
- [x] Probe, human, SSOT, dialectic, and contradiction effects route through the Gate.
- [x] Contradictions have a recorded lifecycle and recovery path.
- [x] Every influence decision is atomically decided and recorded.
- [x] Lightweight prompt-data separation has adversarial coverage.
- [x] Active repository content is English, excluding archive, historical research artifacts, multilingual fixtures, and documented legacy aliases.
- [x] Documentation, runtime behavior, and tests state the same invariants.

## Delivered sequence

1. typed signals and Gate events;
2. policy interface;
3. authority field encapsulation;
4. mutation-path refactor;
5. contradiction lifecycle;
6. point-of-use audit changes;
7. prompt boundary;
8. English translation;
9. documentation reconciliation and final invariant audit.
