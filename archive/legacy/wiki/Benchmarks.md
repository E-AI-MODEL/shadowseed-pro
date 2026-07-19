# Benchmarks

Deze pagina legt in gewone taal uit welke soorten tests de repo gebruikt.

Belangrijk:

> niet elke test draagt dezelfde bewijslast.

Sommige tests bewaken vooral de mechaniek. Andere tests geven een eerste inhoudelijke indicatie. Weer andere tests zijn aanvullende evidencelagen die iets laten zien buiten de kleinste basislaag.

## Overzicht

| Naam in Actions | Vraag | Artifact | Bewijssoort |
|---|---|---|---|
| 01 Codecheck | Werkt de Python-code? | geen JSON | regressie |
| 02 Gap Finder | Vindt SSL bekende ontbrekende punten? | `ssl45_gap_suite.json` | kleine benchmark |
| 03 Rustig blijven | Laat SSL volledige antwoorden met rust? | `ssl45_false_positive_suite.json` | regressie / beperkte ruiscontrole |
| 04 Antwoordwinst | Wordt een antwoord completer door SSL? | `ssl45_benefit_suite.json` | kleine benchmark |
| 05 Model smoke | Werkt dezelfde modelroute technisch? | `ssl45_model_benefit_suite.json` | technische smoke |
| 06 Blind test | Blijven labels verborgen tot scoring? | `blind_benchmark.json` | methodologische smoke |
| 06b Adversarial Gate | Blokkeert de Gate misleidende lure-seeds? | `adversarial_gate_benchmark.json`, casebook | aanvullende evidencelaag |
| 06c Probe utility | Helpen promoted seeds bij scherpere vervolgacties? | `ssl45_probe_utility_suite.json` | aanvullende evidencelaag |
| 07 Rapport | Hoe zien de resultaten er samen uit? | `analysis_report.md`, `summary.json` | rapportage |
| 08 AbsenceBench rooktest | Werkt de lokale dataset-run? | `absencebench_smoke.json` | technische smoke |
| 09 Herhalingstest | Wat gebeurt er bij meer rondes? | `ssl45_gap_suite_turns_*.json` | gevoeligheid / regressie |
| handmatig | Kan SSL onbekende teksten reviewbaar samenvatten zonder vaste seedlijst? | open-set review artifacts | aanvullende evidencelaag |

## Wat betekent elke bewijssoort?

### Regressie

Een regressietest zegt vooral:

- de basis werkt nog;
- een refactor heeft de kern niet stukgemaakt.

### Technische smoke

Een technische smoke-test zegt:

- een route werkt technisch;
- maar de inhoudelijke claim blijft nog beperkt.

### Methodologische smoke

Een methodologische smoke-test zegt:

- de meetmethode blijft eerlijk;
- bijvoorbeeld doordat labels niet vooraf in de detectielaag terechtkomen.

### Kleine benchmark

Een kleine benchmark zegt:

- er is meetbare winst of verlies op een kleine vaste set;
- maar nog niet automatisch buiten die vaste set.

### Aanvullende evidencelaag

Een aanvullende evidencelaag zegt:

- hier probeert de repo inhoudelijk verder te gaan dan alleen fixture- en scenario-smokes;
- maar ook deze laag moet nog voorzichtig gelezen worden.

## Wat bezoekers het vaakst verkeerd lezen

### "Model smoke" is geen grote modelclaim

De standaard CI draait `fixture` om de meetketen te testen.
Dat is nuttig, maar geen brede claim over echte modelprestatie.

### Adversarial en probe utility zijn belangrijk, maar nog niet alles

Deze twee lagen staan nu bewust in de standaardpublicatie omdat ze publiek zichtbaar moeten zijn.
Ze moeten nog steeds gelezen worden als aanvullende evidencelagen en niet als volledig eindbewijs.

### Open-set review is inhoudelijk belangrijker dan alleen meer scenario's

Open-set review probeert te meten of SSL ook buiten een vaste seedlijst nog kleine, relevante en toetsbare seeds maakt.
Dat is een sterkere richting dan alleen nog meer vaste suites toevoegen.

## Hoe lees je de standaardpublicatie verstandig?

Lees in deze volgorde:

1. regressie en smoke: werkt de basis?
2. kleine benchmarks: zie je winst op de vaste set?
3. aanvullende evidencelagen: zie je extra bewijs buiten de kleinste basislaag?
4. claimgrens: wat is nog niet bewezen?

## Belangrijkste grens

De standaardpublicatie is vandaag bedoeld om drie dingen tegelijk zichtbaar te maken:

- mechanische stabiliteit;
- kleine benchmarksignalen;
- eerste aanvullende bewijslagen.

Ze is nog niet bedoeld als definitieve eindvalidatie van het hele SSL-programma.
