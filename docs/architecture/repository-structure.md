# Repository Structure

**Authority:** CANONICAL_SPEC  
**Companion file:** [`repository-authority.yaml`](../../repository-authority.yaml) (machine-readable)

This document explains how the Shadowseed Pro repository is organized so humans and agents can tell what is canonical runtime/specification, what is evaluation or publication material, what is compatibility-only, and what is frozen or historical context.

## How to read the repository

1. **Canonical runtime code lives under `src/shadowseed/` and `src/shadowseed_agent/`.** That is the code the installed package ships.
2. **Canonical architecture lives under `docs/architecture/`.** The manuscript may describe reviewed runtime evidence, but it cannot override current architecture or runtime behavior.
3. **The installed package is the runtime source of truth, not an accidental checkout import.** If behavior works only because the repository root is on `sys.path`, it is wrong.
4. **Seven files are legacy import facades** (`COMPATIBILITY_ONLY`). They re-export canonical objects and contain no independent logic. New code must import the canonical module instead.
5. **Everything under `archive/` is frozen history.** It must not be imported at runtime or cited as current guidance.
6. **Research/evaluation artifacts do not become product authority.** Benchmarks, results and the paper can report evidence but cannot authorize seeds or redefine runtime contracts.
7. **Execution plans and rebuild audit records are historical context.** `docs/plans/README.md` explains their precedence; completed or superseded plans cannot override later ADRs, runtime behavior, research status, or product documentation.
8. **When a result artifact has a canonical and legacy name, canonical wins.** See [Artifact precedence](#artifact-precedence).
9. When in doubt, consult `repository-authority.yaml`: the **most specific path/glob wins**.

## Current layout

```text
shadowseed-pro/
├── src/
│   ├── shadowseed/                 RUNTIME_IMPLEMENTATION (canonical package)
│   │   ├── manager.py              orchestration, registry, logs, serialization,
│   │   │                           authority mutation primitive, compatibility facade
│   │   ├── models.py               stable data contracts and authority guards
│   │   ├── contradictions.py       contradiction collection and lifecycle
│   │   ├── intake.py               embedding, normalization, dedup, seed creation
│   │   ├── lifecycle.py            TTL, dormancy, TrTL, terminal expiry
│   │   ├── vector_workflows.py     vector search, feedback routing, constellations
│   │   ├── gate/                   typed signals/policies/events + Gate engine
│   │   ├── application/            UI-independent tester/session workflows
│   │   ├── storage/                workspace persistence, backup/restore, audit storage
│   │   ├── workbench/              chat-first Gradio UI + standalone launcher
│   │   ├── adapters/               model/service adapters
│   │   ├── detection/              open-set model detector
│   │   ├── analysis/               result analyzer + artifact snapshot
│   │   ├── vectorstore/            memory + optional FAISS/Chroma stores
│   │   ├── data/                   packaged curated input data
│   │   ├── benchmark/              evaluation suites + 7 compatibility facades
│   │   ├── evaluation/             evaluation-area docs/placeholders
│   │   └── *.py                    chat, CLI, SSOT, retrieval, prompts, surfacing, etc.
│   └── shadowseed_agent/           point-of-use contract and audit policy
├── tests/                          CONTRACT_TEST
├── benchmarks/                     EVALUATION_IMPLEMENTATION
│   └── results/                    EVIDENCE_ARTIFACT result snapshots
├── results/                        EVIDENCE_ARTIFACT analysis output
├── data/                           EVIDENCE_ARTIFACT source/reference material
├── paper/                          EVIDENCE_ARTIFACT manuscript/publication bundle
├── scripts/                        research/build/operational tooling
├── experiments/                    exploratory research runners
├── docs/
│   ├── architecture/               primary CANONICAL_SPEC authority
│   ├── workbench/                  current tester/product documentation
│   ├── research/                   current research status and bounded conclusions
│   ├── usage/                      current CLI/user guidance
│   ├── plans/                      HISTORICAL_REFERENCE execution records; README is index
│   └── migration/                  current language policy plus historical rebuild records
├── .github/workflows/              CI, portability, standalone and release automation
├── archive/                        ARCHIVE / HISTORICAL_REFERENCE
├── templates/                      review/run templates
├── examples/                       sample inputs
├── pyproject.toml                  packaging authority
└── repository-authority.yaml       machine-readable authority map
```

## Responsibility model

| Area | Owns | Authority |
|---|---|---|
| `src/shadowseed/manager.py` | Runtime orchestration, state registry, logs, serialization, compatibility facade | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/models.py` | Stable data contracts and guarded authority fields | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/contradictions.py` | Contradiction collection, blocking state, formal resolution | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/intake.py` | Embedding, normalization, deduplication, seed creation/update | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/lifecycle.py` | TTL, dormancy, TrTL, terminal expiry | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/vector_workflows.py` | Vector search, feedback routing, constellation construction | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/gate/` | Typed Gate contracts, policies, logging, executable authority engine | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/application/` | UI-independent product workflows and session orchestration | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/storage/` | Local workspace persistence, migrations, backup/restore, audit storage | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/workbench/` | Chat-first tester UI and standalone launcher | RUNTIME_IMPLEMENTATION |
| Other `src/shadowseed/*.py` modules | Chat, CLI, SSOT, surfacing, probes, prompts | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/adapters/` | Embedding and LLM service adapters | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/detection/` | Open-set model detector | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/analysis/` | Result analysis and artifact precedence | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/vectorstore/` | Vector store backends | RUNTIME_IMPLEMENTATION |
| `src/shadowseed/benchmark/` | Benchmark/evaluation suites | EVALUATION_IMPLEMENTATION |
| `src/shadowseed_agent/` | Point-of-use contract and policies | RUNTIME_IMPLEMENTATION |
| `tests/` | Contract and regression tests | CONTRACT_TEST |
| `benchmarks/results/`, `results/`, `data/` | Generated or curated research evidence/reference material | EVIDENCE_ARTIFACT |
| `paper/` | Manuscript source, bibliography and compiled publication artifact; not runtime/spec authority | EVIDENCE_ARTIFACT |
| `docs/plans/**` | Execution and alignment history; `docs/plans/README.md` is the current precedence index | HISTORICAL_REFERENCE |
| selected `docs/migration/` audit records and `MIGRATION_REPORT.md` | Rebuild provenance and historical inventories | HISTORICAL_REFERENCE |
| `archive/` | Frozen pre-rebuild material | ARCHIVE / HISTORICAL_REFERENCE |

## Product and research surfaces

The ordinary Workbench product surface lives in `src/shadowseed/workbench/` and delegates to canonical runtime/application/storage modules. New ordinary sessions are live/evidence-backed. The optional same-message SSL-off control is generated automatically and cannot mutate detector, recurrence, Gate, seed, or later conversation-history state.

Historical evaluation sessions, authored baseline fixtures, scenario JSON, benchmark outputs and other controlled comparison tooling remain research/evaluation material. They are not prerequisites for the product flow.

The `paper/` directory is a publication bundle. `main.tex` is manuscript source and `shadowseed-paper.pdf` is its compiled artifact. Any manuscript refresh must update source claims against an exact reviewed commit and regenerate the PDF. Neither the manuscript nor its bibliography may silently supersede `docs/architecture/**` or the runtime.

Execution plans preserve sequence and rationale, not current authority. Current contract questions should be answered from architecture/runtime first. Current claim questions should be answered from `docs/research/status.md`; current product questions should be answered from the Workbench/usage docs.

## Compatibility facades

These seven legacy import paths remain thin re-export facades. Each is `COMPATIBILITY_ONLY`, declares an explicit `__all__`, and delegates directly to its canonical module.

| Legacy path | Canonical module |
|---|---|
| `shadowseed.benchmark.embedding_backends` | `shadowseed.adapters.embedding` |
| `shadowseed.benchmark.openai_client` | `shadowseed.adapters.openai_client` |
| `shadowseed.benchmark.ollama_client` | `shadowseed.adapters.ollama_client` |
| `shadowseed.benchmark.open_set_model_detector` | `shadowseed.detection.model_detector` |
| `shadowseed.benchmark.recurrence_clustering` | `shadowseed.recurrence_clustering` |
| `shadowseed.benchmark.seed_retrieval_probe` | `shadowseed.retrieval_probe` |
| `shadowseed.prompt_templates` | `shadowseed.prompts` |

Full rules: [`compatibility-policy.md`](compatibility-policy.md). The contract is guarded by `tests/test_compatibility_contracts.py`.

## Artifact precedence

The result analyzer resolves the open-set review summary canonical-first:

```text
1. results/open_set_seed_review_summary.json        (canonical)
2. results/open_review/open_set_review_summary.json (legacy fallback)
```

When both exist, the canonical file wins. This is enforced in `shadowseed.analysis.ssl45_result_analyzer.analyze_results` and guarded by `tests/test_result_analyzer.py::test_result_analyzer_prefers_canonical_open_set_summary_over_legacy`.

## Manager modularization

The original `manager.py` combined data contracts, contradiction workflows, Gate execution, intake, lifecycle, vector search, constellation construction and probe feedback. Those concerns were moved in bounded, behavior-preserving steps while `SSLManager` kept historical methods as explicit facades:

1. `shadowseed.models` - stable data contracts;
2. `shadowseed.contradictions` - contradiction state and record lifecycle;
3. `shadowseed.intake` - embedding, normalization, deduplication, creation;
4. `shadowseed.lifecycle` - TTL, dormancy, TrTL, expiry;
5. `shadowseed.vector_workflows` - vector search, feedback, constellations;
6. `shadowseed.gate.runtime_adapter` - Gate-controlled authority decisions.

`manager.py` now owns configuration, the live seed registry, audit collections, serialization, the guarded authority mutation primitive and compatibility method routing. Contract tests pin delegation, import identity, authority boundaries and a size ceiling so the former monolith cannot silently return.

## Packaging impact

Runtime modules and subpackages under `src/shadowseed/` are discovered by the package configuration. The Workbench extra and standalone build include the additional product dependencies explicitly. Public manager imports, CLI entry points and package data remain controlled through `pyproject.toml`.

`archive/`, `benchmarks/`, `paper/`, `scripts/`, `experiments/`, historical plans, and rebuild audit records are not runtime package code. Paper and benchmark artifacts may be shipped or published separately without becoming runtime authority.

## If you move files later

Move files in bounded groups, preserve compatibility facades at historical import paths when required, delegate directly to final canonical modules rather than facade-to-facade, update `pyproject.toml`, `repository-authority.yaml` and docs in the same change, then re-run the full suite, out-of-tree import smoke, wheel build and any affected Workbench/standalone gates.
