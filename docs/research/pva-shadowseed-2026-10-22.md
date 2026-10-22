# Plan van Aanpak — Shadowseed na de web-only integratie

**Datum:** 22 oktober 2026  
**Status:** werkplan voor toetsing; geen besluit tot release, detectorpromotie of architectuurwijziging  
**Referentie:** main f3ec86c124ab88247e0739a6cbe3c817a6508219, PR #202 (concept)  
**Eigenaar van de uitvoering:** repositorymaintainers; iedere inhoudelijke wijziging via controleerbare PR en tests

## 1. Waarom dit PVA nodig is

We hebben een werkende engine, een afzonderlijke onderzoekspackage en een web-only distributie in main. Maar de centrale vraag is ouder dan die software: kan een taalmodel een interessante mogelijkheid, onzekerheid of twijfel bewaren zonder die direct op te lossen of als waarheid te gebruiken? Inmiddels is de repository deels gaan spreken in termen van hiaten, ontbrekende onderdelen en legacy-onderdelen. Dat vermengt **doel**, **mechaniek**, **historie**, **productstatus** en **bewijs**.

Dit PVA is geen toestemming voor een snelle promptwissel. Eerst het probleem per laag vaststellen, dan verschillende verklaringen of oplossingen toetsen, vervolgens gericht wijzigen en de gevolgen meten. Het bevroren archief wordt niet herschreven om later ontstane inzichten achteraf ouder te laten lijken.

## 2. Gereconstrueerde lijn — van oorspronkelijke bedoeling naar huidige code

| Bron en periode | Wat dit toevoegde | Wat we er vandaag wel/niet uit afleiden |
| --- | --- | --- |
| Historische SSL 4.5 en 4.6; [4.6-brontekst](../../archive/source-docs/00_shadow_seed_learning_4_6.md) | Atomische seed, trace versus weight, levenscyclus, Validation Gate en aparte evaluatielagen A–G. | Mechanische en methodologische herkomst, niet automatisch de huidige runtimeautoriteit. De oude formulering 'precies één gap' is smaller dan de latere generatieve bedoeling. |
| [Generatieve visie, juni en juli 2026](../../archive/source-docs/research/vision-generative-seeds.md) | Het expliciete onderscheid tussen wat had **kunnen** staan en wat had **moeten** staan. Een seed kan een niet-genomen onderzoekrichting zijn; eerste generatieve variant, Retrieval Probe en meerbeurtige tests. | Essentiële herkomst van de doelstelling. Gedurfde mogelijkheden blijven onzeker; een fraaie gedachte wordt niet vanzelf bewezen, bruikbaar of veilig. |
| [Oorspronkelijk PvA van juni](../../archive/source-docs/research/pva-checklist.md) | Open-set detectie, echte wild-to-payofflus, domeintransfer en proefnut; ook negatieve uitkomsten en nul kansen op surfacing. | Voorkomt opnieuw beginnen. Historische afvinkstanden en percentages zijn geen status van oktober en worden niet gekopieerd als actuele bewijzen. |
| [ADR-001, juli](../architecture/adr/ADR-001-validation-gate-authority.md) | Alleen de Validation Gate mag autoriteit veranderen; geheugen mag onzekerheid bewaren zonder te sturen. | Harde invarianten blijven gelden, ook bij nieuwsgierigheid of speculatie. |
| [ADR-002 en doctrine-alignment, augustus](../architecture/adr/ADR-002-epistemic-seed-contract.md) en [plan](../plans/ssl-doctrine-alignment-2026-08.md) | Gap, twijfel en wat-als als mogelijke kandidaten; oude woordgrenzen en normalisatie als heuristiek in plaats van definitie. | Een seed hoeft geen fout te zijn; semantische atomiciteit is nog niet automatisch bewezen door kort of correct geformatteerd tekstgebruik. |
| [ADR-003 tot en met ADR-005](../architecture/) | Contaminatie, onafhankelijke bewijsidentiteit en het chat-first-product als afzonderlijke grenzen. | Recurrence is geen onafhankelijk bewijs; verschillen tussen SSL aan/uit zijn geen bewezen effect zonder feitelijk gesurfacete en toegestane seed. |
| [ADR-009, oktober — voorgesteld](../architecture/adr/ADR-009-runtime-component-orchestration.md) | Component- en rolonderscheid in de interactie, inclusief onderzoek naar andere productregimes. | Een *Proposed* ADR is geen automatische vervanging van het daadwerkelijk geleverde evidence-backed-productbeleid. Eerst besluit en uitvoering verifiëren. |
| [Actuele onderzoeksstatus](status.md) en [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202) | Onderzoeksinstrumenten, kandidaat-review en een inquiry-first detector v0.7 in concept. | Code- en regressietests bewijzen het gedrag van contracten, niet de kwaliteit van modelgegenereerde vragen. |
| [PR #201](https://github.com/E-AI-MODEL/shadowseed-pro/pull/201), 22 oktober | De bestaande browserinterface en Python-engine zijn nu de hoofdroute voor een gecontroleerde download zonder Gradio/Pillow. | Gemerged op main is **niet** hetzelfde als gepubliceerd v0.12.3 of afgeronde lokale Ollama-/productassurance. De optionele Gradio-interface bestaat nog. |

**Werkhypothese, niet als feit presenteren:** Shadowseed kan zinvolle, specifieke, nog niet vaststaande onderzoekrichtingen over meerdere beurten bewaren en later onder bewijs- en gebruiksvoorwaarden helpen. De repo moet toetsen of dat meer is dan gewoon nog een andere prompt.

## 3. Begrippen en beslisgrenzen

Gebruik [het actuele onderscheid tussen productroutes en historisch materiaal](../architecture/surfaces-and-terminology.md). Spreek niet zonder kwalificatie over 'legacy' of 'de Workbench'. Gebruik precies: **lokale webapp** (normale distributie), **Gradio-interface** (optionele oudere UI, niet in de gecontroleerde download), **compatibiliteitsimport** (functionele facade), **onderzoekspackage** (actief maar geen eindgebruikersinterface), **bevroren archief** (historische bron) en **voorgesteld ontwerpbesluit** (nog niet geaccepteerd als nieuw contract).

Een mogelijke vraag of onzekerheid is nog geen aanwijzing dat het voorgaande antwoord incompleet is; herinnering is niet hetzelfde als waarheid. Een nieuw voorstel voor meer autoriteit mag niet via de detector, prompt, UI of onderzoeksharnas binnensluipen.

## 4. Uitvoering — vijf gescheiden sporen

### A. P0 — Begrips- en repositoryruis herstellen

- [x] Historische herkomst, architectuurcontracten, huidige distributie en PR #202 van elkaar onderscheiden.
- [x] Een woorden- en statuskaart publiceren voor webapp, Gradio, imports, onderzoek en archief.
- [x] Actuele product- en architectuurdocumenten corrigeren waar ze web-only nog 'prototype' noemen of Gradio als normale download voorstellen.
- [ ] Repo-brede inventaris afmaken van onduidelijk 'legacy', ongekwalificeerd 'Workbench', obsolete statusclaims en foutieve links in actieve paden. Uitkomst per bestand: vervangen / begrensd toelichten / archiveren / bewust behouden.
- [ ] Functioneel actieve compatibiliteitsinterfaces pas verwijderen nadat imports, downstreamgebruik, migratiepad en regressies zijn vastgesteld. Niet 'legacy' schrappen uit API-namen om teksten netter te laten lijken.
- [ ] Verifiëren of niet-geaccepteerde ADR's, oude conceptplannen en externe uitleg onterecht voor huidige policy worden aangezien. Alleen statuskaders toevoegen; historische besluiten niet herschrijven.
- **Klaar wanneer:** actuele startpunten hebben één duidelijke productroute, één status per route en geen tegenstrijdige claims over de Gate, release of onderzoek. Een review van veranderde links en contracttests slaagt.

### B. P0 — Reproduceerbare en veilige distributie

- [x] Web-only bundel, strikte audit van de geleverde Python-afhankelijkheden, drie platformbuilds en releaseworkflow zijn geïntegreerd via PR #201; **dit zegt niets over gepubliceerde release of live Ollama**.
- [ ] De drie door de Daily Run gemelde npm-advisories reproduceerbaar identificeren met exacte pakket- en CVE/advies-ID's, aangetaste codepaden en gespecificeerde reparaties. Een statische export vermindert mogelijk aanvalsoppervlak maar maakt een auditmelding niet automatisch onschadelijk.
- [ ] Next/React/andere aangetaste dependencies op passende, geverifieerde versies brengen; een lockfile vastleggen, CI naar reproduceerbare installatie en een gecontroleerde JS-audit omzetten, en daarna exports en frozen assets opnieuw testen.
- [ ] Lokale Ollama + EmbeddingGemma praktijkcyclus, ondertekende/provenancechecks, exacte main-SHA en release-criteria onafhankelijk afvinken.
- **Klaar wanneer:** geen onverklaarde kritieke/hoge kwetsbaarheden in de geleverde closure, reproduceerbare dependency-resolutie, CI en ondersteunde platformchecks groen op dezelfde bronversie. Legacy Gradio blijft afzonderlijk issue #200.

### C. P1 — Open vragen herkennen (divergent, vervolgens toetsen)

- [ ] Vaste inputset bevriezen: volledige correcte antwoorden, onzekerheid, relevante andere invalshoeken, schijnbaar interessante onzin, herhalingen, adversarial voorbeelden en legitieme NONE-gevallen; meerdere domeinen en Nederlands/Engels.
- [ ] Detector v0.6 (hiaatgericht) en v0.7 (inquiry-first uit PR #202) onder dezelfde modelidentiteit, temperatuur, vraag, conceptantwoord, begrensde context en kandidaatbudget vergelijken. Behoud ruwe output, prompt-hash, parse-diagnostiek en provenance.
- [ ] Ten minste twee onafhankelijke, blind werkende beoordelaars laten coderen: specificiteit, contextbinding, onderzoekbaarheid, ongefundeerde feitclaim, geforceerde omissie, triviaal vraaggedrag, doublure en bruikbaarheid. Meningsverschil registreren, niet wegmiddelen zonder toelichting.
- [ ] Meer kandidaten mag **geen** succescriterium zijn. Vergelijk aantallen samen met kwaliteit, onterechte vraagproductie en passende abstentie.
- **Klaar wanneer:** een herhaalbare kwalitatieve vergelijking beschikbaar is; de uitkomst mag ook zijn dat v0.7 onvoldoende toevoegt. Zonder deze beoordeling PR #202 niet inhoudelijk 'bewezen' noemen.

### D. P1 — De levende schaduw over meerdere beurten

- [ ] Open vragen en mogelijke verbanden door detectie, normalisatie, opslag, verval, herhaling, tegenspraak, audit en surfacing volgen; vraagvorm en oorspronkelijke context behouden.
- [ ] Gewichtloos geheugen apart toetsen van steun voor een toetsbare deelclaim. Een vraag kan onderzoek uitlokken maar niet zelf door een bron 'waar worden'.
- [ ] Gate- en point-of-use-grenzen ongewijzigd doorlopen, inclusief geblokkeerde gevallen en kansen waarop geen surfacing plaatsvond.
- [ ] Het bestaande meerbeurtige onderzoekswerk en de eerdere nulresultaten benutten in plaats van een nieuwe wegwerp-harness te bouwen.
- **Klaar wanneer:** per kandidaat precies zichtbaar is wat er gebeurde en waarom deze niets, iets, of later misschien iets mocht beïnvloeden.

### E. P2 — Waarde van Shadowseed, niet alleen van output

- [ ] Alleen wanneer er echte, toegestane invloed plaatsvindt, blind vergelijken met same-model SSL-off onder de vastgelegde condities. Niet-aangeboden, geblokkeerde en vervallen seeds als gebeurtenissen meetellen.
- [ ] Mogelijke winst tegen gewone uitleg, extra prompten en waar passend gewone vraaggestuurde retrieval/RAG vergelijken. Nieuwheid en nut afzonderlijk beoordelen.
- [ ] Onderzoeken of een vraag daadwerkelijk nieuwe toetsbare richting opleverde en wat de kosten waren (ruis, onterechte nadruk, tijd, rekenwerk), niet alleen of een tekst 'beter klinkt'.
- **Klaar wanneer:** brontrouwe, controleerbare conclusies met beperkingen en negatieve uitkomsten, zonder claim dat CI, modeloutput of subjectieve indruk leer-/antwoordwinst bewijst.

## 5. Volgorde en beslismomenten

1. **Eerst betekenis herstellen:** spoor A en de beveiligings-/reproduceerbaarheidsbevindingen uit B. Geen nieuwe detectorlogica introduceren onder het etiket terminologie-opruiming.
2. **Dan detectie falsifieerbaar onderzoeken:** C, met v0.6 als nulmeting. Alleen bij inhoudelijk gedragen signalen v0.7 accepteren of aanpassen.
3. **Dan het geheugen laten werken:** D, waarbij NONE, verval, geen promotie en nul surfacing geldige uitkomsten blijven.
4. **Pas dan effect beoordelen:** E, met vooraf bepaalde vergelijkingsregels en menselijke toetsing.
5. **Releases apart:** de 0.12.3 Research Preview mag technisch worden gepubliceerd wanneer eigen release-eisen gehaald zijn; een inquiry-first kwaliteitsclaim loopt niet automatisch mee.

Voor elke merge: exact-SHA review, tests passend bij gewijzigde laag, check dat bronstatus, ondersteuningsstatus en publicatiestatus correct worden weergegeven. Bewaak drie claims apart: **werkt als software**, **biedt zinvolle onderzoekrichtingen**, **leidt tot aantoonbaar betere latere antwoorden**.

## 6. Artefacten en onderhoud

| Artefact | Plaats | Status |
| --- | --- | --- |
| Actueel werkplan en besliskaders | dit bestand | in uitvoering, versiegebonden |
| Status- en termkaart | [surfaces-and-terminology.md](../architecture/surfaces-and-terminology.md) | startpunt voor actuele terminologie |
| Bronmateriaal van de visie | [archief — generatieve visie](../../archive/source-docs/research/vision-generative-seeds.md) | bevroren herkomst, niet herschrijven |
| Technische/onderzoeksstatus | [status.md](status.md) | blijft de statusbron |
| Inquiry-first implementatie en testmateriaal | [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202) | concept; live modelbeoordeling ontbreekt |
| Release-informatie | [0.12.3](../workbench/release-0.12.3.md) | releasekandidaat, geen gepubliceerde tag |
| CI, kwetsbaarheden en modelgebruik | GitHub workflow-runs en [issue #200](https://github.com/E-AI-MODEL/shadowseed-pro/issues/200) | ieder afzonderlijk volgen |

**Bijwerken:** wijzig dit PVA bij een besluit of testuitkomst, met commit/PR, concrete bron en reden. Geen nieuwe totaalscores, afrondingsclaims of generieke taken zonder controleerbaar eindcriterium.
