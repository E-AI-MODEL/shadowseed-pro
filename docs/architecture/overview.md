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

## Main modules

| Module | Responsibility |
|---|---|
| `shadowseed.manager` | Seed model, lifecycle, TTL, TrTL, Validation Gate, probe feedback |
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
