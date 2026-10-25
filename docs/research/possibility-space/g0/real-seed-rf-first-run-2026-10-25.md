# RF-verkenning: eerste echte GPT-5-onderzoeksvragen en gecontroleerde stop

> 25 oktober 2026. **Feitelijk resultaat van [Action #40224494313](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224494313).** Alleen voorlopige waarnemingen, geen G0-goedkeuring, onafhankelijke semantische beoordeling of aangetoonde Q1/Q2-werking.

## Werkelijk uitgevoerd

- **430 geslaagde en 3 overgeslagen** offline researchtests vóór de betaalde modelcalls. De Action sloot de live-run af als **failure**, maar publiceerde het gedeeltelijke `observed.json` onder artifact `g0-real-seed-rf-inquiry-40224494313`.
- **14 afgeronde GPT-5-modelaanroepen**, plus embeddingaanroepen; **37.503 providergerapporteerde tokens**.
- T0: twee extra gewone antwoorden, een echt hostantwoord, daarna een echte detectorwaarneming met de bestaande `current_pair`-prompt, intake en **gecontroleerde geboorte** van seed `ss_001`. De originele kandidaat was: “Onbekende ruimtelijke offset: de twee sensoren bemonsteren mogelijk niet exact dezelfde plek/volume van het materiaal, waardoor lokale, echte transiënten alleen in kanaal 1 verschijnen.”
- T1: een nieuwe vooraf geschreven externe waarneming; een echt gewoon GPT-5-antwoord en afzonderlijke detectie. De eerste seed kreeg een geldige bestaande meerturnscheck. Daarna gaf GPT-5 in **alle vijf** afzonderlijke onderzoeksarmen een syntactisch geldige JSON-onderzoeksvraag.
- T2: een nieuwe externe waarneming; host en detector voltooiden hun werk. **De daaropvolgende meerturnscheck voor de oorspronkelijke seed wierp een `ValueError`.** De runner stopte terecht voordat de vijf T2-onderzoeksarmen werden uitgevoerd. De precieze onvervulde invariant is in deze run helaas niet opgenomen. De runner rapporteert de foutklasse, geen fouttekst; we kunnen uit het bestaande artifact dus niet afleiden of het om historische consistentie, bewijsstatus, eventlog of een andere checkpointvoorwaarde ging.

## De vijf T1-vragen in gewone woorden

| Arm | Model stelde een vraag over |
| --- | --- |
| A, gewone generatie | Of uitschieters binnen een kort tijdvenster na schakelgebeurtenissen optreden |
| B, doelbewust zoeken | Of meetpieken rond precieze schakelranden clusteren |
| C, gewone notities | Of pieken direct rond schakelkanten samenvallen |
| D, echte gewichtloze Shadowseed | Of pieken systematisch samenvallen met schakelmomenten van de regelkast |
| E, andere echte T0-detectorwaarneming | Of de frequentie van pieken rond schakelmomenten significant hoger is |

**Voorlopige inhoudelijke observatie:** alle vijf voorstellen liggen in dezelfde algemene familie van *tijdelijke samenhang met schakelmomenten*. De originele D-seed ging juist over mogelijke **ruimtelijke verschillen tussen de meetpunten**. De feitelijke D-vraag volgde die richting op T1 niet duidelijk. Dit is geen onafhankelijke blindbeoordeling en betekent evenmin dat de kandidaat het model intern niet beïnvloedde. Wel is er op dit moment **geen zichtbaar D-specifiek voordeel**.

Er is geen onafhankelijke meting uitgevoerd als reactie op een van deze vijf vragen. Het volgende externe T2-resultaat was vooraf door de onderzoeker geschreven. **RF is geen RI** en kan geen ander feitelijk onderzoeksgevolg aantonen.

## Wat T0 suggereert, maar niet bewijst

De eerste seed kwam uit de echte detector, na drie gewone T0-antwoorden (twee replicaties en één hostantwoord). De concrete formulering over een ruimtelijke meetpuntverschuiving was daarin niet duidelijk als afzonderlijke hypothese zichtbaar. Dit is slechts een handmatige beschrijving van drie kleine outputvoorbeelden, geen geschatte kansverdeling of interne activatiemeting. Het model kan de relatie op een andere manier impliciet verwoord hebben; een onafhankelijke semantische codering ontbreekt.

## Extra controle zonder API-aanroepen

Na de mislukte run is een nieuwe regressietest toegevoegd met **meerdere kandidaat-geboorten op T0, T1 en T2**, via de echte Engine en een gesimuleerde provider. Deze is [in GitHub Action #40224969754](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224969754) geslaagd. De totale researchsuite komt daarmee op **431 geslaagd, 3 overgeslagen**. De test reproduceert de specifieke live-fout **niet**. We mogen de eerste failure niet zonder diagnose aan een bewezen productbug of een bewezen modelgedrag toeschrijven.

## Technische vervolgstap

De huidige onderzoeksrunner bewaart de brongegevens en hostrapporten, maar slaat vóór een falende `freeze_weightless_followup` niet het precieze faalargument of een beperkte manager-state-snapshot op. Een volgende run moet minstens de **gesloten, toegestane foutcode** en de hashes van het relevante eventledger-prefix vastleggen, zonder sleutel, intern redeneringsspoor of onbewezen autoriteit te publiceren.

Zonder dat herstel starten we **geen nieuwe betaalde run**. De v1-uitvoer blijft intact en de runner blijft research-only. Q1 blijft een gedragsvraag en Q2 is nog niet onafhankelijk aangetoond. Ook G0 blijft `NOT PASSED`.

## Instrumentcorrectie na deze run

Er is een fail-closed diagnostiek toegevoegd die bij een volgende afwijking de **vaste checkpoint-foutcode**, de verwachte en werkelijk berekende event-/Gate-/historyprefix-hashes en de nul-autoriteitsstatus in het gedeeltelijke onderzoeksartifact bewaart. De normale `freeze_weightless_followup` is **niet** aangepast of overgeslagen. Een nieuwe negatieve no-networktest simuleert een tweede-follow-up-fout en verifieert dat T2 niet alsnog modelvragen genereert. Dit is nog **geen diagnose van de oorspronkelijke ValueError** en geen reden voor een automatische betaalde herhaling.

Laatste offline verificatie: [run #40225139146](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40225139146), **432 tests geslaagd, 3 overgeslagen**. De nieuwe negatieve test verifieert dat een geforceerde T2-checkpointfout de T2-onderzoeksvragen niet uitvoert en de foutcode en niet-gevoelige prefixcontrole bewaart. Deze injectietest reproduceert **niet** de oorspronkelijke foutoorzaak.
