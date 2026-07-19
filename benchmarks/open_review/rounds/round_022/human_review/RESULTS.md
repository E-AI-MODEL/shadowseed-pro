# Round 022 — W9f blind A/B review op VEILIGE drempels: gespleten oordeel

> **Status: eerste blinde review van W9f-cross-turn op veilige doctrine-drempels.
> Uitkomst: geen consensus.** Twee onafhankelijke reviewers scoorden hetzelfde
> blinde A/B-pack (8 cross-turn payoff items, gpt-4.1, `recurrence_mode=cluster`,
> veilige defaults). Ze kozen op **7 van de 8 items een andere winnaar**. Dit is
> niet de herhaling van de round-019-overeenstemming (2 reviewers, 92%/98%); op
> veilige drempels is het oordeel reviewer-afhankelijk.

## Opzet

- Bron: blind A/B-pack gegenereerd door `scripts/make_blind_ab_review.py` uit een
  `ssl-session` run (PR #150-tooling), gebalanceerde A/B-shuffle.
- 8 cross-turn payoff items: `CONV_STARTUP` t04/t05/t07/t08 en `CONV_CITY`
  t05/t06/t07/t08.
- Twee reviewers vulden **hetzelfde pack** (identieke A/B-volgorde — bevestigd
  doordat beide motivaties per letter dezelfde inhoud beschrijven).
- Reviewer A: NL, kritisch, vult `seed_effect_after_choice` met
  ruis/helpt-een-beetje/helpt-duidelijk. Reviewer B: EN-template,
  helps-clearly/a-bit/no-difference, `noise = low` op alle items.

> **Belangrijke kanttekening over de SSL-toewijzing.** De officiële
> `w9f_blind_ab_answer_key.json` is hier niet meegenomen; welke kant (A/B) de
> SSL- vs baseline-variant was, is **afgeleid uit de motivaties** (beide reviewers
> identificeren onafhankelijk dezelfde variant als de seed-gedreven). De
> *kop-bevinding* — reviewers oneens op 7/8 — staat los van die afleiding.

## De cijfers

| Item | Seed-variant (afgeleid) | Reviewer A kiest | Reviewer B kiest | Eens? | Reviewer A: seed-effect |
|---|:--:|:--:|:--:|:--:|---|
| CONV_STARTUP-t04 | B | A (baseline) | B (seed) | nee | ruis |
| CONV_STARTUP-t05 | B | B (seed) | B (seed) | **ja** | helpt duidelijk |
| CONV_STARTUP-t07 | A | B (baseline) | A (seed) | nee | helpt een beetje |
| CONV_STARTUP-t08 | A | B (baseline) | A (seed) | nee | helpt een beetje |
| CONV_CITY-t05 | A | B (baseline) | A (seed) | nee | ruis |
| CONV_CITY-t06 | B | A (baseline) | B (seed) | nee | ruis |
| CONV_CITY-t07 | A | B (baseline) | A (seed) | nee | helpt een beetje |
| CONV_CITY-t08 | B | A (baseline) | B (seed) | nee | helpt een beetje |

Afgeleide totalen:

- **Inter-reviewer winnaar-overeenstemming: 1/8** (alleen CONV_STARTUP-t05). κ ≈ 0.
- **SSL/seed-variant geprefereerd: Reviewer A 1/8, Reviewer B 8/8** — een vrijwel
  perfecte inversie.
- **CONV_CITY is het meest gepolariseerd**, niet het sterkste positieve signaal:
  Reviewer A koos daar de seed-variant 0/4 (expliciet "veroorzaakt ruis" /
  "diffuus"); Reviewer B 4/4.
- Reviewer A `seed_effect`: ruis ×3, helpt-een-beetje ×4, helpt-duidelijk ×1.
  Reviewer B `seed_effect`: helps-clearly ×5, a-bit ×2, no-difference ×1,
  noise ×0.

## Wat dit betekent

**1. De onenigheid is structureel, niet willekeurig.** Beide reviewers wijzen per
item dezelfde variant aan als seed-gedreven; ze verschillen op de waardering.
Reviewer A straft "de seed verdringt de letterlijke vraag" af als ruis/vernauwing;
Reviewer B beloont "rijker, geïntegreerd, meerlagig". Dat is de **rubric-as**
verrijking-vs-ruis — eerder al als rubric-fragiliteit gezien in rounds 006–007,
nu op de beslissende payoff-vraag.

**2. Het enige consensus-item is het meest concrete.** Op CONV_STARTUP-t05 (virale
piek → autoscaling, queues, rate limiting) zijn beide reviewers het eens dat de
seed duidelijk hielp. Waar de seed concreet *operationaliseert*, is hij
onbetwist waardevol; waar hij *breedte/thema* toevoegt, splitst het oordeel.

**3. De ruis zit in GEVALIDEERDE seeds.** De gesurfacete seeds zijn
pijplijn-PROMOTED (recurrence ≥ Gate-bar, contradiction-vrij, born-earlier,
cosine ≥ `surface_threshold`). De door Reviewer A gemarkeerde ruis/vernauwing zit
dus *niet* in ongefilterde supply, maar in seeds die de Gate al hadden gehaald.
Het supply-filter (weight-0 / TTL / EXPIRED) werkt; het ontbrekende stuk is
**use-time discipline**: de Gate valideert persistentie + geen-contradictie, niet
of déze promoted seed dít specifieke antwoord scherper of juist smaller maakt
(de `surface_threshold` ~0.30 is grof, en de weave-prompt zegt "betrek expliciet").

**4. Doctrine-link.** SSL stelt: weight = *potentieel, geen must*. De huidige
weave-stap dwingt een promoted seed altijd te sturen → potentieel wordt must.
Reviewer A's taal ("te seed-gedreven", "vernauwt", "diffuus") is daarvan de
signatuur. Sluit aan op round 014: do-no-harm is niet automatisch op
antwoordniveau voor irrelevante seeds.

## Conclusie

Dit weerlegt W9f niet: het mechanisme (detecteren → recurrence → Gate →
cross-turn surfacing) vuurt reproduceerbaar op veilige drempels. Maar het is óók
**geen schone bevestiging van de payoff op veilige drempels** — anders dan round
019 (lossere drempels) komt de blinde review gesplitst terug, en de splitsing zit
precies op de vraag of gesurfacete cross-turn context verrijking of ruis is.

De juiste vervolgvraag is daarmee scherp en falsifieerbaar: **wanneer mag een
promoted seed het antwoord sturen?** Niet "altijd expliciet betrekken", maar
sturen wanneer hij aanscherpt en dormant blijven wanneer hij zou vernauwen — dat
is weight-als-potentieel toegepast op het surfacing-moment. Dit is de kern van de
W10-richting.

## Grenzen

- n = 8 items, twee reviewers; Reviewer B mogelijk minder kritisch of een
  AI-lezer (EN-template, `noise = low` op alle 8).
- SSL/baseline-toewijzing afgeleid uit motivaties, niet uit de answer key
  (kop-bevinding 1/8 staat daar los van).
- Eén model (gpt-4.1), auteur-gekozen thema's. **Signaal, geen verdict — en de
  richting is waarschuwend, niet bevestigend.**
