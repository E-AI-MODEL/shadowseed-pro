# Production Actor and Authorization Contract

**Status:** Proposed  
**Scope:** Product authorization surrounding the canonical Shadowseed runtime.

## Purpose

Shadowseed already decides whether a signal may change seed authority through the Validation Gate. Production needs a separate answer to a different question: who is allowed to submit an authority-bearing action.

This contract keeps those decisions separate.

## ActorContext

Production application services will receive a trusted context created by the product boundary, conceptually:

```text
ActorContext
- actor_id: stable non-empty identifier
- scope_id: workspace or tenant identifier
- capabilities: explicit set
- auth_method: local-install or hosted authentication mechanism
- assurance: metadata needed to interpret authentication strength
- request_id: correlation identifier
- policy_version: application authorization policy revision
```

The exact Python type is an implementation decision for Phase 2. Client-controlled form data may not instantiate a trusted context directly.

## Initial capabilities

The local profile should remain minimal:

- `chat.use`
- `session.manage`
- `feedback.record`
- `evidence.verify`
- `export.create`
- `workspace.backup_restore`

Read-only inspection may be covered by ordinary workspace ownership rather than a large role system. Hosted production may group capabilities into roles, but the underlying checks remain capability/scope based.

## Authority-bearing operation rule

An operation that constructs a `verified=True` support signal or another future authority-bearing operator signal must:

1. receive trusted ActorContext;
2. verify scope against the target session/workspace;
3. require the relevant capability, initially `evidence.verify`;
4. validate request fields and stable evidence identity;
5. record the authorization decision and actor metadata;
6. only then construct/submit the typed ValidationSignal to the canonical Gate;
7. record the resulting Gate event and authority version transition.

The application layer may reject the request. It may not force a Gate promotion.

## Local actor identity

For `production-ready/local`, one logical workspace owner is sufficient. The product should create or derive a stable local actor/install identity and keep any private signing/identity material in platform secure storage when such material is required.

The stable actor identifier may be persisted in audit records. Private key material must not be persisted in ordinary session configuration, exports or operational logs.

A fresh installation or deliberate identity reset must be represented as a new actor identity rather than silently impersonating the old one.

## Hosted extension

Hosted ActorContext must be server-derived from authenticated identity and tenant context. Tenant scope cannot come only from a user-supplied session/seed id.

Hosted authorization must cover all object reads/writes, not just evidence submission. Cross-tenant requests fail without revealing whether the target object exists.

## Audit fields

For an authority-bearing action, audit data must include at least:

- actor_id;
- scope_id;
- capability checked;
- authorization policy version;
- request_id;
- action type;
- session_id and seed_id;
- evidence source identity where applicable;
- timestamp;
- Gate policy id;
- resulting Gate event id;
- authority version before and after.

Authentication secrets/tokens are never audit fields.

## Failure semantics

Authorization failures occur before the Gate receives a verified signal and before authority state is mutated.

Validation, provider or persistence failures must not be transformed into a successful authority action. Retries must use stable request/event identifiers where necessary to avoid duplicate application of an action.

## Compatibility

Research/evaluation APIs may retain explicit low-level/test paths where already documented, but those paths cannot be represented as production-authorized actions. Production application services must use the ActorContext boundary.

The existing Gate remains the authority source of truth.

## Acceptance targets for Phase 2

- forged/bare client attestation cannot create verified support;
- missing `evidence.verify` is rejected before Gate submission;
- wrong workspace/tenant scope is rejected;
- successful evidence support is attributable through authorization and Gate audit records;
- retries cannot double-apply the same accepted evidence unit;
- no authorization helper writes weight/status directly;
- existing Gate and point-of-use contract tests remain green.
