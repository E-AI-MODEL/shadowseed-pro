# Eén echte seed weghalen: exacte T1-ablatie met GPT-5

> **Onderzoeksbesluit van 25 oktober 2026, vóór deze nieuwe modelrun.** Dit is een **post-hoc verkennende** proef: we hebben de T1-antwoorden van de eerdere studie al gezien, waaronder een mogelijke inhoudelijke echo in de oorspronkelijke Shadowseed-arm. Het is geen vooraf afgeschermde bevestigingsstudie en **G0 is NOT PASSED**. De formele onafhankelijke beoordeling van G0 loopt apart via [#234](https://github.com/E-AI-MODEL/shadowseed-pro/issues/234) en [#235](https://github.com/E-AI-MODEL/shadowseed-pro/issues/235).

## Waarom deze beperkte stap

De eerdere [14-call GPT-5 RF-proef](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224494313) liet een echt via de canonieke detector geboren seed `ss_001` op T0 en één correcte gewichtloze T1-checkpoint zien. De vijf T1-onderzoeksvragen gingen allemaal richting pieken en schakelmomenten. Alleen de D-uitvoer verwees in een onzekerheidsvoorbehoud naar mogelijke ruimtelijke verschillen tussen de sensormetingen.

In de bestaande proef verschilden arm D en de andere onderzoeksarmen ook in instructie en notitielengte. We weten uit [de offline promptreconstructie](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40231215980) dat de seed letterlijk uitsluitend D bereikte, maar de verschillen in vragen kunnen nog niet aan die seed worden toegeschreven.

De nieuwe toets verandert **precies één bestaand notitieveld in dezelfde afzonderlijke T1-onderzoeksprompt**. Hij verandert de gewone productantwoorden, detector, Gate, TrTL, TTL of status van de seed niet. Hij probeert geen nieuwe semantische kandidaat achteraf te selecteren.

## Vastgepinde bron en informatie

- Oorspronkelijke Action: [#40224494313](https://github.com/E-AI-MODEL/shadowseed-pro/actions/runs/40224494313), broncommit `7677f8e145c4766ff3fea5451c95acea21edaacb`.
- De **complete oorspronkelijke ruwe `observed.json`** wordt exact gecontroleerd op SHA-256 `62f778fb53547f2c0532795ccb31f02f09381500a2eb67b7598bf86ae597820f`. Een uit het geheugen nagebouwde of gewijzigde dataset is uitgesloten.
- Het oorspronkelijke publiek beschreven casusbestand heeft inhoudshash `e72bc6a6846d2cbe12af672a0d12365ea571ad10091ab1ec3f4746ad87d38bee`.
- De eerste echte geaccepteerde seed werd op T0 geboren en was op T1 via canonieke broncheckpoints terug te vinden. **Geen T2-prompt** wordt voor deze nieuwe proef gebruikt. T2 is immers eerder mislukt en is ook onderzoeksmatig een andere vraag.
- Alle armen zien dezelfde T0- en T1-context, dezelfde externe T1-waarneming en dezelfde oorspronkelijke gewone hostantwoorden. De normale host wordt niet opnieuw aangeroepen. De onderzoekstaak blijft onveranderd en gebruikt exact de bestaande `INQUIRY_INSTRUCTIONS` van de research-runner.

## Vier omstandigheden, vier pogingen elk

| Arm | Exacte inhoud in het bestaande onbewezen-notitieveld | Wat dit contrast vraagt |
| --- | --- | --- |
| **D** | Exacte, werkelijk op T0 geboren gewichtloze seed, 185 tekens | Originele blootstelling |
| **X** | `NONE` | Wat verandert wanneer alleen die kandidaattekst ontbreekt? |
| **P** | Een vooraf vastgelegde **administratieve tekst van exact 185 tekens** zonder sensorinhoud | Wat verandert door een even lang extra tekstveld zonder de relevante hypothese? |
| **N** | De werkelijk op T0 door GPT-5 gemaakte gewone gespreksnotitie (niet door de onderzoeker achteraf herschreven) | Hoe verhoudt de seed zich tot gewoon zichtbare notities? |

Het verwijderen van inhoud maakt D en X niet token-gelijk; P is in **tekens**, niet noodzakelijk in tokens, gelijk aan D. N is langer en bevat bredere context. We registreren werkelijke tokentellingen per modelaanroep. De placebo zelf is een additionele tekst en dus geen perfecte inhoudsgelijke controle. **Geen van deze verschillen wordt verborgen.**

Elke arm krijgt **vier afzonderlijke stateless GPT-5-responses**, met exact dezelfde prompt per arm (geen vorige experimentele antwoorden of cross-arm geschiedenis). De volgorde is vooraf bepaald in het fixture en per ronde verschoven zodat iedere arm één keer op iedere oproeppositie voorkomt:

| Ronde | Oproepvolgorde |
| --- | --- |
| 0 | D → X → P → N |
| 1 | X → N → D → P |
| 2 | P → D → N → X |
| 3 | N → P → X → D |

Dit zijn **16 modelaanroepen, geen 16 onafhankelijke wetenschappelijke casussen**. Het is één scenario, één specifieke seed en één contextmoment. Er is geen fixeerbare identieke GPT-5-samplingseed, geen claim over model-interne activaties en geen experimentele RI-interventie in de buitenwereld.

De broncode weigert afwijkingen in SHA, casus, seedidentiteit, nul-autoriteitsstatus, vraagcontract, callbudget, oproepvolgorde, latere informatie en G0-claim. Geen stilzwijgende selectie van gunstige runs, niet-geldige modeloutput wordt afzonderlijk gerapporteerd.

## Wat wordt gemeten, en wie beoordeelt wat?

De **technische waarneming** bestaat uit bronherkomst, exact gelogde vraagprompt, conditieblootstelling, antwoordtekst, modelstatus, API-responsidentificatie, verbruikte tokens en parsebare modelvraag. Bij een `NONE`, ongeldig JSON of `incomplete` wordt niet achteraf gerepareerd en niet gezegd dat het systeem geen mogelijkheden had.

Een apart geblindeerd pakket bevat de echte modelteksten onder willekeurige labels, met lege velden voor **twee onafhankelijke menselijke beoordelingen**. Die beoordelen eerst afzonderlijk of:
- de specifieke ruimtelijke hypothese ergens als onzekere mogelijkheid bewaard blijft;
- de nieuwe onderzoeksvraag een andere toetsstrategie voorstelt dan het bestaande schakel/timingprobleem;
- de voorgestelde test onafhankelijk uitvoerbaar of duidelijk af te bakenen is.

Pas daarna wordt de afzonderlijk bewaarde eigenaarssleutel met de conditieletters gebruikt. Het originele resultaat blijft staan, inclusief negatieve gevallen. Onderzoekers met GitHub-toegang kunnen in principe de eigenaarssleutel zien: daarom is blindering hier **organisatorisch**, niet cryptografisch gegarandeerd. Onafhankelijkheid moet daadwerkelijk geregeld worden.

**Geen automatische semantische scores of effectclaim.** Zelfs een zichtbare hogere frequentie van ruimtelijke hypothesebehoud in D bewijst nog geen algemene werking, geen interne Q1-toestand en geen nieuwe uitvoerbare Q2-onderzoekstap. De eerste wetenschappelijk passende uitkomst zou hoogstens een *verkennende aanwijzing voor een tekstspecifiek gedragsverschil in één bevroren context* zijn.

## Stopgrenzen en uitkomstlabels

- Model: `gpt-5` via de bestaande begrensde research-provider, reasoning effort `low`, response `store:false`, geen verborgen retries.
- Hard maximaal **16 modelcalls**, **1 embeddingcall** toegestaan (0 voorzien), **110.000 gerapporteerde tokens**, maximaal **4096 outputtokens per call**. Boven die grenzen wordt afgebroken. Dit is niet hetzelfde als een vaste eurokostengrens.
- Alleen een handmatige, vooraf geconditioneerde eenmalige GitHub-run in de bestaande `OpenAI key`-omgeving, ná groen van de no-network researchtests. Geen secret in de repo of modelartifact; GitHub-artifact bewaart ruwe antwoorden en een apart beoordelings- en eigenaarspakket.
- Bij mislukking wordt de volledige tot dan toe gemeten uitvoer als **incomplete** bewaard. Er volgt geen automatische tweede betaalde poging.
- G0 blijft `NOT PASSED`; de oorspronkelijke T2-`ValueError` blijft afzonderlijk open en mag niet als opgelost worden geclaimd.

Deze proef sluit aan op [het kandidaat-specifieke meetplan op `main`](https://github.com/E-AI-MODEL/shadowseed-pro/blob/main/docs/research/possibility-space/g0/seed-influence-causal-measurement-2026-10-25.md). Hij is een experimentele vervolgstap, geen afzwakking van de oorspronkelijke Q1/Q2-these.
