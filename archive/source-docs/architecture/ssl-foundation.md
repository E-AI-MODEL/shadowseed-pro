# SSL Foundation

Dit document vat de architectonische basis van Shadow Seed Learning 4.5 samen voor deze repo.

## Eén-zinsclaim

Shadow Seed Learning gebruikt kleine structurele afwezigheden als startpunt voor gericht verder zoeken, maar laat alleen gevalideerde seeds invloed krijgen.

## Kernregels

1. Een seed bevat precies één gap.
2. `trace` meet aanwezigheid.
3. `weight` meet invloed.
4. `weight` start altijd op `0.0`.
5. brede detecties moeten eerst naar atomische seeds worden gesplitst.
6. promotie loopt via de Validation Gate.

## Trace en weight

### Trace

- beginwaarde: `2.0`
- betekenis: aanwezigheid in shadow memory
- gedrag: exponentieel verval
- onder `0.05`: operationeel dormant

### Weight

- beginwaarde: `0.0`
- betekenis: invloed op vervolgactie
- gedrag: stijgt alleen na validatie
- vanaf `0.5`: promoted seed

## Validation Gate

Een seed krijgt pas invloed als drie checks slagen:

1. interne herkenning
2. externe bevestiging
3. tegenspraak-test

## Probe-typen

- Socratische probe
- Retrieval probe
- Dialectische probe

## Niveau-1 implementatie in deze repo

Deze repo bouwt eerst Niveau 1 uit:

- tekstuele seeds
- embeddings voor deduplicatie en heractivatie
- lifecycle met `trace`, `weight` en statussen
- benchmarkvoorbereiding rond AbsenceBench

Modelinterne SSL-analyse hoort niet bij deze eerste repo-initialisatie.
