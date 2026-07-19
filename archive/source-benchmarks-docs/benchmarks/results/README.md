# Benchmark Results

Deze map is de vaste opslaglocatie voor benchmarkuitkomsten, voorbereidende runnotities en afgeleide JSON-resultaten.

## Huidige fase

- standaardstatus: `benchmarkvoorbereiding`
- execution-gap mag expliciet als `true` blijven staan zolang de runnerroute niet hard is bevestigd

## Gebruik

- sla voorbereidingsresultaten op als JSON volgens `result_schema.json`
- gebruik de map ook voor handmatige rapportuitvoer uit `scripts/run_absencebench.py` of latere adapters
- claim geen `echte benchmarkrun` zonder geverifieerde host en runner

## Minimale inhoud per resultbestand

- benchmarknaam
- runtype
- executionstatus
- SSL-inputbasis
- hostplatform
- datasetstatus
- runnerstatus
- score of `null`
- interpretatie
- beperkingen
- execution-gap
- timestamp
