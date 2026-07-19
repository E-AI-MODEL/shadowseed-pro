# Resultaten en analyse

De repo maakt resultaten op twee niveaus:

1. ruwe benchmark-JSON;
2. geanalyseerde Markdown, JSON en SVG-grafieken.

## Analyse draaien

```bash
shadowseed run-gap-suite
shadowseed run-false-positive-suite
shadowseed run-benefit-suite
shadowseed run-model-benefit-suite --backend fixture
shadowseed analyze-results
```

Output:

```text
results/analysis/analysis_report.md
results/analysis/analysis_summary.json
results/analysis/coverage.svg
results/analysis/false_positive.svg
```

## Analyse in CI

De workflow `tests.yml` maakt automatisch het artifact:

```text
ssl45-analysis-report
```

Daarin staan:

```text
analysis_report.md
analysis_summary.json
coverage.svg
false_positive.svg
```

## Analyse op de Wiki

De gewone analyse wordt gepubliceerd naar:

```text
SSL-45-Analysis
SSL-45-Analysis-Summary
coverage.svg
false_positive.svg
```

De echte SLM-run wordt gepubliceerd naar:

```text
SLM-Model-Benefit
SLM-Model-Benefit-Analysis
SLM-Model-Benefit-Analysis-Summary
SLM-Model-Benefit-Raw
slm_coverage.svg
slm_false_positive.svg
```

## Wat de grafieken tonen

| Grafiek | Betekenis |
|---|---|
| `coverage.svg` | dekking van gap scores en benefit coverage |
| `false_positive.svg` | false-positive en unsupported-addition rates |

## Semantische analyse

De analyzer groepeert promoted seeds op:

- domein;
- scenario;
- toptermen.

Dit helpt om te zien waar SSL inhoudelijk op stuurt.

## Interpretatie

Een resultaat is pas sterk als deze vier dingen samen kloppen:

1. positieve gaps worden geraakt;
2. negatieve controles blijven schoon;
3. SSL verhoogt gap coverage;
4. unsupported additions blijven laag.

Een hogere score door alleen langere antwoorden telt niet als sterke SSL-winst.
