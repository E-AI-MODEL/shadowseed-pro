# CLI Usage

Install the package in editable mode before running commands from another working directory:

```bash
pip install -e ".[test]"
```

## Live chat

```bash
shadowseed chat --backend fixture
```

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

## Optional backends

Real-model and vector commands require their matching extras and local credentials or services. API keys must be supplied through environment variables, never source files or workflow inputs.
