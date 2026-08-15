# CLI Usage

Install the package in editable mode before running commands from another working directory:

```bash
pip install -e ".[test]"
```

## Live chat

`shadowseed chat` defaults to the product-oriented `live` runtime:

```bash
shadowseed chat --backend fixture
```

The fixture backend is deterministic and is intended for mechanics and smoke tests. In
`live` mode Shadowseed selects already-authorized seeds before generation, performs one
model generation per turn, stores the same visible answer in conversation history, and
detects new candidate gaps on that visible answer. Candidates attributable to seeds that
surfaced on the same turn are suppressed before intake so SSL cannot immediately give
itself recurrence credit.

The `live` runtime defaults to the `evidence_backed` Gate policy. Recurrence remains an
observation but cannot by itself increase steering authority. Use `--gate-policy` only
when a different policy is a deliberate experiment.

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
only as an explicit escape hatch for controlled experiments.

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

## Optional backends

Real-model and vector commands require their matching extras and local credentials or services. API keys must be supplied through environment variables, never source files or workflow inputs.

## Tester workspace foundation

```bash
shadowseed doctor
shadowseed init
shadowseed workspace info
shadowseed workspace backup
```

The default local workspace is `~/.shadowseed`. Use `--workspace PATH` for an
isolated workspace. `workspace delete` requires `--yes`. API keys remain in the
process environment or an OS keyring and are never stored in the workspace.

The current tester Workbench keeps the evaluation-oriented session configuration so its
baseline/SSL comparison tools remain reproducible. The production-oriented `live` path
is available through `ShadowChatSession(runtime_mode="live")` and `shadowseed chat`.