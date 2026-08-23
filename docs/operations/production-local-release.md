# Production-local release assurance

This runbook governs the final `production-ready/local` release candidate from issue #88. It does not apply to hosted/multi-user deployment and it does not expand the rights granted by `LICENSE`.

## Candidate rule

A production-local candidate is an exact commit on protected `main`. The candidate is not production-ready merely because a feature branch or pull-request head is green.

Before publication, record:

- exact protected `main` SHA;
- package version and intended tag;
- schema/audit format versions;
- CI run IDs for `test (3.10)`, `test (3.12)` and the required `build` status;
- the `production-local` Linux/macOS/Windows acceptance jobs transitively required by `build`;
- Standalone Workbench run ID and all three platform manifests;
- dependency-audit and SBOM result;
- independent-assurance verdict from #95;
- unresolved production findings, which must contain no P0/P1 item.

## Required repository gate

`build` remains one of the repository-required CI checks. It now has a hard `needs` dependency on the always-running `production-local` matrix in `ci.yml`. Therefore the required `build` status cannot become successful unless Linux, macOS and Windows Workbench/Phase-4 acceptance has completed successfully. The older path-filtered Workbench CI and Workbench Portability workflows remain useful additional evidence, but production acceptance no longer depends on a path-filtered workflow being configured as an unconditional required status.

A change that removes this dependency or makes the production-local matrix conditional is a production-governance change and requires the same protected review path.

## Release artifact verification

The release workflow is bound to the exact SHA from the successful `Standalone Workbench` run on `main`. It must continue to fail closed if `main` advances before publication.

Before publishing, it verifies:

1. the checked-out commit equals the triggering SHA and current `origin/main`;
2. the dependency lock is current;
3. each standalone manifest names the candidate SHA and expected version;
4. each frozen standalone passed its packaged self-test;
5. wheel and sdist contain the exact repository license;
6. release SBOM, `PROVENANCE.json`, `uv.lock`, license, manifests and standalone archives are present;
7. `SHA256SUMS` validates every release asset;
8. a clean installed-wheel Workbench self-test passes outside the source tree.

After release creation, download all assets again and verify `SHA256SUMS` and the exact tag target. A mismatch invalidates the release.

## Signing and platform-verification policy

The production-local release claim is limited to the verification mechanisms actually shipped.

Required provenance is:

- protected GitHub merge commit with a valid GitHub signature;
- exact immutable source tag pointing to the reviewed candidate SHA;
- SHA-256 checksums over all distributed assets;
- per-platform standalone manifests containing source SHA and archive digest;
- `PROVENANCE.json` linking release assets to source SHA, lock digest, license digest and Standalone workflow run;
- CycloneDX SBOM generated from the locked production dependency closure.

Native Apple notarization, Apple Developer ID signing and Windows Authenticode signing are **not claimed** unless certificates and the corresponding verified workflow are explicitly added. An unsigned native archive must not be described as OS-vendor-signed or notarized. This boundary is a release limitation, not evidence that checksum/provenance verification is optional.

If native signing is later enabled, the signing identity, certificate lifecycle and verification command become mandatory release evidence and must be added here through a protected PR.

## Rollback

Application rollback and workspace-history rollback are different operations.

For a bad binary/release:

1. stop using the affected binary;
2. preserve the workspace and protected integrity material;
3. install the last known-good release whose checksum/provenance has been verified;
4. run `shadowseed doctor` before opening the workspace;
5. if the older application cannot read the current schema, do not manually edit the database or protected anchor. Use the documented backup/restore recovery path or remain on the newer application until a compatible fix is available.

Do not replace a live workspace with an older raw database copy to perform an application rollback. Intentional data rollback must use the supported audited restore flow and create the required new audit epoch.

## Candidate soak

After the final release-candidate commit reaches protected `main`, keep it unchanged for at least 24 hours before the final production-ready/local declaration. During that window:

- complete at least one normal local Workbench use cycle on the candidate;
- run `shadowseed doctor` against the used workspace;
- record any operational, integrity, provider or packaging anomaly on #103;
- treat any discovered P0/P1 as a blocker requiring a new protected fix and a new soak window.

A code change to the candidate SHA resets the soak clock. Documentation-only evidence records that do not alter the candidate release artifact must still be checked against the exact-SHA publication rule.

## Final stop condition

Do not claim `production-ready/local` until all mandatory sections in `docs/architecture/production-acceptance.md` are green on the exact release commit, #95 has a clean independent-assurance verdict, the 24-hour candidate soak completes without unresolved P0/P1 findings, and the release assets have passed post-download verification.

Hosted production remains out of scope. Optional Chroma support remains research-only under #97 until that issue's exit condition is met.
