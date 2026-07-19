# ADR 0003 — Generalize paper pipeline into document-context intake

Status: proposed
Date: 2026-05-30
Deciders: shadowseed maintainers
Related: ADR 0002; `docs/wiki/Paper-naar-Seed-Pipeline.md`; `docs/00_shadow_seed_learning_4_6.md`
Supersedes: none

## Context

The repository already has a paper line:

```text
PDF
-> text extraction
-> claims
-> failure modes
-> candidate seeds
-> scenarios
-> llm_proposed SSOT chunks
-> human verify
-> verified SSOT
-> Validation Gate
```

This line is visible in `docs/wiki/Paper-naar-Seed-Pipeline.md`, implemented in
`src/shadowseed/paper_pipeline.py`, and exercised by the paper workflows and
smokes. It is intentionally safer than a direct paper-to-evidence route: paper
chunks start as `llm_proposed`, and only verified chunks may later support the
existing SSOT and Validation Gate path.

A new product/research need is emerging: uploaded documents and conversation
attachments should be usable in an SLM conversation where SSL "exists" as
context. The risk is that this could accidentally create a second attachment,
seed, or evidence pipeline next to the existing SSL route.

## Decision

We will keep the existing paper line as the canonical route for
uploaded/document-derived context, and generalize its vocabulary and artifacts
into a broader **document-context intake**.

A paper becomes one subtype of document context. Text uploads, later attachment
uploads, and paper PDFs may all enter through the same candidate-only route.
The route may produce proposed context for an SLM conversation, but it must not
assign seed, evidence, or Round status.

In short:

```text
document or paper
-> document-context intake
-> claims
-> candidate seeds / candidate gaps
-> candidate scenarios
-> llm_proposed SSOT chunks
-> optional conversation context
-> human verify
-> verified SSOT
-> existing Validation Gate
```

## Terminology

Use these terms for new or revised artifacts:

- `document_context`: the broad intake layer for uploaded or paper-derived text.
- `document_kind`: subtype such as `paper` or `document`.
- `candidate_seeds`: proposed seed-shaped outputs, not accepted seeds.
- `candidate_gaps`: proposed missing elements for later review or conversation context.
- `conversation_context`: proposed context that may be shown to the SLM.
- `ssot_proposals`: chunks with `trust_level: llm_proposed` and `status: llm_proposed`.

Avoid these terms for unverified document output:

- `evidence`
- `verified`
- `Round 001`
- `accepted_seed`
- `promoted_seed`

`seeds.json` may remain temporarily as a backward-compatible alias, but the
preferred artifact name is `candidate_seeds.json`.

## Rules

1. Document context is not evidence.
2. Paper claims are not automatically true.
3. Uploaded documents are not automatically trusted.
4. SLM conversation context may use document context only as proposed context.
5. No document-context artifact may grant seed, evidence, or Round status.
6. `llm_proposed` chunks must not validate seeds.
7. Human or trusted verification must move a chunk to verified status before it can support external evidence.
8. The existing SSOT and Validation Gate route remains the only route by which document-derived evidence can affect seed weight or promotion.
9. Mechanical or SLM prescreens are triage aids only; they are not reviewer verdicts.
10. Paper/document scenario suites remain optional and must not silently alter core benchmark metrics.

## Intended implementation direction

The next implementation should be deliberately small:

- update `src/shadowseed/paper_pipeline.py` so it emits `candidate_seeds.json`, `candidate_gaps.json`, `conversation_context.json`, and a manifest;
- keep `seeds.json` as a compatibility alias during the transition;
- mark every proposed artifact with `evidence_status: none` and `verification_status: unverified`;
- keep `ssot_proposals.json` as `llm_proposed`;
- add focused tests that prove the route does not grant evidence;
- add a manual workflow, for example `document-context-smoke.yml`, that runs the document-context intake and uploads the artifacts for inspection.

This implementation should not rename the whole paper package in one pass and
should not merge the paper workflow group yet. ADR 0002 remains the place for
workflow consolidation; this ADR covers the semantic boundary of document
context.

## Consequences

Positive:

- uploaded documents, papers, and later chat attachments use one conceptual route;
- SSL can appear in SLM conversations as context without pretending the context is validated evidence;
- the existing paper route becomes more useful without creating a parallel seed pipeline;
- future attachment work can be tested through the same candidate-only artifact contract.

Negative / risk:

- the legacy name `paper_pipeline.py` will temporarily be narrower than the new concept;
- `seeds.json` may continue to confuse readers until downstream callers move to `candidate_seeds.json`;
- a conversation feature may still overclaim if prompts do not clearly label document context as proposed.

Mitigation:

- keep compatibility aliases only temporarily;
- add explicit manifest fields for `evidence_status` and `verification_status`;
- require any SLM-facing prompt to distinguish proposed document context from verified evidence;
- keep Gate and SSOT verification rules unchanged.

## Rejected alternatives

### Build a separate attachment pipeline

Rejected because it would duplicate the paper line and risk a parallel source of
candidate seeds or evidence.

### Treat uploaded documents as SSOT evidence immediately

Rejected because documents can be wrong, incomplete, adversarial, or
misinterpreted. Verification remains required.

### Rename the entire paper line immediately

Rejected for now because the repo already has paper workflows and docs. The
safer path is to generalize artifacts first, keep compatibility aliases, and
consolidate names later in a dedicated cleanup.

## Status and revisit

Proposed. Revisit after the first `document-context-smoke` workflow run has
uploaded inspectable artifacts and after one implementation PR proves the route
remains candidate-only.
