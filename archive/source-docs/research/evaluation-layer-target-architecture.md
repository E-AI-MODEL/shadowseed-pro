# Evaluation Layer Target Architecture

> Status: planning
> Date: 2026-05-22
> Evidence layer: Target architecture across layers
> Current source: yes


Status: uitvoerplan voor de stap na repo-cleanup.

Deze notitie vertaalt de 4.6-koers naar een concrete repo-architectuur. Ze verandert geen claimniveau en vervangt geen tests. Het doel is om de volgende inhoudelijke fase reviewbaar te maken voordat er nieuwe workflowroutes of grote codeverplaatsingen komen.

## Uitgangspunt

De repo moet niet breder worden door steeds meer losse benchmarkroutes toe te voegen.

De repo moet scherper worden door evaluaties te scheiden naar bewijssoort.

Dat volgt uit de 4.6-bron:

- scenario-suites blijven regressie en beperkte benchmarkvalidatie;
- de hoofdclaim moet later worden gedragen door open-set seedkwaliteit, adversarial ruiscontrole, probe utility en domeintransfer;
- smoke, regressie en hoofdvalidatie mogen niet in één totaalscore verdwijnen.

## Doelbeeld

De evaluatielaag krijgt vijf duidelijke banen.

```text
src/shadowseed/evaluation/
  regression/
  open_review/
  adversarial/
  behavioral/
  transfer/
```

Dit hoeft niet in één PR fysiek verplaatst te worden. Eerst wordt de betekenis vastgelegd. Daarna kunnen modules stap voor stap migreren.

## 1. Regression

Vraag:

> Blijft de bestaande mechaniek werken?

Hoort hierbij:

- gap suite
- false-positive suite
- benefit suite
- blind smoke
- model benefit smoke
- AbsenceBench smoke
- manager lifecycle tests
- artifact snapshot tests

Gewenste artifactnamen:

```text
results/regression/gap_suite.json
results/regression/false_positive_suite.json
results/regression/benefit_suite.json
results/regression/model_benefit_suite.json
results/regression/blind_benchmark.json
results/regression/absencebench_smoke.json
```

Claimniveau:

- mechanische stabiliteit
- regressiebewaking
- geen algemene SSL-validatie

Workflowstatus:

- standaard CI
- publishbaar als snapshot

## 2. Open review

Vraag:

> Maakt SSL in onbekende teksten kleine, toetsbare en nuttige seeds zonder vaste expected gaps?

Hoort hierbij:

- open-set input batches
- seed review packets
- menselijke review
- reviewer agreement
- reject codes
- acceptance summary

Gewenste artifactnamen:

```text
results/open_review/review_packets.json
results/open_review/reviewer_labels.json
results/open_review/summary.json
results/open_review/disagreements.json
```

Minimale metrics:

- atomicity_acceptance_rate
- relevance_acceptance_rate
- unsupported_or_hallucinated_rate
- reviewer_agreement_rate
- rejection_code_counts

Claimniveau:

- eerste echte stap weg van scenario-afhankelijkheid
- nog geen automatische standaardroute zolang menselijke review nodig is

Workflowstatus:

- handmatig
- geen standaard CI totdat input, labels en metrics stabiel zijn

## 3. Adversarial

Vraag:

> Houdt de Validation Gate verleidelijke maar onjuiste gaps beter tegen dan simpele promotieregels?

Hoort hierbij:

- adversarial lure cases
- current Gate
- trace-only baseline
- trace without contradiction check
- casebook-output

Gewenste artifactnamen:

```text
results/adversarial/gate_comparison.json
results/adversarial/gate_casebook.md
results/adversarial/baseline_summary.json
```

Minimale metrics:

- current_gate_false_promotion_rate
- trace_only_false_promotion_rate
- no_contradiction_false_promotion_rate
- gate_relative_reduction
- blocked_lure_count
- promoted_lure_count

Claimniveau:

- harde test van Gate-waarde
- hoofdroute voor Fase 2-verdieping

Workflowstatus:

- eerst handmatig
- later kandidaat voor periodieke workflow als data en baselines stabiel zijn

## 4. Behavioral

Vraag:

> Leiden promoted seeds tot betere vervolgstappen?

Hoort hierbij:

- probe utility
- Socratische vraagkwaliteit
- retrieval-query verbetering
- dialectische probekwaliteit
- unsupported-addition reductie

Gewenste artifactnamen:

```text
results/behavioral/probe_utility.json
results/behavioral/probe_casebook.md
results/behavioral/retrieval_probe_comparison.json
```

Minimale metrics:

- probe_specificity_delta
- retrieval_hit_at_k_delta
- unsupported_addition_delta
- human_preference_rate
- useful_followup_rate

Claimniveau:

- bewijst niet alleen dat seeds bestaan
- meet of seeds nuttige acties sturen

Workflowstatus:

- handmatig tot open review en adversarial laag steviger staan

## 5. Transfer

Vraag:

> Blijft seedkwaliteit overeind buiten de bekende domeinen en promptvormen?

Hoort hierbij:

- holdout domains
- nieuwe tekstvormen
- verschillende stijlen
- cross-domain batches

Gewenste artifactnamen:

```text
results/transfer/domain_holdout_summary.json
results/transfer/domain_casebook.md
```

Minimale metrics:

- per_domain_acceptance_rate
- per_domain_false_positive_rate
- domain_variance
- transfer_drop

Claimniveau:

- brede generalisatie
- pas zinvol als open review en adversarial stabieler zijn

Workflowstatus:

- later
- niet de eerstvolgende buildstap

## CLI-tier mapping

De bestaande CLI hoeft nog niet zwaar te worden herbouwd. Wel moet elk command straks zichtbaar aan een evaluatielaag hangen.

| Evaluatielaag | Commands |
|---|---|
| regression | `run-gap-suite`, `run-false-positive-suite`, `run-benefit-suite`, `run-model-benefit-suite`, `run-blind-benchmark`, `run-absencebench-smoke`, `analyze-results` |
| open_review | `run-open-set-seed-review`, `summarize-open-set-seed-review` |
| adversarial | `run-adversarial-gate-benchmark` |
| behavioral | `run-probe-utility-benchmark`, later retrieval-probe comparison |
| transfer | nog geen command |

Regel:

> een command mag pas naar standaard CI als het regressie- of smoke-waarde heeft zonder menselijke review als kernstap.

## Analyzer-output

De analyzer moet niet één totaaloordeel maken dat alle bewijssoorten gelijk behandelt.

Gewenste rapportstructuur:

```text
analysis/
  regression_verdict.md
  open_review_verdict.md
  adversarial_verdict.md
  behavioral_verdict.md
  transfer_verdict.md
  overall_claim_boundary.md
```

`overall_claim_boundary.md` mag alleen samenvatten wat per laag gedragen wordt. Het mag geen smoke-output als hoofdvalidatie laten klinken.

## Volgorde van uitvoering

### PR A: Python correctness

Doel:

- CLI alias-contract herstellen
- stabiele hashing invoeren waar benchmarks deterministic moeten zijn
- vectorstore persistence-semantiek controleren of begrenzen

Waarom eerst:

- bestaande Python-correctness gaat voor nieuwe evaluatiebouw
- dit voorkomt nieuwe rode PR's door bekende drift

### PR B: Open review schema

Doel:

- review packet schema vastleggen
- reviewer label schema vastleggen
- summary shape vastleggen
- tests toevoegen op artifactvorm

Geen nieuwe claim.

### PR C: Adversarial Gate hardening

Doel:

- Gate-comparison output stabiliseren
- baselines expliciet maken
- casebook-output vastleggen
- analyzer laten rapporteren per bewijslaag

### PR D: Behavioral probe utility

Doel:

- probe utility loshalen van alleen lexicale score
- minimaal retrieval-hit of reviewer-preference toevoegen

### PR E: Transfer

Doel:

- pas starten als open review en adversarial niet meer scaffold-only zijn

## Niet doen

Nog niet doen:

- scenario-suites verwijderen
- alles direct fysiek verplaatsen
- open review in standaard CI zetten
- één totaalscore voor SSL maken
- 5.0 claimen als huidige staat

## Eerste concrete stap

De eerstvolgende echte code-PR moet klein zijn:

```text
codex/python-correctness-before-evaluation
```

Scope:

1. CLI alias-contract corrigeren
2. deterministic token hashing centraliseren
3. subprocess-smoke toevoegen voor canonieke en legacy AbsenceBench commands
4. alleen daarna opnieuw kijken naar open review en adversarial verdieping

Dit houdt de repo in dienst van de 4.6-koers: eerst correct, dan dieper, daarna pas breder.
