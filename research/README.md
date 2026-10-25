# Shadowseed Research

Research, benchmark, falsification, and evaluation tooling for Shadowseed.

This package is deliberately separate from the product/runtime distribution.
It depends on `shadowseed`; the product package must never depend on
`shadowseed-research`.

During the migration, the canonical benchmark implementation is mirrored here
while the historical `shadowseed.benchmark` namespace remains available.
Research workflows will move to `shadowseed_research.benchmark` before the
evaluation implementation is removed from the product distribution.

## Archived possibility-space experiment

The [first fixed-edge possibility-space pilot](../experiments/possibility_space/README.md) is retained for historical reproducibility and negative findings only. Its 24 GPT-5 calls did not establish either clause of the [original Shadowseed research question](../docs/research/possibility-space-thesis.md). The archived workflow is manual and offline-only, and an explicit command-line acknowledgement is required before an individual could attempt a paid rerun outside that workflow. This experiment is **not** a current research-package benchmark or evidence of model efficacy. The [new narrow compression-retention test](../docs/research/possibility-space/compression-retention-narrow-pilot-2026-10-25.md) is likewise labelled as mechanical instrumentation, not as proof of the original two-part thesis.
