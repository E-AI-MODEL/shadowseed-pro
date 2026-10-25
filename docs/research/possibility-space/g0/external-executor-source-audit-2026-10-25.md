# G0: source-codeaudit van externe onderzoeksomgevingen, geen uitvoeringsproef

> **Datum:** 2026-10-25. **Basis:** gecontroleerde publieke broncode op vastgezette commits; oorspronkelijke [bureauvergelijking](external-benchmark-feasibility-2026-10-25.md) plus [Blindspot-methodescan](../step1-eai-blindspot-method-audit-2026-10-25.md).
> **Status:** CODE/INTERFACE INSPECTED; NOT EXECUTED; NO EXTERNAL REVIEW; G0 **NOT PASSED**.
> **Reikwijdte:** geen benchmarkresultaten, wetenschappelijke validatie, nieuwe modelaanroepen of goedkeuring om onbetrouwbare code uit te voeren. De [volledige tweedelige hoofdvraag](../../possibility-space-thesis.md) blijft de enige vraagautoriteit; Q1 en Q2 mogen niet in een taakscore worden samengevoegd.

## Waarom dit document bestaat

De oude desk screen stelde een code/API-controle als volgende stap. Die is hieronder **deels uitgevoerd op bronniveau**: concrete repository, exacte commit, publieke methoden, scoremechaniek, autorisaties en zichtbare veiligheidsrisico's. Er is **geen functionele live-executie** geweest: het beschikbare werkcontainer-netwerk kon GitHub niet resolven; download van een commit-archief was evenmin beschikbaar. Het is onjuist om een gelezen methode als een geslaagd runtime-experiment te presenteren. De code van de onderzoeksomgevingen is niet gekopieerd of in Shadowseed opgenomen.

G0 verlangt meer dan een simulator. Hij moet een grote, vooraf **niet door de onderzoeker opgelijste** familie veilige en zinvolle vragen kunnen uitvoeren, de vraag uit de oorspronkelijke modelgeneratie/seed herkennen, en een **later** ontstane onderzoekbare mogelijkheid los van antwoordkwaliteit meten. Een evaluator mag een ongewone vraag **niet-toetsbaar** noemen, maar mag die niet automatisch als onzinnig afwijzen.

## Exact gecontroleerde upstream-versies

| Omgeving en bron | Vastgezette broncommit | Code/interface | Licentiegrens |
| --- | --- | --- | --- |
| **DiscoveryWorld**, [allenai/discoveryworld](https://github.com/allenai/discoveryworld) | [fd591323920be0d3786ef350955de1945aa571e5](https://github.com/allenai/discoveryworld/commit/fd591323920be0d3786ef350955de1945aa571e5) | [DiscoveryWorldAPI.py](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/discoveryworld/DiscoveryWorldAPI.py) + [TaskScorer.py](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/discoveryworld/TaskScorer.py) + [agents/README.md](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/agents/README.md) | Apache-2.0 voor code, **niet automatisch** voor de meegeleverde CuteRPG-afbeeldingen; aparte licentievoorwaarden |
| **DiscoverPhysics**, [SampsonML/DiscoverPhysics](https://github.com/SampsonML/DiscoverPhysics) | [33b7fa9df96de9c35744efd181ca7e5a8dd60ad5](https://github.com/SampsonML/DiscoverPhysics/commit/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5) | [executor.py](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/executor.py) + [agent.py](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/agent.py) + [evaluator.py](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/evaluator.py) | MIT voor de repository |
| **WorldTest / AutumnBench** interface, [BasisResearch/MARAProtocol](https://github.com/BasisResearch/MARAProtocol) | [d0d4e9251151778415cc5195c5dfb8296a5ded24](https://github.com/BasisResearch/MARAProtocol/commit/d0d4e9251151778415cc5195c5dfb8296a5ded24) | [mara_environment_service.proto](https://github.com/BasisResearch/MARAProtocol/blob/d0d4e9251151778415cc5195c5dfb8296a5ded24/protocols/mara_environment_service.proto) | MIT voor deze connectorcode; geen herlicentiëring van externe benchmarkdata |
| **Autumn interpreter**, [BasisResearch/Autumn.cpp](https://github.com/BasisResearch/Autumn.cpp) | [0929d175c3d296de091ac4b998d09b9b55a38f67](https://github.com/BasisResearch/Autumn.cpp/commit/0929d175c3d296de091ac4b998d09b9b55a38f67) | [README](https://github.com/BasisResearch/Autumn.cpp/blob/0929d175c3d296de091ac4b998d09b9b55a38f67/README.md) | MIT voor interpretercode |

De oorspronkelijke literatuur: [DiscoveryWorld, NeurIPS 2024](https://papers.nips.cc/paper_files/paper/2024/hash/13836f251823945316ae067350a5c366-Abstract-Datasets_and_Benchmarks_Track.html), [DiscoverPhysics, arXiv 2605.26087v2](https://arxiv.org/abs/2605.26087), [WorldTest, ICML 2026](https://proceedings.mlr.press/v306/warrier26a.html). Een paperbeschrijving of upstream README is geen door ons uitgevoerde functionaliteitstest.

## E1, kandidaat A: DiscoveryWorld heeft wel een echte interactie-interface

**Wél direct bevestigd in broncode:**

- [`loadScenario(scenarioName, difficultyStr, randomSeed, numUserAgents)`](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/discoveryworld/DiscoveryWorldAPI.py#L73-L123) construeert een wereld en scenario met de opgegeven seed.
- [`getAgentObservation`, `listKnownActions`, `performAgentAction`, `tick`](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/discoveryworld/DiscoveryWorldAPI.py#L128-L363) onderscheiden waarnemen van toegestane, door de agent gekozen interacties. Acties hebben JSON-namen en object-/richtingargumenten. Dat laat onverwachte **reeksen van bestaande handelingen** toe.
- [`getTaskScorecard`](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/discoveryworld/DiscoveryWorldAPI.py#L232-L240) geeft een vooraf vastgesteld taakscoreformulier, met expliciete waarschuwing dat de **oracle-kennis nooit aan de agent getoond** mag worden.
- [TaskScorer.py](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/discoveryworld/TaskScorer.py) werkt met scenario-/taakspecifieke score-elementen en vooraf geschreven `criticalQuestions`. Een hoge taskscore is daarmee geen onafhankelijk bewijs voor een door de agent bedachte nieuwe **latere onderzoeksvraag**.

**Drie bronspecifieke risico's:**

1. [`loadScenario`](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/discoveryworld/DiscoveryWorldAPI.py#L108-L121) bouwt de nieuwe user interface op via `self.ui.append(ui)`, zonder daarin expliciet de oude lijst te legen. Een experiment mag daarom niet aannemen dat *herladen op hetzelfde API-object* een schone, onafhankelijke arm oplevert; gebruik minstens een **verse API-instantie per arm**, een **unieke `threadID`** voor framebestanden, en controleer ook proces- en outputisolatie. De [officiële API-handleiding](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/README.md) waarschuwt dat een gedeelde `threadID` frames kan overschrijven.
2. [Upstream agentdocumentatie](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/agents/README.md) noemt seeds **0–4** als oorspronkelijk gebruikte varianten; hogere seeds zijn niet op alle thema's/difficulties gecontroleerd en kunnen falen. Een nieuwe confirmatieset mag die fout niet stilzwijgend als nul voor Q1/Q2 tellen.
3. De API is niet vanzelf een **algemene semantische vraagevaluator**. De actieparser beoordeelt uitvoerbaarheid van handelingen; het bestaande taakscoreformulier beoordeelt voorgegeven doelen. Een door het model zelf geformuleerde andere onderzoeksvraag vereist een aparte onafhankelijke beoordeling van relevantie, informatieverschil en de latere gevolgvragen. De wereld bevat ook grafische assets met afzonderlijke gebruiksvoorwaarden. De volledige `world.exportWorldHistoryJSON()`-logs bevatten volgens de [API-handleiding](https://github.com/allenai/discoveryworld/blob/fd591323920be0d3786ef350955de1945aa571e5/README.md) eigenschappen van objecten buiten het agentzicht: bewaar die alleen in de afgesloten beoordelaarsomgeving, **niet** in de agentprompt, samenvatting of Shadowseed-observatie.

**Begrensd besluit:** DiscoveryWorld is de **eerste kandidaat voor een E1-interface-preflight**, niet een goedgekeurd G0-construct of een aantoonbaar Q2-benchmark.

## E1/E2, kandidaat B: DiscoverPhysics levert experimentuitkomsten maar geen Q2-oordeel

**Wél direct bevestigd:**

- [`SimulationExecutor.run(experiments: list[dict])`](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/executor.py#L242-L376) accepteert door de agent samengestelde numerieke experimenten met o.a. `p1`, `p2`, `pos2`, `velocity2` en `measurement_times`, en levert trajectposities en -snelheden terug. Andere world executors accepteren hun eigen experimentgrammatica.
- De [DiscoveryAgent-loop](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/agent.py#L190-L475) verwerkt `<run_experiment>` als agentoutput en geeft echte simulatiefeedback. Daarmee is sprake van meerdere experimenteerrondes, niet per definitie van echte Shadowseed-turns.
- De [noise-initialisatie](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/executor.py#L170-L212) ondersteunt een `noise_seed`; **een identieke seed** geeft niet automatisch identieke willekeurige ruis als arms verschillende aantallen of volgordes van meetverzoeken uitvoeren. De analyse moet dat verschil als onderdeel van traject-/kostenprovenance vastleggen of common-random-number-koppeling expliciet ontwerpen.
- De [standaardevaluator](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/evaluator.py#L105-L247) toetst vooral de ingediende **bewegingswet** op trajectfout, niet of een eerdere gewichtloze kandidaat een nieuw zelfstandig onderzoek heeft geopend.

**Twee concrete veiligheidsblokkades:**

1. [`_compile_law`](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/evaluator.py#L1218-L1231) voert model-geleverde Python-broncode uit met **`exec(compile(...))`**. Een timeout rond latere functieroepen is geen procesisolatie van die eerste `exec`. **Niet** met onbetrouwbare modelcode aanroepen in een product- of researchrunner zonder zelfstandige, getoetste OS-/containerisolatie en beperkte rechten.
2. De [`SimulationExecutor._run_one`](https://github.com/SampsonML/DiscoverPhysics/blob/33b7fa9df96de9c35744efd181ca7e5a8dd60ad5/ScienceAgent/scienceagent/executor.py#L297-L368) berekent het aantal simulatiestappen uit de opgevraagde tijdsduur en `dt`; in dit aangetroffen pad is geen harde bovengrens voor elke door de agent gewenste simulatieduur zichtbaar. Een **eigen invoervalidator en harde rekentijdgrens** zijn dus vereist vóór uitvoering van ongecontroleerde modelvoorstellen.

**Constructgrens:** dit is onderzoek naar het reconstrueren van een door de auteur gekozen natuurwet uit experimenten. Het is geschikt voor een *mogelijke* numerieke algemene-interventiecontrole. Het bewijst niet dat de modelagent een nieuwe onderzoekscategorie ontwikkelt, noch dat het verloop door een Shadowseed is veroorzaakt.

**Begrensd besluit:** alleen de **simulatorinterface**, onder vooraf getoetste inputbegrenzing en isolatie, is kandidaat voor een tweede technische preflight. De bestaande evaluator met `exec` is **geen** veilige onbewerkte integratieroute. Geen E2-goedkeuring.

## AutumnBench/WorldTest: goede technische referentie, geen open Q2-test

De [MARA-environmentservice](https://github.com/BasisResearch/MARAProtocol/blob/d0d4e9251151778415cc5195c5dfb8296a5ded24/protocols/mara_environment_service.proto) heeft `Initialize`, `Reset`, `Step`, `QuerySpaces` en `Close`: bruikbare scheiding van actor, omgeving en toegestane actie. [WorldTest](https://proceedings.mlr.press/v306/warrier26a.html) meet drie vooraf benoemde queryfamilies (masked prediction, change detection, planning) over 43 werelden en 129 taken. Het laat goed zien hoe een omgeving een antwoord **gedragsmatig** kan toetsen. De methode laat de agent echter primair **reageren op door het benchmark gekozen testvragen**, en bewijst niet dat het model zelf een nieuwe klasse latere onderzoeksvragen formuleerde. Dit is dus een **referentie voor uitvoer-/resetcontracten en sterke gewone-modelcontroles**, geen zelfstandig G0-bewijs.

## Minimaal zelfstandig te toetsen interfacecontract, zonder model-API

Onderstaande eisen zijn **tests die nog moeten worden uitgevoerd**, geen resultaten. Maak de omgeving exact versiegebonden, code-/assetrechten beoordeeld en de runner geïsoleerd. Voer pas na de benodigde toestemming een hermetische **offline technische preflight** uit; gebruik **geen** betaald model, bekende antwoorden of publieke benchmarkcases als afgesloten confirmatieset.

| Test | Waarnaar kijken | Falen als... |
| --- | --- | --- |
| **P1. Schone armkloon** | Twee aparte instanties/processen met dezelfde gepinde scenario- en wereldseed leveren bij start dezelfde toegestane observatie, toolinventaris en beperkingen | Een arm toegang houdt tot eerdere acties, framebestanden of een oracle-scorecard van een ander, of via volledige wereldlogs verborgen regels leert |
| **P2. Echte onverwachte actie** | Een onafhankelijk van benchmark-antwoordsleutels geschreven, veilige actie binnen de beschikbare grammatica levert een nieuwe, reproduceerbare simulatorobservatie | Alleen vooraf opgesomde "juiste antwoorden" uitvoerbaar zijn; onbedoelde scorefeedback lekt |
| **P3. Afwijzing versus onbeslist** | Onderscheid *uitvoerbaar*, *syntactisch ongeldig*, *niet toetsbaar door deze evaluator*, *geen nieuwe veilige mogelijkheid*, *uitvoerfout* | Een interessante, niet ondersteunde vraag als "onwaar" wordt weggeschreven, of een uitvoerfout als abstentie/NONE |
| **P4. Meerturnstraject** | In één doorlopende researchstaat: eerste onafhankelijke generatie, detector met raw/parserprovenance, echte gewichtloze geboorte, vervolgobservatie, al dan niet andere latere vraag | D pas na T2 wordt aangemaakt; twee hypotheses in één prompt als "longitudinaal" tellen; weightless kandidaat als feit in productieantwoord verschijnt |
| **P5. Negatief/sham** | Nietszeggende en misleidende maar toelaatbare voorstellen, geen-opportunity, neutrale vervangseed en correcte niet-reactivatie | Alleen succesvolle vragen in de noemer zitten of een toevalsverschil in gewone notities als D-specifiek wordt geteld |
| **P6. Resource- en veiligheidsgrenzen** | Zelfde actie-/tool-/modelbudget per arm; werkelijk gebruikte compute/vragen/ruis vast; publieke code en assets afzonderlijk licentiegetoetst; geen exec van LLM-code zonder sandbox | Onbegrensde simulaties, onveilige code-evaluatie, verborgen evaluator-data of ongedekte externe kosten |
| **P7. Semantische onafhankelijke toets** | Een **andere, geblindeerde** beoordelaar bepaalt of een model-originated, eerst onbekende vraag later inhoudelijk iets **anders onderzoekbaar** maakte; onbeslist is toegestaan | Taskscore, syntaxisacceptatie, een extra gegenereerde zin of modelzelfbeoordeling voldoende wordt verklaard |

**RF versus RI:** test P1–P7 onder een vooraf gekozen [feedbackregime](adapter-evaluation-contract-2026-10-25.md#two-noninterchangeable-future-feedback-regimes-b8-resolution-proposed). RF geeft iedereen dezelfde vastgelegde latere waarnemingen, RI geeft alle armen hetzelfde *recht op* handelingen maar de werkelijke uitkomst van hun **eigen** handeling. De uitkomsten blijven afzonderlijk. Nog géén van deze tests is vanuit dit auditdossier geslaagd verklaard.

## Wat aan reviewers overgedragen moet worden

**Technisch onafhankelijke beoordelaar:** kies een *exacte upstream commit*; test P1, P2, P3 en P6 in een veilige, gecontroleerde omgeving. Onderbouw met runlogs, code, foutgevallen, reproduceerbare stappen, licenties en een NO-GO-veto. Verifieer werkelijk dat een vraag die niet in een antwoordset voorkomt door de omgeving **toetsbaar** is, niet alleen dat een JSON-actie geaccepteerd wordt.

**Conceptueel onafhankelijke beoordelaar:** beoordeel P4, P5 en P7 én H0–H5. Probeer elke veronderstelde winst te reduceren tot gewone modelzoekactie, active learning, extra budget, bekende meetkunde/fysica, extra tools, auteurshints of reviewerpreferenties. Keur Q2 niet goed als een nieuwe vraag slechts een variant is van een vooringestelde natuurwetopgave.

**Herkomst:** bewaar de exact gebruikte upstream-sha's; runlogs/versies, modelinstellingen, originele antwoorden, kandidaat-/parserverlies, onderzoeksvraag, toolhandelingen, externe feedback, beoordelaar, afwijzingen en onbekende gevallen. Geen aparte Shadowseed-authority-route.

## Onderbouwd besluit per 25 oktober 2026

- **E1 technische prioriteit:** DiscoveryWorld **voor een afgeschermde API-preflight**, gevolgd door mogelijk simulator-only DiscoverPhysics voor parametrische acties. Dit is een volgorde voor onderzoek, **geen positief G0-verdict**.
- **E2 constructstatus:** geen van deze bronnen toont dat de vereiste *zelfstandig ontstane en later opnieuw geëvalueerde* onderzoekbaarheid met de bestaande scorer algemeen wordt gemeten. **Nog geen kandidaat geaccepteerd**.
- **G0:** **NOT PASSED**, want onafhankelijke technische en methodische beoordelingen, runnable sealed evaluator, nieuwe verborgen confirmatieset en geslaagde end-to-end-toets ontbreken. De [officiële reviewerledger](dynamic-inquiry-independent-review.md) blijft leeg.
- **Productie:** niets gewijzigd aan de productdetector, chatmanager, intake, Gate, trace, weight, TTL, TrTL, ADRs, sleutels of CI-research dispatch. De ongeteste omgeving **niet** direct integreren.

Deze uitkomst is een broncode- en methoderapport. Geen uitgevoerde benchmark, geen negatieve testuitslag over Shadowseed, geen claim van een nieuw soort denken en geen toestemming voor een betaalde Q1/Q2-proef.
