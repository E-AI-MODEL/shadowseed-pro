# Validation Gate Alignment Fix Plan

- Status: Proposed
- Related ADR: `docs/architecture/adr/ADR-001-validation-gate-authority.md`
- Related issue: #8

## Goal

Refactor SSL so all authority-changing effects pass through the Validation Gate while keeping shadow learning permissive and SSOT optional.

## Scope

This plan covers:

- typed support and contradiction signals;
- a single non-bypassable authority mutation path;
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

Initial policies:

- exploratory;
- research;
- evidence-backed;
- creative;
- high-impact.

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

## Phase 2: Make the Gate non-bypassable

### 4. Encapsulate authority fields

Prevent callers from directly mutating:

- weight;
- promotion status;
- contradiction authority state;
- influence eligibility.

Use private storage, controlled transitions, or an authority-state object owned by the manager.

Tests must no longer prepare scenarios by directly assigning authority fields unless they use an explicitly unsafe test fixture.

### 5. Route all current mutation paths through the Gate

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

Trace decay and recurrence counting may remain outside the Gate as observations, provided they do not change authority fields.

### 6. Remove overloaded evidence booleans

Replace `external_evidence: bool` and similar arguments with typed signals.

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

- [ ] The ADR is accepted and linked from the architecture documentation.
- [ ] All authority mutations are reachable only through the Validation Gate.
- [ ] Typed signals replace overloaded evidence booleans.
- [ ] Gate policy is explicit for every authority decision.
- [ ] Recurrence is not double-counted or relabelled as external evidence.
- [ ] Probe, human, SSOT, dialectic, and contradiction effects route through the Gate.
- [ ] Contradictions have a recorded lifecycle and recovery path.
- [ ] Every influence decision is atomically decided and recorded.
- [ ] Lightweight prompt-data separation has adversarial coverage.
- [ ] Active repository content is English, excluding archive and documented legacy aliases.
- [ ] Documentation, runtime behavior, and tests state the same invariants.

## Suggested implementation order

1. typed signals and Gate events;
2. policy interface;
3. authority field encapsulation;
4. mutation-path refactor;
5. contradiction lifecycle;
6. point-of-use audit changes;
7. prompt boundary;
8. English translation;
9. documentation reconciliation and final invariant audit.
