# Changelog

## Unreleased - Hardened seed restoration

Defense-in-depth hardening of the persisted-seed restoration boundary. The
authority model is unchanged: restoration remains a deserialization/migration
operation outside the Validation Gate that reinstates the stored authority
snapshot and original `authority_version` exactly, produces no `GateEvent`, and
counts as no new evidence.

- **Validated snapshots.** `ShadowSeed.from_dict` now validates the snapshot
  (via `validate_seed_snapshot`) before building or installing a seed, rejecting
  malformed or internally inconsistent data with clear, field-specific
  `ValueError`/`TypeError`. Checks cover: non-empty string `id`; string `text`;
  non-empty, numeric, all-finite `embedding`; finite non-negative `trace`;
  integer non-negative counters (`occurrence_count`, `turns_dormant`,
  `evidence_count`, `authority_version`) that reject `bool`; finite `weight`
  within the `[0.0, 1.0]` authority range; finite non-negative
  `contradiction_score`; a valid `SeedStatus`; a well-formed `origin` with a
  valid `CandidateType`; and the cross-field invariant that an `EXPIRED` seed
  has zero weight.
- **Explicit duplicate handling (breaking for silent-overwrite callers).**
  `SSLManager.restore_seed` gains a keyword-only `replace_existing=False`
  parameter. Restoring a snapshot whose id already exists now raises by default
  instead of silently overwriting the live seed; pass `replace_existing=True`
  to replace deliberately. Validation completes before the duplicate check, so
  invalid data never partially mutates the registry.
- **Compatibility preserved.** Default-valued fields are only checked when
  present, so legacy snapshots that omit `authority_version` (restored as `0`)
  or use `occurrence_count = 0` remain valid; only `id`, `text`, and `embedding`
  are required. No minimum-weight constraint is imposed on `PROMOTED` snapshots.

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
