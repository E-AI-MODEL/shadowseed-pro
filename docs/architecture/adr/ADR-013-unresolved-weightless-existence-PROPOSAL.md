# ADR-013 (PROPOSED): Weightless existence before semantic bounding

- **Status:** Proposed; **not accepted**, not a change to currently accepted ADR-002 or a release authorization
- **Date:** 2026-10-28
- **Project:** Shadowseed **Pro**; neither the legacy Shadow Seed Learning repository nor NeSy
- **Related:** [ADR-001](ADR-001-validation-gate-authority.md), [ADR-002](ADR-002-epistemic-seed-contract.md), [ADR-003](ADR-003-contaminated-observation-boundary.md), [possibility-space thesis](../../research/possibility-space-thesis.md), [PR #262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262)
- **Scope:** seed existence, source attribution and authority isolation; **not** a judgement of model novelty, a new G0 decision, a production release or a claim of Q1/Q2 efficacy

## Problem and motivation

Accepted ADR-002 makes **one investigable atomic uncertainty** a contract for a seed. ADR-002 expressly says length, word limits, commas and Dutch conjunctions are *heuristics*, not atomicity. But Pro's lexical intake historically excluded some context-bound, potentially coherent dependencies as `not_atomic`. In the preserved 27 October source, 46 of 94 detector candidate occurrences failed that admission rule; all 46 passed the **current** predicate after changing only terminal sentence punctuation from a period to a question mark.

This demonstrates a **form-dependent admission boundary**, not that the 46 are independently valuable, true, one atomic thought each, model-novel or scientifically validated.

Importantly, original detector observations were already preserved in the report. **They were not live shadow seeds** and thus could not travel through the same seed-ID/trace/TTL/TrTL cycle. A separate review spreadsheet does not restore that live existence.

## Proposed decision, subject to independent architecture review

**Existence and authority are two different decisions.** Nonempty, parser-recognized, context-attributed detector possibilities may be retained as **provisional, non-authoritative living shadow seeds** even if their internal semantic scope has not yet been determined. The property `scope_status="unresolved"` means **unbounded/unknown structure**, not "probably false", "low quality", "unimportant" or "awaiting a favourable score".

- `scope_status="bounded"`: an accepted, individually investigable candidate under the existing ADR-002 contract. Its existing Gate and use-time rules remain unchanged.
- `scope_status="unresolved"`: the original candidate is retained in the **actual** Pro seed registry with its original text, attributable observation/turn and seed ID, `trace > 0`, `weight=0`. Its content may be composite, relational, exploratory or simply not yet classifiable.
- Unresolved seeds follow the existing observational lifecycle and may reactivate through TrTL, but neither lifecycle updates nor exact re-observation imply **evidence**, semantic understanding, a new relation or extra authority.
- The **current Gate can never promote** an unresolved seed and **point-of-use can never surface it** in the ordinary user-facing host prompt, tool call, retrieval influence or decision. Even a verified source match may be an answer to only part of a composite note.
- No background model calls, autonomous reasoning loop, new prompt injection path or semantic "quality detector" is authorized by this decision.

The submitted PR #262 is a **working implementation proposal** for this contract, not proof that the full security and semantic contract is ready for deployment.

## Transition and identity rules

```text
host draft -> original detector output (raw audit)
            -> parsed observation + provenance
                -> bounded seed (ADR-002 as before; Gate may later examine)
                -> unresolved seed (NEW: real, weightless, Gate-ineligible)
                -> parser-invalid/empty observation (raw audit only; never asserted as seed)
                
unresolved seed + future observations -> retain same identity; trace/TTL/TrTL
                           |           -> record relation/branch/contradiction **separately**
                           +---- NO automatic conversion into authority

If a later *new* bounded hypothesis can be articulated, it must get its own
identity and a source-traceable relation to the original unresolved candidate.
```

An unresolved seed must **not** be rewritten in place into a "better" bounded seed. New relations across multiple seed IDs belong to separate observation/lineage events, not to silent edits of the original claims. No automatically generated relation types or value ranking are assumed to exist in Pro today. The current PR records provenance and scope but **does not implement the future cross-seed semantic relation ledger**.

**Source boundary:** this proposal begins after the current detector parser. It does **not** solve candidate ideas never generated because the detector prompt asks for only up to `max_seeds` and uses the term "atomic". Neither an empty/malformed parser item nor a transcript snippet is automatically promoted to a seed. Record parser drops in the audit and examine that earlier selection later, separately.

## Trust and observability invariants

1. New unresolved seeds are born with `weight=0`, `trace>0` and immutable `scope_status="unresolved"`.
2. Existing bounded seed path is unaffected; an unresolved seed is never a deduplication/recurrence representative that can grant bounded candidates false repeated support.
3. Exact re-observation preserves identity but never manufactures `occurrence_count`, independent support, Gate credit, or truth probability.
4. Normal expiry removes authority, not the historical source audit. A store capacity ceiling may log observational backlog, **not silently drop original detector observations**.
5. The Gate and all ancillary authority paths must fail closed: explicit signals, automatic recurrence, probe feedback, SSOT evidence search, use-time surfacing, restore, import and legacy compatibility.
6. v4 serialized sessions must include `scope_status` for each seed. Legacy v1-v3 source imports may supply a historical default only within a **trusted, version-attributed migration path**. A caller's arbitrary downgrade to an older schema is not authentication.
7. Original candidate text and sensitive context stay in owner-controlled storage, not public build logs or shared research artifacts. Public aggregates may expose counts, hashes and test outcomes but no hidden raw user input.
8. Experimental research-only introspection must not be mistaken for a normal-answer injection; any model invocation on a shadow candidate is **a distinct, logged intervention** and charged to the experimental budget.

## Alternatives considered

| Alternative | Trade-off |
| --- | --- |
| Keep strict textual admission to atomic seeds | Preserves simple legacy schema but excludes complex candidate structure before longitudinal observation |
| Auto-split a composite sentence into fragments | May destroy the dependency that made the candidate interesting and silently rewrite provenance |
| Keep every excluded item only in an offline spreadsheet/observation ledger | Preserves raw evidence but **does not** give the possibility an actual Pro lifecycle |
| Remove all Gate/atomicity controls | Confuses weightless observation with unchecked authority, unacceptable |
| Distinct `ShadowPossibility` entity outside the seed registry | May offer cleaner long-term semantics, but requires duplicated/rebuilt TTL/TrTL, ID and audit plumbing; still a viable alternative for reviewers |
| **Proposed: `ShadowSeed(scope_status="unresolved")`** | Reuses the real lifecycle and enforces Gate exclusion, but is a substantial extension to the meaning of the seed model and requires compatibility/security review |

## Current verification and pending review

Mechanical verification from frozen, source-pinned Pro replay: **12 persistent sessions × four turns**, original 94 detector candidates, **48 bounded + 46 unresolved** actual births, **94 retained**, zero positive weights/promotions/normal prompt exposures, 12/12 export/restore checks passed. Source model outputs were frozen and embeddings were a deterministic toy hash, so **no semantic development or Q2 effect was observed**. Regresstion tests cover Gate, re-observation and restore. SSOT's *automatic Gate-evidence route* now excludes unresolved items; direct read-only SSOT search is still possible. This is one additional defense, not final sign-off.

**Required before ADR acceptance / merge:** (a) a reviewer independent of the implementation examines one-vs-many semantics, private data lifecycle, internal state growth, source lineage, backwards-compatible restore and all authority paths; (b) CI/test matrix including SSOT and runtime passes; (c) an explicitly logged choice of `ShadowSeed` versus a separate pre-seed representation; (d) proven rollback/migration. Recording this proposal does **not** independently satisfy those requirements.

The separate [G0 independent scientific-executor reviews](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228) are still open, with veto tasks [#234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) and [#235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235). **Do not** convert this technical feasibility into scientific approval. A new paid Q1/Q2 model run remains **NO-GO** under the current source-pinned evaluation contract until those independent review conditions are met.

## Acceptance / rejection record

**No independent reviewer decision recorded. Proposed, not accepted.** The next code PR may be reviewed, rejected, narrowed or replaced without losing the original archived candidates or changing historical benchmark denominators.
