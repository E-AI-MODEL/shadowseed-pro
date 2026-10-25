# Technische bijlage stap 1: van H-Neurons naar onderzoek van ongekozen mogelijkheden

> 25 oktober 2026. **Methodische vergelijking, geen nieuwe neurale meting.**
> Onderdeel van [de uitgebreide stap-1-studie](step1-model-signals-gap-origin-2026-10-25.md) en het [bewijsregister](step1-evidence-register-2026-10-25.md).
> Niet de productdetector vervangen, geen verborgen modeltoegang suggereren en de oude negatieve Laag G-uitkomst niet herinterpreteren.

## 1. Het oorspronkelijke H-Neurons-onderzoek in zeven meetbare stappen

[Gao et al., *H-Neurons* (2025)](https://arxiv.org/html/2512.01797) voerden een onderzoek uit dat zich juist NIET beperkte tot wat een model als antwoord tekstueel zegt.

1. **Genereer onder vaste sampling meerdere antwoorden op dezelfde feitelijke vraag.** In het onderzoeksontwerp werden per vraag tien antwoorden getrokken. Alleen vragen waarvoor alle tien antwoorden correct waren of alle tien onjuist, werden in het hoofdcontrast opgenomen. Dat maakt het gedrag stabieler, maar selecteert ook specifieke gemakkelijk/hardere uitersten; dit mag niet worden vergeten.
2. **Koppel antwoordlabels aan externe feitelijke criteria.** Labels zijn geen zelfbeschrijving van de gesondeerde modelinstantie. De auteurs gebruiken ook een apart model om de feitelijke antwoordspan naar tokens te aligneren. Dat maakt die spanbepaling een onafhankelijke, te controleren annotatiestap, geen betrouwbaar natuurgegeven.
3. **Meet interne feedforward-neuronbijdragen per relevante tokenpositie.** Niet alleen ruwe neuronwaarde, maar de grootte van de naar de residual stream geprojecteerde bijdrage wordt relatief aan de verborgen toestand berekend (CETT).
4. **Scheid antwoordtokens van andere tokens.** Dezelfde hoge activatie bij verbindingswoorden is niet even informatief als tijdens een hallucinerend feitelijk antwoord. Het onderscheid is onderdeel van de negatieve controle.
5. **Train een schaarse, regulier gemaakte lineaire classifier.** De gevonden niet-nulcoëfficiënten duiden een *voorspellende subgroep van neuronfeatures* aan. Dat is nog geen uniek, fysisch onafhankelijk mechanisme.
6. **Test generalisatie en onzekerheid.** Houd achteraf andere datasets/vragen apart, rapporteer classifierprestatie en vergelijk met willekeurige controls.
7. **Grijp pas daarna gericht in activaties in.** De auteurs schalen geselecteerde neuronactivaties tijdens inference en vergelijken het effect op gedrag. De studie bevat ook metingen rond pretraining/alignment.

**Cruciaal:** het LLM wees zijn eigen H-Neurons niet aan. Onderzoekers en code lazen activaties van een model met toegankelijke gewichten. Het model produceerde tekst; het experiment mat intern. Dat is een wezenlijk andere betekenis van het woord "signaleren" dan een tekstuele gapdetector.

### Wat CETT wel en niet is

Voor neuron j en positie t definieert het H-Neurons-onderzoek de genormaliseerde bijdrage CETT als de Euclidische norm van de geprojecteerde bijdrage van neuron j, gedeeld door de norm van de relevante volledige verborgen toestand. De ratio maakt de *sterkte* van een bijdrage vergelijkbaar bij antwoordposities. Zij identificeert niet automatisch wat een neuron semantisch "bedoelt". De naar een antwoord gelokaliseerde classificatiescore is nog geen causale uitleg en geen verborgen kennisinhoud.

De exacte neuronindex, projectiematrix, breedte en parameterisatie zijn modelafhankelijk. Een lijst neuron-IDs uit Mistral kan niet als dezelfde biologische of semantische eenheden in Qwen worden behandeld.

### Broncontrole: labeloriëntatie in de publicatie en de code

Bij het controleren van de primaire bronnen vond ik een **concrete interne tegenstrijdigheid in de HTML-methodesectie van Gao et al.** De tekst definieert de positieve klasse als hallucinerende antwoordtokens, maar de weergegeven vergelijking laat voor antwoordtokens juist de waarde 1 bij "faithful" zien. De [officiële classificatiecode](https://github.com/thunlp/H-Neurons/blob/main/scripts/classifier.py) maakt de gebruikte implementatie helder: *false answer tokens* krijgen label 1; *true answer tokens* en beide soorten overige tokens krijgen label 0. De [officiële README](https://github.com/thunlp/H-Neurons/blob/main/README.md) noemt deze 3-vs-1-strategie ook expliciet.

Dit lijkt op een **vergissing in de formule/notatie**, maar daaruit volgt zonder volledige reproductie geen conclusie over onjuiste experimentresultaten. Voor onze toekomstige instrumentproef geldt: neem geen labeloriëntatie uit een losse paperzin over zonder code, trainlabels en daadwerkelijke evaluatiesplit naast elkaar te controleren. Controleer ook of "positive coefficient" dezelfde klasse betekent als in de interventiecode.

## 2. De beperkingen van sparse lokalisatie zijn nu expliciet onderzocht

[Cavus et al., 2026, preprint](https://arxiv.org/html/2609.29781) onderzochten twee 4B Gemma-familiemodellen en drie QA-datasets. Zij bevestigen dat een sparse classifier bepaalde gedragstypen kan voorspellen, terwijl gekozen neuronen **niet uniek** lijken. Hun onderzoeksspecifieke cijfers:

- Gemma 3 4B op TriviaQA: AUROC 0.811, op BioASQ: 0.974, op NQ-Open: 0.628. De prestatie is taakafhankelijk; één uitzonderlijk cijfer is geen universele detector.
- Gemma 3 4B: 19 van 22 geselecteerde H-neuronen, geteld over drie datasets, vertoonden correlatie boven |r| = 0.7 met een niet-geselecteerde feature.
- De selectieoverlap tussen bootstraprondes en tussen L1- en L2-rangschikking bleef beperkt, ondanks voorspellende kracht.
- Gerichte activatieonderdrukking had kleine, meetbare effecten vergeleken met matched random same-layer controles. Dat duidt op interventiegevoeligheid, niet op unieke neuronauteurschap van het hele gedrag.

Hun vijf diagnostieken vertalen we niet naar productiecode maar naar mogelijke vereisten voor een **afzonderlijke** latere mechanistische studie: featurecorrelaties, selectie-/bootstrapstabiliteit, L1/L2-discrepantie, matched interventiebaselines, cross-domain/model-overlap.

## 3. De verkeerde doelvariabele van onze eerdere Laag G

In [Round 032](../../../benchmarks/open_review/rounds/round_032/RESULTS.md) en [Round 033](../../../benchmarks/open_review/rounds/round_033/RESULTS.md) werd gemeten of activaties van Qwen2.5-0.5B onderscheid konden maken tussen **expliciet aangeboden stellingen** die GPT-4.1 beoordeelde als WEERLEGD of HOUDT_STAND. De uitkomsten waren niet overtuigend na correctie, en 033 repliceerde 032 niet.

Een verborgen, niet-uitgesproken mogelijkheid is iets anders dan het externe oordeel over een al voorgelegde stelling. Verder staat "extern oordeel van GPT-4.1" niet gelijk aan een onafhankelijk feitelijk experiment. De historische nuluitkomst is geldig op haar eigen taak en schaal, niet op de nieuwe hypothese.

[Issue #203](https://github.com/E-AI-MODEL/shadowseed-pro/issues/203) beschrijft expliciet die verkeerde doelvariabele. De bewust gesloten [PR #204](https://github.com/E-AI-MODEL/shadowseed-pro/pull/204) heeft een P0/P1-instrument dat oorspronkelijke generatieactivaties en latere kandidaatlabels scheidt. Daarin worden tokenuitlijning, model- en datahash, bron-/onderwerp-disjuncte splits en controle op kandidaat-lekkage voorbereid. Een live 14B-meting is niet verricht. De code is onderzoeksprovenance, niet een aangenomen productfunctie.

## 4. Twee mogelijke wetenschappelijke estimands, niet één

Dit is een **nieuw voorstel**, geen feit over modelgewichten.

**E1: algemene detecteerbare ruimte voor alternatieve onderzoeksvragen.**
Kan een vooraf vastgezette activatieweergave van een oorspronkelijke vraag/antwoordgeneratie voorspellen of onafhankelijke onderzoekers later überhaupt een geldige, niet-expliciet uitgesproken onderzoekbare relatie kunnen aanwijzen? Een positieve classificatie kan ook simpelweg taakonzekerheid, antwoordstijl, lengte of onderwerp voorspellen. De vergelijking moet daarom al die eenvoudigere factoren meenemen.

**E2: specifieke kandidaatidentiteit.**
Kan de oorspronkelijke activatieweergave, zonder dat de gesondeerde generatie de kandidaat ziet, later een verband leggen met één **bepaalde** onafhankelijke candidate-familie sterker dan met zorgvuldig gematchte alternatieven? Dat is een veel moeilijkere claim. Zij vereist een vooraf gedefinieerd kandidaat-vergelijkingsprotocol met gelijke onderwerpen, lengte en relationele vorm, plus een krachtig text-only model dat dezelfde kandidaat zonder activaties mag vergelijken.

E1 kan positief uitvallen terwijl E2 faalt. E2 kan een discriminatiesignaal opleveren zonder de candidate semantisch in één neuron te lokaliseren.

### Het identificatieprobleem dat snel vergeten wordt

Eén oorspronkelijk modelantwoord en zijn vaste activaties kunnen achteraf aan veel kandidaatteksten worden gekoppeld. Een classifier die alleen het activatievector ontvangt, kan onmogelijk weten welk later aangewezen tekstkandidaat bij die vector hoort. Verschillende labels voor exact dezelfde vector maken zo'n classifier principieel verkeerd gespecificeerd.

Een kandidaat-geconditioneerde classifier ontvangt alsnog de later gegenereerde candidate-tekst **als externe onderzoeksinput**, niet als deel van de oorspronkelijke modelgeneratie. Die tekst kan het label zelf voorspellen. Vergelijk daarom altijd eerst met een even capabele text-only kandidaatbeoordelaar en met een kandidaat/sham-swap. Een goede score is niet genoeg om verborgen kandidaatrepresentaties aan te tonen.

## 5. De feitelijke tijdsvolgorde die een nieuwe studie moet bewaken

| Tijd | Observatie | Toegestane informatie | Buiten de runtime blijvend |
| --- | --- | --- | --- |
| U0 | Oorspronkelijke vraag, huidige context | Werkelijke vraag en voor zover toegestaan eerdere schone turns | Externe labels, kandidaatdoel en toekomstige gebeurtenis |
| U1 | Normaal antwoord en eventueel originele hidden-state-capture | U0, pinned model en decoder | Geen detectorlabel of kandidaattekst vooraf ingegeven |
| U2 | Onafhankelijke kandidaatexploratie | U0 en wel/niet U1 afhankelijk van vooraf toegewezen arm | Geen latere antwoordinvloed of Gate-promotie |
| U3 | Parser/normalisatie/atomiciteit/intake | De ruwe gelogde U2-output en canoniek intakecontract | Geen herschreven juiste seed achteraf |
| U4...Un | Echte gespreksturns met nieuwe bronfeiten en gebeurtenissen | Correct begrensde gesprekscontext en bestaande managerstaat | Geen automatisch bewijs uit recurrence of embeddings |
| R | Onafhankelijke review | Geanonimiseerde samples, vaste selectie, broncontext | Geen modelarm, activatiescore of verwachte uitkomst |
| Q2 | Toets van later veranderde onderzoekbaarheid | Prospective vraag en onafhankelijke evaluator | Geen fictieve ondervraaglijst die het juiste resultaat al bevat |

De activatiecapture voor E1/E2 is optioneel en vereist echt toegankelijke open-weight-modellen. **De operationele Shadowseed-detector en seedgeboorte hoeven geen neurale detector te hebben.**

## 6. Controleerbare contrasten

**Voor modelgedrag:** hetzelfde sterke model zonder detector; current_pair v0.6; generative v0.4; deliberate exploration met hetzelfde budget; meerdere gewone samples; prompt zonder het ankerende eerste antwoord. Een test mag niet puur uit promptschakelen "neural insight" afleiden.

**Voor gap-to-seed:** ruwe output, parser, normalisatie, één-gap-semantiek, identiteit, bronref, toegelaten/afgewezen en gewichtloze geboorte afzonderlijk registreren. De classifier van modelgedrag mag niet tegelijk kwaliteitslabels voor seeds genereren en als onafhankelijke evaluator fungeren.

**Voor herkenning over meerdere beurten:** dezelfde seed in andere woorden, andere seed met vergelijkbare woorden, inhoudelijk ongerelateerde beurt, extern ondersteunde en contradictoire vervolginfo, en expliciet geen groeisignaal. Embeddinggelijkenis bewijst geen identiteit of bewijs.

**Voor H-Neurons-achtige activaties:** label-shuffle, bron-/topic-disjuncte test, text-only basislijn, onzekerheidsbaseline, syntax/antwoordlengte, correlated-feature/sham controls, random same-layer interventies, bootstrap, correctie over lagen en neuronen, geen leakage van toekomstige kandidaat.

**Voor Q2:** individueel geregistreerde latere onderzoeksvragen, onafhankelijke toets of die werkelijk anders en uitvoerbaar zijn, en een kandidaat-specifieke counterfactual bij gelijke context/toegang. De kandidaat kan ook terecht geen nieuw onderzoek openen.

## 7. Stopregels

- Onvoldoende heldere betekenis van een "niet-uitgesproken mogelijkheid": nog geen voorspellende training.
- Kandidaat of onafhankelijke beoordeling zichtbaar in de originele generatie-input: activatiemetingen ongeldig.
- Geen capabel gepind model/hook/valid tokenalignment: instrument niet geslaagd, geen neurologisch nulresultaat.
- Geen bron-/topic-onafhankelijke test of overfitte sparse feature: geen lokalisatieclaim.
- Geen menselijke onafhankelijke review: bruikbaarheid = model-/onderzoekersoordeel, geen gold.
- Positieve mechanische maar negatieve gedragsmatige uitkomst: rapporteer beide.
- Door gewichtloze kandidaten in het antwoord te injecteren een voordeel creëren: ongeldig als normale productpipelinevergelijking.
- Meerturnsstate achteraf opbouwen: ongeldig voor de hypothese over groei/afname in de schaduw.
- Geen nieuwe vervolgonderzoekbaarheid ondanks meer antwoorden: geen Q2-resultaat.
- Een eerdere null uit ronde 033 met andere taak/modelgrootte automatisch tot nieuw positief of negatief resultaat heretiketteren: verboden.

## 8. Wat we nu wél beslissen

De bestaande productarchitectuur blijft intact. Eerst de onafhankelijke gedragsmatige stap 1 met de **bestaande detectorrollen, intake en observatieregistratie**. Vervolgens echte doorlopende sessies, met groei, verval, terugkeer of geen verandering. Het optionele activatiespoor krijgt alleen een aparte onderzoeksbeslissing nadat construct, mogelijke modeltoegang en onafhankelijke beoordeling aantoonbaar in orde zijn.

Dit document is een protocolvoorstel en literatuur-vergelijking, **geen verzoek om alvast alle denkbare modellen te draaien**. De echte tweeledige Shadowseed-these blijft volledig staan.
