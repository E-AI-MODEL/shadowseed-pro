# ADR 0002 — Consolidation plan: workflows, wiki, Pages

Status: accepted; partially executed (see "Execution status")
Date: 2026-05-22 (execution status updated 2026-06-06)
Deciders: shadowseed maintainers
Related: #34 (roadmap), ADR 0001; 4.6 canon `docs/00_shadow_seed_learning_4_6.md`
Supersedes: none

## Execution status (2026-06-06)

| Workstream | State | Evidence |
|---|---|---|
| A1 — kill nightly crons + remove dead workflow | **done** | no `schedule:` triggers remain; `publish-existing-slm-conclusion.yml` removed |
| B — wiki to 5-page reading order + Archief | **done** | merged (#91) |
| C — Pages dashboard as A–G status story | **done** | merged (#92) |
| A2 — merge research workflows into `vector-retrieval.yml` / `ssot.yml` / `paper.yml` | **not done / deferred** | 19 workflows remain; the three merged files do not exist |

A1, B and C are executed and merged. A2 (the higher-risk workflow merges) is
deliberately deferred per the ADR's own "we can stop after A1" note. The plan
below is kept as written for historical context.

## Context

The mechanical core and the evidence layers have matured (A/B strong, D/E first
evidence, C infrastructure complete). But the **presentation and operations
surface has sprawled** to the point where a newcomer cannot see what the
project is or what it proves:

- 20 GitHub Actions workflows, including 2 nightly crons on a research prototype
- 20 wiki pages with no single reading order; the sidebar still says "4.5"
- a Pages dashboard that shows a wall of numbers instead of a status story

The 4.6 canon explicitly names this as a threat ("workflow sprawl, overclaiming
from fixture results") and prescribes the cure ("consolideer infrastructuur en
rapportage, maar niet ten koste van epistemische eerlijkheid"). This ADR is that
consolidation, planned before execution because deleting workflows and
restructuring the wiki are shared-state, partly irreversible actions.

## Guiding principle

Consolidation is not deletion of honest findings. Negative and historical
results (round 001 static finding, Eindconclusie SSL 4.5, interim reports) stay
in the repo and the wiki, but in a clearly labelled **Archief / Legacy**
structure instead of competing with the current entry path.

## Workstream A — Workflows: 20 → ~9

### Phase A1 (low risk, do first)

- **Disable the two nightly crons.** `nightly-vector-backend-comparison.yml`
  (03:17 daily) and `retrieval-backend-comparison.yml` (02:23 daily) become
  `workflow_dispatch`-only. A research prototype does not need daily unattended
  CI minutes.
- **Remove genuinely dead routes.** `publish-existing-slm-conclusion.yml`
  publishes a one-off stale conclusion; fold any still-true content into
  `publish-test-results.yml` and delete it.

### Phase A2 (merge by input, do after A1 is confirmed green)

Merge overlapping research routes into single workflows gated by an input. Each
merged workflow calls the **same `shadowseed` CLI commands** as today — only the
dispatch surface shrinks.

| New workflow | Absorbs | Selector input |
|---|---|---|
| `vector-retrieval.yml` | complete-vector-ssot, nightly-vector-backend-comparison, retrieval-backend-comparison, retrieval-model-comparison, retrieval-model-hf, vectorstore-smoke | `mode` (vector-smoke / backend-compare / retrieval / retrieval-model / model-reality / complete) |
| `ssot.yml` | ssot-smoke, ssot-falsification | `mode` (smoke / falsification) |
| `paper.yml` | paper-pipeline, paper-evidence-smoke, paper-scenario-smoke, paper-scenario-suite | `stage` (evidence-smoke / scenario-smoke / scenario-suite / full) |

### Keep unchanged

`tests.yml` (core CI), `open-set-hf-review.yml`, `slm-model-benefit.yml`,
`publish-wiki.yml`, `publish-test-results.yml`, `pages-dashboard.yml`,
`full-validation-sweep.yml` (made dispatch-only if it still has a push trigger).

### Result

20 → 10: tests, open-set-hf-review, slm-model-benefit, publish-wiki,
publish-test-results, pages-dashboard, full-validation-sweep, vector-retrieval,
ssot, paper. (9 if full-validation-sweep is folded into the sweep use of the
others.)

Risk note: A2 (merging) is higher risk than A1 because a single file now has
multiple paths. A1 is safe and reversible. We can stop after A1 if A2 feels too
invasive.

## Workstream B — Wiki: 20 → ~7 with one reading order

### Target reading order (sidebar top section)

1. **Home** — one paragraph: what SSL 4.6 is, link to the next three pages
2. **Start hier** — orientation + the reading order itself
3. **Wat is SSL** — concept (merge Conceptueel-Overzicht + Waarom-SSL-niet-naief-is + the conceptual half of Architectuur)
4. **Huidige evidence-status** — the A-G layer status: proven vs goal (rebuilds Resultaten-en-Analyse around the layer model from `docs/research/current-status.md`)
5. **Reproduceren** — how to run (merge Quick-Start + Benchmarks)
6. **Roadmap** — where it goes (keep, refresh)

### Archief section (sidebar bottom, clearly labelled "Archief / Legacy")

Eindconclusie-SSL-4-5, Tussentijdse-Rapportage, Visueel-Verhaal, SLM-Runs,
Blind-Benchmark, Blind-Review-Protocol, SSOT-en-Documentvalidatie,
Vectorstore-en-Gewichtloze-Seeds, Paper-naar-Seed-Pipeline, Dashboard. These
stay published; they move out of the primary path, not out of the repo.

### Fixes

- `_Sidebar.md` title `Shadow Seed Learning 4.5` → `4.6`
- every primary page gets a one-line header: what it is, whether it is current

### Publish mechanics note

`publish-wiki.yml` does `cp docs/wiki/*.md wiki/` — a flat glob. Archived pages
therefore stay flat files; archiving is done via the sidebar grouping, not a
subfolder, unless we also update the publish step to recurse. Plan: keep flat,
regroup in the sidebar. Low risk.

## Workstream C — Pages dashboard: status story, not number wall

Redesign `site/index.html` + `site/app.js` to lead with the **evidence-layer
table (A-G)**: each layer shows status (strong / first-evidence / infrastructure
/ absent) and links to the artifact that backs it. Raw numbers move below the
fold. Presentation-only; lowest risk; no workflow or Python change.

| Layer | Label shown |
|---|---|
| A regression | strong |
| B small benchmark | usable |
| C open-set | first evidence — quality warning (round 005, acceptance 0.29) |
| D adversarial Gate | first evidence (F1 1.0) |
| E probe utility | first evidence |
| F domain transfer | absent |
| G model-internal | research only |

## Execution order (proposed)

1. **This ADR merged** (plan agreed)
2. **B (wiki) + C (Pages)** — highest "nobody understands it" payoff, low/again-reversible risk, presentation only
3. **A1 (kill crons + remove dead workflow)** — safe ops cleanup
4. **A2 (merge research workflows)** — only after A1 is confirmed green; can be deferred or skipped

Each step is its own PR. No step deletes an honest finding; archive over delete.

## Consequences

Positive: a newcomer can read Home → Wat is SSL → Evidence-status → Reproduceren
in four pages; the Actions tab is scannable; CI minutes drop; the 4.5/4.6 drift
in the presentation layer is gone.

Negative / risk: A2 concentrates several research routes into three files with
mode-switches; a mistake there affects more than one route. Mitigated by doing
A1 first and keeping each merge a separate, reviewable PR that preserves the
underlying CLI calls verbatim.

## Status and revisit

Proposed. On approval, execute in the order above, one PR per step. Revisit if
A2 merging proves more fragile than the sprawl it replaces.
