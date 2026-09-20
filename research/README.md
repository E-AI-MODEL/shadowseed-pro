# Shadowseed Research

Research, benchmark, falsification, and evaluation tooling for Shadowseed.

This package is deliberately separate from the product/runtime distribution.
It depends on `shadowseed`; the product package must never depend on
`shadowseed-research`.

During the migration, the canonical benchmark implementation is mirrored here
while the historical `shadowseed.benchmark` namespace remains available.
Research workflows will move to `shadowseed_research.benchmark` before the
evaluation implementation is removed from the product distribution.
