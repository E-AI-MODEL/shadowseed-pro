# Changelog

## Unreleased - Validation Gate authority alignment

Aligns the authority model around a single Validation Gate (issues #10–#17,
[ADR-001](docs/architecture/adr/ADR-001-validation-gate-authority.md)). Scope is
the core runtime; benchmark suites and data fixtures are unchanged in meaning.

- Added the `shadowseed.gate` package: typed `ValidationSignal`s, named Gate
  policies (`exploratory` default, `evidence_backed`), immutable `GateEvent`
  records, and `ContradictionRecord`s.
- Encapsulated authority state: `weight`, `status`, `evidence_count`,
  `contradiction_score`, and `authority_version` are no longer settable through
  the constructor or by direct assignment; all changes go through the manager's
  single transition path. Added `ShadowSeed.from_dict` / `SSLManager.restore_seed`
  for deserialization. Test/benchmark fixtures use explicit `unsafe_set_authority`
  / `unsafe_install_seed` hooks.
- Routed recurrence, probe, feedback, SSOT, and dialectic effects through the
  Gate via typed signals. Recurrence is recorded as recurrence and no longer
  relabeled as external evidence. The `external_evidence` / `contradiction`
  boolean Gate arguments are retained for backward compatibility.
- Added a contradiction lifecycle (open/resolved/superseded/withdrawn) with
  Gate-controlled recovery that requires a recorded resolution basis and
  revalidation; the legacy `contradiction_score` scalar is retained and migrated.
- Made point-of-use influence a single atomic `decide_and_record` linked to the
  authorizing Gate event and authority version, with strict replay validation.
- **Breaking (agent adapter):** removed the public non-recording
  `AgentSafetyContract.decide()` / `can_influence()`; use `decide_and_record`
  to authorize influence, or the new non-authorizing `inspect()` for status.
- Added a lightweight prompt-data boundary that quotes surfaced seeds as bounded
  candidate data (not injection prevention).
- Made English the enforced language of the core runtime prose, with a
  tokenizer-based check and documented Dutch input-language exceptions.

## Unreleased - Seed-origin observability

- Added optional, audit-only `SeedOrigin` metadata (`CandidateType` closed
  vocabulary, `detection_basis`, `context_ref`) recording *why* a candidate
  absence was proposed.
- Recorded origin on the seed `created` event and in seed serialization; the
  field is optional and defaults to `None` (backward compatible).
- Recorded a derived `basis` (`semantic` / `keyword` / `semantic+keyword`) on
  the TrTL `reactivated` event alongside the existing similarity and
  keyword-hit signals.
- Exported `SeedOrigin` and `CandidateType` from the package root.
- Guaranteed by tests that origin metadata never increases weight or counts as
  evidence: a convincing rationale must still leave `weight` at `0.0`. The seed
  lifecycle is unchanged.

## 0.3.0 - Rebuilt research repository

- Audited the complete supplied source archive.
- Extracted shared surfacing logic from the benchmark into runtime code.
- Synchronized live chat with baseline isolation, early-turn thresholds, and resurface damping.
- Applied resurface timestamps only to contract-approved seeds.
- Extracted model, embedding, retrieval, clustering, and text-similarity utilities from the benchmark namespace.
- Added compatibility wrappers for previous benchmark import paths.
- Rewrote active documentation and detector prompts in English.
- Preserved original documents, workflows, and result artifacts under `archive/`.
- Restored installed-package and Git-based integration tests.
