# SSOT-verificatie: voorgestelde productreparatie

> 25 oktober 2026 | Draft, **geen gemergde productieaanpassing**. Aansluiting op issue [#241](https://github.com/E-AI-MODEL/shadowseed-pro/issues/241), [PR #240](https://github.com/E-AI-MODEL/shadowseed-pro/pull/240) en het read-only onderzoek in [PR #242](https://github.com/E-AI-MODEL/shadowseed-pro/pull/242). De oorspronkelijke tweeledige Q1/Q2-vraag blijft open. **G0 NOT PASSED.**

## Wat er in bestaande code fout ging

De SSOT-producer stuurde iedere voldoende vergelijkbare chunk met `status=verified` rechtstreeks als `SSOT SUPPORT` naar de bestaande Gate. Dat gebeurde ook bij de *ontkennende* voorbeelden in de gecontroleerde, fictieve proef. De originele [GitHub-run #40176388209](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40176388209) blijft het historische bewijs: twee tegengestelde bronfamilies kregen ieder vier SUPPORT-signalen en eindigden op gewicht 0,6. Dat was uitvoerbaar softwaregedrag, geen onafhankelijke waarheidstoets.

## Wat deze productbranch wijzigt

De bestaande `SSOTManager` blijft de producer, de bestaande `SSLManager` en de **enige echte Validation Gate** blijven eigenaren van autoriteit. Er komt geen extra model, onderzoeksmemory, detector, Gate, TrTL, TTL of promptlaag.

- `ingest_document` houdt document-identiteit en SHA-256 van de exacte brontekst én elke geïndexeerde chunk bij. Nieuwe broninhoud onder hetzelfde document-ID vervangt de oude chunks en maakt bestaande relatiebeoordelingen ongeldig. Veranderde chunktekst of oude chunkmetadata zonder versiehash mogen geen bewijs opleveren, ook niet met een eerdere attestatie.
- `attest_document_relation(seed_id, doc_id, relation, reviewer, rationale, evidence_unit_id)` is een **expliciete operatoractie**. De reviewer wordt als bewering opgeslagen, niet geauthenticeerd of wetenschappelijk gevalideerd door de code. Een modelantwoord mag die rol niet aannemen.
- Relaties zijn `supports`, `opposes`, `topical`, `undetermined` en `not_testable`. Het type relatie is **niet** uit vectorovereenkomst, negatie-woorden of het oude `verified`-label afgeleid.
- `validate_open_seeds_against_ssot` blijft voor gewichtloze seeds zoeken. Alleen `supports`, **gecombineerd** met geldige, versiegebonden bronrelatiebeoordeling en verificatiestatus van alle documentchunks, mag één steunbewijs naar de bestaande Gate sturen.
- Eén document met veel chunks is maximaal **één geclaimde bewijs-eenheid**. Duplicaten met hetzelfde `evidence_unit_id` tellen één keer; een conflict tussen relaties binnen die geclaimde eenheid blokkeert SUPPORT. Verschillende ID's zijn op zichzelf geen wetenschappelijk bewijs van onafhankelijke studies.
- `opposes` maakt niet automatisch een `CONTRADICTION`. Een what-if of vraag hoeft immers geen bewezen stelling te zijn.
- Een seed met historisch SSOT-SUPPORT, zonder de nieuwe relatiebeoordeling, wordt **niet stilzwijgend opnieuw gevalideerd**. Het oude Gate-logboek blijft onaangeroerd en vereist een afzonderlijke migratie-/auditbeslissing.

Het enige SSOT-SUPPORT-signaal dat dit pad nog maakt, heeft `reason=relation-attested:ssot:...` en `source_ref=evidence_unit_id`. `strength=1.0` in deze compatibiliteitsroute is **geen kans op waarheid** en **niet** de zoekscore. Brononafhankelijkheid wordt niet door `independent=True` geclaimd: die vlag blijft `False`.

## Wat deze wijziging niet kan bewijzen

De methode **verifieert geen echte menselijke identiteit**, authenticiteit of onafhankelijke bronherkomst. Een operator kan een onwaarachtige `supports`-verklaring opslaan. De code controleert het vastgelegde besluit en de versie, niet de feitelijke semantiek. Dat is een expliciete beperking, geen reden om opnieuw een onzichtbare LLM-beoordelaar in te voeren. Alleen een betrouwbaar extern beoordelingsproces kan die laag invullen.

Een oude seed kan al gezag gekregen hebben van vóór deze reparatie. Noch de nieuwe relatiebeoordeling, noch herimporteren trekt dat oude gezag automatisch in. De geschiedenis mag niet worden herschreven. Correctie, herbeoordeling of blokkering daarvan moet via **een afzonderlijk expliciet Gate-proces** worden besloten.

## Regressies en onderzoeksgrens

- Producttests toetsen wegvallen van automatische SUPPORT, vier fictief en apart geattesteerde bronnen, één document met vele chunks, bronduplicaten, bronconflicten, gewijzigde documenten, afgewezen materiaal en een bestaand historisch Gate-event.
- De eerder onjuist positieve SSOT-tests worden inhoudelijk gecorrigeerd, niet stilzwijgend verwijderd.
- De bestaande modelvrije G0-proef produceert een **voor/na-vergelijking**: historische resultaten worden gelinkt aan hun oude GitHub-run; huidige code wordt echt uitgevoerd. Alle beoordelingen in de huidige proef blijven expliciet door de **onderzoeker gesimuleerd**.
- De `run-ssot-smoke` geeft geen groen resultaat meer alleen omdat één document meerdere chunks oplevert. Het toetst dat zonder relatiebeoordeling niets promoveert, en dat één geattesteerd document als één bronunit wordt behandeld.

## Nog vereist voordat een merge inhoudelijk verantwoord is

1. Vaststellen welke actor een relatiebeoordeling mag afgeven, hoe identiteit en bronherkomst worden vastgesteld, en wat de betekenis van SUPPORT bij een open vraag of wat-if is.
2. Beslissen hoe oude, door similarity bevoegde seeds afzonderlijk beoordeeld, geblokkeerd of gemigreerd worden zonder bestaande Gate-events te herschrijven.
3. Verifiëren van negatieve en aanvullende tegenproeven, de volledige testsuite op GitHub en eventuele problemen met `run-ssot-smoke` en opgeslagen datasets.
4. Onafhankelijke technische en wetenschappelijke toets voor **Q1/Q2 zelf** blijven aparte taken. Deze SSOT-reparatie bewijst geen nieuwe mogelijkheden, semantische groei of blijvend modelvoordeel.

**Geen betaalde LLM-calls, keys, nieuwe modelrollen of wijzigingen aan de meerturns-shadowroute.**
