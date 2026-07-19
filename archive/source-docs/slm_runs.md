# SLM-runs

Deze pagina beschrijft hoe je een echte kleine taalmodel-run uitvoert voor SSL 4.5.

## Doel

De SLM-run vergelijkt hetzelfde model in twee condities:

```text
baseline: vraag direct beantwoorden
SSL: baseline-antwoord herzien met gevalideerde SSL-seeds
```

Het model blijft hetzelfde. Alleen SSL-guidance verandert.

## Handmatig starten in GitHub Actions

Ga naar:

```text
Actions → SLM Model Benefit Run → Run workflow
```

Vul in:

| Veld | Voorbeeld |
|---|---|
| `model_id` | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` |
| `turns` | `3` |
| `max_new_tokens` | `220` |

Klik daarna op **Run workflow**.

## Output artifacts

Na afloop krijg je:

```text
ssl45-slm-model-benefit-results
ssl45-slm-analysis-report
```

Het eerste artifact bevat de ruwe modelvergelijking:

```text
results/ssl45_model_benefit_suite.json
```

Het tweede artifact bevat:

```text
analysis_report.md
analysis_summary.json
coverage.svg
false_positive.svg
```

## Belangrijke metrics

| Metric | Betekenis |
|---|---|
| `baseline_mean_gap_coverage` | dekking zonder SSL |
| `ssl_mean_gap_coverage` | dekking met SSL-guided rewrite |
| `coverage_delta` | verbetering door SSL |
| `mean_answer_length_delta_words` | hoeveel langer SSL-antwoorden zijn |
| `coverage_delta_per_100_added_words` | verbetering gecorrigeerd voor extra lengte |
| `unsupported_ssl_addition_rate` | aandeel unsupported SSL-toevoegingen |

## Eerlijke interpretatie

Een goede SLM-run toont niet alleen dat SSL-antwoorden langer zijn.

Een goede run toont:

```text
hogere gap coverage
zonder hogere unsupported addition rate
bij hetzelfde model
```

## Aanbevolen eerste model

```text
TinyLlama/TinyLlama-1.1B-Chat-v1.0
```

Dit model is klein genoeg om als eerste gratis test te proberen. De run kan traag zijn op CPU.

## Let op

GitHub-hosted runners hebben beperkte CPU, RAM en tijd. Als een model-run faalt door geheugen of timeout, gebruik dan lokaal dezelfde CLI:

```bash
pip install -e ".[models]"

shadowseed run-model-benefit-suite \
  --backend hf-transformers \
  --model-id TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --turns 3 \
  --max-new-tokens 220

shadowseed analyze-results
```

## Alternatief: Ollama-backend (lichter in een runner)

De `ollama`-backend praat over HTTP met een lokale Ollama-server in plaats van
de modelgewichten in-process te laden. Ollama gebruikt gekwantiseerde
GGUF-modellen, dus dit is veel lichter dan de `transformers`/`torch`-stack en
heeft geen extra Python-deps nodig — handig om SSL in een (standaard) runner te
draaien.

### In GitHub Actions

Ga naar:

```text
Actions → Research · SLM Model Benefit (Ollama) → Run workflow
```

Kies een model (bijv. `qwen2.5:0.5b-instruct`) en draai. De workflow installeert
Ollama, start de server, pullt het model en draait de suite met
`--backend ollama`.

### Lokaal

```bash
# 1. installeer Ollama (https://ollama.com) en start de server
ollama serve &

# 2. haal een klein model op
ollama pull qwen2.5:0.5b-instruct

# 3. draai de suite tegen Ollama (geen models-extra nodig)
pip install -e .

shadowseed run-model-benefit-suite \
  --backend ollama \
  --model-id qwen2.5:0.5b-instruct \
  --turns 3 \
  --max-new-tokens 220

shadowseed analyze-results
```

Wijst je Ollama-server elders? Zet dan `OLLAMA_HOST`, bijvoorbeeld
`export OLLAMA_HOST=http://192.168.1.10:11434`. De `ollama`-backend werkt ook
voor de open-set detector via `--detector model --model-backend ollama`.
