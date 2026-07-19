# Round 033 — verdict: NIET gerepliceerd; Laag G spoor 2 sluit voor deze schaal

> **Status: VERDICT (instrument-niveau, gepreregistreerd).** De replicatie
> van het round-032-signaalkandidaat is uitgevoerd (2026-07-18/19) op een
> níeuwe brontekst. Op de vier vooraf vastgelegde toetsen (lagen 2 en 5 ×
> beide detectoren, Bonferroni-lat 0.0125): **0 van de 4 haalt de lat.**
> Het round-032-kandidaat repliceert niet — het was toeval. Conform de
> vooraf vastgelegde leesregel sluit spoor 2 hiermee definitief voor deze
> schaal (≤0.5B). Signaal ≠ verdict; dit raakt lagen A–F niet.

## Runverwijzing

```text
workflow: Research · Laag G sonde met echte verdictbron
run 1 (vers oordeel)     : 29490380118   # gpt-4.1 vers, main @ 9ced9a7, success
re-probe (ongepind)      : 29665325310   # gepinde verdicten, branch @ 5921da2
bevestiging C (gepind)   : 29666729658   # branch @ 9d5e7d0, artifact 8436199831
bevestiging D (gepind)   : 29666734199   # branch @ 9d5e7d0, artifact 8436183526 — C≡D bit-identiek
digest (C)               : sha256:d8ea665b5c2b54f7b5042985c259015d5200857cd9dc311daf338ba0fcd9e814
probe_model: Qwen/Qwen2.5-0.5B (multilingual, read_location=neuron)
verdict_model: gpt-4.1 (extern, ontkoppeld) — 12 HOUDT_STAND / 12 WEERLEGD
input: dialectic_falsification_transfer_v3.json (24 cases, nieuwe brontekst WONEN/ZORG/CULTUUR)
sparse_permutations: 500 (vloer 1/501 ≈ 0.0020)
```

De re-probe pinde de geverifieerde round-1-verdicten
(`verdicts_run_29490380118.json`), zodat gpt-4.1 niet opnieuw hoefde te
oordelen en de meting een faithful reproductie is van run 29490380118. HF
Hub is in de sandbox org-geblokkeerd (403), dus dit is de manier om de
gepreregistreerde lagen expliciet af te lezen.

## De vier gepreregistreerde toetsen (lat 0.05/4 = 0.0125)

| Toets | round 032 (ontdekking) | round 033 (reproduceerbaar, C≡D) | onder 0.0125? |
|---|---|---|---|
| `layers.2.mlp.down_proj` — centroïde-p | 0.014 | **0.0319** | nee |
| `layers.2.mlp.down_proj` — sparse-p | — | **0.509** (LOOCV 0.50) | nee |
| `layers.5.mlp.down_proj` — centroïde-p | — | **0.0479** | nee |
| `layers.5.mlp.down_proj` — sparse-p | 0.018 (LOOCV 0.88) | **0.4232** (LOOCV 0.5417) | nee |

**0 van de 4. Niet gerepliceerd.**

### Reproduceerbaarheid van het verdict (codex-P1) — aangetoond

De eerste re-probe (run B, ongepinde deps) reproduceerde run A niet
bit-identiek: de sterkste sparse-laag verschilde (10 vs 19). Na het pinnen
van torch/transformers zijn **twee onafhankelijke bevestigingsruns gedraaid
— C (29666729658) en D (29666734199), zelfde commit, near-simultaan — en
die zijn tot op de laatste decimaal gelijk**: sterkste centroïde laag 11
(cos 0.1546, p 0.008), sterkste sparse laag 19 (LOOCV 1.0, p 0.002,
35/4864), en de vier gepreregistreerde toetsen exact zoals in de tabel
hierboven. Het eerdere 10→19-verschil wás dus deps-drift tussen 16 en 18
juli, nu gedicht.

De volledige numerieke omgeving is gepind — `torch==2.12.1`,
`transformers==5.12.1`, `numpy==2.4.6` — en het faithful-pad eist een
immutable `--model-revision` (commit-SHA) zodat ook de modelsnapshot
vastligt; die SHA vergt HF-netwerk (in de sandbox geblokkeerd) en wordt door
de maintainer aangeleverd voor een volledig durable pin. C≡D toont dat het
resterende gat (numpy/BLAS binnen dezelfde runner-image) in de praktijk
gesloten is. Het verdict staat op deze reproduceerbare cijfers: alle vier
ver boven 0.0125, sparse-LOOCV op toevalsniveau (0.50 / 0.54).

## Waarom dit beslissend is

1. **De sparse detector klapt in tot toeval.** Het round-032-"signaal" zat
   vooral in de sparse L1-classifier op laag 5 (LOOCV 0.88). Op een nieuwe
   brontekst geeft diezelfde laag met dezelfde detector LOOCV **0.50** —
   zuiver muntworp-niveau, p 0.56. Er was niets stabiels om te vinden.
2. **Het "sterkste" signaal is niet gelokaliseerd — twee aparte redenen.**
   Sterkste lagen: round 032 → 2 (centroïde) / 5 (sparse); round-033-run-1
   → 11 / 10; round-033 re-probe → 11 / 19. Hier moeten twee verschillen
   uit elkaar gehouden worden (codex-P1-correctie — mijn eerdere lezing
   plakte ze op één hoop):
   - **Tussen 032 en 033 (verschillende brontekst):** de sterkste lagen
     verspringen 2/5 → 11/10. Dát is legitiem bewijs dat er geen codering
     is die over datasets heen op dezelfde plek stabiel is.
   - **Tussen run-1 en de re-probe (identieke brontekst én labels):** de
     sterkste sparse-laag verspringt 10 → 19. Dit is **géén** dataset-ruis
     — de dataset was identiek. Het is (a) numerieke
     niet-reproduceerbaarheid doordat torch/transformers in die twee runs
     ongepind vers geïnstalleerd werden, en (b) het feit dat de sparse
     LOOCV op n=24 op véél lagen tegen het plafond zit (0.96–1.0), zodat de
     argmax onstabiel is voor minieme float-verschillen. Beide punten
     bevéstigen "geen echt gelokaliseerd signaal", maar via
     overfitting/instabiliteit, niet via de dataset.
   Dit is precies waarom de preregistratie de vier toetsen op vaste lagen
   vastlegde in plaats van "de sterkste laag": een losse "sparse p 0.004 op
   laag 19" is post-hoc geselecteerde ruis en telt niet mee.
3. **Het instrument werkt — het zegt correct néé.** De permutatiecontrole
   en de LOOCV hielden hier een ceiling-scorende classifier (LOOCV 1.0 op
   laag 19) tegen als niet-repliceerbaar. Dat is precies de bescherming
   waarvoor de sparse-detector-with-permutation is gebouwd.

## Wat dit betekent (en niet)

- **Spoor 2 (activatie-sonde) sluit voor deze schaal (≤0.5B).** Vijf
  iteraties met echte modelruns, nu ook met de H-Neurons-methodiek
  (leespunt `neuron`, sparse detector) en een gepreregistreerde
  replicatie: geen aantoonbare interne codering van het externe
  houdbaarheidsoordeel in kleine modellen. Dat is een eerlijk, definitief
  antwoord op dít niveau.
- **Niet uitgesloten**, maar expliciet toekomstwerk zonder belofte: het
  H-Neurons-precedent (Gao et al. 2025) meet op 24B–70B — een orde van
  grootte die geen GitHub-Actions-werk is. Een heropening vraagt die schaal
  én een nieuwe preregistratie.
- **Spoor 1 (dialectische falsificatie) blijft de actieve Laag G-route** en
  levert vandaag Gate-waarde: het draaide ook hier zonder mankement (12/12
  houdbaarheidsoordelen over de nieuwe caseset).
- **Lagen A–F onaangetast.** De kernclaims van SSL steunen niet op interne
  steun; dit was verkenning van de bovenkant van de stack.

## Claimgrens

Exploratieve Laag G. "Sluit voor deze schaal" betekent: geen nieuwe runs op
dit spoor onder ~1B zonder een nieuw, vooraf geregistreerd plan. De
methodische winst blijft staan — het instrument rapporteert correct néé,
ook toen een positief resultaat aantrekkelijker was geweest.
