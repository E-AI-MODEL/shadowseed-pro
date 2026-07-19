# Resultaten

Deze pagina beschrijft de actuele output van de SSL 4.5 benchmarkruns uit GitHub Actions artifacts.

Deze pagina is een leeswijzer voor de gepubliceerde standaardresultaten. Ze is geen zelfstandige eindconclusie over SSL 4.5 als algemeen mechanisme.

De actuele publicatie verschijnt via Wiki, Pages en het workflow-artifact `published-latest-results-snapshot`. De publish-workflow commit geen resultatensnapshot terug naar `main`.

## Runs

| Suite | Outputbestand | Scenario's | Bewijssoort |
|---|---|---:|---|
| SSL 4.5 Gap-Test Suite | `ssl45_gap_suite.json` | 3 | kleine benchmark / regressie |
| SSL 4.5 false-positive controls | `ssl45_false_positive_suite.json` | 3 | regressie / beperkte ruiscontrole |

## Positieve Gap-Test Suite

| Metric | Waarde |
|---|---:|
| Mean scenario score | 2.00 |
| Atomische hits | 10 |
| Promoted hits | 10 |

De score gebruikt de schaal uit de Gap-Test Suite:

| Score | Betekenis |
|---:|---|
| 0 | geen relevante gap gevonden |
| 1 | richting klopt, maar output is te vaag of te breed |
| 2 | atomische en structureel juiste gap gevonden |

### Per scenario

| Scenario | Titel | Score | Atomische hits | Promoted hits | Interpretatie |
|---|---|---:|---:|---:|---|
| A | Industriële Revolutie | 2 | 2 | 2 | Werkt binnen de suite. De detector vindt twee atomische koloniale/economische gaps. |
| B | Grensoverschrijdende juridische casus | 2 | 4 | 4 | Werkt binnen de suite. De detector vindt rechtsbevoegdheid, toepasselijk recht, afdwingbaarheid en forumkeuze. |
| C | Software Architectuur | 2 | 4 | 4 | Werkt binnen de suite. De detector vindt privacy-, security- en API-gerelateerde gaps. |

## False-positive controls

De negatieve controles bevatten volledige antwoorden waarin de relevante gaps al expliciet aanwezig zijn. De detector hoort dan niets nieuws te detecteren of te promoten.

| Metric | Waarde |
|---|---:|
| Candidate false positives | 0 |
| Promoted false positives | 0 |
| Candidate false-positive rate | 0.00 |
| Promoted false-positive rate | 0.00 |
| Passed | true |

### Per negatieve controle

| Scenario | Candidate false positives | Promoted false positives | Passed |
|---|---:|---:|---|
| NEG_A | 0 | 0 | true |
| NEG_B | 0 | 0 | true |
| NEG_C | 0 | 0 | true |

Belangrijk:
dit is een nette regressie-uitkomst, maar nog geen zware adversarial Gate-evaluatie.

## Gepromoveerde seeds

### Scenario A

- Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen.
- Goedkope koloniale grondstoffen als voorwaarde voor schaalvergroting van productie.

### Scenario B

- Rechtsbevoegdheid bij een geschil tussen een Nederlandse consument en een Amerikaanse webwinkel.
- Toepasselijk recht bij een grensoverschrijdend consumentencontract.
- Afdwingbaarheid van EU-consumentenrecht tegenover een niet-EU retailer.
- Forumkeuzebeding in internationale online koopvoorwaarden.

### Scenario C

- AVG-compliance bij verwerking van medische hartslagdata.
- Authenticatiestrategie voor toegang tot gezondheidsdata.
- Encryptie van medische data in rust en tijdens transport.
- Rate-limiting op API's die gezondheidsdata verwerken.

## Interpretatie

De huidige runs laten zien dat de pipeline vijf dingen goed doet:

1. atomische detectie in alle drie positieve scenario's;
2. correcte scheiding tussen detectie en promotie;
3. promotie via de Validation Gate zodra de Gate-condities zijn gehaald;
4. herkenning van juridische procedurele gaps in een grensoverschrijdende consumentencontext;
5. geen false positives op drie volledige negatieve controles.

Alle promoted seeds in de artifact-output hebben in de positieve suite:

```text
trace = 3.0
weight = 0.6000000000000001
occurrence_count = 3
evidence_count = 2
status = PROMOTED
```

Dat past bij SSL 4.5: seeds beginnen gewichtloos, worden drie keer herkend, krijgen externe evidence en stijgen pas daarna boven de promotiedrempel.

## Wat deze pagina wel en niet laat zien

Wel:

- de regressielaag werkt;
- de kleine benchmark raakt de ontworpen gaps;
- de meetketen en rapportage zijn reproduceerbaar.

Niet:

- open-set seedkwaliteit buiten vaste scenario's;
- sterke adversarial Gate-robustheid;
- domeintransfer;
- brede modelclaims op echte backends;
- modelinterne validatie.

## Beperking

Deze runs gebruiken de gratis deterministische detector. De resultaten tonen dat de huidige kleine suite volledig geraakt wordt en dat de eerste negatieve controles schoon blijven. Dit is nog geen bewijs dat SSL 4.5 algemeen sterk is buiten deze zes scenario's.

## Volgende stap

- matrix-runs vergelijken voor turns `1`, `2`, `3`, `5` en `8`;
- meer false-positive scenario's toevoegen;
- moeilijkere gedeeltelijk-complete antwoorden testen;
- open-set seed review toevoegen;
- echte adversarial Gate-evaluatie toevoegen;
- daarna pas claims in paper of README verder opschalen.
