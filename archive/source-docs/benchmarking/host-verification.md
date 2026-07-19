# Host Verification

Dit document beschrijft hoe `shadowseed` benchmarkhosts en runners controleerbaar beoordeelt.

## Doel

Een benchmarkhost mag niet alleen "bestaan"; hij moet als operationele route beoordeeld kunnen worden.

## Minimale verificatievelden

- benchmarknaam
- hostplatform
- repo of runnerbron
- runner_status
- host_status
- execution_status
- verificatie-opmerkingen
- execution_gap

## AbsenceBench in fase 3

Op **2 mei 2026** is in de repo vastgelegd dat:

- de Hugging Face dataset `harveyfin/AbsenceBench` publiek aanwezig is
- de Hugging Face paper `2506.11440` publiek aanwezig is
- de GitHub-repo `harvey-fin/absence-bench` publiek aanwezig is
- de upstream repo een zichtbare `evaluate.py`-entrypoint en README-evaluatie-instructie heeft

Dat is genoeg voor een **controleerbare readiness-route**, maar nog niet automatisch voor een `echte benchmarkrun`.

## Outdated-repo regel

Een outdated repo blokkeert direct de live runnerstatus.

Dan moet de verificatielaag minimaal vastleggen:

- `runner_status = outdated`
- `execution-gap aanwezig`
- `execution_status != echte benchmarkrun`

## Praktische uitkomst

Als host en runner wel zichtbaar zijn maar nog niet end-to-end zijn gevalideerd, dan blijft:

- `run_type = benchmarkvoorbereiding` of `benchmarkscan`
- `execution_status = execution-gap aanwezig` of `benchmarkvoorbereiding`
