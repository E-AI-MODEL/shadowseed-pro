# Frontier-jewels: eerste live vergelijking, 4 november 2026

Twee fictieve onderzoeksproblemen, F02 (latere tegenspraak) en F04 (latere steun), vijf condities en tien tweebeurttrajecten. In iedere tweede beurt ontvangt het model exact zijn eigen eerste antwoord en de later bekend geworden informatie.

De vijf condities zijn: gewoon gesprek, gewone notitie, kandidaat vroeg, kandidaat pas na nieuwe informatie, irrelevante notitie. De volgorde is vooraf deterministisch gehusseld. GPT-6.1 Sol wordt direct via de Responses API bevraagd. Geen extra tooling en geen automatische herhalingen.

**Vraag:** houdt een vroege kandidaat een bruikbare onderzoekstoets vast, of vernauwt hij de vraag juist? Vooral bij F02 hoort het model de eerder vermoedelijke diepteverklaring te laten vallen zodra de nieuwe meting die weerspreekt.

**Kosten en toegang:** de bestaande GitHub Actions Environment `OpenAI key` levert `secrets.OPENAI_KEY`. De sleutel blijft buiten het repositorybestand en de logs. De runner reserveert conservatief en stopt bij een geraamd totaal van 0,50 USD. Werkelijke facturering kan afwijken van de raming. Bij een providerfout wordt niet automatisch herhaald.

**Uitkomst en grenzen:** de job bewaart per oproep zijn prompt, antwoord, response-ID, tokentelling en checksum. Beoordelingsformulieren worden blind op conditie gemaakt. Dit is een verkennende proef met door de onderzoeker geschreven kandidaten, geen bewijs voor autonoom ontstaan van seeds of werking van de ShadowSeed Gate. Eén traject per combinatie levert nog geen statistische effectclaim op.

**Oorsprong:** onderzoeksgenerator uit het eerder lokaal geteste ShadowSeed-frontier-proefpakket. Bronmateriaal: `research/atlas/` en de historische modellenarchieven. Geen wijziging van bestaande bronuitvoer of productcode.
