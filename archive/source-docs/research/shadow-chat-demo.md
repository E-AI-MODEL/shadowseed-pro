# Shadow chat: de levende schaduwlaag als applicatiedemo

> Status: current
> Date: 2026-07-02
> Evidence layer: geen — applicatiedemo op gevalideerde mechaniek
> Current source: yes

## Wat dit is

`shadowseed chat` is de eerste operationele demonstratie van visie-item 5 uit
`docs/research/vision-generative-seeds.md` §6: de levende schaduw-geheugenlaag
over beurten. De lifecycle was al unit-getest en benchmark-geharnast (W9), maar
de "shadow" in shadow seed had nog geen demonstratie in een echt gesprek: een
seed die in beurt 1 gewichtloos geboren wordt, in de schaduw meereist, via de
Validation Gate promoveert, en pas daarna een láter antwoord mag sturen.

De sessie hergebruikt bewust de gevalideerde mechaniek in plaats van nieuwe te
bouwen:

- W9e clusterrecurrence (`RecurrenceClusterer`, strikte 0.85-dedup intact);
- W9f representative-only promotie (niet-representatieve clusterleden slaan de
  Gate over);
- round-023 use-time discipline: promoted seeds worden gerankt en gecapt
  (`surface_top_k`, default 2) en de prompt weeft ze als *potentieel, geen
  must*;
- dezelfde `build_chat_prompt` en `select_cross_turn_seeds` als
  `ssl_session_suite`.

## Wat het contract afdwingt

Nieuw ten opzichte van de benchmarkroute is dat het `shadowseed_agent`
safety-contract hier live op de invloedgrens staat:

- elke surfacing-kandidaat gaat per beurt opnieuw door
  `AgentSafetyContract.decide()` (weight > 0, status PROMOTED, gelogde
  Gate-promotie in `validation_log`, geen actieve contradictie);
- elke poging tot invloed — toegestaan of geblokkeerd — wordt vastgelegd als
  `AgentInfluenceRecord`;
- `/audit` (en de verplichte audit vóór transcript-write) replayt die records
  via `assert_no_weightless_influence` en faalt hard op gewichtloze invloed;
- `/falsify <seed-id>` is gebruikersgedreven falsificatie: contradictie via de
  Gate, gewicht daalt, en het contract blokkeert de seed vanaf dat moment.

Retrieval-doctrine blijft gelden: een seed die *gevonden* wordt is daarmee niet
*waar* of *sturend*; sturen kan alleen na Gate-promotie én contractcheck.

## Gebruik

```bash
# interactief (fixture-backend, geen secrets nodig)
shadowseed chat --backend fixture

# non-interactief: vragen uit een script, geauditeerd transcript naar disk
shadowseed chat --backend fixture \
  --script vragen.txt --transcript transcript.json --show-shadow
```

In de interactieve modus: `/shadow` toont de schaduwlaag, `/audit` replayt de
influence-records, `/falsify <id>` falsificeert een seed, `/quit` stopt. Het
transcript wordt alleen geschreven nadat de audit is geslaagd.

Echte backends (`openai`, `hf`) volgen dezelfde vlaggen als de
benchmarkroutes.

## SSL→RAG-brug live (`--probe-corpus`)

Met `--probe-corpus <pad>` (JSON-chunks of platte tekst) zoeken promoted seeds
per beurt echt in een corpus — de live consumer van visie-item 2. Wanneer de
manager een retrieval-grade constellatie ziet (`probe_type="retrieval"`) is de
constellatie-centroid de query; anders probet elke promoted seed
(representative-only in clustermodus) zelf. Het beurtsrapport toont
`seed_only_chunk_ids`: wat de seed vindt en de vraag niet.

Doctrine-grens, in code afgedwongen en getest: de hits zijn **aanwezigheid,
geen sturing** — ze gaan nooit de antwoordprompt in en muteren geen seed-state.
Of/hoe seed-gevonden context een antwoord mag verrijken is een later
ontwerpbesluit op de contractlaag, geen retrievalfeature.

## Claimgrens

Dit is een **applicatiedemo op de gevalideerde mechaniek, geen nieuwe
bewijslaag**. Er komt geen evidence-artefact uit dat meetelt in lagen A–G, en
de claimgrenzen in de researchdocs veranderen er niet door. De demo laat zien
dát de doctrine end-to-end afdwingbaar is in een echt gesprek; of de gestuurde
antwoorden ook *beter* zijn blijft de vraag van de blinde reviews (round 022+),
niet van deze route.
