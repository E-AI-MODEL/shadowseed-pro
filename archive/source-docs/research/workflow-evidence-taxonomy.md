# Workflow evidence taxonomy

> Status: current
> Date: 2026-05-22
> Evidence layer: Workflow ↔ evidence taxonomy
> Current source: yes


Deze pagina legt vast hoe workflows, benchmarkruns en resultaatartefacts benoemd en gelezen moeten worden.

Doel:

- zichtbaar maken of een workflow SSL bewaakt of bewijs probeert te verzamelen;
- voorkomen dat regressiechecks en researchclaims door elkaar lopen;
- duidelijk maken welke runs merge-blokkerend zijn;
- standaardiseren hoe benchmarkartefacts gelezen worden.

## Drie workflowlagen

De repo gebruikt drie hoofdlagen.

| Prefix | Rol | Merge-blokkerend | Bewijsniveau |
|---|---|---|---|
| `CI` | regressie en kapotchecks | ja | laag |
| `B` | benchmark- en evidenceruns | soms | middel |
| `R` | research- en exploratieruns | nee | experimenteel |

## 1. CI-routes

CI-routes beantwoorden:

> werkt SSL nog mechanisch correct?

Voorbeelden:

- unit tests
- smoke-routes
- regressiesuites
- false-positive guards
- standaard workflowvalidatie

Voorbeeldnamen:

- `CI01_unit_tests.yml`
- `CI02_regression_smoke.yml`
- `CI03_false_positive_guard.yml`

Kernregel:

> een CI-run zegt niet automatisch iets over de algemene wetenschappelijke geldigheid van SSL.

## 2. Benchmark- en evidenceruns

Benchmarkruns beantwoorden:

> levert SSL meetbare output op binnen een bepaalde evaluatielaag?

Voorbeelden:

- gap-suite
- adversarial Gate benchmark
- probe utility benchmark
- open-set review

Voorbeeldnamen:

- `B01_gap_suite.yml`
- `B02_adversarial_gate.yml`
- `B03_probe_utility.yml`
- `B04_open_set_review.yml`

Kernregel:

> benchmarkoutput moet altijd gelezen worden samen met het bewijsniveau en de beperkingen van die evaluatielaag.

## 3. Research-routes

Research-routes beantwoorden:

> welke aanvullende hypotheses of evaluatievormen willen we onderzoeken?

Voorbeelden:

- LLM-backends
- vectorstorevergelijkingen
- domeintransfer
- grotere open-set intake

Voorbeeldnamen:

- `R01_llm_backend.yml`
- `R02_vector_backend_comparison.yml`
- `R03_domain_transfer.yml`

Deze routes horen standaard geen merges te blokkeren.

## Evidence labels

Elke benchmark- of researchrun hoort zichtbaar te maken:

| Label | Betekenis |
|---|---|
| `fixed-scenarios` | vaste scenario’s of fixtures |
| `open-set` | onbekende of bredere input |
| `manual-review` | menselijke beoordeling nodig |
| `local-deterministic` | geen externe modelcalls |
| `llm-assisted` | gebruikt modelbackend |
| `vector-assisted` | gebruikt vectorstore of retrieval |

## Resultaatinterpretatie

Een run hoort altijd zichtbaar te maken:

- of het een regressiecheck is;
- of het een benchmarkresultaat is;
- of het een exploratieve researchrun is;
- welke inputbasis gebruikt werd;
- welke beperkingen gelden.

## Waarom dit nodig is

Zonder deze indeling ontstaat verwarring tussen:

- kapotchecks;
- kleine benchmarkvalidatie;
- aanvullende evidencelagen;
- echte open-world validatie.

Juist SSL heeft deze scheiding nodig omdat de repo tegelijk:

- engineeringcode;
- benchmarkinfrastructuur;
- researchartefacts;
- en hypothesevorming bevat.

## Praktische hoofdregel

> eerst zichtbaar maken welke bewijslaag een workflow ondersteunt, daarna pas nieuwe evaluatieroutes toevoegen.
