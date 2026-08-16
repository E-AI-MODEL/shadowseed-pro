# Changelog

## Unreleased - Live runtime review follow-up

- Live measurement now requires an English suite and live generation explicitly requests English output. The canonical primary and transfer session suites are English.
- The detector leak filter now covers generative few-shot examples as well as absence examples, including Markdown-wrapped echoes. Detector prompts also require plain-text candidates.
- Deferral recovery is now scored only when a later uninfluenced observation window exists. Runs with continuous surfacing report a null recovery rate instead of conflating unobservability with zero recovery.
- The recorded Qwen2.5-0.5B live run is explicitly classified as diagnostic pipeline evidence rather than efficacy evidence; its raw artifacts remain unchanged.
- `run-ssl-session` can now execute the real one-generation live runtime with
  `--runtime-mode live`. Its default live measurement runs the shipped
  evidence-backed policy without fabricated evidence plus a clearly labelled,
  non-production recurrence counterfactual. The result artifact automatically
  counts same-turn deferrals, normalization-admissible candidates, later
  semantic recovery and model/detector calls. Adapter setup, the live turn-loop,
  deferral scoring, other overhead, and total wall time are reported separately
  so scoring embeddings cannot inflate live-runtime latency. The artifact also
  pins its input digest, package version, Git revision, and dirty-worktree state.
  Live measurement rejects fixture generation and lexical hash embeddings.
- `ShadowChatSession` now preserves an explicitly configured zero recurrence
  cluster threshold instead of replacing it with the default value.
- Workbench evidence submission now clears the operator-attestation checkbox
  after every successful Gate call, so each authority-bearing source requires a
  fresh confirmation. Compare applies the same evaluation fallback as session
  inspection to malformed legacy runtime metadata.
- The Workbench extra now installs HTTPX SOCKS support. Gradio can start in
  environments that configure a SOCKS proxy without disabling or bypassing the
  user's proxy settings.
- Workbench session creation now offers explicit live/evaluation and embedding
  backend choices. Session lists display the selected mode, and imported
  scenarios persist the same runtime configuration.
- Live Workbench sessions expose an operator-attested evidence action that sends
  provenance-bearing human support through the existing Validation Gate. The UI
  cannot set weights or promotion status directly, and duplicate sources remain
  idempotent.
- Baseline comparison now rejects live turns with an actionable explanation
  instead of rendering their intentionally absent baseline as `None`.
- Workbench session views and load/create status text now expose the persisted
  runtime mode. Legacy Workbench snapshots without runtime metadata are shown as
  evaluation sessions.
- Live sessions and the direct `ShadowChatSession` API now default to the
  `evidence_backed` product path and expose an explicit `submit_evidence` trust
  boundary. Verified external support must be supporting, provenance-bearing,
  and externally typed; the interactive chat exposes the same path through
  `/support <seed_id> <source_ref>`.
- A live turn that surfaced SSL context defers every candidate detected in that
  answer. This closes same-turn self-credit for both paraphrases and semantically
  different consequences, which an embedding threshold could not prove
  independent.
- The corrected half-life formula keeps true half-life semantics while migrating
  the default to `3*ln(2)` turns, preserving the historical `exp(-t/3)` decay
  curve and its default dormant/expiry horizon. Pre-live version-1 session
  snapshots are migrated on restore while later version-1 snapshots, which
  already used true half-life semantics, remain unchanged. Legacy snapshots also
  resume explicitly in evaluation mode instead of inheriting the new live
  default.
- Evaluation sessions now apply the configured Gate policy instead of silently
  forcing `exploratory` recurrence decisions.
- Fixture session benchmarks reject missing, blank, and non-string
  `baseline_answer` values with the same actionable validation error.
- Recurrence-driven benchmarks take their signal threshold from
  `SSLCoreConfig`; the fixed benefit fixtures declare their historical
  two-occurrence benchmark setting in that config.
- Added direct contracts for configured recurrence thresholds, changed-signal
  Gate events, evaluation isolation and policy selection, live persistence, and
  invalid fixture baselines.
- Updated the README, architecture, usage documentation, and manuscript to
  distinguish the live one-generation path from the baseline-isolated evaluation
  path and to document the live evidence boundary. The operator or host
  application is explicitly identified as the trust anchor behind `verified=True`.

## 0.4.2 - 2026-08-15 - Authority and retrieval hardening

- Validation Gate support is idempotent for recurrence observations and exact
  verified evidence source-and-kind pairs. Replaying the same observation no
  longer raises weight or evidence count; the ignored duplicate remains visible
  in the Gate event reason. Multiple independent confirmations within one signal
  kind require typed signals with distinct `source_ref` values. For non-expired
  seeds, new verified external support without `source_ref` raises a clear error
  before any Gate event or authority change. Expired seeds instead record the
  terminal `EXPIRED` decision without applying evidence or authority; historical
  anonymous events remain replayable.
- External feedback accepts an optional `source_ref`, so distinct reviewers or
  evidence items can be credited without treating repeated feedback as new
  authority.
- Chat retrieval probes now pass every promoted candidate through the atomic
  point-of-use contract and record retrieval decisions in the influence ledger.
  Retrieval centroids contain authorized seeds only.
- Intake deduplication selects the most similar eligible seed instead of the
  first seed above the threshold.
- Benchmark drivers no longer relabel recurrence as external evidence or use
  unsafe authority setup for benefit promotion. Benefit fixtures now use four
  observed turns, and adversarial positive controls carry explicit evidence
  references.
- CLI smoke tests write into pytest temporary directories. CI now gates branch
  coverage at 80% and fails if the suite changes the checkout.
- Reconciled the README, architecture ADR and summaries, research status,
  language policy, and completed alignment plan with the delivered runtime
  contract and the final PR #46 provenance rules.

## 0.4.1 - 2026-08-08 - Workbench review follow-up

Corrective patch for two P2 review findings that arrived after the 0.4.0
Workbench pull requests had already merged.

- Seed inspector timelines now interleave events across ledgers by the actual
  timestamp instant, including ISO-8601 timezone offsets, instead of presenting
  ledger grouping as chronology.
- Scenario batches preserve the session id and completed progress when a backend
  call fails part-way through.
- Partial scenarios can resume at the failed question without replaying completed
  hosted-model calls. Resume validates persisted turn count, completed question
  prefix, profile, backend, and model before continuing.
- The Workbench Scenario tab now reports partial batches as paused and exposes a
  dedicated resume action.
- The release workflow derives its tag and release notes from the project version
  so patch releases use the same post-merge portability and checksum gates.

`v0.4.0` remains immutable historical release evidence. This patch does not
modify benchmark evidence or add scientific model-benefit claims.

## 0.4.0 - 2026-08-08 - Tester Workbench preview

Adds a practical, local-first tester environment on top of the existing
Shadowseed runtime without weakening Validation Gate or point-of-use authority.

- Added application services and a versioned SQLite workspace for resumable
  tester sessions, profiles, feedback, backup, restore, and diagnostics (#39).
- Added the local Gradio Workbench, seed inspection, record-only tester feedback,
  scenario import, and deterministic side-by-side/blind comparison (#42).
- Added a real `[workbench]` package extra and `shadowseed workbench` CLI entry
  point with loopback-only binding by default.
- Added full session report ZIPs and privacy-minimized support bundles with
  SHA-256 manifests, defensive ZIP validation, and atomic verified replacement.
- Added report/support/verify CLI commands and an Export tab in the Workbench.
- Added Linux, macOS, and Windows clean-install portability smokes plus optional
  Docker packaging. Windows coverage exposed and fixed a SQLite backup-handle
  lifetime bug before release.
- Added release automation that publishes `v0.4.0` only after the post-merge
  Workbench Portability workflow succeeds on `main`; the workflow re-verifies
  the published wheel, source distribution, and `SHA256SUMS`.
- Added practical tester, privacy/limitation, and release documentation.

The Workbench remains local-first, single-user, research-ready, and not
production-ready. Fixture and tester runs are product/evaluation artifacts, not
new benchmark evidence and not proof of general model-quality improvement.

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
