# Benchmark-register

Dit register is de vaste benchmarkbibliotheek voor deze Shadow Seed Learning 4.5-repo.

## Doel

- vastleggen welke benchmarks relevant zijn voor SSL 4.5
- koppelen van benchmarks aan concrete SSL-onderdelen
- status en bronroute expliciet maken
- voorkomen dat benchmarkwerk buiten vaste lablogica om gebeurt

## Benchmarks

| Benchmark | Primaire SSL-koppeling | Rol in deze repo | Verwachte bron | Status | Opmerking |
|---|---|---|---|---|---|
| AbsenceBench | Detection-Pass / geometrie van afwezigheid | eerste execution-lane | Hugging Face dataset + GitHub-code | in gebruik | default startbenchmark |
| GAIA | structurele gaps / multi-step ambiguity | latere verbreding | Hugging Face leaderboard of repo | in bibliotheek | pas na hardere execution-route |
| LLM Spark | Validation Gate | latere validatielaag | externe repo of paperbron | te verifiëren | nuttig voor flawed-information tests |
| PTF-ID-Bench | Active Probing / escalatie | latere escalatietest | externe repo of paperbron | te verifiëren | relevant voor mens-escalatiegedrag |
| AMA-Bench | JSON-state / geheugencontinuïteit | latere geheugentest | externe repo of paperbron | te verifiëren | relevant voor state-updates |
| MR-Ben | meta-redeneren | latere interpretatietest | externe repo of paperbron | te verifiëren | relevant voor foutanalyse |

## Fase-3 status voor AbsenceBench

Op 2 mei 2026 geldt in deze repo:

- dataset aanwezig op Hugging Face
- paper aanwezig op Hugging Face Papers
- runnerrepo aanwezig op GitHub
- runnerstructuur zichtbaar via README en `evaluate.py`
- execution-gap blijft aanwezig totdat end-to-end uitvoering en outputmapping harder zijn bevestigd

## Outdated-repo regel

Een outdated repo telt nooit als geldige runner.

Bij zo'n signaal moet de benchmarklane minimaal vastleggen:

- `runner_status = outdated`
- `execution-gap aanwezig`
- `execution_status != echte benchmarkrun`
