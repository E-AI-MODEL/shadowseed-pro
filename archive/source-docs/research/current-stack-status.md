# Current Stack Status

> Status: current
> Date: 2026-06-30
> Evidence layer: Repository stack snapshot
> Current source: yes

## Purpose

This document records the current technical baseline of `shadowseed` from repository state, not from memory or GitHub UI assumptions.

Use it as a short factual reference before changing tooling, artifact contracts, workflows or evidence layers.

## Project and packaging

- Project name: `shadowseed`
- Project version: `0.2.0`
- Python requirement: `>=3.10`
- Build backend: `setuptools.build_meta`
- Package layout: `src/`
- CLI entry point: `shadowseed = shadowseed.cli:main`

## Core dependency model

The fixed runtime dependency set is intentionally small:

- `numpy>=1.24`

Optional extras carry heavier dependencies:

- `test`: `pytest`, `pytest-cov`, `ruff`
- `models`: `sentence-transformers`, `transformers`, `torch`
- `openai`: `openai`
- `paper`: `pymupdf`
- `vector-faiss`: `faiss-cpu`
- `vector-chroma`: `chromadb`
- `vector`: bundles FAISS and Chroma extras
- `dev`: bundles test, models, vector, paper and openai extras

## Current quality tooling

Current state:

- pytest is configured and used in CI.
- ruff check is configured and runs in CI.
- pytest-cov is configured and runs in CI.
- coverage XML is uploaded from the Python 3.11 job.
- No formatter gate is configured yet.
- No type checker is configured yet.
- No pre-commit config is present.

### Coverage assessment (2026-07-02, maintainer-supplied)

Reading rule: judge the test layer only on the paths it actually touches; label
untested paper/prompt paths separately instead of counting them as failures of
this layer. Under that rule the maintainer scored the coverage zip **7.6/10** as
test-layer evidence: SSL core strong (94.32% line / 83.33% branch), tested
benchmark parts good (85.21% / 73.58%), **vectorstore weak (48.31% / 23.33%)** —
with the doctrine note that gap retrieval must never silently become truth or
steering.

Action taken the same day (`tests/test_vectorstore_hardening.py`):

- FAISS/Chroma adapters now run in CI behind lightweight fakes (no optional
  deps needed): chroma_store 22.7% → 98.3%, faiss_store 21.0% → 95.1%; the
  numpy-payload hydration regression is pinned by a test.
- memory/factory/vector_constellation/vectorstore_smoke → 100%.
- Explicit doctrine guard: retrieval (manager route and store route) mutates no
  seed weight/status/trace/occurrence — "gevonden" is never "waar" of "sturend".
- Found and fixed en passant: the vectorstore smoke had silently degraded to
  `passed: false` (its query/falsification strings shared zero lexical tokens
  with the seed, and the Gate's min-evidence rule needs 4 feedback rounds, not
  3). Fixture repaired; the smoke now runs as a pytest test so CI guards it.

Known documented behavior: a failed backend delete in the Chroma adapter lets
an entry resurrect from the backing collection on the next full read — the
store is an index, not the source of truth; SSLManager stays leading.

## Standard CI baseline

The main CI workflow is `.github/workflows/tests.yml`.

It runs on:

- `push`
- `pull_request`
- `workflow_dispatch`

The codecheck job runs on:

- Python 3.10
- Python 3.11

The codecheck installs `.[test]` and runs:

```bash
python -m ruff check src tests
python -m pytest -q --cov=shadowseed --cov-report=term-missing --cov-report=xml
```

## Standard benchmark and analysis routes

The standard CI workflow also runs benchmark or reporting jobs after pytest on `main`, including:

- gap suite: `python -m shadowseed.cli run-gap-suite`
- false-positive suite: `python -m shadowseed.cli run-false-positive-suite`
- benefit suite: `python -m shadowseed.cli run-benefit-suite`
- model-benefit fixture smoke: `python -m shadowseed.cli run-model-benefit-suite --backend fixture`
- blind benchmark smoke: `python -m shadowseed.cli run-blind-benchmark ...`
- adversarial Gate benchmark: `python -m shadowseed.cli run-adversarial-gate-benchmark`
- probe utility benchmark: `python -m shadowseed.cli run-probe-utility-benchmark`
- analysis report: `python -m shadowseed.cli analyze-results`
- AbsenceBench smoke: `python -m shadowseed.cli run-absencebench-smoke --output absencebench_smoke.json`
- repeat-test matrix for different gap-suite turn counts

The analysis job rebuilds a provenance-safe `results/` tree from downloaded artifacts through `shadowseed.analysis.artifact_snapshot` before running `analyze-results`.

## Manual OpenAI benefit workflow

The manual OpenAI workflow is `.github/workflows/openai-benefit.yml`.

It is triggered with `workflow_dispatch` and uses:

- `OPENAI_API_KEY`
- `contents: read`

Supported experiments:

- `model-benefit`
- `ssl-vs-rag`
- `adversarial-payoff`
- `wild-payoff`
- `generative-payoff`
- `ssl-session`

For `ssl-session`, the workflow now also generates a blind A/B review pack from `results/ssl_session_suite.json`:

- `results/blind_ab_review/ssl_session_blind_ab_review_items.json`
- `results/blind_ab_review/ssl_session_blind_ab_answer_key.json`
- `results/blind_ab_review/ssl_session_blind_ab_review_form.md`
- `results/blind_ab_review/ssl_session_blind_ab_scoring_template.csv`
- `results/blind_ab_review/ssl_session_blind_ab_summary.json`

These files are uploaded in the same `ssl-openai-ssl-session-<model>` artifact. The answer key is for post-review unblinding only.

## Manual open-set workflow

The manual open-set workflow is `.github/workflows/open-set-hf-review.yml`.

It is triggered with `workflow_dispatch` and uses:

- `HUGGINGFACE_TOKEN`
- `contents: write`

It runs these core steps:

1. fetch an open-set HF batch
2. build open-set review packets
3. generate a pending open-set summary
4. write a short artifact README
5. commit selected open-set summary artifacts back to `main` only when `github.ref == 'refs/heads/main'`
6. upload all open-set review artifacts

The write-back guard is important: branch-based manual runs should not push results to `main`.

## Current open-set artifact contract

Current canonical open-set names and paths are:

- seed output: `results/open_review/open_set_seed_output.json`
- review packets: `results/open_review/open_set_review_packets.json`
- analyzer-facing CLI default summary: `results/open_set_seed_review_summary.json`
- workflow write-back summary: `results/open_review/open_set_seed_review_summary.json`
- disagreements: `results/open_review/open_set_disagreements.json`
- report: `results/open_review/open_set_review_report.md`

The standard analysis workflow includes a passthrough step: if `results/open_review/open_set_seed_review_summary.json` exists in checkout, it is copied into `downloaded-artifacts/open-set-passthrough/` before artifact snapshotting.

This means open-set metrics stay `n/a` until the manual HF workflow has produced and committed a summary.

## Current CLI defaults worth preserving

Important defaults:

- `summarize-open-set-seed-review --output`: `results/open_set_seed_review_summary.json`
- `summarize-open-set-seed-review --disagreements-output`: `results/open_review/open_set_disagreements.json`
- `summarize-open-set-seed-review --report-output`: `results/open_review/open_set_review_report.md`
- `run-open-set-seed-review --review-packets`: `results/open_review/open_set_review_packets.json`
- `run-absencebench-smoke --output`: `absencebench_smoke.json`

The AbsenceBench default is intentionally not `results/absencebench_smoke.json`, because the result writer places it under `benchmarks/results/`.

## W9f baseline state

The W9f cross-turn *mechanism* is confirmed at safe doctrine thresholds (recurrence -> Gate -> surfacing fires reproducibly). The W9f *payoff quality* is a baseline candidate, not a closed result: the first blind review at safe thresholds came back split (round 022, two reviewers disagreed on 7/8).

Important repo state:

- PR #148 merged the follow-up cluster-liveness fixes.
- Release/tag `w9f-follow-up-baseline` freezes the mechanism state.
- PR #150 merged automatic blind A/B review-pack generation for `ssl-session` runs.
- Round 022 ran the first blind A/B review at safe thresholds; see `benchmarks/open_review/rounds/round_022/human_review/`.

## Backlog direction

The next research direction is not more mechanism proof (it fires), but use-time seed-discipline plus W10 doctrine-transfer:

- when may a promoted seed steer the answer (steer on sharpening, stay dormant on narrowing);
- additional domains;
- additional task types;
- model transfer;
- explicit seed-effect labels for help, no difference, ruis and vernauwing.

## Known limitations

This document is a snapshot, not a generated inventory.

Do not treat counts such as number of tests, workflow runs or wiki pages as stable unless they are regenerated and dated in a separate report.

## Interpretation

`shadowseed` is currently best understood as a Python SSL research harness with a strong lifecycle core, explicit artifact routes, and a confirmed W9f cross-turn *mechanism* at safe thresholds whose *payoff quality* is still reviewer-dependent (round 022). The next step is use-time seed-discipline plus doctrine transfer, not another proof loop around the mechanism.
