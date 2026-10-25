# Shadowseed Pro — methodische Blindspot-audit van Q1, Q2 en stap 1

> **25 oktober 2026 | Interne, brongebonden zelfaudit; geen onafhankelijke methodereview.**
> **Onderzoeksbasis:** main op commit [500e658](https://github.com/E-AI-MODEL/shadowseed-pro/commit/500e658ace43476d6839dec802dc0a2ad0f881c9).
> **Resultaat:** het bestaande onderzoeksontwerp bewaart de tweedelige hoofdvraag en herkent veel bekende valkuilen, maar een aantal beslissende meetafspraken ontbreekt of is nog niet eenduidig.
> **Besluit:** G0 blijft **NOT PASSED**. Geen modelproef, automatische API-run, nieuwe detector, gewijzigde Gate, andere gewichtstoekenning of nieuw ADR op basis van deze audit.

## De vraag verandert niet

> Kunnen we de waarschijnlijkheidsgerichte werking van een taalmodel gebruiken om niet alleen te onderzoeken wat het model weet, niet weet of niet genereert, maar ook welke relaties en mogelijkheden er zouden kunnen zijn buiten de gebruikelijke generatie? En kunnen we onderzoeken hoe nieuwe mogelijkheden ontstaan die de ruimte van wat daarna denkbaar is zelf veranderen?

Deze formulering is letterlijk overgenomen uit de [oorspronkelijke, gezaghebbende onderzoeksvraag](../possibility-space-thesis.md). Q1 gaat over wat onder een bepaalde generatieconditie niet wordt geselecteerd maar onder een andere conditie mogelijk onderzoekbaar blijkt. Q2 gaat over een eventuele verandering van wat **later** denkbaar of onderzoekbaar wordt. Een geheugenvoordeel, een extra antwoord of een nieuwe formulering is op zichzelf geen bewijs voor Q2.

### Wat EAI Blindspot hier wel en niet bijdraagt

De **methodische discipline** uit EAI Blindspot Core 0.5.4 is hier bruikbaar: (a) observeerbaar gedrag vóór interpretatie; (b) expliciete herkomst van handelingen en beoordeling; (c) bewijs passend bij precies de geclaimde uitkomst; (d) ontbrekend bewijs is niet automatisch een negatief resultaat; (e) tegenbewijs en niet-geslaagde gevallen behouden; (f) een controleerbaar proces is geen automatisch valide conclusie.

**Dit is geen EAI-classificatie van Shadowseed.** De onderwijsspecifieke dimensies, scores, drempels, rubric-voorbeelden en leerclaims van Blindspot worden niet naar de Shadowseed-detector vertaald. EAI Blindspot is zelf niet empirisch gevalideerd als meetinstrument voor deze onderzoeksvraag. Deze auteursscan is evenmin de vereiste onafhankelijke G0-beoordeling. Er is geen blind onderzoeksresultaat of externe wetenschappelijke consensus geproduceerd.

## Wat in de repository daadwerkelijk is aangetroffen

| Bron | Gecontroleerde observatie | Wat de bron niet aantoont |
| --- | --- | --- |
| [Onderzoek stap 1](step1-model-signals-gap-origin-2026-10-25.md) | Scheidt gewone modelgeneratie, detectie, parser/intake, echte gewichtloze geboorte, vervolgturns en eventueel intern activatieonderzoek. | Dat één complete model-naar-gap-naar-seed-naar-later-onderzoekbaarheid-proef al bestaat. |
| [Huidige detector](../../../src/shadowseed/detection/model_detector.py) | Current-pair v0.6 vraagt expliciet om gaps bij vraag, conceptantwoord en maximaal vier begrensde eerdere turns; generative v0.4 vraagt expliciet om alternatieve richtingen. Er zijn vorm- en maximumregels. | Dat de voorgestelde relatie spontaan ontstond of vóór die instructie intern als specifieke onuitgesproken relatie aanwezig was. |
| [Chat en intake](../../../src/shadowseed/chat.py) en [intake](../../../src/shadowseed/intake.py) | De echte chatroute gebruikt prepare_turn/observe_turn en bij detectorinvoer expliciet expand_short_fragments=False en split_broad=False; een ruwe kandidaat kan worden afgewezen of gededupliceerd. | Dat de automatische vormcontrole semantische nieuwheid, bruikbaarheid of niet-voorgeschreven relaties valideert. |
| [Offline stap-1 meetinstrument](step1-gap-birth-instrument-2026-10-25.md) | Twee vaste sessies, elk vier gescripte turns, volgen de werkelijke detectorparser en intake; NONE, leeg, misvormd, herdetectie en echte geboorte worden gescheiden. | Detectorprestatie met echte modellen, modelinterne signalen, relevantie of inhoudelijke groei. Er waren nul modelaanroepen. |
| [Live GPT-5-compressieproef](live-compression-retention-result-2026-10-25.md) | 30 GPT-5-aanroepen; het gewone antwoord en de samenvatting behielden de relevante verklaring al. De armen onderscheidden zich inhoudelijk niet overtuigend. | Een apart Shadowseed-effect, werkelijke initiële gapdetectie of Q2. |
| [G0 v3-voorstel](g0/dynamic-inquiry-protocol-candidate-2026-10-25.md) en [ongevulde review](g0/dynamic-inquiry-independent-review.md) | Model-originated vervolgvragen, algemene onafhankelijke toetsing en sterke vergelijkingsarmen worden geëist. Onafhankelijke goedkeuring en werkende evaluator ontbreken nog. | Dat het onderzoeksontwerp al constructvalide of uitvoerbaar is. |

Een belangrijke **correctie op een mogelijke schijnfout**: de historische komma-/lijstopsplitsing is aanwezig in de normalisatiecode, maar de gecontroleerde live chat-intake zet split_broad=False. De audit mag dus **niet** beweren dat de huidige modelchat alle complexe voorstellen op komma's versnijdt. De resterende vraag is welke betekenis via de detectoropdracht, nummerparser, maximaal toegestane kandidaten, atomiciteitscontrole en semantische deduplicatie behouden blijft of verloren gaat.

## Beoordeling: negen punten die de interpretatie kunnen veranderen

De prioriteiten hieronder geven de **volgorde van methodische aandacht** aan, geen wetenschappelijke score of EAI-classificatie. Bij ieder punt: feitelijke bron, gevolg voor de interpretatie en minimale reparatie vóór een relevante claim.

### B1. Opgeroepen mogelijkheid is niet hetzelfde als een zelfstandig ontdekt intern signaal — hoog

**Bron:** [current-pair- en generative-prompts](../../../src/shadowseed/detection/model_detector.py), [stap-1 vergelijkingsarmen](step1-model-signals-gap-origin-2026-10-25.md).

**Observatie:** de detector wordt doelbewust gevraagd een niet-benoemde relatie of andere invalshoek te zoeken. Current-pair ziet bovendien het gewone conceptantwoord. Generative v0.4 bevat een aangezette, genummerde antwoordvorm en voorbeelden.

**Gevolg:** een bruikbare kandidaat kan een effect zijn van de prompt, sampling of het lezen van het eerste antwoord. Haar verschijning bewijst geen neuronale detectie, autonome introspectie of uniek Shadowseed-mechanisme.

**Vereiste afspraak:** houd vóór scoring aparte condities vast voor herhaald gewone generatie, current-pair, generative, doelbewust alternatieven zoeken, semantische variatie en detectie zonder conceptantwoord. Gebruik identiek model en eerlijke totale kosten. Rapporteer de **procedure die de kandidaat zichtbaar maakte**. Een modelinterne claim blijft alleen mogelijk met een afzonderlijke activatie-/interventiestudie.

### B2. De vorm van een seed mag de grens van het onderzoek niet bepalen — hoog

**Bron:** [detectorcode](../../../src/shadowseed/detection/model_detector.py), [intake](../../../src/shadowseed/intake.py), [oorspronkelijke these](../possibility-space-thesis.md).

**Observatie:** current-pair vraagt één gap per kandidaat, accepteert hoogstens het geconfigureerde aantal en de parser verwacht genummerde regels; niet-genummerde uitvoer wordt in het offline instrument terecht zichtbaar als parseverlies. De intake moet de kandidaat structureel acceptabel vinden. De oorspronkelijke these laat óók interacties tussen relaties of veranderingen van een interpretatiekader toe.

**Gevolg:** een inhoudelijk interessante relatie kan niet verschijnen door de generatieregels, als niet-genummerde tekst verdwijnen of in een bestaand cluster terechtkomen. Dat is niet hetzelfde als bewijs dat de mogelijkheid er niet was. Omgekeerd is een correct geformatteerde seed niet vanzelf betekenisvol.

**Vereiste afspraak:** behoud per modelcall ruwe tekst, kandidaatpositie, ingekorte uitvoer, parserstatus, pre-/post-intaketekst, afwijzing en semantische samenvoeging. Laat onafhankelijke beoordelaars ook een geblindeerde steekproef uit **afgevallen en niet-geparseerde** tekst beoordelen. Houd complexere relationele voorstellen als onderzoeksobservatie beschikbaar; wijzig daarvoor niet stilzwijgend het product-seedschema.

### B3. Een algemene evaluator kan ongewone vragen alsnog wegfilteren — hoog

**Bron:** [G0 v3](g0/dynamic-inquiry-protocol-candidate-2026-10-25.md), [G0-reviewvragen](g0/dynamic-inquiry-independent-review.md).

**Observatie:** de nieuwe onderzoeksrichting vereist een onafhankelijke uitvoerder voor onverwachte, door het model voorgestelde vragen. Zo'n uitvoerder moet wel een afgebakende taaktaal en toetsregels hebben.

**Gevolg:** de evaluator kan ongemerkt bepalen welke vragen als onderzoekbaar meetellen. Een vraag buiten zijn ondersteunde taal mag niet automatisch worden gecodeerd als onzinnig of onjuist.

**Vereiste afspraak:** toets de dekking van de evaluator apart met nieuwe, veilige, verrassende vragen van een andere auteur. Rapporteer afzonderlijk: toegestaan en informatief; toegestaan maar niet informatief; verworpen met inhoudelijke reden; **buiten bereik van deze evaluator/onbeslist**. Laat een onafhankelijke domeinbeoordelaar de laatste categorie inspecteren. Zet de taal en de afwijzingsregels vóór de proef vast, zonder de onderzochte nieuwe mogelijkheden inhoudelijk voor te schrijven.

### B4. Een latere goede vraag bewijst nog geen verandering die aan de seed is toe te schrijven — hoog

**Bron:** [herzien Q1/Q2-protocol](revised-q1-q2-experiment-2026-10-25.md), [A/B/C/D/E-contract](g0/adapter-evaluation-contract-2026-10-25.md).

**Observatie:** dezelfde nieuwe informatie kan gewone modelredenering, doelbewuste zoekstrategieën en een herinnerde seed allemaal helpen. De echte GPT-5-pilot liet dit concreet zien.

**Gevolg:** alleen een goede T3-vraag of een lange keten van vragen is onvoldoende. De kandidaat moet aantoonbaar **specifiek bijdragen** aan een andere latere onderzoeksmogelijkheid, vergeleken met een sterke gewone route.

**Vereiste afspraak:** bevries kandidaat, timing, toegestane kennis en toets vóór toekomstige feedback. Vergelijk het echte gewichtloze traject met gewone generatie, sterke zoekstrategie, gewone notities en exacte kandidaatablatie met een vergelijkbare neutrale vervanging. Houd alle nutteloze, triviale, mislukte en niet-ontstane vervolgvragen in de uitkomst. Een succesvolle gewone baseline telt als tegenbewijs voor een exclusieve Shadowseed-bijdrage.

### B5. Hoe wordt een gewichtloze seed onderzocht zonder de product-Gate te omzeilen? — hoog

**Bron:** [stap 1](step1-model-signals-gap-origin-2026-10-25.md), [adaptercontract](g0/adapter-evaluation-contract-2026-10-25.md), [productchat](../../../src/shadowseed/chat.py).

**Observatie:** de geaccepteerde productregels scheiden gewichtloze observaties van bevoegde invloed op een antwoord. De beoogde Q2-studie moet een kandidaat wel als **onderzoeksvraag** kunnen gebruiken.

**Gevolg:** zonder expliciete onderzoeksinterface kan de experimentele D-arm ongemerkt een onbetrouwbare kandidaat in de gewone hostprompt stoppen en daarmee de bestaande veiligheid omzeilen. Een arm die de kandidaat juist nooit kan onderzoeken, test Q2 niet.

**Vereiste afspraak:** beschrijf vooraf een geïsoleerde, alleen-lezen onderzoeksroute met zijn eigen taak, toestemming, output en logging. Een candidate mag daar als **te toetsen hypothese** voorkomen, niet als feit of verborgen instructie voor het gebruikersantwoord. Geen mutatie van productstate, Gate, point-of-use, weight, trace, TTL/TrTL of geaccepteerde ADR's. Ontbreekt een gecontroleerd pad, dan geen longitudinale Q2-uitvoering.

### B6. Groei, herhaling en spoorsterkte zijn drie verschillende dingen — hoog

**Bron:** [stap-1 instrument](step1-gap-birth-instrument-2026-10-25.md), [meerturnsplan](step1-model-signals-gap-origin-2026-10-25.md).

**Observatie:** de offline meting toonde dat trace over turns kan dalen ondanks nieuwe herkenning. De meetcode is gerepareerd om geboorte, herdetectie, TTL-voorbereiding en de latere toestand afzonderlijk te bewaren.

**Gevolg:** extra mentions, occurrence_count, traceverandering of alleen een nieuwe string zijn geen bewijs dat de betekenis van een seed is gegroeid. Een seed die niet groeit kan een volkomen geldige uitkomst zijn.

**Vereiste afspraak:** vergelijk per turn (a) identiteit van de oorspronkelijke open relatie, (b) eventuele nieuwe voorwaarde, afhankelijkheid of onderscheid, (c) nieuwe onafhankelijke onderzoeksvraag, (d) externe toetsing, (e) verdwijnen, samenvoegen of terecht niet-reactiveren. Bewaar zowel **geen groei** als betekenisvolle verandering zonder een samengestelde groeiscore op te leggen. Laat identiteits- en transformatieoordelen blind beoordelen op de ruwe tijdlijn.

### B7. De auteur, het model, de detector en de omgeving mogen niet één 'AI-ontdekker' worden — hoog

**Bron:** [bewijsregister](step1-evidence-register-2026-10-25.md), [G0-reviewformulier](g0/dynamic-inquiry-independent-review.md).

**Observatie:** een onderzoeker kiest de casus en het testkader; de host genereert; een apart model kan kandidaattekst voorstellen; parser en embeddings verwerken; mensen of een externe omgeving leveren latere informatie; beoordelaars bepalen wat betekenisvol telt. In eerdere trials schreef de onderzoeker relevante vervolgscenario's al voor.

**Gevolg:** een mooie latere onderzoeksvraag kan vooral uit menselijke aanwijzingen, nieuwe toegestane acties of de evaluator voortkomen.

**Vereiste afspraak:** bewaar per gebeurtenis actor/rol, exacte zichtbare context, tijdstip, tooltoegang, ingebrachte kennis en beslissende menselijke interventie. Noteer of een interpretatie *model-originated, prompt-cued, researcher-provided, environment-provided, reviewer-inferred* of onbeslist is. Dat zijn **herkomstcategorieën voor onderzoek**, geen nieuwe productlabels of EAI-scores. Laat de opdrachtgever en casusauteur niet zelf de geblindeerde eindbeoordeling ondertekenen.

### B8. De onderzoeksdocumenten spreken elkaar tegen over toekomstige feedback — hoog, concreet tekstconflict

**Bronnen:**
- [Herzien Q1/Q2-protocol](revised-q1-q2-experiment-2026-10-25.md): de armen krijgen 'the same revealed future observations'.
- [A/B/C/D/E-adaptercontract](g0/adapter-evaluation-contract-2026-10-25.md): ieder krijgt 'the actual result of their own allowed interventions', bij equivalente mogelijkheden.
- [G0 v3](g0/dynamic-inquiry-protocol-candidate-2026-10-25.md): gelijk aantal toolobservaties en toegestane experimenten.

**Observatie:** deze instructies zijn niet in alle dynamische experimenten tegelijk mogelijk. Twee armen kunnen andere geldige meetvragen stellen en daardoor noodzakelijk verschillende waarnemingen terugkrijgen.

**Gevolg:** een onuitgesproken keuze tussen vaste feedback en eigen interventiegevolgen kan de Q2-vergelijking vertekenen.

**Vereiste afspraak:** maak vooraf **twee verschillende onderzoeksvormen**:
- *Vaste-feedbacktoets:* dezelfde vervolggegevens voor alle armen; meet interpretatie/onderzoeksvragen onder gelijke informatie. Dit kan niet op zichzelf het voordeel van verschillende zelfgekozen meetinterventies aantonen.
- *Adaptieve onderzoekstoets:* gelijke rechten, mogelijkheden, kosten en evaluatorregels; iedere arm krijgt de werkelijke uitkomst van zijn **eigen** gekozen vraag. Het verschil in ontvangen inhoud is hier een te onderzoeken gevolg, geen vanzelfsprekende protocolfout.

Rapporteer die uitkomsten apart; stel van tevoren vast welke vorm welk deel van Q2 toetst. De bestaande documentteksten zijn nog niet op dit punt gelijkgetrokken.

### B9. Voorbereiding is geen onafhankelijke bevestiging — hoog

**Bron:** [ongevulde G0-review](g0/dynamic-inquiry-independent-review.md), [onderzoeksstatus](../status.md), [stap-1 meetinstrument](step1-gap-birth-instrument-2026-10-25.md).

**Observatie:** het offline instrument werkt technisch en de ontwerpdocumenten zijn uitgebreid. Toch is er geen ingevulde onafhankelijke inhoudelijke G0-beoordeling, geen werkende algemene evaluator, geen nieuwe afgesloten confirmatieset en geen vooraf vastgesteld minimumeffect met passende steekproefomvang.

**Gevolg:** een groene workflow of deze Blindspot-audit kan wetenschappelijke goedkeuring niet vervangen. Een automatisch of door dezelfde auteur gelabeld voorbeeld is geen onafhankelijke validatie.

**Vereiste afspraak:** laat een aparte methodereviewer en een technische evaluatorreviewer ieder een versiegebonden, gemotiveerde GO/NO-GO met mogelijkheid tot veto afgeven. Vooraf: evaluatietaal, onbeslist-categorie, negatieve gevallen, verdeelsleutel tussen ontwikkel/confirmatiegevallen, totale kosten en stopregels vastzetten. Houd de reviewledger **ongevuld** tot echte externe beoordelingen binnen zijn.

## Wat al aantoonbaar goed is, en niet opnieuw gebouwd moet worden

- De oorspronkelijke filosofische hoofdvraag is letterlijk bewaard en is niet teruggebracht tot antwoordaanvulling of RAG.
- De echte scheiding tussen modelantwoord, detectie, parser, kandidaatobservatie, seed-geboorte en latere Gate bestaat al.
- De echte productchat splitst modelzinnen niet automatisch op komma's; eerdere intakefouten zijn expliciet onderzocht.
- Het offline instrument gebruikt echte productmethoden en corrigeert eerder door elkaar gehaalde geboorte en herdetectie.
- De eerste 24-call-mislukking en de 30-call-niet-onderscheidende proef zijn niet als succes herschreven.
- De plannen erkennen dat H-Neurons/activaties een **ander meetobject** zijn en dat modeluitvoer geen verborgen neuronale representatie bewijst.
- Een nuluitkomst, een gewone sterke modelbaseline die even goed presteert en een seed die terecht verdwijnt moeten allemaal geldig blijven.

## Minimale volgorde vóór een nieuwe live modelproef

1. **Maak één versiegebonden meetcontract:** wat telt als niet geselecteerd (Q1), als onderzoekbare kandidaat, als echte gewichtloze geboorte, als inhoudelijke transformatie en als onafhankelijk getoetste nieuwe onderzoekbaarheid (Q2). Laat 'onbeslist' werkelijk mogelijk.
2. **Los B8 expliciet op:** kies vooraf vaste-feedbacktoets, adaptieve interventietoets of beide als afzonderlijke experimenten. Behoud een sterke gewone modelbaseline, gewone notities en kandidaatspecifieke ablatie.
3. **Toets de beoordelaar vóór het model:** generaliseerbare, veilige, onverwachte vragen; negative/no-opportunity; afgewezen versus niet-beoordeelbare vragen; aparte domeinreview. Geen categorieën of antwoordketens die de gewenste vondst al voorschrijven.
4. **Beoordeel het observatiepad end-to-end:** de bestaande detectorpromptversies, ruwe output, parser-/intakeverlies, één blijvende manager over turns, recurrences en betekenisverschuiving, zonder productcode te wijzigen.
5. **Teken de herkomst en rolverdeling uit:** model, detector, onderzoeker, gebruiker, omgeving, tools en menselijke reviewers. Bevries elke kandidaat vóór nieuwe feedback.
6. **Vraag echte G0-review aan:** twee onafhankelijke, verschillende beoordelaars en verse confirmatiegevallen; een afwijzing blijft afwijzing. Pas na goedgekeurde methode volgt afzonderlijke toestemming voor een begrensde, betaalde modelproef.

## Eindbesluit en claimgrens

**Onderbouwd door code en bestaande runs:** de Shadowseed-pijplijn kan detectoruitvoer verwerken tot gewichtloze, herleidbare seeds; de nieuwe offline audit meet geboorte en herdetectie zonder een nieuwe detector te bouwen. De 30-call GPT-5-proef gaf geen onderscheidende Shadowseed-winst in de geteste fictieve gevallen.

**Nog niet vastgesteld:** dat de huidige detector betekenisvolle onuitgesproken mogelijkheden vindt voorbij een sterke, eerlijk bekostigde gewone modelprocedure; dat er een bijzonder modelintern signaal voor zulke mogelijkheden bestaat; dat één seed inhoudelijk groeit; of dat die seed **causaal** andere toekomstige onderzoeksvragen mogelijk maakt.

**Dit document levert uitsluitend een interne methodische controle.** Het vult geen G0-reviewveld, verleent geen Gate-autoriteit en rechtvaardigt geen empirische Q1/Q2-claim. De EAI Blindspot-werkwijze helpt vooral bij brontrouw, actorherkomst, ontbrekend bewijs en claimgrenzen. De inhoudelijke categorieën van EAI horen **niet** thuis als voorselectie in Shadowseed.

De eerste volgende handeling is methodisch, niet architectonisch: B8 eenduidig maken en het onafhankelijke evaluatorontwerp beoordelen, waarna pas een echte modelstudie zin heeft.
