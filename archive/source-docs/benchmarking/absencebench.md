# AbsenceBench voor Shadow Seed Learning 4.5

Dit document beschrijft hoe AbsenceBench binnen deze repo aan SSL 4.5 wordt gekoppeld.

## Waarom deze benchmark

AbsenceBench is de meest logische eerste benchmark omdat hij het dichtst aansluit op SSL's detection-pass:

- zoeken naar afwezigheid in plaats van alleen aanvullen
- vergelijken van baseline versus expliciete SSL-sturing
- observeren van failure modes rond gemiste structurele relaties

## SSL-koppeling

| Benchmarkonderdeel | SSL-koppeling |
|---|---|
| absence detection | Detection-Pass |
| te brede outputs | seed-normalisatie |
| consistente herdetectie | trace-opbouw |
| steun over meerdere interacties | Validation Gate |
| vervolgactie | Socratische, retrieval- of dialectische probe |

## Huidige status

- executionstatus: `benchmarkvoorbereiding`
- execution-gap aanwezig: `ja`
- runnerstatus: `te verifiëren`

## Voorwaarden voor opwaardering naar echte benchmarkrun

1. actuele runnerroute is geverifieerd
2. startcommando's voor baseline en SSL-conditie zijn expliciet vastgelegd
3. model en provider zijn gekozen
4. score-output en rapportstructuur zijn vastgelegd
5. de repo-route is niet outdated

## Eerste repo-doel

Deze repo maakt dus eerst de benchmark **klaar voor uitvoering**, niet afgerond in uitvoering.
