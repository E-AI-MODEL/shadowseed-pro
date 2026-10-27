# Shadowseed: GPT-5 versus GPT-6 Luna, echte A/B per model

> 27 oktober 2026. Vooraf vastgelegd **verkennend** onderzoek. Nog geen modelresultaat op het moment van schrijven. G0 = `NOT PASSED`. Onderliggende methodebouwstenen: PR #255, #256 en #257. De oorspronkelijke tweedelige vraag blijft onveranderd in `docs/research/possibility-space-thesis.md`.

## Wat we vergelijken

Twee onafhankelijke, echte `ShadowseedEngine`-processen per vooraf vastgelegde fictieve RF-casus:

- **GPT-5**: `gpt-5-2025-08-07` (huidige historische onderzoeksreferentie).
- **GPT-6 Luna**: `gpt-6-luna` (goedkoopste GPT-6-API-model op 27 oktober 2026). Het geretourneerde model-ID wordt per verzoek vastgelegd. Geen andere GPT-6-versie achteraf invullen.

Voor **elk model afzonderlijk**: normale T0-generatie (twee afzonderlijke samples), gewone hostreacties op vier echte beurten, `OpenAIDetectorBackend(current_pair)`, echte canonieke geboorte op T0 of T1, minimaal twee volgende beurten met `freeze_weightless_followup`, en twee bij elkaar horende onderzoeksvragen in beide condities. Detector, host en onderzoeksvragen gebruiken hetzelfde model binnen één model-/casustraject. Alleen de afzonderlijke research-invoer ziet de seed, nooit de gewone product-host.

De **behandeling binnen een model**:

| Conditie | Gewone zichtbare geschiedenis | Extra ongetoetste onderzoeksnotitie |
| --- | --- | --- |
| A | exact dezelfde normale dialoog, T0-notitie en externe waarnemingen | `NONE` |
| B | exact dezelfde normale dialoog, T0-notitie en externe waarnemingen | letterlijke **echt geboren gewichtloze** seed |

Op de eerste onderzoekbeurt verschilt alleen dit kandidaatveld. Op de volgende beurt hebben A en B elk hun **eigen** eerdere onuitgevoerde modelvragen. Dat is een toegelaten, maar te registreren divergentie. Alle modelverzoeken houden `reasoning.effort=low`, dezelfde output-/call-/tokenlimieten en dezelfde onderzoeksinstructie.

**Modelvergelijking**: hetzelfde externe RF-casusmateriaal wordt aan beide modellen aangeboden. GPT-5 en Luna produceren mogelijk een andere gewone geschiedenis, kandidaat en geboorte; de directe vergelijking gaat daarom over de **gehele model+Shadowseed-pijplijn** en de A/B-verschillen *binnen* die pijplijn, niet over een identieke seed die in twee modellen is geïmplanteerd. Dezelfde letterlijke hypothese in twee modellen testen vraagt een aparte cross-over.

## Casussen en negatieve uitkomsten

De zes nieuwe, fictieve situaties staan als bevroren JSON in `research/fixtures/g0_gpt5_luna_dual_model_v1.json`: conditionele herinterpretatie, meet-/instrumentmogelijkheden, relationele afhankelijkheden en een expliciet no-opportunity-controle. T1/T2/T3-waarnemingen zijn vóór modelverzoeken door de onderzoeker geschreven en **niet** de uitgevoerde resultaten van modelvoorstellen. Geen casus bevat een gewenste seed, winnaar, labels of goede vervolgvraag.

**Het eerste echte geboorte-event op T0 of T1** wordt alleen door de bestaande canonieke Engine toegelaten, inclusief exacte ruwe detectoritem→intake→seedherkomst. T0-geboorte: eigen onderzoek op T1 en T2; T1-geboorte: op T2 en T3. Geboorte op T2/T3 is *te laat voor twee vervolgbeurten*: bewaren als eigen categorie, niet als nul-effect, geen handgemaakte seed en geen terugdatering. Geen geboorte, mislukte modelcall, onverwachte checkpointfout, `NONE`, syntaxfout of promptoverschrijding blijven in de oorspronkelijke noemer.

## Vooraf bepaalde controles

- Zes casussen × twee modellen = **12 model-/casustrajecten**.
- Per traject maximaal **16 echte modelverzoeken, 24 embeddingverzoeken en 65.000 gerapporteerde tokens**. Bovenlimiet volledige studie: 192 modelverzoeken en 780.000 geregistreerde tokens; geen verborgen retries. Maximaal 4.096 outputtokens per verzoek; de harde providerlimiet van 12.500 prompttekens blijft bestaan. Overschrijding = eerlijke technische uitval, nooit afgekapt.
- Verzoeken worden pas na een succesvolle **no-network fake-provider-preflight** uitgevoerd via de al afgeschermde GitHub Environment `OpenAI key`, met secret `OPENAI_KEY`. Geen sleutel in broncode of logs. Slechts éénmalige Action op exact gecontroleerde broncommit, niet op automatische herhalingen.
- De A/B-volgorde is vóór de eerste echte aanvraag gebalanceerd geloot: drie A-eerst en drie B-eerst voor GPT-5; Luna krijgt de tegengestelde eerste arm per casus. Op de tweede inquiry-beurt is de volgorde omgekeerd. De modelvolgorde wisselt per casus. Dit vergroot **niet** het aantal onafhankelijke onderzoeksgevallen.
- Alle ruwe antwoorden, providerreceipts, model-ID, tokenverbruik, geboornevents, checkpoint-hashes en uitvalredenen blijven bewaard in een apart eigenaar-artifact. De beoordelaarsversie verbergt modelnaam, armnaam, bronseed, parserlabel en gewone T0-notitie. De modeltekst kan de conditie alsnog verraden; niemand mag blindering als perfect beschrijven.
- Twee onafhankelijke menselijke reviewers moeten eerst **inhoudelijk beoordelen** of iets anders wordt voorgesteld dan parafrase, of de test onderscheidend is, en of T2 werkelijk afhankelijk is van T1. Daarna pas de eigenaarssleutel openen. Er is geen automatische semantische effectscore. `G0 NOT PASSED` blijft ongewijzigd.

## Geen claims die deze proef kan bewijzen

Een extra seedzin kan gewoon tekstconditionering zijn. Een nieuwe **voorgestelde** test is niet gelijk aan een uitgevoerde test, en een betere score op vraagvorming niet aan een veranderde mogelijkheid om de wereld te onderzoeken. Deze proef vergelijkt daarom alleen **RF-vraagvorming**. Ze bevat geen onafhankelijke open **RI-executor** en geen interne LLM-activatiegegevens. Ze kan geen Q1-neuronenclaims, Q2-verandering van werkelijk onderzoekbare relaties of uniek SSL-mechanisme boven gewone notities en lengte-gelijke placebo bevestigen.

Ook een goedkoper model dat sterkere A/B-verschillen laat zien bewijst geen algemeen voordeel voor Shadowseed: modelcapaciteit, andere seedgeboorten en onvergelijkbare eigen histories blijven alternatieve verklaringen.

**Volgende experimentele grens**: na ruwe resultaten en onafhankelijk oordeel afzonderlijke placebo-/notitiecontrole en een werkelijk uitgevoerde RI-test met nieuwe afgeschermde casussen. G0-review #234 en #235 blijft extern en door mensen.
