# Echte gewichtloze seed → modelbedachte onderzoeksvragen (RF-verkenning)

> 25 oktober 2026. **Verkennende proef, nog geen resultaten.** G0-v3 onafhankelijke beoordeling ontbreekt en blijft **NOT PASSED**. Geen nieuw productonderdeel of aanpassing van de Gate. Deze proef mag niet als Q1/Q2-bewijs worden aangehaald.

## Uitgangspunt

[Oorspronkelijke tweedelige these](../../possibility-space-thesis.md): onderzoek wat in de gewone waarschijnlijkheidsgerichte generatie niet werd geselecteerd, en of een daaruit voortgekomen mogelijkheid later een nieuwe onderzoeksvraag kan helpen openen. Een gemiste zin is geen bewijs van een intern aanwezig maar onderdrukt idee. Een later nieuw geformuleerde vraag is nog geen bewijs van een gewijzigde ruimte van onderzochte mogelijkheden.

De [geslaagde 20-call GPT-5-proef](real-model-stage1-observations-2026-10-25.md) toonde echte detectie, intake en gewichtloos meereizen, maar geen nieuw door het model geformuleerd vervolgonderzoek. De poging met gecorrigeerde context [stopte](real-model-stage1-v2-execution-status-2026-10-25.md) bij een onvolledig T0-hostantwoord. Deze nieuwe, afzonderlijke proef maakt de modeluitvoergrens expliciet 4.096 tokens en bewaart alle gedeeltelijke resultaten bij een fout. Er is **geen automatische retry**.

## Wat de run werkelijk doet

De onderzoeksrunner `research/src/shadowseed_research/benchmark/real_seed_rf_inquiry.py` gebruikt precies één **blijvende, echte** `ShadowseedEngine`, met de bestaande `OpenAIDetectorBackend(current_pair)`, parser, intake, manager, gewichtloze geboorte, TrTL en Gate. De gewone host krijgt nooit een ongeautoriseerde seed. Een tweede engine met `NONE`-detector controleert technisch de ongewijzigde gewone antwoordroute.

- **T0:** twee normale GPT-5-antwoorden vóór enige seed-detectie, daarna een apart normaal hostantwoord; vervolgens detectie en het **eerste werkelijk geaccepteerde** seedgeboorte-event. Geen door onderzoekers verzonnen kandidaattekst ter vervanging. Een gewone notitie wordt afzonderlijk uit de zichtbare casus en het hostantwoord gemaakt.
- **T1:** hetzelfde gewone gesprek krijgt pas nu de eerste vooraf beschreven externe waarneming. Na het normale antwoord en de bestaande detector volgt pas de **aparte experimentele vraagronde**. Het model mag één nieuwe toetsbare vraag voorstellen of expliciet `NONE` aangeven. Dit is een onderzoekssandbox, geen antwoordrevisie.
- **T2:** de tweede vooraf beschreven waarneming komt erbij. De echte seed krijgt het bestaande meerturnscheckpoint. Ieder onderzoeksarm ziet uitsluitend zijn **eigen** eerdere onderzoeksvraag; opnieuw mag het model zelf een vraag of `NONE` genereren. De omgeving voert geen vragen uit en geeft geen onderzoeksresultaten van die vragen terug.

De primaire uitvoer is de volledige, niet geselecteerde tekst van alle voorgestelde vragen en afwijzingen, plus bronherkomst, gespreksrapporten, budget, gebruikte model- en embeddingcalls en oorspronkelijke gewichtloze kandidaat. De studie rapporteert ook wanneer T0 **geen seed** oplevert. Dan vindt er **geen** gefingeerde D-arm plaats.

## De vijf onderzoeksarmen

| Arm | Wat de aparte onderzoeksvraagmaker ontvangt |
| --- | --- |
| **A** | Alleen de normale zichtbare gespreksgeschiedenis, zonder extra seed |
| **B** | Dezelfde geschiedenis met een bewuste, doelgerichte zoektocht naar andere verklaringen |
| **C** | Een gewone modelgemaakte notitie over de eerdere geschiedenis, geen Shadowseed |
| **D** | De exacte eerste, echt geboren gewichtloze seed, uit het bestaande productgeheugen, **alleen voor onderzoek** |
| **E** | Een alternatieve onbewezen notitie als sham/ablatie; interpretatie beperkt door mogelijke verschillen in inhoud en relevantie |

**Kosten en tijd:** alle onderzoeksarmen gebruiken hetzelfde GPT-5-model, twee momenten, dezelfde externe waarnemingen en hetzelfde maximum per modelaanroep. De complete proef telt ook de afzonderlijke detector-/notitiegeneraties mee; die extra oproepen zijn niet kostenvrij en worden gerapporteerd. Een match in modelaanroepen en toegestane informatie is niet vanzelf een match in daadwerkelijk gebruikte tokens. Budgetverschillen zijn expliciet een beperking.

**Dit is RF (fixed replay)**: de externe T1/T2-waarnemingen zijn voor alle armen identiek en zijn niet veroorzaakt door de door het model bedachte vragen. We mogen uit verschillen in vraagformulering geen verschillende interventiegevolgen afleiden. **Dit is niet RI.**

## Voordat resultaten betekenis krijgen

Een echte Q2-uitkomst vergt meer dan een nieuw klinkende vraag. Twee onafhankelijke menselijke beoordelaars moeten blind toetsen of de latere vraag inhoudelijk anders is, onafhankelijk toetsbaar is en daadwerkelijk een **ander vervolgend onderzoek** mogelijk maakt. De bestaande [review-pakketworkflow](blind-later-inquiry-review-handoff-2026-10-25.md) mag daarbij worden hergebruikt. Zonder echte uitvoerbare onderzoeksactie en onafhankelijke nieuwe waarnemingen wordt de dimensie 'later gevolg' als **niet aangetoond** vastgelegd.

De eerste vraag of het model intern een niet-gekozen mogelijkheid representeerde, **wordt niet opgelost** met deze API-only proef. Voor dat deel is later een eigen open-weight activatieproef nodig, met de juiste doelvariabele, controles en voldoende modelcapaciteit. De oude negatieve 0,5B-H-Neuron-uitkomst is geen bewijs dat zo'n signaal niet kan bestaan.

## Uitvoering en stopregels

Een **eenmalige, betaalde** GitHub Action gebruikt uitsluitend de bestaande afgeschermde `OpenAI key`-omgeving, met expliciete eenmalige trigger ná groene offline preflight. Eén fictieve casus, hoogstens 24 GPT-5-modelverzoeken, 48 embeddingverzoeken en 110.000 geregistreerde tokens; uitgaande van één geldige seed zijn 19 modelcalls gepland. Geen automatische herhaling. De kostenlimiet is een registratieplafond, geen gegarandeerd eurobedrag.

Foute parsing, `NONE`, weggevallen seed, onvolledig modelantwoord, overgeslagen turn, Gate-invloed of gebrekkige provenance worden niet weggefilterd. De officiële onderzoeksthese, Gate, SSOT, modelgewichten, TTL, TrTL, gewone hostprompt en productdefaults blijven ongewijzigd.

**Kwalificatie:** zelfs een technisch volledig geslaagde run levert alleen een gedocumenteerde verzameling **model-geformuleerde vragen** en een mechanische vergelijking. Q1, Q2 en G0 blijven onbewezen tot onafhankelijk nagekeken en getoetst.
