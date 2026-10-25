# SSOT-bewijsroute: conceptreparatie en historische blokkering

> 25 oktober 2026 | **Draft PR #243; niet gemerged.** [Issue #241](https://github.com/E-AI-MODEL/shadowseed-pro/issues/241) blijft open. De tweeledige Shadowseed-vraag Q1/Q2 is **niet** getest. G0 **NOT PASSED**.

## Waargenomen fout, met twee afzonderlijke uitvoerbewijzen

Het oorspronkelijke product stuurde een vergelijkbaar gevonden `verified`-document direct als `SSOT SUPPORT` naar de bestaande Gate. Vier kunstmatig geverifieerde ontkennende teksten leverden daardoor vier SSOT-steunsignalen op en promoveerden de fictieve seed tot gewicht 0,6. De oorspronkelijke [modelvrije GitHub-run #40176388209](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40176388209) bewijst dit voor die onderzoeksinputs, niet voor echte onafhankelijk gecontroleerde bronnen.

Een eerdere versie van concept-PR #243 koppelde het Gate-signaal aan een opgegeven `reviewer` en `supports`-label. De [groene run #40182789691](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40182789691) bevestigde dat de nieuwe selectie technisch werkte, maar **niet** dat de reviewer echt bevoegd was. Een zelfverklaarde controle kon nog steeds via de nieuwe SSOT-route gewicht toekennen. Een groene test was geen inhoudelijke toestemming om dit te mergen.

## Huidige voorgestelde oplossing

Het bestaande `SSOTManager`-pad blijft gericht op gewichtloze, contextgebonden seeds en werkt over dezelfde documenten. Het verandert **geen** Gate-, model-, detector-, memory-, TTL-, TrTL-, gewicht- of promptregel.

- `ingest_document` bewaart document- en chunkversiehashes. Opnieuw importeren met hetzelfde document-ID verwijdert oude chunks en maakt bestaande relatiebeoordelingen ongeldig. Beschadigde of oude chunkmetadata zonder versiehash wordt niet als beoordeelde bron geaccepteerd.
- `attest_document_relation` legt een **zelf opgegeven** relatie vast tussen exacte seed en document: `supports`, `opposes`, `topical`, `undetermined` of `not_testable`. Een ingevuld `reviewer`-veld blijft metadata, geen bewijs van authenticatie of bronwaarheid.
- `validate_open_seeds_against_ssot` is, ondanks de historische naam, nu een **read-only inspectie**. De functie retourneert alleen `review_candidates`; de velden `gate_authorized=False` en `requires_authorized_submission=True` maken duidelijk dat er nog geen autoriteit is toegekend. Zelfs vier geattesteerde ondersteunende documenten leveren **geen** Gate-event, gewicht of bewijsopbouw op.
- De bestaande vectorzoekfunctie blijft ontkennende, topicale en onbesliste bronnen tonen. De relatie wordt niet met een woordfilter, een negatieheuristiek of een modelscore gegist. Oppositie tegen een open what-if wordt niet automatisch een formele `CONTRADICTION`.
- Eén geclaimde bron-eenheid levert maximaal één kandidaat voor vervolgbeoordeling op. Tegenstrijdige verklaarde relaties binnen dezelfde bronunit blokkeren ondersteuning. Een tweede ID bewijst op zichzelf geen onafhankelijke studie.

### Wie mag echt bewijs indienen?

De productieomgeving heeft al een aparte grens: `ActorContext` met de capability `evidence.verify`, scopecontrole, idempotente aanvraag-ID, een bestaande Gate-transitie en een atomair productielogboek. Dat staat in [production-actor-authorization.md](../../../architecture/production-actor-authorization.md) en `SessionService.submit_verified_evidence_authorized`.

De SSOT-manager wordt **niet** heimelijk een tweede productie-ingang. Het is de taak van een vertrouwde product-operator om de precieze bron/seedrelatie inhoudelijk te beoordelen en, waar gerechtvaardigd, de **bestaande geautoriseerde** bewijsfunctie te gebruiken. De SSOT-inspectie doet die stap niet automatisch, beschikt niet zelf over een productie-`ActorContext` en maakt geen valse claim dat twee velden menselijke verificatie aantonen. Een complete duurzame koppeling van SSOT-relatiebeoordeling aan een productie-ledger-event vraagt nog een afzonderlijk uitvoeringsbesluit.

### Historische seedgewichten worden niet stilzwijgend vertrouwd

Een nieuw, read-only signaal in de agent-facing point-of-use-controle herkent oudere `SSOT SUPPORT`-events, zowel uit echte objecten als uit opgeslagen JSON. Zo'n seed kan historisch nog `PROMOTED` en positief gewogen zijn, maar mag **geen nieuwe** antwoordwijziging, toolactie of retrieval veroorzaken. De geweigerde poging wordt gewoon als point-of-use-besluit geregistreerd, met reden `legacy_ssot_requires_review`.

De Workbench-inspectie toont `legacy_ssot_requires_review=True`, `current_gate_authorized=False` en een heldere uitleg. Ook als een oudere sessie current-Gate-herbeoordeling uit heeft staan, blijft het laatste point-of-use-contract weigeren.

De blokkering blijft bewust gelden nadat iemand alleen een nieuw, los `supports`-label indient. Een onwaarachtig label mag een oud historisch gewicht niet opnieuw bruikbaar maken. De geschiedenis blijft intact: eerder vastgelegde Gate-events, bronverwijzingen, seedgewichten en vroegere toegestane point-of-use-besluiten worden niet herschreven of achteraf als nieuwe overtredingen bestempeld. Historische records blijven reproduceerbaar, maar zijn geen toestemming voor een **nieuw** gebruik. Een later besluit over herstel of migratie heeft een nieuwe versiegebonden, door bevoegd gezag goedgekeurde procedure nodig.

Dit is een conservatieve blokkering: ook werkelijk betrouwbare oudere SSOT-steun blijft tijdelijk buiten nieuwe invloed. Dat is een bewuste keuze zolang de oude records geen product-authenticatie van de precieze bron/seedrelatie aantonen. De code beweert **niet** dat iedere oude bron onjuist is.

## Testafbakening

- Producttests: geen promotie door zoekovereenkomst, fake reviewers of vier `supports`-claims; bronduplicaten, conflicten, veranderde tekst, onvolledig geverifieerde documenten, modelvoorstellen en oude logboeken.
- Agenttests: nieuw antwoord, retrieval en besluit geblokkeerd door oude SSOT-steun; JSON-restore herkent dezelfde situatie; normale recurrence-seeds blijven toegestaan; historische toegestane point-of-use-besluiten blijven replaybaar.
- Workbenchinspectie: de oud gepromoveerde seed verschijnt als `legacy_ssot_requires_review`, zonder dat gewicht of Gate-geschiedenis verdwijnt.
- Modelvrije G0-proef: oorspronkelijke fout blijft gepind op [#40176388209](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40176388209), de tussenvorm met operatorclaims op [#40182789691](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40182789691). De nieuwe proef moet aantonen dat geen van de fictieve relatieverklaringen op zichzelf een Gate-event veroorzaakt. Er zijn geen echte bronbeoordelaars of modelcalls.

## Nog vereist vóór merge

Een review van de nieuwe **read-only** responsvorm van `validate_open_seeds_against_ssot` is nodig omdat eerdere callers `applied_evidence` en daadwerkelijke Gate-resultaten verwachtten. We veranderen hier een API-contract en moeten eventuele externe clients expliciet waarschuwen.

Ook nodig: het formele werkproces voor onafhankelijke bronherkomst en bron/seedrelatie, plus een versiegebonden herstelprocedure voor historische SSOT-autoriteit. De [production-migration-policy.md](../../../architecture/production-migration-policy.md) verbiedt om oude events stilzwijgend met nieuwe garanties te markeren.

**Deze reparatie is geen resultaat voor G0, Q1 of Q2.** De echte meerturns-shadowpipeline blijft bestaan en ongewijzigd. Er zijn geen betaalde LLM-aanroepen, nieuwe sleutels, tweede Gate of nieuwe modelrollen gebruikt.
