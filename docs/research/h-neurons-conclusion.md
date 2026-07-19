# Layer G Conclusion: H-Neurons in Small Models

## Hypothesis

Inspired by H-Neurons research, the experiments tested whether small language models expose an internal activation pattern that supports verdicts about missing or dialectically relevant context.

## Method

The repository contains a deterministic activation-probe pipeline with sparse logistic regression, leave-one-out cross-validation, label-shuffle permutation controls, and corrected significance thresholds. The research sequence also includes dialectical falsification tasks and a preregistered replication.

## Result

The experiments found no reproducible evidence of a linearly decodable dialectical verdict signal in the evaluated models up to 0.5B parameters. A candidate signal in Round 032 reached high leave-one-out accuracy but did not survive the corrected significance threshold. The preregistered Round 033 replication returned to chance-level performance.

## Interpretation

This is a bounded null result. It does not show that models have no internal representation of missing context. It does not rule out nonlinear representations, other activation sites, different tasks, larger datasets, or larger models.

It does show that the present SSL safety design must not depend on the tested internal signal. An external, logged Validation Gate and a point-of-use `AgentSafetyContract` remain the safer architecture because their decisions can be inspected, reproduced, contradicted, and rolled back.

Layer G is closed for the current small-model research track. Larger-model studies remain a separate future investigation.
