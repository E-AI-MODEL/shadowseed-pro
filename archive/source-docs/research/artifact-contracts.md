# Artifact and Analyzer Publication Contracts

> Status: current
> Date: 2026-05-22
> Evidence layer: Artifact contract — all layers
> Current source: yes


Status: current as of 2026-05-10
Base commit: `acd4e4512ca16d370595b26a99f4b8b4be42d320`
Related issue: #39

## Purpose

This document makes the artifact surface explicit.

It records how CLI commands, workflows, analyzer inputs and public report outputs connect. The goal is to prevent path drift and to make clear which files are raw evidence, which files are summaries, and which fields can shape public-facing interpretation.

This is a contract document. It does not change benchmark behavior.

## Terms

| Term | Meaning |
|---|---|
| Raw output | Direct benchmark or command output. Usually scenario-level or run-level data. |
| Summary | Aggregated metrics derived from raw output. Usually JSON under `summary`. |
| Analyzer-facing input | File that `shadowseed analyze-results` reads from `results/`. |
| Public-report input | File or field that can affect `analysis_report.md`, `analysis_summary.json`, Wiki or Pages publication. |
| Interpretive field | Field that goes beyond raw metric reporting and shapes wording, verdicts or claim boundaries. |
| Standard CI | Produced by `.github/workflows/tests.yml`. |
| Manual research | Produced only by manual workflows or local/manual runs. |
| Fixture | Deterministic or scaffolded run. Useful for regression and smoke checks, not broad validation. |

## Contract rules

1. A benchmark artifact name should have one canonical name.
2. CLI defaults, workflow output paths, analyzer lookup paths and docs must agree on that name.
3. Public-facing conclusions must be traceable to named analyzer inputs.
4. Raw evidence and interpretive report text must stay distinguishable.
5. Manual research artifacts may be absent. Their absence should lead to `n/a`, not broken analysis.
6. Write-back workflows must state what they commit and under which branch guard.

## Standard CI artifacts

These artifacts are produced by `.github/workflows/tests.yml` and are part of the standard publication path.

| Evidence layer | CLI command | Primary input | Canonical output | Analyzer lookup | Artifact type | Public role |
|---|---|---|---|---|---|---|
| Gap suite | `run-gap-suite` | `src/shadowseed/data/gap_test_suite_4_5.json` | `results/ssl45_gap_suite.json` | `results/ssl45_gap_suite.json` | raw output plus summary | Metric-bearing public input |
| False-positive suite | `run-false-positive-suite` | `src/shadowseed/data/gap_test_suite_false_positive_4_5.json` | `results/ssl45_false_positive_suite.json` | `results/ssl45_false_positive_suite.json` | raw output plus summary | Metric-bearing public input |
| Benefit suite | `run-benefit-suite` | `src/shadowseed/data/ssl45_benefit_suite.json` | `results/ssl45_benefit_suite.json` | `results/ssl45_benefit_suite.json` | raw output plus summary | Metric-bearing public input |
| Model benefit fixture smoke | `run-model-benefit-suite --backend fixture` | `src/shadowseed/data/ssl45_model_benefit_suite.json` | `results/ssl45_model_benefit_suite.json` | `results/ssl45_model_benefit_suite.json` | raw output plus summary | Metric-bearing public input |
| Blind benchmark smoke | `run-blind-benchmark` | `src/shadowseed/data/blind_suite_public.json` plus generated private labels | `results/blind_benchmark.json` | `results/blind_benchmark.json` | raw output plus summary | Metric-bearing public input |
| Adversarial Gate benchmark | `run-adversarial-gate-benchmark` | `src/shadowseed/data/adversarial_gate_benchmark.json` | `results/adversarial_gate_benchmark.json` | `results/adversarial_gate_benchmark.json` | raw output plus summary | Metric-bearing public input |
| Adversarial Gate casebook | `run-adversarial-gate-benchmark --casebook` | same as benchmark | `results/adversarial_gate_casebook.md` | not read by analyzer | public-supporting prose | Supporting artifact, not metric source |
| Probe utility benchmark | `run-probe-utility-benchmark` | `src/shadowseed/data/ssl45_probe_utility_suite.json` | `results/ssl45_probe_utility_suite.json` | `results/ssl45_probe_utility_suite.json` | raw output plus summary | Metric-bearing public input |
| AbsenceBench smoke | `run-absencebench-smoke` | `examples/local_absencebench_sample.json` | `benchmarks/results/absencebench_smoke.json` | not read by analyzer today | smoke output | CI smoke artifact, not report source |
| Repeat gap matrix | `run-gap-suite --turns N` | `src/shadowseed/data/gap_test_suite_4_5.json` | `results/ssl45_gap_suite_turns_N.json` | glob `results/ssl45_gap_suite_turns_*.json` | raw output plus summary | Public trend input |

## Manual and optional research artifacts

These artifacts are not guaranteed in every standard CI run.

| Evidence layer | CLI command or workflow | Primary input | Canonical output | Analyzer lookup | Artifact type | Status |
|---|---|---|---|---|---|---|
| Open-set HF batch | `fetch-open-set-hf-batch` in `.github/workflows/open-set-hf-review.yml` | HF source registry | `benchmarks/open_review/input/hf_batch.json` | not read by analyzer | intake batch | Manual research |
| Open-set seed output | `run-open-set-seed-review` | `benchmarks/open_review/input/hf_batch.json` | `results/open_review/open_set_seed_output.json` | not read by analyzer | raw output | Manual research; **gitignored** (transient: Actions artifact + per-round copy) |
| Open-set review packets | `run-open-set-seed-review --review-packets` | open-set seed output | `results/open_review/open_set_review_packets.json` | not read by analyzer | human-review input | Manual research; **gitignored** (transient: Actions artifact + per-round copy) |
| Open-set summary, CLI default | `summarize-open-set-seed-review` | `results/open_review/open_set_review_packets.json` | `results/open_set_seed_review_summary.json` | `results/open_set_seed_review_summary.json` | summary | Analyzer-facing manual result |
| Open-set summary, HF workflow write-back | `.github/workflows/open-set-hf-review.yml` | `results/open_review/open_set_review_packets.json` | `results/open_review/open_set_seed_review_summary.json` (nested) | not currently read by the analyzer at this nested path; a future fix should either copy to `results/open_set_seed_review_summary.json` after commit or extend the analyzer lookup | summary | Manual result; workflow path drift acknowledged |
| Open-set disagreements | `summarize-open-set-seed-review --disagreements-output` | review packets | `results/open_review/open_set_disagreements.json` | not read by analyzer | follow-up artifact | Manual research |
| Open-set report | `summarize-open-set-seed-review --report-output` | review packets | `results/open_review/open_set_review_report.md` | not read by analyzer | prose summary | Manual research |
| Vectorstore smoke | `run-vectorstore-smoke` | synthetic smoke input | `results/vectorstore_smoke.json` | `results/vectorstore_smoke.json` | smoke output | Optional manual input |
| SSOT smoke | `run-ssot-smoke` | synthetic smoke input | `results/ssot_smoke.json` | `results/ssot_smoke.json` | smoke output | Optional manual input |
| Retrieval benchmark | `run-retrieval-benchmark` | `src/shadowseed/data/retrieval_benchmark.json` | `results/retrieval_benchmark.json` | `results/retrieval_benchmark.json` | raw output plus metrics | Optional manual input |
| Retrieval model benchmark | `run-retrieval-model-benchmark` | retrieval and output benchmark data | `results/retrieval_model_benchmark.json` | `results/retrieval_model_benchmark.json` | raw output plus summary | Optional manual input |

## Open-set detector selection

`run-open-set-seed-review` chooses its candidate generator with `--detector`
(canonical list: `SUPPORTED_DETECTORS` in
`src/shadowseed/benchmark/open_set_candidate_adapter.py`). The CLI and the
`open-set-hf-review` workflow both follow that list. See
`docs/adr/0001-open-set-detector-strategy.md` for the rationale.

| `--detector` | `--model-backend` | What runs | Layer C evidence? |
|---|---|---|---|
| `adapter_v1` (default) | n/a | regex/template baseline (v0.1) | no — infrastructure |
| `adapter_v2` | n/a | text-grounded template baseline (v0.2) | no — stronger baseline |
| `model` | `fixture` | deterministic `[FIXTURE]` detector | no — CI fixture |
| `model` | `hf-transformers` (needs `--model-id`) | real taalmodel detector (v0.3) | yes — the only Layer-C-eligible combination |

Notes:
- the model path suppresses the auto-"ontbreekt" fragment expansion in
  `seed_normalization`, so language-model output is judged as written
- `--model-id`, `--max-new-tokens` only apply to `--model-backend hf-transformers`
- the summary records `detector` and `model_backend` so each artifact is
  traceable to the generator that produced it

## Open-set round and prescreen artifacts (round-local, manual research)

These artifacts live per round under `benchmarks/open_review/rounds/round_NNN/`.
They are manual research, round-local, and NOT read by `analyze-results`. None of
them is Layer-C evidence by itself: detector output is candidate-only (#109) and
only human review on the packets counts as `open_set_seed_quality` evidence.

| Artifact | Produced by | Type | Notes |
|---|---|---|---|
| `input/hf_batch.json` | `fetch-open-set-hf-batch` | intake batch | source items for the round |
| `model_seed_output.json` | `run-open-set-seed-review --detector model --model-backend hf-transformers` | raw output | v0.3 detector candidates; carries `detector`/`model_backend` provenance |
| `baseline_seed_output.json` | `run-open-set-seed-review --detector adapter_v1` | raw output | template baseline arm; not Layer-C eligible |
| `mechanical_prescreen.json` / `.md` | `scripts/prescreen_open_set_output.py` | triage filter | deterministic; NOT evidence and NOT human review |
| `blind_review_packets.json` | `scripts/build_blind_control_packets.py build` | human-review input | model+baseline candidates interleaved, arm hidden |
| `blind_key.json` | `scripts/build_blind_control_packets.py build` | hidden key | NOT committed; reviewers must not see it; deterministically regenerable from the two arm files |
| `blind_control_summary.json` | `scripts/build_blind_control_packets.py unblind` | summary | per-arm accept/atomic rates + model-minus-baseline delta, after un-blinding |

Contract notes:
- `results/open_review/open_set_seed_output.json` and
  `open_set_review_packets.json` are **gitignored, not committed**. The
  HF-review workflow's write-back commits only the summary set
  (`open_set_seed_review_summary.json` + disagreements + report + README), so
  tracking the two transient files froze them at the PR #76 state while the
  summary advanced (Codex finding on #128). The coherent per-run set lives in
  the Actions artifact and the curated `benchmarks/open_review/rounds/round_NNN/`
  copy; `tests/test_open_review_artifact_coherence.py` guards against
  re-tracking them.
- the prescreen `near_duplicate` flag marks near-identical restatements of the
  same gap only; distinct-but-related gaps are spared as Constellation material
  (4.5 §9.1)
- the prescreen `truncated` and `claim_vs_gap` codes are mutually exclusive
  diagnoses: an unfinished clause ("Of ..." without its scaffold, or a
  dangling tail) is a decoding/parse artifact (`truncated`); `claim_vs_gap`
  means the candidate ASSERTS a fact (main-clause finite verb without an
  absence marker). Since prompt v0.3g the canonical candidate form is the
  gap-label noun phrase (which cannot assert anything); absence sentences
  stay allowed. Conflating the two codes points prompt iterations at the
  wrong root cause
- the detector prompt enforces only generation-level rules (one gap, no
  fabrication, tied to this text); triviality, specificity and redundancy are
  review/Gate concerns, not generation blockades (02_atomic_seeds §2)
- near-paraphrase candidates from the model path are deliberately not
  auto-collapsed; they are surfaced to the reviewer (prescreen + `duplicate`
  reject code), consistent with the weightless-seed principle

## Known legacy fallback

The analyzer currently attempts this open-set path first:

- `results/open_review/open_set_review_summary.json`

That is a legacy fallback name. The canonical summary name is:

- `open_set_seed_review_summary.json`

New code, workflows and docs should not introduce new uses of `open_set_review_summary.json`. A later cleanup PR may remove the legacy analyzer fallback once compatibility is no longer needed.

## Analyzer publication outputs

The analyzer writes to `results/analysis/`.

| Output | Produced by | Type | Public role |
|---|---|---|---|
| `results/analysis/analysis_summary.json` | `shadowseed analyze-results` | machine-readable summary | Public report data, includes conclusion object |
| `results/analysis/analysis_report.md` | `shadowseed analyze-results` | Markdown report | Public-facing prose report |
| `results/analysis/coverage.svg` | `shadowseed analyze-results` | chart | Public chart |
| `results/analysis/false_positive.svg` | `shadowseed analyze-results` | chart | Public chart |
| `results/analysis/manifest.json` | workflow copy from `results/manifest.json` | provenance metadata | Publication provenance |

The analyzer output is not raw evidence. It is a derived publication layer.

## Analyzer fields by role

The analyzer summary has several kinds of fields.

### Metric-bearing fields

These fields should be treated as direct metric summaries from upstream artifacts:

- `gap`
- `false_positive`
- `benefit`
- `model_benefit`
- `blind`
- `adversarial_gate`
- `open_set_review`
- `retrieval`
- `retrieval_model`
- `probe_utility`
- `ssot`
- `vectorstore`
- `turn_matrix`

### Provenance and publication context

These fields describe publication context, not model quality:

- `manifest`
- `publish_mode`
- `charts`

### Interpretive and public-facing fields

These fields shape public interpretation and must be read as generated report framing, not raw benchmark output:

- `conclusion.verdict`
- `conclusion.headline`
- `conclusion.body`
- `conclusion.supporting_observations`
- `conclusion.claim_boundary`
- `semantic.by_domain`
- `semantic.by_scenario`
- `semantic.top_terms`

The conclusion object is selected from available payloads and metrics. It can be useful, but it is not a substitute for the underlying JSON artifacts.

## Publication boundary

The following files and fields can affect public-facing wording:

- `analysis_report.md`
- `analysis_summary.json`
- `conclusion.headline`
- `conclusion.body`
- `conclusion.verdict`
- `conclusion.supporting_observations`
- `conclusion.claim_boundary`
- open-set section in the report when `open_set_review` is present
- adversarial Gate section in the report when `adversarial_gate` is present
- probe utility rows when `probe_utility` is present

The following files are evidence inputs, not public conclusions by themselves:

- `ssl45_gap_suite.json`
- `ssl45_false_positive_suite.json`
- `ssl45_benefit_suite.json`
- `ssl45_model_benefit_suite.json`
- `blind_benchmark.json`
- `adversarial_gate_benchmark.json`
- `ssl45_probe_utility_suite.json`
- `open_set_seed_review_summary.json`

## Open-set passthrough rule

Open-set is a manual evidence layer.

Standard CI does not generate new open-set review data. It only passes through a summary if a previous manual open-set workflow committed one.

Current flow:

1. Manual HF workflow writes `results/open_review/open_set_seed_review_summary.json`.
2. Standard analysis checks whether that file exists in checkout.
3. If present, it copies it into `downloaded-artifacts/open-set-passthrough/`.
4. `artifact_snapshot` rebuilds a clean `results/` tree.
5. The analyzer reads `results/open_set_seed_review_summary.json`.

If no summary exists, open-set metrics should remain `n/a`.

## Write-back rule

The only open-set write-back route in this contract is `.github/workflows/open-set-hf-review.yml`.

It uses:

- `permissions: contents: write`
- branch guard: `if: github.ref == 'refs/heads/main'`

It may commit these files:

- `results/open_review/open_set_seed_review_summary.json`
- `results/open_review/open_set_disagreements.json`
- `results/open_review/open_set_review_report.md`
- `results/open_review/README.md`

Any new workflow that writes generated evidence back to the repository must document the same four things:

1. source workflow
2. branch guard
3. files written
4. whether the files are raw evidence, summaries or report text

## Contract checklist for future PRs

Before changing a benchmark command, analyzer lookup or workflow artifact path, check:

- Does the CLI default change?
- Does a workflow explicit path override the CLI default?
- Does `artifact_snapshot` preserve the expected file name?
- Does `analyze-results` read the new name?
- Does a test assert the important default or lookup?
- Does the output affect public metrics or public wording?
- Does the doc distinguish raw output from interpreted summary?

## Next hardening step

This document should be followed by a small test-focused PR that checks the most important defaults and analyzer lookups.

Suggested first test targets:

- `summarize-open-set-seed-review --output` defaults to `results/open_set_seed_review_summary.json`
- `run-absencebench-smoke --output` defaults to `absencebench_smoke.json`
- analyzer reads `results/open_set_seed_review_summary.json`
- no new code path introduces `open_set_review_summary.json` as a non-legacy artifact name
