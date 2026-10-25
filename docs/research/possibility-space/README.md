# Shadowseed possibility-space research — questions, sources, rival mechanisms

> **Status:** open research program; no demonstrated Q1/Q2 efficacy or accepted architecture change.
> **Updated:** 2026-10-25 following first-principles review.
> **Question authority:** [Verbatim Dutch thesis](../possibility-space-thesis.md), with **both clauses** intact. No narrower paraphrase or experiment can replace it.

## Stap 1: modelvermogen, gap-detectie en gewichtloze geboorte

- **[Uitgebreid onderzoek: van modelsignaal naar gap en seed](step1-model-signals-gap-origin-2026-10-25.md)** — code en oorspronkelijke H-Neurons-bronnen naast elkaar; modelrollen, detector v0.6/generative, ruwe kandidaat tot seed, echte meerturnslevenscyclus en mogelijke modelinterne metingen. Dit is een onderzoeksontwerp, geen bewezen Q1/Q2-uitkomst of vrijgave voor nieuwe betaalde runs.
- **[Bronnen en bewijsoverzicht voor stap 1](step1-evidence-register-2026-10-25.md)** — onderscheid tussen uitgevoerde proeven, beoordelingen door andere LLM's, oude nulresultaten, niet-gemergede prototypes en nog ontbrekende onafhankelijke controles.
- **[Technische vergelijking met H-Neurons](step1-h-neurons-method-crosswalk-2026-10-25.md)** — originele activatiemeetmethode, CETT, nieuwe kritische controles, E1 versus E2 en de eis dat kandidaat/label pas na originele generatieactivaties ontstaat. Dit is een onderzoeksvoorstel, geen neuronresultaat.
- **[Stap-1 meetinstrument met echte detector/intake](step1-gap-birth-instrument-2026-10-25.md)** — offline, volledig vooraf vastgelegde model- en detectorantwoorden; daadwerkelijke productparser, observe_turn, intake, gewichtloze seedgeboorte, eventlogs en oorspronkelijke promptversies. Geen werkelijke modeldetectie, geen modelcalls en geen wetenschappelijke effectclaim.
- **[Methodische EAI Blindspot-audit van Q1/Q2 en stap 1](step1-eai-blindspot-method-audit-2026-10-25.md)** — uitsluitend een interne controle op bronfit, rol/herkomst, parser- en evaluatorselectie, latere causaliteit, gewichtloos onderzoek en de verschillende feedbackregels in de protocollen. Geen EAI-rubric als gapfilter, geen nieuwe proef, geen onafhankelijke G0-goedkeuring.

## Current reading order (start here)

1. **[Fundamental question](../possibility-space-thesis.md)** — canonical, literal Dutch wording and honest scientific claim boundary.
2. **[First-principles reorientation](first-principles-reorientation-2026-10-25.md)** — **current conceptual framework**: five distinct meanings of possibility, the source-to-hypothesis leap, H0–H5 rival mechanisms, and what would eliminate each.
3. **[Source-to-claim audit](source-claim-audit-2026-10-25.md)** — what original SSL 4.5/4.6, Pro ADRs and primary papers actually support, and where earlier readings overclaimed.
4. **[Annotated research literature](literature-map-2026-10-24.md)** — 17 source entries, including 2026-10-25 additions. Theory, experimental observations and non-conclusions are separated; papers linked rather than copied as PDFs.
5. **[Amended Q1/Q2 proposal](revised-q1-q2-experiment-2026-10-25.md)** — **current candidate experimental contract**, not implemented or preregistered. Q2 can involve reframing, conditions, meaning, dependencies, tests, constraints and optionally new relation kinds. G0 requires at least two distinct mechanisms and negative cases **before model calls**.
6. **[G0 internal rejection of F1/F2](g0/internal-adversarial-audit-2026-10-25.md)** — author-side **NO-GO**: both measure mainly conventional diagnosis/planning, with author-provided capabilities and follow-ups. Technical examples are retained as [historical calibration material](g0/README.md); the unfilled reviewer form remains unfilled.
7. **[F3/F4 challenger designs](g0/redesign-v2-candidate-mechanisms-2026-10-25.md)** and **[formal self-check + blockers](g0/v2-review-and-selfcheck-2026-10-25.md)** — order-composition and jointly informative observations have checkable nulls but may merely test well-known algebra and feature engineering; **not approved or run**.
8. **[Current G0 method proposal: model-originated dynamic inquiry](g0/dynamic-inquiry-protocol-candidate-2026-10-25.md)** — move from scripted answer chains to bounded environments accepting many **model-proposed prospective questions**, independently checked against held-out consequences, with strong model/ordinary notes/weightless memory and exact-candidate-ablation controls. **No approved evaluator, independent review, preregistration or new model calls yet.**

## Adapter framing and readiness checks (still unapproved)

- **[LLM-adapter positioning](adapter-not-model-improver-2026-10-25.md)** — existing external memory/validation interface versus an *unproven* possibility-inquiry process. The host model and its credentials stay separate from the adapter; this is not an accepted ADR or a model-fine-tuning method.
- **[External environment feasibility](g0/external-benchmark-feasibility-2026-10-25.md)** — primary-source screen of DiscoveryWorld, DiscoverPhysics, WorldTest, AgentIdeaBench, Into the Unknown and ScienceWorld, with an explicit *not yet verified at code/API level* boundary.
- **[G0 codecontrole externe onderzoeksomgevingen](g0/external-executor-source-audit-2026-10-25.md)** — gepinde upstream-bronnen en veiligheidsgrenzen. De daaropvolgende [DiscoveryWorld-interface-rooktest](../../../research/scripts/g0_discoveryworld_smoke.py) **is inmiddels modelvrij uitgevoerd en gereproduceerd** (PR #230); dat is geen onafhankelijke Q2-validatie.
- **[Modelvrije G0-calibratie van onderzoeksvragen](g0/open-inquiry-interface-calibration-2026-10-25.md)** — vervolgproef met expliciete vrije onderzoeksvragen, gescheiden toolaanvragen, tijdcontrole, afwijzingen en vragen buiten het evaluatiebereik. *Onderzoeker-geschreven calibratie, niet model-originated of G0.*
- **[G0-product-naar-wereld-meerturnsbridge](g0/real-shadowchat-discoveryworld-bridge-2026-10-25.md)** — verbindt de echte gewichtloze ShadowChatSession-pijplijn met de echte externe omgeving en een expliciete detector-NONE controle, via vier gescheiden turns; onderzoeker-scripted, nul modelcalls, geen bewijs voor Q1/Q2 en geen aanpassing aan Gate/TTL/TrTL.
- **[G0-blindreview voor nieuwe vervolgvragen](g0/blind-later-inquiry-review-handoff-2026-10-25.md)** — bouwt geblindeerde bewijskaarten uit echte meerturndata, ondersteunt twee onafhankelijke menselijke beoordelingen en ontblind pas achteraf. Verbergt geen modeltekort, publiceert geen private armkeys en kent geen automatische Q1/Q2-score of G0-status toe.
- **[Correctie: gewichtloze shadow-route bestond al](g0/weightless-inquiry-causal-boundary-2026-10-25.md)** — controle van het oorspronkelijke 'schaduw die meereist'-ontwerp tegenover product-Engine, lifecycle/TrTL, open vectorzoekruimte, SSOT-validatie en Gate. De beoogde nieuwe onderzoeksrol is niet gebouwd; eerst meten wat de bestaande code werkelijk doet. G0 niet geslaagd.
- **[Matched-model adapter contract](g0/adapter-evaluation-contract-2026-10-25.md)** — exact A/B/C/D/E controls, genuine weightless cross-turn persistence, fair total budgets, independent later-question validation and candidate ablation. Research proposal only, NOT G0 approval or permission to run paid models.

## Narrow compression-retention research (NOT a replacement thesis)

- **[Compression-retention mechanics and prospective study](compression-retention-narrow-pilot-2026-10-25.md)** — a separately labeled, offline calibration test using canonical candidate birth and vector retrieval. Investigator-authored summaries and candidates, no model calls, no result about Q1 or Q2. Details matched strong-model controls for a *future* independently reviewed study without claiming G0 approval.

## One-shot exploratory live compression pilot (not Q1/Q2 evidence)

- **[Bounded GPT-5 engineering protocol](live-compression-retention-engineering-pilot-2026-10-25.md)** — synthetic cases, prospective freeze of model-generated candidates and genuine model-produced summaries, real embedding retrieval, ordinary notes and a negative control. This is a technical feasibility run only, without independent G0 review, equal total call budgets or scientific discovery claims.
- **[Completed live GPT-5 result](live-compression-retention-result-2026-10-25.md)** — 30 model calls, 3 real embedding requests, no Gate events, and a NON-DISCRIMINATING outcome: the ordinary model's first answer and compressed summaries already retained both relevant hypotheses. No Shadowseed effect or new possibility-space claim established.

## Historical reasoning, decisions and failed trial — keep intact

- **[Conversation reconstruction and user corrections](conversation-record-2026-10-24.md)** — chronology of the recoverable discussion; **not** a literal full transcript.
- **[Earlier elimination of directions](course-elimination-2026-10-24.md)** — historical method comparison, including the correction that FunSearch is not a direct Shadowseed competitor.
- **[Initial experiment proposal](first-discriminating-experiment.md)** — superseded draft, preserved so its narrowing is visible.
- **[GPT-5 fixed-edge pilot failure record, PR #220](https://github.com/E-AI-MODEL/shadowseed-pro/blob/research/possibility-pilot-20261024/docs/research/possibility-space/first-live-pilot-result-2026-10-24.md)** — 24 genuine API calls, 16 parseable, 8 incomplete; more fundamentally the test measured fixed-rule missing graph edges rather than the thesis. Raw artifacts preserved, no claim of proven or disproven SSL.

## Current findings and decision boundary

- **Q1 remains unproved.** Failing to generate a relation is not evidence that a model knows its own absence or that the relation is outside its representational ability.
- **Q2 remains unproved.** A new type of edge is neither necessary nor automatically sufficient for a changed space of meaningful, subsequently investigable possibilities.
- **The existing product's true distinctive asset is an implemented boundary between observed, weightless candidates and trusted influence.** This is not yet proof that its persistent shadow has a discovery advantage over ordinary notes, deliberate exploration or a strong LLM.
- **No winner yet among H0–H5.** A powerful ordinary model, decoding/selection effects, internal interventions, weightless cross-turn memory, conceptual reframing, and human/environment interaction all require fair discriminatory tests.
- **G0 status — NOT PASSED:** F1/F2 **rejected as main thesis cases** by internal self-audit, F3/F4 **blocked by remaining construct-identifiability risk** despite correct toy math, and E1/E2 **proposed as dynamic inquiry method** without an implemented or independently accepted evaluator. A version-specific independent review, prospective question-validation criteria and true post-preregistration holdouts are required **before any more model calls**.
- **No new production changes or paid calls from this review.** Existing Gate/point-of-use rules and accepted ADRs remain authoritative. The [historical v0 pilot workflow](https://github.com/E-AI-MODEL/shadowseed-pro/pull/220) was made manual/offline-only; its failure must not be hidden or rerun as if it were the current study.

Related [original 2026-06 generative vision](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md) and [accepted Pro ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md).

**This folder is for continuity, source scrutiny, and test design — not a code implementation order or a claim that Shadowseed has demonstrated possibility-space expansion.**

- **[G0: overeenkomst versus bewijsrichting in bestaande SSOT](g0/ssot-polarity-support-vs-relevance-2026-10-25.md)** — falsificatieproef met echte Manager/SSOT/Gate, fictief ondersteunende en tegengestelde broninhoud, plus een niet-geverifieerde controle. Geen productwijziging of Q1/Q2-conclusie.
