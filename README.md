# Shadow Seed Learning (SSL)

> ### Gaps aren't a bug. Gaps are fuel.
>
> When a language model senses that *something is missing* from an answer, that hunch is a signal worth chasing — not an error to bury. Shadow Seed Learning turns **"what's missing"** into a disciplined starting point for asking better questions — while never letting a hunch pretend to be a fact.

Most systems are built to look like they know everything. SSL starts from the opposite conviction: **noticing what you don't know is a strength, and being honest about it is the whole point.** A model's sense of absence becomes a lead to investigate — but a lead is treated as a suspicion, not a verdict, until evidence and a logged check say otherwise.

Never heard of SSL? Good — this page assumes you haven't. Pick your lane:

- 🌱 **[In plain language](#-in-plain-language)** — no coding or AI background needed.
- 🛠️ **[For developers](#️-for-developers)** — the theory, then install, run, and the rules the code enforces.

---

## 🌱 In plain language

### The idea behind it

Imagine reading an essay and feeling *"wait — something important is missing here."* That feeling is often the most useful thought you have. SSL is built on a simple belief:

> **An AI noticing what's missing is more valuable than an AI pretending it knows everything.**

But that only works if there's a hard rule keeping everyone honest: **a hunch is never allowed to pose as the truth.** SSL lets an AI *have* hunches, remember them, and chase them down — while making sure a hunch can't quietly rewrite an answer until it has actually been checked.

### The one thing to remember

Think of a courtroom. A **suspicion is not a verdict.** Someone can be a suspect — written down, investigated, revisited — but they can't be treated as guilty until evidence passes a proper check, and the whole process stays on the record.

SSL does the same thing with an AI's hunches:

```text
trace  > 0   →  the AI remembers the hunch
weight = 0   →  the hunch is NOT allowed to change any answer
```

Every hunch starts *remembered but powerless.* It earns the power to influence an answer only by passing a check — and never before.

### How a hunch travels through the system

1. **Noticing.** The AI spots a possible gap — "something seems missing here." That becomes a **seed** (and each seed is exactly *one* small, checkable thing — never a vague "needs more detail").
2. **Powerless by default.** The seed is remembered but has *zero* influence. It cannot touch an answer yet.
3. **Fading and returning.** If nothing reinforces the seed, it slowly fades, like a memory you stop thinking about. If the topic comes back, the seed can wake up again.
4. **The check (the "Validation Gate").** Before a seed is ever allowed to matter, it has to pass a logged check that weighs real evidence and looks for anything that *contradicts* it. Contradiction can block it, weaken it, or reset it.
5. **One more check at the last second.** Even a seed that passed the gate is checked *again* the moment it tries to influence an answer.
6. **Everything is written down.** Every step — created, faded, returned, checked, used — is recorded, so a human can go back and see exactly what happened and why.

### Why this matters

Most AIs can't show you *why* they said something. SSL is built so you can **audit** it: real evidence stays separate from the AI's own guesses, guesses can't sneak into the answer, and there's a paper trail for every decision. It's about turning an AI's "memory" from something mysterious into something you can actually trust — and being upfront about the difference between *what's proven* and *what's still just a promising idea.*

---

## 🛠️ For developers

### Philosophy

In most LLM work a gap is a failure to be hidden. SSL inverts that: **a gap is a signal from the model's own representation about where its knowledge thins out.** The one-sentence claim:

> Shadow Seed Learning is a mechanism by which a language model detects small structural absences in an answer, stores those detections as **weightless shadow seeds**, and uses only *validated* seeds to make follow-up questions, retrieval, or falsification more targeted.

Shorter: **SSL uses what a model is missing as a starting point for targeted inquiry.** The core rule: **a seed contains exactly one gap** — small, specific, and testable, so a reviewer can say it is right, partly right, or wrong. A list of missing domains or a vague "add more nuance" is not a seed.

This is a deliberate move from *passive retrieval* to **active epistemic navigation**, resting on three ideas from the literature:

- **Epistemic (reducible) uncertainty** — Kendall & Gal, 2017. SSL targets "something should be here that isn't," not aleatoric noise. It is not a hallucination filter or a calibration system; it is *epistemic self-reporting about structural absence.*
- **Intrinsic motivation / computational curiosity** — Schmidhuber, 2011. Seeds are prioritized by how often they recur and how well they survive falsification.
- **Active learning** — Settles, 2009. A promoted seed marks a high-uncertainty region; a probe is the query the system chooses to reduce that uncertainty.

Running alongside the mechanism is an **epistemic-honesty discipline**: keep evidence separate from the model's own speculation, and keep *what works today* separate from *what still needs to be proven.* (This is the shift the 4.6 specification names explicitly: consolidate infrastructure and reporting, but never at the expense of epistemic honesty.)

### What the code enforces

SSL separates **detection → storage → validation → influence**, so a plausible model-generated gap never silently becomes memory or steers output.

```text
trace > 0   means the seed is present
weight = 0  means the seed cannot steer
```

- A seed is a *candidate absence*, not a fact; it holds exactly one gap.
- `trace` records presence, recurrence, and reactivation (decays via TTL, reactivates via TrTL); it **never** grants influence by itself.
- `weight` is steering power; new candidates start at `0.0` and rise **only** through a successful Validation Gate decision, and fall on contradiction or falsification.
- Lifecycle: `NEW → ACTIVE → DECAYING → DORMANT → PROMOTED or EXPIRED`; `EXPIRED` is terminal.
- Evidence (external/trusted) is kept separate from generated speculation.
- Promotion is necessary but not sufficient: `AgentSafetyContract` re-checks the seed at the point of use.
- Every influence attempt is recorded for replay and audit.

This repository is a cleaned, English-language **research implementation** of that mechanism. Historical source documents and result artifacts are retained under `archive/` for traceability.

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

In keeping with the epistemic-honesty discipline above: the scenario suites are a **regression and small-benchmark layer**, not final proof. The headline claim is intended to rest on open-set seed quality, adversarial noise control, probe utility, and domain transfer — layers the repository is built to grow into. Production deployment still needs durable persistence, migrations, monitoring, privacy and retention controls, operator gates, rollback, and real-world abuse testing.

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
- Conceptual origin: the SSL 4.5 and 4.6 specifications (archived Dutch source under [`archive/`](archive/)), from which the philosophy above is distilled.

## License

No license was present in the source archive. A license must be selected before public distribution or third-party reuse.
