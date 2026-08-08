# Shadowseed Tester Workbench 0.4 Implementation Plan

**Status:** In progress  
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
- The server binds to `127.0.0.1` unless the tester explicitly overrides it.
- Backend credentials are never accepted as persisted configuration and are
  redacted from reports and support bundles. Tester-provided message content is
  stored locally and may itself contain sensitive text.
- The UI never writes seed authority fields directly.
- Tester feedback is recorded only by default. Authority-changing feedback
  requires an explicit normal runtime route through the Gate.
- `trace` and `weight` remain separate and are displayed separately.
- Promotion is permission to be considered, not an obligation to influence.
- Every allowed influence remains linked to a current Gate event and a
  point-of-use decision.
- Research and benchmark commands remain available, but they are not the primary tester interface.
- The release remains research-ready and tester-oriented, not production-ready.

## Architecture

```text
Workbench UI
    ↓
Application services
    ↓
Existing Shadowseed runtime
    ↓
Repository interfaces
    ↓
SQLite workspace
```

The CLI and Workbench use the same application services. UI code may format and
present data but may not reimplement intake, lifecycle, contradiction, Gate, or
point-of-use decisions.

## Delivery rounds

### Round 1: foundation, persistence, and workspace management

Branch: `agent/workbench-foundation`

Deliverables:

- application-level session, profile, health, and workspace contracts;
- lossless `ShadowChatSession` snapshots and restoration;
- transactional SQLite workspace with normalized turn, seed, audit, and
  feedback tables;
- schema versioning, backup, restore, and safe deletion;
- `shadowseed doctor`, `shadowseed init`, and `shadowseed workspace ...`;
- regression tests for persistence, restart, audit replay, backup, and secret rejection.

Non-goals:

- browser UI;
- direct authority editing;
- cloud storage;
- hosted backend setup screens;
- statistical research dashboards.

### Round 2: practical Workbench

Branch: `agent/workbench-ui`

Deliverables:

- `shadowseed workbench` using a local Gradio UI;
- setup, session, seed ledger, and decision-inspection views;
- Demo, Balanced, Conservative, and Exploratory profiles;
- fixture and Ollama onboarding, then OpenAI and Hugging Face configuration;
- simple record-only feedback;
- scenario import, side-by-side comparison, and blind A/B review;
- pause, resume, and failure isolation for scenario batches.

### Round 3: reports, privacy, and tester release

Branch: `agent/workbench-release`

Deliverables:

- standalone HTML reports plus JSON and CSV artifacts;
- redacted support bundles;
- environment and configuration manifests with hashes;
- token, latency, and cost metadata where the backend provides them;
- headless UI and clean-install end-to-end tests;
- wheel, optional Docker packaging, upgrade guidance, tester terms, privacy guidance, and a release candidate.

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
6. understand why seeds were used, blocked, or ignored;
7. record feedback without silently changing authority;
8. close and resume the session;
9. export a safe report and support bundle;
10. back up and restore the workspace.

## Explicitly out of scope for 0.4

- multi-tenant hosting;
- user accounts and organizations;
- mobile clients;
- automatic evidence verification;
- direct weight or status editors;
- autonomous promotion outside the existing Gate;
- a plugin marketplace;
- production-readiness claims.
