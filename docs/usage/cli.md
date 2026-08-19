# CLI Usage

Install the package in editable mode before running commands from another working directory:

```bash
pip install -e ".[test]"
```

## Live chat

`shadowseed chat` and `ShadowChatSession` default to the product-oriented `live`
runtime:

```bash
shadowseed chat --backend fixture
```

The fixture backend is deterministic and is intended for mechanics and smoke tests. In
`live` mode Shadowseed selects already-authorized seeds before generation, performs one
model generation per turn, stores the same visible answer in conversation history, and
detects new candidate gaps on that visible answer. When a seed surfaced, every candidate
detected in that same answer is deferred. This conservative rule is intentional: vector
similarity can recognize paraphrases but cannot prove that a differently worded candidate
was not caused by the supplied SSL context.

The `live` runtime defaults to the `evidence_backed` Gate policy. Recurrence remains an
observation but cannot by itself increase steering authority. Use `--gate-policy` only
when a different policy is a deliberate experiment.

Inspect the live shadow and submit verified operator support with stable provenance:

```text
/shadow
/support <seed_id> <source_ref>
```

Each distinct source reference is offered as one verified `human_feedback` signal through
the normal Validation Gate. Reusing the same underlying source reference does not create
additional authority credit, even if it is later presented through another external
signal channel. Generated model text, anonymous support, recurrence, and unverified
observations are rejected by the `ShadowChatSession.submit_evidence(...)` boundary. The
command is an explicit trust action, not an automatic conversion of chat output into
evidence.

The boundary validates the signal kind, support direction, `verified` marker, and stable
provenance. It cannot establish that a source is authentic or correct. The operator behind
`/support`, or the host application calling `submit_evidence`, is the trust anchor and must
perform that verification before setting `verified=True`. Integrations must not hard-code
that flag or derive it from model output, recurrence, or an untrusted retrieval result.

For a local model with semantic embeddings:

```bash
pip install -e ".[models]"
shadowseed chat \
  --backend ollama \
  --model-id <model> \
  --embedding-backend sentence-transformers
```

For a hosted model and hosted embeddings:

```bash
pip install -e ".[openai]"
shadowseed chat \
  --backend openai \
  --model-id <model> \
  --embedding-backend openai
```

Live non-fixture sessions reject the deterministic `lexical` hash embedder because it is
a CI/demo scaffold, not a production semantic retriever. `--allow-toy-embedder` exists
only as an explicit escape hatch for controlled experiments. The fixture backend retains
the lexical default so its offline mechanics tests stay deterministic; `shadowseed doctor`
reports this product limitation explicitly.

Surfacing controls:

```bash
shadowseed chat \
  --surface-threshold 0.55 \
  --surface-top-k 3 \
  --early-turn-margin 0.10 \
  --early-turn-history 5 \
  --resurface-margin 0.15
```

`early-turn-margin` raises the relevance threshold during the first turns. `resurface-margin` temporarily raises the threshold for a seed that recently influenced an answer and halves that extra margin after each turn.

### Evaluation mode

The historical research loop remains available explicitly:

```bash
shadowseed chat --backend fixture --runtime-mode evaluation
```

`evaluation` preserves the isolated baseline arm used for controlled comparisons: the
baseline is kept separate from a possible SSL-assisted visible answer. Use this mode for
research A/B work and benchmark reproducibility, not as the default conversational
product path.

## Core benchmark commands

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

`run-ssl-session` no longer accepts question-only session suites with the fixture backend.
Fixture session turns must contain an authored `baseline_answer`; otherwise the command
fails closed instead of producing a successful but behaviorally empty run. Use a real
model backend for question-only session suites.

The command defaults to the historical `evaluation` benchmark. To measure the actual
one-generation live runtime with a local model:

```bash
pip install -e ".[models]"
shadowseed run-ssl-session \
  --runtime-mode live \
  --live-arms both \
  --backend ollama \
  --model-id <model> \
  --embedding-backend sentence-transformers \
  --output results/ssl_live_session.json
```

Live measurement rejects the fixture backend and lexical hash embeddings and requires an
English input suite declaring `"language": "en"`. Live answers are explicitly requested
in English. It constructs fresh `ShadowChatSession` state for every conversation while
reusing the loaded model, detector, and semantic embedder. The default `both` setting runs
two clearly separated arms:

- `evidence-backed` is the shipped policy. The runner supplies no external evidence, so
  it measures detection and memory without silently granting authority.
- `counterfactual` uses recurrence-only exploratory authority to make organic surfacing
  possible. It does not guarantee promotion or influence. When no turn is influenced, zero
  suppressed candidates means deferral was not observed, not that it had no cost. This is
  not a production result and is labelled that way in the artifact.

The artifact pins the input digest, package version, Git revision and dirty-worktree state.
It also records answer-generation and detector-call counts, suppressed candidate
occurrences, normalized candidates that pass the atomicity heuristic, and how many return
semantically on a later uninfluenced turn. Recovery is scored only when such a later
observation window exists; otherwise `later_recovery_rate` is `null`, never a synthetic
zero. Timing is split into adapter setup, the live turn-loop, deferral scoring, other arm
overhead, and total measurement wall time. Extra embedding calls made during semantic
recovery scoring therefore never count as live-runtime latency. These are automated
opportunity-cost proxies. They do not establish that a candidate is true, relevant, or
useful, and the counterfactual does not turn recurrence into evidence. Use
`--live-arms evidence-backed` when only the shipped no-evidence behavior is needed and the
second set of model calls is not justified.

The first real-model pipeline run and a separate non-production stress measurement are in
[`benchmarks/results/live_runtime/`](../../benchmarks/results/live_runtime/). The stress run
lowers Gate and surfacing thresholds explicitly to ensure that deferral is exercised; its
authority and influence counts must not be presented as product behavior. The 0.5B run is
diagnostic only; evidence-quality reruns should use a stronger instruction model with stable
English instruction following.

## Optional backends

Real-model and vector commands require their matching extras and local credentials or services. API keys must be supplied through environment variables, never source files or workflow inputs.

## Tester workspace foundation

```bash
shadowseed doctor
shadowseed init
shadowseed workspace info
shadowseed workspace backup
```

The default local workspace is `~/.shadowseed`. Use `--workspace PATH` for an isolated
workspace. `workspace delete` requires `--yes`. API keys remain in the process environment
or an OS keyring and are never stored in the workspace.

The ordinary Workbench product creates new sessions in `live` mode with the
`evidence_backed` Gate policy. A live user may request **Compare this message with SSL
off** for a single message. The Workbench generates that control automatically from the
same model configuration and pre-turn visible history, keeps it out of candidate
detection, recurrence, Gate state, and later conversation history, then executes the real
live turn normally.

Historical `evaluation` sessions, authored baseline fixtures, scenario JSON, and blind
research comparison workflows remain available under **Advanced / research**. Persisted
legacy sessions keep their recorded runtime mode; old snapshots without runtime metadata
continue to resolve to `evaluation` for compatibility. Direct `ShadowChatSession()` use
and `shadowseed chat` default to `live`; pass `runtime_mode="evaluation"` explicitly only
for the research comparison runtime.
