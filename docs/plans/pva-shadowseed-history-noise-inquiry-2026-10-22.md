# Plan van aanpak: Shadowseed-doelstelling, historische samenhang en repo-ruis

**Datum:** 22 oktober 2026  
**Status:** werkplan; geen claim van bewezen modelkwaliteit, releasegoedkeuring of gewijzigd SSL-gezag  
**Werkbasis:** `main` op `f3ec86c124ab88247e0739a6cbe3c817a6508219`; de inquiry-first wijzigingen staan afzonderlijk in [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202).  
**Eerstvolgende uitkomst:** opgeschoonde actuele documentatie + getraceerde beslis- en evaluatieroute. Niet: het automatisch samenvoegen van #202.

## 1. Opdracht en uitgangspunt

We bouwen niet in de eerste plaats een *missing-gap detector*. Shadow Seed
Learning (SSL) moet ruimte kunnen geven aan een specifieke, onderzoekbare
**nieuwsgierigheid, twijfel, onzekerheid, onverwachte verbinding of mogelijke
andere richting**. Ook een voldoende en juist antwoord kan een nieuwe vraag
oproepen. Een taalmodel hoeft die vraag niet direct te beantwoorden.

Een seed registreert **een mogelijke onderzoekrichting**, niet de waarheid ervan.
Het systeem heeft geen menselijke gevoelens van nieuwsgierigheid of twijfel.
`trace > 0` betekent dat een kandidaat kan worden onthouden;
`weight = 0` betekent dat die geen bevoegdheid heeft het antwoord te sturen.
Een mogelijke vraag krijgt niet door herhaling, interessantheid of een
krachtiger detectormodel automatisch de status van extern geverifieerde
informatie. De actuele Gate, tegenspraakregels en point-of-use-controle
blijven leidend.

**Twee gescheiden vragen:**

1. *Werking:* herkennen, onthouden, ontwikkelen en afvoeren van betekenisvolle
   open vragen zonder er kennis van te maken.
2. *Effect:* indien specifieke informatie daadwerkelijk volgens de geldende
   policy bevoegd en relevant wordt, verbetert het gebruik ervan een
   vervolgantwoord of onderzoekhandeling? Dit moet afzonderlijk worden gemeten.

Vaker of meer seeds produceren is **geen** succescriterium.

## 2. Geschiedenis eerst: wat de bronnen echt zeggen

Deze samenvatting bevat bronstatus en tegenspraak, geen nieuwe meting.

| Periode / bron | Wat werd vastgelegd | Wat we nú wel en niet mogen afleiden |
| --- | --- | --- |
| SSL 4.5 en 4.6, [historische 4.6-brontekst](../../archive/source-docs/00_shadow_seed_learning_4_6.md) | Atomaire, gewichtloze seeds, TTL/TrTL en Gate; 4.6 formuleert expliciet **één ontbrekende schakel/gap** per seed. | De mechanische geschiedenis blijft bewaard. De tekst noemt zichzelf destijds 'canoniek', maar ligt nu onder `archive/` en **heeft geen huidige architectuurautoriteit**. |
| 14 juni 2026, [generatieve visie](../../archive/source-docs/research/vision-generative-seeds.md) | Scherpt het doel aan van *wat had moeten staan* naar *wat had kunnen staan*: mogelijke invalshoeken en vragen die nog niet zijn gesteld. | Richtinggevend maar **geen** bewezen superioriteit ten opzichte van een model of RAG. Uitspraken als 'gewichtloos kost niets' en 'wordt noodzaak' zijn visietaal, geen veilige runtimeclaim. |
| Juni 2026, [historisch PVA/rounds](../../archive/source-docs/research/pva-checklist.md) | Detectie-payoff bleek geregeld redundant; echte cross-turn-lus en beoordelingskwaliteit kregen voorrang. R019 gaf een beperkt signaal met soepelere drempels, met bekende confounders. | Positieve en negatieve uitkomsten, kansen op echte invloed en gewijzigde condities moeten samen worden geteld. Niet alleen de gunstige rounds overnemen. |
| 13 juli 2026, [integrale evaluatie](../../archive/source-docs/research/ssl-integrale-evaluatie.md) | Verdeelt mechaniek, open-set kwaliteit, adversarial risico, payoff, transfer en modelinterne onderzoekslijnen over afzonderlijke bewijsniveaus A–G. | **Geen totaalscore** en geen bewijs dat elke onderzoeklijn al werkt. Oud verslag heeft in het archief historische status. |
| 18 augustus 2026, [ADR-002](../architecture/adr/ADR-002-epistemic-seed-contract.md) en [doctrine-alignment](ssl-doctrine-alignment-2026-08.md) | Een seed kan **gap, doubt, what-if of alternatief** zijn. Betekenis, bewijs, recurrence, Gate en gebruik zijn aparte grenzen. Historische 18-woordenregel is geen doctrine. | Dit is de geldende inhoudelijke minimumnorm, samen met ADR-001/003/004/005. Oude onderzoeksclaims mogen haar niet overrulen. |
| 1 oktober 2026, [ADR-008](../architecture/adr/ADR-008-workbench-ui-reset.md) | Chat eerst, één sessie, zichtbaar onderscheid tussen onthouden, bevoegdheid en daadwerkelijk aangeboden context; geen sliders die mechanismen vermengen. | Producttaal moet corresponderen met feitelijk inspecteerbare runtimevelden, niet alleen prettig klinken. |
| 21–22 oktober 2026, [PR #202](https://github.com/E-AI-MODEL/shadowseed-pro/pull/202) | Inquiry-first v0.7-prompts, intake, UI en regressietests; 12 tweetalige cases voor het **ontwerp** van een vergelijking. | PR is **draft**. Groene CI bewijst implementatieconsistentie, geen kwaliteit van gegenereerde onderzoekvragen. |
| 22 oktober 2026, [PR #201](https://github.com/E-AI-MODEL/shadowseed-pro/pull/201) | Startup + geaudite web-only distributie samengevoegd op `main`. | Dit is de actuele distributierichting. Gradio/Pillow zijn niet daarmee gerepareerd; de Gradio-variant blijft opt-in en apart te beoordelen via [#200](https://github.com/E-AI-MODEL/shadowseed-pro/issues/200). |

**Beslissende correctie:** de oude hoofdclaim (*wat ontbreekt?*) is een
toegestane **deelcategorie** van de huidige, bredere vraag (*wat verdient
het om nog open te blijven?*). We schrijven vroegere versies niet om alsof
de bredere formulering toen al overal gold.

## 3. Verplichte P0: repository-ruis zichtbaar verminderen

Begin met de echte productroute, niet met een ongerichte zoek-en-vervangactie.

| Onderdeel | Vastgestelde ruis | Actie en controle |
| --- | --- | --- |
| `README.md`, `docs/workbench/README.md` | 'Workbench' verwijst zowel naar de huidige lokale webapp als naar Gradio. Source-quickstart installeert onnodig Gradio. | Maak **Lokale webapp** de primaire naam, **Gradio Workbench (optioneel, niet in web-release)** de specifieke naam; wijs op de juiste install-/buildroutes. |
| `docs/architecture/repository-structure.md` | Beschrijft het gewone product nog vanuit `src/shadowseed/workbench/` en noemt de web-API/app niet helder. | Voeg webclient + loopback-service toe en corrigeer de rolbeschrijving. |
| `docs/architecture/adr-0.12.3-web-only-distribution.md` | Er staat nog 'prototype this', 'later change release workflow', en 'merge into #199' na de merge van #201. | Markeer het besluit als **geïmplementeerd op main**, maar publicatie, lokale Ollama-test en production-ready/local als open. Bewaar de oorspronkelijke alternatieven en datering. |
| Compatibiliteit en archief | Eén woord 'legacy' suggereert soms 'dood', soms 'onveilig', soms 'alleen voor herhaalbaarheid'. | Gebruik het [begrippen- en statusoverzicht](../architecture/current-surfaces-and-terminology.md). Verwijder geen functionerende facades of bevroren bewijsstukken. |
| Detector en onderzoek | Historische absence-prompts, huidig v0.6 gedrag, generatieve v0.7 in #202 en onderzoeksresultaten kunnen door elkaar raken. | Label **actueel op main**, **concept in PR**, **historisch voor replay** of **afzonderlijke onderzoekslijn**. Vervang geen oude tests/resultaten stilzwijgend. |
| Frontend/afhankelijkheden | Op `main` staat Next `16.1.1`; `apps/web/package-lock.json` ontbreekt en npm-audit signaleerde meldingen. | Apart technisch herstel: advisories controleren, geverifieerde update, lockfile, `npm ci`, build + audit; niet de audit uitschakelen. |
| Communicatie van kwaliteitsclaims | 'CI groen', 'freeze-build', 'onderzoeksklaar', 'publiceerbaar' en 'effectief' worden gemakkelijk als synoniemen gelezen. | Benoem per claim **broncommit, testbereik, niet-aangetoonde schakel en resterende beslisgate**. |

**Definition of done P0:** de primaire README, documentatie-ingangen,
repo-structuur, productuitleg, CLI-instructies en release-status spreken
elkaar niet tegen over primaire UI, naamgeving, afhankelijkheden en status.
Een verklarend document zonder deze concrete wijzigingen is **onvoldoende**.

## 4. Onderzoekslijnen na de opschoning

### A. Detector: divergent vragen kunnen bewaren (PR #202)

- Baseline v0.6 en kandidaat v0.7 op **exact dezelfde** volledige
  antwoorden, onvolledige antwoorden, twijfelgevallen, nieuwe verbanden,
  herhaalde vragen, misleidende inputs en terechte `NONE`-gevallen.
- De bestaande 12 cases zijn **pilotcases**, geen wetenschappelijk bewijs.
  Maak vóór de beslissende meting een gebalanceerde, vastgezette en
  gecontroleerde set (richtgetal minimaal 50 verschillende gesprekken/cases,
  Nederlands en Engels); reserveer een ongeziene holdout.
- Log model-ID/digest, prompts + versies, decoding, embeddinginstellingen,
  zichtbare voorgeschiedenis, bron-SHA, ruwe output, parsing, `NONE` en kosten.
- Laat minstens twee onafhankelijke beoordelaars *blind* scoren op
  specificiteit, verankering in de input, onderzoektbaarheid, relevantie,
  vermijdbare omissieclaim, ongefundeerd feit, ruis en nuttige abstentie.
  Rapporteer verdeeldheid tussen beoordelaars.
- **Stopcriterium:** meer seeds maar meer verzinsels/algemene vragen is
  geen vooruitgang; houd v0.6 als controlegroep en bespreek negatieve resultaten.

### B. Levensloop: gewichtloos onthouden zonder betekenisverlies

- Volg open vragen door detector, parser, normalisatie, identiteit,
  persistente opslag, herlezing, TTL/TrTL, dedup, tegenspraak en expiry.
- Controleer dat `?` niet verandert in een feitelijke bewering; geen
  ongevraagde verplichting voor de gebruiker om de vraag te beantwoorden.
- Herhaling, contaminatie en modeluitvoer worden niet als externe
  verificatie verkocht. Vergelijk dezelfde vraag over verschillende beurten.
- Meet **hoe vaak** een zinvolle vraag behouden, vervormd, ten onrechte
  gededupliceerd of vergeten wordt. Toon voorbeelden en audittrails.

### C. Bevoegdheid en gebruik: niet forceren om een effect te tonen

- Onder de normale `evidence_backed` policy blijft nieuwe autoriteit
  nul zolang onafhankelijke onderbouwing ontbreekt.
- Een **vraag** is niet op zichzelf 'waar'. De Gate kan hoogstens
  afgebakende toetsbare claims/ondersteuning valideren en het
  eventuele gebruik ervan onder huidige policy toestaan.
- Gebruik uitsluitend **daadwerkelijk geautoriseerde en aangeboden**
  seeds voor de eventuele antwoordkwaliteitvergelijking.
- Vergelijk identieke modelinstellingen met SSL aan/uit, tel expliciet
  no-opportunity, geblokkeerde Gate, niet-relevante en niet-gebruikte gevallen.
- Laat uitkomsten geblindeerd beoordelen; een tekstverschil is niet
  automatisch verbetering. Leg ook verslechtering en ruis vast.

### D. Product- en distributiecontrole (aparte vrijgavebeslissing)

- Blijf bij de web-only loopback-route; Gradio geen verplichte download.
- Voer web- en Python-tests, audits van daadwerkelijk geleverde afhankelijkheden,
  frozen HTTP/chat-tests en builds op drie platformen uit op **dezelfde commit**.
- Controleer npm-advisories/Next-update en vergrendelde npm-afhankelijkheden
  vóór een downloadclaim; geen audit-onderdrukking.
- Voor lokaal gebruik: afzonderlijke, handmatige test met echte
  Ollama + EmbeddingGemma, herstart/persistentie en `shadowseed doctor`.
- Publicatie van v0.12.3, productiegeschiktheid en het
  wetenschappelijke oordeel over inquiry-first blijven **drie besluiten**.

## 5. Werkvolgorde en beslispoorten

| Stap | Klaar wanneer | Vervolg |
| --- | --- | --- |
| **P0a Historische trace** | Bronnen hierboven gecontroleerd, huidige versus historische autoriteit gedocumenteerd, alle inhoudelijke spanningen vermeld | Geen stilzwijgende herschrijving van archief/paper |
| **P0b Ruis daadwerkelijk herstellen** | Terminologiematrix, primaire ingangen, architectuur en release-ADR in één reviewbare wijziging; link-/claimcontrole | PR review + CI; niet zelf publicatie afleiden |
| **P1 Frontend security** | Advisories geanalyseerd, ondersteunde Next-update, gelockte npm-installatie, audit plus web/frozen tests op exact SHA | Alleen vrijgeven bij groene echte artefactcontrole |
| **P2 Inquiry-pilot** | Identieke gepinde v0.6/v0.7-runs, ruwe antwoorden, beoordelingsprotocol en eerste onafhankelijke scores | Besluit of groter onderzoek gerechtvaardigd is |
| **P3 Levensloop/overdracht** | Vraag blijft onderzoekbaar en gewichtloos, redactionele betekenis intact, no-opportunity inzichtelijk | Geen wijzigingen in Gate als workaround |
| **P4 Effectonderzoek** | Alleen geautoriseerde invloed, geblindeerde vergelijking, negatieve en lege resultaten meegenomen | Gefundeerde conclusie met beperkingen |
| **P5 Eindcontrole** | Gewijzigde documenten, code, tests, claims, modellen en evidence aan één SHA herleidbaar | PR #202 al dan niet samenvoegen na review |

## 6. Niet doen

- Geen snelle herbenaming van iedere `gap` tot `curiosity`: oudere
  benchmarknames, schema's, API's en modelprompts zijn meetprovenance.
- Geen historische `archive/`, benchmarkuitkomsten of manuscripten verwijderen
  om de repo cosmetisch rustig te maken.
- Geen `legacy`-compatibiliteit schrappen zonder migratie/consumententest
  conform `compatibility-policy.md`.
- Geen verklaringen over modelinterne nieuwsgierigheid, eigen wil,
  gegarandeerde waarheid of ongezien kwaliteitsvoordeel.
- Geen Gradio/Pillow- of npm-beveiligingscontrole uitschakelen voor groene CI.
- Geen historische proef met ruimere Gate-instellingen als bewijs voor de
  huidige `evidence_backed` productpolicy presenteren.

## 7. Vast te leggen resultaten

1. Een beoordeelde terminologie- en bronnenmatrix plus concrete opschoning
   in de actieve repo-ingangen (deze PR).
2. Een issue/PR-overzicht met wijzigingen naar **behouden, verduidelijken,
   herstellen, uitstellen of historisch laten**; geen ongedekte delete.
3. Een vooraf vastgelegd v0.6-v0.7-onderzoekspakket met ruwe modeluitvoer,
   onafhankelijke beoordelingsgegevens en voldoende negatieve controls.
4. Een afzonderlijke, auditbare levensloop- en effectrapportage.
5. Een release-dossier waarin softwareveiligheid, lokale praktijktest en
   onderzoeksclaims gescheiden conclusies krijgen.

De PVA-status verandert pas naar **uitgevoerd** nadat de bijbehorende
GitHub-PR's en onderzoeksartefacten bestaan én de noodzakelijke reviews
hebben plaatsgevonden. Dit document zelf is geen implementatiebewijs.
