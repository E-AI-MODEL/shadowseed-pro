# Testplan Fase 0 tot en met Fase 4

## Doel

Het testplan onderzoekt waar SSL werkt en waar het faalt. Test niet alles tegelijk. Elke fase heeft een eigen vraag.

## Overzicht

| Fase | Vraag | Output | Succescriterium |
|---|---|---|---|
| 0 | Kan het model kleine gaps vinden? | detectiescore, precision, recall | atomische hits boven baseline |
| 1 | Helpt state over meerdere beurten? | turn-to-detection | sneller of scherper dan baseline |
| 2 | Werkt de Validation Gate? | weight-verdeling | echte gaps stijgen, ruis blijft laag |
| 3 | Helpen constellations? | clusterkwaliteit | cluster-query beter dan losse seeds |
| 4 | Is er steun in modelinterne activaties? | correlatie of causale interventie | effect boven random baseline |

## Fase 0: detectie

### Vraag

Kan een LLM kleine structurele afwezigheden detecteren in een antwoord?

### Test

1. Geef het model de input uit een scenario.
2. Laat het een antwoord maken.
3. Voer de detectie-prompt uit.
4. Normaliseer brede output naar atomische seeds.
5. Vergelijk met de ground truth.

### Metrieken

- detectiescore per scenario: 0, 1 of 2
- precision: hoeveel gevonden seeds zijn relevant?
- recall: hoeveel ground truth seeds worden geraakt?
- atomiciteit: hoeveel outputs zijn echt klein?

### Succes

Fase 0 slaagt wanneer het model meer atomische juiste gaps vindt dan een baseline met algemene aanvullingen.

## Fase 1: multi-turn state

### Vraag

Voegt het meenemen van seeds over beurten waarde toe?

### Condities

A. Standaard LLM zonder seed-state  
B. LLM met ruwe context uit de eerste beurt  
C. LLM met SSL-state

### Metrieken

- in welke beurt wordt de kritieke gap gedetecteerd?
- hoeveel duplicate seeds ontstaan?
- blijft de seed klein?
- verbetert het vervolgantwoord?

### Succes

SSL-state moet scherper of compacter werken dan ruwe context.

## Fase 2: Validation Gate en probes

### Vraag

Filtert de Validation Gate ruis en leveren probes betere vervolgstappen op?

### Test

1. Introduceer echte gaps en valse gaps.
2. Laat het systeem drie of meer turns draaien.
3. Registreer `trace`, `weight`, `occurrence_count` en `evidence_count`.
4. Laat de Gate beslissen welke seeds promoveren.
5. Genereer Socratische en Retrieval Probes voor promoted seeds.

### Metrieken

- percentage valse promoties
- percentage gemiste echte gaps
- kwaliteit van Socratische probes
- informatiewinst van Retrieval Probes

### Succes

Valse gaps blijven rond `weight = 0.0`. Echte, herhaalde en bevestigde gaps stijgen.

## Fase 3: constellations

### Vraag

Voorspellen clusters van kleine gaps een groter ontbrekend kader?

### Test

1. Verzamel promoted seeds uit meerdere turns.
2. Cluster seeds op cosine similarity.
3. Vorm constellations bij minimaal drie verwante seeds.
4. Vergelijk retrieval op losse seeds met retrieval op het clustercentrum.

### Metrieken

- relevantie van clusterlabel
- retrievalkwaliteit op clustercentrum
- aantal nieuwe relevante seeds dat door het cluster wordt voorspeld

### Succes

Een cluster-query levert vaker bruikbare context op dan losse seed-queries.

## Fase 4: modelinterne test

### Vraag

Komt externe `weight` overeen met patronen in modelinterne activaties?

### Test

1. Gebruik een open-source model.
2. Maak paren van context-rijke en context-arme antwoorden.
3. Zoek sparse activatiepatronen die het verschil voorspellen.
4. Test of activation scaling het gedrag meetbaar verandert.

### Metrieken

- classifier boven random baseline
- effect van interventie
- correlatie tussen externe `weight` en interne signalen

### Succes

Er is een reproduceerbaar effect dat niet alleen correlatie is, maar ook reageert op interventie.

## Go/no-go per fase

| Fase | Go wanneer | No-go wanneer |
|---|---|---|
| 0 | atomische hits boven baseline | output blijft vaag of breed |
| 1 | SSL-state beter dan geen state of ruwe context | state voegt niets toe |
| 2 | Gate filtert ruis | valse gaps promoveren vaak |
| 3 | clusters leveren betere retrieval | clusters zijn ruis of duplicaten |
| 4 | activatie-effect reproduceerbaar | geen effect boven random |

## Minimale eerste run

Voor een eerste run zijn drie scenario's genoeg:

1. Industriële Revolutie
2. Grensoverschrijdend consumentencontract
3. HealthTrack software-ontwerp

Draai per scenario:

- baselinevraag
- detectie-prompt
- seed-normalisatie
- scoring
- korte runlog
