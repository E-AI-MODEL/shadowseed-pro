# Reproduceerbaarheid

## Doel

Een SSL-run moet later te reconstrueren zijn. Bewaar daarom niet alleen eindcijfers, maar ook ruwe output, prompts, parameters en beslissingen.

## Per run vastleggen

Leg per run minimaal vast:

- datum en tijd
- modelnaam
- modelversie als die beschikbaar is
- promptversie
- scenario-ID
- inputtekst
- eerste antwoord
- ruwe detectie-output
- genormaliseerde seeds
- ground truth match
- score
- beoordelaar
- opmerkingen

## Runlog-template

| veld | voorbeeld |
|---|---|
| run_id | 2026-05-02_phase0_A_001 |
| phase | 0 |
| scenario_id | A |
| model | modelnaam |
| prompt_name | detection_pass_atomic |
| detected_seed | Koloniaal kapitaal als financieringsbron voor Britse fabrieksinvesteringen. |
| score | 2 |
| reviewer | reviewer_01 |
| notes | financiële relatie expliciet |

## Bestanden bewaren

Bewaar deze bestanden per fase:

```text
runs/
├── phase0/
│   ├── raw_llm_outputs.jsonl
│   ├── normalized_seeds.jsonl
│   ├── scoring.csv
│   └── analysis.md
├── phase1/
│   ├── conversations.jsonl
│   ├── ssl_states.jsonl
│   └── scoring.csv
└── phase2/
    ├── validation_gate_events.jsonl
    ├── probes.jsonl
    └── scoring.csv
```

## Random seeds

Wanneer scripts randomisatie gebruiken, leg de seed vast:

```python
RANDOM_SEED = 42
```

## Parameters loggen

Leg deze waarden vast:

- `half_life_turns`
- `dedup_threshold`
- `promotion_threshold`
- `dormant_threshold`
- `validation_increment`
- embeddingmodel
- LLM-model

## Failed runs bewaren

Verwijder mislukte runs niet. Markeer ze als failed en noteer waarom.

Voorbeelden:

- prompt gaf brede outputs
- JSON kon niet worden geparsed
- beoordelaars waren het sterk oneens
- model gaf geen atomische seeds

## Minimale metadata in JSONL

```json
{
  "run_id": "2026-05-02_phase0_A_001",
  "phase": 0,
  "scenario_id": "A",
  "model": "modelnaam",
  "prompt_name": "detection_pass_atomic",
  "raw_response": "...",
  "normalized_seeds": ["..."],
  "scores": {"A1": 2},
  "created_at": "2026-05-02T12:00:00"
}
```

## Analyse

Rapporteer niet alleen gemiddelden. Rapporteer ook:

- aantal items
- aantal beoordelaars
- scoreverdeling
- voorbeelden van score 0, 1 en 2
- interbeoordelaarsovereenstemming als er meerdere beoordelaars zijn
- duidelijke no-go redenen

## Praktische regel

Als je over zes maanden niet kunt zien waarom een seed promoveerde, is de run onvoldoende gedocumenteerd.
