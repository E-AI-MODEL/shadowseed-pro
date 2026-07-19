# AI-prescreen — round 004 (NIET menselijke review)

> **Status: hulpmiddel, geen evidence.** Dit is een prescreen door het
> Claude-assistentmodel. Het telt **niet** als `reviewer_a`/`reviewer_b` en
> **niet** als `open_set_seed_quality` (Laag C) bewijs. Menselijke reviewers
> oordelen onafhankelijk; deze notitie is bedoeld voor triage en voor het
> verbeteren van de generatie-prompt.

Canonieke data: `ai_prescreen.json` (per-seed verdict + reden + faalcodes).

## Uitkomst (54 seeds)

- accept: **22**
- borderline: **8**
- reject: **24**

Reële acceptatie ligt dus rond **40–55%**, tegenover de 0.90 die de
automatische normalisatie van het model zelf rapporteert.

## Systematische faalpatronen

1. **claim_vs_gap (15×)** — het model schrijft beweringen ("X heeft geen Y
   gedaan") in plaats van afwezigheden ("de tekst noemt Y niet"). Kostte
   TEST_0, TEST_3 en TEST_5 vrijwel volledig. Belangrijkste probleem.
2. **mistranslation (8×)** — brontermen vertaald naar onzin:
   `bovine → bovenspanen` (TEST_4, alle 5), `bloom filter → bloombestek`
   (TEST_7), `stolen cards → gereden cards` (TEST_9).
3. **false_gap (5×)** — gap claimt dat iets ontbreekt dat wél in de bron staat
   (TEST_1 ss_001: prijs; TEST_9 ss_003: besparing). Plausibel ogend maar fout,
   dus extra riskant.
4. **language_leak (4×)** — onvertaalde Engelse frasen ("stricken parent firm",
   "high-speed wireless format", "music retailers").
5. **entity_bleed (1×)** — `#36;` (niet-gedecodeerde `$`) in TEST_1 ss_001.
6. **grammar (3×)** — ontbrekende finiete werkwoorden (TEST_2 ss_003/004).

## Beste / slechtste items

- Schoonst: **TEST_11**, **TEST_12**, **TEST_1** — concrete, feitelijke berichten.
- Zwakst: **TEST_3** (narratief), **TEST_0** (zeer kort), **TEST_4** (mistransl.).

## Implicatie

Qwen-3B is grammaticaal netter dan de 1.5B uit round 003, maar **inhoudelijk
niet duidelijk beter**: claim-vs-gap en de vertaalfouten zijn structureel, niet
incidenteel. De volgende stap richt zich op het wegnemen van deze patronen in de
v0.3-prompt voordat een sterkere/grotere run zin heeft.
