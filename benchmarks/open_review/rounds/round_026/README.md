# Round 026 — eerste echte activatie-sonde-runs (Laag G, spoor 2)

> **Status: mechaniek-validatie op echte gewichten GESLAAGD via twee
> onafhankelijke routes; meting zegt nog niets over interne steun (per
> constructie, zie hieronder).** Geen bewijslaag-claim.

## De twee runs (2026-07-03)

| Route | Model | Run/bron | Sterkste laag | Cosine-afstand |
|---|---|---|---|---|
| Actions (`activation-probe.yml`) | distilgpt2 | run 28639320528, artifact `activation-probe` (id 8058091841) | `transformer.h.2.mlp.c_proj` | 0.0054 |
| Sandbox via git-model-mirror (`model-mirror.yml`) | EleutherAI/pythia-14m | branch `model-mirror/EleutherAI-pythia-14m` → lokaal (`activation_probe_pythia14m.json` hier) | `gpt_neox.layers.1.mlp` | 0.0013 |

Beide runs: 3 dialectische cases (2 HOUDT_STAND, 1 WEERLEGD,
fixture-verdicts), alle MLP-lagen correct gevangen (GPT-2- én
GPTNeoX-naamgeving), artifact met `evidence_layer: "G"` en de
doctrine-regel (signaal ≠ verdict; raakt geen seed-state).

## Wat dit wel en niet betekent

**Wel:** het volledige Laag G-sondepad werkt end-to-end op echte gewichten,
in twee architecturen, via twee infrastructuurroutes (Actions én de
git-mirror-backup voor omgevingen zonder HF-toegang). De
netwerkbeperking rond modelgewichten is structureel opgelost.

**Niet:** een uitspraak over interne steun. De gemeten scheiding is
verwaarloosbaar en dat is grotendeels **per constructie**: de prompts zijn
~95% identiek (zelfde bron + instructie; alleen de stelling verschilt) en
mean-pooling over de hele sequentie verdunt het stellingsverschil weg.
Daarnaast: n=3, fixture-verdicts als labels, Engels-getrainde modellen op
Nederlandse prompts.

## Volgende stap (zie `docs/research/laag-g-scoping.md`)

1. token-scoped pooling (stelling-tokens of laatste token);
2. meer cases (transfer-set) en een NL-capabel klein model;
3. échte dialectische verdictbron in plaats van fixture-labels.

## Iteratie 2 (zelfde dag): token-scoped pooling gebouwd en gemeten

De methodologische fix uit "volgende stap 1" is direct gebouwd
(`--pooling stelling`, nu default; `full` blijft beschikbaar) en op
hetzelfde model met dezelfde cases gedraaid
(`activation_probe_pythia14m_stelling.json`):

| Laag (pythia-14m) | full | stelling |
|---|---|---|
| gpt_neox.layers.0.mlp | 0.0009 | 0.1268 |
| gpt_neox.layers.1.mlp | 0.0013 | **0.2097** |
| gpt_neox.layers.2.mlp | 0.0005 | 0.0800 |
| gpt_neox.layers.3.mlp | 0.0009 | 0.1383 |
| gpt_neox.layers.4.mlp | 0.0003 | 0.0248 |
| gpt_neox.layers.5.mlp | 0.0001 | 0.0104 |

Lezing, eerlijk: de verdunning is bevestigd én verholpen — het instrument
heeft nu meetbereik (×160 in de sterkste laag), met een consistent
laagprofiel (vroeg/midden draagt het verschil, de late lagen convergeren).
Dit is een **instrument-validatie, geen signaalvondst**: bij n=3 produceert
élk lexicaal verschil tussen stellingen scheiding onder stelling-pooling.
De echte meting vraagt meer cases (transfer-set), permutatie-/
shuffle-controles (labels husselen hoort de scheiding te laten
instorten), een NL-capabel model en een echte verdictbron.
