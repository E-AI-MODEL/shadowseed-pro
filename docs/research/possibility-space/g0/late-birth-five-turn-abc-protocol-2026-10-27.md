# G0: prospectieve T0- en late-geboortecohorten, twee echte vervolgbeurten

> 27 oktober 2026. Gestapelde, **uitsluitend verkennende** research op PR #256. Geen betaalde modelrun gestart, geen onafhankelijke wetenschappelijke review, G0 **NOT PASSED**.

## Waarom een andere proef nodig is

De vorige zes-casus A/B-studie bevatte 67 GPT-5-aanroepen, maar slechts twee complete A/B-paren. In twee andere casussen ontstonden na T0 wel nieuwe kandidaten terwijl de T0-intake ze niet toeliet. Dat is een beperking van de **T0-selectieregel**, niet het bewijs dat Shadowseed iets nieuws heeft gecreëerd. De oude ruwe data en oorspronkelijke validator blijven bevroren.

Voor de volgende proef zijn zes **nieuwe, openbare, door de onderzoeker geschreven fictieve casussen** vastgelegd in `research/fixtures/g0_late_birth_rf_v2.json`. Deze zijn niet onafhankelijk gecreëerd, niet afgeschermd en kunnen **niet** worden gebruikt als een geheime confirmatieset.

## Feitelijk protocol

Elke casus doorloopt de ongewijzigde `ShadowseedEngine.prepare_turn → gewone modelgeneratie → observe_turn` vijf keer. De bestaande echte `OpenAIDetectorBackend(current_pair)` en de canonieke intake bepalen op elke beurt of er een echte nieuwe, gewichtloze seed ontstaat. Geen fictieve vervanging en geen verandering aan Gate, SSOT, trace, TTL/TrTL of de gewone productprompt.

De zes cases zijn **vóór de modelaanroepen** ingedeeld in twee cohorten:

- Twee cases met selectie uitsluitend uit de allereerste echte geboorte op **T0**.
- Vier cases met selectie uitsluitend uit de eerste echte nieuwe geboorte op **T1 of T2**. Geboorten op T0 worden bij deze gevallen **wel geregistreerd**, maar niet achteraf alsnog geselecteerd. Geboorten op T3/T4 blijven eveneens in het logboek, zonder retrospectieve uitkomstselectie.

Elke geselecteerde kandidaat moet **op twee latere volledige beurten** een onveranderde identiteit, herkomst en gewichtloosheid door de bestaande `freeze_weightless_followup`-controle behouden. Een kandidaat die pas bij T2 geboren wordt, krijgt dus T3 en T4 als follow-up. Uitval, een geweigerde eerste geboorte of een checkpointfout worden niet als nul-effect geteld. Twee of meer nieuwe seeds op dezelfde beurt geven geen cherry-picking: de eerste werkelijk canoniek geaccepteerde, verse seed wordt gekozen, de rest blijft in het logboek.

## De vergelijking

De gewone gebruiker/host ziet **geen** gewichtloze seed. Alleen de afzonderlijke onderzoeksaanroepen krijgen de kandidaat als onbewezen, expliciet niet-autoritatieve extra tekst.

- **A:** hetzelfde sterke model, gewone gesprekken, dezelfde neutrale notitie, sterke zoekinstructie, in extra veld `NONE`.
- **B:** exact dezelfde middelen en geschiedenis, in het extra veld de echte op T0/T1/T2 geboren gewichtloze kandidaat.
- **C:** dezelfde middelen en een generieke, vooraf gekozen irrelevante tekst van **dezelfde tekenlengte** als B.

Een C-placebo van gelijke tekenlengte is **niet semantisch gelijkwaardig en niet exact token- of overtuigingskrachtgematcht**. Hij controleert een deel van het 'er staat extra tekst'-effect, niet alle concurrerende verklaringen. Op de tweede onderzoekbeurt mogen de condities uitsluitend hun **eigen, nog niet uitgevoerde** eerdere onderzoeksvragen terugzien. Alle externe T1-T4-waarnemingen zijn vooraf geschreven en in iedere conditie identiek: **RF, niet RI**.

Per case wordt de A/B/C-aanroepvolgorde vóór de eerste modelaanroep bepaald. Over zes cases hebben alle drie even vaak de eerste positie. De tweede onderzoekbeurt roteert de volgorde. Het eerste A/B/C-antwoord verschilt uitsluitend in het gemarkeerde onbewezen kandidaatveld, plus eventuele onvermijdelijke lengteverschillen voor NONE. Bij de tweede beurt kan de eigen eerdere vraagstelling het pad mede bepalen. Dit is **geen** directe observatie van een interne LLM-representatie.

## Meetuitkomsten en uitval

De uitvoer bewaart echte Engine-rapporten, alle nieuwe geboorten en niet-geselecteerde geboorten, de gekozen eerste echte seed, T1/T2/T3/T4-checkpoints, onverkorte modelvragen, ongeldige JSON, providerreceipts, promptlengtes, hashes en volledige niet-gehaalde gevallen. Voorlopig telt software uitsluitend: compleet traject, geen toelaatbare geboorte, technisch onvolledig, geldige/ongeldige modeloutput.

Er is **geen automatische semantische effectscore**. Pas na een onafhankelijke, daadwerkelijk blinde menselijke beoordeling kan worden gevraagd of B inhoudelijk een andere testfamilie ontwikkelde dan A en C. Een aparte **A/B/C-blindering** is nu als code toegevoegd in `g0_late_birth_blind_review.py`. Die maakt een eerste beoordelingsdossier met drie geanonimiseerde onderzoeksroutes, de volledige gewone context en lege beoordelingsvelden, zonder bronseed of armnaam. Een ander, afgeschermd eigenaarsbestand bewaart de volledige zes-casustelling, de echte seed en de codesleutel. Beide menselijke beoordelingen moeten eerst onafhankelijk zijn afgerond voordat de eigenaarssleutel vrijgegeven mag worden. Dat wordt niet automatisch gedaan. De modeltekst zelf kan de conditie alsnog gedeeltelijk verraden. Los daarvan moeten de onafhankelijke technische en conceptuele G0-reviews (#234/#235) nog plaatsvinden.

De prompt is maximaal 12.500 tekens, de antwoorden volgen de exact beschreven JSON-schema's en de eerdere v1-data krijgen geen reparatie. Het onderzoek is begrensd op maximaal 19 modelcalls, 48 embeddings en 65.000 providergerapporteerde tokens **per casus**, dus hoogstens 114 modelcalls, 288 embeddings en 390.000 tokens totaal. De normale 5-turns-hostgeschiedenis wordt niet ingekort of heimelijk samengevat. Een te lange prompt maakt het traject technisch onvolledig.

## Uitvoering en beslisgrens

De nieuwe code staat in `g0_late_birth_cohort.py` en `g0_late_birth_real_rf.py`; de tests gebruiken **FakeProvider met echte Engine** en doen **geen** API-aanroep. Er is in deze PR **uitsluitend een offline CI-workflow**, geen netwerk-runner en geen betaalde GitHub Actions-trigger.

**Geen G0 PASS, geen algemene modelprestatieclaim en geen Q2-wereldverandering.** De volgende echte modelproef kan alleen als afzonderlijk begrensde verkennende run worden besloten, met expliciete vastlegging van broncommit, kosten, drie-arm-blindering, reviewstatus en bewaarde originele noemers. Een confirmatieve wetenschappelijke claim wacht op onafhankelijk technisch/conceptueel G0-oordeel, nieuwe afgeschermde casussen en echte RI-onderzoekshandelingen.
