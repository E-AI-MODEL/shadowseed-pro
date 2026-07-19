# SWOT Naar Werkcategorieen

> Status: current
> Date: 2026-05-22
> Evidence layer: SWOT-to-categories map
> Current source: yes


Status: active
Date: 2026-05-13
Role: planning and backlog-scoping document
Related issue: #37

## Doel

Dit document vertaalt de bestaande SWOT-achtige observaties over `shadowseed` naar concrete werkcategorieen.

Het doel is niet om nog een abstracte analyse boven op de roadmap te zetten. Het doel is om sneller te kunnen beslissen welk soort repo-werk een voorstel eigenlijk is:

- iets dat we moeten behouden;
- iets dat we moeten verminderen;
- iets dat we gericht moeten benutten;
- iets dat we actief binnen grenzen moeten houden.

Deze indeling helpt om PR's, issues en documentatie dichter bij de bestaande SSL-route te houden.

## Hoofdregel

Niet elk probleem vraagt om nieuwe code.

Soms is de beste verbetering:

- minder dubbele workflowlogica;
- minder concurrerende documentbronnen;
- explicietere artifact- en claimgrenzen;
- smallere, scherpere evaluatielagen.

## Werkcategorieen

| SWOT-hoek | Werkcategorie | Centrale vraag | Typisch repo-werk |
|---|---|---|---|
| Strength | Preserve | Wat mag niet kapotgerefactord worden? | bestaande kern beschermen, contracten vastzetten, regressielaag behouden |
| Weakness | Reduce | Waar veroorzaakt drift of onduidelijkheid onnodige schade? | docs opschonen, naming aanscherpen, routes consolideren, contracttests toevoegen |
| Opportunity | Use | Welke volgende laag maakt de repo inhoudelijk sterker? | open-set review, adversarial Gate, probe utility, transfervoorbereiding |
| Threat | Constrain | Welke risico's moeten actief begrensd worden? | overclaiming, workflow-sprawl, scenario-overfitting, publicatieverwarring |

## 1. Preserve

Dit zijn sterke eigenschappen die de repo al heeft en die leidend moeten blijven bij wijzigingen.

### Mechanische kern behouden

- atomische seeds blijven de eenheid van opslag en evaluatie;
- `trace` en `weight` blijven gescheiden;
- manager, Gate en core-logica blijven beslissend voor seedwaardigheid;
- promoted behavior mag niet via een parallelle route ontstaan.

### Regressielaag behouden

- fixture-first CI blijft nuttig als regressieruggengraat;
- kleine suites blijven bruikbaar voor mechanische stabiliteit;
- analyzer- en artifactcontracten blijven expliciet en controleerbaar.

### Bestaande research-discipline behouden

- handmatige evidence blijft herkenbaar gescheiden van standaard CI;
- open-set review blijft een menselijke evidencelaag, geen fixture-surrogaat;
- aanvullende lagen mogen niet stilzwijgend tot een totaalscore worden samengevouwen.

## 2. Reduce

Dit zijn zwakke plekken die de repo niet inhoudelijk sterker maken, maar wel onnodige ruis veroorzaken.

### Documentatie-drift verminderen

- meerdere documenten die tegelijk "leidend" lijken;
- status, plan en rapportage die door elkaar lopen;
- oude paden of artifactnamen die blijven terugkomen.

### Workflow- en publicatieruis verminderen

- overlappende publicatieroutes;
- losse handmatige routes die op publiek resultaat lijken maar een andere status hebben;
- benchmark- en analyseteksten die dezelfde uitkomst op verschillende manieren benoemen.

### Overbodige breedte verminderen

- nieuwe helperlagen die naast de bestaande SSL-route gaan hangen;
- extra code die alleen abstractie toevoegt maar geen contract of gedrag scherper maakt;
- functies of docs die oude naamgeving in leven houden zonder inhoudelijke reden.

## 3. Use

Dit zijn de kansen die de repo echt inhoudelijk verder brengen binnen de bestaande architectuur.

### Open-set seedkwaliteit benutten

De grootste inhoudelijke stap is nog steeds Round 001 via de bestaande open-set review-route.

Belang:

- verschuift open-set van `n/a` naar echte menselijke evidence;
- houdt de claimgrens eerlijk;
- versterkt de repo zonder nieuwe pipeline.

### Adversarial Gate-laag verdiepen

Belang:

- laat zien dat de huidige Gate sterker is dan zwakkere promotieregels;
- ondersteunt de bestaande manager/gate/core-route in plaats van die te omzeilen.

### Probe utility scherper meten

Belang:

- maakt zichtbaar of promoted seeds werkelijk iets nuttigs doen;
- houdt gedragswaarde gescheiden van regressiemetingen.

### Selectieve consolidatie benutten

Belang:

- minder losse documenten en minder dubbele routes maken de repo begrijpelijker;
- consolidatie mag, zolang bewijssoorten niet inhoudelijk worden vermengd.

## 4. Constrain

Dit zijn de risico's die actief begrensd moeten worden.

### Overclaiming begrenzen

Niet doen:

- fixture-uitkomsten presenteren als brede open-world validatie;
- pending of afwezige open-set data als echte evidence labelen;
- aanvullende evidencelagen lezen alsof ze al volledige eindvalidatie vormen.

### Workflow-sprawl begrenzen

Niet doen:

- elke nieuwe behoefte oplossen met nog een los YAML-pad;
- publicatie, smoke, manual evidence en fallback-routes door elkaar laten lopen.

### Scenario-overfitting begrenzen

Niet doen:

- vaste scenario-scores behandelen als volledige claimdrager;
- detectorgedrag stilzwijgend afmeten aan alleen bekende suites.

### Architectuurlekken begrenzen

Niet doen:

- SLM-output als parallelle seedbron naast de bestaande SSL-route behandelen;
- adapterfouten verwarren met echte seed- of evidence-status.

## Backlog-routing

Deze tabel helpt om issues sneller te plaatsen.

| Werkcategorie | Type werk | Voorbeelden | Open issues |
|---|---|---|---|
| Preserve | contracten en regressie beschermen | artifactcontracten, analyzer lookup-discipline, minimale CI | #34, #44 |
| Reduce | drift en overlap weghalen | doc cleanup, wiki-opschoning, route-aanscherping | #45 |
| Use | nieuwe inhoudelijke bewijslagen bouwen | Round 001, adversarial verdieping, probe evaluation | #41, #42, #43, #62 |
| Constrain | risico's en claimgrenzen bewaken | positionering, publicatiegrenzen, version talk | #46, #56 |

## Gebruik bij PR-scoping

Gebruik deze vragen voordat een verandering wordt opgepakt.

1. Beschermt dit iets dat al sterk is?
2. Vermindert dit aantoonbare drift of overlap?
3. Bouwt dit een echte volgende evidencelaag binnen de bestaande SSL-route?
4. Houdt dit een bekend risico binnen grenzen?

Als geen van de vier vragen met ja kan worden beantwoord, hoort het werk waarschijnlijk niet bovenaan de backlog.

## Korte prioriteitsvolgorde

1. Preserve de mechanische kern en regressielaag.
2. Reduce document- en workflow-drift.
3. Use de open-set, adversarial en probe-kansen.
4. Constrain overclaiming en parallelle routevorming.

## Samenvatting

De repo wordt niet beter door steeds meer naast elkaar te zetten.

De repo wordt beter wanneer:

- de sterke kern intact blijft;
- ruis en overlap afnemen;
- de volgende evidencelagen echt gebouwd worden;
- de claimgrens zichtbaar streng blijft.
