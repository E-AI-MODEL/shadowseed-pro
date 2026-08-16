# Architecture Overview

Shadow Seed Learning separates detection, storage, validation, and influence. This prevents a plausible model-generated gap from silently becoming memory or steering.

## Runtime flow

1. A detector proposes a candidate intended to represent one absence; normalization uses tested heuristics and can still produce a compound, vague, or weak candidate.
2. `SSLManager` stores it with trace above zero and weight exactly zero.
3. TTL reduces trace when the seed is not reinforced.
4. TrTL can reactivate a dormant seed through a trigger or semantic match.
5. Evidence and contradiction signals are evaluated by the Validation Gate.
6. Only a promoted seed with a logged gate decision may be considered for influence.
7. The surfacing policy applies relevance, early-turn discipline, top-k selection, and per-seed resurface damping.
8. `AgentSafetyContract` checks the seed again at the point of use.
9. The influence attempt and decision are recorded for replay and audit.

## Authority model

Authority — whether a seed may eventually influence behavior — is governed by one
Gate-controlled decision engine on the supported runtime API. Restoration and
explicitly unsafe test hooks remain outside that new-decision guarantee. The
details live in dedicated documents; in summary:

- **Signals and policies** ([gate-contracts.md](gate-contracts.md)): typed
  `ValidationSignal`s (recurrence, SSOT, human feedback, retrieval, dialectic,
  probe, task outcome, contradiction, resolution) are offered to named policies
  (`exploratory` default, `evidence_backed`). Policies propose; only the Gate
  applies. Recurrence is a first-class signal and is never relabeled as external
  evidence. Verified external support requires a non-empty `source_ref`; repeated
  use of the same source-and-kind pair is idempotent. The same reference under a
  different signal kind is distinct support. Every Gate decision produces an
  immutable `GateEvent`.
- **Encapsulation** ([lifecycle-and-gate.md](lifecycle-and-gate.md)): `weight`,
  `status`, `evidence_count`, `contradiction_score`, and `authority_version` are
  guarded; `SSLManager._set_authority` is the only runtime writer, while Gate
  decisions and mechanical intake/lifecycle transitions remain distinct. The
  seed registry is a read-only view. Deserialization uses `ShadowSeed.from_dict` /
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
| `shadowseed.manager` | `SSLManager` runtime orchestration, configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |
| `shadowseed.models` | Stable seed, lifecycle, validation-result, constellation, and probe data contracts |
| `shadowseed.contradictions` | Contradiction record collection, identifier sequencing, blocking-state derivation, formal lifecycle workflows, and legacy migration |
| `shadowseed.intake` | Embedding acquisition, atomicity heuristics, detector-candidate normalization, deduplication, and seed creation/update |
| `shadowseed.lifecycle` | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |
| `shadowseed.vector_workflows` | Uncertain-region search, external-feedback routing, and in-memory constellation construction |
| `shadowseed.gate` | Typed validation signals, named Gate policies, and immutable Gate events / contradiction records |
| `shadowseed.surfacing` | Shared cross-turn eligibility, thresholds, ranking, and resurface damping |
| `shadowseed.chat` | Dual-mode conversation session: one-generation live runtime and isolated evaluation A/B loop |
| `shadowseed.detection.model_detector` | Model-backed open-set candidate generation |
| `shadowseed.adapters` | Model, embedding, Ollama, and OpenAI runtime adapters |
| `shadowseed.retrieval_probe` | Retrieval probe execution outside the benchmark namespace |
| `shadowseed.recurrence_clustering` | Reusable recurrence clustering logic |
| `shadowseed.ssot` | Trusted external rules and evidence interfaces |
| `shadowseed.vectorstore` | Memory, FAISS, and Chroma storage adapters |
| `shadowseed_agent.agent_contract` | Bounded point-of-use eligibility decision with a mandatory current-version Gate-event link and a configurable contradiction check |
| `shadowseed.benchmark` | Evaluation harnesses, regression suites, and compatibility wrappers |

## Conversation modes

The product-oriented `live` mode selects previously authorized seeds, applies the
point-of-use contract, and performs one model generation. The visible answer is
stored in history and inspected for new candidate gaps. Candidates attributable
to seeds surfaced on the same turn are suppressed before intake, so a seed cannot
immediately earn recurrence credit from text it helped introduce.

The research-oriented `evaluation` mode retains the isolated baseline arm. It
generates and stores an answer without seeds, then optionally generates a separate
SSL-assisted answer for comparison. This isolation prevents gap starvation and
history contamination in controlled A/B measurements. It is not the default CLI
conversation path.

## Shared surfacing implementation

The old repository had separate surfacing implementations in the live chat and the session benchmark. The rebuilt repository uses `shadowseed.surfacing` as the single implementation. Tests call the same runtime functions instead of carrying a third copy.
