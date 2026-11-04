# ShadowSeed Research Atlas

**Startpunt voor het onderzoek, niet voor de productcode.** Stand: 4 november 2026.

De Atlas maakt historische experimenten en hun uitkomsten vindbaar. De 34 bevindingen zijn geen 34 onafhankelijke effectstudies. De 13 verbanden zijn nieuwe onderzoeksvragen, geen bewezen causale relaties. De vergelijking van 24 tweebeurttrajecten is niet-blind gecodeerd en komt uit twee momenten van één fictieve casus.

## Direct naar de gegevens

| Wat zoek je? | Bestand |
| --- | --- |
| 34 bevindingen (S01-S34), elk met bron, meetstap en bewijsgrens | [Onderzoeksregister](data/atlas.json), [originele CSV](sources/34_bevindingen_bronafhankelijkheid_2026-11-04.csv) |
| 13 verbanden (R01-R13), met tegenverklaringen en vervolgvraag | [Verbanden in hetzelfde register](data/atlas.json), [originele CSV](sources/verbindingskaart_tussen_34_bevindingen_2026-11-04.csv) |
| 24 historische trajecten, samengevat als acht groepen | [Vergelijkingsgegevens](data/atlas.json), [originele CSV](sources/24_trajecten_vergelijkingsmatrix_2026-11-04.csv) |
| De inhoudelijke kruisanalyse, inclusief negatieve resultaten | [Onderzoeksnotitie van 4 november](notes/synthese-2026-11-04.md) |
| De oorspronkelijke 48 modelantwoorden en herstelbestanden | [Bronarchief 28 oktober](../datasets/2026-10-28-q1q2-48/README.md) |
| Vier Git-histories, vier snapshots en 62 originele Actions-artifacts | [Bronarchief 27 oktober](../../docs/research/archives/2026-10-27/README.md) |
| Historische onderzoeksprotocollen, verslagen en open problemen | [Bestaande onderzoeksindex](../../docs/research/README.md) |
| Branches en bijbehorende PR's, stand 28 oktober | [Gedateerd branchregister](../../docs/research/possibility-space/branch-register-2026-10-28.md) |

## Wat blijft waar staan?

De productcode blijft onder src/shadowseed/. De scripts en tests van het onderzoek blijven onder research/. De originele modeluitvoer blijft onder research/datasets/ en in de aangewezen archieven. Eerdere beoordelingsrondes blijven onder benchmarks/. Gedateerde onderzoeksverslagen blijven onder docs/research/.

Onder research/atlas/ bewaren we **afgeleide registers, de oorspronkelijke CSV-werkbestanden van deze analyse en gedateerde notities**. De ruwe modelantwoorden blijven in hun oorspronkelijke archief. We verplaatsen geen historische bronbestanden, wijzigen geen brondata en breken geen bestaande links. De [uitleg bij de data](data/README.md) beschrijft hoe de velden tot stand kwamen.

## Nieuwe bevinding toevoegen

Noteer altijd de oorspronkelijke run, bron of commit, welke handeling werkelijk is gemeten, op welke versie de bevinding betrekking heeft en wat niet is vastgesteld. Leg vast welke andere bevindingen dezelfde oorspronkelijke data gebruiken. Een tegenvoorbeeld hoort erbij. Nieuwe analyses krijgen een eigen datum: oude observaties en uitkomsten worden niet overschreven.

Een niet-afgeronde onafhankelijke beoordeling is een beperking op een bevestigende claim, geen reden om waarnemingen weg te gooien of al het verkennende onderzoek stop te zetten.

Dit overzicht werkt rechtstreeks via GitHub. Er is **geen MCP-server of aparte hosting** nodig.
