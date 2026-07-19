# Open-set Review Round 003

> Status: **klaar voor menselijke review**
> Detector: `model` + `hf-transformers` (Qwen/Qwen2.5-1.5B-Instruct), v0.3c prompt
> Evidence layer: `open_set_seed_quality` (Laag C)
> Related: #41, #62, ADR 0001

## Wat dit is

Dit is de eerste open-set batch geproduceerd door een **echt taalmodel** dat
voldoet aan de 4.6 één-zinsclaim — niet door de regex-baseline (round 001) of
een template-baseline. Het model las 12 AG News test-items en stelde per item
voor welke structurele afwezigheden ontbreken.

- 12 items, 62 unieke seeds, 124 review-packets (62 seeds × reviewer_a + reviewer_b)
- alle packets staan op `pending`
- gegenereerd tegen de v0.3c prompt (vreemd-domein few-shot + leak-filter), dus
  de leakage van round 003b (Sven Jaschan in een pensioen-item) is weg

## Eerlijke kwaliteitswaarschuwing

Qwen-1.5B is een klein model. De output is **echt maar rommelig**:

- de meeste seeds zijn echte zin-vormige gap-observaties
- sommige zijn een mix van Nederlands en Engels (het model echoot soms de
  brontaal)
- enkele zijn zwak of triviaal (bijvoorbeeld een los "Nee.")
- de batch is nog 12/12 nieuws/Sci-Tech (offset 0) — geen domein-spreiding

Dit is precies waarom menselijke review nodig is: de cijfers van het model
zeggen niets, jullie oordeel wel. Een hoog afwijspercentage is een geldige
uitkomst, geen mislukking.

## Hoe in te vullen

Elke reviewer bewerkt **alleen het eigen bestand**:

- `reviewer_a_packets.csv` (62 rijen)
- `reviewer_b_packets.csv` (62 rijen)

Per rij invullen:

- `review_status`: `accepted` of `rejected`
- vijf booleans (`atomicity`, `relevance`, `testability`, `non_triviality`,
  `follow_up_utility`): `true` of `false`
- `reject_reason`: één code uit de lijst hieronder als `rejected`, leeg als `accepted`
- `reviewer_notes`: korte tekst

De CSV is een werkkopie. De canonieke artefact is
`open_set_review_packets.json`; ingevulde rijen moeten daar via `packet_index`
terug naartoe voordat de summary draait.

### Reject codes

`too_broad`, `too_vague`, `trivial`, `not_relevant`, `not_testable`,
`duplicate`, `style_not_gap`

(En, gezien dit een modelrun is, let extra op: `not_dutch` / taalmenging mag je
als `style_not_gap` afwijzen met een notitie.)

## Na het invullen

Merge de ingevulde CSV-rijen terug in `open_set_review_packets.json` en draai:

```bash
shadowseed summarize-open-set-seed-review \
  --input benchmarks/open_review/rounds/round_003/open_set_review_packets.json \
  --output results/open_review/open_set_seed_review_summary.json \
  --disagreements-output results/open_review/open_set_disagreements.json \
  --report-output results/open_review/open_set_review_report.md
```

## Claim-grens

Toegestaan na een geldige ronde:

> Een eerste menselijk gereviewde open-set seed-quality sample met een echt
> taalmodel-detector bestaat.

Niet toegestaan:

> SSL is bewezen beter op open data.
