# Round 029 — reviewer 2: onafhankelijke blinde scoring, instemming met r1

> Status: vastgelegd 2026-07-07, gerapporteerd door de maintainer.

## Methode

Reviewer 2 heeft **hetzelfde blinde pack** (run 28710838639, artifact
8082998649, digest `756e672e…`) **zelfstandig gescoord, zónder r1's oordelen
of de answer key te zien**, en kwam per item op **dezelfde uitkomsten** als
reviewer 1: dezelfde winnaarkeuzes én dezelfde seed-effect-richting.

Daarmee is de tabel in `RESULTS.md` inhoudelijk een consensus-tabel — maar
**níet audit-gelijkwaardig aan round 025**: daar zijn beide sheets
(`r1_scores.csv` + `r2_scores.csv`) gecommit en narekenbaar, hier alleen r1's.
Round 029 blijft daarom een **voorlopig consensus-verdict onder
provenance-voorbehoud**; het wordt pas protocol-af zodra r2's eigen sheet als
`r2_scores.csv` is gecommit.

## Provenance-kanttekening (eerlijk)

- Reviewer 2's eigen ingevulde scoresheet is **niet als CSV gecommit**; de
  item-niveau-instemming is gerapporteerd door de maintainer na de
  onafhankelijke scoring. Wordt het sheet alsnog aangeleverd, dan hoort het
  hier als `r2_scores.csv` naast `r1_scores.csv`.
- De consensus-tellingen (winnaar-as 0.50; seed-effect 6/9 "helpt") zijn
  daarom gebaseerd op r1's gecommitte sheet, door r2 bevestigd — in de
  twee-assen-teltabel (`ssl-integrale-evaluatie.md`) blijven de round-029
  labels als 9 geteld (niet 18): instemming bevestigt, maar wordt niet
  dubbel geteld zonder eigen sheet.
