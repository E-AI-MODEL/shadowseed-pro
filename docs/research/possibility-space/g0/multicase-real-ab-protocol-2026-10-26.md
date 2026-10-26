# Shadowseed: breder, gerandomiseerd A/B-onderzoek met echte seeds en drie beurten

> 26 oktober 2026. **Vóór de nieuwe modelcalls vastgelegde, verkennende studie.** Zes door onderzoekers geschreven openbare casussen, geen verborgen onafhankelijke steekproef. De eerdere 16-call T1-ablatie is bekend, inclusief de 2/4 letterlijke terugkomsten van 'ruimtelijke offset'. Dit protocol maakt van die bevinding **geen** bevestigde hypothese. **G0 = NOT PASSED** en er is geen onafhankelijke E1/E2-beoordeling afgerond. Alleen een gescheiden onderzoekssandbox is toegestaan, geen productwijziging.

## De onderzoeksvraag blijft ongewijzigd

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

Dit is de *letterlijke* [oorspronkelijke these](../../possibility-space-thesis.md), niet een toets op antwoordvolledigheid, geheugen, efficiëntere taken of het aantal nieuwe zinnen. Lees ook de [eerste-principes-herijking](../first-principles-reorientation-2026-10-25.md). We onderscheiden **niet-gekozen betekenis**, **later geconstrueerde relatie**, en **feitelijk anders onderzoekbare mogelijkheid**. De drie verschijnselen mogen niet als één score worden samengevoegd.

### Welke eerdere resultaten sturen de aanpassing?

In de [exacte T1-ablatie](exact-seed-ablation-first-results-2026-10-25.md) waren alle 16 GPT-5-hoofdvragen onderdeel van dezelfde familie: temporele samenhang tussen pieken en regelkastschakelingen. Slechts twee van de vier antwoorden mét de echte seed noemden letterlijk de ruimtelijke hypothese als onzeker alternatief; de overige 12 antwoorden niet in die exacte woorden. Dat is een **achteraf geselecteerde exacte woordtelling** zonder onafhankelijke semantische beoordeling. Het kan gewone tekstconditionering zijn. Uit die 16 afhankelijke voorbeelden volgt geen generaliseerbaar of modelintern mechanisme.

De nieuwe proef verbetert de doelvariabele. Een model mag **nul, één of maximaal twee** zinvolle vervolgonderzoekspaden formuleren. We vragen niet de oorspronkelijke kandidaat te herhalen. Het model kiest zelf vragen en mogelijke tests zonder een vooraf in de tekst ingebouwde ideale vervolgvraag. Een zinvolle `NONE` blijft een volwaardige negatieve uitkomst.

## Dezelfde échte pijplijn, zonder shortcuts

Voor **iedere** casus: twee gewone T0-antwoordvarianten (Q1 geobserveerde selectie, niet interne afwezigheid), nog een gewone hostreactie, dezelfde bestaande `OpenAIDetectorBackend(current_pair)`, canonieke intake, eerste *werkelijk geaccepteerde* gewichtloze geboorte op T0 en daarna echte `ShadowseedEngine.prepare_turn → host → observe_turn`-beurten op T1 en T2. Op elk latere turn wordt de originele seed met de bestaande `freeze_weightless_followup` gecontroleerd. **Geen onderzoeker-verzonnen seed**, geen herstel van mislukte geboorte, geen bypass van de Gate, geen bewijs/weight/authority, geen seed in gewone antwoorden.

De zes casussen in [de vastgelegde fixture](../../../../research/fixtures/g0_multicase_real_ab_v1.json) bestrijken twee voorbeelden van conditionele herinterpretatie, twee voorbeelden van andere meet-/waarnemingsmogelijkheden, één relationele afhankelijkheid en één expliciete negatieve situatie zonder duidelijke nieuwe aanleiding. Dat zijn door onderzoekers geschreven **RF-waarnemingen**. Geen van de casussen bevat een doelvraag, winnende arm, voorgeschreven seedgeboorte of uitgevoerde latere test.

### De A/B-behandeling

Beide condities krijgen dezelfde sterke `gpt-5`, dezelfde zichtbare gewone gespreksgeschiedenis, **dezelfde gewone T0-notitie**, dezelfde ruimere instructie tot zorgvuldig zoeken en dezelfde vooraf vastgelegde externe T1/T2-waarnemingen. De onderzoeksarme zijn gescheiden; uitsluitend de eigen onderzoeksvragen van T1 mogen op T2 worden meegenomen. Een eerdere onderzoeksvraag telt nooit als onafhankelijke waarneming.

- **A:** aanvullend hypotheseveld `NONE`; zelfde notities, zoekwijze en middelen.
- **B:** precies de eerste echte, op T0 gewichtloos geboren seed in datzelfde veld. De seed wordt expliciet als onbewezen mogelijkheid aangeboden, niet als feit of opdracht.

De eerste conditie wordt **vóór de eerste modelaanroep** voor alle zes casussen evenwichtig, cryptografisch willekeurig toegewezen (3× A eerst, 3× B eerst). De complete allocatie wordt vóór de eerste providercall in het ruwe artifact vastgelegd. Op T2 wordt de volgorde omgekeerd. Dit controleert positie-effecten, maar maakt het aantal onafhankelijke casussen niet groter.

Het verschil in informatielengte tussen `NONE` en een echte seed blijft bestaan. Dit A/B-contrast meet het *toevoegen van de kandidaattekst binnen deze onderzoeksopzet*, niet uniek het effect van een gewichtloos geheugenmechanisme. De sterke zoekinstructie en gewone notities in beide armen zijn expliciete concurrerende verklaringen. Een volgende gerichte placebo-/notitievergelijking met meer onafhankelijke casussen blijft nodig.

## Wat we als echte voortgang beschouwen

| Waarneming | Wat hij kan laten zien | Wat hij NIET bewijst |
| --- | --- | --- |
| Echte T0-detectorgeboorte, gecontroleerde herkomst | Modelgerelateerde kandidaat is opgeslagen na gewone generatie | Dat de kandidaat voordien als afzonderlijke interne representatie bestond |
| Identieke A/B-prompt buiten seedveld, T1 | Invloed van de expliciet aangeboden kandidaattekst op *zichtbaar gedrag* in één scenario | Uniek Shadowseed-effect boven extra context |
| Bewaard, onbewezen alternatief in output | Mogelijk tekstueel behoud van een niet-gekozen hypothese | Conceptuele verandering of betekenisvolle nieuwe onderzoekbaarheid |
| T1→T2 eigen onderzoeksvragen over verschillende externe waarnemingen | Onderzoekspaden kunnen vervolgvraagvorming verschuiven, onder vast bewijs | Dat een door model voorgestelde proef werkelijk is uitgevoerd |
| T2-vraag die conditioneel een ander toetsbaar experiment opent | Kandidaat voor Q2-vraagvorming, nog zonder echte bevestiging | Een externe Q2-doorbraak of nieuw ontdekte werkelijkheid |
| Geen T0-geboorte, ongeldige JSON, `NONE`, verlopen seed of checkpointfout | Werkelijke negatieve of onvolledige trajecten; blijven zichtbaar | Nul-effect van Shadowseed bij een niet-uitgevoerde vergelijking |

**Onafhankelijke beoordeling** blijft noodzakelijk: beoordeel gepaarde T1- en T2-antwoorden blind op behoud, inhoudelijk andere vraagfamilie, onderscheidende test, afhankelijkheid tussen de vragen en het vermijden van echo/parafrase. De casus/seedtrajecten vormen de eenheid van analyse, niet tokens, zinnen of losse API-calls. Deze zes openbare cases kunnen hoogstens een **verkennend** signaal geven, geen betrouwbare populatie-effectgrootte.

## Falsificatie en filosofische tegenverklaringen

We proberen **niet** een positieve score af te dwingen. De [H0–H5-mechanismen](../first-principles-reorientation-2026-10-25.md) blijven concurreren. Een gewone sterke GPT-5 die zonder seed dezelfde onderscheiden vervolgonderzoeken ontwikkelt, is een sterke negatieve uitslag voor extra Shadowseed-bijdrage. Het kopiëren van de seed zonder andere test is onvoldoende. Een nieuwe vraag die uitsluitend mogelijk is doordat de onderzoeker nieuwe meetgegevens heeft geschreven, is geen zelfstandig gecreëerde mogelijkheid. En wanneer de werkelijke detector géén gewichtloze seed vindt, **verzinnen we er geen**.

Ook het oorspronkelijke anti-embedding-beeld blijft uitsluitend een *filosofische metafoor*, geen gedefinieerde inverse vectorruimte of bewijs van introspectie. H-Neuron/interne activatieonderzoeken zijn een aparte Q1-route. Aan de bestaande product-Gate, trace, TTL en TrTL verandert niets.

De **Q2-ambitie** verlangt op termijn een afzonderlijke RI-proef waarin het model zelf een toelaatbare test voorstelt, een onafhankelijke evaluator die test daadwerkelijk uitvoert en het model vervolgens een *nieuwe, anders onderzoekbare* vraag uit het resultaat kan ontwikkelen. De huidige proef is eerlijk gelabeld **RF**, niet RI.

## Uitvoeringsafspraken en stopgrenzen

- Zes **vooraf gekozen** openbare cases, drie beurten per case. **Geen casussen verwijderen** wanneer er geen seed komt of een model stopt. Een mislukking wordt niet als `NONE` of als nul-effect geteld.
- Maximaal **14 GPT-5-modelcalls per casus, 24 embeddings per casus en 65.000 providergerapporteerde tokens per casus**. Totale bovengrens 84 modelcalls en 390.000 geregistreerde tokens. Door detector/host/no-seed kunnen minder calls plaatsvinden. Geen verborgen provider-retry.
- Eén GitHub Action vanuit de bestaande afgesloten `OpenAI key`-omgeving, uitsluitend na no-network preflight. Geen nieuwe sleutels, geen secret in bestanden. Een AI-modelantwoord wordt nooit achteraf vervangen.
- De onderzoekscode bewaart de ruwe T0-T2-stappen, alle providerreceipts, echte eerste seedgeboorte (of expliciet ontbreken), verificatie van gewicht nul, A/B-allocatie, eigen vervolgvragen en alle uitvalreden(en). Bij individuele fout gaan de overige vooraf gekozen casussen verder, zonder de fout te verbergen of de foute casus opnieuw te betalen.
- Geen automatische semantische score, geen **G0 PASS**, geen onafhankelijk Q1-bewijs, geen gevalideerde Q2-verbreding door deze run. De twee werkelijk onafhankelijke G0-beoordelingen staan open onder [#234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) en [#235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235).

**Go/no-go voor wetenschappelijke claim:** pas na onafhankelijk beoordeelde vraagfamilies, een grotere vooraf ingeschreven set nieuwe casussen en een werkelijke RI-uitvoer. Een positieve pilot rechtvaardigt hoogstens nader onderzoek, geen nieuwe productarchitectuur.
