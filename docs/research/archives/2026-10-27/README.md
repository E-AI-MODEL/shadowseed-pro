# Original research sources — archive of 27 October 2026

**Public release:** [Original Shadowseed research archives (27 October 2026)](https://github.com/E-AI-MODEL/shadowseed-pro/releases/tag/research-archive-2026-10-27)  
**Original ZIP:** [`shadowseed_alle_raw_artifacts_20261027.zip`](https://github.com/E-AI-MODEL/shadowseed-pro/releases/download/research-archive-2026-10-27/shadowseed_alle_raw_artifacts_20261027.zip)  
**Size:** 87,841,733 bytes  
**SHA-256:** `0c2fac002613e88dd74a8d305cb7c8078d6349fbc2c76b11042982cdeaf921d8`

The GitHub release asset's own SHA-256 digest matches the original ZIP checked during archival review. Unlike an expiring Actions run artifact, this is a **release asset** with no seven-day Actions retention setting. Its future availability still depends on keeping the public repository and release accessible.

## Nederlandse toelichting — waarom bewaren we deze bronnen?

Shadowseed onderzoekt iets wat een gewoon modelantwoord vaak uit beeld laat: mogelijke verbanden, twijfel of vragen die niet werden geselecteerd. Een niet-gekozen mogelijkheid is daarmee nog geen verborgen waarheid en ook niet automatisch waardevol. De vraag is of we zo'n mogelijkheid **zonder sturende bevoegdheid** kunnen waarnemen en bewaren, en of er in latere gespreksturns werkelijk nieuwe onderzoeksvragen door ontstaan.

In de ontwikkeling van Shadow Seed Learning naar Shadowseed Pro zijn we van vroege gap-proeven naar **herleidbare meerbeurtenobservaties** gegaan. Het systeem kan een kandidaat onthouden (`trace > 0`) terwijl die geen bevoegdheid heeft om antwoorden te sturen (`weight = 0`). De oorspronkelijke modeltekst, detectoruitspraak, intakekeuze, het verdere verloop en een eventuele daadwerkelijke invloed moeten daarom afzonderlijk bekeken worden. Die technische scheiding is een concreet onderzoeksresultaat; het is nog geen bewijs dat een model een nieuwe mogelijkhedenruimte heeft gevormd.

**Wat dit archief daadwerkelijk bevat:** de bronmomentopname en Git-geschiedenis van vier repositories plus 62 originele, destijds op te halen GitHub Actions-ZIP's. `INVENTORY.json` bevat de individuele bestandsnamen en SHA-256-controlesommen. Dit zijn **62 bewaarde artifacts, geen 62 onafhankelijke experimenten of 62 positieve uitkomsten**. Ook onvolledige proeven, beperkingen en vroegere methodische aannames zijn relevant. Door ze te bewaren kunnen we achteraf de werkelijke onderzoeksgeschiedenis lezen in plaats van één huidige conclusie op het verleden te projecteren.

Het oorspronkelijke ZIP-bestand is op de [publieke onderzoeksrelease](https://github.com/E-AI-MODEL/shadowseed-pro/releases/tag/research-archive-2026-10-27) beschikbaar. De apart gepubliceerde [48-call-proef van 28 oktober](../../../../research/datasets/2026-10-28-q1q2-48/README.md) is **een latere, afzonderlijke broncollectie** en mag niet zonder herkomstcontrole bij de 62 artifacts worden opgeteld.

**De kern:** we zijn ver gekomen in het observeerbaar maken van kandidaten, bewaargeschiedenis en onderzoekspaden. Of het bewaren van een ongekozen mogelijkheid vervolgens verandert wat *later denkbaar en onderzoekbaar wordt*, blijft de richtinggevende onderzoeksvraag. Daarom bewaren we de oorspronkelijke antwoorden en beslissingen eerst, vóór we ze beoordelen.

---

## Why these sources matter

Shadow Seed Learning asks what happens to a possible relation that does *not* appear in a model's selected answer: whether it can be noticed, retained without claiming truth, revisited in later turns, and perhaps change what becomes investigable next. That is a research question, not a statement that an LLM introspects every ungenerated possibility.

The software now offers a testable boundary between **being remembered** (`trace > 0`) and **having permission to influence an answer** (`weight = 0` initially, with separate Validation Gate and point-of-use decisions). The preserved model and workflow records make it possible to examine original candidate language alongside parser and intake decisions. This is a real research and engineering achievement, independently of any future Q1/Q2 effect estimate.

The original research question remains:

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

See the [foundational thesis](../../possibility-space-thesis.md) for its original context.

## Exact contents of the 27 October archive

The outer ZIP holds **71 members**:

| Material | Count | Contents |
| --- | ---: | --- |
| Repository `main` source snapshots | 4 | One `.tar` each for `shadow-seed-study`, `shadowseed`, `shadowseed-agent-lab`, and `shadowseed-pro` |
| Git history bundles | 4 | One `.git.bundle` each, preserving refs available at collection time |
| Original GitHub Actions artifact ZIPs | 62 | Exactly the artifact files successfully retrieved during the 27 October collection |
| `INVENTORY.json` | 1 | Path, byte size, SHA-256 and source metadata for each of the other 70 members |

The archive is **a record of what could be retrieved on that date**. It is not all historical Actions runs, and the 62 ZIPs are neither 62 independent experiments nor 62 confirmed positive results. Unavailable and previously expired artifacts could not be retroactively retrieved. The snapshots are dated sources, not the present state of `main`.

The internal `INVENTORY.json` enumerates 70 hashed members. During the 29 October archival check, each recorded member's actual byte length and SHA-256 matched its inventory entry, and the outer ZIP passed its integrity test. The release asset exposes an identical outer ZIP digest.

## How to work from the sources

1. Download the [original ZIP](https://github.com/E-AI-MODEL/shadowseed-pro/releases/download/research-archive-2026-10-27/shadowseed_alle_raw_artifacts_20261027.zip) and verify its SHA-256 against the value above.
2. Inspect `INVENTORY.json` first; it distinguishes source snapshots, Git bundles and individual original Actions ZIPs. Preserve the original filenames and SHA-256 values when extracting or comparing records.
3. For any finding, cite the **specific** original artifact, model, case, turn, source candidate and relevant processing stage. Distinguish detector output, recorded intake verdict, retained memory, actual exposure and later observed text.
4. Treat a recorded `accepted` or `not_atomic` result as an **engineering event**. It is not independent evidence that an underlying idea was true, valuable, novel or useless. A GitHub workflow reported `success` is not an independent scientific verdict.
5. Keep independent datasets separate: the [28 October 48-call original records](../../../../research/datasets/2026-10-28-q1q2-48/README.md) were published later as another source collection. Do not count them as additional files among these 62 ZIPs or merge their denominators without de-duplication and provenance.

The **positive outcome of this archiving effort** is that original outputs, source-code histories, research choices and negative or incomplete tests are now inspectable together. The research can distinguish effects of the detector, text formatting, memory, intervention and strong ordinary-model baselines rather than retroactively treating every candidate as evidence of a new possibility.

## Research interpretation and preprint

The earlier preprint drafts moved from aggregate `valuable residue` categories and numerical headline claims toward a **reproducible retrospective audit of observed stages**. Some earlier novelty/value labels were assigned by one AI rater and must remain exploratory rather than become a population estimate. Equally, an unexposed seed cannot be counted as evidence that a seed had no effect.

The current [preprint evidence position](../../preprint-evidence-position-2026-10-29.md) separates established contributions from research hypotheses, retained historical observations and the tests that would distinguish a genuine downstream change. It does not overwrite the original drafts, diagrams, raw data or previously reported outcomes.

For current navigation, start at the [research entry](../../README.md) and [main project README](../../../../README.md). The [27 October retrospective evidence map](../../possibility-space/retrospective-evidence-map-2026-10-27.md) has a different purpose from the primary archive: it is an interpretation layer, not a replacement for source text.

## Preservation

No original member of the ZIP was altered to produce this explanatory document. Preserve the release asset itself and its hash. A future research conclusion should cite the actual source bytes and the version of any derived register or code used to analyse them. This file describes the archive; it does not assert that the possibility-space hypothesis has already been demonstrated.
