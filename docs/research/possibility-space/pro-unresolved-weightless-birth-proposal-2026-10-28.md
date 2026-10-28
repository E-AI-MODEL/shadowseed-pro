# Shadowseed Pro — weightless birth for unresolved-scope possibilities

**28 October 2026. Status: proposed Pro contract extension; working draft implementation in this branch. Not an accepted ADR, approved production behaviour, or proven Q1/Q2 effect.**

## What motivated this

The original 27 October dual-model source artefact contained 94 detector-item observations; 46 were rejected as `not_atomic`. Replaying the 46 original sentences through the current Pro `is_atomic_seed` revealed a **form-dependent refusal**: the rejected declarative sentences would all pass the question-shaped branch if the final period became a question mark. This does *not* show that all 46 are semantically atomic, true, original or valuable. It shows that the current intake can preclude their actual life in shadow memory based on expression. Original observation text survived in the raw records, but had no live seed ID or TTL/TrTL path.

Accepted [ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md) currently requires every **accepted** seed to represent one independently investigable atomic epistemic candidate. This proposal deliberately **extends that contract** for an earlier stage of uncertainty: a nonempty original detector possibility whose individual scope has not been determined. It requires independent architectural review/amendment to ADR-002 before merging into a release. *Weightless* means zero authority, not presumed semantic adequacy.

## Implemented behind this unmerged proposal branch

A detector candidate meeting the current atomicity contract keeps its ordinary `scope_status="bounded"` flow, deduplication, recurrence, evidence, Gate and point-of-use.

A **nonempty** candidate which failed current structural/lexical atomicity intake no longer vanishes from the actual Pro runtime. The intake records it as a real `ShadowSeed` with `scope_status="unresolved"`, original source string, source/observation lineage, trace greater than zero and **weight exactly zero**.

This unresolved seed:

- has a normal `ss_...` identity and an audited `created` event, plus separate `born_unresolved` intake lineage and `seeds_born_unresolved` report fields;
- persists in the real `ShadowseedEngine` across turns, export/restore, trace decay, DORMANT, TrTL reactivation and normal terminal expiry;
- retains the exact source expression, without silently splitting or paraphrasing the possibility to pass lexical rules;
- may be encountered again by **exact text**, preserving its ID and recording `unresolved_reobserved` without changing occurrence credit or Gate authority; a repeated item in the **same** batch gives no extra credit;
- is **excluded** from ordinary embedding-based seed deduplication and accepted-seed recurrence clustering so the structure of a different bounded seed cannot silently overwrite or reinforce it;
- **cannot receive positive weight, evidence-count authority or promoted status** while unresolved, even if a strong exploratory or verified-evidence Gate policy is invoked;
- is excluded by `current_gate_authorizes` and normal point-of-use, so the host receives no unresolved seed prompt text, injected retrieval, influence or permission to act.

This is an *actual birth and lifecycle*, not another independent review queue. Yet it is **not** autonomous content growth or evidence that the model has found a new kind of relation.

### No automatic semantic upgrade

A newly observed bounded candidate is independently born and does not silently alter an unresolved one. Any future operation to give such a record bounded structure must specify the source observation, new identity, transformation steps and verification before that separate candidate enters standard authority handling. It must not rewrite the old record or pretend that the original was proven true.

### Persisted snapshots and rollback

Session state schema advances to v4. New v4 session restores fail closed if a saved seed lacks `scope_status`; v1–v3 snapshots remain supported and are interpreted with the historical bounded scope. `scope_status` is immutable on live seed instances. The storage snapshot's separate integrity controls remain important: the schema check cannot by itself prevent an attacker who can forge arbitrary historical v3 data from claiming an older shape. No cryptographic security claim is made here.

## Evidence and boundaries

**Mechanics tested locally, no new model calls:** All 46 previously excluded raw sentences became 46 distinct unresolved, weight-zero Pro seeds in a deterministic replay: 46 stored and zero Gate events. Seven new targeted tests check birth, source identity, same-ID observation, multi-turn travel, TTL/TrTL, session round-trip, v4 scope omission tampering, Gate policies and separation from bounded seeds. Existing selected Gate and product tests pass.

**Full test status:** the broader suite was run in parts. Three Gradio UI tests fail because the installed version does not support `Markdown(..., scale=4)`. They failed identically on the original unmodified checkout, so are not caused by this change. The normal repository CI must still pass before merging. `ruff` is not installed in the local execution environment.

**Scientific uncertainty remains:** syntactic form is not epistemic value. The 46 observations are not independent conceptual discoveries. No test demonstrates that an unresolved seed produces new model-originated relationships in subsequent answers. Zero external evidence and no human semantic review were manufactured.

## Required ADR and security review before merge

- Is `scope_status="unresolved"` on `ShadowSeed` the correct first-class representation, or should a distinct shadow-possibility object precede strictly atomic `ShadowSeed` objects? This implementation makes the former choice **as a proposal**, not an accepted architectural fact.
- Should every unknown-scope observation be represented as a new seed, or should truly non-investigable/hostile/raw boilerplate follow a different still-preserved non-authoritative path? Preserve rare propositions without denial or unbounded resource exhaustion.
- Review structured data contracts, export/privacy, restoration authorization and caller-facing UI labels for new records. Verify that accidental `scope_status` removal in direct, unauthenticated manager snapshot imports cannot silently up-scope an untrusted input.
- Audit every Gate-related auxiliary path, including probe feedback, SSOT validation, external audit tooling, legacy import and adversarial replay, for defensive failure behaviour instead of silent authority. This draft explicitly blocks the canonical Gate and point-of-use; not all clients are yet certified.
- Independently review exact-match identity versus semantic recurrence, and the consequences of unresolved memory accumulation.
- Preserve separate `born`, `reobserved`, `revived`, `bounded`, `promoted` and `expired` events, without treating any as proof of model-internal novelty.

## What this does *not* change

The full two-part [possibility-space thesis](../possibility-space-thesis.md) remains intact. The user's main goal is **Shadowseed Pro**. The historical Shadow Seed Learning vision is provenance, not runtime authority. No change to default Gate policy, trace/TTL thresholds, use-time permission, model weights, or research review blinding. No unrelated NeSy changes. Existing PR #260 (the prompt-based 48-call pilot) and PR #261 (read-only 46-candidate fate audit) remain separate and unmerged.

**Decision requested before merge:** accept, refine, or reject this extension to ADR-002. Until then the feature branch is a tested technical proposal, not shipped Pro behavior.
