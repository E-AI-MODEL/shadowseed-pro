# SSL doctrine alignment execution plan

Date: 2026-08-18  
Status: execution record; doctrine/correctness work and the first mass-tester packaging baseline are merged, while evidence-scale and production-readiness work remain open  
Original branch: `agent/ssl-doctrine-alignment`

> This file records the execution sequence used during the August 2026 alignment. Current architecture authority lives in `docs/architecture/**`; current research/product status lives in `docs/research/status.md` and the Workbench documentation.

## Goal

Bring Shadowseed Pro into explicit alignment with ADR-001 through ADR-004 while preserving the 4.5/4.6 research history and keeping claims at research-ready, not production-ready. Later ADR-005 defines the chat-first product surface.

The execution order follows risk, not file layout.

## Phase 1: doctrine and correctness

Required before the doctrine alignment merge:

- ADR-002 defines one atomic epistemic candidate and separates doctrine from calibration.
- ADR-003 defines same-turn SSL-exposed detector output as a contaminated observation, not independent recurrence.
- ADR-004 defines evidence identity independently from the external signal channel.
- Real model detector output bypasses historical human-category splitting and Dutch short-fragment expansion.
- Empty/whitespace candidates and restored seed text fail closed.
- Core numeric configuration fails fast on impossible or unsafe ranges.
- Negative `surface_top_k` is rejected rather than interpreted as unlimited.
- Sparse/restored seed registries cannot overwrite an existing `ss_NNN` id.
- Workspace restore validates/migrates a temporary candidate before replacing the live database.
- The same external source cannot accumulate authority by changing SSOT/retrieval/human-feedback labels.

Verification gate:

```text
new doctrine regressions
+ focused live/Gate/lifecycle/storage tests
+ full pytest with branch coverage >= 80%
+ Ruff
+ git diff --check
+ clean package build / installed CLI via normal repository CI
```

## Phase 2: contamination observability

ADR-003 accepts fail-closed same-turn deferral as the minimum safe implementation because deferred candidates are persisted in turn reports. A later implementation may add an immutable candidate-observation ledger if cross-session analysis needs a first-class structure.

Semantic recurrence was later tightened so one detector observation context can contribute at most one recurrence credit to a matching semantic cluster. Do not make contaminated observations recurrence-bearing merely to reduce deferral counts. Recurrence remains observation, not evidence.

Research measurements should report:

- influenced turns;
- deferred contaminated observations;
- atomicity admissibility;
- later clean observation opportunities;
- later clean semantic recovery where observable;
- human quality review of a sample of deferred candidates.

## Phase 3: evidence-grade model scaling

After Phase 1 merged, the existing Qwen 7B artifacts remained historical reference measurements. Do not reinterpret them as validation of the changed runtime.

Run a new evidence-quality suite on the strongest practical model(s) available at execution time. Model scale is an experimental variable, not an SSL authority variable.

At minimum compare:

- candidate atomicity;
- candidate relevance;
- gap/doubt/what-if category mix;
- malformed-output rate;
- duplicate/near-duplicate rate;
- contaminated-observation rate after surfacing;
- false-promotion and contradiction behavior;
- answer-level blind comparison where influence actually occurs.

Freeze or record model revision/digest, detector prompt id, embeddings, dependency lock or environment manifest, input digest, Git revision, and dirty state.

This phase remains evidence work. Product packaging or successful tester operation must not be counted as efficacy evidence.

## Phase 4: mass-tester product

Do not expose the local Gradio Workbench directly as a hostile-network multi-tenant service.

The delivered chat-first tester target is:

```text
download/open -> choose model or provider -> create chat -> chat normally with SSL -> optional same-message SSL-off comparison -> feedback/export
```

The tester never authors the no-SSL baseline/control. The product generates a same-model control from the same pre-turn visible history and keeps it out of candidate detection, recurrence, the Gate, seed state, and later conversation history. Only the real live turn mutates state.

Keep advanced CLI and research controls available, but do not require Python/Git knowledge for ordinary testers when verified standalone assets are published.

The initial 0.5.0 packaging baseline covers:

- verifiable standalone build contracts for Windows amd64, Linux x86_64 and macOS Apple Silicon arm64;
- live/evidence-backed chat presented as the normal product path;
- historical evaluation/blind A/B marked as research comparison;
- hosted-provider consent and secret handling preserved;
- content-bearing export warnings preserved;
- crash-safe workspace backup/restore;
- no direct authority editor in the UI.

Platform-vendor signing/notarization, Intel/universal macOS support and public release publication remain separate from the source-level packaging contract and must not be implied unless actually delivered.

## Phase 5: production-readiness work

This phase is outside the current research-ready claim.

Required categories include:

- durable append-only or tamper-evident authority/audit storage;
- deterministic migration and replay across released schemas;
- monitoring for false promotion, stale seeds, contradictions, and evidence-source reuse;
- privacy, deletion, retention, and access control;
- rollback of promoted influence;
- prompt-injection and adversarial seed-spam controls;
- rate/resource limits;
- operator controls for high-impact actions;
- independent real-world evaluation.

## Non-negotiable invariants throughout all phases

1. One accepted seed is one bounded epistemic candidate; normalization remains heuristic rather than a semantic guarantee.
2. New seeds are weightless.
3. Trace is presence, not authority.
4. Recurrence is observation, not external evidence.
5. Generated model output is not verified evidence.
6. One underlying external source cannot be multiplied by relabelling its channel.
7. Unresolved contradictions block influence by default.
8. Promotion is eligibility, not mandatory use.
9. Actual influence requires a current point-of-use decision linked to current Gate authority.
10. Model capability never bypasses the trust model.
