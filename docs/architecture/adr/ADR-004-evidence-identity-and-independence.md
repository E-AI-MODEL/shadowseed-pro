# ADR-004: Evidence Identity Is Independent of the Signal Channel

- Status: Accepted; implementation aligned
- Date: 2026-08-18
- Refines: ADR-001 and ADR-002

## Context

The Validation Gate receives typed channels such as SSOT, human feedback, and retrieval. At the time this ADR was proposed, the runtime deduplicated verified external support by `(signal kind, source_ref)`. This meant the same underlying source reference could be offered once as SSOT and again as retrieval or human feedback and be counted as distinct authority support.

That behavior was auditable, but it confused two different concepts:

- **channel**: how an observation reached the Gate;
- **evidence identity**: which underlying source or evidence unit the observation represents.

Channel diversity is not automatically evidential independence. Human verification of a retrieved document can increase confidence in that same evidence unit, but it does not create a second independent document.

`ValidationSignal.independent` already exists as provenance metadata, but a boolean assertion alone cannot safely create a new evidence unit. Likewise, `strength` cannot serve as source trust: some producers use it for relevance or semantic similarity.

## Decision

External authority support is deduplicated by its **underlying evidence identity**, not by the signal kind.

For the current contract, a stable non-empty `source_ref` is the canonical evidence identity unless a future schema introduces a separate explicit `evidence_id`.

Canonical rule:

> One underlying evidence unit may travel through several channels, but it may contribute authority only once unless the Gate receives a genuinely different evidence identity.

Therefore, for verified supporting external signals:

```text
SSOT(source_ref=A)
RETRIEVAL(source_ref=A)
HUMAN_FEEDBACK(source_ref=A)
```

represent one authority-bearing evidence unit, not three.

The signal kind remains in the immutable audit record so the path by which evidence arrived is still visible.

## Independence

`independent=True` is a provenance assertion, not a mechanism for bypassing identity deduplication.

Two support items may be treated as distinct only when they carry distinct canonical evidence identities. The host/operator remains responsible for not minting artificial source references for the same underlying material.

A future evidence schema may make this stronger with fields such as:

- `evidence_id`;
- `source_ref`;
- `independence_group`;
- `verifier_ref`;
- source version or content digest;
- provenance chain.

Until that exists, exact `source_ref` identity is the safest compatibility-preserving unit available to the runtime.

## Strength is not trust

`ValidationSignal.strength` is a bounded magnitude that may encode relevance, similarity, or another channel-specific score. It must not be interpreted globally as source reliability without a separate typed contract.

For example, SSOT validation can use semantic similarity as a signal strength. A high similarity score does not by itself prove that the source is authoritative or independent.

## Evidence-backed authority

The public `evidence_backed` policy may continue to grant bounded authority increments for unique verified external evidence units. Recurrence remains observable but cannot satisfy the external-evidence requirement.

Promotion remains cumulative and policy-controlled. This ADR does not declare a universal number of evidence units sufficient for every deployment. The current fixed weight increment and promotion threshold are calibration values and should be treated as such under ADR-002.

## Historical replay

Historical Gate events must remain readable and immutable. Tightening evidence identity for new and reconstructed deduplication must not rewrite old event payloads or retroactively change recorded weight transitions.

When a historical ledger already contains the same source under multiple channel kinds, those events remain part of the audit history. For subsequent authority support, that source is treated as already applied.

## Contradictions

Contradiction evidence is not collapsed into supporting-evidence identity merely because it references the same source. Direction, contradiction records, and resolution remain separate authority workflows under ADR-001.

## Consequences

### Positive

- closes cross-channel double counting of the same source;
- makes evidence independence scientifically clearer;
- keeps channel provenance without confusing it with independent confirmation;
- does not elevate semantic similarity into source trust;
- improves replay and audit interpretation.

### Costs

- callers that intentionally reused one `source_ref` across channels no longer receive multiple authority increments;
- source-reference discipline becomes more important;
- stronger independence guarantees eventually require richer evidence identifiers or content digests.

## Required invariants

1. The same verified supporting external `source_ref` contributes authority at most once, regardless of external signal kind.
2. Different signal kinds remain visible in Gate events.
3. Recurrence can never share or impersonate an external-evidence identity.
4. `independent=True` cannot bypass evidence-identity deduplication.
5. `strength` is not globally interpreted as source trust.
6. Historical event payloads are never rewritten.
7. Contradiction lifecycle remains separate and explicit.

## Verification targets

Contract coverage includes tests for:

- same source and same kind is idempotent;
- same source across SSOT, retrieval, and human-feedback kinds is also idempotent for authority;
- distinct source references can each contribute bounded authority;
- duplicate evidence remains visible in the Gate audit reason/input record;
- recurrence cannot satisfy `evidence_backed`;
- restoration/replay still recognizes previously applied evidence.