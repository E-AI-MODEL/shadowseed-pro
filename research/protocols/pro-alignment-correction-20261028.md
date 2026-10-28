# Pro alignment correction: candidate, seed, relation and authority

**Date:** 2026-10-28  
**Status:** methodological correction within **Shadowseed Pro** research. No runtime modification, accepted ADR, Gate change, G0 approval, new paid model call, or efficacy finding.

## Source order

1. Current **Shadowseed Pro** implementation and accepted [ADR-002](../../docs/architecture/adr/ADR-002-epistemic-seed-contract.md), [ADR-001](../../docs/architecture/adr/ADR-001-validation-gate-authority.md) and their tests govern mechanics and authority.
2. Pro's full, verbatim [two-part possibility-space research question](../../docs/research/possibility-space-thesis.md) governs the *open scientific question*, not the implementation by assumption.
3. Earlier Shadow Seed Learning 4.5/4.6 and the June vision are historical provenance, **not** a substitute for the current Pro architecture. The name `SSL` still appears in Pro module and class names but does not mean the separate historical repository is the active study.

## Correction of an overstatement

**Invalid inference:** “A gap becomes a weightless seed, therefore a new relationship has arisen.”

**Actual Pro event:** a detector proposes a possibly investigable gap, doubt, what-if, boundary or relation. Intake may **create** a new context-bound atomic epistemic seed, **deduplicate** against an existing seed, or **reject** the candidate. A created seed has `trace > 0` and `weight = 0`. It is a retained representation of a candidate, **not** proof of truth, model-internal novelty, a newly constructed relation between seeds, or a changed possibility space. A rejected detector item is not a born seed: preserve its observation/lineage without silently granting it seed status.

ADR-002 requires **epistemic identity preservation**. An existing seed may receive further observations, recurrence and status changes, but a downstream component may not silently rewrite its original claim/question. A substantively different candidate or a relation involving multiple candidates needs separate source-traceable representation or research notation, not hidden replacement of the prior seed. Whether the product currently makes such new relations is an open empirical question, not presumed code functionality.

## Mechanism and scientific levels must not be merged

| Level | Observable Pro event | Forbidden inference |
|---|---|---|
| Detector observation | Original generated candidate, source and parser lineage | It is a reliable internal absence signal |
| Intake | Accepted+created, accepted+deduplicated, rejected | Accepted means valuable or true; rejected means scientifically impossible |
| Weightless persistence | Same seed ID in a continued session, `trace`, `weight=0`, status and TTL/TrTL | Storage alone changes host-model generation |
| Research/investigation | Newly detected or independently observed relation, provenance, external source feedback | A text association or recurrence equals conceptual growth |
| Gate and point of use | Typed support/contradiction, Gate event, specific authorization | Candidate birth or recurrence itself authorizes answer steering |
| Q1/Q2 interpretation | Matched-model/compute comparisons and independently checkable later consequences | A second prompted question proves an unreachable or transformed possibility |

A **candidate involving a relationship** is not identical to a **new relationship among existing seeds**. Neither is automatically an LLM capability unavailable during ordinary generation.

## What the 48-call pilot really tested

[PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) used two checkpoints from one fictional sea-buoy case and externally supplied candidate text in a research prompt. It was a prompt-conditioning comparison, **not** an operational test of a naturally travelling Pro seed behind the normal Gate. Do not label the prompt arm “actual SSL shadow-memory development”, count a rejected intake item as a created seed, or use second-turn hypothesis articulation as a proxy for Q2.

The REVIEW A methods note came from a **Claude AI-model reviewer**, not a human. Its aggregate interpretations are *not independent scientific findings*. Because REVIEW B has not yet submitted an independently completed set, the source note and any judgments remain **author-only**, not published on this open branch. No arm allocations or reviewer text are added here.

## Next research work, grounded in existing Pro code

1. **Source-first mechanical trace:** read `ShadowseedEngine.prepare_turn/observe_turn`, `src/shadowseed/intake.py`, `src/shadowseed/observations.py`, `src/shadowseed/lifecycle.py` and the accepted ADRs together; preserve raw rejected detector observations as observations.
2. **Actual birth versus re-detection:** record `created` versus `deduplicated`, seed IDs and lineage per original turn, including the detector-NONE arm. Never count a model-generated candidate as a born seed without a recorded create event.
3. **Travel without answer steering:** track retained seed state over true additional turns; keep Gate influence distinct from shadow research. Dormant-only TrTL reactivation in the current code cannot be equated with general cross-turn semantic re-evaluation.
4. **Possible relation formation:** observe whether separately attributable subsequent content makes a new relationship, transformation or dependence describable; preserve the original seed identity and who contributed new information. Report zero/no-new-relation cases rather than rewarding output novelty at birth.
5. **Only later interpret Q1/Q2:** compare ordinary generation, deliberate search, ordinary notes and exact candidate ablation at the same model/opportunity budget. Attribute any effect to actual retained state rather than the researcher's repeated instruction.

**No changes to production code, authority policies or branch stacking are authorized by this note.** It corrects the interpretation of prior work and the research design within Shadowseed Pro.
