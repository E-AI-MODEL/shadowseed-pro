# Detector → normalisatie → intake → seed: herkomst per kandidaat

> 25 oktober 2026. Onderzoeksondersteunende productinstrumentatie in concept, gebaseerd op de bestaande `main`-pipeline. Geen nieuw geheugen, geen Gate-aanpassing, geen modelcall en geen Q1/Q2-resultaat. Het originele tweetrapsonderzoek blijft leidend.

## Aanleiding en het exacte probleem

De bestaande `ShadowChatSession` registreert al de ruwe detectoruitvoer, een verzameling `CandidateObservation`-records, genormaliseerde teksten, geaccepteerde seeds, afwijzingen en `created`-/`deduplicated`-events. De opslag per **gespreksturn** is dus niet leeg. Toch ontbrak een betrouwbaar spoor voor de vraag: *welke specifieke ruwe detectorregel werd via welke genormaliseerde kandidaat aan welke seed-ID gekoppeld, en was dat een geboorte, herdetectie of afwijzing?*

Die onzekerheid werd zichtbaar in [research-PR #245](https://github.com/E-AI-MODEL/shadowseed-pro/pull/245). Die PR beweert uitdrukkelijk niet de individuele herkomst te kennen. Dit voorstel vult het ontbrekende, **mechanische** spoor in de bestaande uitvoering aan. Het herinterpreteert geen oude events.

## Eén normalizer, niet twee

`seed_normalization.normalize_detection_candidates_with_sources` doorloopt dezelfde bestaande schoonmaak-, splits- en uitbreidingsregels als `normalize_detection_candidates` en bewaart voor elke output de **exacte ruwe index**. De oude functie levert ongewijzigd `list[str]` en hergebruikt diezelfde regels. Een ruwe invoer mag nul, één of meerdere genormaliseerde kandidaten opleveren; twee identieke invoerregels houden hun eigen indices.

De bestaande, overschrijfbare `SSLManager.normalize_detection_candidates` wordt nog steeds daadwerkelijk aangeroepen. Bij de normale implementatie wordt de per-item-herkomst opnieuw berekend met de **gedeelde regels** en vergeleken met de echte uitvoer. Bij een afwijkende of overschreven normalizer worden geen ruwe indices op basis van tekstgelijkenis gegist. De uitkomst heet dan `unresolved_normalizer_override` of `unresolved_normalizer_mismatch`. Dit is conservatief: we claimen geen individueel herkomstbewijs uit een aangepaste adapter waarvan de transformatie onbekend is.

## Werkelijke intakebeslissingen blijven intact

`ingest_detection_candidates` accepteert en verwerpt dezelfde kandidaten als voorheen. De bestaande `accepted`, `rejected` en `normalized_candidates` behouden exact hun vorm. Extra auditvelden onder schema `candidate-intake-lineage-v1` zijn:

| Veld | Betekenis |
| --- | --- |
| `normalized_index` | Positie in de werkelijk genormaliseerde uitvoer; `null` bij volledig verwijderde ruwe invoer |
| `raw_candidate_index` | Positie in de ruwe detectorlijst; `null` als de adapter niet betrouwbaar te herleiden is |
| `source_mapping_status` | `canonical` of expliciet onopgeloste herkomst |
| `normalized_text` | De werkelijk aan intake aangeboden tekst |
| `outcome`, `reason` | Geaccepteerd, afgewezen of door normalisatie verwijderd, met de bestaande afwijzingsreden |
| `seed_id`, `seed_transition` | Alleen bij acceptatie: daadwerkelijk teruggegeven seed-ID en een geregistreerd `created`-/`deduplicated`-event; een aangepaste adapter zonder zo'n event wordt `unresolved_custom_adapter` |

Een niet-atomische kandidaat of een batchduplicaat krijgt dus **geen** verzonnen seedgeboorte. Een tweede semantisch vergelijkbare tekst kan dezelfde bestaande seed-ID opleveren, maar dat wordt `deduplicated`, niet `created`. Een blanco ruwe detectorregel die de normalizer verwijdert blijft zichtbaar als `normalizer_dropped`, zonder fictieve seed.

## Koppeling met de bestaande observation ledger

De rapportage van `ShadowChatSession` op **live**, **evaluation** en **observe_source_text** gebruikt de bestaande `CandidateObservationLedger`. In `intake_diagnostics.item_lineage` koppelt `link_intake_lineage_to_observations` uitsluitend de werkelijk **in die batch aangemaakte** observatie-ID aan de herleide ruwe index. De ID wordt exact volgens het bestaande ledgercontract uit `context_ref`, index en ruwe tekst berekend en tegen het opgenomen observationrecord gecontroleerd.

Een eerder opgeslagen observationrecord met dezelfde ID wordt niet automatisch voor een nieuwe batch geclaimd. Dan staat `not_recorded_in_current_batch`. Een blanco invoer heeft geen observationrecord; een onopgeloste normalizer geen ruwe index, dus ook geen exact bronrecord. Eén ruwe bronregel die in meerdere genormaliseerde kandidaten uiteenvalt kan in diezelfde rapportage bij meerdere beslissingen horen; dat zijn meerdere **intakepaden**, niet meerdere onafhankelijke waarnemingen.

De `CandidateObservation`-schema's, opgeslagen seedstructuur, Gate-events, weight, TTL/TrTL en promptrollen veranderen niet. Oude sessies zonder `item_lineage` blijven oude sessies. We reconstrueren niet achteraf wat zij niet registreerden.

## Aantoonbare grenzen

Deze wijziging test uitsluitend **mechanische afstamming van tekst en besluit**, niet:

- of de oorspronkelijke detectoruitvoer een werkelijk niet-gekozen interne LLM-mogelijkheid representeert;
- of een samengestelde, opgesplitste of herschreven zin inhoudelijk trouw is aan de ruwe suggestie;
- of een score, embeddingmatch of herhaalde detectorzin onafhankelijk bewijs oplevert;
- of de seed later een nieuw, toetsbaar onderzoeksidee veroorzaakt.

Ook een exact herleidbare seed houdt bij geboorte `weight=0`. Het bijbehorende `observation_id` is een administratieve herkomst-ID, geen toestemming om de seed in een normaal antwoord te gebruiken. `AgentSafetyContract` en de bestaande Validation Gate blijven onaangetast.

## Regresstoets en vervolg

De tests controleren de historische normalisatieresultaten, één-op-veel splitsingen, herhaalde identieke ruwe regels, blanco weggefilterde regels, afwijzingen, bestaande seedherkenning, aangepaste normalizerhooks en daadwerkelijke observation-ID's. Een echte `ShadowseedEngine` wordt over twee turns gevolgd, zonder hostmodelcalls. Hij bewaart de nieuwe diagnostiek in zijn bestaande turnrapport zonder extra seedgewicht of Gate-event.

Een latere **werkelijke modelproef** kan voortaan de exacte stap `raw detectoritem → intakebesluit → seed-ID` controleren voor nieuwe runs met de canonieke normalizer. Dat is nog geen antwoord op Q1/Q2. De originele [step-1-methodiek](step1-model-signals-gap-origin-2026-10-25.md), de [geboortecontrole in PR #245](step1-to-weightless-inquiry-handoff-2026-10-25.md) en de [onafhankelijke G0-review](g0/dynamic-inquiry-independent-review.md) blijven afzonderlijke beoordelingsgrenzen. **G0 NOT PASSED.**
