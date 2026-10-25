# Van modelobservatie naar gewichtloze seed, vóór een nieuwe onderzoeksvraag

> 25 oktober 2026 | Uitgevoerd: code-audit en afgebakende, **modelvrije** onderzoeksinstrumentatie. **Niet uitgevoerd:** sterke-modelmeting, semantische beoordeling, activatiemetingen, onafhankelijke G0-review of Q1/Q2-experiment. Geen nieuwe productcode of Gate. De oorspronkelijke [tweedelige these](../possibility-space-thesis.md) is ongewijzigd.

## Waarom hier terug beginnen?

De bestaande Shadowseed-route kan een kandidaat al over meerdere turns bewaren. Dat is niet het onderzoeksresultaat dat we zoeken. De werkelijke vraag is of een niet-gekozen mogelijkheid **uit de probabilistische werking van een LLM** betrouwbaar als onderzoekbare kandidaat kan worden gesignaleerd (Q1), en of die kandidaat **later** bijdraagt aan een andere, betekenisvolle onderzoeksvraag of mogelijke interventie (Q2). Een betere eerste reactie, meer tekens of een algemeen nieuwe formulering zijn daarvoor niet genoeg.

De afgelopen SSOT-wijzigingen in draft [PR #243](https://github.com/E-AI-MODEL/shadowseed-pro/pull/243) en [#244](https://github.com/E-AI-MODEL/shadowseed-pro/pull/244) gaan over onterecht toegekende autoriteit en de audit daarvan. Ze zijn noodzakelijk maar beantwoorden de Q1/Q2-vraag niet. Beide PR's zijn nog niet gemerged; dit onderzoek is daarom op **de ongewijzigde main** gebaseerd en loopt niet op hun branches.

## Bestaand gedrag, exact gescheiden

| Onderdeel | Huidige code en waarneming | Nog niet aangetoond |
| --- | --- | --- |
| Eerste hostgeneratie | `ShadowseedEngine.prepare_turn` levert alleen toegestane modelcontext; de **host** voert het eigen LLM aan en stuurt de zichtbare output naar `observe_turn` | Dat een niet-genereerde relatie al als specifiek intern neuronaal object bestaat |
| Detectie | `ShadowChatSession.observe_turn` geeft vraag, zichtbare eerste antwoordtekst en begrensde schone historie aan de **bestaande detector**. v0.6 `current_pair` mag `NONE` geven; `generative` v0.4 vraagt naar andere mogelijke richtingen | Dat een detectoruitvoer inhoudelijk origineel, toetsbaar of nuttig is; alle modellen/promptvarianten presteren niet gelijk |
| Intake | De echte `ingest_detection_candidates` normaliseert, probeert één atomische kandidaat vast te houden, dedupliceert en kan afwijzen; de `CandidateObservationLedger` bewaart waarnemingen | Dat normalisatie geen betekenisverlies of foutieve samenvoeging veroorzaakt in echte modeluitvoer |
| Geboorte | `ShadowSeed` begint met `weight=0`, `evidence_count=0`, een identiteit en een `created`-event. Een later geaccepteerde herdetectie van dezelfde seed telt **niet** als nieuwe geboorte | Dat de kandidaat een daadwerkelijke niet-gekozen modelmogelijkheid representeert |
| Meereizen | Dezelfde `ShadowChatSession` bewaart de manager over meerdere `prepare_turn`/`observe_turn`-cycli. Trace kan vervallen, recurrence vereist herdetectie, en TrTL reageert op **dormant** seeds | Dat een actieve gewichtloze seed op iedere turn opnieuw inhoudelijk wordt onderzocht; dat louter bewaren semantische groei is |
| Gewone antwoorden | `prepare_turn` en `AgentSafetyContract` kunnen enkel geautoriseerde seeds laten meetellen in het gewone antwoord. De huidige `_run_retrieval_probe` gebruikt promoted/authorized seeds | Een autonome, gewichtloze, modelgestuurde onderzoeksactie die uit de seed een **eigen** vervolgonderzoek afleidt |
| Autoriteit | `Validation Gate` en point-of-use blijven afzonderlijke grenzen. Geen onderzoek mag daar een shortcut omheen leggen | Dat validatie van steunbewijs gelijkstaat aan Q1/Q2 |

Dit is ook waarom we niet nog eens een shadowgeheugen, tweede Gate of algemene 'inquiry role' moeten programmeren voordat er een beslissende proef is.

## Wat deze branch werkelijk bouwt

De kleine module `research/src/shadowseed_research/benchmark/weightless_birth_handoff.py` neemt **een al voltooide, echte `ShadowseedEngine`-turn** en bevriest uitsluitend de **eerste geboorte** van één kandidaat. Het is geen detector, generator, prompt, classifier, bronbeoordelaar of nieuwe memory.

`freeze_canonical_weightless_birth(engine, observed_turn, seed_id)` weigert een snapshot wanneer:

- een turn nog openstaat, de meegegeven turn niet de laatst opgeslagen turn is of de tijdsvolgorde verschilt;
- de seed niet in `seeds_born_weightless` voorkomt of `born_turn` een eerdere beurt aanwijst, ook al staat de ID opnieuw in die productrapportage;
- het seedrecord, `created`-event, intakeacceptatie, contextreferentie of oorsprong niet overeenkomt;
- er al gewicht, evidence, een Gate-event, promotie of zelf-afgeleide antwoordcontext aanwezig is;
- de detectorobservaties ontbreken of volgens het productrecord door SSL-context beïnvloed zijn.

Het resultaat bevat seed-ID, turn, hashes van kandidaat, antwoord, broncontext, intake, `created`-event en detectorobservaties. Standaard wordt de kandidaattekst niet meegegeven; een lokale onderzoeker kan die expliciet opvragen. De SHA-256's bewijzen alleen dat twee **aangeleverde records** overeenkomen, niet dat het hostantwoord werkelijk door een LLM kwam, dat de bron waar is of dat de kandidaat semantisch uniek is. Alle onderzoeksclaims blijven `False`, met onder meer `subsequent_inquiry_generated=False` en `q1_or_q2_effect_established=False`.

De regressie `research/tests/test_weightless_birth_handoff.py` gebruikt **dezelfde canonieke Engine**, niet een gekopieerde manager. Het hostantwoord en de detector zijn bewust onderzoeker-gescript. Ze controleert: eerste geboorte, zero-authority, schone provenance, falsificatie met gewijzigde events, geen promotie of invloed, expliciete NONE-controle en echte opeenvolgende turns waarin **dezelfde seed** meereist zonder nieuwe onderzoeksvraag.

**Dit is een grenscontrole, geen werkzaamheidsproef.** Het bestaande offline meetinstrument in [step1-gap-birth-instrument](step1-gap-birth-instrument-2026-10-25.md) meet parser/intake en varianten gedetailleerder; deze nieuwe functie voegt daar alleen het compacte, versiegebonden **eerste-geboorte-handoff** aan toe voor een later onderzoeksontwerp. Niet nogmaals de hele bestaande audit herschrijven.

## Precies de ontbrekende schakel

Tussen **gewichtloze kandidaat bewaren** en **een door het model bedachte, later toetsbare andere vraag** ontbreekt uitvoerbaar wetenschappelijk bewijs én een goedgekeurd onderzoekscontract. De volgende proef moet modelgeneratie, detectie, de originele seed en latere inquiry **chronologisch** scheiden. De onderzoeker mag niet de uiteindelijke goede vervolgvragen in de prompt verstoppen.

Minimale volgorde, nog **niet** als nieuwe productruntime geïmplementeerd:

- **T0:** een capabel, exact gepind hostmodel produceert een gewoon antwoord. Herhaalde gewone generaties leveren een budgetgebonden referentie van zichtbaar gekozen mogelijkheden. Eén niet-genoemde richting is niet per definitie intern afwezig.
- **T1:** de bestaande, gescheiden detector stelt één of meer mogelijke open relaties voor; de bestaande parser en intake beslissen; het eerste echte `created`-event levert een vaste **gewichtloze seed** op, of er komt terecht niets.
- **T2:** dezelfde live Engine volgt een nieuwe, onafhankelijke gespreksturn, terwijl alle kandidaten gewichtloos blijven en buiten de gewone antwoordprompt. De onderzoeker en de evaluator houden toekomstige feedback en antwoorden afgeschermd van de kandidaatselectie.
- **T3:** alleen in een **afgescheiden research-arm** mag hetzelfde capabele model in een vooraf beschreven, beperkte inquiry-taak een **zelf geformuleerde, toetsbare vraag** voorstellen. De seed mag in die experimentele onderzoekscontext bekeken worden, maar niet als feit of autoriteit in de gewone gebruikersreactie. Registreer welke tekst van welk model of onderzoeker kwam.
- **T4:** een onafhankelijk, versiegepind uitvoerings-/beoordelingsmechanisme toetst de voorgestelde vraag en het latere effect. Vergelijk met het gewone model, expliciet divergent zoeken, gewone notities en een exacte kandidaat-ablatie. Geen succesclaim als dezelfde vraag met hetzelfde budget al zonder Shadowseed ontstaat.

De bestaande [adaptervergelijking](g0/adapter-evaluation-contract-2026-10-25.md) onderscheidt **RF** (alle armen krijgen dezelfde latere externe informatie, alleen latere vraagformulering) van **RI** (iedere arm kiest zelf een toegestane interventie en ziet de eigen gevolgen). Die twee zijn niet uitwisselbaar. De onderzoeksopzet moet dat **vóór** de eerste modelaanroep vastleggen.

## Hoe dit falsifieerbaar wordt

Een latere proef moet tegenvoorbeelden opnemen waarin er géén betekenisvolle kandidaat bestaat, een kandidaat niet te testen is, een onderzoeksrichting onjuist blijkt, of gewone modelnotities hetzelfde bereiken. Minder omwegen, verrassende taal of een extra relationeel label tellen niet automatisch als verandering in wat later onderzoekbaar is.

Het onderzoek moet minimaal onderscheiden: **(a)** detectorvoorstel, **(b)** werkelijke eerste seedgeboorte, **(c)** over meerdere turns behouden of verdwenen kandidaat, **(d)** model-originated vervolgonderzoek, **(e)** externe toetsbaarheid, en **(f)** kandidaat-specifiek oorzakelijk voordeel boven de sterkste kosten-gelijke controle. Verschillende negatieve antwoorden zijn toegestaan.

Voor een claim over *interne* modelrepresentaties zou aanvullend een apart open-weight/activation-onderzoek nodig zijn. De eerder bestudeerde [H-Neurons-methodiek](step1-h-neurons-method-crosswalk-2026-10-25.md) ondersteunt de methode van activaties meten, niet de claim dat zulke neuronen niet-gekozen relaties aantonen.

## Huidige stopbeslissing

De [onafhankelijke G0-v3-review](g0/dynamic-inquiry-independent-review.md) is nog leeg. De benodigde algemene executor voor onvoorziene modelvragen en de toekomstig te beschermen casussen zijn nog niet onafhankelijk goedgekeurd. **G0 NOT PASSED.** Geen betaalde modellen, geen verse AI-gegenereerde 'waarheidslabels' en geen activatieclaims.

Er worden geen productinstellingen, Gate-signalen, modelproviders, TTL/TrTL, promptvarianten of opgeslagen seedscoreregels aangepast. Eerst moet deze read-only handoff mechanisch groen zijn. Pas daarna is de volgende keuze aan de orde: een extern beoordeelde, vooraf vastgelegde **inquiry**-proef op één concrete ontbrekende schakel. Dat is een nieuwe onderzoeksactiviteit, geen vervanging van de oorspronkelijke tweedelige these.
