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

**Bijgewerkt 31 oktober 2026 (op de actuele `main` gebracht):** het oude Gate-eventmodel bevat geen authentiek productautorisatiebewijs voor een `SSOT SUPPORT`-signaal. Een `reviewer`, `verified`, bronreferentie, vectorovereenkomst of documenthash is daarvoor onvoldoende. De huidige point-of-use-blokkering weigert daarom **alle** SSOT-steunsignalen zonder afzonderlijk controleerbare productautorisatie, ook bij onbekende legacy-formaten en eerder afzonderlijk ingediende onderzoekssignalen. De reden `legacy_ssot_requires_review` blijft behouden voor compatibele auditlogs.

Dit is strenger dan de eerdere detectie op `verified SSOT chunk`, `::chunk_` en `relation-attested:ssot:`. De oude herkenning liet onbenoemde SSOT-varianten ongemoeid. De code vertrouwt voortaan geen onbeoordeelde historische SSOT-steun, ongeacht de schrijfwijze van `reason` of `source_ref`.

Een seed mag historisch nog `PROMOTED` en positief gewogen zijn. Dat verandert niet. De agent weigert **nieuwe** antwoordwijzigingen, retrieval, toolacties en andere point-of-use-invloed vanuit zo'n geschiedenis. Ook de live `ShadowChatSession.prepare_turn`-grens blijft zonder modelcontext voor deze seed. Eerdere Gate-events, seedgewichten en toegestane gebruiksrecords blijven ongewijzigd en replaybaar. De Workbench-inspectie maakt de blokkering zichtbaar, inclusief `current_gate_authorized=False`.

Deze maatregel geldt ook voor een onafhankelijk gedocumenteerd onderzoekssignaal zonder productie-autorisatieledger. Het signaal mag onderzoeksbewijs blijven, maar krijgt daarmee geen **productbevoegdheid**. Dat zegt niets over de feitelijke juistheid van de bron. De huidige geautoriseerde Workbench-route `submit_verified_evidence_authorized` gebruikt `HUMAN_FEEDBACK`, een vertrouwde `ActorContext`, de `evidence.verify`-capability en een atomair logboek. Er is nog geen afzonderlijke productroute die een SSOT-signaal met zo'n authentieke ledgerbinding mag vrijgeven.

### Migratiebesluit en beperking

- **Bij openen van oude sessies:** behoud de bestaande toestand en logboeken; weiger nieuwe invloed zodra `SSOT SUPPORT` in de geschiedenis staat. Geen automatische reparatie van oud gewicht en geen stilzwijgende herclassificatie als menselijk geverifieerd.
- **Bij bronbeoordeling:** inspecteer de exacte bron/seedrelatie, de volledige tekst, de bronherkomst en onafhankelijkheid. Leg bevindingen buiten het bestaande Gate-event vast. Een tekstveld met een reviewersnaam is geen identiteitscontrole.
- **Bij mogelijk herstel:** autorisatie via een nieuwe, versiegebonden productprocedure met `ActorContext`, scope, idempotentie en een controleerbare ledgerbinding. Ontwerp, review en test die procedure afzonderlijk. Een los `supports`-label mag de blokkering niet opheffen.
- **Bestaande dossiers:** deze repository bevat geen inventaris van alle lokale gebruikerssessies. De tests dekken bekende en onbekende synthetische Gate-eventvormen. Ze bewijzen geen volledigheid van historische gebruikersgegevens; zo'n inventaris en eventuele gegevensmigratie blijven een afzonderlijke acceptatiestap.

Deze conservatieve blokkering is geen bewijs dat alle oude SSOT-bronnen onjuist zijn. Ook correct onderbouwde oude steun kan tijdelijk buiten nieuwe invloed blijven. Dit is bewust totdat productautorisatie bewijsbaar is.

**Onderzoeksuitzondering, niet voor het product:** de bestaande offline evaluatie met `runtime_mode="evaluation"` blijft de historische synthetische Gate-proef kunnen reconstrueren. Alleen een expliciet in dezelfde Python-processessie aangeleverde `_OFFLINE_RESEARCH_CAPABILITY` kan deze evaluatieaanroep aanzetten. De code geeft pas dan het tijdelijke interne argument `_research_evaluation_only=True` door. De capability is een niet-serialiseerbaar object en staat niet in de sessie-/contractinstellingen; herstel uit JSON verliest deze toestemming. De live runtime geeft altijd `False` door en blijft weigeren, ook bij gemanipuleerde bronmetadata. Een onderzoeksscore of geslaagde A/B-simulatie is geen productie-autorisatie. Voor de uiteindelijke release moet de productgrens afzonderlijk worden getest.

## Testafbakening

- Producttests: geen promotie door zoekovereenkomst, fake reviewers of vier `supports`-claims; bronduplicaten, conflicten, veranderde tekst, onvolledig geverifieerde documenten, modelvoorstellen en oude logboeken.
- Agenttests: nieuw antwoord, retrieval en besluit geblokkeerd door oude SSOT-steun; JSON-restore herkent dezelfde situatie; normale recurrence-seeds blijven toegestaan; historische toegestane point-of-use-besluiten blijven replaybaar.
- Workbenchinspectie: de oud gepromoveerde seed verschijnt als `legacy_ssot_requires_review`, zonder dat gewicht of Gate-geschiedenis verdwijnt.
- Modelvrije G0-proef: oorspronkelijke fout blijft gepind op [#40176388209](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40176388209), de tussenvorm met operatorclaims op [#40182789691](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40182789691). De nieuwe proef moet aantonen dat geen van de fictieve relatieverklaringen op zichzelf een Gate-event veroorzaakt. Er zijn geen echte bronbeoordelaars of modelcalls.

## Nog vereist vóór merge

Een review van de nieuwe **read-only** responsvorm van `validate_open_seeds_against_ssot` is nodig omdat eerdere callers `applied_evidence` en daadwerkelijke Gate-resultaten verwachtten. We veranderen hier een API-contract en moeten eventuele externe clients expliciet waarschuwen.

Ook nodig: het formele werkproces voor onafhankelijke bronherkomst en bron/seedrelatie, plus een versiegebonden herstelprocedure voor historische SSOT-autoriteit. De [production-migration-policy.md](../../../architecture/production-migration-policy.md) verbiedt om oude events stilzwijgend met nieuwe garanties te markeren.

**Deze reparatie is geen resultaat voor G0, Q1 of Q2.** De echte meerturns-shadowpipeline blijft bestaan en ongewijzigd. Er zijn geen betaalde LLM-aanroepen, nieuwe sleutels, tweede Gate of nieuwe modelrollen gebruikt.
