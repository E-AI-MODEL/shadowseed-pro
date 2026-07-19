# Blind review protocol

> Status: secundair protocol. Dit document is nuttig voor handmatige review, maar is niet de primaire statusbron. Gebruik voor de laatste resultaten eerst [Latest Test Results](Latest-Test-Results) en [SSL 4.5 Analysis](SSL-45-Analysis).

Blind review is nodig om te voorkomen dat beoordelaars automatisch het SSL-antwoord beter vinden omdat ze weten dat het SSL is.

## Doel

Beoordeel of een antwoord inhoudelijk beter is, zonder te weten welke conditie het is:

```text
baseline
SSL-guided rewrite
```

## Waar staan de review-items?

Model benefit output kan reviewvelden bevatten zoals:

```text
blind_review_items
blind_answer_key
```

Gebruik eerst alleen:

```text
blind_review_items
```

Gebruik de key pas na de beoordeling.

## Beoordeling per item

Vul per scenario in:

| Veld | Waarde |
|---|---|
| better_answer | `A`, `B` of `tie` |
| gap_coverage_a_0_5 | score 0-5 |
| gap_coverage_b_0_5 | score 0-5 |
| unsupported_claims_a_0_5 | score 0-5 |
| unsupported_claims_b_0_5 | score 0-5 |
| notes | korte toelichting |

## Richtlijn voor scores

### Gap coverage

| Score | Betekenis |
|---:|---|
| 0 | mist alle structurele gaps |
| 1 | raakt één punt vaag |
| 2 | raakt enkele punten, maar onvolledig |
| 3 | dekt meerdere gaps redelijk |
| 4 | dekt bijna alles goed |
| 5 | dekt alle verwachte gaps helder en specifiek |

### Unsupported claims

| Score | Betekenis |
|---:|---|
| 0 | geen unsupported claims |
| 1 | klein twijfelachtig detail |
| 2 | enkele onduidelijke claims |
| 3 | meerdere zwakke of niet-gedekte claims |
| 4 | veel unsupported claims |
| 5 | antwoord is sterk vervuild door ongedekte claims |

## Belangrijk

Beloon geen lengte op zichzelf.

Een langer antwoord is alleen beter als het:

- meer gevalideerde gaps dekt;
- geen nieuwe ongedekte claims toevoegt;
- duidelijker wordt zonder te verwateren.

## Na beoordeling

Vergelijk de ingevulde scores met:

```text
blind_answer_key
```

Daarna kun je bepalen of SSL vaker wint dan baseline.
