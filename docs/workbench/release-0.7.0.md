# Shadowseed Workbench 0.7.0 Research Preview

Version 0.7.0 is the production-local assurance candidate built on the existing live `evidence_backed` authority model. It hardens the single-user local Workbench, persistence/recovery, operator authorization, release provenance, and the contradiction-resolution product path without expanding the hosted or multi-user claim.

This file does not declare `production-ready/local`. That claim remains gated by `docs/architecture/production-acceptance.md`, exact-SHA release verification, the independent assurance record, and the required unchanged candidate soak.

## What changed

### Production-local authorization and authority boundaries

- authority-bearing product actions use the trusted `ActorContext` and workspace/scope capability checks;
- contradiction resolution is available through the supported production-local UI and remains routed through the application boundary and Validation Gate;
- the resolution UI lists only live sessions and currently blocking seeds;
- resolving a contradiction does not directly restore seed weight or bypass point-of-use authorization.

### Persistence, integrity, recovery, and lifecycle

- production SQLite state, authorization state, and authority ledger changes use the production repository contract;
- protected integrity-anchor checks fail closed on tampering, deletion, reorder, anti-rollback mismatch, and unsupported newer schema;
- supported recovery covers backup/restore, crash recovery, intentional audited restore, workspace deletion, and integrity diagnostics;
- `shadowseed doctor` remains the operator-facing integrity/permissions check.

### Local deployment boundary

- the production-local launcher remains bound to IPv4 loopback only;
- provider and input failure paths are tested to avoid partial authority/state mutation;
- workspace erasure and cleanup reporting remain explicit;
- hosted authentication, tenant isolation, public-network deployment, and multi-user claims remain out of scope.

### Release and supply-chain assurance

- the required `build` status runs with `always()` after the Linux/macOS/Windows `production-local` matrix and explicitly fails unless that matrix succeeds;
- release publication is bound to the exact current protected `main` SHA and verified standalone manifests;
- `Release Workbench` creates Sigstore-backed GitHub artifact attestations before publication for every checksum-listed subject and for `SHA256SUMS` itself;
- `Production Release Assurance` is read-only and verifies the trusted checksum-manifest attestation, exact release file set, checksums, provenance, all subject attestations, and unchanged `main`;
- native Apple notarization, Apple Developer ID signing, and Windows Authenticode signing are not claimed.

### Codex follow-up review

The Phase 5 follow-up review closed the reported CI propagation, release-attestation trust-direction, and production-UI reachability gaps. Subsequent Codex findings on initial seed population, filtering to blocking seeds, live-session filtering, and workflow documentation were addressed with regression coverage before merge.

## What did not change

- New candidates start with positive trace and zero steering weight.
- Recurrence is observation, never external evidence.
- Ordinary new Workbench sessions use `runtime_mode = live` and `evidence_backed`.
- Validation Gate remains the authority owner.
- Contradictions remain blocking until explicitly resolved through the authorized boundary.
- Point-of-use authorization remains mandatory.
- Same-message SSL-off controls remain non-mutating.
- Optional research backends and hosted production remain outside the `production-ready/local` claim.
- The PolyForm Noncommercial License 1.0.0 terms remain unchanged.

## Production-local promotion requirements

A `v0.7.0` publication is still only a release candidate until all final production-local evidence is green on the exact tagged commit. Required final evidence includes:

- protected `main` exact SHA and successful required checks;
- successful Linux/macOS/Windows frozen standalone self-tests and manifests;
- verified release checksums, provenance, SBOM, lockfile, wheel, sdist, and license;
- trusted pre-publication artifact attestations plus a successful read-only Production Release Assurance run against the exact tag;
- no unresolved P0/P1 production finding;
- the required unchanged candidate soak and normal local Workbench/`shadowseed doctor` use record.

Any code change after the candidate is selected resets the soak clock. Hosted production requires the separate controls defined by the accepted architecture and is not implied by this release.