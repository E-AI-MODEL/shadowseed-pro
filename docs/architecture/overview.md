# Architecture Overview

Shadow Seed Learning separates detection, storage, validation, and influence. A plausible model-generated gap may be remembered without silently becoming truth or steering authority.

## Runtime flow

1. A detector proposes a candidate intended to represent one bounded epistemic absence or uncertainty. Normalization uses tested heuristics and can still produce a compound, vague, or weak candidate; redundancy and other defects remain possible.
2. `SSLManager` stores the candidate with trace above zero and weight exactly zero.
3. TTL reduces trace when the seed is not reinforced.
4. TrTL can reactivate a dormant seed through a trigger or semantic match.
5. Recurrence, verified external support, and contradictions remain distinct observations.
6. The Validation Gate evaluates typed signals under a named policy and owns Gate-controlled authority changes.
7. Only a promoted seed with positive weight and a current authorizing Gate event can become eligible for influence.
8. The surfacing policy applies contextual relevance, early-turn discipline, top-k selection, and per-seed resurface damping.
9. `AgentSafetyContract` checks the seed again at the point of use.
10. Allowed and denied influence attempts are recorded for replay and audit.

## Authority model

Authority, meaning whether a seed may eventually influence behavior, is governed by one Gate-controlled decision engine on the supported runtime API. Restoration and explicitly unsafe test hooks remain outside that new-decision guarantee.

- **Signals and policies** ([gate-contracts.md](gate-contracts.md)): typed `ValidationSignal`s are offered to named policies. Policies propose; only the Gate applies. Recurrence is never relabeled as external evidence. The live product default is `evidence_backed`; the manager/evaluation default is `exploratory` unless a caller explicitly selects another policy.
- **External evidence identity**: verified support requires stable provenance. The underlying `source_ref` is the authority identity across external signal channels, so relabeling or replaying the same source cannot create extra authority credit. Signal kind remains channel provenance, not an additional independent source.
- **Encapsulation** ([lifecycle-and-gate.md](lifecycle-and-gate.md)): `weight`, `status`, `evidence_count`, `contradiction_score`, and `authority_version` are guarded. `SSLManager._set_authority` is the single runtime writer for authority fields while Gate decisions and mechanical lifecycle transitions remain distinct categories. The seed registry is read-only to callers. Deserialization uses `ShadowSeed.from_dict` and `SSLManager.restore_seed`.
- **Contradictions** ([lifecycle-and-gate.md](lifecycle-and-gate.md)): explicit `ContradictionRecord`s have an `open`/`resolved`/`superseded`/`withdrawn` lifecycle. Open records block influence. Recovery requires a recorded resolution basis and later revalidation; resolution itself does not silently restore authority.
- **Point of use** ([lifecycle-and-gate.md](lifecycle-and-gate.md)): influence requires one atomic `decide_and_record`, linked to an authorizing Gate event for the seed's current `authority_version` and replayable against the point-of-use invariants.
- **Prompt boundary** ([prompt-boundary.md](prompt-boundary.md)): surfaced seeds are structurally quoted as bounded candidate data, not instructions. This reduces ambiguity but is not a universal prompt-injection guarantee.

## Main modules

| Module | Responsibility |
|---|---|
| `shadowseed.manager` | `SSLManager` runtime orchestration, configuration/state registry, audit logs, serialization, guarded authority mutation primitive, and compatibility facades |
| `shadowseed.models` | Stable seed, lifecycle, validation-result, constellation, and probe data contracts |
| `shadowseed.contradictions` | Contradiction records, blocking-state derivation, formal lifecycle workflows, sequencing, and legacy migration |
| `shadowseed.intake` | Embedding acquisition, atomicity heuristics, candidate normalization, deduplication, and seed creation/update |
| `shadowseed.lifecycle` | TTL decay, dormancy, TrTL reactivation, and terminal expiry workflows |
| `shadowseed.vector_workflows` | Uncertain-region search, external-feedback routing, and in-memory constellation construction |
| `shadowseed.gate` | Typed validation signals, named Gate policies, immutable Gate events, and the executable Gate-controlled authority engine |
| `shadowseed.surfacing` | Shared cross-turn eligibility, thresholds, ranking, and resurface damping |
| `shadowseed.chat` | Product-oriented live conversation runtime plus the historical isolated evaluation runtime |
| `shadowseed.detection.model_detector` | Model-backed open-set candidate generation |
| `shadowseed.adapters` | Model, embedding, Ollama, and OpenAI runtime adapters |
| `shadowseed.retrieval_probe` | Retrieval probe execution outside the benchmark namespace |
| `shadowseed.recurrence_clustering` | Observation-scoped semantic recurrence clustering logic |
| `shadowseed.ssot` | Trusted external rules and evidence interfaces |
| `shadowseed.vectorstore` | Memory, FAISS, and Chroma storage adapters |
| `shadowseed.application` | UI-independent tester workflows and workspace/session orchestration |
| `shadowseed.storage` | Local tester persistence, backup/restore, and normalized audit storage without authority decisions |
| `shadowseed.workbench` | Local chat-first tester UI and standalone launcher |
| `shadowseed_agent.agent_contract` | Bounded point-of-use eligibility with a mandatory current-version Gate-event link |
| `shadowseed.benchmark` | Evaluation harnesses, regression suites, and compatibility wrappers |

## Conversation modes and product comparison

The product-oriented `live` mode is the direct-session, CLI, and ordinary Workbench default. It selects previously authorized seeds, applies the point-of-use contract, and performs one visible model generation. That visible answer is stored in history and inspected for new candidate gaps. If any seed influenced generation, every candidate detected in that same answer is deferred before intake. This fail-closed rule is broader than semantic matching because semantic distance cannot prove causal independence.

Verified external support enters live sessions through an explicit evidence API. Support must be externally typed, verified by the caller/operator, and carry a stable source reference. The runtime validates the attestation shape; the operator or host application remains the trust anchor for source authenticity and correctness.

The ordinary Workbench may additionally generate a paired **SSL-off control for one live message**. It uses the same model configuration and pre-turn visible history but supplies no surfaced Shadow Seeds. The control is comparison data only: it does not enter candidate detection, recurrence, the Gate, or later conversation history. The real live turn remains the only state-changing turn. A textual difference may be attributed to SSL only when an authorized seed actually surfaced on the real turn.

The historical `evaluation` runtime retains an isolated baseline arm for controlled benchmark, replay, and research A/B work. It is available under Advanced/research surfaces and is not the preferred ordinary product comparison path. Legacy persisted sessions keep their recorded runtime mode; old records without runtime metadata remain evaluation-compatible rather than being silently reinterpreted as live.

Product chat follows the language of the current user question. Research benchmarks may still pin a language as part of their protocol.

## Shared surfacing and recurrence implementation

The rebuilt repository uses `shadowseed.surfacing` as the single cross-turn surfacing implementation. Runtime and benchmark paths import the same logic rather than carrying separate policy copies.

Semantic cluster membership is not itself recurrence credit. A detector observation context can contribute at most one recurrence credit to a matching semantic cluster; a later independent detector observation may contribute another. Recurrence remains observation, never evidence or authority by itself under the live `evidence_backed` policy.
