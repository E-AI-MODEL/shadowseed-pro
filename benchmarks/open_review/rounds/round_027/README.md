# Round 027 — eerste gecontroleerde activatie-meting (permutatie + transfer-cases)

> **Status: het instrument is compleet en de eerste gecontroleerde meting is
> een schoon NULRESULTAAT — het correcte gedrag.** Geen Laag G-claim.

## Opzet

- **Permutatie-controle ingebouwd** (`permutation_control`): labels husselen
  over de vectoren; bij klein n exact (álle toewijzingen opgesomd — de
  controle kwantificeert dan zelf waarom klein n geen claim kan dragen:
  `min_possible_p = 1/n_toewijzingen`), anders Monte Carlo met vaste seed.
- **Transfer-cases** (`dialectic_falsification_transfer.json`): 10 stellingen
  tegen één samengestelde casusbron — de 7 échte round-025 promoted seeds,
  1 domein-nabije stelling en 3 off-topic distractors. Labels op runtime uit
  de fixture-dialectiek (lexicale mechaniek-toets, géén waarheidsoordeel;
  uitkomst: 4 HOUDT_STAND / 6 WEERLEGD).
- Model: pythia-14m (git-mirror), stelling-pooling, alle 6 MLP-lagen.

## Resultaat

| Laag | afstand | p (exact, 210 toewijzingen) | null-gemiddelde |
|---|---|---|---|
| gpt_neox.layers.0.mlp | 0.0351 | 0.552 | 0.0362 |
| gpt_neox.layers.1.mlp | 0.0547 | 0.624 | 0.0593 |
| gpt_neox.layers.2.mlp | 0.0150 | 0.790 | 0.0177 |
| gpt_neox.layers.3.mlp | 0.0236 | 0.810 | 0.0335 |
| gpt_neox.layers.4.mlp | 0.0094 | 0.243 | 0.0081 |
| gpt_neox.layers.5.mlp | 0.0039 | 0.614 | 0.0046 |

**Geen enkele laag scheidt boven toeval.** De waargenomen afstanden liggen op
of onder het null-gemiddelde.

## Lezing (eerlijk)

1. **De controle werkt en deed zijn werk**: de ×160-"scheiding" uit iteratie 2
   (n=3) stort onder de shuffle in — dat was lexicaal toeval, geen signaal.
   Zonder deze controle was dat een verleidelijke overclaim geweest.
2. **Het nulresultaat is verwacht én informatief**: een 14M-parameter
   Engels-getraind model, Nederlandse prompts, en mechaniek-labels (lexicale
   overlap) — er is geen reden waarom hier interne "houdbaarheids"-structuur
   zichtbaar zou zijn. Dat het instrument dat correct rapporteert in plaats
   van schijnscheiding, is de validatie.
3. **Wat een echte Laag G-meting nu nog vraagt** (ongewijzigd): een
   NL-capabel/groter model en een échte dialectische verdictbron; het
   instrument (pooling + permutatie + artifact) ligt er klaar voor.

Doctrine: signaal ≠ verdict; deze route raakt geen seed-state; niets hierin
wijzigt de claimgrenzen van lagen A–F.

## Controle op modelgrootte (pythia-31m, zelfde opzet)

Om uit te sluiten dat het nulresultaat aan "te klein model" ligt, dezelfde
gecontroleerde meting op pythia-31m (bredere hidden dim; via de
model-mirror, fp16 60 MB). Uitkomst
(`activation_probe_pythia31m_transfer_permutation.json`):

| Laag (pythia-31m) | afstand | p (exact, 210) |
|---|---|---|
| gpt_neox.layers.0.mlp | 0.058 | 0.286 |
| gpt_neox.layers.1.mlp | 0.034 | 0.581 |
| gpt_neox.layers.2.mlp | 0.031 | 0.329 |
| gpt_neox.layers.3.mlp | 0.019 | 0.281 |
| gpt_neox.layers.4.mlp | 0.018 | 0.600 |
| gpt_neox.layers.5.mlp | 0.003 | 0.843 |

Opnieuw **geen enkele laag boven toeval** (haalbare vloer 1/210 ≈ 0.005;
laagste p 0.286). Het nulresultaat is dus **robuust tegen modelgrootte** —
14m en 31m geven hetzelfde beeld. Dat lokaliseert het ontbrekende signaal
bij de **labelbron** (fixture-mechaniek = lexicale overlap), niet bij de
modelcapaciteit. Precies daarom is de échte verdictbron (gpt-4.1 via
`activation-probe-real-verdict.yml`, PR #175) de juiste volgende hefboom —
niet een nóg groter model.

Kanttekening bij de mirror: pythia-70m (fp32, 158 MB) werd door de 95 MB-guard
correct geweigerd; 31m (fp16, 60 MB) past. Voor >31m is een fp16-downcast in
de mirror nodig.
