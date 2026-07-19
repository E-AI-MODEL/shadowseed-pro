# Round 030 — resultaat: schone null, nu ook op een NL-capabel model

> **Status: VERDICT (instrument-niveau).** De iteratie-6-run is uitgevoerd
> (2026-07-07) en geeft opnieuw een schoon nulresultaat — voor het eerst op
> een model dat het oordeel plausibel kon encoderen, met een vloer die laag
> genoeg was om echt signaal te zien. Signaal ≠ verdict; dit raakt lagen A–F
> niet.

## Runverwijzing

```text
workflow: Research · Laag G sonde met echte verdictbron
run_id: 28879610931            # main @ fad92a3, conclusion: success
artifact: activation-probe-real-verdict (id 8143469738)
artifact_digest: sha256:dd0c539a2bf4899785a69b30efc1fff5c00c1cbfba0d4154c1841fc04f9f2549
probe_model: GroNLP/gpt2-small-dutch (NL-getraind, GPT-2, 12 lagen)
verdict_model: gpt-4.1 (extern, ontkoppeld)
input: dialectic_falsification_transfer_v2.json (24 cases)
```

## Stap 1 — gpt-4.1-verdicten (uit de job-log)

- **6× HOUDT_STAND / 17× WEERLEGD / 0× ONBESLIST** over 23 cases (1 van de
  24 is door de echte Gate-ingest geweigerd vóór de dialectiek).
- De klassenbalans is daarmee wezenlijk beter dan round 028 (daar minderheid
  n=2): minderheid n=6, vloer haalbaar op 0.002.
- Inhoudelijk gedroeg gpt-4.1 zich zoals de ontwerp-intenties hoopten maar
  strenger: alle bron-parafrases, strijdige stellingen en distractors →
  WEERLEGD; van de 7 nieuwe kandidaat-gaps overleefden er 4 (privacy/
  datasporen, docent-bijscholing, adaptatie-financiering, monitoring), plus
  2 originele round-025 seeds (sociale ongelijkheid, kosten-baten). Drie
  kandidaat-gaps werden alsnog weggeargumenteerd — de toetser is geen
  stempelmachine, precies zoals bedoeld.

## Stap 2 — activatie-sonde op het NL-model

| Meting | Waarde |
|---|---|
| Sterkste laag | `transformer.h.5.mlp.c_proj` |
| Cosine-afstand (klasse-centroïden) | 0.1355 |
| **Permutatie-p** | **0.2056** |
| Haalbare vloer | 0.002 |

**Geen enkele laag scheidt boven toeval.** De cosine-afstand oogt hoger dan
in round 028, maar de permutatietoets laat zien dat een gehusselde
labeltoewijzing dat net zo vaak haalt — lexicale variatie, geen codering
van het oordeel.

## Eerlijke lezing

1. **Dit is de sterkste null tot nu toe.** Round 028 kon worden weggelegd
   als "Engels model, NL-oordeel, minderheid n=2". Round 030 sluit die
   uitvluchten: NL-getraind model, betere klassenbalans, vloer 0.002 — en
   nóg geen lineair leesbaar spoor van gpt-4.1's houdbaarheidsoordeel in de
   MLP-activaties.
2. **Wat dit wél en niet betekent.** Niet aangetoond: dat kleine modellen
   (≤124M) het houdbaarheidsoordeel van een frontier-model lineair in hun
   stelling-tokens coderen. Niet uitgesloten: niet-lineaire codering,
   codering op andere posities/lagen (attention i.p.v. MLP), of codering
   in grotere modellen — het H-Neurons-precedent (Gao et al. 2025) zit op
   modellen van een andere orde.
3. **Het instrument is klaar en gevalideerd.** Zes iteraties hebben een
   keten opgeleverd die echte oordelen koppelt aan echte activaties met
   een correcte nulhypothese-toets. Elke volgende modelkeuze is nu een
   parameter, geen bouwwerk.

## Vervolgrichting (open, geen must)

1. Een wezenlijk groter gesondeerd model (0.5B–1B, multilingual) — de
   eerstvolgende plausibele stap op dit spoor.
2. Andere leeslocaties: attention-outputs of residual stream i.p.v.
   MLP-out.
3. Of: dit spoor hier laten rusten en de Laag G-energie op de dialectische
   falsificatie (spoor 1) richten, die vandaag al doctrine-waarde levert.

## Claimgrens

Exploratieve laag G. Drie schone nulls op kleine modellen zeggen niets over
lagen A–F en sluiten interne steun in grotere modellen niet uit. De waarde
van deze ronde is methodologisch: het instrument rapporteert correct néé
waar néé hoort — ook wanneer een positief resultaat aantrekkelijker was
geweest.
