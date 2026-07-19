# Fase 2: model benefit suite

Deze suite test of hetzelfde model beter functioneert met SSL dan zonder SSL.

## Vraag

> Wordt een LLM of SLM beter als gevalideerde SSL-seeds de revisie sturen?

De suite vergelijkt dus niet model A met model B. De suite vergelijkt:

```text
zelfde model zonder SSL
vs
zelfde model met SSL-guided rewrite
```

## Waarom deze suite nodig is

De Gap-Test Suite test of SSL intern werkt:

- detectie
- atomische seeds
- trace
- weight
- Validation Gate
- promotie

De Model Benefit Suite test een andere vraag:

- verbetert het antwoord?
- worden ontbrekende structurele gaps toegevoegd?
- ontstaan er unsupported additions?
- is de verbetering meer dan alleen extra lengte?

## CLI

Snelle CI-smoke zonder modeldownload:

```bash
shadowseed run-model-benefit-suite --backend fixture
```

Echte lokale SLM-run:

```bash
pip install -e ".[models]"

shadowseed run-model-benefit-suite \
  --backend hf-transformers \
  --model-id <huggingface-model-id> \
  --max-new-tokens 220
```

Voorbeeld met een klein instruct-model:

```bash
shadowseed run-model-benefit-suite \
  --backend hf-transformers \
  --model-id TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
  --max-new-tokens 220
```

## Output

Standaard:

```text
results/ssl45_model_benefit_suite.json
```

Belangrijke velden:

| Veld | Betekenis |
|---|---|
| `baseline_mean_gap_coverage` | hoeveel verwachte gaps al in het eerste antwoord zitten |
| `ssl_mean_gap_coverage` | hoeveel verwachte gaps na SSL-revisie aanwezig zijn |
| `coverage_delta` | verschil tussen SSL en baseline |
| `mean_answer_length_delta_words` | hoeveel woorden SSL gemiddeld toevoegt |
| `coverage_delta_per_100_added_words` | verbetering gecorrigeerd voor extra lengte |
| `unsupported_ssl_additions` | gepromote toevoegingen die niet matchen met verwachte gaps |
| `unsupported_ssl_addition_rate` | unsupported additions gedeeld door promoted seeds |

## Blind review

De JSON bevat ook:

```text
blind_review_items
blind_answer_key
```

Gebruik `blind_review_items` voor menselijke beoordeling. Daarin staan antwoord A en B zonder dat de beoordelaar weet welke baseline of SSL is.

Gebruik `blind_answer_key` pas na de beoordeling.

Beoordeel per item:

- welk antwoord is beter: A, B of gelijk?
- gap coverage 0-5
- unsupported claims 0-5
- helderheid
- opmerkingen

## Belangrijk

Deze suite mag SSL niet reduceren tot “meer bullets toevoegen”. Daarom meet de runner ook lengteverschil en unsupported additions.

Een goed resultaat is niet:

```text
SSL-antwoord is langer
```

Een goed resultaat is:

```text
SSL-antwoord dekt meer gevalideerde gaps
zonder unsupported additions
met hetzelfde model
```

## Huidige status

- `fixture` backend draait in CI.
- `hf-transformers` backend is bedoeld voor echte lokale of aparte runner-runs.
- Resultaten moeten als artifacts worden opgeslagen voordat ze in `docs/results.md` worden opgenomen.
