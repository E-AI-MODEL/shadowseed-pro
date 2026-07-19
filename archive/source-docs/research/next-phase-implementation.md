# Uitvoeringsplan Voor De Volgende SSL-fase

> Status: historical
> Date: 2026-05-22
> Evidence layer: Predecessor of roadmap-shadowseed-stabilization.md
> Current source: no


## Doel

Dit document vertaalt de bestaande 4.6-koers naar een directe bouwvolgorde voor de repo.

De vraag is niet meer:

> wat zou SSL ooit idealiter moeten bewijzen?

De vraag is nu:

> wat bouwen we als volgende twee bewijs-lagen eerst, in welke volgorde, en hoe weten we dat de repo daarna beter aligned is?

## Korte kern

De hoogste hefboom is nu:

1. regressielaag behouden zoals hij is;
2. open-set seedkwaliteit operationeel maken;
3. adversarial Gate-vergelijking operationeel maken;
4. daarna pas probe utility en transfer uitbouwen.

Dat is de kortste route van een sterke harness naar een geloofwaardiger onderzoeksrepo.

## Waarom deze volgorde

### Eerst niet doen

- niet meteen een brede 5.0-sprong
- niet eerst meer scenario's toevoegen
- niet eerst domeintransfer willen meten
- niet eerst behavioral metrics zwaar maken

### Eerst wel doen

- betere bewijssoorten bovenop de bestaande mechanische ruggengraat
- zichtbaar onderscheid tussen regressie en hoofdclaim
- artifacts die open-set en adversarial evaluatie echt kunnen dragen

## Fase 1 — Regressielaag bevriezen als regressielaag

### Doel

De huidige standaardroutes blijven de mechanische ankers van de repo.

### Wat hieronder valt

- `run-gap-suite`
- `run-false-positive-suite`
- `run-benefit-suite`
- `run-model-benefit-suite --backend fixture`
- `run-blind-benchmark`
- `run-absencebench-smoke`
- `analyze-results`

### Klaar als

- docs nergens meer impliceren dat deze laag de hele algemene SSL-claim bewijst
- rapportage deze laag blijft labelen als regressie, smoke of kleine benchmark
- nieuwe research-lagen deze laag niet overschrijven in de hoofdnavigatie

## Fase 2 — Open-set seedkwaliteit echt operationeel maken

### Hoofdvraag

Kan SSL op onbekende teksten kleine, relevante, toetsbare en niet-triviale seeds maken zonder vaste seedlijst?

### Minimale repo-deliverables

```text
benchmarks/open_review/
  input/                     # kleine eerste batch open teksten
  README.md                  # protocol en artifactcontract

results/open_review/         # niet als vaste repo-output, maar als beoogde artifactmap
```

### Minimale workflow

1. inputteksten verzamelen
2. `run-open-set-seed-review` draaien
3. review-packets laten invullen
4. `summarize-open-set-seed-review` draaien
5. acceptance, agreement en disagreements apart lezen

### Minimum viable artifacts

- `open_set_seed_output.json`
- `open_set_review_packets.json`
- `open_set_seed_review_summary.json`
- `open_set_disagreements.json`

### Definition of done

- review-packets hebben vaste velden
- reject-codes zijn stabiel
- de summary maakt acceptance, atomiciteit en disagreements zichtbaar
- de laag kan als aparte evidence layer benoemd worden zonder scenario-ground-truth

## Fase 3 — Adversarial Gate-laag echt operationeel maken

### Hoofdvraag

Is de huidige Validation Gate beter dan eenvoudiger promotieregels op misleidende of verleidelijk irrelevante gaps?

### Minimale repo-deliverables

```text
benchmarks/adversarial/
  input/                     # bijna-complete, lokkende en niet-gap teksten
  README.md                  # baseline- en artifactcontract
```

### Minimale baselinevergelijkingen

- `current_gate`
- `trace_only`
- `trace_no_contradiction_check`

### Minimum viable artifacts

- `adversarial_candidates.json`
- `adversarial_gate_comparison.json`
- `adversarial_false_positive_log.json`
- `adversarial_casebook.md`
- `adversarial_summary.json`

### Definition of done

- false positives zijn zichtbaar per baseline
- de huidige Gate kan concreet vergeleken worden met zwakkere regels
- de casebook toont niet alleen scores maar ook voorbeelden
- de laag kan een zelfstandige kwaliteitsclaim dragen over Gate-waarde

## Fase 4 — Probe utility pas daarna verdiepen

### Waarom pas daarna

Als seedkwaliteit en Gate-waarde nog niet stevig staan, meet probe utility te vroeg op een half-bewezen basis.

### Wat hierna logisch wordt

- betere vervolgvragen meten
- retrieval improvement meten
- dialectische falsificatiekwaliteit meten
- menselijke voorkeur toevoegen voor vervolgacties

### Klaar als

- promoted seeds aantoonbaar nuttiger vervolgactie opleveren dan bredere baseline-aanpakken

## Fase 5 — Domeintransfer daarna pas breed trekken

### Waarom daarna

Transfer is pas interessant als je eerst weet dat de kernlaag van open-set seedkwaliteit en Gate-beslissingen sterk genoeg is.

### Eerste doel

- extra domeinen
- holdouts
- meerdere tekstgenres
- minimale afhankelijkheid van domein-priors

## Technische repo-aanpassingen die dit ondersteunen

## 1. Zichtbare werkvakken

De repo moet expliciet laten zien waar de volgende lagen landen.

Daarom zijn deze plekken bedoeld als doelstructuur:

- `src/shadowseed/evaluation/`
- `benchmarks/open_review/`
- `benchmarks/adversarial/`
- `benchmarks/transfer/`

Nog niet alles hoeft daarheen verhuisd te worden. Maar nieuwe laag-specifieke artifacts en docs moeten vanaf nu wel consequent die richting op wijzen.

## 2. Geen samensmelting van ongelijke bewijssoorten

Niet doen:

- open-set en regressie in één totaalscore duwen
- adversarial artifacts dezelfde status geven als standaard CI-smokes
- fixture-smokes en menselijke review als één bewijssoort presenteren

## 3. Artifactdiscipline

Nieuwe lagen moeten dezelfde basisdiscipline volgen:

- vaste bestandsnamen
- vaste JSON-velden
- duidelijke manifest- of herkomstinformatie waar nodig
- leesbare summary-artifacts naast ruwe JSON

## Alignment-check na uitvoering

Als deze fase goed staat, moet de repo na een review deze drie uitspraken waar maken.

### 1. Inhoudelijk

- de hoofdclaim rust niet meer alleen op scenario-suites
- open-set en adversarial zijn zichtbaar als echte volgende bewijslagen

### 2. Structureel

- nieuwe lagen hebben een herkenbare plek in docs en benchmarkmappen
- de CLI-indeling vertelt hetzelfde verhaal als de research-docs

### 3. Technisch

- nieuwe werkvakken beschadigen de regressielaag niet
- er ontstaat geen onduidelijke mix van CI-smoke, handmatige review en hoofdclaim

## Korte uitvoervolgorde

1. regressielaag blijven labelen als regressie
2. open-set artifacts en protocol vastzetten
3. adversarial baselinevergelijking vastzetten
4. daarna probe utility verdiepen
5. daarna transfer uitbouwen

## Eindzin

De juiste volgende stap voor SSL is nu niet groter klinken, maar scherper bewijzen.

Kort:

> eerst open-set seedkwaliteit en adversarial Gate-waarde hard maken, daarna pas het bereik van de claim vergroten.
