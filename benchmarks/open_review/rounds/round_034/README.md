# Round 034 — gebruiksdemping (TrTL op use-time): bouwen en blind hertesten

> **Status: INGREEP GEBOUWD, hertest nog niet gedraaid.** Doel: de laatste
> gemeten hinderbron dichten — en dit keer in SSL's eigen taal. Round 031
> localiseerde het falen precies: dezelfde matig passende seed stuurde
> twee opeenvolgende late beurten (inclusiviteit op EDU-t05+t06,
> lokale kennis op POLICY-t05+t06) — 8/14 hinder-labels, terwijl de
> vroege beurten juist doctrine-conform waren geworden.

## De ingreep: gebruik verbruikt trace

De eerdere fix-kandidaat was een mechanische "cooldown" (seed mag even
niet). Op aanwijzing van de maintainer is dat vervangen door de
doctrine-native vorm, geredeneerd vanuit weight en TrTL:

- **TrTL zegt al hoe terugkeer hoort**: een dormante seed komt terug via
  herkenning in de níeuwe input — niet op krediet uit het verleden. Het
  round-031-falen was precies een seed die doorleefde op eerdere
  relevantie.
- **Dus: gebruik verbruikt trace.** Een seed die net een antwoord heeft
  gestuurd krijgt op de dírect volgende beurten een hogere surfacing-lat
  (`--resurface-margin`, default 0.15), **halverend per beurt** sinds de
  laatste surfacing. Terugkomen kan meteen — maar alleen via een verse,
  sterkere fit met de nieuwe vraag.
- **Wat er bewust níet gebeurt**: weight blijft onaangeroerd (invloed
  verandert uitsluitend via de Validation Gate); beurten worden nooit
  geblokkeerd (het blijft fit-selectie, zoals de vroege-beurt-marge); de
  seed wordt niet gedempt als hij níet gebruikt is.

Deterministisch getest: zonder demping stuurt een sim-0.35-seed elke beurt
na promotie; met demping nooit twee beurten op rij, mét terugkeer zodra de
extra lat is weggeëbd; de eerste surfacing blijft ongemoeid; de parameter
staat per conversatie te overriden en in `applied_thresholds`.

## Run-recept voor de blinde hertest

```text
workflow: Research · SSL Benefit (OpenAI)
experiment: ssl-session
model_id: gpt-4o                # zelfde model als rounds 029/031
recurrence_mode: cluster
input_path: src/shadowseed/data/ssl_session_transfer_suite.json
max_new_tokens: 1600
review_prefix: ssl_session_blind_ab
```

De nieuwe demping-default geldt automatisch. Protocol: ≥2 onafhankelijke
blinde reviewers, seed-effect-labels, answer key in quarantaine, beide
sheets als CSV gecommit, seed-gecontroleerd rapporteren (welke seeds
promoveerden — de round-031-confound).

## Leesregel (vooraf vastgelegd, drie standen)

1. **Geslaagd** als de hinder-labels (ruis/vernauwt) op late beurten
   substantieel dalen t.o.v. round 031 (8/14) zónder dat er nieuwe hinder
   op vroege beurten ontstaat. Winnen hoeft niet: niks en ondersteunend
   zijn goede uitkomsten; alleen hinderen is de faalstand.
2. De winnaar-as wordt gerapporteerd maar is nevengeschikt (twee assen).
3. Uitkomst eerlijk gedocumenteerd, ook als de demping te bot blijkt
   (bv. de HEALTH-winst dempt mee) — dan is dát de bevinding en volgt
   kalibratie van de marge, niet van de leesregel.

## Claimgrens

Dit is een disciplinestap plus meetplan, geen resultaat. Tot de blinde
hertest binnen is, blijft de round-031-lezing staan: late-beurt-herhaling
is gelokaliseerd maar nog niet aantoonbaar gedicht.
