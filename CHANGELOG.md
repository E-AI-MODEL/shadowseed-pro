# Changelog

## Unreleased - Manager modularization and Gate boundary completion

`SSLManager` was reduced from 1,974 to 727 lines and now serves as the runtime
orchestrator and compatibility facade. Executable concerns that were previously
embedded in `manager.py` now have one canonical implementation:

- `shadowseed.models` owns stable data contracts, authority guards, snapshot
  validation, and serialization (#26).
- `shadowseed.contradictions` owns contradiction-record collection,
  blocking-state derivation, formal resolution, identifier sequencing, and
  legacy migration (#27).
- `shadowseed.intake` owns embedding acquisition, candidate normalization,
  atomicity heuristics, deduplication, and seed creation/update (#30).
- `shadowseed.lifecycle` owns TTL decay, dormancy, TrTL reactivation, and
  terminal expiry (#31).
- `shadowseed.vector_workflows` owns uncertain-region search,
  external-feedback routing, labels, and in-memory constellation construction
  (#32).
- `shadowseed.gate.runtime_adapter` is the single executable Gate-controlled
  authority-decision engine, including contradiction resolution and probe
  feedback (#22, #29).
- Canonical documentation and `repository-authority.yaml` now reflect the final
  ownership boundaries. Structural tests cap `manager.py` and prevent extracted
  implementation primitives from drifting back into it (#33, #35).

Compatibility remains explicit:

- Existing public manager methods remain available. Methods for extracted
  concerns delegate to their canonical modules.
- Historical model imports remain object-identical. For example,
  `shadowseed.manager.ShadowSeed`, `shadowseed.models.ShadowSeed`, and
  `shadowseed.ShadowSeed` are the same class. `manager.ContradictionRecord`
  remains the Gate contract class, and the historical wildcard-import surface
  is covered by regression tests.
- `SSLManager.contradiction_records` changed from an instance attribute to a
  property backed by the canonical contradiction domain. Normal reads,
  mutation, and assignment remain compatible. An assigned `list` keeps its
  identity, so later appends through the caller's own reference remain visible
  to blocking queries and export. Code that inspects instance storage or
  descriptor behavior may observe this structural change.
- `AgentSafetyContract.require_logged_promotion` remains accepted by the
  constructor for compatibility but has no effect on authorization. Point-of-use
  authorization always requires a logged promotion and a live Gate event for
  the current `authority_version`. Only the contradiction check remains
  configurable (#35).

Claim and assurance wording was synchronized with the final structure:
`GateEvent` and `AgentInfluenceRecord` are frozen and support strict in-process
replay; other retained event and result objects are mutable; durable,
tamper-evident audit storage remains a production gap (#34, #35). No runtime
policy threshold, serialized shape, or benchmark meaning was intentionally
changed by the modularization series.

## Unreleased - Claim discipline and CI assurance

Documentation and CI hardening (issue #23). No runtime behavior change.

- Calibrated README claims to what the runtime and tests support, with a new
  **Assurance boundaries** section:
  - "non-bypassable" is scoped to *new* authority decisions on the supported
    runtime/public API surface; restoration (`from_dict` / `restore_seed`) is
    carved out as a separate validated trusted boundary that reinstates a
    prior Gate-produced snapshot, and the test/benchmark `unsafe_set_authority`
    / `unsafe_install_seed` hooks plus arbitrary in-process Python mutation are
    explicitly out of scope (enforced by the static checks in
    `test_gate_signal_routing.py`);
  - "atomic seed" is described as a normalization target and tested heuristic,
    not a semantic guarantee for every model-generated candidate;
  - in-process frozen/replayable `GateEvent` and influence records are
    distinguished from durable, append-only, tamper-evident storage, which is
    called out as a production gap;
  - the point-of-use `AgentSafetyContract` is documented by its exact checks:
    weight above zero, promoted status, a logged promotion, and a live
    current-version Gate-event link are always required; the contradiction
    check is enabled by default and is the only configurable relaxation. The
    compatibility-only `require_logged_promotion` field cannot bypass the
    logged-promotion requirement. This replaces broader wording that implied
    both checks were configurable opt-outs;
    "zero-trust" wording bounded to the default configuration.
- Expanded CI: added a `build` job that builds the wheel/sdist, installs it in a
  clean virtualenv, and runs the installed console entry point; added a CLI smoke
  step to the test matrix. Documented explicit deferral decisions for static type
  checking and coverage gating in the workflow.

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
  `contradiction_score`; a valid `SeedStatus`; a well-formed `origin` (mapping
  with a valid `CandidateType`, string `detection_basis`, and string-or-`None`
  `context_ref`); and the cross-field invariant that an `EXPIRED` seed has zero
  weight.
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
