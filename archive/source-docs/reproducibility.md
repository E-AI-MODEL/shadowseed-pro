# Reproduceerbaarheid

Een SSL-run moet later reconstrueren hoe een seed is gedetecteerd, genormaliseerd, gevalideerd en eventueel gepromoveerd.

## Per run minimaal vastleggen

- datum en tijd
- benchmark of fase
- modelnaam
- modelversie als beschikbaar
- provider
- promptversie
- inputtekst of benchmarksubset
- eerste antwoord
- ruwe detectie-output
- genormaliseerde seeds
- score of beoordelingsuitkomst
- reviewer of beoordelaar
- opmerkingen

## Configuratievelden voor de manager

Leg minimaal deze waarden vast:

- `half_life_turns`
- `dedup_threshold`
- `promotion_threshold`
- `dormant_threshold`
- `validation_increment`
- `contradiction_penalty`
- embeddingmodel of embeddingfunctie
- LLM-model

## Aanbevolen runstructuur

```text
runs/
├── absencebench/
│   ├── preparation.json
│   ├── raw_outputs.jsonl
│   ├── normalized_seeds.jsonl
│   ├── scores.jsonl
│   └── analysis.md
└── phase_experiments/
    ├── validation_gate_events.jsonl
    └── probes.jsonl
```

## Praktische regels

- verwijder mislukte runs niet
- markeer failed runs expliciet
- bewaar ruwe output naast samenvattingen
- scheid score van interpretatie
- noteer waarom een seed gepromoveerd of afgewezen werd

## Randomness

Wanneer randomisatie wordt gebruikt, leg de seed vast:

```python
RANDOM_SEED = 42
```

## Benchmarkspecifieke no-claim regel

Voor AbsenceBench geldt in deze repo:

- geen claim van een echte benchmarkrun zonder geverifieerde runner
- geen fictief startcommando
- geen scoreclaim zonder traceerbare output
