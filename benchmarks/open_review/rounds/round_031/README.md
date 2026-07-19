# Round 031 — vroege-beurt-discipline: bouwen en blind hertesten

> **Status: VERDICT — hertest gedraaid én blind gereviewd (2 reviewers,
> beide sheets gecommit). Op de drie standen van de doctrine (winnend /
> ondersteunend / niks; alleen hinderen is fout): vroege beurten nu
> doctrine-conform (geen hinder), maar 8/14 hinder op late beurten — dáár
> zit het falen, niet in het uitblijven van een vroege winner.
> Zie `human_review/RESULTS.md`.** Doel:
> de laatste bekende ruisbron dichten. In round 029 stuurde een matig
> passende seed op de vroege t04-beurten het antwoord off-topic (EDU en
> POLICY), terwijl een sterk passende seed op diezelfde beurt juist duidelijk
> hielp (HEALTH). De bestaande use-time discipline begrenst *hoeveel* seeds
> meesturen, niet *of* een matig passende seed vroeg het onderwerp verschuift.

## De ingreep (fit-selectie, geen beurt-blok)

1. **Vroege-beurt-marge** (`--early-turn-margin`, default 0.10): zolang de
   beurtindex kleiner is dan `--early-turn-history` (default 5) geldt een
   hogere relevantielat (`surface_threshold` + marge). Let op de indexering:
   review-items zijn 0-geïndexeerd (`t{t}`), dus de round-029-ruisbeurten
   (t04 = index 4) vallen precies bínnen de default-zone, en t05/t06 — in
   rounds 023/025 schoon en winnend — blijven erbuiten op de basislat. Rationale: vroeg in
   het gesprek is er nog weinig opgebouwd bewijs dat het thema centraal
   staat, dus moet de fit met de gestelde vraag zelf sterker zijn. Een
   HEALTH-t04-achtige sterk-passende seed blijft vuren; een EDU/POLICY-
   t04-achtige matig-passende valt af. Beurten worden nooit geblokkeerd.
2. **Prompt-aanscherping** (alleen SSL-arm, verandert de A/B-vergelijking
   niet aan de baseline-kant): "De gestelde vraag blijft leidend: een
   invalshoek mag het antwoord verdiepen, nooit het onderwerp of de focus
   van de vraag verschuiven."

Beide instellingen staan in het artifact (`applied_thresholds`), zijn per
conversatie te overriden en met `--early-turn-margin 0` volledig uit te
zetten. Deterministisch getest (marge blokkeert sim~0.35 op vroege lat,
zelfde seed surfacet zonder marge of buiten de vroege zone).

## Run-recept voor de blinde hertest

```text
workflow: Research · SSL Benefit (OpenAI)
experiment: ssl-session
model_id: gpt-4o                # zelfde model als round 029 = zuivere vergelijking
recurrence_mode: cluster
input_path: src/shadowseed/data/ssl_session_transfer_suite.json
max_new_tokens: 1600
review_prefix: ssl_session_blind_ab
```

De nieuwe discipline-defaults gelden automatisch. Vergelijkingsdoel is
round 029: zelfde model, zelfde suite, zelfde protocol (≥2 blinde
reviewers, seed-effect-labels, answer key in quarantaine).

## Runverwijzing

```text
run_id: 29238820927            # main @ 722f700 (mét discipline), conclusion: success
artifact: ssl-openai-ssl-session-gpt-4o (id 8274672968)
artifact_digest: sha256:2c90b4ef2fc8a353b135a326de82681d927d076ba37889c8401dd57cd0966505
```

**Distributieprotocol (blindering!):** alléén de maintainer downloadt het
artifact. Reviewers krijgen uitsluitend `review_form.md` (of
`review_items.json`) plus `scoring_template.csv` uit de map
`blind_ab_review/`. De bestanden `answer_key.json`, `summary.json` en het
ruwe `ssl_session_suite.json` blijven dicht tot ná de scoring — ze
onthullen de SSL-kant (artifact-contract). Stuur reviewers dus nooit de
artifact-zip of de download-URL zelf.

Kwalitatief uit de job-log (geen claim, wel sanity): het cross-turn
mechanisme vuurt (o.a. psychologische-motivaties-seed in HEALTH,
lokale-kennis-seed in POLICY t5 en t6), antwoorden eindigen op volledige
slotalinea's, en de zichtbare events bevatten geen zwakke-fit-surfacing op
vroege beurten. De cijfers komen uit de blinde review, niet uit deze log.

## Klaar wanneer

1. Run gedraaid, pack gereviewd door ≥2 onafhankelijke blinde reviewers,
   beide sheets als CSV gecommit (de round-029-les).
2. Leesregel vooraf vastgelegd: de hertest slaagt als de
   "veroorzaakt ruis"-labels op vroege beurten verdwijnen zónder dat de
   "helpt duidelijk"-winst daar verdwijnt (HEALTH-t04-patroon blijft).
   Win-rate blijft nevengeschikt (twee assen).
3. Uitkomst eerlijk gedocumenteerd, ook als de marge te bot of te slap
   blijkt (dan is dát de bevinding en volgt kalibratie).

## Claimgrens

Dit is een disciplinestap plus meetplan, geen resultaat. Tot de blinde
hertest binnen is, blijft de round-029-lezing staan: vroege-beurt-sturing
is gelokaliseerd maar nog niet aantoonbaar gedicht.
