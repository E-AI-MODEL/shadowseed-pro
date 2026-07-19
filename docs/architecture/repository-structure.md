# Repository Structure

**Authority:** CANONICAL_SPEC
**Companion file:** [`repository-authority.yaml`](../../repository-authority.yaml) (machine-readable)

This document explains how the Shadowseed Pro repository is organized so that
humans and agents can tell, at a glance, **what is canonical, what is a legacy
facade, and what is frozen history** — and never mistake one for another. It is
the narrative companion to the machine-readable `repository-authority.yaml`.

## How to read the repository (quick rules)

1. **Canonical runtime code lives under `src/shadowseed/`** (and
   `src/shadowseed_agent/`). That is the only code the installed package ships.
2. **The installed package is the source of truth, not the checkout.** If
   something works only because the repo root is on `sys.path`, it is wrong.
3. **Seven files are legacy import facades** (`COMPATIBILITY_ONLY`). They
   re-export canonical objects and contain no logic. New code must never import
   them — import the canonical module instead.
4. **Everything under `archive/` is frozen history.** It is excluded from the
   package, must never be imported at runtime, and must not be cited as current
   guidance. Some archive material is in Dutch.
5. **When a result artifact has a canonical and a legacy name, canonical
   wins.** See "Artifact precedence" below.
6. When in doubt, consult `repository-authority.yaml`: the **most specific
   path/glob wins**.

## Current layout

```text
shadowseed-pro/
├── src/
│   ├── shadowseed/                 RUNTIME_IMPLEMENTATION (canonical package)
│   │   ├── *.py                    core runtime: chat, cli, manager, ssot,
│   │   │                           recurrence, retrieval_probe, prompts,
│   │   │                           seed_normalization, surfacing, …
│   │   ├── adapters/               model/service adapters (embedding, openai,
│   │   │                           ollama, models)
│   │   ├── detection/              open-set model detector
│   │   ├── analysis/               result analyzer + artifact snapshot
│   │   ├── vectorstore/            memory (canonical) + optional faiss/chroma
│   │   ├── data/                   packaged curated input data (package-data)
│   │   ├── benchmark/              EVALUATION_IMPLEMENTATION (suites) +
│   │   │                           7 COMPATIBILITY_ONLY facades (see below)
│   │   └── evaluation/             evaluation-area docs (README-only)
│   └── shadowseed_agent/           RUNTIME_IMPLEMENTATION (agent contract/policy)
├── tests/                          CONTRACT_TEST (contracts + regressions)
├── benchmarks/                     EVALUATION_IMPLEMENTATION inputs/rounds +
│   └── results/                    EVIDENCE_ARTIFACT (result snapshots)
├── results/                        EVIDENCE_ARTIFACT (analysis output location)
├── data/                           EVIDENCE_ARTIFACT (source papers, not packaged)
├── scripts/                        EVALUATION_IMPLEMENTATION (research tooling)
├── experiments/                    EVALUATION_IMPLEMENTATION (exploratory)
├── docs/                           CANONICAL_SPEC (architecture) + docs
│   └── architecture/               primary specification authority
├── archive/                        ARCHIVE / HISTORICAL_REFERENCE (frozen)
├── templates/                      review/run templates
├── examples/                       sample inputs
├── pyproject.toml                  CANONICAL_SPEC (packaging authority)
└── repository-authority.yaml       CANONICAL_SPEC (authority map)
```

## Responsibility model

| Area | Owns | Authority |
|---|---|---|
| `src/shadowseed/` top-level modules | Core SSL runtime, CLI, manager, SSOT | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/adapters/` | Embedding + LLM service adapters | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/detection/` | Open-set model detector | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/analysis/` | Result analysis, artifact precedence | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/vectorstore/` | Vector store backends | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/benchmark/` | Benchmark/evaluation suites | EVALUATION_IMPLEMENTATION |
| `src/shadowseed_agent/` | Agent contract + policies | RUNTIME_IMPLEMENTATION |
| `tests/` | Contract + regression tests | CONTRACT_TEST |
| `benchmarks/results/`, `results/`, `data/` | Generated/curated evidence | EVIDENCE_ARTIFACT |
| `archive/` | Frozen pre-rebuild material | ARCHIVE / HISTORICAL_REFERENCE |

## Compatibility facades

These seven legacy import paths remain only as thin re-export facades. Each is
`COMPATIBILITY_ONLY`, declares an explicit `__all__`, and delegates directly to
its canonical module — never to another facade.

| Legacy path | Canonical module |
|---|---|
| `shadowseed.benchmark.embedding_backends` | `shadowseed.adapters.embedding` |
| `shadowseed.benchmark.openai_client` | `shadowseed.adapters.openai_client` |
| `shadowseed.benchmark.ollama_client` | `shadowseed.adapters.ollama_client` |
| `shadowseed.benchmark.open_set_model_detector` | `shadowseed.detection.model_detector` |
| `shadowseed.benchmark.recurrence_clustering` | `shadowseed.recurrence_clustering` |
| `shadowseed.benchmark.seed_retrieval_probe` | `shadowseed.retrieval_probe` |
| `shadowseed.prompt_templates` | `shadowseed.prompts` |

Full rules: [`compatibility-policy.md`](compatibility-policy.md). The contract is
guarded by `tests/test_compatibility_contracts.py`.

## Artifact precedence

The result analyzer resolves the open-set review summary **canonical-first**:

```text
1. results/open_set_seed_review_summary.json        (canonical)
2. results/open_review/open_set_review_summary.json (legacy fallback)
```

When both exist, the canonical file wins. This is enforced in
`shadowseed.analysis.ssl45_result_analyzer.analyze_results` and guarded by
`tests/test_result_analyzer.py::test_result_analyzer_prefers_canonical_open_set_summary_over_legacy`.

## Why no files were physically moved

The v0.3.0 rebuild already places responsibilities under clear packages
(`adapters/`, `detection/`, `analysis/`, `vectorstore/`, `benchmark/`), and all
active runtime code already imports canonical paths — no active module imports a
compatibility facade. The remaining ambiguity was **authority legibility**, not
physical location: it was hard to tell canonical from legacy from archive.

Physical moves would have risked packaging (package-data, console entry points,
import identity) without improving that legibility. The chosen approach instead
makes authority **explicit and testable**:

- `repository-authority.yaml` — machine-readable classification of every area;
- explicit `COMPATIBILITY_ONLY` headers + `__all__` on all facades;
- visible historical banners on archive documentation;
- a canonical-first artifact-precedence guard.

Public APIs, CLI entry points, packaging, and benchmark semantics are unchanged.

## Packaging impact

None. `pyproject.toml` discovers packages from `src/` only, so `archive/`,
`benchmarks/`, `scripts/`, and `experiments/` are never packaged. Package-data
(`shadowseed/data/*.json`) is unchanged. Editable install, wheel build, and the
`shadowseed` console entry point all continue to work.

## If you do move files later

Follow the migration groups and gates in the restructure specification: move in
bounded groups, keep a compatibility facade at each historical import path
(delegating directly to the final canonical module — never facade-to-facade),
update `pyproject.toml` and docs in the same change, and re-run the full suite,
an out-of-tree import smoke, and a wheel build after each group.
