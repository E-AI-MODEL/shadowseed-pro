# Verkennende modelproef zonder voortijdige G0-claim

> 25 oktober 2026. **Voorstel voor een eerste echte, begrensde modelrun; nog geen resultaat zolang geen Actions-artifact beschikbaar is.** Status onafhankelijke G0-v3-review: **NOT PASSED**. De bestaande verplichting tot onafhankelijk toetsen blijft onverkort van toepassing op bevestigende Q1/Q2-claims.

## Waarom nu toch een modelproef?

G0 stelt hoge eisen aan een *bevestigende* studie over het ontstaan van nieuwe onderzoekbare mogelijkheden. Daarvoor ontbreken twee onafhankelijke deskundigenoordelen, beschermde nieuwe testgevallen en een algemene toets van onvoorziene modelvragen. Dat maakt de huidige bewering over een effect onhoudbaar, maar hoeft een **verkennende technische live-proef** niet te verbieden. De oude absolute NO-GO voor *alle* live modelcalls was een zelfgekozen onderzoeksbeperking. Deze proef wordt als expliciete verkenningsuitzondering vastgelegd, zonder G0 of de oorspronkelijke these te wijzigen.

[Geaccepteerde meerturnsregistratie, PR #249](https://github.com/E-AI-MODEL/shadowseed-pro/pull/249) kan de eerste echte kandidaat via canonieke observaties volgen. In de eerdere 30-call GPT-5-compressieproef ontbrak dit complete `ShadowseedEngine.prepare_turn → hostantwoord → observe_turn`-traject. Deze proef gebruikt precies dat traject, geen kopie.

## Stappen, zonder het onderzoek in één prompt te proppen

- **T0, gewone generatie:** de host vraagt GPT-5 om een gewoon antwoord op een fictieve waarneming. Twee extra gewone antwoorden worden vóór de detector aangemaakt. Dit is slechts een ruwe, kleine gedragsreferentie, geen geschatte interne kansverdeling.
- **T0, gescheiden detectie:** het bestaande `OpenAIDetectorBackend(prompt_variant="current_pair")` gebruikt de vraag, het echte zichtbare eerste antwoord en toegestane schone voorgeschiedenis. De canonieke parser en intake kunnen ook `NONE` leveren. De eerste daadwerkelijk geaccepteerde, nieuwgeboren seed wordt meteen via `freeze_canonical_weightless_birth` vastgelegd. De onderzoeker kiest geen 'mooiste' seed achteraf.
- **T1, T2, T3, afzonderlijk:** per beurt pas een nieuwe externe waarneming; de host maakt weer een gewoon antwoord zonder seedcontext. Detector, manager, Gate en lifecycle zijn dezelfde blijvende engine. `freeze_weightless_followup` verifieert per beurt identiteit, herdetectie, trace, TrTL, weigering of levenscyclusverloop.
- **NONE-controle:** tweede canonieke Engine met opzettelijk lege detector krijgt exact dezelfde hostantwoorden. Dit controleert dat de gewone antwoordroute niet stiekem door gewichtloos geheugen wordt veranderd, **niet** of SSL beter is dan gewone notities.
- **Uitvoer:** echte ruwe output en originele auditrapporten per beurt; model-ID, API-response-ID, input-/outputtokens, hash en aantal verzoeken. Geen API-sleutel in log of artifact. Fouten, `NONE`, ongebruikte kansen, ongeldige parsing en afwijzingen blijven in de ruwe observatie zichtbaar.

## Beperkingen en kostengrens

De twee fictieve **publiek zichtbare** cases zijn: een meetinstallatie met nog niet uitgezochte tijdregistratie en een stabiele administratieve telcontrole. De toekomstige gegevens zijn vooraf door de onderzoeker geschreven, maar komen pas in hun eigen beurt in de prompt. De testcases zijn **geen geheime holdouts**. Er bestaat ook geen onafhankelijk vooraf gekozen `ideal_question` of score om succes te suggereren.

Provider: GPT-5 via de Responses API; embeddings: `text-embedding-3-small`. Maximaal 24 modelverzoeken (20 voorzien), 48 embeddingverzoeken, 85.000 gezamenlijk geregistreerde tokens en 1.600 modeloutputtokens per aanroep. Geen automatische retries; fout blijft fout. Een gedeeld onderzoeks-tokenplafond is geen gegarandeerd geldmaximum, en het uitgeschakelde automatisch herhalen beschermt tegen verborgen extra verbruik. De betaalde GitHub-Action mag uitsluitend handmatig beheerde **OpenAI key**-omgeving gebruiken; er wordt geen secret in code opgeslagen.

## Eerlijke uitkomstlabels

**Wel op te maken uit een geldige run:** model heeft zichtbare antwoorden teruggegeven; bestaande detector produceerde wel/geen kandidaten; intake liet kandidaten wel/niet toe; een specifieke seed werd echt geboren en bleef per beurt traceerbaar; weigeringen en werkelijk vergeten kandidaten blijven behouden; gewone antwoordprompt bleef onbeïnvloed.

**Niet op te maken:** intern niet-gekozen neuronale mogelijkheid, kans van niet-generatie, feitelijke semantische waarde of originaliteit, autonome nieuwe Q2-onderzoeksvraag, kandidaat-specifieke bijdrage boven krachtige B/C-controles, of goedkeuring van G0.

Voor Q2 is een **volgende, gescheiden** studie nodig waarin het model zélf later een onverwachte onderzoeksvraag voorstelt, die een onafhankelijke algemene toets kan uitvoeren. De Q1/Q2-comparaties A/B/C/D/E, RF/RI-scheiding, volledige kostenvergelijking en onafhankelijke beoordeling uit [het bestaande evaluatiecontract](adapter-evaluation-contract-2026-10-25.md) blijven vereist voor een echte effectclaim.

## Stopregels

Uitblijvende `OPENAI_KEY`, inconsistente chronologie, ontbrekende providerusage, responsefout, onbedoelde antwoordinvloed, positieve seedgewicht-/evidencewaarde, onbetrouwbare detectorherkomst, budgetoverschrijding of mislukte no-network preflight stopt de live-run. Geen tweede Gate, gewijzigd TrTL/TTL, ander promptcontract, of live-run in reguliere GitHub-product-CI. Het onderzoeksresultaat wordt als **verkennende observatie** gepubliceerd, nooit als G0-PASS.
