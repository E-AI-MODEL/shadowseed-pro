# ADR-006: Production-ready/local Is a Single-User Local Deployment Contract

- Status: Accepted
- Date: 2026-08-20
- Related: issue #88, ADR-001, ADR-004, ADR-005

## Context

Shadowseed v0.6.0 is a local-first research/tester product. The canonical live runtime already separates candidate presence from authority, uses the `evidence_backed` Gate policy for ordinary product sessions, and performs a separate point-of-use authorization before a promoted seed may influence an answer.

Those SSL contracts are not the main reason the current product is not production-ready. The remaining gap is the product and operational boundary around the runtime: attributable authority-bearing actions, durable audit integrity, schema upgrades and recovery, resource controls, deployment safety, observability, supply-chain assurance and repository governance.

A single word, `production-ready`, is too broad. A local single-user application and a hostile-network multi-user service have materially different security and operations requirements. Treating the current Gradio process with `--allow-remote` as a hosted production architecture would blur those boundaries.

## Decision

Shadowseed will use deployment-qualified production claims.

The first production target is:

> **`production-ready/local`**: a single-user, local or managed-workstation Shadowseed product whose normal UI is reachable only through the local machine boundary and whose production claim does not include hostile-network or multi-tenant protection.

An unqualified `production-ready` claim is not permitted while more than one deployment profile exists.

Hosted production is a separate architecture governed by ADR-007 and cannot be inferred from this ADR.

## Canonical runtime remains unchanged in principle

Production hardening wraps the existing runtime. It does not create a second authority engine.

The following remain mandatory:

1. candidates are born with zero weight;
2. recurrence remains an internal observation signal, not external evidence;
3. ordinary live product sessions use `evidence_backed` unless an explicitly different research mode is selected;
4. verified external support requires stable evidence identity under ADR-004;
5. only the Validation Gate applies Gate-controlled authority changes;
6. contradictions remain explicit and blocking until their recorded lifecycle permits later revalidation;
7. promotion is not sufficient for influence;
8. point-of-use authorization requires current authority and a current authorizing Gate event;
9. same-turn SSL-exposed detector output cannot silently become independent recurrence;
10. the paired SSL-off control remains non-mutating comparison data;
11. product UI and authorization code may decide who may request an authority-bearing action, but may not decide the Gate outcome itself.

## Local production trust boundary

The local production profile assumes one logical workspace owner operating within one OS user/workstation security context.

The boundary includes:

- the local product UI and application services;
- the canonical Shadowseed runtime and Gate;
- the local production workspace and its backups;
- local model services explicitly selected by the user;
- hosted model/embedding providers explicitly selected and confirmed by the user;
- platform secure storage used for local product identity or audit signing material.

The boundary does **not** claim protection against a fully compromised host, an administrator with unrestricted OS-level access, malicious kernel/runtime instrumentation, or a user intentionally extracting secrets available to their own account.

Production-local tamper evidence must therefore be described as detection of unauthorized or offline history modification relative to protected local signing/checkpoint material, not as a claim that a hostile machine owner cannot rewrite history.

## Network decision

The production-local launcher must enforce loopback-only binding.

Remote binding remains available, if retained at all, only as an explicitly non-production trusted-environment/development mode. A warning plus `--allow-remote` is not sufficient to make a remote binding part of the production-local profile.

Container documentation and examples must publish the host port on loopback by default. Internal container binding to `0.0.0.0` is acceptable only when the documented host/network boundary prevents unintended remote exposure.

## Product identity and authority-bearing actions

The local production profile does not require a multi-user login screen, but authority-bearing operations must still be attributable.

The product will establish a stable local actor/install identity and construct a trusted `ActorContext` at the product boundary. Verified evidence and other future authority-bearing operator actions must record that actor identity and the authorization decision that permitted the action.

A client-supplied checkbox or bare boolean is not, by itself, production authorization.

The application authorization layer answers:

> Is this actor allowed to submit this class of action for this workspace?

The Validation Gate separately answers:

> Does the submitted signal change this seed's authority under the active Gate policy?

These decisions must remain separate in implementation and audit.

## Persistence and audit decision

Current mutable snapshots remain useful for efficient loading, but they are not sufficient as authoritative production history.

`production-ready/local` requires:

- versioned database migrations;
- an append-only authority/audit ledger;
- tamper-evident event chaining and signing/checkpoint verification as specified by the production persistence contract;
- snapshot-to-ledger consistency verification;
- backup/restore validation that includes schema and audit integrity;
- a documented recovery path for interrupted or failed upgrades.

Historical event payloads must not be silently rewritten to fit new schemas or policies.

## Data lifecycle decision

The local product remains local-first and has no automatic cloud workspace synchronization by default.

Primary conversation and SSL state may be retained until the user deletes the session or workspace, but the product must make deletion behavior explicit and testable. User-created exports and backups are separate files and cannot be represented as deleted merely because the source session was deleted.

Operational logging must be content-minimized by default. Raw prompts, answers, seed text and free evidence notes must not be emitted into normal operational logs or metric labels.

Provider-side retention is outside the local workspace boundary and must remain explicit when a hosted provider is selected.

## Resource and failure behavior

The local product must define bounded input and resource limits for expensive or integrity-sensitive operations. At minimum this includes message size, evidence fields, seed creation, comparison generation, imported backup size, export size and provider timeout/retry behavior.

Limit or dependency failures must fail explicitly. They may not silently switch Gate policy, evidence semantics, model backend, or persistence mode. An operation that fails before commit must not partially mutate seed authority.

## Repository and release governance

`production-ready/local` cannot be claimed while production changes can bypass repository quality gates.

Issue #66 records this administrative production dependency. It was completed on 2026-08-20 after end-to-end enforcement proved that protected `main` blocks pending and failed required CI and permits a passing PR to merge normally. The production claim continues to require that protection to remain active: protected `main`, required applicable checks, no force-push/delete path for normal operation, and a documented break-glass procedure.

Release assurance must extend current exact-source provenance and cross-platform self-tests with the production acceptance contract in `docs/architecture/production-acceptance.md`.

## Licensing decision for this profile

The technical label `production-ready/local` does not grant commercial rights.

The repository is currently distributed under PolyForm Noncommercial License 1.0.0. Under the current repository license, the first production-local claim is therefore limited to uses permitted by that license. A commercial product, commercial deployment or commercial distribution remains a separate legal/release gate and requires rights that are not granted by this ADR.

Documentation must not use technical production readiness to imply commercial licensing.

## Explicit non-goals

This ADR does not provide:

- multi-user authentication;
- tenant isolation;
- hostile-network TLS/CSRF/session protection;
- hosted service rate limiting or cost quotas;
- a shared hosted database;
- hosted incident-response/SLO guarantees;
- a claim that local tamper evidence defeats a compromised host owner;
- proof that SSL improves answer quality in every domain;
- automatic verification that an external evidence source is factually true.

## Acceptance criteria

This ADR may be marked accepted only when the architecture review agrees that:

1. `production-ready/local` is the first production target and remains single-user/local;
2. remote binding is outside the production-local claim;
3. the current Gate and point-of-use authority model remains canonical;
4. authority-bearing product actions require trusted actor attribution before the Gate sees verified support;
5. mutable snapshots are separated from append-only production history;
6. migrations, recovery, data lifecycle and operations have canonical contracts;
7. the production claim is explicitly bounded by the current license;
8. ADR-007 remains the only path to a future hosted production claim.
