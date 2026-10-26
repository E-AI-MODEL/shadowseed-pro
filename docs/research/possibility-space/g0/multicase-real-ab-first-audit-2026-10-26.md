# Zes-casus A/B: ruwe uitvoering, negatieve uitkomsten en methodefouten

> 26 oktober 2026. **Onvolledige verkennende modelstudie, geen onafhankelijke wetenschappelijke effectbeoordeling.** G0 blijft `NOT PASSED`. Ruwe resultaten worden niet aangepast, vervangen of achteraf als een geslaagde zes-casus A/B-studie gepresenteerd.

## Ongewijzigde bron

- Werkelijke [GitHub Action #40402783698](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40402783698), source commit `1aea4cf62c4e7717a533ffa6f0945577b8137f08`, status **failure** door de opzettelijke eindcontrole op incomplete casussen.
- Artifact `multicase-real-ab-raw-owner-40402783698`: origineel `observed.json` SHA-256 **`b56f03d9fe7a18011812db7d88e7b62b5b63b9724f6e2d3e77dad4fc8876e505`**; aparte eigenaarssleutel. Het gepubliceerde geblindeerde artifact is `multicase-real-ab-blind-40402783698`.
- Een modelvrije onafhankelijke reconstructie van beide volledig afgeronde paren en de bronadministratie is uitgevoerd in [Action #40408066000](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40408066000): **14 tests geslaagd**, ruwe SHA gecontroleerd, identiteiten/turnvolgorde/checkpoints en echte A/B-prompt-hashes opnieuw opgebouwd. Ook hiermee is de werking van een kandidaat nog niet onafhankelijk vastgesteld.

## Feitelijke omvang

| Onderdeel | Werkelijk |
| --- | ---: |
| Vooraf vastgelegde fictieve RF-casussen geprobeerd | **6/6** |
| Volledige T1 + T2 A/B-paren | **2** (C04, C05) |
| T0 zonder geaccepteerde seedgeboorte | **2** (C01, C06) |
| Onvolledig, technisch gestopt | **2** (C02, C03) |
| GPT-5-modelaanroepen | **67** |
| Embeddingaanroepen | **36** |
| Providergerapporteerde tokens | **151.982** |
| Opgeslagen onderzoeksvraag-antwoorden op T1/T2 | **13** |
| Daarvan parsebaar als JSON met twee modelvragen | **13** |
| Daarvan geldig onder strenge vooraf vastgelegde validator | **7** |
| Daarvan inhoudelijk niet automatisch goedgekeurd wegens te veel alternatieven | **6** |
| Onafhankelijke semantische menselijke beoordelingen | **0** |

**Let op:** de 13 onderzoeksvraagrecords zijn niet 13 onafhankelijke casussen en niet alle zes trajecten zijn compleet. De zes 'ongeldige' records zijn **wel geldig JSON met werkelijke, door het model geformuleerde vragen**. Het gespecificeerde formaat verbood meer dan drie items in `unresolved_alternatives`, maar de instructie vroeg niet expliciet om die beperking. Het model genereerde vijf tot zeven alternatieven. De oude validatoruitslag is dus terecht volgens het vooraf geldende contract, maar **niet** hetzelfde als 'geen onderzoeksvraag' of 'geen denkbare mogelijkheden'.

## Het T0-criterium bleek inhoudelijk te smal

| Casus | T0-geaccepteerde eerste seed? | Latere geregistreerde nieuwe kandidaten | A/B-status |
| --- | --- | --- | --- |
| C01, metingen/instrumentvolgorde | Nee; alle drie T0-items afgewezen als `not_atomic` | **2 op T1** | Buiten T0-A/B, niet nul-effect |
| C02, catalogi | Ja, een eerste echte seed | **3 nieuwe op T2** | Incompleet |
| C03, systeemvertraging | Ja, twee echte T0-seeds | Geen op T2 | Incompleet |
| C04, geluidsopnamen | Ja, twee echte T0-seeds | Nieuwe op T1 en T2 | Volledig |
| C05, werkplaatsbeoordeling | Ja, een eerste echte seed | Nieuwe op T1 en T2 | Volledig |
| C06, identieke exportlijsten | Nee; alle drie T0-items afgewezen als `not_atomic` | **2 op T2** | Buiten T0-A/B, niet nul-effect |

De twee T0-negatieve casussen zijn **niet** 'geen seed ooit': de canonieke Engine registreerde juist later nieuwe kandidaten. Ze mogen niet achteraf in het oorspronkelijke gerandomiseerde T0-cohort worden geschoven. Dit is wel een rechtstreeks waarneembare beperking van onze onderzoekskeuze. Een mogelijke relatie kan ontstaan of pas toegelaten worden **nadat** de context verandert. Dat raakt de originele filosofische Q1/Q2-vraag en is inhoudelijk meer dan een geheugentest.

In C01 en C06 wees de bestaande intake op T0 alle drie gedetecteerde kandidaten af als `not_atomic`. Dat is een echte productregel die we voor deze proef **niet** veranderen. De wetenschappelijke kwestie of samengestelde/voorwaardelijke relaties daardoor te vroeg uit beeld verdwijnen is **nog niet getest**. Een afgewezen kandidaat wordt niet stiekem een nieuwe gewichtloze seed, en geen enkele proef mag daardoor de Gate omzeilen.

## Wat ging er fout in de twee incomplete gevallen?

**C02 (catalogi): reproduceerbare promptlimiet.** T1: A leverde twee protocolgeldige onderzoeksvragen, B leverde JSON met twee echte vragen maar **zes** onbewezen alternatieven en kreeg de status `invalid`. Op T2 had B geen geldig eigen eerder vragenrecord en gaf toch één nieuwe geldige vraaguitvoer. De oorspronkelijke **A-T2 prompt** werd uit de bewaarde gewone geschiedenis en eigen geldige T1-vragen exact opnieuw opgebouwd: **13.197 tekens**, terwijl de research-provider `MAX_PROMPT_CHARS=12.500` accepteert. Daardoor werd **de tweede T2-modelaanroep niet gedaan**. Dat is aantoonbaar een limiet van deze onderzoeksrunner, geen valide nuluitkomst of vastgesteld Shadowseed-falen.

**C03 (webserver/wachtrij): foutreden niet bewaard.** T0 en T1 zijn wel compleet; zowel A als B gaf op T1 twee geldige vragen. T2-host en detector zijn volgens echte providerreceipts voltooid en er is een T2-rapport, maar de T2-seedcheckpoint ontbreekt en daarna volgde geen A/B-onderzoeksvraag. De foutklasse was `ValueError`. **De volledige fouttekst en relevante T2-mutation-state zijn niet gearchiveerd.** We kunnen de exacte oorzaak niet reconstrueren zonder extra bewijs. Geen automatische reparatie of betaalde herhaling.

**C04 en C05:** de technische T1/T2-canonieke checkpoints en gepaarde prompt-hashes bleken sluitend. Beide leverden twee modelantwoorden per beurt, maar drie van de vier C04-outputs en nul van de vier C05-outputs voldeden aan het strenge JSON-schema. In C05 zijn alle vier JSON-teksten wel inhoudelijk voorzien van twee onderzoeksvoorstellen. Deze tekstoutput is geen onafhankelijke Q2-validatie.

## Filosofische en technische consequentie

De oorspronkelijke vraag blijft **letterlijk** staan in [possibility-space-thesis.md](../../possibility-space-thesis.md). Onze onderzoeksoutput toont afzonderlijk (a) detectie en toelating, (b) latere geboorte onder andere context, (c) exacte gewichtloze herkomst, (d) een modelvraag die de seed kent of niet, en (e) een echte externe latere toets. Alleen (a)-(d) zijn hier gedeeltelijk onderzocht. **(e) is niet uitgevoerd**. Een andere kandidaattekst of meerdere voorstellen betekenen niet vanzelf dat de effectieve onderzoeksruimte veranderde.

De volgende versie moet zonder resultaatmassage de onderzoekstechniek verbeteren: de **volledige** gewone productgeschiedenis blijft ongewijzigd, maar de afzonderlijke onderzoeksprompt krijgt een vooraf gedocumenteerd maximaal contextbudget om omvangsuitval te voorkomen; het antwoordformaat moet letterlijk overeenkomen met het validatorschema; alle uitzonderingen moeten vóór het verlaten van hun fase met een veilige foutcode en geplande invoerlengte worden vastgelegd. Opgenomen eigen vragen van T1 zijn onbewezen en mogen nooit als T2-waarnemingen gelden. T0- en **later geboren** kandidaten vergen afzonderlijke cohortregels en een langere horizon, anders verwarren we ontstaan met behoud.

Voor echte causale meerwaarde moet een volgende vooraf gekozen nieuwe set ook **gelijke sterke modelzoekstrategie, gewone notities, inhoudsgelijke placebo, seedgewicht=0, geblindeerde externe beoordeling** en uiteindelijk een afzonderlijke toegestane RI-uitvoering behouden. De procedure van een positief experiment mag de oorspronkelijke vraag niet reduceren tot 'meer tekst' of 'betere antwoorden'.

**Besluit:** PR #255 blijft draft. G0 NOT PASSED. Geen nieuwe betaalde run op dezelfde reeds ingeziene zes casussen. Eerst onderzoeksfouten afzonderlijk isoleren, de nul- en uitvalgevallen behouden en een nieuwe studieversie vastleggen.
