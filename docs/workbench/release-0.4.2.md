# Shadowseed Workbench 0.4.2 Tester Preview

Shadowseed 0.4.2 publishes the authority and retrieval hardening already merged and validated on `main` after 0.4.1. It does not introduce a new tester workflow or a new scientific claim.

## Hardened authority and evidence handling

- Verified external support is provenance-bound to a non-empty `source_ref` for non-expired seeds.
- Recurrence observations and verified evidence are idempotent at their intended identity boundary; replaying the same support cannot silently raise authority again.
- Distinct support in the same signal kind requires distinct source references, while the same source under a different typed signal kind remains a distinct signal.
- Historical anonymous Gate events remain replayable, and expired seeds follow their terminal `EXPIRED` path without applying new evidence or authority.
- External feedback can carry an optional `source_ref` so independent reviewers or evidence items can be represented without treating repeated feedback as new support.

## Hardened retrieval and intake behavior

- Promoted candidates are re-authorized through the atomic point-of-use contract before retrieval influence.
- Retrieval centroids include authorized seeds only.
- Intake deduplication selects the best eligible similarity match rather than the first candidate above threshold.

## CI and reproducibility

- CI now enforces at least 80% branch coverage.
- CI verifies that the test suite leaves the tracked checkout unchanged.
- Package build, clean-wheel installation, installed CLI smoke, Python 3.10 and 3.12 tests, Workbench checks, portability checks, and release-asset verification remain part of the release path.
- This release metadata change does not rewrite benchmark result artifacts.

## Claim boundary

This release remains a local-first, single-user tester preview and a research-ready implementation. It does not establish general answer-quality improvement, production readiness, universal prompt-injection safety, or a general neural missing-context signal.

`v0.4.0` and `v0.4.1` remain unchanged historical release artifacts.
