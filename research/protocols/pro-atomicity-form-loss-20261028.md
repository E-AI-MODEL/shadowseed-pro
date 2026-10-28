# Shadowseed Pro: kandidaatverlies door atomiciteitsvormregels

**28 oktober 2026 | Status:** ruwe bronanalyse en reproduceerbare mechanische controle. Geen waardeoordeel, geen nieuwe LLM-proef, geen wijziging van productie-intake of Validation Gate. Gebaseerd op het oorspronkelijk opgeslagen `observed.json` van [Actions-artifact 12754935105](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40542431712), SHA-256 `0a5094e38ab2fdcf8c68dc8d6a3c75d29eeffd49e1f6c8e138589ed73ca36bbf`.

## De vastgestelde tegenstrijdigheid

[ADR-002](../../docs/architecture/adr/ADR-002-epistemic-seed-contract.md) definieert *atomair* als **één zelfstandig onderzoekbare epistemische kandidaat**. Een vaste woordlimiet, komma, voegwoord of lexicale drempel is volgens dezelfde geaccepteerde ADR **niet** de definitie. Een candidate die een relatie tussen meerdere variabelen noemt, kan nog steeds één onderzoekbare vraag bevatten. Andere kandidaten zijn daadwerkelijk meervoudig en mogen niet zomaar één seed worden.

De actuele `src/shadowseed/intake.py` behoudt voor niet-vraagvormige Nederlandse kandidaten een historische separator- en woordenlijst. `src/shadowseed/atomicity.py` laat een enkel zichtbaar vraagteken juist ruim toe. Dit veroorzaakt een **vormgevoelige geboortegrens**, zelfs bij inhoudelijk vergelijkbare kandidaten. In het modelpad van `src/shadowseed/chat.py` staat `split_broad=False`, zodat de opname niet automatisch door een lijst-split wordt gered.

## Directe herberekening uit de ruwe data

| Controle | Rechtstreeks waargenomen |
| --- | ---: |
| Detector-itemregistraties | 94 |
| Historisch als `accepted` | 48 |
| Historisch als `rejected / not_atomic` | 46 |
| `created`-events in die item-lineage | 48 |
| Afwijzingen met ten minste twee van de geconfigureerde scheidingstekens | 46/46 |
| Afwijzingen met zichtbaar meerdere zelfstandige zinnen | 0/46 |
| Afwijzingen die de **huidige** `is_atomic_seed()` zouden passeren wanneer uitsluitend de afsluitende punt door `?` wordt vervangen | 46/46 |
| Afwijkingen bij replay van huidige intakefunctie versus historisch besluit | 0/94 |

Deze tellingen zijn **geen** steekproef van 94 onafhankelijke onderzoeken. De bron bevat zes fictieve casussen met twee modellen en herhaalde beurten. Een `created`-event is geen bewezen ontdekking.

### Waarom het vraagtekenonderzoek betekenisvol is, maar geen oplossing

Bij de meetboei werd de detectoruiting over batterijspanning, bewegingssensor en tijdregistratie als `not_atomic` afgewezen. De lijst- en scheidingstekenregel ziet meerdere verbindingswoorden. De uiting beschrijft mogelijk toch één afhankelijke onderzoeksvraag. Een blind aangepast vraagteken verandert de feiten niet, maar maakt alle 46 afgewezen formuleringen syntactisch toelaatbaar. Daaronder kunnen ook échte opsommingen zitten. **Dus niet automatisch 46 seeds creëren** en ook niet ieder vraagteken als semantische atomiciteit interpreteren.

Ook andere ruwe afwijzingen beschrijven vermoedelijk één afhankelijkheid met meerdere onderdelen, zoals de vraag of A/B-batchidentiteit na een flessenwissel betrouwbaar blijft. Die voorbeelden zijn onderzoeksmateriaal, geen gevalideerde nuttige discoveries.

## De precieze schade: niet gewist, wél uit de operationele schaduw

De originele kandidaattekst en observation provenance blijven beschikbaar in de `candidate_observations` en `intake_diagnostics` van de oorspronkelijke rapporten. Een `rejected`-item heeft echter **geen geboren seed-ID**, neemt niet deel aan seed-lifecycle, TTL/TrTL of toekomstige recurrence, en kan geen Gate-besluit krijgen. Het materiaal wordt dus niet noodzakelijk van schijf verwijderd, maar de mogelijkheid verdwijnt uit de **operationele Shadowseed Pro-onderzoeksketen**.

De eerste prioriteit is dit risico **zichtbaar en herstelbaar** maken zonder het systeem op vertrouwen te laten promoveren. Het is wetenschappelijk onjuist om onmiddellijk te zeggen dat de 46 afwijzingen 'goud' zijn. Wat aantoonbaar gebeurt: de intake sluit een vormafhankelijke klasse van kandidaten uit vóór meerturnsontwikkeling kan worden waargenomen.

## Onderzoekslijn, zonder voorselectie op waarde

1. **Bevries de ruwe observatie.** Bewaar elke detectoroutput met originele tekst, herkomst, context, detectorvariant, normalisatie, oorspronkelijke afwijsreden en observation-ID. De bestaande ledger vormt hiervoor het vertrekpunt.
2. **Leg een read-only reconsideration-lijst aan.** Selecteer `not_atomic`-afwijzingen voor nader semantisch onderzoek. Dat is *geen* nieuwe seedstatus of automatisch toegelaten productseed. Houd originele tekst en alle afhankelijke begrippen samen.
3. **Classificeer alleen de vormvraag:** één onderzoekbare afhankelijkheid, meerdere losstaande kandidaten, niet te bepalen. Geen oordeel over waarheid, originaliteit, waarde of opbrengst. Het is toegestaan om geen beslissing te nemen.
4. **Herkomstgestuurd alternatief:** uitsluitend waar onafhankelijke toetsing een afzonderlijk onderzoekbare kandidaat aanwijst, kan een **nieuwe** gewichtloze onderzoeksrepresentatie worden voorgesteld met eigen ID en verwijzing naar de oorspronkelijke observatie. Overschrijf de originele seed of observatie niet. Voor productie geldt nog steeds eerst ADR-/veiligheidsreview.
5. **Vergelijk verlies en ongewenste opname op ruwe bronteksten**, óók in Engelstalige en negatieve casussen. Geen automatische verruiming gebaseerd op deze geselecteerde 46 afwijzingen. Meet parserfouten, gesplitste contextafhankelijkheden, onterecht samengevoegde onderdelen en valse herhalingen apart.
6. **Pas daarna** echte meerturnsontwikkeling volgen in de bestaande Pro-runtime en vergelijken met gewone generatie, gewone notities en een kandidaat-specifieke controle.

### Koppeling met filosofische hoofdvraag

De oorspronkelijke [tweedelige Pro-onderzoeksthese](../../docs/research/possibility-space-thesis.md) blijft intact. Een vormafwijzing kan een later onderzoekbare mogelijkheid voortijdig uitsluiten, maar bewijst niet dat de relatie nieuw was in het model. De tweede vraag gaat over verandering in wat latere context mogelijk maakt. Die ontwikkeling kunnen we niet observeren voor kandidaten die nooit een actieve onderzoeksmogelijkheid kregen. Dit is een beperking van het **meetinstrument**, geen bewijs voor of tegen de filosofie.

## Reproduceren (lokaal, zonder modelcalls)

```bash
PYTHONPATH=src python research/scripts/pro_atomicity_fate_audit.py \
  --observed /restricted/observed.json \
  --output /restricted/aggregate.json \
  --private-items /restricted/PRIVATE_item_fate.json
PYTHONPATH=src pytest -q research/tests/test_pro_atomicity_fate_audit.py
```

Het script eist de exacte SHA-256 van het originele artifact en schrijft alleen geaggregeerde tellingen in de gewone uitvoer. De optie `--private-items` schrijft de oorspronkelijke kandidaatteksten uitsluitend naar een door de auteur gekozen niet-publieke map. **Upload `observed.json`, `PRIVATE_item_fate.json`, de blinde reviewbestanden of owner-unblind nooit naar een publieke PR.**

## Beslissing voor deze PR

**Documenteren en afzonderlijk instrumenteren: JA.**  
**Bestaande atomair-/Gate-/dedup-/TTL-/TrTL-runtime wijzigen: NEE, nog niet.**

Er is nu aantoonbaar een implementatiegrens die een substantieel deel van de detectorkandidaten afhankelijk van de schrijfvorm uitsluit. Eerst een semantisch gecontroleerde reparatie met behoud van identiteit en zonder binnensmokkelen van extra autoriteit, daarna een afzonderlijk productbesluit. Ook een 'weigering om te oordelen' moet geldig blijven.
