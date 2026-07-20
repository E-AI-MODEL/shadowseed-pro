# Architecture Overview

Shadow Seed Learning separates detection, storage, validation, and influence. This prevents a plausible model-generated gap from silently becoming memory or steering.

## Runtime flow

1. A detector proposes an atomic candidate absence.
2. `SSLManager` stores it with trace above zero and weight exactly zero.
3. TTL reduces trace when the seed is not reinforced.
4. TrTL can reactivate a dormant seed through a trigger or semantic match.
5. Evidence and contradiction signals are evaluated by the Validation Gate.
6. Only a promoted seed with a logged gate decision may be considered for influence.
7. The surfacing policy applies relevance, early-turn discipline, top-k selection, and per-seed resurface damping.
8. `AgentSafetyContract` checks the seed again at the point of use.
9. The influence attempt and decision are recorded for replay and audit.

## Authority model

Authority — whether a seed may eventually influence behavior — is governed by a
single non-bypassable Validation Gate. The details live in dedicated documents;
in summary:

- **Signals and policies** ([gate-contracts.md](gate-contracts.md)): typed
  `ValidationSignal`s (recurrence, SSOT, human feedback, retrieval, dialectic,
  probe, task outcome, contradiction, resolution) are offered to named policies
  (`exploratory` default, `evidence_backed`). Policies propose; only the Gate
  applies. Recurrence is a first-class signal and is never relabeled as external
  evidence. Every Gate decision produces an immutable `GateEvent`.
- **Encapsulation** ([lifecycle-and-gate.md](lifecycle-and-gate.md)): `weight`,
  `status`, `evidence_count`, `contradiction_score`, and `authority_version` are
  guarded; the manager's single transition path is the only writer, and the seed
  registry is a read-only view. Deserialization uses `ShadowSeed.from_dict` /
  `SSLManager.restore_seed`.
- **Contradictions** ([lifecycle-and-gate.md](lifecycle-and-gate.md)): explicit
  `ContradictionRecord`s with an `open`/`resolved`/`superseded`/`withdrawn`
  lifecycle. Open records block influence; recovery needs a recorded resolution
  basis, a Gate event, and revalidation.
- **Point of use** ([lifecycle-and-gate.md](lifecycle-and-gate.md)): influence
  requires one atomic `decide_and_record`, linked to the authorizing Gate event
  and the seed's current `authority_version`, and replayable against every
  invariant.
- **Prompt boundary** ([prompt-boundary.md](prompt-boundary.md)): surfaced seeds
  are structurally quoted as bounded candidate data, not instructions.

## Main modules

| Module | Responsibility |
|---|---|
| `shadowseed.manager` | Seed model, encapsulated authority, lifecycle, TTL, TrTL, Validation Gate, contradiction records, probe feedback |
| `shadowseed.gate` | Typed validation signals, named Gate policies, and immutable Gate events / contradiction records |
| `shadowseed.surfacing` | Shared cross-turn eligibility, thresholds, ranking, and resurface damping |
| `shadowseed.chat` | Live sidecar session with uncontaminated baseline history |
| `shadowseed.detection.model_detector` | Model-backed open-set candidate generation |
| `shadowseed.adapters` | Model, embedding, Ollama, and OpenAI runtime adapters |
| `shadowseed.retrieval_probe` | Retrieval probe execution outside the benchmark namespace |
| `shadowseed.recurrence_clustering` | Reusable recurrence clustering logic |
| `shadowseed.ssot` | Trusted external rules and evidence interfaces |
| `shadowseed.vectorstore` | Memory, FAISS, and Chroma storage adapters |
| `shadowseed_agent.agent_contract` | Zero-trust point-of-use influence decision |
| `shadowseed.benchmark` | Evaluation harnesses, regression suites, and compatibility wrappers |

## Baseline isolation

The live session first generates a baseline answer without seeds. Gap detection runs on that baseline, and the baseline is what enters conversation history. The SSL answer is a sidecar output. This avoids two feedback loops:

- gap starvation, where an SSL-improved answer hides the absence that should be detected;
- history contamination, where previous SSL additions become indistinguishable from the model's original context.

## Shared surfacing implementation

The old repository had separate surfacing implementations in the live chat and the session benchmark. The rebuilt repository uses `shadowseed.surfacing` as the single implementation. Tests call the same runtime functions instead of carrying a third copy.
