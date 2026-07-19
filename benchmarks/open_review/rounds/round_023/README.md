# Round 023 — W9f use-time seed-discipline: potentieel, geen must

> **Status: mechanisme geland (deterministische test); live her-draai + verse
> review is de pending validatie.** Round 022 liet zien dat de blinde review op
> veilige drempels gespleten terugkwam, en dat de gemarkeerde ruis/vernauwing in
> *gevalideerde, promoted* seeds zat — niet in ongefilterde supply. Dit round
> pakt dat aan op het surfacing/use-moment, niet op de Gate.

## De diagnose (uit round 022)

De gesurfacete seeds zijn pijplijn-PROMOTED (recurrence ≥ Gate-bar,
contradiction-vrij, born-earlier, cosine ≥ `surface_threshold`). Toch markeerde
reviewer A meerdere antwoorden als "te seed-gedreven", "diffuus" of "vernauwt":

- `CONV_CITY-t06`: "B probeert veel surfaced seeds te verwerken en wordt diffuus"
  → **te veel** seeds tegelijk ingeweven;
- `CONV_CITY-t05`: historische/economische seed verdringt de kernvraag
  (vergroening) → **één** seed gedwongen ingeweven waar hij vernauwt.

De Gate valideert persistentie + geen-contradictie, niet of déze promoted seed
dít specifieke antwoord scherper of juist smaller maakt. SSL-doctrine zegt:
weight = *potentieel, geen must*. De oude weave-stap dwong echter elke
losjes-relevante promoted seed te sturen (`surface_threshold` ~0.30 +
"betrek expliciet"). Potentieel werd must.

## De wijziging (use-time discipline)

In `ssl_session_suite` (geen Gate-/opslagwijziging):

1. **Ranked + capped surfacing.** Eligible promoted seeds worden op relevantie
   (cosine) gesorteerd en alleen de `surface_top_k` meest relevante mogen een
   beurt sturen (`select_cross_turn_seeds`, default `top_k=2`, `-1` = geen
   limiet). Dit dempt het "diffuse" faalpatroon. Het cross-turn mechanisme blijft
   intact: het vuurt nog steeds zodra ≥1 seed kwalificeert.
2. **Weave-prompt = potentieel, geen must.** Van *"betrek daarbij expliciet"*
   naar: *"je mág deze invalshoek(en) betrekken — maar alléén als ze het antwoord
   aantoonbaar aanscherpen; laat ze weg als ze zouden afleiden of vernauwen."*
   Het model mag een seed dus laten vallen (do-no-harm op antwoordniveau).
3. **Per-topic instelbaar.** `surface_threshold`/`surface_top_k` kunnen, net als
   de Gate-knoppen, per conversatie worden overschreven; CLI: `--surface-top-k`,
   `--surface-threshold`.

## Bewijs in deze PR (deterministisch, geen model)

- `select_cross_turn_seeds` rankt op relevantie en capt op `top_k` (unit test);
- de weave-prompt bevat de potentieel-niet-must-formulering (aanscherpen/vernauwen)
  en niet langer de harde "betrek expliciet"-instructie;
- `surface_top_k`/`surface_threshold` worden vastgelegd in `applied_thresholds`.

Volledige suite groen (291 passed, 4 skipped); ruff clean.

## Honest scope / pending

Dit is het *mechanisme* voor de discipline. Of het de round-022-ruiscases
daadwerkelijk dempt **zonder de wins te verliezen** (vooral het
consensus-item `CONV_STARTUP-t05`), is een modelrun-vraag:

1. Her-draai de round-020/022-conversaties op `gpt-4.1`, veilige drempels,
   `--recurrence-mode cluster`, met de nieuwe defaults (`surface_top_k=2`,
   potentieel-prompt) via `Research · SSL Benefit (OpenAI)`.
2. Verse blinde review (≥2 reviewers, mét answer key) en vergelijk met round 022:
   dempen de ruis/vernauwing-cases, blijft `CONV_STARTUP-t05` een win?
3. Pas daarna mag de payoff-claim van "kandidaat" opschuiven.

Dit is spoor 1 van de twee na round 022; spoor 2 is W10 doctrine-transfer.

## Eerste validatie-run (binnen) — 2026-06-30

Stap 1 hierboven is uitgevoerd. Provenance: run **28442142918**, job 84282442326,
`Research · SSL Benefit (OpenAI)`, `gpt-4.1`, `recurrence_mode=cluster`, OpenAI
embeddings, de nieuwe round-023 defaults (`surface_top_k=2` + potentieel-prompt),
branch-sha `692c889`, artifact `ssl-openai-ssl-session-gpt-4.1` (id 7979699416).
Run geslaagd; alle `ssl-session`-stappen success.

Wat de run laat zien (mechanisme):

- **Cross-turn payoff events = 10** (answer key: `CONV_STARTUP` t4–t8 en
  `CONV_CITY` t4–t8; `CONV_IR_SHORT` 0). De cap (`top_k=2`) + potentieel-prompt
  hebben het mechanisme dus **niet gesmoord** — surfacing vuurt nog breed
  (vergelijkbaar met round 020/022's ~8–10; de exacte telling is run-to-run ruizig
  op een LLM-detector, dus lees dit als "intact", niet als "meer = beter").
- **Cap aantoonbaar actief**: het ene leesbare item in de joblog (`CONV_CITY-t8`)
  surfacet **exact 1** seed ("historische gelaagdheid…") en weeft die als een
  nette *"Aanscherping"* binnen de draagvlak-/identiteitspunten — leest coherent,
  niet als het round-022 "te-seed-gedreven/diffuus"-patroon. Eén-item-leesindruk.
- Blind A/B-pack gegenereerd (`w9f_blind_ab_*`); SSL-toewijzing A=4 / B=6.

**Eerlijke grens — dit is signaal, geen verdict.** Of de ruis/vernauwing t.o.v.
round 022 echt daalt en of `CONV_STARTUP-t05` een win blijft, vereist stap 2: een
**verse blinde review** (≥2 reviewers, mét answer key). De per-seed promoted-count
en coverage staan in het artifact `ssl_session_suite.json` (niet hier overgenomen).
De payoff-claim blijft "kandidaat" tot die review binnen is.

## Blinde review binnen (3 reviewers) — zie `human_review/`

Stap 2 is uitgevoerd: 3 onafhankelijke reviewers scoorden het blinde A/B-pack.
Volledige cijfers + analyse in `human_review/RESULTS.md`, ruwe scores in
`human_review/scores.csv`. Kort:

- **Ruis/vernauwing sterk verminderd — het round-023-doel grotendeels gehaald
  (niet nul).** Noise-noten: r1 0/10, r2 0/10, r3 3/10. Eerlijk uitgesplitst:
  `CONV_STARTUP-t04` is een milde ruisnotitie op de **SSL-kant** ("apparaatgegevens",
  niet duidelijk seed-gedreven); t06/t08 gaan over het baseline-antwoord. Netto
  1 milde SSL-zijdige notitie op 30 reviewer-items, vs round 022's ~3/8 seed-zijdige
  ruis/vernauwing-flags. De seed-effect-kolom zegt nergens "ruis" — potentieel-
  niet-must doet het grootste deel van het werk, met één milde rest.
- **Overeenstemming hersteld:** 5/10 unaniem, ~0.67 pairwise — scherp beter dan
  round 022 (~0.125, de 1-vs-8 inversie is weg).
- **Win-rate blijft ≤0.5** (SSL-voorkeur r1/r2/r3 = 5/3/4 van 10, ~0.40), en is
  bovendien vertroebeld door **afkap** (veel keuzes hingen op welk antwoord minder
  abrupt werd afgekapt bij `max_new_tokens=400`).

Conclusie: use-time discipline geslaagd op eigen doel; payoff-claim blijft
"kandidaat". Volgende schone stap: her-draai met ruim `max_new_tokens` (~900–1200)
zodat de win-rate niet op afgekapte zinnen rust. Daarna W10 doctrine-transfer.
