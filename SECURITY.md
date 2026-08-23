# Security policy

Shadowseed's first production target is the bounded `production-ready/local` profile: one user on a local or managed workstation, with the supported product launcher bound to loopback. It is not a hostile-network, multi-user or tenant-isolated service.

## Supported security boundary

The production-local profile includes the controls documented in:

- `docs/architecture/production-acceptance.md`;
- `docs/workbench/production-local.md`;
- `docs/operations/production-local-recovery.md`;
- `docs/operations/production-local-release.md`.

The generic source Workbench `--allow-remote` mode is a trusted-environment/development preview and is outside the production-local claim. A compromised operating system or malicious local administrator is also outside the supported local trust boundary.

Optional Chroma support is not part of the production dependency closure while #97 remains open.

## Reporting a vulnerability

Do not post credentials, private workspace data, evidence notes, prompts, model outputs or other sensitive reproduction material in a public issue.

For a public, non-sensitive finding, open a GitHub issue with the smallest reproducible description and affected version/commit. For a finding that requires sensitive material, use GitHub's private vulnerability reporting/security-advisory path for this repository when available rather than publishing the material in an ordinary issue.

Include, when possible:

- affected version and exact commit SHA;
- deployment profile (`production-ready/local`, research/evaluation, or another mode);
- whether the issue crosses the Gate/point-of-use authority boundary;
- whether persistence, audit integrity, deletion, provider credentials or release provenance are involved;
- reproduction steps that do not contain user content or secrets.

## Severity and release handling

A production release may not proceed with an unresolved P0/P1 production finding. Security or correctness findings that can change seed authority outside the selected Gate policy, bypass attributable authorization, break audit integrity, expose protected secrets, defeat the production-local network boundary, or falsely report destructive lifecycle operations as complete are release blockers until dispositioned.

The release process is exact-SHA and fail-closed. Fixes go through a protected pull request and create a new candidate SHA; they do not rewrite an already-reviewed commit.

## Cryptographic and platform-signing boundary

Release artifacts carry exact-source provenance, per-platform manifests and SHA-256 checksums as documented in the production-local release runbook. The final production-local release assurance workflow additionally creates Sigstore-backed GitHub artifact attestations for every checksum-listed release subject using an immutable pinned `actions/attest` commit and verifies those attestations through GitHub's attestation policy. That is the declared cryptographic artifact-signing path for the bounded local release.

Native Apple notarization/Developer ID signing and Windows Authenticode signing are not claimed unless a dedicated verified workflow and signing identity are added. Do not infer OS-vendor signing from either GitHub's verified merge signature or the Sigstore artifact attestation.

## Commercial-use boundary

The repository license is PolyForm Noncommercial 1.0.0. Technical production readiness does not grant commercial-use rights. Commercial deployment requires separate permission.
