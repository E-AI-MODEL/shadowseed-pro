# Tussentijdse rapportage SSL 4.5

## 1. Samenvatting

Shadow Seed Learning 4.5 is in deze repo uitgewerkt als een toetsbare research-pipeline met een duidelijke standaardroute:

```text
Checks en benchmark-resultaten
  -> Publiceer testresultaten naar Wiki en Pages
  -> Latest Test Results + SSL 4.5 Analysis + GitHub Pages
```

De belangrijkste tussentijdse conclusie is nu:

> SSL 4.5 is technisch stabiel genoeg om dagelijks toetsbaar te blijven via een vaste benchmark- en publicatieketen. De huidige claims moeten nog steeds beperkt blijven tot de bestaande suites, de huidige analysemethode en de expliciet uitgevoerde modelchecks.

Wat nu sterk staat:

- de lifecycle van seeds is geïmplementeerd;
- trace en weight zijn gescheiden;
- promotie loopt via de Validation Gate;
- positieve gaps worden getest;
- false positives worden getest;
- antwoordwinst wordt getest;
- model-smoke wordt getest;
- blinde labelscheiding wordt getest;
- analyse, manifest, grafieken en publicatie zijn geautomatiseerd.

Wat nog niet sterk genoeg is voor een brede wetenschappelijke claim:

- de suite is nog klein;
- er is nog weinig variatie in domeinen;
- blind review moet nog structureel worden ingevuld;
- meerdere echte modellen moeten worden getest;
- de resultaten moeten worden herhaald over meer scenario's.

## 2. Onderzoeksvraag

De centrale vraag is:

> Functioneert een model beter wanneer Shadow Seed Learning gevalideerde ontbrekende elementen gebruikt om een antwoord te verbeteren?

Deze vraag is opgesplitst in kleinere toetsbare vragen:

1. Kan SSL ontbrekende structurele elementen atomisch detecteren?
2. Blijven die seeds gewichtloos totdat ze zijn gevalideerd?
3. Promoot SSL alleen seeds die aan de Gate-condities voldoen?
4. Laat SSL volledige antwoorden met rust?
5. Verbetert SSL de gap coverage van een antwoord?
6. Laat dezelfde meetketen zich betrouwbaar publiceren via Wiki en Pages?

## 3. Begrippen

### Shadow seed

Een shadow seed is een klein, specifiek en toetsbaar ontbrekend element.

Voorbeeld:

```text
Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel.
```

Niet goed:

```text
De juridische context mist.
```

Dat is te breed.

### Trace

`trace` meet of een seed aanwezig blijft of opnieuw wordt herkend.

Een seed start met:

```text
trace = 2.0
```

### Weight

`weight` meet of een seed invloed mag hebben.

Een seed start met:

```text
weight = 0.0
```

Daarmee wordt voorkomen dat elke detectie meteen het antwoord gaat sturen.

### Validation Gate

Een seed krijgt pas gewicht als deze voorwaarden gelden:

```text
occurrence_count >= 3
evidence_count >= 2
geen contradictie
```

Daarna stijgt `weight`. Bij voldoende gewicht wordt de seed `PROMOTED`.

## 4. Implementatie

De belangrijkste bron van waarheid is:

```text
src/shadowseed/manager.py
```

Daarin zitten de regels voor:

- seed-status;
- trace;
- weight;
- decay;
- deduplicatie;
- Validation Gate;
- promotie;
- falsificatie.

Belangrijke benchmarkbestanden:

```text
src/shadowseed/benchmark/ssl45_gap_suite.py
src/shadowseed/benchmark/ssl45_false_positive_suite.py
src/shadowseed/benchmark/ssl45_benefit_suite.py
src/shadowseed/benchmark/ssl45_model_benefit_suite.py
src/shadowseed/benchmark/blind_benchmark.py
src/shadowseed/analysis/ssl45_result_analyzer.py
src/shadowseed/analysis/artifact_snapshot.py
```

Belangrijke datasets:

```text
src/shadowseed/data/gap_test_suite_4_5.json
src/shadowseed/data/gap_test_suite_false_positive_4_5.json
src/shadowseed/data/ssl45_benefit_suite.json
src/shadowseed/data/ssl45_model_benefit_suite.json
src/shadowseed/data/blind_suite_public.json
```

## 5. Benchmarklagen

### 5.1 Positieve Gap-Test Suite

Doel:

> Testen of SSL de juiste ontbrekende structurele gaps vindt.

Belangrijke metrics:

- `mean_scenario_score`
- `atomische_hits`
- `promoted_hits`

### 5.2 False-positive controls

Doel:

> Testen of SSL niets verzint wanneer het antwoord al volledig is.

Belangrijke metrics:

- `candidate_false_positives`
- `promoted_false_positives`
- `promoted_false_positive_rate`

### 5.3 Benefit Suite

Doel:

> Testen of SSL-promoted seeds de gap coverage van een antwoord verhogen.

Belangrijke metrics:

- `baseline_mean_gap_coverage`
- `ssl_mean_gap_coverage`
- `coverage_delta`
- `unsupported_ssl_additions`

### 5.4 Model smoke

Doel:

> Testen of dezelfde modelroute technisch werkt zonder zware modeldownload.

De standaard CI gebruikt een fixture-backend. Dat bewijst de meetketen, niet de brede prestatie van een echt model.

### 5.5 Blind test

Doel:

> Testen of labels verborgen blijven tot de scoring.

Deze laag bewaakt dat detectie en scoring gescheiden blijven.

## 6. Standaard publicatie

De dagelijkse standaardroute is nu belangrijker dan losse experiment-workflows.

De keten is:

```text
Checks en benchmark-resultaten
  -> artifacts
  -> Publiceer testresultaten naar Wiki en Pages
  -> Latest Test Results
  -> SSL 4.5 Analysis
  -> GitHub Pages dashboard
```

Belangrijke output:

```text
results/latest/summary.json
results/latest/analysis_report.md
results/latest/manifest.json
results/artifacts/
workflow-artifact: published-latest-results-snapshot
```

De publish-route controleert nu ook expliciet of kernbestanden ontbreken, of het manifest leeg is, of de centrale summary ongeldig is. Daardoor stopt een halve publicatie zichtbaar in plaats van stilletjes door te lopen.

## 7. Aanvullende handmatige checks

Naast de standaardroute bestaan nog aanvullende runs:

### Model Reality Check

Workflow:

```text
Actions -> Model Reality Check
```

Gebruik deze run om te testen of retrieval + SSOT ook bij een echt HF-model helpt.

### SSOT Falsification Run

Workflow:

```text
Actions -> SSOT Falsification Run
```

Gebruik deze run om te testen of SSL niet naïef elke bron of `llm_proposed` chunk accepteert.

### Full Validation Sweep

Workflow:

```text
Actions -> Full Validation Sweep
```

Gebruik deze run als bredere systeem- en backendcheck. Dit is geen dagelijkse statusroute, maar een aanvullende technische sweep.

## 8. Analyse en rapportage

De analyse wordt gemaakt door:

```text
shadowseed analyze-results
```

Output:

```text
results/analysis/analysis_report.md
results/analysis/analysis_summary.json
results/analysis/coverage.svg
results/analysis/false_positive.svg
```

De publicatieroute bouwt daaruit de centrale publiekslaag:

- `Latest Test Results`
- `SSL 4.5 Analysis`
- `SSL 4.5 Analysis Summary JSON`
- GitHub Pages dashboard

## 9. Tussentijdse conclusie

Op basis van de huidige stand is de juiste conclusie:

> SSL 4.5 is nu een werkende, reproduceerbare en publiceerbare research-pipeline. De methode detecteert atomische afwezigheden, houdt trace en weight gescheiden, promoot seeds pas na validatie en zet standaardresultaten automatisch om in een controleerbare publieke snapshot.

De huidige resultaten ondersteunen deze beperkte claim:

> Binnen de huidige benchmarkopzet kan SSL worden gemeten als verbetering van gap coverage, mits unsupported additions en false positives laag blijven en de publicatieketen de echte artifacts correct doorzet.

De huidige resultaten ondersteunen nog niet deze brede claim:

> SSL verbetert modellen in het algemeen.

Daarvoor is meer nodig:

- meer scenario's;
- meer domeinen;
- meerdere echte modellen;
- herhaalde runs;
- blind review;
- rapportage van negatieve en gemengde resultaten.

## 10. Risico's en beperkingen

### Kleine suite

De huidige suite is klein. Goede scores op deze suite zijn nuttig, maar niet genoeg voor een brede claim.

### Detector kan te passend zijn

Omdat de detector nu domeinpriors gebruikt, moet worden getest of hij ook buiten de huidige scenario's goed werkt.

### Lengte-effect

SSL-antwoorden kunnen langer zijn. Daarom blijft het belangrijk om niet alleen coverage, maar ook unsupported additions en lengte-effecten mee te lezen.

### Geen automatische waarheid

Een promoted seed is geen absolute waarheid. Het is een gevalideerd signaal binnen de testopzet.

### Model Reality Check is modelafhankelijk

Een positief resultaat met één echt model geldt niet automatisch voor andere modellen.

## 11. Blind review

Blind review blijft nodig voordat claims sterker worden gemaakt.

Gebruik hiervoor:

- [Blind review protocol](Blind-Review-Protocol)
- de output van modelruns
- vergelijking zonder vooraf te weten welke conditie baseline of SSL is

## 12. Volgende stappen

### Stap 1: standaardroute stabiel houden

Blijf eerst de normale route gezond houden:

```text
Checks en benchmark-resultaten
-> Publiceer testresultaten naar Wiki en Pages
```

### Stap 2: scenario's uitbreiden

Minimaal uitbreiden naar:

- 10 positieve scenario's;
- 10 negatieve scenario's;
- 10 gedeeltelijk complete scenario's.

### Stap 3: meerdere echte modellen testen

Altijd per model vergelijken:

```text
zelfde model zonder SSL
zelfde model met SSL
```

### Stap 4: blind review uitvoeren

Gebruik de reviewtemplates en de modeloutput.

### Stap 5: paperclaims aanpassen

Pas na meer runs en reviews kunnen claims in paper of README sterker worden.

## 13. Printbare conclusie

Als dit dossier wordt uitgeprint, is de kern:

1. SSL 4.5 is geïmplementeerd als testbare methode.
2. De repo bewaakt de interne methode met regressie-, benchmark- en safety-tests.
3. De standaard publicatieroute maakt van artifacts een controleerbare publieke snapshot.
4. De huidige benchmarklaag test positieve detectie, negatieve controles, antwoordwinst, model-smoke en blinde labelscheiding.
5. Aanvullende model- en safety-runs bestaan, maar zijn secundair aan de dagelijkse standaardroute.
6. De huidige claim moet beperkt blijven tot de huidige suites en uitgevoerde runs.
7. De volgende stap is schaalvergroting, echte modelvergelijking en blind review.

## 14. Verwijzingen binnen de Wiki

- [Latest Test Results](Latest-Test-Results)
- [SSL 4.5 Analysis](SSL-45-Analysis)
- [Dashboard](Dashboard)
- [Benchmarks](Benchmarks)
- [Waarom SSL niet naïef is](Waarom-SSL-niet-naief-is)
- [Blind review protocol](Blind-Review-Protocol)
- [Roadmap](Roadmap)
