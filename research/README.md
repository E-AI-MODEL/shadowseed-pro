# Shadowseed Research

Research, benchmark, falsification, and evaluation tooling for Shadowseed.

This package is deliberately separate from the product/runtime distribution.
It depends on `shadowseed`; the product package must never depend on
`shadowseed-research`.

During the migration, the canonical benchmark implementation is mirrored here
while the historical `shadowseed.benchmark` namespace remains available.
Research workflows will move to `shadowseed_research.benchmark` before the
evaluation implementation is removed from the product distribution.


## Layer G vNext (issue #203)

The [preflight protocol](../docs/research/layer-g-vnext-preflight.md) and
`benchmark/layer_g_vnext.py` isolate original-answer activations from candidate
and label metadata. This is a **synthetic instrument preflight**, not a
reproduction of H-Neurons or evidence for internal unspoken-possibility
signals. It does not change the SSL runtime or Gate.

## P2 original-generation capture

The optional GPU-only [generation-time reader](src/shadowseed_research/benchmark/layer_g_live_generation.py) measures next-token **decision-prefix** MLP activations during the original `model.generate()` call, before any seed or label is created. Its [CLI](scripts/layer_g_live_generation.py) requires a pinned model revision and a synthetic test prompt. Passing fake-hook CI is not actual model evidence. See [the P2 protocol](../docs/research/layer-g-vnext-preflight.md#p2-synchronous-original-generation-decision-feature-capture-code-ready).

## Gratis 14B-instrumentpilot

[Open in Colab](https://colab.research.google.com/github/E-AI-MODEL/shadowseed-pro/blob/feat/layer-g-vnext-preflight/research/notebooks/layer_g_14b_free_gpu.ipynb) of gebruik [het notebook](notebooks/layer_g_14b_free_gpu.ipynb) in Kaggle met een gratis CUDA GPU. Dit draait Qwen 2.5 14B in NF4 4-bit (dus niet full precision), met exact dezelfde generatie-hooks als de overige P2-instrumentcode. Geen betaalde jobs of automatische downgrade. Een CI-pass bewijst geen werkende 14B-run of neurale SSL-hypothese.
