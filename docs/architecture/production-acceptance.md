# Production Acceptance Gate

**Status:** Accepted  
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
- applicable Workbench/portability quality gates cannot be bypassed: before a production claim, path-filtered workflows that are part of the production gate must expose an always-reporting terminal/aggregate check (or equivalent safe conditional enforcement) and that result must be required at the repository layer;
- break-glass process documented and validated by a non-destructive administrative/tabletop exercise; routine production acceptance must not weaken the ruleset merely to prove that bypass exists;
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

### Actor, scope and operator authorization

- every production workspace has a stable opaque `workspace_id` independent of filesystem path;
- production authority-bearing operator actions receive trusted `ActorContext` scoped to that workspace;
- local actor identity is stable and attributable within the supported local boundary;
- `evidence.verify` or equivalent capability is checked before verified support construction;
- operator falsification/contradiction submission requires `contradiction.submit` or equivalent capability;
- contradiction resolution requires a distinct `contradiction.resolve` or equivalent capability and recorded basis;
- restore/integrity-recovery actions are explicitly authorized and audited;
- a bare client boolean cannot create a verified production signal;
- authorization and Gate/contradiction decision records are durably linkable by request/workspace/session/seed/event identity;
- authorization metadata cannot be lost while the corresponding authority mutation still commits successfully.

### Persistence, integrity and recovery

- append-only workspace-wide authority ledger implemented;
- authority state mutation and corresponding ledger append commit in the same local SQLite transaction;
- protected live anchor exists outside ordinary workspace/backup data;
- ledger tampering tests cover modification, deletion and reordering;
- valid-old-history rollback test proves that replacing a live workspace with an older internally valid backup fails closed unless the supported restore workflow creates a new epoch;
- snapshot/ledger mismatch is detected;
- database/anchor crash-window recovery is deterministic and tested;
- protected key/anchor loss cannot silently recreate the same audit continuity;
- audit/key rotation or recovery continuity boundaries are explicit;
- versioned migrations exist for every supported schema in the declared support window;
- v0.6.0 bootstrap creates a clearly marked pre-production genesis/import boundary rather than retroactive tamper-evidence claims;
- migration failure/recovery tests pass;
- backup/restore validates schema, session-state compatibility, ledger and current-anchor relation before replacement;
- intentional restore to older state creates an explicit new audit epoch;
- historical event payloads are not rewritten to new semantics.

### Local deployment security

- production-local launcher enforces loopback binding;
- remote/trusted-environment mode is not described as production-local;
- container examples publish loopback by default;
- input/resource bounds exist for expensive or integrity-sensitive operations;
- limit/provider failures do not partially mutate authority;
- arbitrary production provider endpoints are disallowed unless explicitly governed.

### Privacy, deletion and operations

- data lifecycle is documented and executable;
- session deletion removes content-bearing session data and raw evidence material while retaining only the declared minimal content-minimized workspace-ledger continuity data/tombstone;
- full workspace erase removes live workspace/ledger data and attempts cleanup/invalidation of workspace-specific protected integrity material;
- deletion tests detect orphaned rows/files and report incomplete erase;
- backup/export lifecycle is clearly separate from source deletion;
- operational logs/metrics are content-minimized;
- low-entropy/raw content is not naively made permanently discoverable merely by hashing it into the ledger;
- health distinguishes usable local runtime state, integrity state and dependency degradation;
- audit/migration/restore integrity failures are visible and actionable;
- recovery/rollback runbook is tested.

### Secrets and supply chain

- provider secrets remain outside session persistence;
- protected private integrity/signing material remains outside ordinary workspace backups/exports;
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
- missing/wrong actor capability or workspace scope;
- unauthorized falsification/contradiction submission;
- unauthorized contradiction resolution;
- evidence replay across channels;
- prompt-like seed/evidence content;
- stale Gate authorization;
- corrupt ledger and snapshot mismatch;
- replacement with an older valid backup/history;
- crash after database commit but before protected-anchor advancement;
- loss/reset of protected integrity material;
- malicious/oversized restore/export inputs;
- provider timeout/failure during state-changing flow;
- remote production-local launch attempt;
- secret-like values entering persistence/export/log paths;
- session deletion leaving raw content in supposedly content-minimized audit history.

## Exact-SHA release evidence

Before production publication:

1. identify the merged candidate SHA on protected `main`;
2. run all required production gates against that SHA or an artifact provably built from it;
3. verify `main` has not advanced during publication or bind the release to the exact reviewed SHA;
4. verify published assets after download;
5. record the production profile, workspace/schema/audit format versions, workflow/run provenance and known non-goals in release notes.

## Stop condition

`production-ready/local` is achieved only when all mandatory sections are green on the exact release commit. Remaining hosted-only work is not a blocker and must be named explicitly as such.

`production-ready/hosted` requires all local/shared invariants plus the complete ADR-007 hosted gate: authentication, tenant isolation, hosted database, TLS/session/CSRF/CORS controls, rate/abuse limits, managed secrets, tenant lifecycle enforcement, hosted SLO/incident operations and cross-tenant adversarial evidence.
