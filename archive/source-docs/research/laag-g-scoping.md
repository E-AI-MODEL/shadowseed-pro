# Laag G scoping: van dialectische falsificatie naar modelintern signaal

> Status: current
> Date: 2026-07-07
> Evidence layer: Laag G — scoping + iteratieve metingen (rounds 026–030)
> Current source: yes
> Refs: PvA V2 ("scoping-notitie of eerste sonde"), visie-item 4

## Aanleiding

Met de levende schaduwlaag (PR #164), de SSL→RAG-brug (PR #166) en het
positioneringsbesluit (issue #46) is visie-item 4 het laatste onbebouwde punt
van het pad: **echte falsificatie voor speculatieve seeds**, uiteindelijk
modelintern (Laag G). De maintainer heeft dit spoor geopend (2026-07-02).

De contradiction-check van de Gate is vandaag lexicaal/numeriek. Generatieve
"kunnen staan"-seeds vragen meer: een toets die de seed actief probeert weg te
argumenteren, en op termijn een intern modelsignaal dat die toets fundeert.

## Twee sporen

**Spoor 1 — dialectische falsificatie (nu gebouwd).**
`dialectic_falsification.py` + `run-dialectic-falsification`: een model krijgt
bron en stelling en probeert de stelling weg te argumenteren (gedekt, overbodig
of strijdig?). Verdict-mapping, hard in code:

- `WEERLEGD` → contradictie via de Validation Gate: gewicht daalt, het
  agent-contract blokkeert de seed;
- `HOUDT_STAND` → bounded probe-feedback (`probe_type="dialectic"`): kan
  gewicht beperkt bevestigen maar **nooit promoveren**;
- `ONBESLIST` (ook de fail-safe bij onparseerbare output) → neutraal.

De runner promoveert fixture-seeds eerst via de échte Gate en valt ze dán aan:
falsificatie precies op de seeds die zouden mogen sturen. Deterministisch
getest via een fixture-backend; echte runs volgen dezelfde backend-vlaggen als
de andere routes.

**Spoor 2 — H-neuron-achtige interne sonde (harnas gebouwd; echte runs gedraaid in rounds 026–030).**
Gao et al. 2025 (arXiv 2512.01797, code thunlp/H-Neurons, MIT) identificeren
hallucinatie-geassocieerde neuronen in LLM's. De Laag G-vraag voor SSL: is er
*interne* steun voor wat extern als ontbrekend/onhoudbaar wordt gemeten?

Gebouwd (`activation_probe.py` + `run-activation-probe`):

1. model-vrije, deterministische analysekern: per laag de cosine-afstand
   tussen de klasse-centroïden (WEERLEGD vs HOUDT_STAND) plus de
   kandidaat-dimensies met het grootste verschil — kandidaten, geen bewezen
   neuronen;
2. `HFActivationModel` (opt-in, `models`-extra): forward-hooks op de
   MLP-lagen van een klein HF-model tijdens het dialectische verdict;
3. `FakeActivationModel` voor CI: hash-gedreven activaties zonder
   klasse-informatie — bewijst uitsluitend de harnas-mechaniek;
4. artifact `activation_probe.json`, `evidence_layer: "G"`, doctrine-regel in
   het artifact zelf.

**Eerste echte runs (2026-07-03, twee modellen, twee routes):**

- Actions-route: `distilgpt2` (run 28639320528, artifact `activation-probe`
  id 8058091841) — sterkste laag `transformer.h.2.mlp.c_proj`,
  cosine-afstand **0.0054**;
- sandbox-route via de git-model-mirror: `EleutherAI/pythia-14m` (destijds
  branch `model-mirror/EleutherAI-pythia-14m`; de mirror-branches zijn na
  afronding opgeruimd en met de `model-mirror`-workflow op elk moment opnieuw
  te genereren) — alle 6 GPTNeoX-MLP-lagen gevangen,
  sterkste `gpt_neox.layers.1.mlp`, cosine-afstand **0.0013**.

Lezing, eerlijk: de mechaniek werkt end-to-end op echte gewichten in twee
architecturen, maar de gemeten scheiding is verwaarloosbaar — en dat is
grotendeels **per constructie**: de prompts zijn ~95% identiek (zelfde bron +
instructie, alleen de stelling verschilt) en mean-pooling over de hele
sequentie verdunt het stellingsverschil weg. Bovendien n=3 (2 vs 1) en beide
modellen zijn Engels-getraind op Nederlandse prompts. Dit zegt dus níets over
interne steun, positief noch negatief.

**Iteratie 2 (2026-07-03): token-scoped pooling gebouwd en gemeten.**
`--pooling stelling` (nu default) poolt alleen de stelling-tokens via
char-offset-mapping. Op pythia-14m met dezelfde cases: sterkste laag van
0.0013 → **0.2097** (×160), consistent laagprofiel (vroeg/midden draagt het
verschil). Dit is een instrument-validatie, geen signaalvondst — bij n=3
produceert élk lexicaal verschil scheiding. Zie round 026.

**Iteratie 3 (2026-07-03): permutatie-controle + transfer-cases — schoon
nulresultaat.** `permutation_control` (exact bij klein n, anders Monte Carlo)
zit nu in elk probe-rapport; op 10 transfer-cases (7 echte round-025 seeds +
distractors, mechaniek-labels) scheidt op pythia-14m **geen enkele laag boven
toeval** (p 0.24–0.81, exact over 210 toewijzingen). De ×160-"scheiding" uit
iteratie 2 (n=3) stort onder de shuffle in — lexicaal toeval, geen signaal.
Het instrument rapporteert dus correct néé waar néé hoort. Zie round 027.

**Iteratie 4 (2026-07-03): verdictbron ontkoppeld van gesondeerd model.**
`run-activation-probe --verdicts <dialectic-artifact>` leest echte
verdict-labels uit een `dialectic_falsification`-run in plaats van de
fixture-mechaniek. Daarmee is de zuivere Laag G-vraag stelbaar: **encodeert
een klein model intern het houdbaarheidsoordeel dat een sterk model velt?**
De workflow `activation-probe-real-verdict.yml` ketent het: stap 1 laat
gpt-4.1 oordelen (`--backend openai`), stap 2 sondeert een klein model met
díe labels. Verdictbron en gesondeerd model zijn bewust ontkoppeld; het
artifact draagt `verdict_source: "extern"`.

**Iteratie 5 (2026-07-04): eerste inhoudelijke meting — schoon nulresultaat.**
De `activation-probe-real-verdict`-workflow liep end-to-end: gpt-4.1 oordeelde
de houdbaarheid (7 WEERLEGD / 2 HOUDT_STAND / 1 ONBESLIST over de 10
transfer-stellingen), distilgpt2 werd met díe labels gesondeerd. Sterkste laag
`transformer.h.0.mlp.c_proj` cosine 0.102 maar **permutatie-p 0.833** (vloer
0.028) — geen scheiding boven toeval. distilgpt2 codeert gpt-4.1's oordeel niet
lineair. Een null is hier het correcte antwoord (82M Engels model, NL-oordeel);
signaal ≠ verdict, de null raakt lagen A–F niet. Zie round 028.

**Iteratie 6 (2026-07-07, gedraaid — derde schone null): NL-capabel model +
24 cases.**
Beide open punten uit iteratie 5 zijn nu bebouwd
(`dialectic_falsification_transfer_v2.json`, round 030):

1. **caseset 10 → 24** (zelfde brontekst voor vergelijkbaarheid): de 10
   originele cases plus 14 nieuwe met bewuste ontwerp-intentie — 7 kandidaat
   echt-ontbrekende punten, 5 bron-parafrases ("al gedekt"), 2 strijdige
   stellingen — zodat beide klassen plausibel gevuld raken en de
   permutatievloer daalt van 1/36 naar Monte-Carlo-niveau (~0.002, lokaal
   geverifieerd met de fixture-keten);
2. **NL-capabel gesondeerd model**: `GroNLP/gpt2-small-dutch` (GPT-2-
   architectuur, dus de bestaande `.mlp.c_proj`-hooks passen ongewijzigd) via
   de bestaande `activation-probe-real-verdict.yml` (geparametriseerd op
   `probe_model_id` en `input_path`) — gpt-4.1 blijft de oordeelbron.

De ontwerp-intenties in de notes zijn géén labels: labels komen op runtime
van gpt-4.1, en de sonde meet vervolgens of het NL-model dat oordeel intern
lineair codeert.

**Uitkomst (run 28879610931, round 030):** gpt-4.1 gaf 6× HOUDT_STAND /
17× WEERLEGD (23/24 cases; klassenbalans veel beter dan round 028); de
sonde op `GroNLP/gpt2-small-dutch` vond **geen scheiding boven toeval**
(sterkste laag `transformer.h.5.mlp.c_proj`, cosine 0.1355, permutatie-p
0.2056, vloer 0.002). Dit is de sterkste null tot nu toe: NL-model, betere
balans, lage vloer — en nog steeds geen lineair leesbaar spoor van het
externe houdbaarheidsoordeel in de MLP-activaties. Niet uitgesloten blijven:
niet-lineaire codering, andere leeslocaties (attention/residual), of grotere
modellen (het H-Neurons-precedent zit op een andere orde van grootte). Zie
`benchmarks/open_review/rounds/round_030/RESULTS.md`.

**Iteratie 7 (2026-07-14, instrument klaar — run gepland als round 032):
de H-Neurons-methodiek zelf geadopteerd.** De twee open richtingen uit
round 030 in één stap, door het precedent nu ook methodisch te volgen in
plaats van alleen te citeren:

1. **Leespunt `--read-location neuron`**: de input van de down-projectie
   (`.mlp.c_proj` bij GPT-2, `.mlp.down_proj` bij Llama/Qwen) — het
   per-neuron-niveau waarop H-Neurons kwantificeert; onze eerdere rounds
   lazen de al teruggeprojecteerde MLP-output.
2. **Sparse detector**: `sparse_probe` — L1-logistische classifier
   (FISTA, numpy-only, deterministisch) met leave-one-out-CV en een
   label-shuffle-permutatiecontrole op de CV-score, naast de bestaande
   centroïde-meting. Een centroïde ziet alleen gemiddelde-verschuiving;
   dit ziet ook sparse subset-patronen (H-Neurons' kernresultaat: <0.1‰
   van de neuronen draagt het onderscheid).
3. **Groter multilingual model** als run-parameter: `Qwen/Qwen2.5-0.5B`
   (NL-capabel, orde groter dan alles tot nu toe; de
   `down_proj`-naamgeving past direct op de nieuwe hooks).

Bewust niet overgenomen: de activation-scaling-interventie — interveniëren
is pas aan de orde als er een gerepliceerbaar signaal is. Leesregel vooraf
(zie round 032): signaal alleen bij permutatie-p onder Bonferroni over de
geteste lagen; een vierde schone null legt dit spoor in rust en verwijst
de schaalvraag (H-Neurons meet op 24B–70B) expliciet naar toekomstwerk.

**Uitkomst (run 29299952586, round 032): vierde null — spoor in rust.**
gpt-4.1 gaf 7× HOUDT_STAND / 17× WEERLEGD over alle 24 cases; de sonde op
Qwen2.5-0.5B (leespunt `neuron`) vond centroïde-p 0.014
(`model.layers.2.mlp.down_proj`) en sparse-L1-p 0.018
(`model.layers.5.mlp.down_proj`, LOOCV 0.88, 37/4864 dims) — beide ruim
boven de Bonferroni-lat van ~0.00208, en over 24 lagen × 2 detectoren goed
verenigbaar met toeval. Conform de vooraf vastgelegde leesregel gaat spoor
2 hiermee **in rust**: geen nieuwe runs zonder vooraf geregistreerd
replicatieplan. Dat plan bestaat inmiddels: de maintainer heeft besloten
tot één vooraf geregistreerde replicatie (round 033,
`dialectic_falsification_transfer_v3.json`: nieuwe brontekst, alleen de
lagen 2 en 5 tellen, Bonferroni over 4 toetsen, lat 0.0125) — repliceert
het niet, dan sluit het spoor definitief voor deze schaal. Eerlijk
genoteerd: round 032 is de
eerste níet-vlakke null van het spoor (eerdere p's 0.21–0.83) — het
instrument rapporteerde correct néé, en de permutatiecontrole hield een
verleidelijke LOOCV-score van 0.88 tegen. Spoor 1 (dialectische
falsificatie) blijft de actieve Laag G-route. Zie
`benchmarks/open_review/rounds/round_032/RESULTS.md`.

**Iteratie 8 (2026-07-18/19, round 033): gepreregistreerde replicatie —
NIET gerepliceerd; spoor 2 sluit voor deze schaal.** Het round-032-
kandidaat is getoetst op een níeuwe brontekst (WONEN/ZORG/CULTUUR, 24
cases) met vooraf vastgelegde leesregel: alleen de lagen 2 en 5 tellen, ×
beide detectoren, Bonferroni-lat 0.0125. Uitkomst (gpt-4.1: 12 HOUDT_STAND
/ 12 WEERLEGD): **0 van de 4 gepreregistreerde toetsen haalt de lat** —
laag 2 centroïde-p 0.0319 / sparse-p 0.5968 (LOOCV 0.458), laag 5
centroïde-p 0.0459 / sparse-p 0.5649 (LOOCV 0.500). De sparse detector die
in round 032 op laag 5 LOOCV 0.88 gaf, staat nu op 0.50 (toeval). Het
round-032-kandidaat was toeval — precies wat de preregistratie moest
uitwijzen. (De sterkste-laag-instabiliteit kent twee losse oorzaken, zie
`round_033/RESULTS.md`: 032→033 verschuift 2/5→11/10 over een ándere
brontekst, terwijl 10→19 tussen twee runs op dezelfde brontekst numerieke
non-reproduceerbaarheid + ceiling-overfit is — geen dataset-ruis. Deps zijn
inmiddels gepind om dat laatste te sluiten.) **Spoor 2 (activatie-sonde) sluit
definitief voor schaal ≤0.5B**; heropening vraagt de H-Neurons-schaal
(24B–70B) én een nieuwe preregistratie, expliciet toekomstwerk. Het
instrument rapporteerde correct néé. Zie
`benchmarks/open_review/rounds/round_033/RESULTS.md`.

## Doctrine-regels (gelden voor beide sporen)

- Een intern of dialectisch signaal is **falsificatie- of evidence-input**,
  nooit directe promotie: promotie blijft exclusief aan de Gate.
- Dialectiek kan invloed alleen **wegnemen** (Gate-contradictie) of **beperkt
  bevestigen** (bounded probe-feedback); de fail-safe bij twijfel is neutraal.
- "Gevonden" blijft nooit "waar" of "sturend"; een seed die de dialectiek
  overleeft is nog steeds potentieel, geen must.
- Laag G rapporteert per de bestaande laag-taal: geen totaalscore, signaal
  gescheiden van oordeel.

## Klaar-criteria

- Spoor 1 (dialectische falsificatie) is geland en in CI; echte modelruns
  leveren leesbare verdict-artifacts. **Klaar als instap.**
- Spoor 2 (activatie-sonde) is over acht iteraties volledig doorlopen:
  harnas + token-scoped pooling + permutatie-controle + H-Neurons-leespunt
  (`neuron`) + sparse L1-detector, gemeten op meerdere modellen t/m
  Qwen2.5-0.5B, met gpt-4.1 als echte oordeelbron, en afgesloten met een
  **gepreregistreerde replicatie (round 033)** die het enige suggestieve
  kandidaat-signaal (round 032) weerlegde. **Eindresultaat: geen
  aantoonbare interne codering van het externe houdbaarheidsoordeel in
  modellen ≤0.5B.** Spoor 2 is hiermee **gesloten voor deze schaal**;
  heropening vraagt de H-Neurons-schaal (24B–70B) én een nieuwe
  preregistratie — expliciet toekomstwerk, geen must.
- PvA-V2 is afgevinkt (deze scoping + de gelande sonde).

## Claimgrens

Dialectische falsificatie toetst houdbaarheid tegen één bron met één model —
geen waarheidsoordeel. De H-neuron-sonde is verkennend; niets hierin verandert
de bestaande claimgrenzen van lagen A–F.
