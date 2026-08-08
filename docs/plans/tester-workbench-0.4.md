# Shadowseed Tester Workbench 0.4 Implementation Plan

**Status:** Release candidate  
**Target:** 0.4.0 Tester Preview  
**Owner:** E-AI-MODEL  
**Created:** 2026-08-08  
**Last updated:** 2026-08-08

## Product goal

Build a local-first tester environment in which non-developer testers can run
Shadowseed sessions, inspect seed decisions, provide feedback, resume saved
work, and export reviewable reports without understanding the internal research
tooling.

Scientific principles constrain runtime behavior, logging, comparison, and
interpretation. The Workbench is not a scientific statistics platform.

## Primary user flow

```text
install
→ doctor
→ initialize workspace
→ choose backend and profile
→ run or import a session
→ inspect seeds and decisions
→ record feedback
→ resume later
→ export a report
```

## Product boundaries

- Local-first by default. The first release has no account, cloud database,
  or telemetry.
- The supported native server binds to `127.0.0.1` unless the tester explicitly
  overrides it. The optional container is documented with a host-loopback port
  mapping.
- Backend credentials are never accepted as persisted configuration and are
  redacted from reports and support bundles. Tester-provided message content is
  stored locally and may itself contain sensitive text.
- The UI never writes seed authority fields directly.
- Tester feedback is recorded only by default. Authority-changing feedback
  requires an explicit normal runtime route through the Gate.
- `trace` and `weight` remain separate and are displayed separately.
- Promotion is permission to be considered, not an obligation to influence.
- Every allowed influence remains governed by the existing Gate and point-of-use
  runtime contracts.
- Research and benchmark commands remain available, but they are not the primary
  tester interface.
- Workbench development and ordinary test runs do not rewrite benchmark evidence
  artifacts.
- The release remains research-ready and tester-oriented, not production-ready.

## Architecture

```text
Workbench UI
    ↓
Workbench controller
    ↓
Application services
    ↓
Existing Shadowseed runtime
    ↓
SQLite workspace
```

The CLI and Workbench use the same application services. UI code may format and
present data but may not reimplement intake, lifecycle, contradiction, Gate, or
point-of-use decisions.

## Delivery rounds

### Round 1: foundation, persistence, and workspace management — complete

Historical branch: `agent/workbench-foundation`  
Merged as PR #39.

Delivered:

- application-level session, profile, health, and workspace contracts;
- lossless `ShadowChatSession` snapshots and restoration;
- transactional SQLite workspace with normalized turn, seed, audit, and
  feedback tables;
- schema versioning, backup, restore, and safe deletion;
- `shadowseed doctor`, `shadowseed init`, and `shadowseed workspace ...`;
- regression tests for persistence, restart, audit replay, backup, and secret rejection.

### Round 2: practical Workbench — complete

Branch: `feature/workbench-ui`  
Merged as PR #42. The earlier PR #40 was closed as an incomplete staging probe
and is not part of the delivered product.

Delivered:

- `shadowseed workbench` using a local Gradio UI;
- setup, session, seed, and decision-inspection views;
- Demo, Balanced, Conservative, and Exploratory profiles from the application layer;
- fixture, Ollama, OpenAI, and Hugging Face Transformers backend flows;
- record-only tester feedback;
- scenario import and resumable sessions;
- side-by-side and blind A/B review of persisted baseline/SSL answer pairs;
- explicit hosted-provider confirmation and loopback-first server policy;
- dedicated Workbench CI and clean-wheel Workbench-extra installation smoke.

### Round 3: reports, privacy, and tester release — release candidate

Branch: `feature/workbench-release`  
PR #43.

Delivered in the release candidate:

- standalone HTML reports plus JSON and CSV artifacts;
- privacy-minimized support bundles;
- recursive secret-like value and local-path redaction for exported configuration;
- environment/configuration metadata and SHA-256 file manifests;
- defensive ZIP verification for hashes, sizes, traversal, duplicates, symlinks,
  compression ratios, and external/embedded HTML resources;
- atomic replacement only after a newly generated export verifies;
- Workbench export UI plus report/support/verify CLI commands;
- Linux, macOS, and Windows clean-install portability smokes;
- optional Docker packaging;
- upgrade/backup guidance, privacy/limitation guidance, and tester release notes;
- release automation gated by a successful Workbench Portability run on `main`.

Backend token, latency, and cost metadata is included only when a stable runtime
source exists. The 0.4 release does not synthesize or guess missing provider
telemetry, and fixture runs intentionally do not imply cost or performance data.

## Acceptance rules for every pull request

- The existing public runtime and CLI remain compatible unless a change is explicitly documented.
- No new direct authority-mutation path is introduced.
- New storage writes are transactional and idempotent where stable identifiers exist.
- Secrets are rejected or redacted before persistence and export.
- Tests cover failure paths, not only successful examples.
- Ruff, full pytest on Python 3.10 and 3.12, package build, clean-wheel
  install, and source/installed CLI smokes pass.
- Open P1/P2 findings are resolved before merge.

## Definition of done

A tester on a clean machine can, without writing Python code:

1. install the Workbench extra;
2. run `shadowseed doctor`;
3. initialize a local workspace;
4. select a model and profile;
5. run or import a session;
6. understand the stored seed and decision state without granting new authority;
7. record feedback without silently changing authority;
8. close and resume the session;
9. export and verify a full report or minimized support bundle;
10. back up and restore the workspace.

Release completion additionally requires:

- the final PR head to pass full CI, Workbench CI, and portability checks;
- PR #43 to merge into `main`;
- the post-merge portability run on `main` to succeed;
- GitHub prerelease `v0.4.0` to be created at that exact `main` commit;
- the published wheel, source distribution, and `SHA256SUMS` to be downloaded and
  checksum-verified by the release workflow.

## Explicitly out of scope for 0.4

- multi-tenant hosting;
- user accounts and organizations;
- mobile clients;
- automatic evidence verification;
- direct weight or status editors;
- autonomous promotion outside the existing Gate;
- a plugin marketplace;
- production-readiness claims.
