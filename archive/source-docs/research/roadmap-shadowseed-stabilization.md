# Shadowseed Stabilization And Evidence-Hardening Roadmap

> Status: current
> Date: 2026-06-27
> Evidence layer: Top-level roadmap
> Current source: yes

Status: active
Date: 2026-06-27
Scope: repository stability, artifact discipline, workflow clarity, and next-step research hardening

## Goal

Move `shadowseed` from a strong research harness with growing workflow complexity toward a more stable and easier-to-maintain research repository, without overstating the evidence level or introducing heavy tooling too early.

## Current GitHub Issue Status Snapshot

This snapshot aligns the roadmap text with the current GitHub issue state. It is a planning/status correction, not a new evidence claim.

Closed or completed since the original roadmap pass:

- #37 Phase 1: translate SWOT into work categories — closed as completed.
- #41 Phase 5: complete first real open-set review round — closed as completed on 2026-06-09.
- #45 Phase 9: clean up documentation — closed as completed.

Still open:

- #34 Roadmap parent issue — still useful as the coordination anchor, but its checklist needs to be read with this updated status.
- #44 Phase 8: expand tooling slowly — still open; broader than the existing ruff/coverage work.
- #46 Phase 10: revisit positioning and version discussion — intentionally still open until stronger evidence justifies a positioning decision.
- #81 Model selection ladder — still open in GitHub, but the original dispatch blocker was largely superseded by merged PR #119, which made `microsoft/Phi-3.5-mini-instruct` dispatchable through CPU half-precision loading and workflow dropdown sync.

## Working Principle

The order matters:

1. fix active alignment and contract drift
2. document the current stack and artifact contracts
3. turn SWOT observations into usable work categories
4. make workflow behavior easier to understand
5. deepen the real evidence layers
6. only then add heavier tooling or revisit a larger version claim

## Phase -1: Acute Alignment Fixes

Status: completed via #35.

Purpose: remove known contract mismatches before documenting the stack.

Actions:
- align CLI defaults, workflow outputs, analyzer lookups, tests, and docs where they still drift
- confirm each evidence layer has one canonical artifact name per output type
- add or verify explicit branch guards on write-back workflows
- keep this phase small and non-feature-bearing

Done when:
- known path and contract mismatches are closed
- write-back routes are explicit and bounded
- docs no longer reference known stale artifact paths

## Phase 0: Freeze The Current Technical State

Status: completed via #36.

Purpose: stop working from memory or stale assumptions.

Actions:
- maintain `docs/research/current-status.md`
- record only repo-derived facts: Python version, dependencies, extras, workflows, CLI defaults, artifact names, and missing tooling
- include dates for any counts or status snapshots

Done when:
- one short document describes the current technical baseline
- the baseline does not depend on GitHub UI memory
- no undated claims remain in the status layer

## Phase 1: Translate SWOT Into Work Categories

Status: completed via #37.

Purpose: turn the SWOT into a usable execution model.

Primary document:
- `docs/research/work-categories.md`

Categories:
- strengths to preserve
- weaknesses to reduce
- opportunities to use
- threats to constrain

Examples:
- preserve: small Python core, atomic seeds, manager and Gate logic, fixture-first CI, explicit artifact contracts
- reduce: stale docs, duplicate publication routes, mixed claim language, path drift risk
- use: real open-set human review, deeper adversarial Gate evaluation, probe utility evaluation, selective consolidation
- constrain: workflow sprawl, overclaiming from fixture results, artifacts bypassing analysis, oversized mixed-goal PRs

Done when:
- each SWOT observation belongs to a concrete work category
- technical work and research work are clearly separated
- the category model is usable for issue and PR scoping

## Phase 2: Make Artifact And Analyzer-Publication Contracts Explicit

Status: completed via #39.

Purpose: stop CLI, workflows, analyzer, tests, docs, and public reporting from speaking different path dialects or mixing raw evidence with interpretive outputs implicitly.

Actions:
- maintain `docs/research/artifact-contracts.md`
- document per evidence layer: command, input path, output path, analyzer path, artifact name, and status (`standard_ci`, `manual`, `experimental`)
- begin with: gap suite, false-positive suite, benefit suite, model benefit suite, blind benchmark, adversarial Gate, probe utility, open-set review, and AbsenceBench smoke
- mark which artifacts are raw outputs, summaries, analyzer-facing inputs, and public-report inputs
- make explicit which analyzer outputs are metric-bearing and which are interpretive or public-facing
- add a simple contract test that validates important defaults and lookup paths

Done when:
- artifact names are explicit rather than implied
- path drift is caught by tests
- open-set has one canonical summary name: `open_set_seed_review_summary.json`
- analyzer-facing and publication-facing artifacts are clearly distinguished
- it is visible which outputs are raw evidence and which are interpretive summaries

## Phase 3: Create A Workflow And Claim-Publication Map

Status: completed via #40.

Purpose: make workflow behavior readable without hunting through Actions YAML and make public claim-publication routes visible end to end.

Actions:
- maintain `docs/research/workflow-map.md`
- for each workflow document: trigger, purpose, outputs, whether it writes back to the repo, whether it uses secrets, and whether it belongs to standard CI or manual research
- explicitly separate standard CI, publish/wiki/pages, manual HF or open-set routes, and model or retrieval routes
- mark write-back workflows with permissions, branch guards, and touched files
- identify which workflows produce raw benchmark artifacts, summaries, regenerated analyzer output, and Wiki or Pages publication
- identify where automatic public conclusion text is generated and published

Done when:
- it is obvious which workflows support which claim layers
- it is obvious which workflows are smoke-only
- write-back routes are not hidden in implementation detail
- public-report publication routes are visible end to end
- it is clear which workflow paths can affect public claim wording versus only raw artifacts or metrics

## Phase 4: Complete The First Real Open-Set Review Round

Status: completed via #41 on 2026-06-09. The result is evidence, but not a broad validation claim.

Purpose: move from pending review packets to actual human review evidence.

Actions:
- run a small review round on roughly 12 to 20 items
- use two reviewers and fixed reject codes
- avoid converting the task back into scenario-style ground truth
- rerun `shadowseed summarize-open-set-seed-review`
- inspect acceptance rate, disagreement count, reject-reason distribution, atomicity, relevance, and follow-up utility
- label the result conservatively as an open-set evidence layer rather than a general claim

Suggested labeling:
- `evidence_layer: open_set_seed_quality`
- `status: first-human-review-round`

Done when:
- real review data exists
- pending is no longer the only open-set state
- the analyzer reads real review output
- reporting clearly says this is not standard regression evidence

## Phase 5: Deepen Adversarial Gate Evaluation

Status: completed as first real Layer-D evidence via #42 / PR #80.

Purpose: show that the current Gate is stronger than weaker promotion routes.

Actions:
- curate or verify an adversarial set with nearly-complete answers, tempting but irrelevant gaps, style weaknesses without real gaps, and conflict cases
- compare at least `current_gate`, `trace_only`, and `trace_no_contradiction_check`
- report promoted false positives, blocked bad seeds, missed good seeds, and a readable casebook
- keep the interpretation scoped to Gate quality rather than total SSL quality

Done when:
- the current Gate promotes fewer bad seeds than the baseline variants
- examples and summary metrics support each other

## Phase 6: Evaluate Probe Feedback Behavior

Status: completed as first real Layer-E behavioral evidence via #43 / PR #82.

Purpose: verify that the reward and penalty loop is not only present but behaviorally meaningful.

Actions:
- check which probe outcomes produce reward, penalty, or neutral feedback
- confirm visibility in seed weight, status transitions, feedback log, and persistence
- add a small evaluation layer showing that good probes strengthen useful seeds, bad probes weaken them, clamping works, and promoted seeds can drop back to active when justified
- keep this separate from open-set review

Done when:
- probe feedback has measurable lifecycle effects
- weak probes do not merely log but also correct behavior

## Phase 7: Expand Tooling Slowly

Status: partly complete; still tracked by #44.

Purpose: add engineering discipline without creating noise.

Possible order:
1. `ruff check` — present in CI
2. `ruff format --check`
3. `pytest-cov` — present in CI
4. `pyright` or `mypy`
5. `pre-commit`
6. lockfile
7. release process

Done when:
- each tooling step has one clear purpose
- CI remains green
- benchmark claims do not change
- churn stays low

## Phase 8: Clean Up Documentation

Status: completed via #45; keep as ongoing maintenance discipline.

Purpose: keep docs aligned with code, workflows, and evidence limits.

Actions:
- remove stale artifact names and old paths
- weaken any language that overclaims fixture or pending outputs
- separate status docs, plan docs, and report docs more clearly
- add a small header to each current research doc with date, status, role, and whether it is current
- keep historical sources available, but outside the current-source lane

Done when:
- old paths no longer recur
- status and planning text are not mixed together
- docs do not claim more than the data supports
- older canonical material is still readable without competing with the current source stack

## Phase 9: Revisit Positioning

Status: still open via #46. Do not close until the evidence surface justifies a positioning decision.

Purpose: decide whether the project should still present as an evolved 4.6 line or whether stronger evidence supports a bigger label.

Continue as a 4.6-style line if:
- open-set review is still small
- adversarial Gate is still narrow
- probe feedback is still mainly technical

Only revisit a 5.0-style shift if:
- open-set has real review data
- adversarial Gate baseline comparisons are solid
- probe feedback shows meaningful learning behavior
- docs, analyzer output, and workflow labeling cleanly separate evidence layers

## Remaining Immediate Order

1. Update or close the stale parent checklist in #34 using this status snapshot.
2. Close, retitle, or convert #81 into a follow-up dispatch/tracking issue now that PR #119 removed the original model-dropdown blocker.
3. Continue #44 only as incremental tooling, with no benchmark-claim changes.
4. Keep #46 open until the positioning decision is evidence-led rather than momentum-led.
5. If an agent/RAG fork is created, keep it separate from this research roadmap until it has its own safety contract, gate tests, and audit replay.

## Summary

The next best move for `shadowseed` is not to sound bigger, but to keep the roadmap aligned with live evidence, live issues, and conservative claim boundaries. Several early stabilization phases are now completed; the remaining work is mainly issue hygiene, incremental tooling, and a later evidence-led positioning decision.