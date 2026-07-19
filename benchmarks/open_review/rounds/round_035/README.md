# Round 035 — grotere-model-rerun: schaalt het (uitblijvende) signaal met modelgrootte?

> **Status: PREREGISTRATIE + run gestart.** Nieuwe vraag, los van het
> gesloten ≤0.5B-verdict (round 033): **codeert een groter model wél wat
> een 0.5B-model niet lineair codeerde?** Zelfde opzet als round 033
> (v3-caseset, gpt-4.1 als ontkoppelde rechter, leespunt `neuron`, 500
> permutaties), alleen het gesondeerde model wordt groter.

## Waarom en wat

Round 033 sloot spoor 2 voor schaal ≤0.5B: geen aantoonbare interne
codering van het externe houdbaarheidsoordeel. De enige open richting was
schaal (het H-Neurons-precedent zit op 24B–70B). Deze round zet de
eerstvolgende CPU-haalbare stap op de schaal-as:

**0.5B (round 033) → 3B (deze round) → 7B (indien geheugen toelaat).**

Zelfde familie (Qwen2.5) zodat de vergelijking zuiver over grootte gaat, en
zelfde v3-caseset + gpt-4.1-verdicten als round 033.

## Geheugen-/precisie-noot (waarom bf16)

De gratis Actions-runner heeft 16 GB RAM. In fp32 kost het gewicht ~4 bytes
per parameter: 0.5B ≈ 2 GB (paste), 3B ≈ 12 GB (krap), 7B ≈ 30 GB (OOM).
Daarom laadt deze round het model in **bfloat16** (`probe_dtype: bfloat16`,
~2 bytes/param): 3B ≈ 6 GB (ruim), 7B ≈ 15 GB (grens — kan alsnog OOM'en,
dan is dát de bevinding: 7B vraagt een grotere runner/GPU). De **gepoolde
activaties worden altijd naar fp32 gecast** vóór de detector, dus bf16 raakt
alleen het geheugen, niet de detector-precisie.

## Run-recept

```text
workflow: Research · Laag G sonde met echte verdictbron
probe_model_id: Qwen/Qwen2.5-3B        # daarna eventueel Qwen/Qwen2.5-7B
dialectic_model_id: gpt-4.1
input_path: src/shadowseed/data/dialectic_falsification_transfer_v3.json
read_location: neuron
sparse_permutations: 500
probe_dtype: bfloat16
```

## Extra exploratieve arms (cross-variant, buiten de schone schaal-as)

Naast de zuivere Qwen2.5-schaal-as draaien op verzoek enkele cross-variant-
modellen. Ze worden gerapporteerd maar vallen buiten de schone
grootte-vergelijking (andere generatie/training); dezelfde leesregel geldt.

| Model | Grootte | bf16-geheugen | Haalbaar op 16GB CPU? |
|---|---|---|---|
| `Qwen/Qwen3-4B` | 4B dense | ~8 GB | ja |
| `Qwen/Qwen2.5-Coder-7B-Instruct` | 7B dense | ~15 GB | grens (kan OOM'en) |
| `Qwen/Qwen3-Coder-30B-A3B-Instruct` | 30B MoE (3B actief) | ~60 GB | **nee** |

`Qwen3-Coder-30B-A3B` kan niet in deze opzet: (1) 60 GB >> 16 GB (harde
OOM), en (2) het is een **mixture-of-experts** — de sonde hookt één
`.mlp.down_proj` per laag, maar MoE routeert tokens over losse expert-MLP's,
dus dat leespunt meet de per-token-activaties niet correct. Dit vraagt een
GPU én een MoE-bewuste sonde-variant; expliciet toekomstwerk, niet deze
round. Coder-modellen zijn bovendien op code getraind (zwakker op
NL-proza), dus hun uitkomst leest als zwakkere indicatie voor de
NL-houdbaarheidsvraag.

## Leesregel (vooraf vastgelegd)

- **Signaal** alleen als een laag na Bonferroni-correctie over het aantal
  geteste lagen onder 0.05 blijft, op centroïde óf sparse — én, om de
  round-032/033-les te respecteren, **stabiel op dezelfde laag(en) bij een
  replicatie**. Eén laag die ongecorrigeerd oogt telt niet.
- **Opkomend-met-schaal patroon** (0.5B null → 3B zwak → richting
  significant) zou de eerste echte aanwijzing zijn dat de codering pas op
  grotere modellen leesbaar wordt; dat vraagt dan een gepreregistreerde
  replicatie op nóg groter (GPU-werk, toekomst).
- **Opnieuw null** = het schaal-argument verzwakt verder voor deze
  grootteklasse; spoor 2 blijft gesloten en de schaalvraag verschuift naar
  ≥24B (GPU, toekomst).
- Signaal ≠ verdict; een eventueel signaal voedt geen promotie en raakt
  lagen A–F niet.

## Claimgrens

Exploratieve Laag G. Deze round kan hoogstens een instrument-niveau-signaal
opleveren, geen SSL-claim. Een 7B-OOM is geen mislukking maar een
meetgrens: de echt relevante schaal (24B+) is geen gratis-CPU-werk.
