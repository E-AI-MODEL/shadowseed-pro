# G0 — SSOT: documentovereenkomst is niet dezelfde zaak als steun voor een seed

> 25 oktober 2026 | broncodeonderzoek + **uitvoerbare, fictieve** falsificatieproef. De test moet eerst slagen in GitHub Actions voordat het resultaat als uitgevoerd mag gelden. Geen productwijziging of G0-goedkeuring.

## De oorspronkelijke shadow-route blijft intact

De gewichtloze seed gaat volgens de [oorspronkelijke visie](https://github.com/E-AI-MODEL/shadowseed/blob/main/docs/research/vision-generative-seeds.md) en [ADR-002](../../../architecture/adr/ADR-002-epistemic-seed-contract.md) mee als onbewezen, contextgebonden kandidaat. De [echte meerturns-regressie, PR #239](https://github.com/E-AI-MODEL/shadowseed-pro/pull/239) bevestigt opslag, herdetectie/dormante TrTL-reactivatie en een afgesloten gewone antwoordprompt. Dit is **niet** het ontbrekende onderdeel.

Een reeds bestaande onderzoeksroute is `SSOTManager.validate_open_seeds_against_ssot` in [`src/shadowseed/ssot.py`](../../../../src/shadowseed/ssot.py). Die zoekt naar documenten bij nog gewichtloze seeds, filtert op de SSOT-metadata `status == verified` en geeft hits door aan de **bestaande** Validation Gate.

Het openliggende probleem zit in de **betekenis van het gevonden bewijs**.

## Exact geïnspecteerde codegrens

1. `SSOTManager` zoekt met het **embedding van de seed** en selecteert hits op vectorovereenkomst plus de bronmetadata `verified`.
2. Voor *ieder* geaccepteerd hit maakt `validate_open_seeds_against_ssot` een `ValidationSignal(kind=SSOT, direction=SUPPORT, strength=similarity, verified=True, independent=True, source_ref=chunk_id)`. Er vindt op dat punt **geen** aparte toets plaats of de inhoud de kandidaat **ondersteunt**, **tegenspreekt** of alleen **over hetzelfde onderwerp gaat**.
3. `SSLManager.run_validation_gate` leidt dit signaal door de bestaande Gate, die onafhankelijk van deze broncodebeslissing autoriteit kan verhogen. De Gate werkt dus met een **door de SSOT-producer al vooraf als SUPPORT geclassificeerd** signaal; het Gatebeleid zelf is hier niet de inhoudelijke bewijsclassificator. De bestaande compatibiliteitsadapter voegt daarnaast een apart **RECURRENCE**-signaal toe. Dat blijft herhaling, geen externe bevestiging; de falsificatie vergelijkt uitsluitend de richting van het **SSOT**-signaal.
4. Met `ingest_document(..., trust_level='user_verified')` kunnen bronmetadata direct op `verified` komen. Die metadata betekenen in de code **niet** dat een externe beoordelaar de *relatie tot de specifieke hypothese* onafhankelijk heeft vastgesteld. Ook `independent=True` wordt bij de SSOT-generator zelf ingevuld; dat is op zichzelf geen bewijs van onafhankelijke bronherkomst.

[ADR-002](../../../architecture/adr/ADR-002-epistemic-seed-contract.md) verbiedt dat semantische overeenkomst bronvertrouwen wordt, of dat een retrievalhit als bevestiging telt. [ADR-004](../../../architecture/adr/ADR-004-evidence-identity-and-independence.md) maakt bovendien onderscheid tussen overeenkomst als `strength`, broneenheid (`source_ref`) en echte onafhankelijkheid.

## Reproduceerbare mechanische contrastproef

[Onderzoeksuitvoering](../../../../research/scripts/g0_ssot_evidence_polarity_preflight.py) en [contracttests](../../../../research/tests/test_g0_ssot_evidence_polarity.py) gebruiken **exact de bestaande SSOTManager, SSLManager, InMemoryVectorStore en Validation Gate**. Er is geen vervangende vergelijkingsfunctie, geen LLM en geen nieuwe Gate.

De *onderzoeker* heeft drie fictieve condities opgesteld rond de onbewezen kandidaat:

> Mogelijk beïnvloedt de blauwe klep de druk in kamer B.

| Conditie | Vier fictieve tekstbronnen | Onderscheid dat onderzocht wordt |
| --- | --- | --- |
| A: expliciete steun | Bronnen zeggen dat de klep de druk **wel** beïnvloedt | Worden vergelijkbare, als verified gemarkeerde bronnen als steun verwerkt? |
| B: expliciete ontkenning | Bronnen zeggen dat de klep de druk **niet** beïnvloedt | Wordt **tegenovergestelde inhoud** ten onrechte toch als SUPPORT aangeboden? |
| C: dezelfde ontkenning, niet geverifieerde voorstellen | Metadata blijven `proposed` | Houdt de bestaande gate voor niet-geverifieerde voorstellen stand? |

Alle teksten zijn **onderzoeker-geschreven testmateriaal**. De aanduiding `verified` wordt in A en B **gesimuleerd via metadata**, niet door een onafhankelijke menselijke factcheck. Ook de vier verschillende `source_ref`-IDs simuleren geen werkelijk bewezen onafhankelijke bronnen. De test bewijst dus iets over **softwaregedrag onder die metadata**, niet over de waarheid van een klep of echte onderzoeksresultaten.

De proef registreert: de werkelijk gevonden chunks en similariteit, de `direction` en `kind` van de **echt aan de Gate aangeboden signalen**, de afzonderlijke Gatebeslissingen, seedgewicht, evidence-count en de negatieve controle zonder vertrouwde broneenheid. Iedere verwachte observatie moet **in een echt CI-artifact** aantoonbaar zijn.

## Afbakening: ook een contrasterende uitkomst is geen tweede waarheidsscore

Een Shadowseed hoeft geen als waar gestelde propositie te zijn; het kan ook een *vraag of what-if* bevatten. Een bron die zo'n mogelijkheid weerlegt kan nog steeds **relevante informatie voor het onderzoek** opleveren. Daarom is de juiste reparatie **niet** een naïeve regel "zoek het woord `niet` en maak er een contradiction van".

Het noodzakelijke onderscheid voor een toekomstige verbeterde onderzoeksroute is:

**gevonden en gerelateerd → bronstatus/herkomst → inhoudelijke richting (*steun / tegenspraak / beide / onbeslist*) → eventueel bewijs aan Gate**.

De exacte interpretatie van steun bij een *open vraag* versus een *bevestigde hypothese* vereist eerst een apart gespecificeerd, identiteitsbehoudend evidencecontract. Die inhoudelijke classificatie is in deze probe **niet** gebouwd; dat voorkomt een ad-hoc tweede Gate of een woordheuristiek die de mogelijkheidruimte van Shadowseed zelf afsnijdt.

## Stopregel

Een succesvol contrast A/B/C is **een gelokaliseerde SSOT-evidence-fout bij expliciet tegengestelde inhoud onder het bestaande metadataregime**; geen bewijs dat alle gevalideerde SSOT-hits fout zijn of dat Shadowseed Q1/Q2 wel of niet werkt. Als de werkelijke test afwijkt, zijn de vastgelegde productversie en logs leidend, niet deze verwachting.

**Bij bevestiging:** open een afzonderlijk product-/evidencecontract-issue met concrete repro en onafhankelijke beoordelingsvraag; herstel pas na ADR-compatibele beoordeling met tests op steun, tegenspraak, neutraliteit, onbekend en broneenheid. Houd Gate, TTL, TrTL, gewichtsregels en seedidentiteit verder ongemoeid. G0 blijft **NOT PASSED**.
