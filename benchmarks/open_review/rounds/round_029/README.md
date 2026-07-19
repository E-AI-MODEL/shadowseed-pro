# Round 029 — W10 transfer-replicatie op een tweede model (gpt-4o)

> **Status: VOORLOPIG VERDICT — 2 onafhankelijke blinde reviewers in
> consensus, onder provenance-voorbehoud: alleen r1's sheet is als CSV
> gecommit (zie `human_review/r2_concurrence.md`). Op de winnaar-as
> komt de replicatie zwakker terug dan round 025 (0.50; 2 seed-effect-labels
> 'veroorzaakt ruis' op t04, strikte noise-kolommen schoon); op de
> seed-effect-as helpt de seed óók hier in de meerderheid (6/9 "helpt",
> HEALTH 3/3) — zie `human_review/RESULTS.md`.** Doel: het round-025 transfer-verdict (voorzichtig positief, gpt-4.1)
> onafhankelijk repliceren op een ander modelgeslacht (gpt-4o), zodat laag F
> steviger wordt dan "één model, n=7".

## Run-recept

```text
workflow: Research · SSL Benefit (OpenAI)
experiment: ssl-session
model_id: gpt-4o
recurrence_mode: cluster
input_path: src/shadowseed/data/ssl_session_transfer_suite.json
max_new_tokens: 1600            # zelfde afkap-vrije budget als round 025
review_prefix: ssl_session_blind_ab
```

## Runverwijzing

```text
run_id: 28710838639            # main @ 186f3ed, conclusion: success
artifact: ssl-openai-ssl-session-gpt-4o (id 8082998649)
artifact_digest: sha256:756e672efa827b528721422da80387789d53f68144cd895da20081f31ffee0f3
```

## Wat uit de job-log blijkt (kwalitatief)

- **Het cross-turn mechanisme vuurt óók op gpt-4o.** Voorbeeld CONV_POLICY t6:
  twee eerder-geboren seeds surfacen ("Sociale rechtvaardigheid als lens voor
  kwetsbare gemeenschappen" + "Innovatieve financieringsmodellen") en zijn
  zichtbaar geweven in het SSL-antwoord (sociale rechtvaardigheid + groene
  obligaties/publiek-private samenwerking), terwijl de baseline die punten niet
  noemt. Dat is precies het beoogde "sturen bij aanscherping" op de t6-vraag.
- Antwoorden eindigen op volledige `**Conclusie:**`-alinea's (geen
  mid-zin-afkap in de gelezen voorbeelden) — indicatie dat het 1600-budget de
  afkap laag houdt, zoals round 025.

## Klaar wanneer (analoog aan round 025) — grotendeels afgerond 2026-07-07; open: r2-sheet committen

1. **Vóór de review**: download het artifact (id 8082998649), verifieer de
   digest, en controleer in de summary dat
   `truncation.items_with_likely_truncated_answer` (vrijwel) leeg is en tel de
   cross-turn events. De exacte getallen staan in het artifact, niet hier —
   deze README claimt ze niet.
2. **Blinde review**: ≥2 reviewers, per domein, met seed-effect- en
   ruis/vernauwing-labels; unblinding via de canonieke answer key (seed 45)
   ná scoring.
3. **Verdict**: per-domein rapportage, geen totaalscore. Vergelijk met round
   025 (gpt-4.1): consistente cross-domein voorkeur voor de SSL-kant op de
   valkuil/aanscherpingsvragen zou het "voorzichtig positief" van laag F
   verstevigen naar "gerepliceerd over twee modellen".

## Claimgrens

De blinde review is gedaan (2 reviewers, consensus) en het voorlopige verdict
staat in `human_review/RESULTS.md`: geen head-to-head-replicatie van round 025
op gpt-4o (winnaar-as 0.50), wél replicatie van het seed-effect in de
meerderheid (6/9 "helpt", HEALTH 3/3), met vroege-beurt off-topic-sturing als
specifiek zwak punt. Grenzen: n=9 items, auteur-gekozen thema's, en — anders
dan round 025 — is r2's eigen sheet niet als CSV gecommit
(`r2_concurrence.md`), dus het verdict blijft voorlopig tot dat hersteld is.
