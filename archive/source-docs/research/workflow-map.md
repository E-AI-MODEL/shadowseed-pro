# Workflow Map and Publication Route Audit

> Status: current
> Date: 2026-05-22
>
> **Update 2026-07-07: GitHub Pages is als kanaal verwijderd.** De workflow
> `pages-dashboard.yml` en de map `site/` bestaan niet meer;
> `publish-test-results.yml` blijft bestaan maar publiceert alleen nog naar
> de wiki (de Pages-stappen zijn eruit). Het publieke verhaal is één
> standalone bestand (`verhaal.html` in de repo-root). Pages-vermeldingen
> hieronder zijn historisch.
> Evidence layer: Workflow map + publication routes
> Current source: yes


Status: current as of 2026-05-10
Base commit: `9e8fef85acf5ffa6ded5366cea9214edf8819071`
Related issue: #40
Follow-up cleanup: PR #55 removes the duplicate manual blind benchmark workflow.

## Purpose

This document maps the GitHub Actions surface and audits whether the current workflow set is clear, efficient and justified.

It has two goals:

1. show which workflows collect evidence, analyze results, publish public pages, or write generated files back to `main`;
2. identify overlap, record cleanup decisions, and propose a safe reduction order.

This is primarily an audit document. PR #55 is the first small implementation of the audit: it removes the duplicate manual blind benchmark workflow while keeping the standard blind benchmark job in `tests.yml`.

## Scope

Before PR #55, the repository had 21 workflow files under `.github/workflows/`.

After PR #55 merges, the repository has 20 workflow files. The removed workflow is:

- `.github/workflows/blind-benchmark.yml`

The blind benchmark itself remains covered by the `blind-benchmark-smoke` job in `.github/workflows/tests.yml`.

This audit focuses on:

- trigger type
- purpose
- output type
- publication behavior
- write-back behavior
- secret usage
- claim-publication risk
- overlap and recommended action

## Classification labels

| Label | Meaning |
|---|---|
| keep | Workflow has a clear separate role. |
| keep, document better | Workflow can stay, but its name or docs should explain the boundary more clearly. |
| merge candidate | Workflow overlaps another route and should be considered for consolidation. |
| fallback only | Workflow is useful only as a manual recovery path. |
| removed | Workflow was removed after review because another maintained route covers the same work. |
| delete candidate after replacement | Workflow should not be removed until a better route is merged and tested. |

## Main route overview

| Route | Primary workflow | Role | Public effect | Recommendation |
|---|---|---|---|---|
| Standard CI and benchmark artifacts | `tests.yml` | Lint, tests, standard benchmark artifacts, analyzer report artifact | Indirect, feeds publish route | keep |
| Standard public snapshot | `publish-test-results.yml` | Downloads trusted `tests.yml` artifacts, rebuilds `results/latest`, publishes Wiki and Pages | High | keep |
| Manual dashboard fallback | `pages-dashboard.yml` | Deploys repository `site/` and existing `results/` to Pages | Medium | fallback only |
| Static wiki-only pages | `publish-wiki.yml` | Copies `docs/wiki/*.md` to Wiki | Medium | keep, document better |
| Open-set HF manual review | `open-set-hf-review.yml` | Fetches HF batch, creates review packets, writes summary back to repo | Medium to high | keep, document better |
| SLM model benefit run | `slm-model-benefit.yml` | Runs real HF model benefit suite and publishes SLM wiki pages | High | merge candidate |
| Existing SLM conclusion republish | `publish-existing-slm-conclusion.yml` | Reuses prior SLM run and regenerates conclusion page | High | merge candidate |
| Full validation sweep | `full-validation-sweep.yml` | Runs core, vector, SSOT and retrieval checks, publishes compact wiki page | Medium | merge candidate |
| Vector and SSOT manual routes | `complete-vector-ssot.yml`, `vectorstore-smoke.yml`, `ssot-smoke.yml`, `nightly-vector-backend-comparison.yml` | Backend smoke and comparison routes | Medium | merge candidate group |
| Retrieval routes | `retrieval-backend-comparison.yml`, `retrieval-model-comparison.yml`, `retrieval-model-hf.yml` | Retrieval backend and model comparisons | Medium | merge candidate group |
| Paper routes | `paper-pipeline.yml`, `paper-evidence-smoke.yml`, `paper-scenario-smoke.yml`, `paper-scenario-suite.yml` | Paper ingestion and scenario smoke/suite runs | Medium | merge candidate group |
| Manual blind benchmark | `blind-benchmark.yml` | Duplicate of the standard blind smoke pattern | Low to medium | removed in PR #55 |
| SSOT falsification | `ssot-falsification.yml` | Falsification-specific SSOT route | Medium | keep, document better |

## Applied cleanup

### PR #55: remove duplicate manual blind benchmark workflow

Removed workflow:

- `.github/workflows/blind-benchmark.yml`

Reason:

- it used the same generated private labels as the blind benchmark job in `tests.yml`;
- it used the same public input: `src/shadowseed/data/blind_suite_public.json`;
- it ran the same `run-blind-benchmark` command shape;
- it wrote the same benchmark output path: `results/blind_benchmark.json`;
- the only meaningful difference was manual trigger plus artifact name.

Retained route:

- `.github/workflows/tests.yml` job `blind-benchmark-smoke`

Effect:

- workflow count decreases from 21 to 20;
- blind benchmark coverage remains in standard CI;
- no benchmark input, output path, analyzer behavior or publication route changes.

## Standard CI route

### `.github/workflows/tests.yml`

Trigger:

- `push`
- `pull_request`

Permissions:

- `contents: read`

Main jobs:

- `pytest`, including `ruff check src tests` and `pytest`
- gap suite
- false-positive suite
- benefit suite
- model-benefit fixture smoke
- blind benchmark smoke
- adversarial Gate benchmark
- probe utility benchmark
- analyzer report
- AbsenceBench smoke
- repeat gap matrix

Outputs:

- benchmark JSON artifacts
- adversarial Gate casebook
- analyzer output under `results/analysis`
- charts
- manifest copy

Public effect:

- direct: none
- indirect: high, because `publish-test-results.yml` consumes successful `tests.yml` artifacts from `main`

Audit judgement:

- keep
- this should remain the single trusted standard CI source for public `results/latest`
- avoid adding manual or model-heavy work here unless it is cheap and deterministic

Cleanup note:

- this workflow is long, but it has a clear role: standard CI and standard artifact generation
- do not split it just for file length unless artifact publication remains tied to a single trusted run

## Standard publication route

### `.github/workflows/publish-test-results.yml`

Trigger:

- `workflow_run` after successful `Checks en benchmark-resultaten` on `main`
- manual `workflow_dispatch`

Permissions:

- `actions: read`
- `contents: write`
- `pages: write`
- `id-token: write`

Purpose:

- download artifacts from the latest trusted standard `tests.yml` run
- rebuild `results/latest` through `artifact_snapshot`
- run `shadowseed analyze-results` again for central published output
- publish to Wiki
- deploy Pages dashboard

Public effect:

- very high
- this is the main public claim route for Wiki and Pages

Claim-publication boundary:

- raw artifacts are produced upstream in `tests.yml`
- analysis and public-facing summary are regenerated here
- this route publishes `analysis_report.md`, `summary.json`, charts and `results/latest`

Audit judgement:

- keep
- this is the canonical publication route

Cleanup note:

- other workflows that publish to Wiki should be compared against this route
- if they publish similar analyzer conclusions, they should either feed this route or be clearly marked as separate manual research publications

## Manual and fallback publication routes

### `.github/workflows/pages-dashboard.yml`

Trigger:

- `workflow_dispatch`

Permissions:

- `contents: read`
- `pages: write`
- `id-token: write`

Purpose:

- manually deploy `site/` and existing `results/` to Pages

Public effect:

- medium
- can publish whatever is currently in repository `results/`

Audit judgement:

- fallback only

Recommended action:

- keep for now as a manual fallback
- rename or document as `manual-pages-fallback` in a later PR
- do not treat as normal publication path

Reason:

- overlaps with `publish-test-results.yml`, but lacks the trusted artifact reconstruction step
- useful only when the main publication route is unavailable

### `.github/workflows/publish-wiki.yml`

Trigger:

- `workflow_dispatch`
- push to `main` when `docs/wiki/**` or the workflow changes

Permissions:

- `contents: write`

Purpose:

- publish static Markdown from `docs/wiki/*.md` to the GitHub Wiki

Public effect:

- medium
- static docs only

Audit judgement:

- keep, document better

Recommended action:

- clarify that this route is static-doc-only
- keep it separate from result publication
- do not use it for benchmark or analyzer output

Reason:

- `publish-test-results.yml` also copies `docs/wiki/*.md` during full publication, so the route overlaps in destination but not in purpose

## Manual write-back route

### `.github/workflows/open-set-hf-review.yml`

Trigger:

- `workflow_dispatch`

Permissions:

- `contents: write`

Secret usage:

- `HUGGINGFACE_TOKEN`

Purpose:

- fetch open-set HF batch
- build review packets
- generate pending summary
- upload artifacts
- commit selected summary/report files back to `main` only when `github.ref == 'refs/heads/main'`

Write-back files:

- `results/open_review/open_set_seed_review_summary.json`
- `results/open_review/open_set_disagreements.json`
- `results/open_review/open_set_review_report.md`
- `results/open_review/README.md`

Public effect:

- medium to high
- standard CI later passes the committed summary into the analyzer if present

Claim-publication boundary:

- this workflow does not directly publish Wiki/Pages
- it can affect later public analysis because it persists open-set summary data in the repo

Audit judgement:

- keep, document better

Recommended action:

- keep as separate manual research route
- keep branch guard
- keep write-back list explicit
- later add a small note in the workflow name or README that it is `manual evidence intake`, not standard CI

Reason:

- open-set data is intentionally manual and optional
- folding this into standard CI would blur manual evidence and regression evidence

## SLM publication routes

### `.github/workflows/slm-model-benefit.yml`

Trigger:

- `workflow_dispatch`

Permissions:

- `contents: write`

Purpose:

- run real HF model benefit suite
- generate companion benchmark outputs
- run analyzer
- publish SLM-specific pages to GitHub Wiki

Public effect:

- high

Audit judgement:

- merge candidate

Reason:

- it both collects model evidence and publishes SLM public pages
- publication logic overlaps with `publish-existing-slm-conclusion.yml`
- it regenerates analyzer output outside the standard publication route

### `.github/workflows/publish-existing-slm-conclusion.yml`

Trigger:

- `workflow_dispatch`

Permissions:

- `contents: write`
- `actions: read`

Purpose:

- find or use an existing SLM run
- download model-benefit artifact
- regenerate companion outputs and analysis
- build and publish first-conclusion wiki page

Public effect:

- high

Audit judgement:

- merge candidate

Recommended action for both SLM routes:

- keep both for now
- later merge into one SLM workflow with an input mode:
  - `run_new_model_benefit`
  - `republish_existing_run`
- centralize Wiki page generation in one script or one workflow path

Reason:

- today there are two SLM routes that can publish analyzer-derived conclusions
- this is useful during exploration but confusing as a stable publication surface

## Validation sweep and backend routes

### `.github/workflows/full-validation-sweep.yml`

Trigger:

- push to `main` when `full-validation-sweep.yml` changes
- `workflow_dispatch`

Permissions:

- `contents: write`

Purpose:

- run core tests and SSL suites
- run vector, SSOT, retrieval and retrieval-model checks across memory, FAISS and Chroma
- build compact `Full-Validation-Sweep.md`
- publish summary to Wiki

Public effect:

- medium

Audit judgement:

- merge candidate

Reason:

- it overlaps with standard CI for core SSL suites
- it overlaps with vector, SSOT and retrieval-specific workflows
- it publishes a wiki page from a separate analysis path

Recommended action:

- keep until the backend workflow family is rationalized
- later decide whether this becomes the single manual broad validation workflow or whether it is replaced by smaller workflow groups

### `.github/workflows/complete-vector-ssot.yml`

Trigger:

- `workflow_dispatch`

Permissions:

- `contents: write`

Purpose:

- run vectorstore and SSOT tests for selected backend
- run vectorstore and SSOT smoke commands
- build and publish complete vector + SSOT wiki page

Public effect:

- medium

Audit judgement:

- merge candidate

Reason:

- overlaps with `full-validation-sweep.yml`
- overlaps with `vectorstore-smoke.yml`, `ssot-smoke.yml` and nightly backend comparison

Recommended action:

- keep until backend routes are consolidated
- likely fold into a single `backend-validation.yml` or make it one mode of `full-validation-sweep.yml`

### `.github/workflows/vectorstore-smoke.yml`

Audit judgement:

- merge candidate

Likely role:

- targeted vectorstore smoke run

Recommended action:

- keep only if it gives a faster debug path than `complete-vector-ssot.yml`
- otherwise fold into backend validation workflow

### `.github/workflows/ssot-smoke.yml`

Audit judgement:

- merge candidate

Likely role:

- targeted SSOT smoke run

Recommended action:

- keep only if it gives a faster debug path than `complete-vector-ssot.yml`
- otherwise fold into backend validation workflow

### `.github/workflows/nightly-vector-backend-comparison.yml`

Audit judgement:

- merge candidate

Likely role:

- scheduled or manual backend comparison

Recommended action:

- keep if it is the only scheduled backend drift detector
- otherwise fold its matrix into a broader backend validation workflow

## Retrieval routes

### `.github/workflows/retrieval-backend-comparison.yml`

Audit judgement:

- merge candidate

Likely role:

- compare retrieval behavior across vector backends

Recommended action:

- consider merging with backend validation route

### `.github/workflows/retrieval-model-comparison.yml`

Audit judgement:

- merge candidate

Likely role:

- compare retrieval model behavior using fixture or optional model backend

Recommended action:

- consider merging with retrieval backend comparison or full validation sweep

### `.github/workflows/retrieval-model-hf.yml`

Audit judgement:

- keep, document better or merge candidate

Likely role:

- HF-backed retrieval model check

Recommended action:

- keep separate only if runtime or dependency cost requires manual isolation
- otherwise fold into a retrieval validation workflow with backend/model mode inputs

## Paper routes

### `.github/workflows/paper-pipeline.yml`

Audit judgement:

- merge candidate

Likely role:

- fuller paper pipeline route

### `.github/workflows/paper-evidence-smoke.yml`

Audit judgement:

- merge candidate

Likely role:

- lightweight paper evidence smoke

### `.github/workflows/paper-scenario-smoke.yml`

Audit judgement:

- merge candidate

Likely role:

- lightweight scenario smoke from paper route

### `.github/workflows/paper-scenario-suite.yml`

Audit judgement:

- merge candidate

Likely role:

- broader paper scenario suite

Recommended action for paper routes:

- do not delete yet
- create one follow-up audit for paper workflows only
- likely consolidate into one `paper-validation.yml` with modes:
  - `smoke`
  - `scenario_suite`
  - `full_pipeline`

Reason:

- four paper workflows are hard to reason about from names alone
- the distinction may be real, but it should be encoded as workflow inputs or clear docs

## Blind benchmark route

### `.github/workflows/blind-benchmark.yml`

Status:

- removed in PR #55

Reason:

- standard CI already contains the maintained `blind-benchmark-smoke` job;
- the removed manual workflow repeated the same public input, private-label fixture, CLI route and output path;
- keeping both made the workflow list noisier without adding a separate evidence layer.

Retained coverage:

- `.github/workflows/tests.yml` job `blind-benchmark-smoke`

## SSOT falsification route

### `.github/workflows/ssot-falsification.yml`

Audit judgement:

- keep, document better

Likely role:

- falsification-specific SSOT route

Recommended action:

- keep separate if it tests adversarial or contradiction behavior that should not be hidden inside generic SSOT smoke
- document whether it feeds any public claim pages

## Claim-publication map

| Claim surface | Workflow route | Source of wording | Risk |
|---|---|---|---|
| Standard SSL analysis page | `tests.yml` then `publish-test-results.yml` | `shadowseed.cli analyze-results` and analyzer conclusion object | High |
| GitHub Pages dashboard | `publish-test-results.yml`, fallback `pages-dashboard.yml` | `site/` plus copied results | High for main route, medium for fallback |
| Static Wiki docs | `publish-wiki.yml`, also copied by `publish-test-results.yml` | `docs/wiki/*.md` | Medium |
| Open-set metrics in standard report | `open-set-hf-review.yml` then `tests.yml` passthrough then `publish-test-results.yml` | open-set summary plus analyzer | Medium to high |
| SLM model benefit pages | `slm-model-benefit.yml` | analyzer and workflow-generated Markdown | High |
| Existing SLM first conclusion | `publish-existing-slm-conclusion.yml` | analyzer conclusion fields and workflow-generated Markdown | High |
| Full validation sweep page | `full-validation-sweep.yml` | workflow-generated Markdown | Medium |
| Complete vector + SSOT page | `complete-vector-ssot.yml` | workflow-generated Markdown | Medium |

## Main overlap findings

### 1. Publication is split across too many workflows

Current public publication routes include:

- `publish-test-results.yml`
- `pages-dashboard.yml`
- `publish-wiki.yml`
- `slm-model-benefit.yml`
- `publish-existing-slm-conclusion.yml`
- `full-validation-sweep.yml`
- `complete-vector-ssot.yml`

This is the biggest workflow risk.

Recommendation:

- keep `publish-test-results.yml` as the main route
- keep `pages-dashboard.yml` only as fallback
- keep `publish-wiki.yml` only for static docs
- move SLM and backend pages toward clearer manual research publications with shared conventions

### 2. SLM publication has two overlapping routes

`slm-model-benefit.yml` and `publish-existing-slm-conclusion.yml` can both publish analyzer-derived SLM conclusions.

Recommendation:

- merge later into one workflow with mode input
- keep both until a replacement is tested

### 3. Backend validation is spread across several workflows

The repo has separate routes for:

- full validation sweep
- complete vector + SSOT
- vectorstore smoke
- SSOT smoke
- nightly vector backend comparison
- retrieval backend comparison
- retrieval model comparison
- retrieval model HF

Recommendation:

- define one backend/retrieval validation contract before changing YAML
- likely consolidate into two workflows:
  - `backend-validation.yml`
  - `retrieval-validation.yml`

### 4. Paper validation is spread across four workflows

The repo has:

- `paper-pipeline.yml`
- `paper-evidence-smoke.yml`
- `paper-scenario-smoke.yml`
- `paper-scenario-suite.yml`

Recommendation:

- audit these as a follow-up group
- likely consolidate into one `paper-validation.yml` with mode inputs

### 5. Manual blind benchmark duplicate removed

`blind-benchmark.yml` repeated work that is already covered by `tests.yml`.

Resolution:

- removed in PR #55
- keep `tests.yml` as the single maintained blind benchmark route

## Recommended cleanup order

Do not change all workflows at once.

Suggested order:

1. Keep `tests.yml` and `publish-test-results.yml` as the stable standard route.
2. Rename or document `pages-dashboard.yml` as fallback-only.
3. Remove the duplicate manual blind benchmark workflow after direct comparison. Completed by PR #55.
4. Consolidate SLM workflows into one manual SLM publication route.
5. Consolidate backend and retrieval workflows after a separate route contract.
6. Consolidate paper workflows after a focused paper-route audit.
7. Only then remove old branches or delete more workflow files.

## Follow-up constraints

Future workflow cleanup PRs should avoid mixing unrelated changes.

A workflow cleanup PR should state whether it:

- deletes a workflow;
- disables a trigger;
- changes Pages or Wiki behavior;
- merges YAML files;
- changes artifact names;
- changes analyzer behavior.

PR #55 only deletes the duplicate manual blind benchmark workflow and updates this audit document.

## Practical next PR after this cleanup

After PR #55, the next small workflow cleanup should be one of:

- finish/merge the `pages-dashboard.yml` fallback-label PR if it is still open;
- start a focused SLM publication-route issue before touching SLM YAML;
- start a focused backend/retrieval workflow contract before merging backend workflows.

Avoid starting with SLM, paper or backend consolidation in the same PR as a small cleanup. Those have higher public-claim and dependency risk.
