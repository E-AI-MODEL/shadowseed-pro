# Gap resilience benchmark

This benchmark evaluates the detector as a **candidate-gap generator**. It does
not evaluate seed authority, Gate promotion, or point-of-use influence, and it
does not change production/runtime behavior.

The suite exists because several current agent-memory projects expose useful
evaluation patterns that are applicable to Shadowseed even though their runtime
architectures and objectives are different.

## Frozen comparison basis

The benchmark design was derived from inspection of these upstream repository
states:

| Source | Inspected ref | What is reused as an evaluation idea |
|---|---|---|
| Shadowseed Pro | `0c0e39d4a8ba51799f417383a25fa906a1f82e61` | Current v0.6 gap semantics and bounded clean context |
| AgentToolkit/altk-evolve | `13e0be72015bc04e4f346a4a3cf6bfbd28f0b774` | Repeated-run consistency and arm-separated measurement |
| hamza-dev-tech/agent-memory-bench | `0d5d225504865e81467b7d8cb4724c15c1f41664` | Shared workload treatment, adversarial/no-answer controls, resumable inspectable records |
| vbcherepanov/total-agent-memory | `db3086e752c5aa15a51e00bb5372429cde9ece2d` | Explicit knowledge-update/currentness traps and separate current-vs-stale measurements |
| datapace-ai/agent-memory-benchmark | `0a994d507d9910993186ab582557e548ed0c0974` | Ability-separated metrics, abstention, stale-rate thinking, fixed-seed reproducibility |

No upstream runtime code is copied into Shadowseed. These repositories are
methodological references only.

## Questions this suite asks

The first version measures four separate properties.

1. **Expected-gap recall**  
   When a reviewer has identified a specific unresolved gap, does at least one
   detector candidate match one of its authored aliases?

2. **Negative-control abstention**  
   When the item is deliberately complete, does the detector return no
   candidate rather than manufacture a gap?

3. **Resolved-gap reopen rate**  
   When bounded prior clean context already establishes a point, does the
   detector incorrectly call that same point missing again? This is the
   Shadowseed analogue of a stale/superseded-memory failure.

4. **Repeatability**  
   Across repeated runs of the same frozen item, how similar are the candidate
   sets? This is reported separately from correctness: consistently wrong is
   still wrong.

There is deliberately **no combined quality score**. A model can improve one
dimension while degrading another, and collapsing them would hide the tradeoff
we are trying to inspect.

## Matching

The benchmark uses an inspectable token-Jaccard matcher against reviewer-authored
alias groups. The default threshold is `0.35`.

That matcher is intentionally modest. It is useful for stable regression
measurement and triage, but it is not a semantic judge and it is not Layer-C
evidence. A live benchmark that will support a research claim still needs
independent review of the actual candidates.

## Case set

`cases.json` contains positive, negative, currentness, other-subject and Dutch
cases. Every case keeps expected unresolved gaps and already-resolved gaps
separate.

The current set is small by design. Version 1 is a harness and falsification
surface, not a representative estimate of open-domain performance.

## Run

Harness smoke test:

```bash
uv run python scripts/run_gap_resilience_benchmark.py \
  --backend fixture \
  --repeats 3 \
  --output results/gap-resilience-fixture.json
```

A fixture run is recorded as `benchmark_smoke`. It proves only that the
benchmark route executes.

Example live Ollama run:

```bash
uv run python scripts/run_gap_resilience_benchmark.py \
  --backend ollama \
  --model-id qwen2.5:7b-instruct-q4_K_M \
  --repeats 5 \
  --output results/gap-resilience-qwen.json
```

A non-fixture run is recorded as `live_benchmark`. The report also records the
backend, model id, model revision where applicable, source ref, case-set version,
repeat count and matching threshold.

## Interpretation

A useful result reports the four measurements side by side and inspects the
per-case candidate text.

- High repeatability with poor gap recall is not success.
- High gap recall with a high resolved-gap reopen rate indicates context/currentness
  problems.
- Low candidate count is not automatically good if positive gaps are missed.
- High candidate count is not automatically good if negative controls fail.
- Retrieval, reranking, recurrence and authority are intentionally outside this
  benchmark.

A later benchmark may add **post-authorization reranking in shadow mode**, but
only over seeds already authorized by the current Gate. Reranking must never
become an authority source.
