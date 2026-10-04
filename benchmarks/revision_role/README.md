# Revision-role screen

This benchmark asks a narrow question: can a local model perform Shadowseed's
**same-turn revision** task reliably when the difficult upstream work has
already been done?

The model receives:

- a fixed, human-authored baseline answer;
- the current user question;
- fixed reviewer-supplied candidate perspectives to integrate.

It does **not** generate the baseline, detect gaps, create seeds, evaluate
recurrence, run the Validation Gate, or decide authority. That makes it suitable
for testing whether a smaller local model can earn one conditional model role
without requiring it to perform every Shadowseed task.

## Product fidelity

The benchmark uses the canonical product `minimal_revision` prompt contract
from `shadowseed.surfacing.build_revision_prompt`.

The first screen compares:

- `deepseek-r1:latest`
- `gemma2:latest`

on two fixed cases: one Dutch explanatory answer and one English technical
answer.

The generation budget is the product default of 700 tokens. The benchmark
allows a longer HTTP timeout so it can distinguish:

1. a model that produces a complete final response;
2. a model that would exceed the product's current 120-second provider timeout;
3. a model that consumes its generation budget before reaching a final answer.

Absolute GitHub-runner latency is not a laptop benchmark.

## Measurements

Each case reports separately:

- whether a final response was reached;
- Ollama `done_reason` and token counts;
- expected-point coverage;
- preservation of selected correct baseline content;
- visible contract leakage such as `<think>` or prompt labels;
- whether the call fell inside the current product provider timeout.

A `role_contract_pass` requires a complete final response, full authored-point
coverage, full selected-baseline preservation, and no visible prompt/thinking
leakage. This is a screening contract, not a universal model-quality score.

## Eligibility rule

No model is accepted or rejected because it is below a fixed parameter count.
Role eligibility is empirical and task-specific. A model may fail broad
candidate-gap detection yet still be useful for a bounded conditional revision
task, or vice versa.
