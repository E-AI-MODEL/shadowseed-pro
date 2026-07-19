# Quick Start

## Installatie

```bash
pip install -e ".[test]"
```

Met optionele modeldependencies:

```bash
pip install -e ".[models]"
```

## Basischecks

```bash
pytest
shadowseed run-gap-suite
shadowseed run-false-positive-suite
shadowseed run-benefit-suite
shadowseed run-model-benefit-suite --backend fixture
shadowseed analyze-results
```

## Belangrijkste outputs

```text
results/ssl45_gap_suite.json
results/ssl45_false_positive_suite.json
results/ssl45_benefit_suite.json
results/ssl45_model_benefit_suite.json
results/analysis/analysis_report.md
results/analysis/analysis_summary.json
results/analysis/coverage.svg
results/analysis/false_positive.svg
```

## Echte SLM-run

Gebruik de handmatige GitHub Action:

```text
Actions → SLM Model Benefit Run → Run workflow
```

Standaardmodel:

```text
TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

## Wiki-publicatie

Static Wiki-pagina's komen uit:

```text
docs/wiki/
```

Analysepagina's worden gemaakt uit benchmarkresultaten en door CI naar de Wiki geschreven.
