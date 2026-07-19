# Round 023 — blinde review van de use-time-discipline run (3 reviewers)

> **Status: het round-023-doel (de round-022-ruis/vernauwing dempen) lijkt
> grotendeels gehaald (sterke daling, niet nul); de payoff-win-rate blijft ≤0.5
> en is vertroebeld door afkap.** Drie
> onafhankelijke reviewers scoorden hetzelfde blinde A/B-pack van de
> use-time-discipline run (10 cross-turn items, gpt-4.1, `recurrence_mode=cluster`,
> nieuwe defaults `surface_top_k=2` + potentieel-prompt; run 28442142918).
> SSL/baseline-kant per item uit de answer key (joblog).

## Cijfers

SSL-voorkeur (winnaar == SSL-kant), per reviewer:

| Reviewer | SSL-wins / 10 |
|---|---|
| r1 (gedetailleerd, JSON) | 5 |
| r2 (CSV) | 3 |
| r3 (formulier) | 4 |
| **gemiddeld** | **~0.40** |

Inter-reviewer overeenstemming (winnaar):

- **5/10 unaniem** (t04, t07, CONV_CITY-t04, -t07, -t08);
- pairwise: r1–r2 6/10, r1–r3 7/10, r2–r3 7/10 → **~0.67 gemiddeld**.

Dit is een **scherpe verbetering t.o.v. round 022** (daar: winnaar-overeenstemming
1/8 ≈ 0.125, een vrijwel perfecte 1-vs-8 inversie). De rubric-polarisatie
"verrijking vs ruis" is grotendeels weg.

## Wat dit betekent

**1. De ruis/vernauwing is sterk verminderd — het round-023-doel grotendeels
gehaald (niet volledig).** Noise-notities per reviewer: r1 **0/10**, r2 **0/10**,
r3 **3/10** (`geen` ×7). Die drie r3-noten, eerlijk uitgesplitst naar kant:

- `CONV_STARTUP-t04`: **op de SSL-kant** — milde ruis in het SSL-antwoord
  ("apparaatgegevens"); niet duidelijk seed-gedreven, maar wél SSL-zijdig;
- `CONV_STARTUP-t06` en `-t08`: op het **baseline**-antwoord (harde benchmarks
  resp. brede reguleringsclaims).

De aparte seed-effect-kolom zegt nergens "ruis"/"vernauwt" (overal "helpt" of
"maakt geen verschil"). Netto: **1 milde SSL-zijdige ruisnotitie op 30
reviewer-items** (~3%). Vergelijk round 022, waar de SSL/seed-antwoorden
hérhaald als ruis/vernauwing werden gemarkeerd (**~3 van 8, op de SSL-kant**). Het
diffuse/te-seed-gedreven faalpatroon is dus **sterk teruggebracht, maar niet tot
nul** — de cap (`top_k=2`) + potentieel-niet-must-prompt doen het grootste deel van
het werk, met één milde rest.

**2. Seed-effect = potentieel, geen must (werkend).** De seed-effect-labels zijn
overal "helpt (duidelijk/een beetje)" of "maakt geen verschil" — **nooit ruis**.
De seed helpt waar hij relevant is (CONV_CITY historische gelaagdheid t04/t08;
CONV_STARTUP netwerkeffecten/privacy t06/t08) en is neutraal waar niet (technische
schaalvraag t05). Dat is precies het beoogde gedrag: sturen bij aanscherping,
stil blijven bij irrelevantie, geen schade.

**3. Win-rate blijft ≤0.5 (~0.40).** SSL verslaat de baseline *niet* op win-rate.
Per de answer-space-herkadering is win-rate niet de hoofdmetriek, maar het is
eerlijk om te zeggen: dit is geen bewijs dat handelen op de seed het antwoord
gemiddeld béter maakt — alleen dat het meestal niet schaadt en soms aanscherpt.

**4. Zwaar confound: afkap (truncation).** Veel winnaarkeuzes hingen op wélk
antwoord minder abrupt werd afgekapt (`max_new_tokens=400`) — r1 koos er meerdere
expliciet op "B breekt af midden in een woord ((CPU)". Dat meet tokenbudget-geluk,
niet SSL-kwaliteit, en vertroebelt de win-rate in beide richtingen.

## Conclusie

- **Use-time discipline (round 023): grotendeels geslaagd op eigen doel.** De
  seed-zijdige ruis/vernauwing van round 022 (~3/8) is teruggebracht tot 1 milde
  SSL-zijdige notitie (1/30), en de reviewers zijn het weer grotendeels eens. De
  "potentieel, geen must"-fix doet het grootste deel van het werk — niet tot nul.
- **Payoff-claim blijft "kandidaat".** Win-rate ~0.40 en de afkap-confound betekenen
  dat we niet kunnen zeggen dat SSL antwoorden gemiddeld beter maakt.
- **Volgende schone stap:** her-draai zónder afkap-artefact (`max_new_tokens` ruim
  omhoog, bv. 900–1200) zodat de win-rate niet meer op afgekapte zinnen rust; dan
  pas een payoff-uitspraak. Daarnaast staat W10 (doctrine-transfer) klaar.

## Grenzen

- n = 10 items, 3 reviewers (provenance gemengd/onbekend; r1 oogt AI-gegenereerd
  gezien structuur + volledige JSON). Signaal, geen eindverdict.
- Eén model (gpt-4.1), auteur-gekozen thema's. De afkap-confound moet eruit
  voordat de win-rate iets waard is.
