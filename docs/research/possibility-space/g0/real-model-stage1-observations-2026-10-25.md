# GPT-5 in de echte Shadowseed-meerturnsroute: eerste waarnemingen

> **Uitgevoerd op 25 oktober 2026.** [Eenmalige GitHub Action #40215854335](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40215854335) op commit `89d8a0f3e3817618b07b2bbc58e53028112c0150`. De ruwe `observed.json` staat als artifact bij die run. Dit verslag is *na* de modelproef geschreven. Geen vooraf vastgelegde effectscore, geen onafhankelijke beoordeling. **G0 NOT PASSED; Q1 en Q2 onbewezen.**

## Wat werkelijk draaide

- **20 complete GPT-5 Responses-aanroepen**, allemaal door de provider gerapporteerd als `gpt-5-2025-08-07`; 19 embeddingaanroepen met `text-embedding-3-small`; **36.998 geregistreerde input-/output-/embeddingtokens**.
- Twee door de onderzoeker geschreven, publieke fictieve casussen, ieder vier opeenvolgende `prepare_turn → hostantwoord → observe_turn`-beurten. Per casus twee extra gewone T0-antwoorden vóór de eerste detectie.
- De **echte** `OpenAIDetectorBackend(current_pair)`, canonieke parser, normalisatie, intake en blijvende `ShadowseedEngine` zijn gebruikt. De eerste nieuwe seed werd direct via de bestaande geboortefunctie vastgelegd; per latere beurt is het research-only checkpoint van PR #249 gebruikt.
- Een afzonderlijke **NONE-controle** met de bestaande Engine kreeg exact dezelfde hostantwoorden. Deze controle toetst technische afscherming, niet de toegevoegde inhoudelijke waarde van Shadowseed.
- Alle onderzoeksseeds bleven op **gewicht 0, evidence_count 0, authority_version 0**. Geen seed in de gewone antwoordcontext, geen toegestane invloed, geen Gate-promotie. Het verschil tussen werkelijk hostmodel en productinterne seed is mechanisch geregistreerd.

| Waarneming | MEASUREMENT | STERILE | Totaal |
| --- | ---: | ---: | ---: |
| Gespreksbeurten | 4 | 4 | 8 |
| Losse detectorvoorstellen | 12 | 12 | 24 |
| Geaccepteerde nieuwe seeds | 4 | 7 | **11** |
| Afwijzingen (`not_atomic`) | 8 | 5 | **13** |
| Detector retourneerde expliciet `NONE` | 0 | 0 | 0 |
| Eerste gewichtloze seedgeboorte | T0 | T0 | beide T0 |
| Hernieuwde detectie van de eerste seed | 0 | 0 | 0 |

Beide eerste seedgeboorten zijn volgens de opgenomen canonieke raw-item/intake/`created`-registratie mechanisch traceerbaar. De eerste seed bleef daarna drie beurten bestaan met afnemende trace, zonder extra occurrence, Gate-gewicht of gewone antwoordinvloed.

## Wat inhoudelijk opvalt

De meetcasus leverde vier geaccepteerde seeds op. De eerste ging over de mogelijkheid dat mechanische montage of directe sensoromgeving de verschillen tussen kanalen veroorzaakt. Het zichtbare GPT-5-antwoord had op T0 zelf al meerdere alternatieve verklaringen, waaronder tijdsynchronisatie, voeding en filtering. We kunnen deze eerste seed niet beschouwen als een door het model **niet gekende of onbereikbare** relatie; die claim is niet gemeten.

De lage-onderzoeksbehoeftecontrole (`STERILE`) leverde juist **zeven** geaccepteerde seeds op. Eén voorstel stelde zelfs dat het aantal twintig onvoldoende door gegevens was onderbouwd, hoewel het getal twintig uitdrukkelijk in de fictieve startbeschrijving stond. Dat is reden voor voorzichtigheid bij het tellen van 'gevonden open mogelijkheden'. Zeven aanvaarde zinnen zijn geen zeven waardevolle of nieuwe onderzoeksrichtingen.

De dertien `not_atomic`-afwijzingen zijn productwaarnemingen, **geen** onafhankelijke aanwijzing dat de geweigerde voorstellen inderdaad inhoudelijk niet-atomisch waren. De detector stelde in alle acht beurten precies drie voorstellen voor; of dat door promptgedrag, casuskenmerken of werkelijk bestaande onzekerheden komt, is nog niet vastgesteld.

## Belangrijke meetfout in deze eerste verkenning

De test-harness stuurde de volledige `case.context` aan het **hostmodel**, maar gaf op T0 aan `ShadowseedEngine.prepare_turn` alleen de nieuwe gebruikersvraag door. Daardoor ontving de bestaande `current_pair`-detector wel het **hostantwoord**, maar niet de volledige oorspronkelijke informatie waarop dat antwoord was gebaseerd. Latere detectorbeurten zagen alleen de begrensde gewone gesprekshistorie en de nieuwe externe waarneming, niet de oorspronkelijke volledige casus.

Dit is een fout in **deze research-adapter**, niet aangetoond als een defect van de canonieke productdetector. Sommige gemelde 'gaps' kunnen simpelweg ontstaan door een ongelijke informatiepositie. Het T0-voorbeeld met de twintig dozen illustreert dat concreet. De negatieve controle was ook niet werkelijk vrij van uitnodigingen tot extra onzekerheden: een vervolgvraag vroeg letterlijk wat nog onbekend was, terwijl de algemene hostinstructie vroeg onzekerheden te benoemen.

**Gevolg:** de uitkomst ondersteunt mechanische uitvoerbaarheid van echte GPT-5-detectie en gewichtloos meereizen, niet de kwaliteit van het signaleren van niet-gekozen mogelijkheden. Een volgende **vooraf vastgelegde, als verkennend gelabelde** context-pariteitsproef moet de informatie die werkelijk voor de host beschikbaar was ook voor de detector zichtbaar maken, zonder de productregels of kandidaatacceptatie achteraf te repareren.

## Wat hier niet getest is

- Niet de interne neurale activaties, H-Neurons of de waarschijnlijkheidsmassa van niet-uitgesproken relaties.
- Geen door GPT-5 zelfstandig ontworpen *latere* onderzoeksvraag als afzonderlijke research-actie. De vier gebruikersvragen en de nieuwe waarnemingen waren vooraf door de onderzoeker geschreven.
- Geen onafhankelijke algemene uitvoerder van nieuwe vragen, geen tweede-orde toets en geen blind oordeel.
- Geen kosten-gelijke A/B/C/D/E-vergelijking met bewuste divergente generatie, gewone notities of kandidaatablatie; dezelfde hostantwoorden in een NONE-Engine leveren daarvoor geen geldig substituut.
- Geen G0-toestemming of wetenschappelijk effectbewijs.

De onafhankelijke G0-v3-review blijft open. Dit resultaat wordt niet gebruikt als bewijs voor Q1 of Q2 en corrigeert niets aan Gate, SSOT, TTL/TrTL, modelrollen of productdetector. **Het bruikbare resultaat is een echte, controleerbare technische proef plus een aantoonbare informatie-asymmetrie die de volgende onderzoeksopzet moet herstellen.**
