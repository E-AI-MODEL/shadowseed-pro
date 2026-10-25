# Van modelobservatie naar gewichtloze seed, vóór een nieuwe onderzoeksvraag

> 25 oktober 2026 | Research-only vervolg **na merge van PR #246**. Uitgevoerd: code-audit en modelvrije controles van exacte detectorwaarneming → genormaliseerd intake-item → eerste gewichtloze seed. **Niet uitgevoerd:** sterke-modelmeting, onafhankelijke semantische beoordeling, activatiemetingen, G0-review of Q1/Q2-experiment. Geen wijzigingen aan Gate, seedgewicht of de gewone modelprompt. De oorspronkelijke [tweedelige these](../possibility-space-thesis.md) blijft ongewijzigd.

## Waarom hier terug beginnen?

De bestaande Shadowseed-route kan een kandidaat al over meerdere turns bewaren. Dat is niet het onderzoeksresultaat dat we zoeken. De werkelijke vraag is of een niet-gekozen mogelijkheid **uit de probabilistische werking van een LLM** betrouwbaar als onderzoekbare kandidaat kan worden gesignaleerd (Q1), en of die kandidaat **later** bijdraagt aan een andere, betekenisvolle onderzoeksvraag of mogelijke interventie (Q2). Een betere eerste reactie, meer tekens of een algemeen nieuwe formulering zijn daarvoor niet genoeg.

De afgelopen SSOT-wijzigingen in draft [PR #243](https://github.com/E-AI-MODEL/shadowseed-pro/pull/243) en [#244](https://github.com/E-AI-MODEL/shadowseed-pro/pull/244) gaan over onterecht toegekende autoriteit en de audit daarvan. Ze zijn noodzakelijk maar beantwoorden de Q1/Q2-vraag niet. Beide SSOT-PR's blijven ongemerged. De detector/intake-herkomstregistratie uit [PR #246](https://github.com/E-AI-MODEL/shadowseed-pro/pull/246) is **wel** gemerged en vormt de huidige productbasis van dit onderzoek. We gebruiken geen parallelle detector- of intakeimplementatie.

## Bestaand gedrag, exact gescheiden

| Onderdeel | Huidige code en waarneming | Nog niet aangetoond |
| --- | --- | --- |
| Eerste hostgeneratie | `ShadowseedEngine.prepare_turn` levert alleen toegestane modelcontext; de **host** voert het eigen LLM aan en stuurt de zichtbare output naar `observe_turn` | Dat een niet-genereerde relatie al als specifiek intern neuronaal object bestaat |
| Detectie | `ShadowChatSession.observe_turn` geeft vraag, zichtbare eerste antwoordtekst en begrensde schone historie aan de **bestaande detector**. v0.6 `current_pair` mag `NONE` geven; `generative` v0.4 vraagt naar andere mogelijke richtingen | Dat een detectoruitvoer inhoudelijk origineel, toetsbaar of nuttig is; alle modellen/promptvarianten presteren niet gelijk |
| Intake | De canonieke intake registreert sinds PR #246 per item de ruwe detectorindex, genormaliseerde index, acceptatie/afwijzing, seed-ID en werkelijke `created`/`deduplicated`-transitie. De bestaande observation ledger levert de exacte raw-item-ID. | Of die teksttransformatie inhoudelijk trouw is en een model een zinvolle niet-gekozen mogelijkheid detecteert |
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
- het verslag geen canonieke `candidate-intake-lineage-v1` bevat, de kandidaat slechts via een overschreven normalizer is afgeleid, of het specifieke geaccepteerde item niet exact en **uniek** gekoppeld is aan een ruwe detectorindex, de juiste genormaliseerde positie, het bestaande observationrecord en een echte `created`-transitie;
- er al gewicht, evidence, een Gate-event, promotie of zelf-afgeleide antwoordcontext aanwezig is;
- de detectorobservaties ontbreken of volgens het productrecord door SSL-context beïnvloed zijn.

Het resultaat bevat seed-ID, turn, hashes van kandidaat, antwoord, broncontext, intake, `created`-event en detectorobservaties. Standaard wordt de kandidaattekst niet meegegeven; een lokale onderzoeker kan die expliciet opvragen. De SHA-256's bewijzen alleen dat twee **aangeleverde records** overeenkomen, niet dat het hostantwoord werkelijk door een LLM kwam, dat de bron waar is of dat de kandidaat semantisch uniek is. Alle onderzoeksclaims blijven `False`, met onder meer `subsequent_inquiry_generated=False` en `q1_or_q2_effect_established=False`.

**Mechanische afstamming is nu per item controleerbaar.** Voor **nieuwe** turns met de canonieke normalizer neemt het product uit PR #246 het concrete raw-itemnummer, de genormaliseerde positie en de echte intakebeslissing op. De onderzoeksfunctie accepteert uitsluitend een `accepted`-item met `seed_transition=created`, `source_mapping_status=canonical` en `observation_link_status=recorded_exact_raw_item`. Het observation-ID moet opnieuw overeenkomen met context, index en ruwe tekst. De daadwerkelijke waarneming, genormaliseerde tekst en seed-ID worden ook met het originele `created`-event en de intakeacceptatie vergeleken. Bij ontbrekende velden, meerdere mogelijke matches of gewijzigde gegevens volgt **geen** bevestigde mapping. Het resultaat krijgt alleen voor zo'n gecontroleerde nieuwe geboorte `raw_detector_item_to_seed_mapping_verified=True` en `raw_to_seed_link_scope=recorded_canonical_item_to_first_birth`. De snapshot bevat de bronindex en hashes, niet standaard de ruwe kandidaattekst.

Dezelfde ruwe detectorregel kan bij algemene intake in meerdere genormaliseerde fragmenten uiteenvallen. Dit wordt per fragment geadministreerd. De gewone live-detectorroute gebruikt bewust `split_broad=False`; we veranderen dat niet om een onderzoekssucces af te dwingen. Bij oudere rapporten zonder nieuwe lineage, afwijkende normalizers of ambiguïteit weigert de onderzoekshandoff een exacte claim. **Een administratief exact spoor bewijst niets over de interne modelactivaties, semantische nieuwheid, juistheid of later voordeel.** De detector en het model blijven afzonderlijke verantwoordelijke bronnen van tekst.

De regressie `research/tests/test_weightless_birth_handoff.py` gebruikt **dezelfde canonieke Engine**, niet een gekopieerde manager. Het hostantwoord en de detector zijn bewust onderzoeker-gescript. Ze controleert: eerste geboorte, zero-authority, exacte observation-ID bij dubbele ruwe tekst, afzonderlijke seeds, ontbrekende oude lineage, foutieve bronindex/normalisatiepositie, gemanipuleerde observation-ID, afwijzingen, geen promotie of invloed, expliciete NONE-controle en echte opeenvolgende turns waarin **dezelfde seed** meereist zonder nieuwe onderzoeksvraag.

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

Er worden in deze onderzoeks-PR geen productinstellingen, Gate-signalen, modelproviders, TTL/TrTL, promptvarianten of opgeslagen seedscoreregels aangepast. Het mechanische birth-handoff moet op de huidige hoofdbranch aantoonbaar groen zijn. Pas daarna is de volgende keuze aan de orde: een extern beoordeelde, vooraf vastgelegde **inquiry**-proef op één concrete ontbrekende schakel. Dat is een nieuwe onderzoeksactiviteit, geen vervanging van de oorspronkelijke tweedelige these.

## Regressie op meerdere geboorten in één turn

De strikte onderzoekscontrole vond een echte productinconsistentie: bij meer dan één nieuwe seed kon het tweede `created`-event nog naar de voorlopige `first_pass_answer`-context verwijzen, hoewel de seed inmiddels `visible_answer` als origine had. De fout zit niet in de detector of in de nieuwe lineage-mapping, maar in de volgorde van mutatie en event-reclassificatie binnen de live chatroute. De uitgevoerde negatieve proef is bewaard in [research-run #40208620030](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40208620030).

[Draft PR #248](https://github.com/E-AI-MODEL/shadowseed-pro/pull/248) corrigeert **iedere afzonderlijke `created`-event** zonder de bestaande gedeelde `SeedOrigin`-objectidentiteit te veranderen. Een eerdere poging om de herkomst per seed te kopiëren is op basis van de producttests bewust teruggedraaid. Deze onderzoeks-PR is tijdelijk gestapeld op de reparatiebranch, uitsluitend om de echte twee-seed-regressie vóór integratie opnieuw te testen. Na de productmerge moet de basis weer `main` zijn. Deze tests blijven modelvrij, er is geen Q1/Q2-effectbewijs.
