# SLM-runs

Deze pagina beschrijft echte kleine taalmodel-runs voor SSL 4.5.

## Doel

Een SLM-run test:

```text
zelfde model zonder SSL
vs
zelfde model met SSL-guided rewrite
```

Het model blijft hetzelfde. Alleen de gevalideerde SSL-seeds worden toegevoegd als revisiesignaal.

## Handmatig starten

Ga naar:

```text
Actions → SLM Model Benefit Run → Run workflow
```

Standaardinstellingen:

| Veld | Waarde |
|---|---|
| `model_id` | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` |
| `turns` | `3` |
| `max_new_tokens` | `220` |

## Output

Artifacts:

```text
ssl45-slm-model-benefit-results
ssl45-slm-analysis-report
```

Wiki-pagina's:

```text
SLM-Model-Benefit
SLM-Model-Benefit-Analysis
SLM-Model-Benefit-Analysis-Summary
SLM-Model-Benefit-Raw
```

## Metrics

| Metric | Betekenis |
|---|---|
| `baseline_mean_gap_coverage` | dekking zonder SSL |
| `ssl_mean_gap_coverage` | dekking met SSL-guided rewrite |
| `coverage_delta` | verschil tussen SSL en baseline |
| `mean_answer_length_delta_words` | hoeveel woorden SSL gemiddeld toevoegt |
| `coverage_delta_per_100_added_words` | verbetering gecorrigeerd voor lengte |
| `unsupported_ssl_addition_rate` | aandeel unsupported SSL-toevoegingen |

## Eerlijke conclusie

Een goede SLM-run toont niet alleen dat het SSL-antwoord langer is.

Een goede run toont:

```text
hogere gap coverage
zonder hogere unsupported addition rate
bij hetzelfde model
```

## Als GitHub faalt

GitHub-hosted runners kunnen te weinig geheugen of tijd hebben. Draai dan lokaal:

```bash
pip install -e ".[models]"

shadowseed run-model-benefit-suite \
  --backend hf-transformers \
  --model-id TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --turns 3 \
  --max-new-tokens 220

shadowseed analyze-results
```
