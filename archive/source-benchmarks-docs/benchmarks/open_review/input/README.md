# Open Review Input

Deze map is bedoeld voor kleine reviewbare inputbatches voor open-set seedkwaliteit.

## Bedoeling

Hier landt een eerste genormaliseerde batch onbekende teksten voordat `run-open-set-seed-review` wordt gedraaid.

## Aanbevolen route

```bash
shadowseed fetch-open-set-hf-batch \
  --source-id ag_news_test \
  --output benchmarks/open_review/input/hf_ag_news_test_batch.json

shadowseed run-open-set-seed-review \
  --input benchmarks/open_review/input/hf_ag_news_test_batch.json \
  --output results/open_set_seed_output.json \
  --review-packets results/open_set_review_packets.json
```

## Wat hier wel hoort

- kleine batches voor review
- duidelijke metadata over dataset, split en offset
- batches die handmatig beoordeeld kunnen worden

## Wat hier niet hoort

- grote ruwe upstream downloads
- onbegrensde mirrors van Hugging Face datasets
- automatische CI-output
