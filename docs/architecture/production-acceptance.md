# Production Acceptance Gate

**Status:** Proposed  
**Target:** first `production-ready/local`, later `production-ready/hosted` under ADR-007.

## Claim rule

A release may use the label `production-ready/local` only when every mandatory local control below is implemented, tested on the exact candidate commit, and no unresolved P0/P1 production finding remains.

Passing the research benchmark suite alone is not sufficient.

## Mandatory local gates

### Architecture and governance

- ADR-006 accepted;
- production threat model reviewed and current;
- issue #66 repository protection/ruleset active;
- production changes merge through PR with required checks;
- break-glass process documented;
- license wording matches intended permitted use and does not imply commercial rights not granted by `LICENSE`.

### SSL authority invariants

- ordinary live product still uses `evidence_backed` by default;
- recurrence remains non-evidence;
- no direct product authority editor exists;
- verified support uses stable evidence identity;
- contradictions remain blocking until resolved/revalidated;
- current-version Gate link is required at point of use;
- same-turn SSL-exposed candidates remain contaminated;
- paired SSL-off control remains non-mutating.

### Actor and authorization

- production authority-bearing actions receive trusted ActorContext;
- local actor identity is stable and attributable;
- `evidence.verify` or equivalent capability is checked before verified support construction;
- a bare client boolean cannot create a verified production signal;
- authorization and Gate decision records are linkable by request/session/seed/event identity.

### Persistence and recovery

- append-only authority ledger implemented;
- ledger tampering tests cover modification/deletion/reordering;
- snapshot/ledger mismatch is detected;
- versioned migrations exist for every supported schema in the declared support window;
- migration failure/recovery tests pass;
- backup/restore validates schema and audit integrity before replacement;
- historical event payloads are not rewritten to new semantics.

### Local deployment security

- production-local launcher enforces loopback binding;
- remote/trusted-environment mode is not described as production-local;
- container examples publish loopback by default;
- input/resource bounds exist for expensive or integrity-sensitive operations;
- limit/provider failures do not partially mutate authority;
- arbitrary production provider endpoints are disallowed unless explicitly governed.

### Privacy and operations

- data lifecycle is documented and executable;
- session/workspace deletion tests pass;
- backup/export lifecycle is clearly separate from source deletion;
- operational logs/metrics are content-minimized;
- health distinguishes usable local runtime state from dependency degradation;
- audit/migration/restore integrity failures are visible and actionable;
- recovery/rollback runbook is tested.

### Secrets and supply chain

- provider secrets remain outside session persistence;
- negative tests cover logs, exports and errors for secret leakage;
- production dependency resolution is locked/constrained reproducibly;
- dependency/security scan runs in CI;
- release SBOM is generated and verified;
- production/release GitHub Actions use immutable revisions;
- exact-source provenance and checksums remain verified;
- declared artifact/platform signing or notarization path is complete;
- clean-machine production smoke passes on every supported standalone platform.

## Required adversarial evidence

At minimum tests cover:

- forged verified-evidence attestation;
- missing/wrong actor capability or scope;
- evidence replay across channels;
- prompt-like seed/evidence content;
- stale Gate authorization;
- corrupt ledger and snapshot mismatch;
- malicious/oversized restore/export inputs;
- provider timeout/failure during state-changing flow;
- remote production-local launch attempt;
- secret-like values entering persistence/export/log paths.

## Exact-SHA release evidence

Before production publication:

1. identify the merged candidate SHA on protected `main`;
2. run all required production gates against that SHA or an artifact provably built from it;
3. verify `main` has not advanced during publication or bind the release to the exact reviewed SHA;
4. verify published assets after download;
5. record the production profile, schema version, workflow/run provenance and known non-goals in release notes.

## Stop condition

`production-ready/local` is achieved only when all mandatory sections are green on the exact release commit. Remaining hosted-only work is not a blocker and must be named explicitly as such.

`production-ready/hosted` requires all local/shared invariants plus the complete ADR-007 hosted gate: authentication, tenant isolation, hosted database, TLS/session/CSRF/CORS controls, rate/abuse limits, managed secrets, tenant lifecycle enforcement, hosted SLO/incident operations and cross-tenant adversarial evidence.
