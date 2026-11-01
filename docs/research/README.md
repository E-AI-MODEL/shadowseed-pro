# Onderzoek Shadowseed Pro: waar beginnen? (28 oktober 2026)

> **Momentopname, geen vastgestelde onderzoeksuitkomst.** Dit overzicht is geschreven op 28 oktober 2026 en ordent de op dat moment zichtbare bronbestanden, uitgevoerde metingen, niet-afgeronde beoordelingen en open voorstellen. De bronbestanden en oudere conclusies blijven ongewijzigd. Later bewijs hoort als nieuwe, gedateerde laag naast deze momentopname.

## Research update — 29 October 2026

The [27 October public source release](https://github.com/E-AI-MODEL/shadowseed-pro/releases/tag/research-archive-2026-10-27) preserves four Git histories, four source snapshots and 62 original Actions ZIPs. [Archive guide and verified SHA-256](archives/2026-10-27/README.md). The original outputs of the [48-call pilot from 28 October](../../research/datasets/2026-10-28-q1q2-48/README.md) are separately preserved in `main`. These are primary sources, **not** 62 or 48 independent measurements of scientific effect.

The [preprint evidence position](preprint-evidence-position-2026-10-29.md) maps the historical working-draft assumptions to what the raw records and current implementation actually support. It explicitly describes the **real progress**—working weightless memory, observable multi-turn candidate histories, an audited form-sensitive intake boundary and improved source traceability—without treating single-AI-rater value labels, different answers or zero-exposure controls as proof of a Q1/Q2 effect. The earlier 25–28 October texts remain below unchanged as dated research history.

## De vraag blijft leidend

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

Dit is de letterlijke Nederlandse onderzoeksvraag uit [de oorspronkelijke these](possibility-space-thesis.md). De vraag gaat niet uitsluitend over ontbrekende feiten, een gemiste relatie, tekstkwaliteit, een hoger percentage goede antwoorden of het vaker herhalen van een seed. Een mogelijk nieuwe onderzoeksvraag telt niet automatisch als een verandering in wat later onderzocht kan worden.

## Openbare brondata van de 48-call-proef (28 oktober 2026)

De volledige [oorspronkelijke onderzoeksbestanden, antwoorden, reviewbestanden, herstelcode en ZIP-archieven](../../research/datasets/2026-10-28-q1q2-48/README.md) zijn in de publieke GitHub-geschiedenis opgenomen, inclusief SHA-256-controlebestand. De onderzoeker heeft ook vrijgave van de historische RSA-herstelcode en ontblindingskoppelingen gevraagd. **De oorspronkelijk blinde toewijzing is hiermee openbaar**, zodat een latere beoordeling niet als blind ten opzichte van dit vrijgegeven bestand kan worden beschreven. Dit verandert niets aan de oorspronkelijke 48 modelantwoorden of het feit dat er toen nul onafhankelijke menselijke semantische beoordelingen waren.

## Openbare historische bronarchieven (27 oktober 2026)

Het [oorspronkelijke pakket met 62 GitHub Actions-artifacts en vier repositorygeschiedenissen](https://github.com/E-AI-MODEL/shadowseed-pro/releases/tag/research-archive-2026-10-27) is inmiddels als volledige, ongewijzigde ZIP openbaar gepubliceerd. Het archief is 87.841.733 bytes en heeft een [geverifieerde SHA-256 en een bronregister](possibility-space/historical-source-archive-release-2026-10-28.md). **Dit is een afzonderlijk historisch archief** naast de leesbaar opgenomen 48-call-proef van 28 oktober; geen van beide wordt opgeteld tot nieuwe onafhankelijke experimenten.

## Leesvolgorde

- **Oorspronkelijke vraag en grenzen:** [possibility-space-thesis.md](possibility-space-thesis.md). Deze tekst blijft leidend; ook de tweede helft van de vraag.
- **Ontwikkeling van de methode tot 25 oktober:** [onderzoeksindex, stand 25 oktober](possibility-space/README.md) en [heroriëntatie op de eerste principes](possibility-space/first-principles-reorientation-2026-10-25.md).
- **Wat nu rechtstreeks geobserveerd is:** [de uitgebreide samenvatting boven in de hoofd-README](../../README.md#what-we-understand-now-28-october-2026), met verwijzingen naar primaire runs en hun grenzen.
- **Alle branches en open PR's:** [branchregister van 28 oktober](possibility-space/branch-register-2026-10-28.md). Bevat alle 166 op het moment van inventarisatie aanwezige remote branchrefs en de afzonderlijke open PR-ketens.
- **Onderzoeksarchief van 27 oktober:** [bron-resultatenkaart](possibility-space/retrospective-evidence-map-2026-10-27.md), [historische PR-kaart](possibility-space/research-branch-map-2026-10-27.md) en [publicatie- en reviewstatus](possibility-space/publication-readiness-2026-10-27.md), sinds [PR #259](https://github.com/E-AI-MODEL/shadowseed-pro/pull/259) beschikbaar in `main`. De oorspronkelijke datering blijft behouden.
- **Afzonderlijke 48-call-proef van 28 oktober:** [concept-PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) bewaart protocol, bron-SHA, onderzoeksrunner en uitvoeringsverslag op een aparte branch. De proefgegevens zijn in de huidige onderzoeksingang beschreven; de PR is niet gemerged.
- **Controle van overlappende indexwijzigingen:** [PR #259, #260 en #264 naast elkaar](possibility-space/index-samenvoegcontrole-2026-10-28.md), met een gecontroleerde tekstuele samenvoeging en een veilige volgorde voor latere integratie.

## Wat de bronrecords wel en niet zeggen

| Onderdeel | Waargenomen en geregistreerd | Nog niet vastgesteld |
| --- | --- | --- |
| **Herkomst en reconstructie** | Het afgeleide, door de eigenaar beheerde register bevat 220 turnrecords over 40 opeenvolgende trajecten en 1.224 kandidaatvoorkomens. De reconstructie controleerde 220/220 stage-indexen. Er zijn 368 exacte joins, 96 modelnaamverschillen en 760 voorkomens zonder passende stage-rij in dit register. | Geen onafhankelijke reconstructie van alle 62 oorspronkelijke Actions-archieven, geen 40 onafhankelijke proeven en geen semantisch oordeel over niet-gematchte tekst. [Concept-PR #263](https://github.com/E-AI-MODEL/shadowseed-pro/pull/263). |
| **Ruwe kandidaat naar intake** | Voor de oorspronkelijke 27-oktoberbron bereikten alle 94/94 genummerde kandidaatregels de canonieke intake. Daarvan werden er 48 geaccepteerd en 46 als `not_atomic` afgewezen. Bij die 46 was de regel voor meerdere scheidingstekens vormgevoelig. | De afwijzing bewijst niet dat die 46 inhoudelijk onbruikbaar zijn; doorgang bewijst evenmin dat ze goed of waar zijn. Het zijn 12 afhankelijke model/casustrajecten, niet 94 onafhankelijke proeven. [Concept-PR #261](https://github.com/E-AI-MODEL/shadowseed-pro/pull/261). |
| **Gewichtloze bewaring** | Een lokale, deterministische herhaling in [concept-PR #262](https://github.com/E-AI-MODEL/shadowseed-pro/pull/262) maakte 46/46 historisch afgewezen uitingen aan als onbesliste seeds met gewicht 0, zonder Gate-events. | Dat is een **voorgestelde productwijziging**, nog geen geaccepteerde ADR, semantische validatie of aangetoond wetenschappelijk effect. |
| **Meerdere turns en invloed** | Echte GPT-5-trajecten, een bestaande gewichtloze seed over latere beurten en vijf op T1 modelbedachte onderzoeksvragen zijn geregistreerd. De eerdere T2-poging stopte met een fout; in een andere proef waren host- en detectorcontext ongelijk. | Geen aangetoonde toegevoegde waarde ten opzichte van gewone notities, expliciet doorvragen of een sterke modelbaseline. [PR #250](https://github.com/E-AI-MODEL/shadowseed-pro/pull/250) en [#251](https://github.com/E-AI-MODEL/shadowseed-pro/pull/251). |
| **Twee meetmomenten, 48 calls** | De gecorrigeerde, afzonderlijke proef in [concept-PR #260](https://github.com/E-AI-MODEL/shadowseed-pro/pull/260) registreert 48/48 afgeronde providerantwoorden, 24/24 complete tweeturntrajecten en 187.255 gerapporteerde tokens. | Het is één fictieve boeicasus met twee modelspecifieke meetmomenten, geen onafhankelijke tweecasussenstudie. Er zijn **nul afgeronde onafhankelijke menselijke semantische beoordelingen**. Op het moment van de uitvoering was de ruwe inhoud nog niet publiek; de originele gegevens zijn inmiddels in het openbare bronarchief opgenomen. |
| **Dual-model-meerturnsproef** | De echte eenmalige run achter [concept-PR #258](https://github.com/E-AI-MODEL/shadowseed-pro/pull/258) noteert 12 model/casustrajecten, waarvan 10 volledige T1/T2 A/B-trajecten en 2 met te late geboorte; 172 modelaanroepen en 96 embeddings. | Geen onafhankelijke menselijke beoordeling, geen bewezen Q2-effect. Deze PR staat boven op een lange onderzoeksketen en is niet direct als zelfstandige wijziging voor `main` geschikt. |
| **Downstream blootstelling** | De Qwen2.5 7B verkennende bundel registreerde 43 live kandidaatvoorkomens; in de relevante beoordelingsselectie werd geen kandidaat aan een later antwoord blootgesteld. | Zonder feitelijke blootstelling bestaan geen geldige geblindeerde A/B-antwoordparen en volgt geen bewijs voor of tegen een Shadowseed-effect. Zie de [samenvatting in de hoofd-README](../../README.md#candidate-birth-is-not-the-same-as-downstream-effect). |

## Houd de stappen uit elkaar

De volgende overgang is niet vanzelfsprekend: **ruwe modeluiting → parserherkomst → intakebesluit → gewichtloze seed → latere beschikbaarheid → daadwerkelijk tonen aan de onderzoekende modelroute → andere vraag of handeling → onafhankelijk beoordeeld gevolg**. Elke stap heeft eigen bronmateriaal, noemers, mogelijke uitval en onzekerheden. `Accepted`, `not_atomic`, `born`, `surfaced` en `promoted` zijn historische technische labels, geen onafhankelijke inhoudelijke oordelen. Behoud ook de uitingen die op geen enkele latere stap uitkomen.

Een seed die als schaduw meereist is geen bewijs dat het model meer weet. Het onderscheid tussen herinneren (`trace > 0`) en bevoegdheid (`weight = 0`) is wel bestaande software. Nieuwe kandidaattypen of toelatingsregels veranderen deze grens alleen na afzonderlijk technisch en inhoudelijk besluit.

## Wat nu openstaat

- De eerste zorg is het terugvinden en vergelijken van **oorspronkelijke** kandidaattekst, reguliere modelantwoorden, detectorcontext, intakebesluit en verdere trajecten. Het register van #263 is hulpmateriaal, geen vervanging van de primaire archieven.
- De inhoudelijke beoordeling van de 46 vormgevoelig afgewezen uitingen is nog open. Uit een technische test van bewaring mag geen oordeel over kwaliteit volgen.
- De 48-call proef en de gestapelde A/B-proeven hebben nog geen onafhankelijk afgeronde semantische beoordeling. Eventuele vergelijking vraagt expliciete, gelijke budgetten en goede controles op gewone notities, gericht zoeken, modelverschillen en het werkelijk zichtbaar worden van een kandidaat.
- G0 voor de brede Q1/Q2-vraag is **niet geslaagd**. Er is geen bewijs dat een nieuwe onderzoeksruimte is ontstaan. Negatieve, niet-onderscheidende en onvolledige resultaten blijven onderdeel van de geschiedenis.
- Een preprint blijft een **concept** zolang bronherkomst, beoordelaars, blindering en de verhouding tussen illustraties en empirische claims niet afzonderlijk zijn gecontroleerd. [Publicatiegrenzen in concept-PR #259](https://github.com/E-AI-MODEL/shadowseed-pro/pull/259).

## Wat deze documentatie niet doet

Geen code, Gate, trace, TTL/TrTL, productdefaults, bestaande ADR, onderzoeksartifact, PR-base of onderzoeksscore is veranderd. Er zijn geen nieuwe modelcalls uitgevoerd en er is niets gemerged. Dit is een ingang naar de beschikbare geschiedenis, geen herschrijving daarvan.
