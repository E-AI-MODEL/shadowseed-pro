# Shadow Seed Learning

Shadow Seed Learning (SSL) is an auditable memory discipline for language-model systems. A detected gap starts as a **weightless seed**. It may be stored, revisited, tested, and contradicted, but it cannot steer an answer or action until it passes a logged Validation Gate.

```text
trace > 0  means the seed is present
weight = 0 means the seed cannot steer
```

This repository is a cleaned, English-language research implementation. It combines the original runtime, tests, benchmark fixtures, and reusable logic that was previously embedded in benchmark modules. Historical source documents and result artifacts are retained under `archive/` for traceability.

## Status

**Research-ready, not production-ready.**

The repository contains:

- an SSL manager with separate trace and weight semantics;
- TTL decay and TrTL reactivation;
- a Validation Gate with contradiction handling;
- an agent-side safety contract checked at the point of influence;
- shared surfacing logic used by live chat and session benchmarks;
- deterministic fixture backends and optional real-model backends;
- benchmark suites, regression fixtures, and audit-friendly result writers;
- 375 passing tests in the migration baseline, with four optional-backend tests skipped.

Production deployment still needs durable persistence, migrations, monitoring, privacy and retention controls, operator gates, rollback, and real-world abuse testing.

## Install

```bash
python -m pip install --upgrade pip
pip install -e ".[test]"
pytest -q
```

Optional extras:

```bash
pip install -e ".[models]"          # Hugging Face and Torch
pip install -e ".[openai]"          # hosted OpenAI backend
pip install -e ".[vector]"          # FAISS and Chroma
pip install -e ".[paper]"           # PDF paper pipeline
```

## Quick start

```bash
shadowseed chat --backend fixture
shadowseed run-gap-suite
shadowseed run-false-positive-suite
shadowseed run-benefit-suite
shadowseed run-adversarial-gate-benchmark
shadowseed run-probe-utility-benchmark
```

The live chat stores the uncontaminated baseline answer in history. Promoted seeds are selected through the same shared surfacing policy used by the session benchmark, checked by `AgentSafetyContract`, and only then passed to the model.

## Repository map

```text
src/shadowseed/              core runtime, adapters, surfacing, retrieval, CLI
src/shadowseed_agent/        point-of-use influence contract and policies
src/shadowseed/benchmark/    benchmark runners and compatibility wrappers
tests/                       unit, integration, regression, and fixture tests
benchmarks/open_review/      active historical regression fixtures
docs/                        current English documentation
archive/                     original documents, workflows, results, and legacy files
```

Some benchmark inputs remain in Dutch on purpose. They are test data, not active repository prose, and preserve multilingual regression coverage and historical comparability.

## Core rule

A seed is a candidate absence, not a fact. Evidence is separate from generated speculation. Weight can rise only through the Validation Gate. Every influence attempt must be auditable.

## Documentation

- [Architecture overview](docs/architecture/overview.md)
- [Lifecycle and Validation Gate](docs/architecture/lifecycle-and-gate.md)
- [CLI usage](docs/usage/cli.md)
- [Research status](docs/research/status.md)
- [H-Neurons conclusion](docs/research/h-neurons-conclusion.md)
- [Migration audit](docs/migration/source-audit.md)
- [Reuse decisions](docs/migration/reuse-decisions.md)

## License

No license was present in the source archive. A license must be selected before public distribution or third-party reuse.
