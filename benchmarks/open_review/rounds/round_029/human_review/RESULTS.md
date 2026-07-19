# Round 029 — W10 transfer-replicatie op gpt-4o: voorlopig consensus-verdict

> **Status: VOORLOPIG VERDICT (consensus onder provenance-voorbehoud).**
> Reviewer 2 scoorde hetzelfde pack zelfstandig blind en kwam per item op
> dezelfde uitkomsten, maar diens sheet is niet als CSV gecommit — auditeerbaar
> is alleen r1's sheet; definitief zodra `r2_scores.csv` er is
> (`r2_concurrence.md`). Op de
> winnaar-as reproduceert gpt-4o het round-025-verdict NIET schoon (win-rate
> 0.50) — dat begrenst de head-to-head-transferclaim. Op de seed-effect-as
> ("helpt de seed naar een beter antwoord?") is de consensus 6/9 "helpt", met
> de 2 ruis-labels geconcentreerd op de vroege t04-beurten en HEALTH 3/3
> schoon.

## Unblinding (geverifieerd)

Answer key gereproduceerd uit code (`scripts/make_blind_ab_review.py`,
`_balanced_ssl_a_assignments`, seed 45, **count 9**) en **onafhankelijk
bevestigd**: elke reviewer-motivatie noemt de extra invalshoek (ethiek,
psychologische factoren, sociale rechtvaardigheid, financiering) aan precies
de kant die de key als SSL aanwijst.

| Item | SSL-kant | winnaar (consensus r1=r2) | uitkomst | seed-effect |
|---|---|---|---|---|
| CONV_EDU-t04 | A | B | baseline | **veroorzaakt ruis** |
| CONV_EDU-t05 | A | gelijk | tie | geen verschil |
| CONV_EDU-t06 | B | A | baseline | helpt een beetje |
| CONV_HEALTH-t04 | A | A | **SSL** | helpt duidelijk |
| CONV_HEALTH-t05 | B | B | **SSL** | helpt duidelijk |
| CONV_HEALTH-t06 | A | A | **SSL** | helpt duidelijk |
| CONV_POLICY-t04 | A | B | baseline | **veroorzaakt ruis** |
| CONV_POLICY-t05 | B | B | **SSL** | helpt duidelijk |
| CONV_POLICY-t06 | B | A | baseline | helpt een beetje |

## Cijfers (consensus; r2 bevestigde r1 per item, zie `r2_concurrence.md`)

- **SSL 4 / baseline 4 / 1 tie → win-rate 4/8 = 0.50.**
- Per domein: **HEALTH 3/3 SSL** (schone winst), **EDU 0/2** (+1 tie),
  **POLICY 1/2**.
- **Seed-effect "veroorzaakt ruis" op 2 items** (EDU-t04, POLICY-t04), béide op
  de SSL-kant. **Let op de bron:** dit is het `seed_effect_after_choice`-label,
  níet de strikte noise-kolommen — die bleven schoon (`no_noise_A/B` = 5/5,
  `noise_or_hallucinated_relevance` leeg). Het gaat dus om **seed-gedreven
  off-topic-sturing/vernauwing**, niet om verzonnen ruis of hallucinatie.

## Twee assen — waarom "win-rate 0.50" niet de hele conclusie is

Het blinde A/B-formaat produceert *logischerwijs* een winnaar-metriek: de
reviewer moet A of B kiezen, ook als beide antwoorden goed zijn. Maar de
doctrine (`positioning-synthese.md`) stelt expliciet dat win-rate **nooit de
hoofdmetriek** is — de review is een kwaliteitscontrole op door SSL geopende
antwoordruimte. De vraag van de repo is niet "verslaat SSL de baseline?", maar
"**helpt SSL naar een beter antwoord?**". Dat zijn twee assen:

1. **Winnaar-as (A/B head-to-head):** SSL 4 / baseline 4 / 1 tie = 0.50.
   Interpretatie-nuance: de baseline is hier óók gpt-4o op z'n best; een
   50/50-uitkomst betekent "de seed-kant is even goed", niet "de seed schaadt".
2. **Seed-effect-as (`seed_effect_after_choice`):** **6/9 "helpt"** (4×
   duidelijk, 2× een beetje), 1× geen verschil, 2× veroorzaakt ruis — beide
   ruis-labels op de vroege t04-beurten. De use-time discipline stond dáár
   gewoon aan (hij draait op elke beurt); de cap voorkomt flooding, maar
   sluit off-topic-*sturing* door een gesurfacte seed niet uit.

Op de tweede as — de as waar de kernclaim op leeft — helpt de seed dus in de
meerderheid van de beoordelingen óók op gpt-4o, en is het probleem specifiek
en adresseerbaar (vroege-beurt-sturing), niet diffuus.

## Wat dit betekent (eerlijk)

1. **Zwakker dan round 025.** Op gpt-4.1 kozen de twee blinde reviewers elk
   ~5/7 (≈0.71) de SSL-kant. Op gpt-4o: win-rate 0.50, en 2 seed-effect-labels
   "veroorzaakt ruis" (waar round 025 er 0 had). De round-025-uitkomst was dus
   deels **gpt-4.1-specifiek** — transfer is modelafhankelijk.
2. **De off-topic-sturing zit op de t04-beurten.** De use-time discipline
   (round 023: `surface_top_k=2`, potentieel-geen-must) stond op élke beurt
   aan, óók op t04 — de runner past hem vóór elk surfacen toe
   (`ssl_session_suite.py`), en round 023/025 bevatten eveneens vroege
   events onder dezelfde defaults. Toch stuurde de seed juist op t04 het
   antwoord naar een minder relevante invalshoek (ethiek bij EDU-t04,
   financieringsmodellen bij POLICY-t04) — door de reviewer als
   *seed-effect* "veroorzaakt ruis" gelabeld, niet als hallucinatie (de strikte
   noise-kolommen bleven 5/5). De les is dus niet "t04 valt buiten de
   discipline", maar: de huidige cap/potentieel-prompt voorkomt flooding, maar
   sluit off-topic-*sturing* op vroege beurten niet uit — en gpt-4o weeft
   seeds daar mogelijk minder scherp in dan gpt-4.1.
3. **HEALTH transfereert wél schoon** (3/3, "helpt duidelijk" ×3): de
   psychologische-drijfveren-seed scherpt daar consistent aan. Transfer is dus
   niet alleen model- maar ook domeinafhankelijk.

## Verdict-status

**Laag F blijft "voorzichtig positief".** Op de winnaar-as begrenst deze ronde
de claim (head-to-head-winst draagt niet zonder meer over naar gpt-4o); op de
seed-effect-as bevestigt hij hem conditioneel (6/9 helpt, HEALTH 3/3 schoon).
De open kwestie is specifiek: de bestaande use-time discipline (die ook op t04
actief was) begrenst *hoeveel* seeds meesturen, maar niet *of* een gesurfacte
seed het antwoord off-topic stuurt op een vroege beurt.

**Verdict-basis:** 2 onafhankelijke blinde reviewers in consensus op alle 9
items — inhoudelijk hetzelfde protocol als round 025, maar **niet
audit-gelijkwaardig**: round 025 heeft beide sheets gecommit, hier alleen
r1's (`r2_concurrence.md`). Daarom een *voorlopig* verdict: de
head-to-head-winst van round 025 repliceert niet op gpt-4o (winnaar-as 0.50),
het seed-effect ("helpt") repliceert wél in de meerderheid (6/9), met een
specifiek, adresseerbaar zwak punt op de vroege beurten. Definitief zodra
r2's sheet als `r2_scores.csv` gecommit is.

## Bestanden

- `r1_scores.csv` — reviewer 1 (blind).
- `r2_concurrence.md` — reviewer 2: onafhankelijke blinde scoring, per item
  gelijk aan r1 (instemming; eigen sheet niet als CSV gecommit).
- Answer key: reproduceerbaar uit code (seed 45, count 9); geverifieerd tegen
  de seed-content in de motivaties. Canonieke key in het run-artifact
  (`ssl_session_blind_ab_answer_key.json`, run 28710838639, artifact 8082998649,
  digest `756e672e…`) — te openen ná de scoring.
