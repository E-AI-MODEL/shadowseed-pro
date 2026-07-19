# Round 032 — Laag G iteratie 7: de H-Neurons-methodiek geadopteerd

> **Status: VERDICT — run gedraaid (2026-07-14, run 29299952586): vierde
> null volgens de vooraf vastgelegde leesregel (centroïde p 0.014, sparse
> L1 p 0.018, beide boven de Bonferroni-lat ~0.00208) — het spoor gaat in
> rust. Wel de eerste níet-vlakke null; zie `RESULTS.md`.** Doel: de twee
> open richtingen uit round 030 in één iteratie dichten door de methodiek
> van het H-Neurons-precedent (Gao et al. 2025, arXiv 2512.01797, code
> thunlp/H-Neurons, MIT) daadwerkelijk over te nemen — niet alleen als
> inspiratie te citeren.

## Waarom deze stap

Rounds 026–030 leverden drie schone nulls: geen lineair leesbaar spoor van
het externe houdbaarheidsoordeel in de MLP-**output**-activaties van kleine
modellen, gemeten met een **centroïde**-detector. Round 030 liet twee
inhoudelijke uitwegen open: een groter multilingual model, en andere
leeslocaties. H-Neurons zelf wijst voor allebei de weg — en voegt er een
derde verschil aan toe dat wij tot nu toe niet hadden:

1. **Leespunt.** H-Neurons kwantificeert neuronen op de **input van de
   down-projectie** (`c_proj` bij GPT-2, `down_proj` bij Llama/Qwen-stijl):
   de activatie ná de niet-lineariteit, vóór de terugprojectie. Dat is het
   per-neuron-niveau; onze eerdere rounds lazen de al teruggeprojecteerde
   MLP-output. Nieuw: `--read-location neuron`.
2. **Detector.** H-Neurons vindt zijn neuronen met een **sparse
   L1-classifier**, niet met centroïde-afstand. Een centroïde ziet alleen
   verschuiving van het klasse-gemiddelde; een sparse classifier kan ook een
   klein subset-patroon vinden (<0.1‰ van de neuronen, hun kernresultaat).
   Nieuw: `sparse_probe` — L1-logistische regressie (ISTA/FISTA, numpy-only,
   deterministisch), **leave-one-out-CV** als generalisatietoets en een
   **label-shuffle-permutatiecontrole op de CV-score**. De permutatie is
   essentieel: bij n≈23 en duizenden dimensies haalt een classifier op pure
   ruis makkelijk een "mooie" LOOCV-score; alleen de shuffle-nul verdeelt
   eerlijk.
3. **Model.** `Qwen/Qwen2.5-0.5B` — multilingual (incl. Nederlands), 0.5B
   parameters: een orde groter dan alles wat we tot nu toe sondeerden, en de
   `model.layers.N.mlp.down_proj`-naamgeving past direct op de nieuwe hooks.

Wat we bewust **niet** overnemen: de activation-scaling-interventie
(H-Neurons' Niveau-2-lezing van weight). Interveniëren is pas aan de orde
als er überhaupt een gerepliceerbaar signaal is — eerst meten, dan pas
draaien aan knoppen.

## Run-recept

```text
workflow: Research · Laag G sonde met echte verdictbron
probe_model_id: Qwen/Qwen2.5-0.5B
dialectic_model_id: gpt-4.1
input_path: src/shadowseed/data/dialectic_falsification_transfer_v2.json   # 24 cases
read_location: neuron
sparse_permutations: 500
```

gpt-4.1 blijft de ontkoppelde oordeelbron (zelfde keten als rounds 028/030);
de sonde leest de internals van het Qwen-model met díe labels.

## Leesregel (vooraf vastgelegd)

- **Signaal** alleen als de permutatie-p van de sterkste laag — sparse óf
  centroïde — na Bonferroni-correctie over het aantal geteste lagen onder
  0.05 blijft (24 lagen: ruwe p < 0.05/24 ≈ 0.00208). Eén laag die
  ongecorrigeerd "significant" oogt telt niet; we testen tientallen lagen.
  De permutatievloer moet die lat ook kúnnen halen: met 500 shuffles is de
  laagst haalbare sparse-p 1/501 ≈ 0.0020 — net eronder (codex-P1-les:
  met de eerdere 200 was de lat per constructie onhaalbaar geweest). Bij
  meer dan 24 geteste lagen moet `sparse_permutations` mee omhoog.
- Een hoge LOOCV-score zonder lage permutatie-p is **geen** signaal (zie
  punt 2 hierboven — de detector kan op ruis scoren, de shuffle niet).
- **Vierde schone null** → dit spoor gaat in rust (richting 3 uit round
  030): het instrument is dan op leespunt, detector, taal én schaalstap
  getoetst, en de eerlijke conclusie is dat modellen van deze grootte het
  externe oordeel niet aantoonbaar-leesbaar encoderen. Het H-Neurons-
  precedent zit op 24B–70B; die schaal is geen GitHub-Actions-werk en dan
  expliciet toekomstwerk, geen belofte.
- Een null raakt lagen A–F niet; signaal ≠ verdict, en een eventueel
  signaal voedt geen promotie (Gate-exclusiviteit blijft staan).

## Klaar wanneer

1. Workflow-run gedraaid op bovenstaand recept, artifact + digest hier
   vastgelegd.
2. Uitkomst gelezen op de vooraf vastgelegde leesregel en gedocumenteerd in
   `RESULTS.md` — null of signaal, allebei een geldig antwoord.
3. `laag-g-scoping.md` bijgewerkt met de iteratie-7-uitkomst.

## Claimgrens

Exploratieve Laag G. Dit is instrumentwerk plus een meetplan, geen
resultaat. De adoptie van het H-Neurons-leespunt en de sparse detector dicht
het *methodische* gat met het precedent; het *schaal*-gat (0.5B vs 24B+)
blijft bestaan en wordt hier niet weggeclaimd.
