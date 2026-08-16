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
the normal Validation Gate. Reusing the same reference is idempotent. Generated model
text, anonymous support, recurrence, and unverified observations are rejected by the
`ShadowChatSession.submit_evidence(...)` boundary. The command is an explicit trust action,
not an automatic conversion of chat output into evidence.

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
reports this production limitation explicitly.

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

Live measurement rejects the fixture backend and lexical hash embeddings. It constructs
fresh `ShadowChatSession` state for every conversation while reusing the loaded model,
detector, and semantic embedder. The default `both` setting runs two clearly separated
arms:

- `evidence-backed` is the shipped policy. The runner supplies no external evidence, so
  it measures detection and memory without silently granting authority.
- `counterfactual` uses recurrence-only exploratory authority solely to create surfacing
  turns on which fail-closed candidate deferral can be measured. It is not a production
  result and is labelled that way in the artifact.

The artifact pins the input digest, package version, Git revision and dirty-worktree state.
It also records answer-generation and detector-call counts, suppressed candidate
occurrences, normalized candidates that pass the atomicity heuristic, and how many return
semantically on a later unsuppressed turn. Timing is split into adapter setup, the live
turn-loop, deferral scoring, other arm overhead, and total measurement wall time. Extra
embedding calls made during semantic recovery scoring therefore never count as live-runtime
latency. These are automated opportunity-cost proxies. They do not establish that a
candidate is true, relevant, or useful, and the counterfactual does not turn recurrence
into evidence. Use `--live-arms evidence-backed` when only the shipped no-evidence behavior
is needed and the second set of model calls is not justified.

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

The tester Workbench stores the selected runtime mode when a session is created
and defaults its form to `evaluation`. Evaluation sessions retain the
isolated baseline/SSL comparison. Live sessions use one visible generation and
offer a separate, operator-attested evidence action; they cannot use the A/B
Compare tab. Direct `ShadowChatSession()` use and `shadowseed chat` default to
`live`; pass `runtime_mode="evaluation"` explicitly for a research comparison
session.
