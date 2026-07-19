# Architectuur

## Hoofdflow

```mermaid
flowchart TD
    A[Input of modelantwoord] --> B[Detectie-pass]
    B --> C[Seed-normalisatie]
    C --> D[Nieuwe shadow seed]
    D --> E[trace = 2.0]
    D --> F[weight = 0.0]

    E --> G{Opnieuw herkend?}
    G -- ja --> H[occurrence_count omhoog<br/>trace += 0.5]
    G -- nee --> I[trace decay]
    I --> J{trace < dormant threshold?}
    J -- ja --> K[DORMANT]
    J -- nee --> L[DECAYING / ACTIVE]

    F --> M[Geen retrieval-invloed]
    H --> N[Validation Gate]
    N --> O{occurrence >= 3<br/>evidence >= 2<br/>geen contradictie?}
    O -- nee --> P[weight blijft gelijk]
    O -- contradictie --> Q[weight omlaag<br/>status NEW]
    O -- ja --> R[weight += 0.2]
    R --> S{weight >= 0.5?}
    S -- nee --> T[ACTIVE]
    S -- ja --> U[PROMOTED]
    U --> V[Active Probe]
```

## Belangrijke bestanden

| Bestand | Rol |
|---|---|
| `src/shadowseed/manager.py` | bron voor SSL-formules en state |
| `src/shadowseed/benchmark/ssl45_gap_suite.py` | positieve Gap-Test Suite |
| `src/shadowseed/benchmark/ssl45_false_positive_suite.py` | negatieve controles |
| `src/shadowseed/benchmark/ssl45_benefit_suite.py` | fase 1 benefit-suite |
| `src/shadowseed/benchmark/ssl45_model_benefit_suite.py` | fase 2 model benefit-suite |
| `src/shadowseed/analysis/ssl45_result_analyzer.py` | analyse, Markdown, JSON en SVG |
| `.github/workflows/tests.yml` | CI voor tests, suites, artifacts, analyse en Wiki |
| `.github/workflows/slm-model-benefit.yml` | handmatige echte SLM-run |

## Bron van waarheid

De formules staan in code, niet in de Wiki:

```text
src/shadowseed/manager.py
```

De Wiki beschrijft de werking, maar de tests bewaken de implementatie.

## Canonieke data

De canonieke datasets staan onder:

```text
src/shadowseed/data/
```

Er hoort geen tweede dataset op rootniveau te staan.
