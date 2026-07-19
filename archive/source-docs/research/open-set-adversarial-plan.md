# Plan voor Open-set Seed Review en Adversarial Gate-evaluatie

> Status: partly current
> Date: 2026-05-22
> Evidence layer: Adversarial section fulfilled by PR #80; open-set section tracked by #41/#62/#81
> Current source: partial


## Doel van dit document

Dit document maakt de volgende inhoudelijke stap voor SSL 4.5 concreet.

De repo is inmiddels sterk genoeg in mechanische regressie, standaardpublicatie en kleine benchmarkdiscipline. De grootste inhoudelijke zwakte zit nu niet meer in de build- of publicatieketen, maar in het ontbreken van twee zwaardere bewijslagen:

1. open-set seedkwaliteit;
2. adversarial ruiscontrole voor de Validation Gate.

Dit plan beschrijft hoe die twee lagen als volgende werkfase kunnen worden gebouwd zonder de bestaande regressie- en publicatieroute te verstoren.

## Waarom juist deze twee eerst

Deze keuze volgt direct uit de huidige research-status:

- de repo heeft al een sterke regressielaag;
- de repo heeft al een bruikbare kleine benchmarklaag;
- de repo mist nog een overtuigende open-world evaluatie;
- de repo mist nog een harde vergelijking van de huidige Gate tegen zwakkere promotieregels.

Daarom is de hoogste hefboom nu:

```text
niet meer scenario's alleen
maar betere bewijssoorten
```

## Deel A: Open-set seed review

## 1. Hoofdvraag

Kan SSL op onbekende teksten kleine, relevante, toetsbare en niet-triviale seeds produceren zonder vaste seedlijst?

## 2. Wat hier expliciet niet de bedoeling is

Deze laag is niet bedoeld om opnieuw een kleine scenario-suite te bouwen met vooraf uitgeschreven expected seeds.

We willen hier juist weg van de vraag:

> matcht het systeem exact de seed die wij vooraf hadden bedacht?

En toe naar:

> produceert het systeem blind beoordeelbare goede seeds in onbekende context?

## 3. Minimale datasetvorm

Start klein maar echt bruikbaar.

### Aanbevolen eerste batch

- 12 tot 20 teksten
- 4 tot 5 domeinen
- 3 tot 4 teksten per domein

### Aanbevolen eerste domeinen

- geschiedenis
- recht
- software / architectuur
- beleid / onderwijs
- zorg / ethiek

### Tekstvormen

- korte uitlegteksten
- casusantwoorden
- beleidsreacties
- ontwerpvoorstellen
- half-goede samenvattingen

Belangrijk: de teksten moeten niet eerst tot benchmark-scenario's worden herschreven. Het open-set karakter moet overeind blijven.

## 4. Review-eenheid

Per inputtekst produceert SSL een seedlijst.

Iedere seed wordt daarna blind beoordeeld op ten minste deze velden:

| Veld | Vraag |
|---|---|
| atomic | bevat de seed precies één gap? |
| relevant | gaat de seed echt over een betekenisvol gemis in deze tekst? |
| testable | is de seed in principe verifieerbaar of falsifieerbaar? |
| non_trivial | is de seed niet alleen een vage of banale uitbreiding? |
| useful_for_followup | helpt deze seed een goede vervolgstap maken? |
| reject_reason | waarom moet deze seed weg als hij niet goed is? |

### Aanbevolen reject-codes

- `too_broad`
- `too_vague`
- `trivial`
- `not_relevant`
- `not_testable`
- `duplicate`
- `style_not_gap`

## 5. Gewenste artifacts

Per run moet deze laag minimaal opleveren:

```text
open_set_seed_output.json
open_set_review_packets.json
open_set_reviewer_scores.json
open_set_seed_review_summary.json
open_set_disagreements.json
```

De eerste twee artifacts bestaan al als generatielaag. De volgende praktische stap is dat reviewer-uitkomsten niet alleen los worden ingevuld, maar ook geaggregeerd kunnen worden tot acceptance-, agreement- en disagreement-signalen.

Daarvoor hoort nu expliciet een samenvattingsstap bij:

```text
shadowseed summarize-open-set-seed-review \
  --input results/open_review/open_set_review_packets.json \
  --output results/open_set_seed_review_summary.json \
  --disagreements-output results/open_review/open_set_disagreements.json
```

## 6. Primaire metrics

De eerste versie hoeft nog niet perfect te zijn, maar moet wel deze signalen kunnen laten zien:

- acceptance rate
- atomiciteitsratio
- relevantieratio
- niet-triviale seedratio
- reviewer agreement
- reject-reason verdeling

## 7. Minimum success criteria voor fase 1 van deze laag

Pragmatisch startdoel:

- minstens 60% van de seeds wordt niet direct afgekeurd
- minstens 70% van de geaccepteerde seeds wordt als atomisch beoordeeld
- reviewer disagreement blijft overzichtelijk en uitlegbaar
- reject-redenen geven echte leerinformatie terug in plaats van alleen ruis

Dit zijn nog geen paper-claims. Dit zijn acceptatiecriteria voor een eerste bruikbare open-set evaluatielaag.

## 8. Praktische bouwvolgorde

1. Maak een kleine open-set inputmap.
2. Laat de bestaande seed-output daarop draaien.
3. Bouw review-packets met één seed per item.
4. Definieer reject-codes strak.
5. Schrijf een compacte samenvatter voor reviewer-output.
6. Publiceer dit nog niet als standaard CI-hoofdroute.

## Deel B: Adversarial Gate-evaluatie

## 9. Hoofdvraag

Is de huidige Validation Gate echt beter dan eenvoudigere promotieregels wanneer de input misleidend, bijna-volledig of verleidelijk vaag is?

## 10. Waarom dit nodig is

De huidige false-positive laag is nuttig, maar nog te vriendelijk.

We hebben een zwaardere laag nodig die niet alleen vraagt:

> promoveert SSL geen onzin?

maar ook:

> promoveert de huidige Gate minder onzin dan een zwakkere baseline zou doen?

## 11. Minimale baselinevergelijkingen

De eerste adversarial versie moet ten minste drie promotieregels naast elkaar kunnen lezen:

1. `current_gate`
2. `trace_only`
3. `trace_no_contradiction_check`

Optioneel later:

4. `low_evidence_gate`
5. `early_promotion_gate`

## 12. Minimale datasetvorm

Deze laag heeft andere inputs nodig dan de open-set review.

### Aanbevolen eerste batch

- 15 tot 20 teksten

### Verdeling

- 5 bijna-complete antwoorden
- 5 teksten met verleidelijke maar irrelevante uitbreidingskansen
- 5 teksten met stilistische of retorische zwakte die geen echte gap is
- optioneel 3 tot 5 conflictteksten met tegenstrijdige evidencesignalen

## 13. Wat moet per seed worden gelogd

Per kandidaat-seed wil je minimaal zien:

- detector output
- occurrence_count
- evidence_count
- contradiction state
- promoted under current gate?
- promoted under baseline A?
- promoted under baseline B?
- reviewer oordeel: echte gap of niet?

## 14. Gewenste artifacts

```text
adversarial_candidates.json
adversarial_gate_comparison.json
adversarial_false_positive_log.json
adversarial_casebook.md
adversarial_summary.json
```

## 15. Primaire metrics

- candidate false-positive rate
- promoted false-positive rate
- promoted false-positive delta vs baseline
- blocked-bad-seed examples
- missed-good-seed examples

Belangrijk: deze laag moet niet alleen successen tonen, maar ook de trade-off zichtbaar maken.

## 16. Minimum success criteria voor fase 1 van deze laag

Startdoel:

- `current_gate` promoveert minder false positives dan `trace_only`
- `current_gate` promoveert minder false positives dan `trace_no_contradiction_check`
- verschil is zichtbaar op concrete casussen, niet alleen in totaalcijfers
- er ontstaat een kleine casebook met representatieve fouten en juiste blokkades

## Deel C: Repo-integratie

## 17. Waar deze nieuwe laag in de repo past

Aanbevolen eerste structuur:

```text
benchmarks/open_review/
benchmarks/adversarial/
results/open_review/
results/adversarial/
docs/research/open-set-adversarial-plan.md
```

Later kan dit verder worden opgeschoond, maar voor de eerstvolgende fase is dit al duidelijk genoeg.

## 18. CI-positie

Deze nieuwe lagen horen nog niet in de dagelijkse standaardroute.

### Main route blijft

```text
Checks en benchmark-resultaten
-> Publiceer testresultaten naar Wiki en Pages
```

### Nieuwe lagen worden eerst

- handmatig
- experimenteel
- artifact-first
- review-gedreven

Dat voorkomt dat half-volwassen evaluatielagen meteen dezelfde status krijgen als de regressieruggengraat.

## 19. Publicatiepositie

De eerste versies hoeven nog niet naar de publieke hoofdnavigatie.

Wel verstandig:

- artifact-output in Actions
- wiki-pagina als experimenteel dossier zodra de laag bruikbaar is
- nog niet in `Home` als standaardstatusblok

## Deel D: Beslismoment voor 5.0

## 20. Wanneer een 5.0-discussie wél logisch wordt

Een eerlijke `5.0`-sprong wordt pas inhoudelijk logisch als minstens dit staat:

- bruikbare open-set seed review
- bruikbare adversarial Gate-vergelijking
- eerste zichtbare probe utility of domeintransfer richting
- docs en resultaten die dit als nieuwe bewijslaag kunnen dragen

Dan verandert de repo niet alleen in vorm, maar ook in bewijsniveau.

## 21. Wat dit concreet betekent voor nu

Niet nu:

```text
4.5 -> 5.0 als hoofdclaim
```

Wel nu:

```text
4.5 verdiepen met open-set + adversarial evaluatie
```

## 22. Aanbevolen werkvolgorde

1. Bouw open-set inputbatch.
2. Ontwerp review-packet formaat.
3. Definieer reviewer schema en reject-codes.
4. Bouw eerste open-set summary.
5. Bouw adversarial dataset.
6. Vergelijk huidige Gate met zwakkere promotiebaselines.
7. Leg de eerste casebook-voorbeelden vast.
8. Beslis daarna of dit nog een 4.x-stap is of een echte 5.0-voorbereiding.

## 23. Kort eindadvies

De repo hoeft nu niet groter te klinken. Hij moet eerst inhoudelijk scherper worden.

De beste volgende fase is daarom:

> open-set seedkwaliteit en adversarial Gate-evaluatie toevoegen als eerste serieuze bewijsverdieping bovenop de bestaande regressie- en publicatieroute.
