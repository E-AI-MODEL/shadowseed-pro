# Round 031 — hertest-verdict: vroege ruis weg, maar verschoven — niet geslaagd

> **Status: VERDICT (2 onafhankelijke blinde reviewers, beide sheets als CSV
> gecommit — protocol volledig).** Gelezen op de drie standen van de
> doctrine (winnend / ondersteunend / niks — alleen *hinderen* is fout):
> de vroege beurten zijn nu doctrine-conform (geen hinder; niks of een
> beetje hulp, en dat is prima), maar op late beurten hinderde een matig
> passende seed 8 van de 14 keer. Dát is het falen van deze ronde; het
> uitblijven van een vroege "winner" is dat niet.

## Unblinding (geverifieerd)

Answer key gereproduceerd uit code (`_balanced_ssl_a_assignments`, seed 45,
count 7): EDU-t04 **B**, EDU-t05 **B**, EDU-t06 **A**, HEALTH-t05 **A**,
HEALTH-t06 **A**, POLICY-t05 **B**, POLICY-t06 **A**. Onafhankelijk
bevestigd op 6/7 items: de motivaties noemen de seed-invalshoek
(inclusiviteit, psychologische motieven/groepsdruk, lokale kennis) steeds
aan precies de key-kant; EDU-t04 is in beide motivaties neutraal.

## Cijfers

| Meting | r1 | r2 |
|---|---|---|
| Winnaar-as | SSL 3 / baseline 3 / tie 1 (0.50) | SSL 1 / baseline 6 (0.14) |
| Seed-effect: helpt | 4 (1 duidelijk, 3 beetje) | 1 (duidelijk) |
| geen verschil | 0 | 1 |
| veroorzaakt ruis / vernauwt | 1 + 2 | 3 + 2 |

- **Overeenstemming: 3/7 ≈ 0.43** (fors onder 023/025: 0.67/0.71). Alle
  drie de consensus-items gingen naar **baseline**; consensus-SSL 0.
- **Seed-effect totaal (14 labels): 5 helpt / 1 geen verschil / 8
  ruis-of-vernauwt** — de slechtste verhouding tot nu toe.
- **t04 (1 event, 2 labels): "helpt een beetje" + "maakt geen verschil" —
  géén vroege ruis meer.** Er was ook maar één t04-event: de marge filterde
  vroege surfacing, precies zoals ontworpen.
- **Strikte kolom** (`noise_or_hallucinated_relevance`): r2 vulde 5× "ja"
  met uitleg, r1 1× — álle toelichtingen beschrijven afleiding/verdringing
  door de seed, geen enkele noemt verzonnen feiten. Fabricage blijft 0;
  de kolom is voor het eerst niet leeg en dat tellen we eerlijk mee.

## Leesregel-toets (vooraf vastgelegd in dit dossier)

> "Geslaagd als de ruis-labels op vroege beurten verdwijnen zónder dat de
> helpt-duidelijk-winst daar verdwijnt."

**Deel 1 ✓** — geen ruis op vroege beurten. **Deel 2 ✗ zoals geformuleerd**
— er waren geen vroege events meer die konden winnen. Maar hier past een
zelfkritische noot op de leesregel zelf: "de winst moet blijven" was
winnaar-denken, en dat is niet de doctrine. SSL hoeft niet te winnen; soms
is het niks, soms ondersteunend, soms winnend — alleen hinderen is de
faalstand. Op díe lat zijn de vroege beurten geslaagd (van hinder naar
niks/beetje hulp). **Het verdict blijft "niet geslaagd", maar om de juiste
reden: 8/14 hinder op t05/t06**, waar rounds 023/025 juist hindervrij
waren.

## Eerlijke analyse

1. **De marge deed wat hij moest** (vroege events gefilterd tot één
   sterk-genoeg geval, zonder vroege ruis), maar dat bleek niet het echte
   probleem op te lossen.
2. **Het echte patroon is herhaald duwen van dezelfde seed over late
   beurten.** De inclusiviteit-seed duwde op EDU-t05 én t06; de
   lokale-kennis-seed op POLICY-t05 én t06 — beide keren door reviewers
   als ruis/vernauwing gelabeld. De "vraag blijft leidend"-promptregel
   hield dat onvoldoende tegen.
3. **Confound: nieuw seed-aanbod per run.** Deze run promoveerde andere
   seeds (inclusiviteit, lokale kennis) dan round 029 (ethiek,
   financiering, sociale rechtvaardigheid). De vergelijking met 029 is dus
   niet seed-gecontroleerd; wat we zeker weten is dat déze seeds matig
   pasten en bleven terugkomen.
4. **HEALTH blijft het patroon**: het enige "helpt duidelijk"-consensuspunt
   (r2) en r1's enige "helps_clearly" zitten beide op de
   psychologische-motieven-seed — sterke fit helpt, over modellen en runs
   heen.

## Vervolgrichting (open)

- **Surfacing-herhaling begrenzen**: een seed die al een antwoord heeft
  gestuurd niet opnieuw laten surfacen op de direct volgende beurt(en)
  (cooldown of eenmalig-surfacen), zodat één matige seed niet twee
  opeenvolgende antwoorden kan kleuren.
- Of de fit-lat generiek verhogen (marge op álle beurten) — met het risico
  dat ook de HEALTH-winst sneuvelt; de cooldown adresseert het gemeten
  patroon directer.
- Elke volgende hertest seed-gecontroleerd rapporteren (welke seeds
  promoveerden) zodat run-variatie zichtbaar is.

## Doorwerking op de teltabel (twee assen)

Round 031 voegt 14 labels toe: totaal 83, waarvan **57 "helpt" (~69%)**,
13 geen verschil, 13 hinder (ruis of vernauwing). Op de drie standen van
de doctrine: winnen hoeft niet, niks is prima; **hinder is de enige
faalstand en dus de te minimaliseren metriek — nu 13/83 (~16%)**, waarvan
8 in deze ronde. De kernzin blijft waar (de seed helpt vaker dan hij de
head-to-head wint), en dat rapporteren we overal mee.

## Bestanden

- `r1_scores.csv`, `r2_scores.csv` — beide blinde sheets, verbatim gecommit.
- Answer key: reproduceerbaar uit code (seed 45, count 7); geverifieerd
  tegen de seed-content in de motivaties (6/7, 1 neutraal).
