# Shadowseed Pro

<p align="center">
  <strong>An auditable research implementation of Shadow Seed Learning.</strong>
</p>

<p align="center">
  <a href="https://github.com/E-AI-MODEL/shadowseed-pro/actions/workflows/ci.yml">
    <img alt="Continuous integration" src="https://github.com/E-AI-MODEL/shadowseed-pro/actions/workflows/ci.yml/badge.svg">
  </a>
  <img alt="Repository version 0.3.0" src="https://img.shields.io/badge/repository-0.3.0-2f6f5e">
  <img alt="Python 3.10 or higher" src="https://img.shields.io/badge/Python-3.10%2B-3776AB">
  <img alt="Research status research ready" src="https://img.shields.io/badge/status-research--ready-c88719">
  <img alt="Active repository language English" src="https://img.shields.io/badge/active_language-English-6f42c1">
  <img alt="All rights reserved" src="https://img.shields.io/badge/rights-all_rights_reserved-red">
</p>

<p align="center">
  <code>trace &gt; 0</code> means a candidate is remembered. <code>weight = 0</code> means it cannot steer.
</p>

Shadow Seed Learning, or SSL, treats a possible omission in a model answer as a **candidate for investigation**, not as hidden truth. The candidate is stored as an atomic shadow seed. It may recur, decay, reactivate, collect evidence, face contradiction, and be promoted. It may influence retrieval or an answer only after a logged Validation Gate decision and a second point-of-use safety check.

This repository contains the runtime, tests, benchmark harnesses, research instruments, evidence artifacts, and historical material used to examine that mechanism.

> [!IMPORTANT]
> **Shadowseed Pro is research-ready, not production-ready.**
>
> The repository implements and tests the main SSL mechanics. It does not establish general answer-quality improvement, universal hallucination detection, a general neural signal for missing context, or safe deployment in high-impact settings.

> [!NOTE]
> The core runtime code is English, and this is enforced automatically ([`docs/migration/language-policy.md`](docs/migration/language-policy.md)). Benchmark suites and JSON data fixtures retain documented Dutch content for compatibility, and historical Dutch source material is kept under [`archive/`](archive/) for provenance — neither should be treated as current runtime authority.

> [!CAUTION]
> This repository currently has **no open-source license**. All rights are reserved. Public visibility is not permission for reuse. See [Rights and temporary licensing position](#rights-and-temporary-licensing-position).

---

## Choose your route

| I want to... | Start here |
|---|---|
| Understand why this project exists | [Project origin and author note](#project-origin-and-author-note) |
| Understand SSL without reading code | [The idea in plain language](#the-idea-in-plain-language) |
| See the rule that protects answers from unverified seeds | [The invariant](#the-invariant) |
| See the full runtime path | [How a seed moves through the system](#how-a-seed-moves-through-the-system) |
| Find the code behind each claim | [What the code enforces](#what-the-code-enforces) |
| Understand the H-Neurons connection | [H-Neurons: code influence and separate experiment](#h-neurons-code-influence-and-separate-experiment) |
| Review the scientific basis | [Scientific basis and exact claim boundaries](#scientific-basis-and-exact-claim-boundaries) |
| Review weaknesses and open questions | [Discussion and limitations](#discussion-and-limitations) |
| Install and run the package | [Quick start](#quick-start) |
| Run the H-Neurons-style activation probe | [Activation-probe commands](#activation-probe-commands) |
| Navigate the repository | [Repository map](#repository-map) |
| Understand what is canonical, legacy, or archived | [Repository authority](#repository-authority) |
| Check the evidence level of a result | [Evidence hierarchy](#evidence-hierarchy) |
| See what is proven and what remains open | [Research status](#research-status) |
| Check current usage rights | [Rights and temporary licensing position](#rights-and-temporary-licensing-position) |

---

# Project origin and author note

## The question that started the project

Most AI systems are evaluated on what they produce. Much less attention is paid to what a fluent answer leaves out.

A response can be plausible and still omit a causal boundary, dependency, stakeholder, alternative explanation, contradiction, or necessary question. That omission may matter more than another paragraph of generated text.

Shadow Seed Learning began with a practical question:

> Can an AI system record a suspected omission, keep it powerless while it is uncertain, test it over time, and allow it to influence later work only after explicit validation?

The safety condition was part of the question from the start. A detected gap must not quietly become a fact, memory, or instruction.

## Author note

I am not a formally trained programmer or machine-learning researcher. This repository was developed through iterative, AI-assisted engineering, public research, explicit specifications, tests, benchmark rounds, and repeated attempts to disprove attractive results.

That background is not presented as a credential. It is a limitation that shaped the repository:

- claims are linked to code, tests, or result artifacts;
- runtime code is separated from experiments and history;
- seeds start powerless rather than trusted;
- generated proposals are separated from verified evidence;
- negative results are retained;
- the project states what has not been established;
- independent review remains necessary.

The repository should not be trusted because its author sounds certain. It should be inspected because the decision path is visible.

## How the project developed

The project can be read as a sequence of stricter questions:

1. Can a missing point be represented as one small, testable candidate?
2. Can presence be separated from influence through `trace` and `weight`?
3. Can candidates decay, reactivate, expire, and lose influence after contradiction?
4. Can recurrence, evidence, and falsification pass through one logged Gate?
5. Can promoted seeds be checked again at the exact point where an agent might use them?
6. Can the mechanism be tested with fixtures, adversarial cases, open-set review, transfer, and blind comparison?
7. Can an H-Neurons-style instrument find a stable internal signal for dialectical verdicts?
8. Can a failed replication narrow the claim instead of being hidden?

The H-Neurons work is part of this path, but it is not the sole origin or foundation of SSL. It supplied a recent measurement precedent for one separate research track. The operational runtime remains based on external, logged, reversible decisions.

---

# The idea in plain language

A model answer can be fluent and still leave out a relation, boundary, dependency, assumption, alternative explanation, or relevant contradiction.

SSL allows a detector to say:

> Something specific may be missing here.

That statement is not accepted as fact. It becomes a small, testable seed with no authority over the answer. The system can remember it, look for recurrence, compare it with trusted material, try to falsify it, and record every decision. A seed gains influence only after it passes the Validation Gate.

A useful analogy is a research notebook:

- an observation can be recorded before it is believed;
- repeated observations can justify closer investigation;
- evidence and contradiction must remain visible;
- a hypothesis does not become a result because it sounds plausible;
- a rejected hypothesis must lose influence;
- the route from observation to decision must be reconstructable.

SSL applies that discipline to candidate absences in model output.

## What a seed is

A seed is one atomic candidate absence.

Good seed:

```text
The answer does not state whether the reported association is causal.
```

Too broad:

```text
The answer needs more context, nuance, limitations, causes, consequences, and alternatives.
```

The first can be checked. The second hides several different claims inside one vague instruction.

## What SSL is not

SSL is not:

- a claim that model intuitions are facts;
- a generic long-term memory that silently rewrites future answers;
- a replacement for retrieval, source verification, or human review;
- a universal hallucination detector;
- a claim that an internal neuron signal has been established;
- a production safety certification.

---

# The invariant

The central rule is intentionally simple:

```text
trace  > 0   means the seed is present in shadow memory
weight = 0   means the seed has no steering authority
```

`trace` and `weight` are separate state variables with separate meanings.

| Concept | Meaning | What it cannot do |
|---|---|---|
| `trace` | Presence, recurrence, decay, and reactivation | Grant influence by itself |
| `weight` | Bounded steering authority after validation | Rise because a detector sounds convincing |
| seed | A candidate absence | Count as evidence for itself |
| evidence | External or verified support | Bypass the Validation Gate |
| contradiction | A reason to block, reduce, or reset influence | Be hidden from the audit trail |
| promotion | Permission to be considered | Force inclusion in an answer |
| surfacing | Contextual selection at use time | Override the safety contract |

Three consequences follow:

1. **Detection is not validation.** A detector may propose a seed, but the seed starts at `weight = 0.0`.
2. **Promotion is not mandatory use.** A promoted seed must still fit the current question and pass point-of-use checks.
3. **A signal is not a verdict.** This applies to model-generated gaps, retrieval hits, probe outcomes, and neuron activations.

---

# How a seed moves through the system

```mermaid
flowchart TD
    Q[User question] --> B[Generate uncontaminated baseline answer]
    B --> H[Store baseline in conversation history]
    B --> D[Detect candidate absences]
    D --> N[Normalize into atomic seeds]
    N --> S[Store seed: trace above zero, weight zero]

    S --> T[TTL decay]
    T --> X{Dormant too long?}
    X -->|yes| E[EXPIRED]
    X -->|no| R[TrTL reactivation by trigger or semantic match]

    S --> C[Recurrence and clustering]
    S --> O[Verified SSOT evidence]
    S --> F[Dialectical falsification]
    C --> G[Validation Gate]
    O --> G
    F --> G

    G -->|blocked| W[Remain weightless or active]
    G -->|contradicted| Z[Reduce or reset weight and log contradiction]
    G -->|validated enough| P[PROMOTED]

    P --> U[Shared surfacing policy]
    U --> A[AgentSafetyContract]
    A -->|blocked| L[Log denied influence]
    A -->|allowed| I[Optional retrieval, probe, or answer influence]
    I --> J[Log influence decision]

    B --> V[Visible baseline or SSL-assisted answer]
    I --> V
```

## Baseline isolation

The live chat generates a baseline answer without seed influence. That baseline is:

- inspected for new gaps;
- stored in conversation history;
- kept separate from the SSL-assisted visible answer.

This limits two feedback loops:

- **gap starvation:** an SSL-assisted answer fills an omission and prevents the detector from seeing the original absence;
- **history contamination:** an earlier SSL addition becomes indistinguishable from the model's original answer in later turns.

The implementation is in [`src/shadowseed/chat.py`](src/shadowseed/chat.py) and the shared prompt and surfacing logic is in [`src/shadowseed/surfacing.py`](src/shadowseed/surfacing.py).

## Lifecycle

```text
NEW -> ACTIVE -> DECAYING -> DORMANT -> EXPIRED
                         \-> PROMOTED
```

`EXPIRED` is terminal. A dormant seed may return through TrTL recognition, but an expired seed is not silently resurrected.

---

# What the code enforces

The table below connects repository claims to current code. It is not a list of aspirations.

The authority model — the single non-bypassable Validation Gate — is specified in [ADR-001](docs/architecture/adr/ADR-001-validation-gate-authority.md) and detailed under [`docs/architecture/`](docs/architecture/) ([gate contracts](docs/architecture/gate-contracts.md), [lifecycle and gate](docs/architecture/lifecycle-and-gate.md), [prompt boundary](docs/architecture/prompt-boundary.md)).

| Property | Runtime implementation | Tests or evaluation |
|---|---|---|
| Atomic candidate seeds | [`manager.py`](src/shadowseed/manager.py), [`seed_normalization.py`](src/shadowseed/seed_normalization.py) | [`test_atomic_seed_rules.py`](tests/test_atomic_seed_rules.py), [`test_seed_normalization.py`](tests/test_seed_normalization.py) |
| New seeds start weightless, and authority is encapsulated | [`ShadowSeed`](src/shadowseed/manager.py) (authority fields are `init=False` and guarded; the seed registry is a read-only view) | [`test_authority_encapsulation.py`](tests/test_authority_encapsulation.py) |
| Trace is separate from influence | [`manager.py`](src/shadowseed/manager.py) | [`test_manager_alignment.py`](tests/test_manager_alignment.py), [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py) |
| TTL decay and terminal expiry | [`SSLManager.decay_traces`](src/shadowseed/manager.py) | [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py), [`test_bad_seed_dies_out.py`](tests/test_bad_seed_dies_out.py) |
| TrTL reactivation | [`SSLManager.reactivate_by_text`](src/shadowseed/manager.py) | [`test_lifecycle_ttl.py`](tests/test_lifecycle_ttl.py) |
| Effects route through one Gate via typed signals and a named policy | [`SSLManager.submit_signals`](src/shadowseed/manager.py), [`shadowseed.gate`](src/shadowseed/gate/) | [`test_gate_contracts.py`](tests/test_gate_contracts.py), [`test_gate_signal_routing.py`](tests/test_gate_signal_routing.py) |
| Recurrence is never relabeled or double-counted as external evidence | [`shadowseed.gate.signals`](src/shadowseed/gate/signals.py), [`chat.py`](src/shadowseed/chat.py) | [`test_gate_signal_routing.py`](tests/test_gate_signal_routing.py) |
| Contradictions have an auditable lifecycle and Gate-controlled recovery | [`shadowseed.gate.contradictions`](src/shadowseed/gate/contradictions.py), [`SSLManager.resolve_contradiction`](src/shadowseed/manager.py) | [`test_contradiction_lifecycle.py`](tests/test_contradiction_lifecycle.py) |
| Generated output is not trusted evidence | [`ssot.py`](src/shadowseed/ssot.py), [`agent_contract.py`](src/shadowseed_agent/agent_contract.py) | [`test_ssot_manager.py`](tests/test_ssot_manager.py), [`test_agent_safety_contract.py`](tests/test_agent_safety_contract.py) |
| Influence is one atomic, replayable point-of-use decision | [`AgentSafetyContract.decide_and_record`](src/shadowseed_agent/agent_contract.py) | [`test_point_of_use.py`](tests/test_point_of_use.py) |
| Surfaced seeds are bounded, quoted candidate data (prompt boundary) | [`surfacing.py`](src/shadowseed/surfacing.py) | [`test_prompt_boundary.py`](tests/test_prompt_boundary.py) |
| Live chat and benchmarks share surfacing logic | [`surfacing.py`](src/shadowseed/surfacing.py) | [`test_surfacing.py`](tests/test_surfacing.py), [`test_ssl_session_suite.py`](tests/test_ssl_session_suite.py) |
| Baseline history remains uncontaminated | [`chat.py`](src/shadowseed/chat.py) | [`test_shadow_chat.py`](tests/test_shadow_chat.py) |
| Retrieval probes report presence without declaring truth | [`retrieval_probe.py`](src/shadowseed/retrieval_probe.py), [`chat.py`](src/shadowseed/chat.py) | [`test_seed_retrieval_probe.py`](tests/test_seed_retrieval_probe.py), [`test_ssl_vs_rag_benchmark.py`](tests/test_ssl_vs_rag_benchmark.py) |
| Every Gate decision and influence attempt is an immutable, replayable record | [`SSLManager.gate_events`](src/shadowseed/manager.py), [`audit_policy.py`](src/shadowseed_agent/audit_policy.py) | [`test_point_of_use.py`](tests/test_point_of_use.py), [`test_shadow_chat.py`](tests/test_shadow_chat.py) |
| Active runtime language is English (enforced) | core runtime + checker | [`test_language_alignment.py`](tests/test_language_alignment.py) |

## Seed origin metadata

[`SeedOrigin`](src/shadowseed/manager.py) records why a detector proposed a candidate, including its candidate type, detection basis, and optional context reference.

This metadata is audit-only. It does not count as evidence and cannot raise weight. A persuasive rationale still leaves a new seed at `weight = 0.0`.

## Trusted evidence is stored separately

[`SSOTManager`](src/shadowseed/ssot.py) keeps trusted document chunks separate from uncertain seeds.

- verified chunks may supply external evidence to the Gate;
- LLM-generated claims enter as unverified proposals;
- proposed chunks remain searchable but cannot validate seeds until explicitly verified;
- the SSOT never assigns weight directly.

## Dialectical falsification

[`dialectic_falsification.py`](src/shadowseed/benchmark/dialectic_falsification.py) asks an adversarial reviewer to argue a candidate away against its source text.

- `WEERLEGD` (canonical `REFUTED`) routes through a Gate contradiction and removes influence;
- `HOUDT_STAND` (canonical `SURVIVES`) can provide bounded probe feedback but cannot promote a seed;
- `ONBESLIST` (canonical `UNDECIDED`) is neutral;
- ambiguous model output fails safe to `ONBESLIST` / `UNDECIDED`.

The `DialecticVerdict` enum provides the canonical English names; the Dutch token values are retained as serialization aliases for artifact and model-output compatibility.

---

# H-Neurons: code influence and separate experiment

H-Neurons appears in this repository in **two different roles**. They must not be merged into one claim.

## Role 1: a methodological influence on the activation-probe code

Gao et al. introduced H-Neurons as a sparse subset of feed-forward neurons whose activations can predict hallucination occurrence in large instruction-tuned models. Their public pipeline uses neuron-level activation extraction and sparse logistic regression. Their intervention example acts on the input to the MLP down projection.

Shadowseed Pro adapts parts of that **measurement pattern** for a different research question:

> Can a small model's internal activations linearly separate external dialectical verdicts about whether a candidate absence survives falsification?

The corresponding implementation is [`src/shadowseed/benchmark/activation_probe.py`](src/shadowseed/benchmark/activation_probe.py).

| H-Neurons-inspired element | Shadowseed implementation |
|---|---|
| Per-neuron read point | `HFActivationModel(read_location="neuron")` captures the input to `mlp.down_proj` or `mlp.c_proj`, after the nonlinearity and before projection back to the residual stream |
| Sparse linear detector | NumPy L1 logistic regression using deterministic ISTA/FISTA |
| Sparse candidate dimensions | Non-zero classifier weights are reported as `candidate_neurons`, not established causal neurons |
| Generalization check | Leave-one-out cross-validation reports balanced accuracy |
| Chance control | Exact or Monte Carlo label-shuffle permutation tests |
| Focused activation extraction | Statement-token pooling can isolate the candidate claim from the surrounding source and prompt |
| Reproducibility fields | Model revision, load dtype, verdict source, label coverage, and permutation count are written to the result artifact |
| Separation of label source and probed model | External dialectical verdicts can label activations from a different small Hugging Face model |

The CLI exposes these choices in [`src/shadowseed/cli.py`](src/shadowseed/cli.py):

```text
shadowseed run-activation-probe
  --read-location neuron
  --sparse-permutations 500
  --model-revision <immutable revision>
  --require-verdict-coverage
```

The method is guarded by [`tests/test_activation_probe.py`](tests/test_activation_probe.py). Tests cover planted sparse dimensions, random-noise controls, permutation floors, deterministic fitting, focused pooling, external verdict coverage, and the explicit rule that the probe may not import `SSLManager` or call the Validation Gate.

### Exact difference from the H-Neurons paper

Shadowseed Pro does not reproduce the H-Neurons claim.

- Gao et al. study hallucination-associated neurons in models represented in their public examples at roughly 24B, 27B, and 70B parameters.
- Shadowseed's experiment studies dialectical verdict separation in models up to 0.5B parameters.
- H-Neurons predicts hallucination occurrence. Shadowseed probes whether candidate-gap verdict classes are linearly decodable.
- H-Neurons includes causal interventions. Shadowseed's probe is observational and never changes generation or seed state.
- A `candidate_neuron` in a Shadowseed artifact is a sparse classifier feature, not a proven H-Neuron.

## Role 2: a separate bounded research track

The repository also contains a small, separate H-Neurons-style investigation under the Layer G research track.

Key artifacts:

- [`round_032/RESULTS.md`](benchmarks/open_review/rounds/round_032/RESULTS.md)
- [`round_033/RESULTS.md`](benchmarks/open_review/rounds/round_033/RESULTS.md)
- [`docs/research/h-neurons-conclusion.md`](docs/research/h-neurons-conclusion.md)
- historical workflow provenance: [`archive/source-workflows/activation-probe-real-verdict.yml`](archive/source-workflows/activation-probe-real-verdict.yml)

### What was tested

The track used:

- a multilingual Qwen2.5 0.5B model;
- neuron-level `down_proj` input activations;
- externally generated dialectical verdict labels;
- centroid separation;
- sparse L1 logistic regression;
- leave-one-out cross-validation;
- label-shuffle permutation controls;
- multiple-comparison correction;
- a preregistered replication on a new case set;
- pinned numerical dependencies for repeatability.

### What was found

Round 032 produced a tempting candidate signal, but it did not pass the corrected significance threshold. Round 033 tested fixed layers and detectors on a new case set. None of the four preregistered tests passed, and the sparse classifier returned to chance-level performance on the preregistered layers.

The defensible conclusion is a bounded null result:

- no reproducible linearly decodable dialectical-verdict signal was established in the evaluated models up to 0.5B parameters;
- the result does not exclude nonlinear representations, other activation sites, different tasks, larger datasets, or larger models;
- the result does not weaken the external runtime mechanics in layers A-F;
- the runtime must not depend on the tested internal signal.

### How the result changed the architecture

The experiment supports a conservative boundary already enforced in code:

```text
internal signal != evidence != verdict != permission to influence
```

The production-facing path remains external and auditable:

1. store the seed weightless;
2. require recurrence and verified evidence;
3. test contradiction;
4. log the Validation Gate decision;
5. recheck promotion at the point of use;
6. record every attempted influence.

This is why the activation probe is located in the benchmark package and is forbidden from touching seed state.

---

# Scientific basis and exact claim boundaries

Shadow Seed Learning is a research architecture, not a direct implementation of one paper. The literature below supports specific design choices or supplies relevant counter-evidence. The final column states what the repository does **not** claim.

| Research | Finding relevant to this repository | Where it appears in code | Boundary |
|---|---|---|---|
| Fu et al. (2025), **AbsenceBench** | Models can retrieve present information while struggling to identify information that is missing | Candidate-gap detection, atomic normalization, and gap benchmarks under [`src/shadowseed/detection/`](src/shadowseed/detection/) and [`src/shadowseed/benchmark/`](src/shadowseed/benchmark/) | Does not validate Shadowseed's detector, lifecycle, or answer benefit |
| Li, Kim, and Wang (2025), **QuestBench** | Models can struggle to identify the minimal question needed to resolve underspecified reasoning | Atomic seed rules and optional Socratic-style follow-up behavior | Shadowseed does not guarantee that a generated seed is the minimal or best clarification question |
| Gao et al. (2025), **H-Neurons** | Sparse FFN activations can carry predictive hallucination signals; sparse classifiers and the down-projection input are useful research instruments | [`activation_probe.py`](src/shadowseed/benchmark/activation_probe.py), `read_location="neuron"`, sparse L1 probe | Shadowseed does not claim to have found H-Neurons or to reproduce results from 24B-70B models |
| Vaddi & Vaddi (2026), **Do Hallucination Neurons Generalize?** | A recent preprint reports a large drop from within-domain to cross-domain transfer across 3B-8B models | Domain-specific evaluation, transfer case sets, and refusal to treat one internal signal as universal | This is a preprint, and it does not establish that all neuron signals fail to transfer |
| Alansari et al. (2026), **CrossHallu** | Another recent preprint finds that transfer can occur for many models, while depending on model, language alignment, and dataset | The README and research status treat generalization as an empirical question, not a settled property | The emerging literature is mixed; Shadowseed makes no universal cross-domain or cross-lingual claim |
| Wu et al. (2025), **LongMemEval** | Long-term memory needs separate tests for information extraction, multi-session reasoning, temporal reasoning, knowledge updates, and abstention | Explicit seed lifecycle, TTL, TrTL, expiry, baseline isolation, and audit logs | Shadowseed does not yet provide durable production memory or validated multi-user long-term memory |
| Farquhar et al. (2024), **Semantic entropy** | Uncertainty over meanings can detect a class of confabulations and support selective handling | Candidate gaps are stored as uncertain, powerless signals until checked | Shadowseed does not implement semantic entropy and does not equate a gap signal with hallucination probability |
| Kirichenko et al. (2025), **AbstentionBench** | Models may fail to abstain reliably when questions are unanswerable | Weightless storage, Gate blocking, and explicit `ONBESLIST` handling in dialectical review | Shadowseed has not established calibrated abstention or selective prediction |
| Dhuliawala et al. (2024), **Chain-of-Verification** | Separating initial generation from independent verification can reduce hallucinations | Baseline isolation, external SSOT evidence, Validation Gate, and dialectical falsification | Shadowseed is not a Chain-of-Verification reproduction and verification can still be wrong |
| Fatahi Bayat et al. (2025), **FactBench / VERIFY** | Factuality evaluation benefits from separating supported, unsupported, and undecidable cases | Verified versus proposed SSOT chunks and explicit contradiction or neutral verdicts | Shadowseed has not established comparable evaluator accuracy or coverage |
| Jeong et al. (2024), **Adaptive-RAG** | Retrieval can be selected according to estimated need rather than applied uniformly | Optional seed-triggered retrieval probes and point-of-use surfacing | Shadowseed does not contain a trained complexity router |
| Yao et al. (2025), **SeaKR** | Internal self-aware uncertainty can trigger adaptive retrieval in a trained research system | Promoted seeds can drive optional retrieval probes and are filtered by relevance at use time | Shadowseed does not use its failed activation probe as a runtime retrieval trigger |
| Asai et al. (2024), **Self-RAG** | Retrieval can be selective and paired with explicit critique rather than invoked indiscriminately | Shared surfacing policy, optional retrieval probes, and dialectical review | Shadowseed is not trained with reflection tokens and is not a Self-RAG reproduction |
| Soudani et al. (2025), **Uncertainty estimation in RAG** | Existing uncertainty estimators do not fully satisfy proposed correctness axioms in RAG | Uncertainty remains separate from verified evidence, contradiction, and gate permission | The Gate is an inspectable policy mechanism, not proof that response correctness is calibrated |
| Ge et al. (2025), **Conflicting evidence in RAG fact-checking** | Conflicting evidence and source credibility can materially reduce RAG reliability | Separate SSOT store, trust status, verified proposals, contradiction handling | Shadowseed does not yet implement a complete source-credibility model or source-ranking science |
| Zou et al. (2025), **PoisonedRAG** | A small number of malicious documents can corrupt retrieval-augmented generation | Separation of uncertain seeds, verified evidence, contradiction checks, and production-gap warnings | Current controls are not a demonstrated defense against retrieval poisoning |
| Debenedetti et al. (2024), **AgentDojo** | Agents can be hijacked through untrusted tool or retrieved content | Point-of-use [`AgentSafetyContract`](src/shadowseed_agent/agent_contract.py), audit policy, and explicit high-impact restrictions | Shadowseed has not completed an AgentDojo-style prompt-injection evaluation |

## Design rationale

### Atomic seeds

AbsenceBench and QuestBench support treating missing information as a distinct and difficult target. SSL narrows that target to one candidate at a time so it can be accepted, rejected, or qualified.

### Weightless storage

A detector can be useful without being trustworthy. Weightless storage preserves a lead without allowing it to alter an answer.

### Separate proposals and evidence

FactBench, conflicting-evidence research, PoisonedRAG, and AgentDojo show why generated or retrieved text cannot be treated as automatically trustworthy.

### Independent verification and falsification

Chain-of-Verification supports separating generation from verification. SSL adds a dialectical route that tries to show a candidate is redundant, already covered, unsupported, or contradicted.

### Selective retrieval

Adaptive-RAG, Self-RAG, and SeaKR support the broader principle that retrieval should be selective. SSL applies selection to promoted candidate absences at the moment of use.

### Explicit memory lifecycle

LongMemEval shows that memory quality is not one score. SSL makes persistence, reactivation, decay, and expiry visible, but it does not yet provide durable multi-user memory.

## Scientific position of the repository

The code follows five research-facing principles:

1. **Treat uncertainty as a reason to inspect, not a reason to believe.** A candidate absence may be useful even when it is wrong. The safe first operation is to preserve it without influence.
2. **Separate model-generated proposals from trusted evidence.** Generated text can suggest what to investigate. It cannot verify itself.
3. **Make falsification a first-class operation.** A candidate should face an active attempt to show that it is redundant, already covered, unsupported, or contradicted.
4. **Require selection at the moment of use.** Even a promoted seed may be irrelevant to the current question. Surfacing is based on current semantic fit, conversation timing, top-k limits, and resurface damping.
5. **Prefer bounded null results over attractive overclaims.** The H-Neurons-style track retained its negative replication and used it to tighten the runtime claim boundary.

## Older conceptual antecedents

The mechanism also relates to older work on epistemic uncertainty, active learning, and computational curiosity. Those lines help explain why an uncertain region may be worth probing. They do not by themselves validate this implementation.

---

# Discussion and limitations

## Conceptual limits

### Meaningful absence is not fully defined

A missing point may be essential, useful but optional, already implied, outside scope, unknowable from the evidence, or invented by the detector. Atomicity makes a candidate testable. It does not make it important.

### Recurrence is not truth

A seed can recur because it matters. It can also recur because the detector repeats the same bias. The Gate therefore keeps recurrence separate from verified evidence.

### Weight is not probability

`weight` is steering authority. It is not the probability that a seed is true, useful, complete, or safe.

### Promotion is not relevance

A valid seed may still distract from the current question. Thresholds and top-k limits reduce this risk but do not solve it.

## Method limits

- fixtures verify mechanics, not real-model quality;
- benchmark suites can encode repository assumptions;
- some verdict labels are model-generated;
- human review sets are still small;
- the author designed both the mechanism and much of the evaluation;
- broad independent replication is missing;
- results may change by model, prompt, language, domain, and backend;
- the activation study has limited sample size and model scale.

The null H-Neurons-style result is valid for the tested setup. It does not rule out other scales or methods.

## Author and development limits

The author is not a formally trained programmer. AI-assisted development introduces risks:

- generated code may look convincing while hiding flaws;
- repeated AI review can share blind spots;
- tests may encode the same assumptions as the implementation;
- documentation may look more mature than the runtime;
- abstractions may reflect the prompts used to create them.

The repository reduces these risks through explicit authority rules, tests, public artifacts, negative-result retention, and claim limits. These controls do not replace expert review.

## Engineering limits

Production use still requires:

- durable transactional storage and migrations;
- deterministic replay across versions;
- multi-user authorization and isolation;
- privacy, retention, deletion, and export controls;
- prompt-injection and evidence-poisoning defenses;
- seed-spam controls and rate limits;
- monitoring, rollback, and failure recovery;
- operator approval for high-impact actions;
- independent security, software, and statistical review;
- real-world latency, cost, and load testing.

## Design tensions

| Tension | Current choice | Open question |
|---|---|---|
| Memory versus contamination | Weightless seeds and baseline isolation | What useful context is lost? |
| Persistence versus forgetting | TTL, TrTL, and expiry | How should decay vary by domain and risk? |
| Exploration versus distraction | Relevance thresholds and top-k | Can usefulness be predicted before generation? |
| Recurrence versus bias | Recurrence supports but cannot complete the Gate | How should correlated detector errors be measured? |
| Verification versus verifier error | Evidence and dialectical review | How should malicious or conflicting verifiers be handled? |
| Transparency versus overload | Full logs and authority maps | Can people review the trail efficiently? |
| Memory utility versus privacy | Explicit seed and evidence text | What is the minimum safe retained data? |

## Open research questions

- Can independent reviewers agree on atomic, meaningful absences?
- Does seed quality transfer across languages and professions?
- Can promoted seeds improve answers without narrowing the question?
- What is the best negative control for a plausible but unnecessary seed?
- How should source credibility and conflicting evidence enter the Gate?
- Can Gate thresholds be tied to real decision costs?
- Can a memory system remain auditable while retaining less sensitive text?
- Do larger models contain a replicable signal related to candidate absence?
- Can external teams reproduce the behavioral results?

## Appropriate use today

Suitable uses include research inspection, mechanism testing, benchmark development, controlled local experiments, and discussion of auditable agent memory.

Do not treat Shadowseed Pro as a ready safety layer for healthcare, education decisions, employment, finance, law, public administration, or autonomous high-impact action.

---

# Quick start

## Requirements

- Python 3.10 or newer
- Git
- optional local or hosted model access for non-fixture runs

## Install and test

```bash
git clone https://github.com/E-AI-MODEL/shadowseed-pro.git
cd shadowseed-pro
python -m pip install --upgrade pip
pip install -e ".[test]"
python -m pytest -q
python -m ruff check .
```

## Run the deterministic chat demo

```bash
shadowseed chat --backend fixture --show-shadow
```

The fixture backend checks pipeline mechanics. It is not evidence of real-model quality.

## Run the main regression and benchmark commands

```bash
shadowseed run-gap-suite
shadowseed run-false-positive-suite
shadowseed run-benefit-suite
shadowseed run-model-benefit-suite --backend fixture
shadowseed run-adversarial-gate-benchmark
shadowseed run-probe-utility-benchmark
shadowseed run-probe-feedback-behavior-suite
shadowseed analyze-results
```

## Optional dependencies

```bash
pip install -e ".[models]"          # Hugging Face, Sentence Transformers, Torch
pip install -e ".[openai]"          # hosted OpenAI adapter
pip install -e ".[vector]"          # FAISS and Chroma
pip install -e ".[paper]"           # PDF paper pipeline
pip install -e ".[dev]"             # all development extras
```

API keys must be supplied through environment variables. Never commit keys to source, fixture files, or workflow inputs.

---

# Activation-probe commands

## Mechanics-only smoke run

```bash
shadowseed run-activation-probe \
  --backend fake \
  --input src/shadowseed/data/dialectic_falsification_fixture.json \
  --read-location neuron \
  --sparse-permutations 99 \
  --output results/activation_probe_fake.json
```

This run verifies the hooks-to-vectors-to-statistics pipeline. The fake backend contains no neural signal and supplies no scientific evidence about model internals.

## Real Hugging Face probe

```bash
pip install -e ".[test,models]"

shadowseed run-activation-probe \
  --backend hf \
  --model-id Qwen/Qwen2.5-0.5B \
  --input src/shadowseed/data/dialectic_falsification_transfer_v3.json \
  --verdicts benchmarks/open_review/rounds/round_033/verdicts_run_29490380118.json \
  --pooling statement \
  --read-location neuron \
  --sparse-permutations 500 \
  --model-revision <immutable-hugging-face-commit-sha> \
  --require-verdict-coverage \
  --dtype float32 \
  --output results/activation_probe.json
```

A real probe can require substantial memory and time. Reproducible comparison requires a fixed model revision, fixed dependencies, fixed labels, fixed case data, and an analysis plan written before looking at the strongest layer.

## Generate fresh external dialectical labels

```bash
shadowseed run-dialectic-falsification \
  --backend openai \
  --model-id <model-id> \
  --input src/shadowseed/data/dialectic_falsification_transfer_v3.json \
  --output results/dialectic_verdicts.json
```

Then pass `results/dialectic_verdicts.json` to `run-activation-probe --verdicts`.

Fresh model labels are not bit-reproducible by default. Preserve the verdict artifact and record the model identifier and date.

---

# Architecture

## Runtime modules

| Module | Responsibility |
|---|---|
| [`shadowseed.manager`](src/shadowseed/manager.py) | Seed model, trace/weight separation, lifecycle, TTL, TrTL, Validation Gate, contradiction, feedback logs |
| [`shadowseed.seed_normalization`](src/shadowseed/seed_normalization.py) | Candidate cleanup and atomic splitting |
| [`shadowseed.surfacing`](src/shadowseed/surfacing.py) | Shared relevance thresholds, early-turn discipline, top-k selection, resurface damping |
| [`shadowseed.chat`](src/shadowseed/chat.py) | Live sidecar session, baseline isolation, recurrence, point-of-use filtering, audit trail |
| [`shadowseed.detection`](src/shadowseed/detection/) | Open-set and model-backed candidate generation |
| [`shadowseed.adapters`](src/shadowseed/adapters/) | Model, embedding, Ollama, and OpenAI adapters |
| [`shadowseed.ssot`](src/shadowseed/ssot.py) | Trusted evidence store and explicit verification boundary |
| [`shadowseed.retrieval_probe`](src/shadowseed/retrieval_probe.py) | Seed-based retrieval probes that report presence without declaring truth |
| [`shadowseed.recurrence_clustering`](src/shadowseed/recurrence_clustering.py) | Paraphrase-aware recurrence clustering |
| [`shadowseed.vectorstore`](src/shadowseed/vectorstore/) | Memory, FAISS, and Chroma storage adapters |
| [`shadowseed_agent.agent_contract`](src/shadowseed_agent/agent_contract.py) | Zero-trust influence decision at the agent boundary |
| [`shadowseed_agent.audit_policy`](src/shadowseed_agent/audit_policy.py) | Replay checks for weightless or otherwise forbidden influence |

## Evaluation and research modules

| Module | Responsibility |
|---|---|
| [`shadowseed.benchmark.activation_probe`](src/shadowseed/benchmark/activation_probe.py) | H-Neurons-style activation extraction and sparse statistical probe |
| [`shadowseed.benchmark.dialectic_falsification`](src/shadowseed/benchmark/dialectic_falsification.py) | Active attempt to refute promoted candidates against source text |
| [`shadowseed.benchmark.adversarial_gate_benchmark`](src/shadowseed/benchmark/adversarial_gate_benchmark.py) | Comparison of the current Gate with weaker promotion rules |
| [`shadowseed.benchmark.ssl_session_suite`](src/shadowseed/benchmark/ssl_session_suite.py) | Multi-turn runtime evaluation through the real manager and Gate |
| [`shadowseed.benchmark.ssl_vs_rag_benchmark`](src/shadowseed/benchmark/ssl_vs_rag_benchmark.py) | Gap-query retrieval probe versus ordinary question-query RAG |
| [`shadowseed.analysis`](src/shadowseed/analysis/) | Result analysis and canonical artifact precedence |

---

# Repository map

```text
shadowseed-pro/
├── README.md                       repository front page
├── pyproject.toml                  packaging and tool configuration
├── repository-authority.yaml       machine-readable authority map
├── src/
│   ├── shadowseed/                 canonical runtime package
│   │   ├── adapters/               model and service adapters
│   │   ├── analysis/               result analysis
│   │   ├── benchmark/              evaluation and research implementations
│   │   ├── data/                   packaged fixtures and curated inputs
│   │   ├── detection/              candidate detectors
│   │   └── vectorstore/            memory, FAISS, and Chroma backends
│   └── shadowseed_agent/           point-of-use contract and audit policy
├── tests/                           contract, unit, integration, and regression tests
├── benchmarks/                      benchmark definitions and reviewed rounds
│   ├── open_review/rounds/          committed research and review artifacts
│   └── results/                     generated benchmark snapshots
├── docs/
│   ├── architecture/               canonical architecture specification
│   ├── research/                   current research conclusions and limits
│   ├── usage/                      current usage documentation
│   └── migration/                  rebuild and provenance records
├── data/                            source papers and evidence material, not packaged
├── experiments/                     exploratory runners, not supported runtime
├── scripts/                         research and review utilities
├── results/                         local and generated analysis output
└── archive/                         frozen historical source material
```

---

# Repository authority

The repository distinguishes implementation, evidence, compatibility, and history. The machine-readable source is [`repository-authority.yaml`](repository-authority.yaml). The narrative guide is [`docs/architecture/repository-structure.md`](docs/architecture/repository-structure.md).

| Authority class | Meaning |
|---|---|
| `CANONICAL_SPEC` | Current architecture, packaging, or repository rules |
| `RUNTIME_IMPLEMENTATION` | Code shipped in the installed package |
| `CONTRACT_TEST` | Tests that pin runtime or compatibility behavior |
| `EVALUATION_IMPLEMENTATION` | Benchmarks, research instruments, and evaluation utilities |
| `EVIDENCE_ARTIFACT` | Curated or generated result material |
| `COMPATIBILITY_ONLY` | Legacy import facade with no independent logic |
| `HISTORICAL_REFERENCE` | Superseded material kept for provenance |
| `ARCHIVE` | Frozen source material excluded from the package |

Rules for reading the repository:

- canonical runtime lives under `src/shadowseed/` and `src/shadowseed_agent/`;
- tests are evidence that a behavior is checked, not proof of real-world performance;
- a benchmark runner proves the evaluation route exists, not that a positive result was obtained;
- result artifacts must be read with their case set, backend, labels, thresholds, and review method;
- archive material may explain project history but cannot override current code or architecture docs;
- fixture outputs demonstrate harness behavior only.

---

# Evidence hierarchy

Use this order when checking a repository claim:

1. **Runtime code**: the behavior is implemented.
2. **Contract and regression tests**: the behavior is exercised and pinned.
3. **Benchmark implementation**: a controlled evaluation route exists.
4. **CI or recorded execution**: the route ran in a stated environment.
5. **Result artifact**: outcomes are available with inputs and settings.
6. **Independent or human review**: judgments were checked outside the generating path.
7. **Replication or transfer**: the result survives new data, domains, models, or reviewers.
8. **Documentation claim**: a statement explains the system but is not evidence by itself.

A strong README claim should point downward through this stack, not stop at prose.

## Fixture versus real-model evidence

| Evidence type | What it can show | What it cannot show |
|---|---|---|
| deterministic fixture | command wiring, schemas, state transitions, logging, failure handling | real detector quality or answer benefit |
| synthetic planted signal | whether a statistical instrument can recover a known feature | whether the feature exists in a real model |
| one real-model run | behavior on that model, case set, prompt, and environment | generalization |
| reviewed benchmark | performance under a stated review protocol | production safety |
| preregistered replication | whether a fixed claim survives a new sample | universal validity |

---

# Research status

## Implemented and testable

- atomic seed intake and normalization;
- separate trace and weight state;
- weightless-by-default candidates;
- TTL decay, dormancy, TrTL reactivation, and terminal expiry;
- Validation Gate decisions with recurrence, evidence, and contradiction flags;
- bounded probe feedback and demotion;
- external SSOT evidence separated from generated proposals;
- shared live-chat and benchmark surfacing policy;
- point-of-use AgentSafetyContract;
- baseline isolation in the live chat;
- retrieval probes and vector-store adapters;
- audit logs for seed, gate, feedback, and influence events;
- deterministic fixtures plus optional Hugging Face, Ollama, OpenAI, FAISS, and Chroma routes;
- H-Neurons-style activation-probe instrument with permutation controls;
- committed null-result and replication artifacts for the small-model activation track.

## Not established

- general answer-quality improvement across open-ended tasks;
- a universal definition or detector for meaningful absence;
- a general internal neural representation of missing context;
- cross-domain or cross-lingual generalization of seed quality;
- reliable value from every promoted seed;
- calibration between seed weight and factual correctness;
- safety against all prompt-injection, evidence-poisoning, or seed-spam attacks;
- production readiness.

## Work still required for production use

- durable seed, evidence, gate, and influence storage;
- schema migrations and deterministic replay across versions;
- versioned SSOT policies and source-governance rules;
- privacy, retention, deletion, and access controls for seed and evidence text;
- monitoring for false promotion, stale seeds, contradiction rates, and surfacing drift;
- rate limits and adversarial seed-spam controls;
- rollback for promoted influence;
- explicit operator approval for high-impact actions;
- failure isolation for model, embedding, vector-store, and retrieval backends;
- real-world evaluations with independent review;
- a formal decision about future licensing.

---

# Reproducibility rules

Research runs should record:

- repository commit;
- Python and operating-system version;
- package versions, especially NumPy, Torch, and Transformers;
- model ID and immutable model revision;
- dtype and device;
- input case file and its hash;
- prompt variant and pooling location;
- external verdict artifact and coverage;
- random seeds;
- number of permutations;
- multiple-comparison correction;
- preregistered layers or hypotheses;
- output artifact hash.

Do not select the strongest layer and then present its uncorrected p-value as confirmation. Discovery and confirmation require separate data or a preregistered test.

---

# Documentation

- [Architecture overview](docs/architecture/overview.md)
- [Lifecycle and Validation Gate](docs/architecture/lifecycle-and-gate.md)
- [Repository structure](docs/architecture/repository-structure.md)
- [Compatibility policy](docs/architecture/compatibility-policy.md)
- [CLI usage](docs/usage/cli.md)
- [Research status](docs/research/status.md)
- [H-Neurons conclusion](docs/research/h-neurons-conclusion.md)
- [Migration audit](docs/migration/source-audit.md)
- [Reuse decisions](docs/migration/reuse-decisions.md)
- [Authority map](repository-authority.yaml)

---

# References

## Missing information and memory

- Fu et al. (2025). **Absence Bench: Language Models Can't See What's Missing.** *NeurIPS 2025*. [Paper](https://papers.neurips.cc/paper_files/paper/2025/hash/36b31e1bb8ecd4f4081686448e9eff2d-Abstract-Datasets_and_Benchmarks_Track.html).
- Li, Kim, and Wang (2025). **QuestBench.** [arXiv:2503.22674](https://arxiv.org/abs/2503.22674).
- Kirichenko et al. (2025). **AbstentionBench.** [arXiv:2506.09038](https://arxiv.org/abs/2506.09038).
- Wu et al. (2025). **LongMemEval.** *ICLR 2025*. [Proceedings](https://proceedings.iclr.cc/paper_files/paper/2025/hash/d813d324dbf0598bbdc9c8e79740ed01-Abstract-Conference.html).

## Verification, retrieval, and security

- Dhuliawala et al. (2024). **Chain-of-Verification.** *Findings of ACL 2024*. [Paper](https://aclanthology.org/2024.findings-acl.212/).
- Fatahi Bayat et al. (2025). **FactBench.** *ACL 2025*. [Paper](https://aclanthology.org/2025.acl-long.1587/).
- Jeong et al. (2024). **Adaptive-RAG.** *NAACL 2024*. [Paper](https://aclanthology.org/2024.naacl-long.389/).
- Asai et al. (2024). **Self-RAG.** *ICLR 2024*. [OpenReview](https://openreview.net/forum?id=hSyW5go0v8).
- Yao et al. (2025). **SeaKR.** *ACL 2025*. [Paper](https://aclanthology.org/2025.acl-long.1312/).
- Soudani et al. (2025). **Why Uncertainty Estimation Methods Fall Short in RAG.** *Findings of ACL 2025*. [Paper](https://aclanthology.org/2025.findings-acl.852/).
- Ge et al. (2025). **Resolving Conflicting Evidence in Automated Fact-Checking.** *IJCAI 2025*. [Paper](https://www.ijcai.org/proceedings/2025/1073).
- Zou et al. (2025). **PoisonedRAG.** *USENIX Security 2025*. [Paper](https://www.usenix.org/conference/usenixsecurity25/presentation/zou-poisonedrag).
- Debenedetti et al. (2024). **AgentDojo.** *NeurIPS 2024*. [Paper](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html).
- Farquhar et al. (2024). **Detecting Hallucinations Using Semantic Entropy.** *Nature*. [DOI](https://doi.org/10.1038/s41586-024-07421-0).

## H-Neurons and internal representations

- Gao et al. (2025). **H-Neurons.** [arXiv:2512.01797](https://arxiv.org/abs/2512.01797). [Official implementation](https://github.com/thunlp/H-Neurons).
- Vaddi and Vaddi (2026). **Do Hallucination Neurons Generalize?** [arXiv:2604.19765](https://arxiv.org/abs/2604.19765).
- Alansari et al. (2026). **CrossHallu.** [arXiv:2607.04029](https://arxiv.org/abs/2607.04029).

## Conceptual antecedents

- Kendall, A., & Gal, Y. (2017). **What Uncertainties Do We Need in Bayesian Deep Learning for Computer Vision?** *NeurIPS 2017*.
- Schmidhuber, J. (2010). **Formal Theory of Creativity, Fun, and Intrinsic Motivation.** *IEEE Transactions on Autonomous Mental Development, 2*(3), 230-247.
- Settles, B. (2009). **Active Learning Literature Survey.** University of Wisconsin-Madison.

These references provide problems, methods, counter-evidence, and precedents. They do not collectively prove Shadow Seed Learning.

---

# Rights and temporary licensing position

**Copyright © 2026 H. Visser / E-AI-MODEL. All rights reserved.**

This repository intentionally has no open-source license at present. No general permission is granted to use, copy, modify, redistribute, publish, commercialize, or incorporate the original repository content into another product or service.

Public access is provided for inspection, research discussion, and evaluation. Reuse requires prior written permission from the copyright holder, except where applicable law, GitHub's Terms of Service, or a separate written agreement provides otherwise.

Third-party libraries, papers, datasets, model weights, quoted material, and archived external artifacts remain subject to their own rights and terms.

This is a temporary rights reservation. A later repository update may adopt a different license. Until then, no implied open-source license is granted.

For a legally binding licensing arrangement or commercial use, contact the repository owner and obtain professional legal advice.
