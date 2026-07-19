# Round 030 — Laag G iteratie 6: NL-capabel model + 24 cases

> **Status: gedraaid (2026-07-07) — schone null, zie `RESULTS.md`.** Doel
> was: de twee open punten uit iteratie 5 (round 028) tegelijk sluiten — een
> gesondeerd model dat gpt-4.1's Nederlandse houdbaarheidsoordeel plausibel
> kán encoderen, en genoeg cases om de permutatievloer onder een
> betekenisvol niveau te krijgen. Beide zijn gesloten; het antwoord op de
> sonde-vraag blijft nul (sterkste laag p 0.2056, vloer 0.002).

## Wat er verandert t.o.v. round 028

| Aspect | Round 028 | Round 030 |
|---|---|---|
| Gesondeerd model | distilgpt2 / pythia-14m (Engels) | `GroNLP/gpt2-small-dutch` (NL-getraind, GPT-2-architectuur) |
| Cases | 10 (klasse-minderheid n=2) | 24, met bewuste ontwerp-balans (`…transfer_v2.json`) |
| Permutatievloer | 1/36 ≈ 0.028 | ~0.002 (Monte Carlo; lokaal geverifieerd met de fixture-keten) |
| Oordeelbron | gpt-4.1 (`--verdicts`) | idem — ongewijzigd |
| Pooling | stelling-tokens | idem — ongewijzigd |

De brontekst is identiek aan rounds 026–028, zodat de vergelijking zuiver
blijft. De 14 nieuwe cases dragen een ontwerp-intentie in hun note (7
kandidaat echt-ontbrekend, 5 bron-parafrases, 2 strijdig) — dat is
constructie-informatie, geen label: de labels komen op runtime van gpt-4.1.

## Run-recept

```text
workflow: Research · Laag G sonde met echte verdictbron
probe_model_id: GroNLP/gpt2-small-dutch
dialectic_model_id: gpt-4.1
input_path: src/shadowseed/data/dialectic_falsification_transfer_v2.json
```

## Klaar wanneer

1. gpt-4.1-verdicten over de 24 stellingen gecommit/gelogd (verdeling telt:
   een extreem scheve verdeling maakt de sonde alsnog machteloos — dan is
   dát de eerlijke uitkomst);
2. probe-rapport met per-laag cosine-afstand + permutatie-p; de leesregel
   blijft: **alleen een p nabij de vloer op een consistent laagprofiel telt
   als signaal-kandidaat** — één lage p over 12 geteste lagen is
   multiple-comparisons-ruis;
3. uitkomst (signaal óf null) eerlijk gedocumenteerd hier en in
   `laag-g-scoping.md`.

## Claimgrens

Exploratief, laag G. Een positief signaal zou een eerste aanwijzing zijn dat
een NL-model het houdbaarheidsoordeel intern codeert — falsificatie- of
evidence-input, nooit directe promotie (doctrine). Een null op dít model is
informatiever dan de nulls van round 028, maar sluit interne steun in grotere
modellen niet uit. Niets hierin raakt lagen A–F.
