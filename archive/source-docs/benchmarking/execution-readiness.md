# Execution Readiness

Dit document beschrijft wanneer `shadowseed` een benchmarklane als scan, voorbereiding of echte run behandelt.

## Drie toestanden

1. `benchmarkscan`
2. `benchmarkvoorbereiding`
3. `echte benchmarkrun`

## Beslisregels

### Benchmarkscan

Gebruik deze toestand wanneer:

- je vooral host, dataset of runner inventariseert
- execution nog duidelijk onzeker is
- je geen live benchmark wilt of kunt starten

### Benchmarkvoorbereiding

Gebruik deze toestand wanneer:

- dataset, paper en runnerbron zichtbaar zijn
- runnerstructuur aanwezig is
- maar live verificatie of end-to-end mapping nog ontbreekt

### Echte benchmarkrun

Gebruik deze toestand alleen wanneer:

- host hard is geverifieerd
- runner hard is geverifieerd
- execution-gap afwezig is
- startcommando, provider en outputmapping zijn bevestigd

## AbsenceBench-status op 2 mei 2026

Voor `shadowseed` blijft AbsenceBench in fase 3:

- inhoudelijk uitvoerbaar voorbereid
- operationeel nog niet live bevestigd
- dus minimaal `benchmarkvoorbereiding`

Als een gebruiker toch live aanvraagt zonder harde verificatie, dan moet de repo terugvallen naar een eerlijke readiness-uitkomst in plaats van een nep-run.
