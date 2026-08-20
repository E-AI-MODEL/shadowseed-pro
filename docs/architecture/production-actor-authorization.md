# Production Actor and Authorization Contract

**Status:** Proposed  
**Scope:** Product authorization surrounding the canonical Shadowseed runtime.

## Purpose

Shadowseed already decides whether a signal may change seed authority through the Validation Gate. Production needs a separate answer to a different question: who is allowed to submit an authority-bearing operator action.

This contract keeps those decisions separate.

## ActorContext

Production application services will receive a trusted context created by the product boundary, conceptually:

```text
ActorContext
- actor_id: stable non-empty identifier
- scope_id: stable workspace_id or tenant identifier
- capabilities: explicit set
- auth_method: local-install or hosted authentication mechanism
- assurance: metadata needed to interpret authentication strength
- request_id: correlation/idempotency identifier
- policy_version: application authorization policy revision
```

The exact Python type is an implementation decision for Phase 2. Client-controlled form data may not instantiate a trusted context directly.

`scope_id` for the local profile resolves to the stable production `workspace_id`, not a filesystem path or display label.

## Initial capabilities

The local profile should remain minimal:

- `chat.use`
- `session.manage`
- `feedback.record`
- `evidence.verify`
- `contradiction.submit`
- `contradiction.resolve`
- `export.create`
- `workspace.backup_restore`
- `workspace.integrity_recover`

Read-only inspection may be covered by ordinary workspace ownership rather than a large role system. Hosted production may group capabilities into roles, but the underlying checks remain capability/scope based.

## Authority-bearing operation rule

Every operator action that can cause or participate in a Gate-controlled authority transition must:

1. receive trusted `ActorContext`;
2. verify the context scope against the target workspace/session;
3. require the operation-specific capability;
4. validate request fields and stable identities;
5. establish a stable request/idempotency identity before mutation;
6. prepare the minimal actor/authorization metadata that must accompany the operation in the production ledger;
7. invoke the canonical runtime/Gate or contradiction path without granting the application layer direct authority over weight/status;
8. commit the resulting authoritative state change, Gate/contradiction result, actor/authorization metadata and corresponding production-ledger event atomically under the persistence contract;
9. advance/verify the protected external anchor through the recoverable anchor-update protocol.

The application layer may reject the request. It may not force a Gate promotion, contradiction penalty, contradiction resolution or authority restoration. If the authoritative mutation or ledger append cannot commit together, the operation fails and must not be reported as successful.

### Verified evidence

Submitting operator-verified supporting evidence requires `evidence.verify`. A bare `operator_verified=True`, checkbox value or client assertion is never production authorization.

Authorization happens before construction of a production `verified=True` support signal. Stable evidence identity remains governed by ADR-004 and Gate policy semantics remain unchanged.

### Falsification / contradiction submission

An operator-triggered falsification or contradiction action is authority-bearing because it can block influence or reduce authority. Production application services therefore require `contradiction.submit` and actor attribution before invoking the canonical contradiction/Gate path.

This does not change the underlying contradiction doctrine: contradiction records and the Gate remain the canonical authority mechanism.

### Contradiction resolution

Resolving/superseding/withdrawing a blocking contradiction is especially sensitive because it can reopen a path to later revalidation. Production operator resolution requires `contradiction.resolve`, a recorded resolution basis, actor attribution and the existing runtime sequencing. Authorization to request resolution never directly restores weight or influence eligibility.

### Integrity recovery / restore

A supported restore, actor/key reset, audit-epoch transition or integrity recovery action requires `workspace.backup_restore` or `workspace.integrity_recover` as appropriate and must be visible in the workspace ledger. Recovery cannot be a hidden mechanism for resetting authority or audit continuity.

## Local actor identity

For `production-ready/local`, one logical workspace owner is sufficient. The product creates or derives a stable local actor/install identity and uses the stable `workspace_id` as authorization scope.

Private signing/identity material is stored in platform secure storage when such material is required. Private key material must not be persisted in ordinary session configuration, workspace backups, normal exports or operational logs.

A fresh installation, cross-machine import, deliberate identity reset or recovery after protected-key loss must be represented as a new actor/integrity continuity event rather than silently impersonating the old actor.

A local actor identity establishes attribution within the supported product boundary; it is not a claim of multi-user authentication or protection from a compromised OS account.

## Hosted extension

Hosted `ActorContext` must be server-derived from authenticated identity and tenant context. Tenant scope cannot come only from a user-supplied session/seed id.

Hosted authorization must cover all object reads/writes, not just authority-bearing actions. Cross-tenant requests fail without revealing whether the target object exists.

## Audit fields

For an authority-bearing operator action, canonical ledger data must include or commit to at least:

- actor_id;
- scope/workspace_id;
- capability checked;
- authorization policy version;
- request/idempotency id;
- action type;
- session_id and seed_id where applicable;
- evidence source identity/digest where applicable;
- contradiction/resolution identity where applicable;
- timestamp;
- Gate policy id/verdict where applicable;
- resulting Gate event id;
- authority version before and after;
- the minimal authorization result needed for later verification.

Authentication secrets/tokens are never audit fields.

For an authority-bearing mutation, the actor/authz metadata and resulting ledger event must share the same durable transaction as the authoritative state change under the persistence contract. A separate best-effort authorization log is insufficient.

## Failure semantics

Authorization failures occur before the Gate receives an operator-authorized signal/action and before authority state is mutated.

Validation, provider, ledger or persistence failures must not be transformed into a successful authority action. Retries use stable request/event identifiers where necessary to avoid duplicate application.

If production audit integrity is in a fail-closed state, authority-bearing operator actions are unavailable until supported verification/recovery completes.

## Compatibility

Research/evaluation APIs may retain explicit low-level/test paths where already documented, but those paths cannot be represented as production-authorized actions. Production application services must use the `ActorContext` boundary.

The existing Gate remains the authority source of truth.

## Acceptance targets for Phase 2

- forged/bare client attestation cannot create verified support;
- missing `evidence.verify` is rejected before verified Gate submission;
- operator falsification without `contradiction.submit` is rejected before mutation;
- contradiction resolution without `contradiction.resolve` is rejected before mutation;
- wrong workspace/tenant scope is rejected;
- successful operator authority actions are attributable through authorization and canonical ledger/Gate records;
- retries cannot double-apply the same accepted operator action/evidence unit;
- authorization metadata cannot be dropped while the authority transition still commits successfully;
- no authorization helper writes weight/status directly;
- existing Gate, contradiction and point-of-use contract tests remain green.
