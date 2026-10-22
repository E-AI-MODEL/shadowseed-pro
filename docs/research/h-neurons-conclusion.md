# Layer G Conclusion: H-Neurons in Small Models

## Hypothesis

Inspired by H-Neurons research, the experiments tested whether small language models expose an internal activation pattern that supports verdicts about missing or dialectically relevant context.

## Method

The repository contains a deterministic activation-probe pipeline with sparse logistic regression, leave-one-out cross-validation, label-shuffle permutation controls, and corrected significance thresholds. The research sequence also includes dialectical falsification tasks and a preregistered replication.

## Result

The experiments found no reproducible evidence of a linearly decodable dialectical verdict signal in the evaluated models up to 0.5B parameters. A candidate signal in Round 032 reached high leave-one-out accuracy but did not survive the corrected significance threshold. The preregistered Round 033 replication returned to chance-level performance.

## Interpretation

This is a bounded null result for a **specific target**: the ability to
linearly recover an externally supplied dialectical maintain/reject verdict
from the activations of models at or below 0.5B under the specified
experiments. It does not test whether an unexpressed, coherent alternate
relation was represented but not verbalized by the model. It does not show
that models have no internal representation of missing context, and it does
not rule out nonlinear representations, other read locations, different
labels/tasks, or more capable models.

The original [H-Neurons paper](https://arxiv.org/html/2512.01797)
(Gao et al., 2025) selected sparse feed-forward neurons in **six models
from 4B to 70B**, using factual response labels, then tested neuron-level
interventions on **over-compliance**. Those experiments show that internal
representations can be mined for non-generative signals; they do **not**
identify SSL's hypothetical internal signal for unspoken possibilities.
Our non-replication is neither a replication attempt of their exact task
nor contrary evidence to that study.

See [the revised SSL research doctrine](epistemic-possibility-and-h-neurons.md)
for the distinction between L1 open-set generation and L2 internal probing.

It does show that the present SSL safety design must not depend on the tested internal signal. An external, logged Validation Gate and a point-of-use `AgentSafetyContract` remain the safer architecture because their decisions can be inspected, reproduced, contradicted, and rolled back.

Layer G is closed for the current small-model research track. Larger-model studies remain a separate future investigation.
