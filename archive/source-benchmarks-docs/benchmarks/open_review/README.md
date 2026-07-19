# Open Review Workspace

Deze map is bedoeld voor de eerste echte open-set seedkwaliteitslaag.

## Doel

Beoordelen of SSL op onbekende teksten kleine, relevante, toetsbare en niet-triviale seeds produceert zonder vaste seedlijst.

## Reviewprotocol

Gebruik voor de eerste echte human-reviewronde het protocol in:

```text
docs/research/open-set-review-protocol.md
```

Dat protocol legt vast:

- reviewer-ID's;
- één packetrij per reviewer per seed;
- accept- en rejectregels;
- vaste reject-codes;
- de vijf reviewcriteria;
- hoe disagreements bewaard worden;
- wanneer `#41` echt klaar is.

## Verwachte inputvorm

- kleine batch onbekende teksten
- meerdere domeinen
- meerdere tekstvormen
- geen vooraf uitgeschreven expected seedlijst als primaire waarheid

Een praktische eerste route is nu beschikbaar via Hugging Face intake:

```bash
shadowseed fetch-open-set-hf-batch \
  --source-id ag_news_test \
  --output benchmarks/open_review/input/hf_ag_news_test_batch.json
```

Daarna kan dezelfde batch direct de reviewflow in. Standaard maakt de generator twee pending reviewrijen per seed: `reviewer_a` en `reviewer_b`.

```bash
shadowseed run-open-set-seed-review \
  --input benchmarks/open_review/input/hf_ag_news_test_batch.json \
  --output results/open_review/open_set_seed_output.json \
  --review-packets results/open_review/open_set_review_packets.json
```

Gebruik desgewenst expliciete reviewer-ID's:

```bash
shadowseed run-open-set-seed-review \
  --input benchmarks/open_review/input/hf_ag_news_test_batch.json \
  --output results/open_review/open_set_seed_output.json \
  --review-packets results/open_review/open_set_review_packets.json \
  --reviewer-id reviewer_a \
  --reviewer-id reviewer_b
```

Vul daarna de afzonderlijke reviewer-rijen in. Laat twee reviewers nooit dezelfde packetrij overschrijven.

```bash
shadowseed summarize-open-set-seed-review \
  --input results/open_review/open_set_review_packets.json \
  --output results/open_set_seed_review_summary.json \
  --disagreements-output results/open_review/open_set_disagreements.json \
  --report-output results/open_review/open_set_review_report.md
```

## Verwachte artifacts

- `results/open_review/open_set_seed_output.json`
- `results/open_review/open_set_review_packets.json`
- `results/open_set_seed_review_summary.json`
- `results/open_review/open_set_disagreements.json`
- `results/open_review/open_set_review_report.md`

## Reviewkern

Iedere seed moet uiteindelijk beoordeeld kunnen worden op:

- atomiciteit
- relevantie
- toetsbaarheid
- niet-trivialiteit
- bruikbaarheid voor vervolgactie

Voor de eerste reviewronde geldt: `accepted` alleen als alle vijf criteria slagen. Bij `rejected` hoort precies één vaste `reject_reason`; aanvullende redenen gaan in `reviewer_notes`.

## Belangrijke interpretatieregel

Deze laag is een aparte evidencelaag.

Lees hem dus niet als:

- uitbreiding van de standaard regressiescore
- vervanging van de benchmark-harness

Lees hem wel als:

- eerste open-set kwaliteitslaag bovenop de mechanische regressieruggengraat
- expliciete stap weg van vaste scenario-seeds
- aparte bron voor acceptance, disagreement en seedkwaliteit

## Grens

Deze map is geen nieuwe scenario-suite.

Het doel is juist de stap weg van:

- vaste scenario seeds

naar:

- blind beoordeelbare seedkwaliteit in onbekende context
