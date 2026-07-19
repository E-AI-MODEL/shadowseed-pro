# Benchmark Results

Dit document beschrijft hoe benchmarkresultaten in deze repo worden opgeslagen en gelezen.

## Doel

Resultaten moeten reproduceerbaar, machineleesbaar en methodologisch eerlijk zijn.

## Resultaatschema

De vaste JSON-vorm staat in `benchmarks/results/result_schema.json`.

Daarin zijn minimaal verplicht:

- `benchmark_name`
- `run_type`
- `execution_status`
- `ssl_input_basis`
- `host_platform`
- `dataset_status`
- `runner_status`
- `score`
- `score_type`
- `interpretation`
- `limitations`
- `execution_gap`
- `timestamp`

## Belangrijke regel

Als een benchmark nog niet echt uitvoerbaar is, dan mag:

- `run_type` op `benchmarkvoorbereiding` staan
- `execution_gap` op `true` staan
- `score` op `null` staan

Dat is in deze fase correcter dan een schijnprecisie met een fictieve runscore.

## Opslaglocatie

- JSON-resultaten: `benchmarks/results/`
- voorbereidende runmetadata: `runs/` of `benchmarks/results/`
- benchmarkspecifieke documentatie: `benchmarks/absencebench/`
