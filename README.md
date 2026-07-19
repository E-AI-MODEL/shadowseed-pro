# Shadow Seed Learning (SSL)

**A way to let an AI keep track of things it might be missing — without letting those hunches secretly change its answers until they've been checked.**

Never heard of SSL? Good — this page assumes you haven't. Pick your lane:

- 🌱 **[In plain language](#-in-plain-language)** — no coding or AI background needed.
- 🛠️ **[For developers](#️-for-developers)** — install, run, architecture, and the rules the code enforces.

---

## 🌱 In plain language

### The problem it solves

When an AI assistant reads something, it often *notices things that seem to be missing* — a fact left out, a question left unanswered, an assumption nobody stated. That noticing can be useful. But it's also dangerous: the AI might take one of those **hunches** and quietly treat it as if it were **true**, changing its answer based on something it merely guessed.

Shadow Seed Learning is a set of strict rules that stop that from happening.

### The one idea to remember

Think of a courtroom. A **suspicion is not a verdict**. Someone can be a suspect — written down, investigated, revisited — but they can't be treated as guilty until the evidence has passed through a proper check, and the whole process is on the record.

SSL does the same thing with an AI's hunches:

```text
trace  > 0   →  the AI remembers the hunch
weight = 0   →  the hunch is NOT allowed to change any answer
```

Every hunch starts *remembered but powerless*. It earns the power to influence an answer only by passing a check — and never before.

### How a hunch travels through the system

1. **Noticing.** The AI spots a possible gap — "something seems missing here." That becomes a **seed**.
2. **Powerless by default.** The seed is remembered but has *zero* influence. It cannot touch an answer yet.
3. **Fading and returning.** If nothing reinforces the seed, it slowly fades (like a memory you stop thinking about). If the topic comes back up later, the seed can wake up again.
4. **The check (the "Validation Gate").** Before a seed is ever allowed to matter, it has to pass a logged check that weighs real evidence and looks for anything that *contradicts* it. Contradiction can block it, weaken it, or reset it.
5. **One more check at the last second.** Even a seed that passed the gate is checked *again* the moment it tries to influence an answer.
6. **Everything is written down.** Every time a hunch is created, fades, returns, passes a check, or tries to influence an answer, it's recorded — so a human can go back and see exactly what happened and why.

### Why that matters

Most AI systems can't show you *why* they said something. SSL is built so you can **audit** it: real evidence is kept separate from the AI's own guesses, guesses can't sneak into the answer, and there's a paper trail for every decision. It's about making an AI's "memory" trustworthy instead of mysterious.

That's the whole idea. If you want to see the machinery, read on. 👇

---

## 🛠️ For developers

Shadow Seed Learning (SSL) is an **auditable memory discipline for language-model systems**. A detected gap starts as a **weightless seed**. It may be stored, revisited, tested, and contradicted, but it cannot steer an answer or action until it passes a **logged Validation Gate**.

```text
trace > 0   means the seed is present
weight = 0  means the seed cannot steer
```

The system deliberately separates **detection → storage → validation → influence**, so a plausible model-generated gap never silently becomes memory or steers output. This repository is a cleaned, English-language **research implementation** that combines the runtime, tests, benchmark fixtures, and reusable logic. Historical source documents and result artifacts are retained under `archive/` for traceability.

### Core invariants

- A seed is a *candidate absence*, not a fact.
- `trace` records presence, recurrence, and reactivation (decays via TTL, reactivates via TrTL); it **never** grants influence by itself.
- `weight` is steering power; new candidates start at `0.0` and rise **only** through a successful Validation Gate decision.
- Evidence (external/trusted) is kept separate from generated speculation.
- Promotion is necessary but not sufficient: `AgentSafetyContract` re-checks the seed at the point of use.
- Every influence attempt is recorded for replay and audit.

### Install

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

### Quick start

```bash
shadowseed chat --backend fixture
shadowseed run-gap-suite
shadowseed run-false-positive-suite
shadowseed run-benefit-suite
shadowseed run-adversarial-gate-benchmark
shadowseed run-probe-utility-benchmark
```

The live chat stores the *uncontaminated baseline answer* in history. Promoted seeds are selected through the shared surfacing policy (also used by the session benchmark), checked by `AgentSafetyContract`, and only then passed to the model. This baseline isolation avoids two feedback loops: **gap starvation** (an SSL-improved answer hiding the absence that should be detected) and **history contamination** (past SSL additions becoming indistinguishable from the model's original context).

### Architecture at a glance

| Module | Responsibility |
|---|---|
| `shadowseed.manager` | Seed model, lifecycle, TTL, TrTL, Validation Gate, probe feedback |
| `shadowseed.surfacing` | Cross-turn eligibility, thresholds, ranking, resurface damping |
| `shadowseed.chat` | Live sidecar session with uncontaminated baseline history |
| `shadowseed.detection.model_detector` | Model-backed open-set candidate generation |
| `shadowseed.adapters` | Model, embedding, Ollama, and OpenAI runtime adapters |
| `shadowseed.retrieval_probe` | Retrieval probe execution |
| `shadowseed.recurrence_clustering` | Reusable recurrence clustering logic |
| `shadowseed.ssot` | Trusted external rules and evidence interfaces |
| `shadowseed.vectorstore` | Memory (canonical), FAISS, and Chroma storage adapters |
| `shadowseed_agent.agent_contract` | Zero-trust point-of-use influence decision |
| `shadowseed.benchmark` | Evaluation harnesses, regression suites, compatibility wrappers |

### Repository map

```text
src/shadowseed/              core runtime, adapters, surfacing, retrieval, CLI
src/shadowseed_agent/        point-of-use influence contract and policies
src/shadowseed/benchmark/    benchmark runners and compatibility wrappers
tests/                       unit, integration, regression, and fixture tests
benchmarks/open_review/      active historical regression fixtures
docs/                        current English documentation
archive/                     original documents, workflows, results, legacy files
repository-authority.yaml    machine-readable authority map (canonical vs legacy vs archive)
```

For how the repository is organized — and how to tell canonical code from legacy facades and frozen archive material — see [`repository-authority.yaml`](repository-authority.yaml) and [`docs/architecture/repository-structure.md`](docs/architecture/repository-structure.md).

Some benchmark inputs remain in Dutch on purpose: they are test data (not active prose) and preserve multilingual regression coverage and historical comparability.

### Status

**Research-ready, not production-ready.** The repository contains a working SSL manager with separate trace/weight semantics, TTL decay and TrTL reactivation, a Validation Gate with contradiction handling, an agent-side point-of-use safety contract, shared surfacing logic, deterministic fixture backends plus optional real-model backends, and benchmark/regression suites with audit-friendly result writers. The test baseline is **375 passing tests** (four optional-backend tests skipped).

Production deployment still needs durable persistence, migrations, monitoring, privacy and retention controls, operator gates, rollback, and real-world abuse testing.

### Documentation

- [Architecture overview](docs/architecture/overview.md)
- [Lifecycle and Validation Gate](docs/architecture/lifecycle-and-gate.md)
- [Repository structure](docs/architecture/repository-structure.md)
- [Compatibility policy](docs/architecture/compatibility-policy.md)
- [CLI usage](docs/usage/cli.md)
- [Research status](docs/research/status.md)
- [H-Neurons conclusion](docs/research/h-neurons-conclusion.md)
- [Migration audit](docs/migration/source-audit.md)
- [Reuse decisions](docs/migration/reuse-decisions.md)

## License

No license was present in the source archive. A license must be selected before public distribution or third-party reuse.
