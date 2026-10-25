# Onderzoek stap 1: hoe een model een gap kan signaleren

> **25 oktober 2026. Status: uitgebreid bronnen- en codeonderzoek met een voorgestelde onderzoeksopzet. Geen nieuw modelresultaat, geen preregistratie of G0-goedkeuring. Geen wijziging in productie.**
> Uitgangspunt: [de volledige, tweedelige Shadowseed-these](../possibility-space-thesis.md). De hoofdvraag wordt niet vervangen door een vraag naar betere antwoorden, meer alternatieven, ontbrekende feiten, compressie of RAG.

## 1. De juiste volgorde

De huidige behoefte is niet om een LLM rechtstreeks te vragen twee interessante hypotheses te verzinnen. We moeten onderzoeken hoe zijn getrainde mogelijkheden onder verschillende meetcondities **wel of niet** een concrete, nog niet onderzochte relatie zichtbaar maken. De overgang van een modelobservatie naar een geldige, gewichtloze seed is een tweede stap. De ontwikkeling van die seed over meerdere turns is een derde stap. Een verandering in wat daardoor later onderzoekbaar wordt, is nog een afzonderlijke vierde onderzoeksvraag.

Een **gap** betekent in deze studie een voorstel tot onderzoek naar één concrete open relatie, aanname, voorwaarde, onderscheid, afhankelijkheid of what-if. Een gap hoeft geen ontbrekend feit te zijn. Een opvallende afwezigheid in één gewoon antwoord bewijst niet dat die relatie in het model aanwezig was of wereldwijd nieuw is. De code moet dat onderscheid laten zien, niet verbergen.

De bestaande architectuur blijft leidend. De host genereert een gewoon antwoord. De aparte detector mag kandidaat-gaps formuleren, met ruimte voor NONE. De normale parser, normalisatie, atomiciteitscontrole, deduplicatie en provenance volgen. Een toegelaten seed start met trace boven nul en weight precies nul. Pas in latere echte gespreksturns kunnen recurrence, TTL, TrTL, bronverificatie en falsificatie iets laten zien. De Validation Gate en point-of-use bepalen afzonderlijk of iets invloed mag hebben op een antwoord. Gewichtloze hypothesen mogen als onderzoeksvragen worden bestudeerd, niet stilzwijgend als gezag in antwoorden worden geïnjecteerd.

## 2. Wat werkelijk in de actuele repo zit

[ADR-002](../../architecture/adr/ADR-002-epistemic-seed-contract.md) definieert een seed als atomisch, contextgebonden, in principe onderzoekbaar, niet-bevestigend, gewichtloos bij geboorte en identiteitsbehoudend. [ADR-010](../../architecture/adr/ADR-010-capability-based-model-role-routing.md), met status **proposed**, onderscheidt antwoordgeneratie, gap-detectie en eventuele revisie als modelrollen. De relevante backendconfiguraties zijn in [ShadowChatSession](../../../src/shadowseed/chat.py) aanwezig.

De [detectorcode](../../../src/shadowseed/detection/model_detector.py) bevat een huidige, productmatige **current_pair v0.6**: de actuele vraag, het antwoord en maximaal vier schone voorgaande turns, ieder tot 800 tekens. De output is nul of meer kandidaat-gaps; NONE is toegestaan. Daarnaast bestaat **generative v0.4**: welke inhoudelijke richtingen hadden in het antwoord kunnen staan? Deze oudere prompt heeft een antwoordvorm met een voorgevuld nummer en loopt het risico kandidaten te forceren. Een historische absence-prompt is weer een andere meetconditie. Er bestaat ook een bronobservatiepad zonder actuele chatvraag.

Het inquiry-first detectorvoorstel v0.7 uit [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202) is **zonder merge gesloten** omdat onafhankelijke representatieve beoordeling ontbrak. Het is dus niet de live default. De structurele intake- en levenscyclusreparaties uit [PR #205](https://github.com/E-AI-MODEL/shadowseed-pro/pull/205) zijn wél gemerged zonder v0.6 te wijzigen.

De werkelijke omzetting loopt via de live detector, de [parser](../../../src/shadowseed/detection/model_detector.py), [normalisatie](../../../src/shadowseed/seed_normalization.py), [ingest_detection_candidates](../../../src/shadowseed/intake.py), SeedOrigin en de eigen manager. De [kandidaatobservatielog](../../../src/shadowseed/observations.py) kan ruwe of afgewezen observaties bewaren zonder ze als herhaling of bewijs te boeken. De sessie gebruikt prepare_turn en observe_turn, niet een bij de laatste beurt opnieuw aangemaakte manager.

**De live GPT-5-compressieproef testte dit niet.** Ze liet GPT-5 direct twee alternatieve hypotheses genereren, sloeg de detector over, maakte de manager pas bij de late T2-fase en gaf onbewezen kandidaattekst in een experimentele arm direct mee aan het hostmodel. [De uitslag](live-compression-retention-result-2026-10-25.md) is bruikbaar als technische uitvoerbaarheidstest, niet als bewijs over gap-geboorte, werkelijke meerturnsontwikkeling of de oorspronkelijke these.

## 3. H-Neurons: het methodische voorbeeld, geen bewijs voor Shadowseed

[Gao et al., H-Neurons, arXiv:2512.01797v2 (2025)](https://arxiv.org/html/2512.01797) namen modellen met toegankelijke interne activaties. Ze verzamelden correcte en hallucinerende feitelijke antwoorden, berekenden neuronbijdragen bij relevante tokens, trainden een schaarse classificator en experimenteerden met gerichte activatie-ingrepen. Dat was geen LLM dat zelf neuron-namen uit zijn tekst kon afleiden. Het is een externe meetmethode die mogelijkheden van het model onderzoekt **buiten de zichtbare antwoordtekst**.

[Ji et al., BlackboxNLP/ACL (2024)](https://aclanthology.org/2024.blackboxnlp-1.6/) onderzochten interne toestanden voor het voorspellen van hallucinatierisico bij een vraag. [Farquhar et al., Nature (2024)](https://www.nature.com/articles/s41586-024-07421-0) meten semantische onzekerheid via meerdere gegenereerde antwoorden en semantische groepering. Ze geven verschillende instrumenten. Geen van beide meet het ontstaan van nog niet geformuleerde nieuwe relaties of de verdere onderzoekbaarheid die Shadowseed Q2 bedoelt.

[Cavus et al., arXiv:2609.29781v1, 24 september 2026](https://arxiv.org/html/2609.29781) vonden opnieuw voorspellende H-neuronpatronen en effecten van interventies, maar ook sterke samenhang tussen geselecteerde en andere neuronen, beperkte stabiliteit van schaarse selectie en slechts gedeeltelijke overlap tussen domeinen. Dit is een **preprint**. De belangrijkste les is dat voorspelling, unieke lokalisatie en causaliteit verschillend moeten worden getoetst. Ze stellen vijf concrete diagnoses voor: featurecorrelatie, bootstrapstabiliteit, overlap L1-versus-L2-selectie, controles met willekeurige neuronen in dezelfde laag, en transfer tussen data en modellen.

**De grens voor Shadowseed:** een activatiesignaal dat een externe beoordeling voorspelt is nog geen meting van één specifieke, niet-uitgesproken relatie. Een algemene onzekerheidsindicator kan dezelfde score opleveren. Een kandidaat of reviewlabel in het activatie-inputpad veroorzaakt informatielekkage.

## 4. Wat onze eerdere Laag G-proeven echt maten

[Ronde 032](../../../benchmarks/open_review/rounds/round_032/RESULTS.md) gebruikte Qwen2.5-0.5B, een down-projection-leespunt, 24 expliciet aangeboden stellingen, GPT-4.1 als externe beoordelaar en een centroïde- en sparse-classificator. Ruwe p-waarden 0,014 en 0,018 passeerden de vooraf vastgelegde meervoudig-gecorrigeerde grens van circa 0,00208 niet.

[Ronde 033](../../../benchmarks/open_review/rounds/round_033/RESULTS.md) herhaalde de vooraf geselecteerde toetsen op nieuwe brontekst. **Nul van vier** vaste toetsen passeerde de grens 0,0125. De eerder veelbelovende sparse-classificatie zakte bij een vaste laag terug naar toevalsniveau. Dit is een begrensde negatieve uitkomst voor een **extern houdbaarheidsoordeel over expliciete stellingen in een model van hoogstens 0,5 miljard parameters**. Geen uitspraak over intern gerepresenteerde maar onuitgesproken relaties.

[Issue #203](https://github.com/E-AI-MODEL/shadowseed-pro/issues/203) heeft die verkeerde doelvariabele al benoemd. [PR #204](https://github.com/E-AI-MODEL/shadowseed-pro/pull/204) bevatte een afgezonderde synthetische preflight en optionele generation-time activation hooks, met origineel antwoord **vóór** kandidaat- en labelintroductie. PR #204 is op 23 oktober bewust **zonder merge gesloten**. Een echte 14B-meting is niet uitgevoerd, en ZeroGPU niet gepubliceerd. Die code mag alleen na afzonderlijke review als research-instrument worden hergebruikt. Het is geen nieuwe productdependency en heropenen vergt een aparte keuze.

## 5. Modelcapaciteit en filtering zijn al gedeeltelijk gemeten

[Detectorcalibratie, 24 oktober](../detector-calibration.md): bij Qwen2.5 7B Q4_K_M en 96 turns leverde product v0.6 in de eerste ronde 35 toegelaten kandidaten; v0.7 leverde 478. De afzonderlijk beoordeelde steekproeven hadden **beide 23% bruikbare** kandidaten. In een tweede ronde leverde v0.8 258 kandidaten met **33% bruikbare** in de steekproef. v0.8 is niet aangenomen. Meer kandidaten was dus niet gelijk aan betere detectie. Het hergebruik van suite en beoordelaar begrenst generaliseerbaarheid.

[Seedcalibratie, 23 oktober](../seed-calibration.md): 51 van 60 kandidaten van GPT-5 en GPT-6.1-sol kregen van **een ander taalmodel** het oordeel bruikbaar, niet van onafhankelijke mensen. Bij de vroegere intake waren 22 van 24 afgewezen kandidaten volgens die modelbeoordelaar juist bruikbaar. Die filter is aangepast. Het verschil tussen ruwe detectie, parserverlies, foutieve normalisatie en inhoudelijke waarde moet altijd worden bewaard.

[ADR-012](../../architecture/adr/ADR-012-model-recurrence-recognition.md) gebruikt het gespreksmodel voor de *andere rol* van semantische herkenning bij terugkerende gaps. In de kleine, door een model beoordeelde calibratie herkende zowel embeddingdrempel 0,60 als Qwen 7B 7 van 8 echte herhalingen; de embeddings voegden 10 van 44 inhoudelijk verschillende paren fout samen, Qwen 1 van 44. Die uitkomst ondersteunt nader onderzoek naar semantische identiteit, niet automatische bewijsstatus. Recurrence blijft een observatie.

## 6. Wat stap 1 nu moet scheiden

Een goede studie houdt minimaal vier gebeurtenissen apart:

- **Niet genoemd in gewone generatie:** gemeten onder een vast prompt-, decoding- en tokenbudget, niet globaal onmogelijk.
- **Wel bereikbaar in een andere modeltaak:** detectie, doelbewuste tegenvoorbeelden of meerdere gewone samples laten een relationele kandidaat zien; dit is gedragsmatig toegankelijk, niet automatisch modelintern gelokaliseerd.
- **Geldige kandidaat voor een onderzoek:** een onafhankelijke beoordelaar kan één concrete, contextgebonden en principieel onderzoekbare onzekerheid aanwijzen. Het oordeel kan onbeslist zijn. Het is geen bewijs dat de kandidaat waar is.
- **Kandidaat verandert later onderzoekbaarheid:** alleen te onderzoeken in een latere, onafhankelijke Q2-opzet met toetsbare nieuwe vervolgvragen en kandidaat-specifieke weglating, niet uit het aantal gegenereerde zinnen.

Een klein selectief experiment mag de twee onderdelen van de hoofdthese niet samenvoegen.

## 7. Fase A: onafhankelijke modelgedragsmeting vóór een seed

Bewaar eerst een gewone modelgeneratie bij een vastgelegde vraag en schone context. Vergelijk vervolgens de onderstaande **onderzoekarmen**, niet zes nieuwe productimplementaties:

| Arm | Input of rol | Waarop toets je? |
| --- | --- | --- |
| A0 | Herhaalde gewone generatie, zonder SSL | Relatie-families die spontaan binnen budget B verschijnen |
| A1 | Huidige current_pair v0.6, vraag + antwoord + schone eerdere context | Atomische, niet-geforceerde gaps en eerlijk NONE |
| A2 | Bestaande generative v0.4, exact dezelfde bron | Niet-genomen richtingen, inclusief promptvorm-bias |
| A3 | Hetzelfde krachtige LLM met expliciete bewuste alternatievenzoektocht | Of een gewone sterke modelprompt even goed presteert |
| A4 | Meerdere samples semantisch gegroepeerd, geen seedstore | Of een andere betekenisfamilie bij gewone sampling bereikbaar is |
| A5 | Bronobservatie of vraag zonder het oorspronkelijke antwoord | In hoeverre de eerste formulering de detector verankert |

Voor elke arm pinnen: model en revisie, versie/hash van de detectorprompt, de werkelijk zichtbare historie, sampling, max output, tool- en embeddingtoegang, totale calls/tokens en identificatie van dezelfde casus. Positieve en negatieve cases moeten apart blijven. Forceer geen twee of vijf kandidaten; NONE is een geldige observatie, een parsefout niet. Meet het werkelijke verschil tussen 4 schone eerdere turns, ingekorte context en volledige historie.

**Zonder onafhankelijk geannoteerde voorbeelden** blijft 'bruikbaar' een onderzoekers- of modeloordeel. Bouw daarom een blinde set met echte afwezige maar onderzoekbare relaties, expliciet al genoemde relaties, al opgeloste eerdere punten, foutieve of vergezochte voorstellen, niet-toepasselijke gevallen, semantische bijna-dubbelen, Nederlands/Engels en contextcompressie. Labels worden vastgelegd vóór ontblinding. De cases waarop we prompt en drempels kiezen mogen nooit de definitieve confirmatieset vormen.

## 8. Fase B: waar verandert de modelobservatie in een seed?

Draai de normale productroute detect_seeds → parser → ingest_detection_candidates → manager. Bewaar voor **ieder** voorgesteld item: ruwe modeltekst; parserdiagnose; eventueel NONE; kandidaat-ID, bron en turn; normalisatie vóór/na; atomiciteit; betekenisverandering; wel/niet toegelaten plus reden; exact/semantisch duplicate; en na geboorte trace, weight, evidence_count, status en occurrence_count.

Vergelijk beoordeling **vóór** en **na** intake. Een begrijpelijk maar syntactisch afwijkend punt is niet ineens niet-SSL. Omgekeerd is een korte nette zin geen goede seed per definitie. De filter mag geen inhoudelijke onderzoekswinst fabriceren door achteraf alleen geslaagde kandidaten mee te tellen. Gebruik de bestaande kandidaatobservatielog voor afgewezen, twijfelachtige of aan SSL-output toe te schrijven waarnemingen, zonder ze als onafhankelijke recurrence te laten tellen.

Geen nieuw schema of drempelwijziging voordat is gemeten welke fouten de bestaande keten daadwerkelijk maakt.

## 9. Fase C: een echt gesprek, met groei of juist geen groei

Start bij de eerste turn een echte ShadowChatSession of ShadowseedEngine. Dezelfde toestand leeft gedurende de **gehele** opeenvolging. Iedere beurt gebruikt prepare_turn → hostmodel → observe_turn; abort_turn bij fouten. Observeer zowel nieuwe kansen, herhaling, falsificatie, niet-relevantie, geheugenverval, dormantie, TrTL-reactivatie, betekenisverschuiving en expiratie als het ontbreken daarvan.

Vergelijk identieke modelsnapshots met: gewone notities plus dezelfde embedding-retrieval; sterke bewuste zelfkritiek; beperkte samenvatting; volledige historie als duurdere referentie; echte gewichtloze seedgeboorte + levenscyclus; en exact dezelfde seed weggenomen of vervangen door een voorgevroren neutraal item. Zet vooraf het [feedbackregime RF of RI](g0/adapter-evaluation-contract-2026-10-25.md#two-noninterchangeable-future-feedback-regimes-b8-resolution-proposed) vast. Bij **RF** krijgt iedere arm dezelfde bevroren toekomstige waarnemingen en onderzoeken we latere vraagvorming onder gelijke informatie. Bij **RI** hebben alle armen dezelfde oorspronkelijke wereld, toegestane handelingen, externe veranderingen en maximale middelen, maar ontvangt iedere arm het **werkelijke resultaat van de eigen gekozen interventies**; identieke latere observaties afdwingen zou juist de onderzoeksvraag veranderen. Vergelijk geen RF- en RI-uitkomsten alsof ze één maat zijn. Houd werkelijke kosten, toegankelijke context, niet-gelukte vragen en mens-/toolbijdragen per turn zichtbaar. De methodische basis voor deze splitsing staat in de [Blindspot-audit](step1-eai-blindspot-method-audit-2026-10-25.md).

Een seed die **niet** groeit kan terecht vergeten worden. Een seed die wel telkens terugkomt kan triviaal of onjuist zijn. Een nieuwe, identificeerbare relatie kan op een laat moment ontstaan. Alle drie zijn belangrijke observaties. Het tellen van meer seeds of meer opgeslagen tekst bewijst de these niet.

Gewichtloze kandidaten mogen in een geïsoleerde onderzoekstaak als hypothese worden bevraagd, maar nooit als onbewezen antwoordinstructie worden toegevoegd. Promotie en invloed blijven achter de bestaande Gate en point-of-use. Toets afzonderlijk de toegelaten read-only validatiezoekroute.

## 10. Fase D: eventueel modelintern meten, ná afzonderlijke toestemming en review

Dit is de H-Neurons-achtige route, geen verplicht onderdeel van de normale Shadowseed-pijplijn. Een API-only model geeft geen garantie op interne hidden-state- of neuronhooks; gebruik desgewenst een werkelijk beschikbaar, gepind open-weight model met juiste model- en tokenizerrevisie.

Meet echte activaties **tijdens oorspronkelijke generatie** en vries ze in voordat een kandidaatreferentie of label aan het gesondeerde model wordt getoond. Controleer tokenuitlijning, prefill versus cached forwards, hooknamen, quantisatie en hashes. Gebruik gescheiden beoordelaars voor een onafhankelijke, later ontstane kandidaatset, met expliciet 'onbeslist'. Een vector die algemeen onzeker gedrag voorspelt, heeft nog geen specifieke onuitgesproken relatie bewezen.

Pre-registreer: primaire maat, sampleomvang, uitkomst waarop stoppen toegestaan is, splits op bron én onderwerp, held-out sets, meerdere-laagcorrectie, willekeurige labels, vergelijkbaar maar onjuist materiaal, exacte stimulusidentiteit, featurecorrelaties en bootstraps. Interventies pas na onafhankelijke replicatie, met willekeurige én gecorreleerde-featurecontroles. Een mislukte modeldownload of misplaatste hook is een **instrumentfout**, niet een nuluitkomst over verborgen relaties.

De P0/P1-code in gesloten PR #204 is **onderzoeksprovenance**, geen automatische reden om een oud ontwerp te mergen of een 14B-run te starten. Het 14B-NF4-model heeft andere activaties dan 14B-FP16. Er is geen modelgrootte die zonder meting de oorspronkelijke theorie bevestigt.

## 11. Negatieve controles, uitkomsten en stopregels

| Negatieve/lastige situatie | Fout die we expliciet willen kunnen zien |
| --- | --- |
| Inhoudelijk volledig antwoord | Geforceerde generieke gap ondanks NONE-mogelijkheid |
| Relatie staat al in antwoord of eerder gesprek | Parafrase als nieuwe seed |
| Eerder opgeloste kwestie | Heropening door beperkte 4-turn-historie |
| Niet-gerelateerde latere vraag | Oude seed wordt ongepast geactiveerd of ingevoegd |
| Sterk vergelijkbare woordkeuze, ander vraagstuk | Foutieve recurrencecluster |
| Zelfde gap, andere woorden | Onterechte splitsing |
| Nieuwe, zeldzame maar onderzoekbare mogelijkheid | Verlies door vorm- of lengteheuristiek |
| Onzinnige of ongecontroleerde mogelijkheid | Onterecht status, gewicht of evidentie |
| Contextherhaling na eerder door SSL beïnvloed antwoord | Kunstmatige self-reinforcement |
| Geen contextverlies bij samenvatting | Schijnbare unieke geheugenwinst |
| Andere modeluitkomst maar geen geldig vervolgexperiment | Verschil in tekst wordt 'Q2' genoemd |
| Verleidelijke activatielaag na vele tests | Post-hoc score zonder correctie of replicatie |

Rapporteer **los**: model-outputgedrag, aantal echte kandidaatobservaties, juiste NONE, parseverlies, false merges, menselijke kwaliteitsoordelen, weightless birth, levenscyclus, ongeautoriseerde invloed, foutieve reactivatie, kosten en latere onafhankelijke onderzoeksvragen. Geen enkel totaalcijfer. Een kansarme seed die toch behouden wordt is geen bewijs voor unieke Shadowseed-waarde; een gewone sterke modelbaseline die gelijk scoort is een serieus resultaat.

**NO-GO voor nieuwe betaalde of open-weight confirmatieruns** zolang onafhankelijke construct- en methodreview, vaste kosten, beschermde holdouts en primaire uitkomstmaten ontbreken. **NO-GO voor runtime-/Gate-aanpassingen** alleen om de score te verbeteren. Heropenen van de aparte Laag G-studie vereist een bewuste nieuwe onderzoekbeslissing.

## 12. Uitkomst van deze inventarisatie

We beschikken over bruikbare bouwstenen: modelrollen, v0.6- en generative-detectoren, raw parserdiagnostiek, kandidaatobservatielog, echte intake, modelgebaseerde semantische recurrence, embeddings, TTL/TrTL, Gate en eerdere activatie-instrumenten. Die onderdelen zijn nog **niet** in een onafhankelijk geteste, volledige studie van modelgedrag → gap → seed → meerdere turns → veranderende vervolgonderzoekbaarheid samengebracht.

De eerstvolgende verantwoordelijke stap is een **bron- en rolgecontroleerde proefvoorbereiding op A en B**, met het echte bestaande detectiepad. Laag G kan daarnaast een mechanistisch onderzoeksspoor zijn, maar is geen shortcut en geen voorwaarde om de gewone Shadowseed-pijplijn te onderzoeken.

De oorspronkelijke Q1/Q2-these blijft ongewijzigd en onbewezen.

**Verwijzingen:** [H-Neurons 2025](https://arxiv.org/html/2512.01797), [kritische vervolgstudie 2026](https://arxiv.org/html/2609.29781), [Ji 2024](https://aclanthology.org/2024.blackboxnlp-1.6/), [Farquhar 2024](https://www.nature.com/articles/s41586-024-07421-0), [historische rondes 032/033](../h-neurons-conclusion.md), [geparkeerd Laag G-ontwerp](https://github.com/E-AI-MODEL/shadowseed-pro/pull/204), [detector v0.7 niet gemerged](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202), [bestaande product- en calibratiebronnen](../detector-calibration.md).
