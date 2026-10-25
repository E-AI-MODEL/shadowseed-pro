# G0: identificatie van het causale onderzoekskanaal voor gewichtloze seeds

> **Status:** voorgestelde onderzoeksvoorwaarde, 25-10-2026. **Geen productwijziging, geen experimentele autorisatie, geen G0-goedkeuring.**
> Onderwerp: hoe onderzoekt een LLM later een **onbewezen, gewichtloze** kandidaat, zonder haar ongemerkt in het gewone antwoord te gebruiken?

## Vastgesteld in de bestaande implementatie

De [bestaande productcode](../../../../src/shadowseed/chat.py) (`prepare_turn`, rond L1167–1247 in commit `372a2b8`) haalt alleen **eligible promoted seeds** op voor mogelijke prompt-surfacing, na de bestaande context- en autorisatiecontroles. Een nieuwe `weight=0`-seed is niet automatisch eligible. Dat is een **noodzakelijke productbescherming**. De [geslaagde PR #232-proef](real-shadowchat-discoveryworld-bridge-2026-10-25.md) bevestigde bij twee dezelfde onafhankelijke werelden en dezelfde onderzoekeracties **nul influence records, nul Gate-promoties en identieke hostantwoorden**.

Daaruit volgt een beperking voor de *onderzoeksmethode*, geen fout in het product:

**Als D (gewichtloze seed opgeslagen) en E (dezelfde seed weggenomen) allebei uitsluitend het gewone antwoordmodel gebruiken, zonder enig apart toegestaan toegangspad tot de seed, dan mag het experiment niet verwachten dat die seed later een andere vraag veroorzaakt.** Een nulverschil volgt dan uit de experimentele toegang, niet uit een weerlegde filosofische these. Omgekeerd bewijst het aanbieden van een seed als tekst in een prompt **op zichzelf niets anders** dan een extra observatie-/promptinterventie; er zijn sterke controles nodig.

De [adapternotitie](../adapter-not-model-improver-2026-10-25.md) maakt reeds onderscheid tussen host, bestaande Shadowseed en een **hypothetische aparte research adapter**. De [stap-1-notitie](../step1-model-signals-gap-origin-2026-10-25.md) staat toe gewichtloze kandidaten *als hypothese* in een geïsoleerde onderzoekstaak te bevragen, niet als onbewezen antwoordinstructie. Wat nog ontbreekt is een **afzonderlijk goedgekeurd, observeerbaar blootstellings-/interventiecontract** dat dit onderscheid afdwingt en meet.

## Twee verschillende routes; geen stille derde weg

| Route | Wat werkelijk gebeurt | Wat mag worden geconcludeerd |
| --- | --- | --- |
| **X — productconforme nulcontrole** | Host gebruikt `prepare_turn → gewone generatie → observe_turn` en krijgt geen niet-geautoriseerde gewichtloze kandidaat. Onderzoeker kan read-only seedstatus bekijken maar geeft haar niet aan het model door. | Test echte seedgeboorte, opslag, herdetectie en **afwezigheid van ongeautoriseerde invloed**. **Test niet** of een model door zo'n seed later een andere vraag kan maken. |
| **Y — afzonderlijk, nog te autoriseren onderzoekscontract** | In een **afgeschermde onderzoeksrol** (niet de gebruikersantwoordrol) kan een onafhankelijk geautoriseerde read-only probe **een specifieke bevroren kandidaat** met expliciete bron, onzekerheid en `unvalidated hypothesis` tonen om *een toetsbare onderzoeksvraag* voor te stellen. De handeling wordt pas door een onafhankelijk evaluatorcontract toegestaan of afgewezen. | *Zou* een eerlijk D–E-effect kunnen testen, mits kandidaatblootstelling en alle equivalente alternatieve modellen/notities als interventies worden vastgelegd. Het is **nog niet geïmplementeerd, toegestaan of gevalideerd**. |

Y is **geen standaard productroute**, geen invloedautorisatie, geen wijziging van Gate, point-of-use, trace, weight, TTL of TrTL. Een onderzoeksprompt waarin het model de kandidaat ziet is wél een **experimentele interventie die de onderzoeksoutput kan veranderen**; dat moet worden benoemd, gemeten en budget-gematcht. Als de bestaande ADR's ook die onderzoeksblootstelling verbieden, blijft Y **NO-GO** totdat een bevoegde beoordeling een aparte veilige uitvoering toestaat. De methode mag de productgrens niet omzeilen door iets 'read-only' te noemen.

## Prospectieve volgorde die de hele pijplijn bewaart

1. **T0 Q1/gewone modelgeneratie:** meet herhaalde spontane kandidaat-/vraagfamilies onder vastgepinde modelrevisie, sampling, context en budget **vóór** candidate-detectorblootstelling. Niet-verschijnen is budgetafhankelijk, geen bewijs dat de LLM de mogelijkheid intern niet heeft.
2. **T0 → kandidaat:** normale sterke modelantwoordgeneratie → **apart** huidige productdetector → ruwe respons/parse/normalize/intake → manager maakt een echte, contextgebonden **gewichtloze** seed, of expliciet `NONE`. Behoud alle afwijzingen, identity-merges, foutgevallen, zonder achteraf alleen succes te kiezen.
3. **T1 onderzoeksvoorstel:** uitsluitend indien Y apart is goedgekeurd, legt de geïsoleerde *research inquiry*-rol op een aparte, vooraf vastgepinde plek de exacte bevroren kandidaat als **onbewezen** hypothese voor aan een model. Het model bepaalt zelf een mogelijke onderzoeksvraag; de onderzoeker schrijft die niet voor. De reguliere gebruikersantwoordprompt is **niet** de ontvanger. In X ziet geen model de kandidaat.
4. **T2 onafhankelijke observatie:** in vooraf gekozen **RF** krijgt elke arm identieke bevroren externe vervolggegevens en hebben de voorgestelde acties daar geen effect op. In **RI** krijgt elke arm dezelfde begintoestand en toegestane actie-/kostenplafonds, maar de werkelijkheid van **zijn eigen** veilig toegelaten actie. Ongeldig, niet-toetsbaar, geen-opportunity en systeemfout blijven onderscheiden.
5. **T3 latere tweede onderzoeksvraag:** het model formuleert pas **nadat** de nieuwe observatie is vrijgegeven een *andere, zelfstandig controleerbare* vraag, of géén nieuwe vraag. Leg de precieze afhankelijkheid van kandidaat, interventie en onafhankelijke feedback vast, inclusief niets gevonden, triviale herhaling en betekenisverschuiving.
6. **T4 onafhankelijke vergelijking:** eerst twee menselijke beoordelaars met armgeblindeerde [reviewpakketten](blind-later-inquiry-review-handoff-2026-10-25.md) en sterke tegenhypothesen, dan pas ontblinden; effect/kosten/uitval/onzekerheid per regime; geen totaalscore die Q1, outputkwaliteit en Q2 samenvoegt.

**Nergens** mag de onderzoeksrol een productieantwoord als feit corrigeren, een ongevalideerde toolactie starten, een Gate-event vervalsen, zichzelf als menselijke onafhankelijke reviewer voordoen of verborgen modelredenering als observationeel bewijs registreren.

## Wat een sterke gelijke vergelijking vereist

- **A:** hetzelfde krachtige basismodel met dezelfde gewone informatie en toegestane middelen, zonder de specifieke seed.
- **B:** hetzelfde model met vooraf geregistreerde bewuste alternatievenzoektocht/diversificatie; alle extra calls en tokens meetellen.
- **C:** hetzelfde model met gewone, rijk genoeg gemaakte, even kostbare notities/volledige geschiedenis.
- **D:** dezelfde modelrevisie, met echte gewichtloze kandidaat in de **afzonderlijke onderzoeksrol Y**, onder vooraf expliciet toegelaten onderzoekscontext (nooit gebruikersantwoord of waarheid).
- **E:** dezelfde D-procedure met de **exacte bevroren seed verwijderd, verwisseld of vervangen** door een neutrale kandidaat. Extra prompttekst en aandachtstijd mogen geen verborgen voordeel zijn.

Vraagvorming in D die enkel door het voorlezen van een extra optie ontstaat, bewijst geen bijzonder ontstaansmechanisme. **Kandidaat-specifieke, later onafhankelijk valideerbare effecten onder gelijke middelen** zouden hooguit de beperkte werking van het onderzoeksinstrument ondersteunen. Eventuele nieuwe *ruimte van mogelijkheden* en onderliggende modelinterne oorsprong vergen afzonderlijk bewijs.

## Toestemming, acteur en meetregels nog ONBESLIST

De technische en conceptuele reviewers moeten zich expliciet uitspreken over:

- Is een aparte **onderzoekshypothese-blootstelling** volgens product-ADR-001/002 en beperkte onderzoeksautorisatie überhaupt toegestaan? **Zo niet: veto Y.**
- Welke concrete informatie gaat naar de *research inquiry*-rol en **hoe** wordt voorkomen dat dat gewone productprompts, live gebruikersdata of andere experimentele armen bereikt?
- Hoe wordt het bewijs gescheiden in **modelvoorstel**, **detectorbewerking**, **research kandidaat-expositie**, **toegestane tooluitvoering**, **echte waarneming** en **onafhankelijke menselijke duiding**?
- Is het raadplegen van een opgeslagen kandidaat voldoende onderscheidbaar van de **gewone notitiebaseline**, of levert het alleen extra modelcontext op?
- Zijn de twee onafhankelijke mechanismefamilies en beveiligde onverwachte cases op orde? Zijn de no-opportunity-kansen en uitvalregels vooraf bevroren?
- Welke sterke alternatieve verklaring zou **een positieve D–E uitkomst** kunnen weerleggen? Welke negatieve uitkomst is een **valid null** in plaats van een proef waarin kandidaat-interventie onmogelijk was?

**Externe veto-opdrachten:** [technisch #234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234), [conceptueel #235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235). Het [overkoepelende G0-issue #228](https://github.com/E-AI-MODEL/shadowseed-pro/issues/228) blijft open. Het bestaande [prospectieve G0-evaluatiecontract](adapter-evaluation-contract-2026-10-25.md) en het [letterlijke thesisdocument](../../possibility-space-thesis.md) hebben voorrang boven voorstellen in deze kandidaatnotitie.

**Conclusie als onderzoeksvoorwaarde:** productbescherming en gewichtloze geboorte worden bewaard. Voor causale Q2-toetsing is pas na onafhankelijke toestemming een gescheiden, gecontroleerde onderzoeksexpositie verdedigbaar. **Er is geen positieve review of modelproef uitgevoerd, geen G0-goedkeuring en geen impliciete wijziging aan het product.**
