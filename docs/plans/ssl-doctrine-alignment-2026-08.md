# SSL doctrine alignment execution plan

Date: 2026-08-18
Status: in execution
Branch: `agent/ssl-doctrine-alignment`

## Goal

Bring the current Shadowseed Pro runtime into explicit alignment with ADR-001 through ADR-004 while preserving the 4.5/4.6 research history and keeping current claims at research-ready, not production-ready.

The execution order follows risk, not file layout.

## Phase 1: doctrine and correctness

Required before merge:

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

ADR-003 accepts the existing fail-closed intake behavior as the minimum safe implementation because deferred candidates are persisted in turn reports. A later implementation may add an immutable candidate-observation ledger if cross-session analysis needs a first-class structure.

Do not make contaminated observations recurrence-bearing merely to reduce deferral counts.

Research measurements should report:

- influenced turns;
- deferred contaminated observations;
- atomicity admissibility;
- later clean observation opportunities;
- later clean semantic recovery where observable;
- human quality review of a sample of deferred candidates.

## Phase 3: evidence-grade model scaling

After Phase 1 merges, the existing Qwen 7B artifacts remain historical reference measurements. Do not reinterpret them as validation of the changed runtime.

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

## Phase 4: mass-tester product

Do not expose the current local Gradio preview directly as a hostile-network multi-tenant service.

Target tester path:

```text
download/open -> choose model or provider -> test -> optional feedback/export
```

Keep advanced CLI and research controls available, but do not require Python/Git knowledge for ordinary testers.

Before broader distribution:

- signed or otherwise verifiable standalone packaging per supported desktop OS;
- live/evidence-backed path presented as the normal product path;
- evaluation/blind A/B clearly marked as research comparison;
- hosted-provider consent and secret handling preserved;
- content-bearing export warnings preserved;
- crash-safe workspace backup/restore;
- no direct authority editor in the UI.

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

1. One accepted seed is one epistemic candidate.
2. New seeds are weightless.
3. Trace is presence, not authority.
4. Recurrence is observation, not external evidence.
5. Generated model output is not verified evidence.
6. One underlying external source cannot be multiplied by relabeling its channel.
7. Unresolved contradictions block influence by default.
8. Promotion is eligibility, not mandatory use.
9. Actual influence requires a current point-of-use decision linked to current Gate authority.
10. Model capability never bypasses the trust model.
