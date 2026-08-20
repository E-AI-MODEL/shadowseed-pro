# ADR-007: Hosted Production Is a Separate Deployment Architecture

- Status: Accepted
- Date: 2026-08-20
- Related: issue #88, ADR-005, ADR-006

## Context

The current Workbench is local-first and single-user. A hosted service changes the trust model: network clients are untrusted, multiple principals may share infrastructure, identifiers become authorization boundaries, provider costs become abuse targets, and data deletion/retention must be enforced per tenant.

Treating `--allow-remote` or a reverse proxy in front of the current Workbench as hosted production would not add those guarantees.

## Decision

`production-ready/hosted` is a separate product/deployment profile and requires an explicitly designed service boundary.

The hosted profile may reuse the canonical Shadowseed runtime, Gate, application concepts and compatible storage contracts, but it must not reuse the local Workbench process as the security boundary.

## Required hosted architecture

A hosted implementation must provide:

1. authenticated principal identities;
2. tenant/workspace identity on every durable object;
3. authorization on every session, seed, evidence, feedback, export and administrative operation;
4. explicit roles/capabilities, including a distinct evidence-verifier capability;
5. a tenant-safe hosted database rather than a shared local SQLite workspace;
6. TLS-only external access with trusted-proxy configuration;
7. secure session/token handling and CSRF/CORS/security-header controls appropriate to the chosen protocol;
8. per-principal and per-tenant request, concurrency and cost limits;
9. abuse controls and administrator kill switches;
10. managed service credentials and secrets;
11. tenant-scoped retention, export and deletion workflows;
12. content-minimized operational logging and separate security audit logging;
13. liveness, readiness, dependency health, SLOs, alerting, rollback and incident procedures;
14. cross-tenant adversarial tests before any hosted production claim.

## Authority model

Hosted identity and authorization do not replace the Validation Gate.

The hosted service decides whether the authenticated actor is permitted to submit an authority-bearing action in a tenant. The Gate then evaluates the submitted typed signal under the active policy. Hosted code may not directly edit weight, status, promotion or current Gate authorization.

A verified evidence record must bind the actor, tenant, session, seed, evidence identity, authorization decision and resulting Gate event.

## Tenant isolation rule

Tenant scope is mandatory, not optional metadata.

Every persistent read/write API must either derive tenant scope from trusted server context or require a server-validated tenant key. User-supplied object identifiers alone may never select data outside that scope.

Backups, exports, jobs, caches, vector indexes and operational tooling are included in this rule.

## Network/provider rule

Users may choose only provider/model endpoints allowed by deployment policy. Arbitrary user-controlled base URLs or network destinations are not part of the default hosted contract because they can create SSRF, credential forwarding and data-exfiltration risks.

Provider retry or fallback behavior may not silently change model, evidence or Gate semantics.

## Non-goals of Phase 0

This ADR does not select a hosted framework, identity provider, cloud, database vendor or deployment platform. Those are later implementation choices constrained by this contract.

No hosted runtime implementation is authorized by Phase 0.

## Acceptance criteria

This ADR may be accepted when reviewers agree that:

- hosted production is not an extension of `--allow-remote`;
- all hosted durable objects are tenant-scoped;
- identity/authz and Gate authority remain separate decisions;
- a hosted database and security boundary are mandatory;
- hosted work begins only after `production-ready/local` architecture is stable or an explicit decision changes the program order.
