# Benchmark-pipeline

Dit document beschrijft de vaste benchmark-pipeline voor deze Shadow Seed Learning 4.5-repo.

## Vaste benchmark-pipeline

1. **SSL-inputbasis bepalen**
   - gebruik `shadow_seed_learning_4_5_clean.md` als canonieke SSL SSOT
   - gebruik `ssl_4_5_public_release/` als operationele 4.5-uitwerking
   - benoem welk SSL-onderdeel wordt gebenchmarkt

2. **Benchmark kiezen**
   - kies benchmarkdoel
   - kies startbenchmark
   - default naar `AbsenceBench`

3. **Bron en host verifiëren**
   - controleer dataset, paper, repo of benchmarksite
   - leg `host_status` en `runner_status` vast

4. **Executionstatus bepalen**
   - classificeer het werk als precies één van:
     - `benchmarkscan`
     - `benchmarkvoorbereiding`
     - `echte benchmarkrun`

5. **Execution-gap bepalen**
   - markeer expliciet of een gap aanwezig is
   - outdated repos blokkeren direct de live runnerstatus

6. **Run- of analysepakket opstellen**
   - noteer gebruikte SSL-documenten
   - leg baseline- en SSL-conditie vast
   - leg startcommando of command-template vast

7. **Rapport en resultaatlaag vullen**
   - schrijf JSON-resultaten naar `benchmarks/results/`
   - scheid scan, voorbereiding en echte run

8. **Scoreduiding uitvoeren**
   - scheid ruwe score van interpretatie
   - claim geen SSL-validatie op basis van een niet-geverifieerde route
