# Reporting

Dit document beschrijft het verschil tussen scan-, voorbereidings- en benchmarkresultaten in `shadowseed`.

## Resultaattypen

### Scanresultaat

Doel:
- vastleggen of hosts en runnerbronnen aanwezig zijn
- execution-gap zichtbaar maken

Typische velden:
- `run_type = benchmarkscan`
- `score = null`
- `execution_gap = true`

### Voorbereidingsresultaat

Doel:
- readiness vastleggen
- runkaart en verificatie koppelen
- rapporteren wat nog ontbreekt

Typische velden:
- `run_type = benchmarkvoorbereiding`
- `score = null`
- `limitations` gevuld met missende operationele componenten

### Echte benchmarkresultaat

Doel:
- echte benchmarkoutput vastleggen
- score, scoretype en interpretatie opslaan

Dit type mag alleen worden gebruikt wanneer host en runner echt zijn geverifieerd.

## Voorbeeldbestanden

- `benchmarks/results/example_scan.json`
- `benchmarks/results/example_result.json`

## No-claim regel

Als de executionstatus nog niet hard genoeg is, blijft `score` leeg en blijft de rapportlaag eerlijk over de execution-gap.
