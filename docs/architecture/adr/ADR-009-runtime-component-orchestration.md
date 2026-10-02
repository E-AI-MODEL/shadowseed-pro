# ADR-009: Runtime component ownership and human-SSL orchestration

Status: Proposed  
Date: 2026-10-02  
Owners: Shadowseed maintainers  
Target release: 0.11.0 Research Preview  
Refines: ADR-001, ADR-002, ADR-003, ADR-005 and ADR-008

## Context

The end-to-end live path now works, but runtime, configuration and UX do not always expose the same component boundaries. This ADR aligns component ownership, Validation Gate semantics, human-SSL handoffs, stateful configuration and prompt ownership without replacing the existing SSL doctrine.

The doctrine remains: observation is not authority; recurrence is not external evidence; the Validation Gate is the authority boundary; promotion is eligibility rather than mandatory influence; and point-of-use authorization is required before influence.

## Decision

### 1. Canonical components

The live path is: answer generation -> detection context -> detector -> observation/intake -> semantic representation -> recurrence/lifecycle -> Validation Gate -> human/SSL handoff -> promoted eligibility -> relevance/surfacing -> point-of-use authorization -> influence/revision -> final answer -> optional verify/audit.

Each component owns one decision class. Generation writes the draft. Detection proposes candidates. Intake owns provenance, atomicity and deduplication. Semantic representation owns embeddings. Recurrence/lifecycle owns independent recurrence, trace, dormancy and expiry. The Validation Gate alone owns authority changes. Relevance decides whether an eligible seed matters now. Point-of-use records whether a concrete influence action is allowed. Revision may change answer text but never seed authority. Verification measures without mutating the live path.

### 2. Current, pair, seed and cluster are component-scoped

For chat detection, current pair means current user question + current draft answer. For source ingestion, detection context is the current source observation: source chunk + provenance. Recurrence operates on atomic seed representations and semantic clusters. Surfacing compares the current user question with promoted seeds. Same-turn revision receives current question + existing draft + allowed seed context.

The Workbench must therefore use component-qualified labels such as Detectiecontext, Recurrence, Relevantiematch and Invloed op antwoord. A generic current/pair selector is not sufficient.

### 3. Validation Gate semantics are singular

Detector output, similarity, cluster membership, raw source text, retrieval hits, prompt wording, UI inspection and A/B comparison cannot grant authority.

When current Gate revalidation is enabled, the current check must use the same meaning as the named canonical Gate policy. A second interpretation of evidence_backed or exploratory under the same policy name is not allowed.

legacy_evidence_required remains compatibility/research only and is not a normal maximum-strictness endpoint.

### 4. Human-SSL orchestration is first-class

Every session and seed exposes one of four states: Shadowseed is aan zet; menselijke review is optioneel; jij bent aan zet; geblokkeerd.

Each state explains why it applies, which exact human action is available, and what happens if the human does nothing. The application layer derives the state; the UI only presents it.

The application already computes Assisted review-required seeds. vNext must surface that handoff. A blocking contradiction must expose authorized resolution where supported. Verified support does not silently close an open contradiction.

### 5. Authority profile and Gate policy remain distinct

An authority profile describes the default human/SSL division of labor. The effective Gate policy describes the actual authority rule. If advanced configuration overrides the profile default, the Workbench shows the override explicitly.

### 6. Split self-reinforcement

The current allow_self_reinforcement setting combines two mechanisms: SSL-generated output contributing to later recurrence/authority, and a newly promoted seed triggering one same-turn answer revision.

These become separate settings: allow_ssl_generated_recurrence and allow_same_turn_revision. ADR-003 remains the fail-closed default for SSL-exposed observations.

### 7. Same-turn influence is bounded revision

Same-turn revision receives the existing draft explicitly. Its contract is question + existing draft + allowed seed context -> revised answer. It may return the existing draft unchanged when the seed adds no material value.

### 8. Stateful configuration is explicit

Generation, detection and revision are separate model roles even when one physical model performs all three.

Embedding backend/model affects deduplication, clustering, recurrence, reactivation, relevance, probes, retrieval and SSOT search. Changing embedding space after seeds exist requires a new session, re-embedding migration or explicit rebuild.

recurrence_mode and cluster_threshold affect persisted recurrence state. They may not be hot-switched when that leaves restored state inconsistent with active configuration.

Advanced/God mode remains available and writes runtime configuration only. Settings are grouped by owning component and state whether they are immediate or stateful.

### 9. Prompt contracts are versioned runtime assets

Each live prompt has a prompt id, version, component owner, trigger moment, input contract, exact template, output contract and stable content hash. The live set distinguishes answer generation, chat detection, source detection where different, candidate-context framing and same-turn revision.

### 10. Same-turn A/B remains non-mutating

The ordinary comparison keeps the same current user message and pre-turn visible history, removes SSL candidate context from the control, keeps control output out of detection/recurrence/Gate/history and adds at most one extra current-turn generation.

Reporting distinguishes context exposure, textual difference and human quality judgment. Context exposure is not proof of improvement.

### 11. Add a behavior/configuration epoch

The production reconfiguration audit is extended with a behavior/configuration fingerprint covering material model-role, prompt, embedding, recurrence, Gate, self-generated-recurrence, revision and surfacing settings. Turn reports reference the active epoch or digest so later God-mode changes do not rewrite the meaning of older turns.

## Release policy

This alignment targets 0.11.0. Published 0.10.1 semantics remain reproducible and are not silently replaced. A 0.10.x patch is reserved for isolated operational fixes that do not change SSL research semantics.

## Acceptance criteria

1. Chat detection can consume current question + current draft as an explicit pair.
2. Source detection remains a separate source-observation context.
3. Recurrence remains seed/cluster based.
4. Current Gate revalidation and canonical Gate policy cannot disagree under the same policy name.
5. legacy_evidence_required is removed from normal product strictness choices.
6. vNext exposes session- and seed-level human/SSL orchestration state.
7. Assisted review-required seeds are visible in normal UX.
8. Blocking contradictions expose authorized resolution where supported.
9. Same-turn revision and SSL-generated recurrence are independently configurable.
10. Same-turn revision receives the existing draft and may return it unchanged.
11. Stateful recurrence and embedding changes cannot silently reinterpret stale state.
12. Advanced settings are grouped by owning component and statefulness.
13. Prompt IDs, versions and hashes are available for the active live prompt set.
14. Same-turn A/B distinguishes exposure, textual change and human quality judgment.
15. Turn reports carry a behavior/configuration epoch or digest.
16. Existing Gate, contaminated-observation, point-of-use and audit invariants remain regression-tested.
