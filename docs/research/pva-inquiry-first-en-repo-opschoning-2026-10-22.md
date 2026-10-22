# Plan van aanpak — Shadowseed: van historisch ontwerp naar toetsbare werking

**Datum:** 22 oktober 2026  
**Status:** voorstel ter beoordeling, geen acceptatie of releasebesluit  
**Basis:** `main` op `f3ec86c124ab88247e0739a6cbe3c817a6508219`; PR #202 op eigen branch  
**Scope:** inhoudelijk onderzoek én verplichte opschoning van actuele repo-ruis

## 1. Waarom dit plan nodig is

Shadowseed is niet primair een detector van fouten of ontbrekende onderdelen.
Het oorspronkelijke idee is dat een gesprek ruimte kan laten voor een
**nog onbesliste mogelijkheid**: nieuwsgierigheid, onzekerheid, twijfel,
verwondering, een andere relatie of een vraag die niemand stelde. Ook een goed
en volledig antwoord kan zo'n mogelijkheid oproepen. Het taalmodel wordt
daarmee geen voelend of zelfstandig nieuwsgierig wezen. SSL bewaart een
*onderzoekbare kandidaat*, zonder hem meteen tot feit, advies, opdracht of
gezaghebbende toevoeging te verheffen.

Technische groenmeldingen bewijzen dat het geheugen- en autoriteitscontract
werkt zoals getest, niet dat een kandidaat interessant is of latere antwoorden
daadwerkelijk verbetert. Het Plan van Aanpak scheidt die twee vragen.

## 2. Herkomst en bindende grenzen

| Bron / periode | Wat we hieraan ontlenen | Wat we er niet uit mogen concluderen |
| --- | --- | --- |
| SSL 4.5/4.6: `archive/source-docs/00_shadow_seed_learning_4_6.md` en `archive/legacy/docs/00_shadow_seed_learning_4_5.md` | Trace versus weight; de schaduw als plaats voor mogelijkheden, plus de oorspronkelijke theoretische inspiratie | De historische implementatie is niet automatisch de actuele runtime of bewezen mensachtige nieuwsgierigheid |
| 14 juni 2026: `archive/source-docs/research/vision-generative-seeds.md` | **'Wat had hier kunnen staan?'** gaat voorbij de omissiechecklist. Generatieve, nog niet genomen wegen horen bij het doelbeeld. | De historische tekst noemt 'moet staan' en suggereert soms dat gewicht waarheid/waarde vaststelt. Dat is geen huidige Gate-definitie of bewezen effect |
| 18 augustus: `docs/plans/ssl-doctrine-alignment-2026-08.md` en ADR-001 t/m ADR-004 | Een seed moet atomair, contextgebonden en onderzoekbaar zijn; onbetrouwbare observatie, herhaling, onafhankelijke bron en gezag blijven gescheiden | Een nieuwe detectorprompt mag de evidence/identity/contamination-policy niet versoepelen |
| ADR-005 t/m ADR-010, actuele runtime en testen | Chat-first product; lokale, observeerbare processen; rolrouting, onafhankelijk SSL-enginecontract en beleidsgrenzen | Werkende UI of een succesvolle fixture is geen echte modelgebruikstest |
| `docs/research/status.md` en bestaande onderzoeksresultaten | Beschikbare mechanismen, evidence-efficacy-opzet, kandidaat- en opportunity-audit, bekende nulresultaten | Geen universele kwaliteits-, effectiviteits- of veiligheidsclaim |
| PR #199 en #201; `docs/architecture/adr-0.12.3-web-only-distribution.md` | Lokale webdistributie los van oude Gradio-bundel; security audit van de *geleverde closure*, niet alle optionele extra's | De Gradio-route is niet daarmee veilig geworden; een kandidaatbuild is geen gepubliceerde versie |
| Concept-PR #202, `benchmarks/inquiry_first/cases.json` | Inquiry-first v0.7, geteste intake/presentatie en een eerste tweetalige vergelijkingsset | Nog geen geblindeerd bewijs dat de detector betere open vragen oplevert |

**Bij conflict:** geaccepteerde actuele ADR's, canonieke runtime en tests,
actuele evidence-status en productcontract gaan boven verouderde uitvoeringsplannen.
Historische originelen blijven intact. Een historische *visie* is waardevolle
provenance, geen runtime-autoriteit; behandel botsingen als onderzoeksvraag.

## 3. Centrale onderzoeksvraag

**Kan SSL contextgebonden nieuwsgierigheid, twijfel, onzekerheid en alternatieve
mogelijkheden bewaren en laten ontwikkelen zonder ze voortijdig tot waarheid of
sturende autoriteit te maken, en is er bij geautoriseerd later gebruik aantoonbaar
inhoudelijke meerwaarde ten opzichte van dezelfde modelroute zonder SSL?**

Dit zijn drie verschillende vragen, met eigen bewijs:
1. **Kandidaat:** komt er een specifieke, relevante, niet-assertieve
   onderzoekrichting uit, ook na een volledig antwoord, en is `NONE` passend?
2. **Geheugen:** blijft de betekenis van de kandidaat intact bij opslag,
   herhaling, tegenspraak, verval en terughalen, zonder vals bewijs of gezag?
3. **Invloed:** wat gebeurt er *alleen als* een seed onder de geldende Gate
   en actuele point-of-use-voorwaarden mag worden aangeboden?

## 4. Verplicht werkspoor A: repo-ruis opruimen

Ruis is hier een toetsbaar conflict tussen woorden, status en werkelijk gedrag,
niet simpelweg een groot aantal bestanden.

| Term / situatie | Vast gebruik vanaf nu | Concrete actie |
| --- | --- | --- |
| 'legacy' | **Historisch archief**: onveranderde bronnen in `archive/`; **optionele Gradio-interface**: nog uitvoerbaar maar niet de standaarddownload; **compatibiliteitsfacade**: ondersteunde importdoorverwijzing; **historisch detectorcontract**: voor replay/vergelijking | Zet bij elke actieve vermelding de bedoelde categorie en status; gebruik 'legacy' niet als verzamelbak |
| 'Workbench' | **Product**: lokale browserapp (`shadowseed-web`); **Gradio Workbench**: de afzonderlijke optionele Gradio-interface; **Workbench-tests**: alleen benoemen wat die tests echt raken | Verduidelijk README, Workbench-README, CLI/installerteksten en statuspagina; behoud CLI-namen voor compatibiliteit |
| 'candidate', 'gap', 'missing' | **Seed** is een bounded inquiry; een omissie is één mogelijke herkomst, geen verplichte eigenschap | Vergelijk actuele productteksten, detectorprompt, seed-contract, tests en UI; vervang geen letterlijk historisch meetlabel |
| 'research-ready' / 'production-ready/local' / 'released' | Verskillende afzonderlijke statussen: mechanisme testbaar, release op exact SHA, lokale acceptatie en wetenschappelijke effectiviteit | Corrigeer claims alleen met controleerbaar release-/assurancebewijs; geen groene CI als effectclaim |
| Bron- en documentdubbels | Eén actuele startpagina per domein; bewaarde originelen met tijd/autoriteit; links naar actuele canon | Maak een verifieerbare inventaris; archiveer/annoteer verouderde actieve documenten, maar vernietig geen bron of onderzoeksresultaat |
| npm/Next.js/beveiliging | Afhankelijkheid van product-frontend, niet een SSL-inhoudelijk probleem | Onderzoek actuele npm-audit, reproduceerbare lock en op welke gebundelde componenten advisories van toepassing zijn; repareer zonder ignore-vlag |

**Acceptatie spoor A:** een auditbestand met per bevinding: vindplaats,
oude claim/term, bewijs, categorie, impact, aanpassing/verwijdering en
verificatie. Pas daadwerkelijk aan waar de repo fout of dubbelzinnig is.
Archiveer bronmateriaal; wis nooit onderzoeksprovenance, ADR's of nog gebruikte
API's uitsluitend om de map kleiner te maken.

## 5. Werkspoor B: inquiry-first detector evalueren

Vergelijk de oude v0.6-prompt en de nieuwe v0.7-prompt van PR #202 met hetzelfde
model-ID, decodering, context, maximaal aantal kandidaten en dezelfde
gespreksgeschiedenis. De twaalf bestaande NL/EN-cases zijn **startmateriaal**,
geen representatieve steekproef of scoringsresultaat.

Aanvullen met: volledige juiste antwoorden, twijfel op basis van onderbepaalde
data, nieuw verband, vraag al eerder beantwoord, dunne input (`NONE`),
verleidelijke verzonnen bron, promptinjectie, herhaalde kandidaten en
verschillende vak-/taaldomeinen.

Leg per uitvoering vast: model- en serverversie, promptversie en -hash,
input en clean context, output vóór parsing, parserdiagnostiek, voorgestelde
seeds, weigeringen, tijd en beoordelingsidentiteit.

**Geblindeerde beoordeling:** twee onafhankelijke beoordelaars labelen
relevantie, specificiteit, daadwerkelijke openheid, feitelijke onderbouwing,
onnodige 'er ontbreekt iets'-claim, generieke vraag, hallucinerende details en
passend `NONE`. Meningsverschillen apart rapporteren. Meer kandidaten telt
niet als vooruitgang. Rapportage onderscheidt opbrengst én ruis.

**Stopconditie:** als v0.7 vooral generieke of ongefundeerde vragen oplevert,
geen stille standaardpromotie; herontwerp de detector op basis van de gevallen.

## 6. Werkspoor C: geheugentraject en eventuele invloed

Gebruik meerbeurtentrajecten met een echte, gecontroleerde modelrun en een
zonder-model fixturecontrole. Test vraagtekens, exacte betekenis, herkomst,
verdwijnen/terugkeren, tegenspraak, semantische overeenkomst en het
`evidence_backed`-beleid. Herhaling is géén onafhankelijk bewijs.

Een onderzoeksvraag is op zichzelf niet een bewezen propositie. Verifieerbare
externe steun kan een *begrensde, eraan gekoppelde claim* ondersteunen, niet
de vraag als zodanig 'bewijzen'. Leg bloot wanneer de huidige Gate-datahierarchie
dit onderscheid nog niet goed kan uitdrukken; geen automatische
semantische normalisatie naar een waarheidsclaim.

Alleen bij daadwerkelijk geautoriseerde en gesurfacte seeds wordt een
gebalanceerde SSL-on/off antwoordvergelijking beoordeeld. Geen
opportunity/auditverlies bij afwijzing, geen effect claimen op basis van
tekstverschil en geen versoepeling van de Gate om A/B-data af te dwingen.

## 7. Uitvoeringsvolgorde en beslismomenten

| Fase | Uitvoering | Gereed als |
| --- | --- | --- |
| **0. Historisch/terminologisch referentiekader** | Historische 4.5/4.6-ontwerpen, generatieve visie, ADR's en actuele runtime naast elkaar; term- en statusinventaris | Traceerbare verschillenlijst met besluit: herstellen, conserveren of onderzoeken |
| **1. Verplichte repo-opruiming** | Feitelijke tegenstrijdigheden, verouderde actieve verwijzingen en release-/legacy-terminologie aanpassen; browser-/legacy-grenzen en npm-afhankelijkheden checken | Diff + inventaris + volledige relevante CI; geen blind verwijderen |
| **2. Detectoronderzoek** | v0.6/v0.7 NL/EN-uitvoeringen, blind review, ruis- en `NONE`-analyse | Onderbouwd behouden/bijstellen/afwijzen van v0.7; geen kwaliteitsclaim zonder resultaat |
| **3. Geheugenonderzoek** | Meerbeurtenrun, onafhankelijke bronidentiteit, lifecycle en zero-weight audit | Herleidbare seedgeschiedenis zonder automatische autoriteit |
| **4. Invloed en verslag** | Geautoriseerde point-of-use-gebeurtenissen en geblindeerde SSL-on/off-comparaties | Volledig opportunity-denominator en eerlijk verslag incl. nullen en beperkingen |

**Twee onafhankelijke poorten:** distributie/release-assurance versus
inquiry-first onderzoek. Werkspoor B hoeft een goedgekeurde 0.12.3
distributie niet inhoudelijk te blokkeren, maar mag niet als bewezen
productverbetering worden meegenomen zolang de vergelijking ontbreekt.

## 8. Concrete deliverables

- `docs/research/pva-inquiry-first-en-repo-opschoning-2026-10-22.md`
  (dit versiegebonden uitvoeringsplan).
- `docs/research/terminologie-en-ruis-audit-2026-10-22.md`:
  bevindingen, bronprioriteit, handeling en resterende risico's.
- Nieuwe commits/PR met uitsluitend verifieerbare reparaties van actieve
  tekst, configuratie of code; geen wijziging aan historisch archief.
- Versiegebonden dataset plus uitvoerlog voor detectorvergelijking; blinde
  beoordelingsformulieren; evidence- en opportunity-audit.
- Beslisnotitie over kandidaatkwaliteit, behoud van de geheugenbetekenis,
  autoriteitsgrenzen en waar SSL wel/niet aantoonbaar verschil maakt.

## 9. Verboden shortcuts

Geen omzetting van `gap` naar `curiosity` in oude experimentlabels of bestanden;
geen 'legacy' gelijkstellen aan 'onveilig' of 'ongebruikt'; geen verwijdering
van compatibiliteitsfacades zonder aanroep- en testonderzoek; geen
security-audit-bypass; geen vertraagde release maskeren als 'gepubliceerd';
geen nieuwe Gate-regels afleiden uit een visiequote; geen conclusie over
werkzaamheid uit alleen CI, prompts of fixtureantwoorden.

**Startbesluit:** dit plan staat ter beoordeling. De document- en
terminologiecorrecties kunnen alvast als aparte PR worden gereviewd. Echte
modelresultaten en onafhankelijke review blijven expliciete vervolgstappen.
