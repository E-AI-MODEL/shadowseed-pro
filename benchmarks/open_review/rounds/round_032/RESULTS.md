# Round 032 — resultaat: vierde null volgens de leesregel, maar de eerste die niet vlak is

> **Status: VERDICT (instrument-niveau).** De iteratie-7-run is uitgevoerd
> (2026-07-14) met het H-Neurons-leespunt (`neuron`: down_proj-input), de
> sparse L1-detector én een groter multilingual model. Uitkomst op de
> vooraf vastgelegde leesregel: **geen signaal** — beide detectoren blijven
> boven de Bonferroni-lat. Daarmee gaat dit spoor in rust, precies zoals
> vooraf afgesproken. Signaal ≠ verdict; dit raakt lagen A–F niet.

## Runverwijzing

```text
workflow: Research · Laag G sonde met echte verdictbron
run_id: 29299952586           # main @ 92fc205, conclusion: success (31 min)
artifact: activation-probe-real-verdict (id 8298589138)
artifact_digest: sha256:b44fcccf0e9ef3d7bfd8de22f5cd5ed7e06155c5bcdd4b1056d06fa4f8d9b0d5
probe_model: Qwen/Qwen2.5-0.5B (multilingual, 24 lagen, read_location=neuron)
verdict_model: gpt-4.1 (extern, ontkoppeld)
input: dialectic_falsification_transfer_v2.json (24 cases)
sparse_permutations: 500 (vloer 1/501 ≈ 0.0020)
```

## Stap 1 — gpt-4.1-verdicten

**7× HOUDT_STAND / 17× WEERLEGD over alle 24 cases** (geen Gate-weigering
dit keer; round 030 had er één). De 7 overlevers zijn dezelfde inhoudelijke
kern als in round 030 (sociale ongelijkheid, kosten-baten, privacy/
datasporen, docent-bijscholing, adaptatie-financiering, monitoring) plus
hittestress; parafrases, distractors en strijdige stellingen gingen
opnieuw allemaal onderuit.

## Stap 2 — de sonde op het neuron-leespunt

| Detector | Sterkste laag | Score | Ruwe p | Bonferroni-lat |
|---|---|---|---|---|
| Centroïde (cosine) | `model.layers.2.mlp.down_proj` | 0.1211 | **0.014** | 0.05/24 ≈ 0.00208 |
| Sparse L1 (LOOCV) | `model.layers.5.mlp.down_proj` | bacc 0.8824 | **0.018** | 0.05/24 ≈ 0.00208 |

De sparse fit gebruikte 37 van de 4864 dimensies (~0.8%) — sparse zoals
de detector hoort te zijn, maar dat is een eigenschap van de L1-straf,
geen bewijs op zich.

## Lezing op de vooraf vastgelegde leesregel

- **Geen signaal.** Beide ruwe p's (0.014 en 0.018) liggen ruim boven de
  lat van ~0.00208. Over 24 geteste lagen is een minimum-p van 0.014 goed
  verenigbaar met toeval (kans op minstens zo'n lage laag onder de
  nulhypothese ≈ 29%, en er liepen bovendien twee detectoren).
- **Dus: vierde null → het spoor gaat in rust**, conform de vooraf
  vastgelegde afspraak in het README van deze round. Geen kalibreren
  achteraf, geen lat verschuiven omdat de uitkomst "bijna" was.

## Eerlijke lezing — wat deze null anders maakt

1. **Dit is de eerste niet-vlakke null.** Rounds 027/028/030 gaven p's van
   0.21–0.83; deze round geeft 0.014/0.018 op twee onafhankelijke
   detectoren, op het per-neuron-leespunt van het H-Neurons-precedent, op
   het grootste en best passende model tot nu toe. Dat is precies het
   patroon dat je zou verwachten als er een zwak signaal bestaat dat pas
   op grotere schaal draagkracht krijgt — én het patroon dat toeval bij 48
   tests regelmatig produceert. We kunnen en willen die twee hier niet
   uit elkaar trekken.
2. **Wat een eventuele heropening zou vergen** (toekomstwerk, geen
   belofte): een vooraf geregistreerde replicatie op een níeuwe caseset
   die uitsluitend de twee hier gevonden lagen toetst met beide detectoren
   (Bonferroni over 4 toetsen: lat 0.05/4 = 0.0125 — haalbaar voor
   effecten van deze orde als ze echt zijn; dit is dezelfde lat als de
   round-033-preregistratie), of een wezenlijk groter model. Beide zijn
   expliciet níet deze round; dat zou post-hoc-selectie zijn als we het nu
   alsnog draaiden en meetelden.
3. **Het instrument heeft zich opnieuw bewezen.** De permutatiecontrole
   hield een LOOCV-score van 0.88 tegen — zonder die controle was dit een
   verleidelijk "resultaat" geweest. Correct néé zeggen waar néé hoort is
   de methodologische winst van zeven iteraties.

## Doorwerking

- `laag-g-scoping.md`: iteratie 7 afgerond; spoor 2 in rust, spoor 1
  (dialectische falsificatie) blijft de actieve Laag G-route.
- Lagen A–F: onaangetast. De kernclaims van SSL steunen niet op interne
  steun; dit was verkenning van de bovenkant van de stack.

## Claimgrens

Exploratieve Laag G. "In rust" betekent: geen nieuwe runs op dit spoor
zonder vooraf geregistreerd replicatieplan. Deze round toont geen interne
codering aan en sluit haar evenmin uit — de uitkomst is een gekwantificeerd
"nog niet aantoonbaar op deze schaal".
