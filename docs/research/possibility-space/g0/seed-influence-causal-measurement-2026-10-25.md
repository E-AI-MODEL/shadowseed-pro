# De invloed van een gewichtloze seed: meetmodel, falsificatie en grens van de huidige proef

> 25 oktober 2026. **Prospectieve meetinstructie voor volgende experimenten, met retrospectieve audit van 25 oktober.** Geen automatisch scoringssysteem, geen post-hoc succesclaim, geen Gate-aanpassing. G0 = NOT PASSED. Dit document is bedoeld voor de onafhankelijke R1/R2-review onder issues #234 en #235.

## Wat is eigenlijk de behandeling?

Eerst onderscheiden wat in een gescheiden onderzoeksruimte mag gebeuren:

- De *werkelijke behandeling* in arm D is **toegang tot de tekst van precies één daadwerkelijk eerder geboren, bevroren, gewichtloze seed op een apart onderzoeksmoment**. De seed blijft van hetzelfde ID, heeft correcte intake/herkomst en blijft weight/evidence/authority 0. Dit is geen bewijs voor een model-interne niet-gekozen activatie.
- Arm E haalt **precies die bevroren seed** uit de onderzoeksprompt of vervangt haar door een inhouds-/lengte-vergelijkbare andere kandidaat; verschil tussen verwijderen en vervangen is expliciet een afzonderlijke contrastvraag. Andere kandidaattekst uit dezelfde detectoruitvoer is een bruikbare exploratieve sham maar **niet automatisch inhoudelijk gelijkwaardig**.
- Armen A, B en C zijn echte rivalen: gewone modelgeneratie, doelgericht zoeken en normale notities/volledige historie. Alle armen moeten op iedere beurt dezelfde exogene informatie krijgen; bij RI zijn hun eigen onafhankelijke *actie-uitkomsten* juist verschillend toegestaan, mits starttoestand, regels, werktuigen en limieten gelijk zijn.
- De gewone product-host krijgt *nooit* gewichtloze seeds zonder de bestaande autorisatie. **Nul gewone antwoordinvloed is hier de ontworpen veiligheidseigenschap, niet een mislukte Q2-uitkomst.**

Een positief D-vs-A-verschil alleen is geen specifiek Shadowseed-effect. D kan extra informatie, extra promptlengte, één extra modelaanroep of sturing door de onderzoeker bevatten. Het sterkste contrast is een **gepaarde D-vs-exact-kandidaat-ablatie E** met gelijkwaardige informatie, kosten en instrumenttoegang. Ook dat schat alleen het effect van de extra kandidaatcontext *in die configuratie*.

## Vijf gescheiden meetlagen

| Laag | Meetbare waarneming | Stand 25 oktober 2026 | Niet bewezen door deze laag |
| --- | --- | --- | --- |
| **P. Herkomst** | Ruwe detectoruitvoer, item-to-intake, eerste created-event, kandidaat-ID, timestamp, geboorteturn, hash | Via [PR #247](https://github.com/E-AI-MODEL/shadowseed-pro/pull/247) + [PR #249](https://github.com/E-AI-MODEL/shadowseed-pro/pull/249) op `main` rechtstreeks controleerbaar | Dat de kandidaat intern latent was of inhoudelijk zinvol is |
| **L. Levensloop** | Elke echte Engine-turn, weight=0, recurrence, DORMANT/TrTL/TTL, geblokkeerde Gate, gebruik in gewone prompt | Mechanisch in checkpoints; de eerste live RF-T1 is vastgelegd, T2-ValueError nog niet gediagnosticeerd | Dat de seed inhoudelijk groeide |
| **X. Blootstelling** | Exacte kandidaattekst + positie + tokens in afgeschermde onderzoeksarm D, geen seed in gewone host, afwezigheid in A/B en ablaties | Via opgeslagen promptvariant/audit en kandidaat-ID controleerbaar; nog geen onafhankelijke inspectie van elke gegenereerde prompt | Dat het model de seed werkelijk gebruikte |
| **B. Gedragsrespons** | Wijziging in probleemformulering, alternatieve verklaring, onderzoeksvoorstel, onderscheidende meting, onzekerheid en toetsvoorwaarden | T1 levert vijf tekstoutputrecords en één mogelijke semantische echo | Causale *kandidaat*-bijdrage of externe geldigheid |
| **C. Causale bijdrage en RI** | Gepaard D vs exacte kandidaatablatie, vooraf gekozen uitkomstcriteria, randomisatie, replicaties, onafhankelijke toets en werkelijk externe later gevolg | **Niet gemeten** | Wetenschappelijk unieke mogelijkheidsexpansie |
| **I. Interne modelrepresentatie** | Modelinterne activaties, gerichte interventies/ablaties in open-weights modellen met voldoende capaciteit | **Niet gemeten** | Dat een GPT-5 API-output een onderdrukte neurale mogelijkheid representeert |

P en L zijn robuuste **software-observaties**, X is een manipuleerbare onderzoeksconditie; B is gedragsbeschrijving; C vergt een studie met herhalingen; I heeft een andere onderzoeksinfrastructuur nodig.

## Retrospectieve audit: wat vertelt één echte T1-vergelijking?

Bron: [GitHub Action #40224494313](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224494313) en het niet-voltooide `observed.json`, in artifact `g0-real-seed-rf-inquiry-40224494313`. De eerste echte seed `ss_001` luidt (verkort): *mogelijk meten de sensoren ruimtelijk niet hetzelfde deel van het materiaal*. Hij kwam uit een echte `current_pair`-detectie en bleef weight=0.

Bij de nieuwe T1-waarneming stelden **alle vijf** condities een vraag over de temporele relatie tussen pieken en schakelmomenten van de regelkast. D verschilde niet duidelijk in **vraagrichting**. Alleen in D's zichtbare onzekerheidstekst stond: *lokale procestransiënten op een ander meetvolume zijn niet volledig uitgesloten*. Deze interpretatie is uit de ruwe tekst afgeleid, **niet door een onafhankelijke rater vastgesteld**.

Zorgvuldig onderscheid:
- **Zichtbare mogelijke echo:** de ruimtelijke hypothese verschijnt in een onzekerheidsvoorbehoud van D.
- **Geen geïsoleerde causale invloed:** D/E/A/B/C werden elk één keer bemonsterd; uiteenlopende sampling en andere instructies zijn alternatieve verklaringen. E gebruikte een andere echte detectoruitvoer, geen exact gematchte of seed-verwijderde prompt. Eén echo kan toeval, algemene domeinkennis of gewone promptcontext zijn.
- **Geen nieuw geopend onderzoek:** alle T1-vragen gingen over dezelfde temporele relatie; geen aparte vraaguitvoering, bewijsupdate of nieuwe tweede-orde vraag. Het exogene T2-resultaat was door de onderzoeker vooraf geschreven.
- **T2 incompleet:** na 14 voltooide GPT-5-aanroepen faalde `freeze_weightless_followup` met een niet nader geregistreerde `ValueError`. Geen geldige T2-onderzoeksarm of Q2-resultaat. [PR #251](https://github.com/E-AI-MODEL/shadowseed-pro/pull/251) heeft daarna de fail-closed diagnostiek uitgebreid, zonder de eerdere fout als opgelost te presenteren.
- **De numerieke noemer:** vijf T1-outputrecords, maar **één casus / één seed / één T1-context**. Geen n=5 onafhankelijke effectwaarnemingen, geen betrouwbaarheidsinterval of p-waarde mogelijk.

## Prospectieve meetmaten, NIET automatisch als waar aangemerkt

Meet per *gematchte casus/seedtraject* en bevroren T1- of T2-turn, naast elkaar:

1. **Hypothesebehoud:** behandelt de tekst de specifieke T0-seed als een onbewezen alternatieve mogelijkheid, ook wanneer de hoofdvraag in een andere richting gaat? Noteer `ja/nee/onbeslist`, letterlijke onderbouwde passages en referentieturn. Dit is een gedragsmaat, geen causaliteit.
2. **Vraagonderscheid:** is de latere modelvraag inhoudelijk anders dan de eerdere eigen vragen en de andere onderzoeksarmen? Blind beoordeeld als wezenlijk anders, herformulering of onbeslist. Geen stringoverlap- of embeddingdrempel als waarheid.
3. **Toetsbaarheid:** noemt het model een onafhankelijke waarneming/handeling die de vraag zou kunnen onderscheiden? Beoordeel via algemene instrumentregels en menselijke review; een niet-ondersteunde maar zinvolle vraag is `niet toetsbaar hier`, niet `onwaar`.
4. **Voorwaardelijke afhankelijkheid:** verandert het afgeschermde D-vs-E-contrast de kans op een inhoudelijk andere vraag of een relevante onzekerheid? Dit vergt vooraf ingevroren prompts, herhaalde gepaarde gevallen, gerandomiseerde model-callvolgorde en middelenbalans.
5. **Nieuwe werkelijke onderzoeksstap:** kan een externe evaluator onder RI een door het model gekozen ingreep uitvoeren, nieuwe waarneembare informatie teruggeven en een tweede nieuwe, conditioneel afhankelijke vraag beoordelen? Alleen onafhankelijke uitkomsten, geen door de onderzoeker gescripte toekomstdata.
6. **Negatieve uitkomsten:** `NONE`, ongeldig JSON, model `incomplete`, onbeslist, unsupported, no-opportunity, budgetoverschrijding, recurrence zonder groei, en Gate-blokkades blijven in de oorspronkelijke aantallen.

## Causaal contrast: precieze schatting

Definieer voor casus `i`, onder vooraf bepaalde semantische uitkomst `Y`:

`Delta_i = Y_i(D, met exact T0-seed) - Y_i(E, exact T0-seed verwijderd)`.

De gemiddelde `Delta` over **onafhankelijke seedtrajecten** met herhaalde, gerandomiseerde runvolgorde is een schatting van **het effect van onderzoeksblootstelling aan die specifieke tekst**, niet van de verklaring dat de modelinterne zoekruimte is veranderd. Rapporteer onzekerheid per *casus*, niet alsof losse LLM-tokens of calls onafhankelijke onderzoeken zijn. Gebruik waar mogelijk gekoppelde bootstrap/permutatie over casussen en rapporteer ruwe uitkomsten, modelidentiteit, decodeerinstellingen, gebruikte tokens, afgebroken runs en beoordelaarsonenigheid.

De D-vs-E-varianten moeten apart worden geanalyseerd:
- **E0:** exacte seed weglaten, met structureel gelijke niet-inhoudelijke promptomgeving. Dit test het tekstspecifieke additieve effect, maar informatie-/tokenbalans is lastig.
- **E1:** seed vervangen door vooraf vastgelegde, lengte- en relevantie-gematchte controle. Dit test specificiteit bovenop het effect van een extra notitie; de match moet onafhankelijk en vóór outputinzage worden goedgekeurd.
- **C:** gewoon modelgeheugen met gelijkwaardige broninformatie en token-/callbudget. Wanneer C hetzelfde bereikt, is een unieke Shadowseed-uitleg niet aangetoond.

**Methodisch veto:** een claim over veranderd 'denkbaar' of 'nieuw idee' volgt niet uit hypothesebehoud, meer tekst, een betere taakscore, of zelfs een positief gekoppeld D-effect. Voor Q2 moet een nieuw en onafhankelijk toetsbaar later onderzoek daadwerkelijk mogelijk blijken. Voor Q1 vergt de claim over interne niet-gekozen mogelijkheden aparte directe interne probes; gewone API-output geeft hoogstens gedragsmatige dekking onder een bevroren samplingbudget.

## Wat wetenschappelijk al waarde kan hebben

De **versievaste, auditeerbare scheiding** van kandidaat-geboorte, gewichtloos behoud, latere blootstelling en onafhankelijke toetsing kan een reproduceerbare **meetmethode** zijn, ook wanneer D geen voordeel heeft. Het is geen aangetoonde ontdekking van een nieuw LLM-mechanisme; externe onderzoekers moeten kunnen reproduceren en falsifiëren. Dit is een verdedigbare *methodische* bijdrage, niet reeds een gevalideerde effecttheorie.

Voor een eerste openbaar methodisch artikel zouden vooral waardevol zijn: reproduceerbare code, volledig negatieve én positieve runs, formele stoppers, bron/claim-mapping, controle van inputpariteit, onafhankelijke codering van vragen en het verschil tussen gewone notitie versus echt gewichtloos geheugen. Een artikel dat meteen beweert dat Shadowseed nieuwe wetenschappelijke mogelijkheden schept, gaat verder dan deze resultaten.
